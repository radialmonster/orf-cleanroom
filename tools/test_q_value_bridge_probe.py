#!/usr/bin/env python3
"""Synthetic exact arithmetic, framing and failure checks; no sample inputs."""
import contextlib
from fractions import Fraction
import io
import itertools
import json
import os
import sys
import struct
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_value_bridge_probe as probe


def oracle(xs):
    n = len(xs)
    mean = Fraction(sum(xs), n)
    bridges = [sum(Fraction(x) - mean for x in xs[:k]) for k in range(1, n + 1)]
    energy = sum(b * b for b in bridges) / n
    variance = sum((Fraction(x) - mean) ** 2 for x in xs) / n
    return energy, (n + 1) * variance / 6


def container(payload, endian='<'):
    """Original minimal one-strip TIFF fixture, held only in memory."""
    fields = [(0x100, 4, 1, 8), (0x101, 4, 1, 4),
              (0x103, 3, 1, 1), (0x111, 4, 1, 128),
              (0x117, 4, 1, len(payload))]
    header = (b'II' if endian == '<' else b'MM') + struct.pack(endian + 'HIH', 0x4f52, 8, len(fields))
    entries = b''
    for tag, kind, count, value in fields:
        inline = struct.pack(endian + ('H' if kind == 3 else 'I'), value)
        entries += struct.pack(endian + 'HHI', tag, kind, count) + inline.ljust(4, b'\0')
    return (header + entries + bytes(4)).ljust(128, b'\0') + payload


class BridgeTests(unittest.TestCase):
    def test_id_conversion_failure_is_argument_error_before_measurement(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [('2', True)]
        if limit:
            cases.append(('9' * (limit + 1), False))
        for sid, simulated in cases:
            args = ['--sample', '1', 'public', 'unused', '--sample', sid, 'public', 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated), patch.object(probe, 'report') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private detail', err.getvalue())

    def test_leading_zero_id_passes_as_canonical_integer(self):
        output = io.StringIO()
        with patch.object(probe, 'report', return_value={'pixls_id': 1}) as measured, contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(['--sample', '01', 'public', 'unused']), 0)
        self.assertEqual(measured.call_args.args[0], 1)
        self.assertEqual(type(measured.call_args.args[0]), int)


    def test_exact_oracle_and_permutation_null(self):
        for xs in ([0, 1], [-1, 0, 2], [-2, -2, 1, 3], [0, 0, 0, 1], [9], [7, 7, 7]):
            n = len(xs)
            energies = []
            for order in itertools.permutations(xs):
                a, v = probe.terms(order)
                e, null = oracle(order)
                self.assertEqual(Fraction(a, n ** 3), e)
                self.assertEqual(Fraction((n + 1) * v, 6 * n ** 2), null)
                energies.append(e)
            self.assertEqual(sum(energies) / len(energies), oracle(xs)[1])

    def test_mapping_all_ordinary_symbols(self):
        expected_zigzag = list(itertools.chain.from_iterable((i, -i - 1) for i in range(272)))
        for u in range(17 * 32):
            q, s = divmod(u, 32)
            self.assertEqual(probe.mapped(q, s, "u32"), u)
            self.assertEqual(probe.mapped(q, s, "zigzag_u32"), expected_zigzag[u])
        with self.assertRaises(ValueError):
            probe.mapped(0, 0, "unknown")

    def test_opposite_order_controls_and_invariance(self):
        alternating = [-1, 1] * 64
        grouped = [-1] * 64 + [1] * 64
        for xs in (alternating, grouped):
            a, v = probe.terms(xs)
            self.assertEqual(probe.terms(list(reversed(xs))), (a, v))
            self.assertEqual(probe.terms([3 * x + 100 for x in xs]), (9 * a, 9 * v))
        self.assertEqual(oracle(alternating)[0], Fraction(1, 2))
        self.assertEqual(oracle(grouped)[0], Fraction(128 ** 2 + 2, 12))
        self.assertLess(probe.pool(128, [probe.terms(alternating)])["R_pool"]["approx"], 0.5)
        self.assertGreater(probe.pool(128, [probe.terms(grouped)])["R_pool"]["approx"], 1)

    def test_pool_is_ratio_of_sums(self):
        xs, ys = [-1, 1] * 64, [-7] * 64 + [7] * 64
        e1, n1 = oracle(xs)
        e2, n2 = oracle(ys)
        pooled = probe.pool(128, [probe.terms(xs), probe.terms(ys)])
        actual = pooled["R_pool"]
        self.assertEqual(Fraction(actual["numerator"], actual["denominator"]), (e1 + e2) / (n1 + n2))
        self.assertNotEqual((e1 + e2) / (n1 + n2), (e1 / n1 + e2 / n2) / 2)
        self.assertIsNone(probe.pool(128, [])['R_pool'])
        self.assertIsNone(probe.pool(128, [(0, 0)])['R_pool'])

    def test_omissions_absolute_parity_and_all_cells(self):
        tokens = [(0, i % 32) for i in range(3 * 128 + 1)]
        tokens[128] = (17, 0)
        tokens[-1] = (18, 0)
        result = probe.aggregate(tokens)
        self.assertEqual(result["selection"], {"complete_blocks": 3, "retained_blocks": 2,
                         "escape_omitted_blocks": 1, "escape_omitted_tokens": 128,
                         "incomplete_tail_tokens": 1, "parsed_escapes": 2, "tail_escapes": 1})
        self.assertEqual(len(result['cells']), 4)
        for cell in result['cells']:
            self.assertEqual([b['absolute_block_index'] for b in cell['blocks']], [0, 2])
            if cell['lane_count'] == 2:
                for parity in (0, 1):
                    xs = [probe.mapped(q, s, cell['mapping']) for q, s in tokens[:128][parity::2]]
                    self.assertEqual(cell['parity_pools'][parity]['sum_A'], 2 * probe.terms(xs)[0])
        for cell in probe.aggregate([(0, 0)] * 128)['cells']:
            self.assertIsNone(cell['pool']['R_pool'])
            self.assertEqual(cell['pool']['zero_variance_lanes'], cell['lane_count'])
        for bad in ([(0, 32)], [(-1, 0)], [(True, 0)]):
            with self.assertRaises(ValueError):
                probe.aggregate(bad)

    def test_bounded_parser_complete_tokens_only(self):
        tokens = [(0, 31), (2, 4), (17, 3), (1, 9)]
        bits = ''.join('0' * q + '1' + format(s, '05b') for q, s in tokens)
        padded = bits + '0' * (-len(bits) % 8)
        data = int(padded, 2).to_bytes(len(padded) // 8, 'big')
        self.assertEqual(probe.candidate.scan_prefix(data), (tokens, len(bits)))
        self.assertEqual(probe.candidate.scan_prefix(b'\x01'), ([], 0))

    def test_container_report_and_bounds(self):
        for endian, mark in (('<', b'II'), ('>', b'MM')):
            for bad in (None, 'compression', 'bounds', 'fixed'):
                payload = b'\x84' * 129
                fields = [(0x100, 4, 1, 8), (0x101, 4, 1, 4),
                          (0x103, 3, 1, 2 if bad == 'compression' else 1),
                          (0x111, 4, 1, 10000 if bad == 'bounds' else 128),
                          (0x117, 4, 1, 48 if bad == 'fixed' else len(payload))]
                header = mark + struct.pack(endian + 'HIH', 0x4f52, 8, len(fields))
                entries = b''
                for tag, kind, count, value in fields:
                    inline = struct.pack(endian + ('H' if kind == 3 else 'I'), value)
                    entries += struct.pack(endian + 'HHI', tag, kind, count) + inline.ljust(4, b'\0')
                data = (header + entries + bytes(4)).ljust(128, b'\0') + payload
                with patch.object(probe, 'open', return_value=io.BytesIO(data), create=True), patch.object(probe, 'LIMIT', 128):
                    if bad:
                        with self.assertRaises(ValueError):
                            probe.report(1, 'PUBLIC', 'PRIVATE')
                    else:
                        result = probe.report(1, 'PUBLIC', 'PRIVATE')
                        self.assertEqual(result['payload_w'], 8)
                        self.assertEqual(result['payload_bytes'], 129)
                        self.assertEqual(result['sha256'], probe.hashlib.sha256(data).hexdigest())
                        self.assertEqual(len(result['cells']), 4)
                        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_incomplete_prefix_never_computes_statistics(self):
        # Four q=0,s=0 tokens occupy 24 bits; three occupy 18 bits.
        for endian in ('<', '>'):
            for payload, returned, consumed in ((b'\0', 0, 0), (b'\x01', 0, 0),
                                                (b'\x80', 1, 6), (b'\x82\x08\0', 3, 18)):
                with self.subTest(endian=endian, payload=payload):
                    with patch.object(probe, 'LIMIT', 4), patch.object(probe, 'aggregate') as aggregate:
                        with patch.object(probe, 'open', return_value=io.BytesIO(container(payload, endian)), create=True):
                            with self.assertRaises(probe.IncompletePrefix) as caught:
                                probe.report(1, 'PUBLIC', 'PRIVATE')
                        self.assertEqual(caught.exception.diagnostic,
                                         {'reason': 'incomplete_prefix', 'requested_tokens': 4,
                                          'returned_tokens': returned, 'token_shortfall': 4 - returned,
                                          'consumed_bits': consumed, 'payload_bits': 8 * len(payload)})
                        aggregate.assert_not_called()
            with patch.object(probe, 'LIMIT', 4), patch.object(probe, 'open', return_value=io.BytesIO(container(b'\x82\x08\x20', endian)), create=True):
                result = probe.report(1, 'PUBLIC', 'PRIVATE')
            self.assertEqual(result['returned_tokens'], 4)
            self.assertEqual(result['token_shortfall'], 0)
            self.assertEqual(result['consumed_bits'], 24)
            self.assertEqual(len(result['cells']), 4)

    def test_real_report_cli_incomplete_and_mixed_batches(self):
        fixtures = {'PRIVATE_SHORT': container(b'\x80'),
                    'PRIVATE_COMPLETE': container(b'\x82\x08\x20')}
        def read_input(path, mode):
            return io.BytesIO(fixtures[path]) if path in fixtures else open(path, mode)
        for complete in (False, True):
            args = ['--sample', '2', 'PUBLIC_SHORT', 'PRIVATE_SHORT']
            if complete:
                args += ['--sample', '1', 'PUBLIC_COMPLETE', 'PRIVATE_COMPLETE']
            out = io.StringIO()
            with patch.object(probe, 'LIMIT', 4), patch.object(probe, 'open', side_effect=read_input, create=True), contextlib.redirect_stdout(out):
                status = probe.main(args)
            result = json.loads(out.getvalue())
            self.assertEqual(status, 1)
            self.assertEqual([sample['pixls_id'] for sample in result['samples']], [1] if complete else [])
            self.assertEqual(result['failures'], [{'pixls_id': 2, 'category': 'input_or_measurement_error',
                              'reason': 'incomplete_prefix', 'requested_tokens': 4, 'returned_tokens': 1,
                              'token_shortfall': 3, 'consumed_bits': 6, 'payload_bits': 8}])
            self.assertNotIn('PRIVATE', out.getvalue())
            self.assertNotIn('cells', result['failures'][0])
            self.assertNotIn('selection', result['failures'][0])

    def test_production_prefix_boundary(self):
        # Original string encoder, actual 262144-token contract (no patched limit).
        for count in (probe.LIMIT - 1, probe.LIMIT):
            bits = '100000' * count
            padded = bits + '0' * (-len(bits) % 8)
            payload = int(padded, 2).to_bytes(len(padded) // 8, 'big')
            with patch.object(probe, 'open', return_value=io.BytesIO(container(payload)), create=True):
                if count < probe.LIMIT:
                    with self.assertRaises(probe.IncompletePrefix) as caught:
                        probe.report(1, 'PUBLIC', 'PRIVATE')
                    self.assertEqual(caught.exception.diagnostic['returned_tokens'], count)
                    self.assertEqual(caught.exception.diagnostic['token_shortfall'], 1)
                else:
                    result = probe.report(1, 'PUBLIC', 'PRIVATE')
                    self.assertEqual(result['returned_tokens'], probe.LIMIT)
                    self.assertEqual(result['selection']['complete_blocks'], 2048)
                    self.assertEqual(result['consumed_bits'], 6 * probe.LIMIT)

    def test_mixed_cli_preserves_success_sanitizes_failure(self):
        out = io.StringIO()
        with patch.object(probe, 'report', side_effect=[{'pixls_id': 1}, OSError('PRIVATE')]), contextlib.redirect_stdout(out):
            status = probe.main(['--sample', '1', 'PUBLIC1', 'PRIVATE1', '--sample', '2', 'PUBLIC2', 'PRIVATE2'])
        result = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(result['samples'], [{'pixls_id': 1}])
        self.assertEqual(result['failures'], [{'pixls_id': 2, 'category': 'input_or_measurement_error'}])
        self.assertNotIn('PRIVATE', out.getvalue())


if __name__ == '__main__':
    unittest.main()
