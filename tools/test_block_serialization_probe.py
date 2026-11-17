"""Synthetic accounting and cross-parser tests; no ORF inputs."""
import os
import hashlib
import io
import json
import random
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_serialization_probe as probe


def encode(values, separated):
    parts = []
    for start in range(0, len(values), 32):
        block = values[start:start + 32]
        unary = ['0' * (v >> 5) + '1' for v in block]
        suffix = [format(v & 31, '05b') for v in block]
        parts.extend(unary + suffix if separated else
                     [a + b for a, b in zip(unary, suffix)])
    return ''.join(parts)


def bytepack(bits):
    assert len(bits) % 8 == 0
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def reference(bits, count, separated):
    pos = qsum = maxq = complete = blocks = 0
    if len(bits) < 6 * count:
        return ('minimum',)
    for _ in range(count // 32):
        for _ in range(32):
            end = bits.find('1', pos)
            if end < 0:
                return ('unary', pos, complete, blocks)
            q = end - pos
            pos = end + 1
            qsum += q
            maxq = max(maxq, q)
            if not separated:
                if pos + 5 > len(bits):
                    return ('suffix', pos, complete, blocks)
                pos += 5
                complete += 1
        if separated:
            available = min(32, (len(bits) - pos) // 5)
            pos += available * 5
            complete += available
            if available < 32:
                return ('suffix', pos, complete, blocks)
        blocks += 1
    return ('complete', pos, complete, blocks, qsum, maxq, all(x == '1' for x in bits[pos:]))


class Synthetic(unittest.TestCase):
    def compare(self, bits, count, separated):
        expected = reference(bits, count, separated)
        got = probe.scan(bytepack(bits), count, separated)
        if expected[0] == 'minimum':
            self.assertEqual(got['status'], 'contradiction_minimum_length')
        elif expected[0] in ('unary', 'suffix'):
            self.assertEqual(got['status'], 'contradiction_truncated_' + expected[0])
            # A failed unary consumes its remaining zero bits in the production scan.
            if expected[0] == 'suffix':
                self.assertEqual(got['consumed_bits'], expected[1])
            self.assertEqual((got['complete_values'], got['complete_blocks']), expected[2:4])
        else:
            self.assertEqual(got['status'], 'complete')
            self.assertEqual((got['consumed_bits'], got['complete_values'], got['complete_blocks'],
                              got['sum_q_read'], got['max_q_read'], got['hypothetical_all_ones_tail']),
                             expected[1:])
            self.assertEqual(got['strict_end'], expected[1] == len(bits))
            self.assertEqual(got['tail_bits'], len(bits) - expected[1])

    def test_generated_cross_parses(self):
        rng = random.Random(29830)
        for _ in range(300):
            values = [rng.randrange(128) for _ in range(64)]
            for source in (False, True):
                bits = encode(values, source)
                bits += '1' * (-len(bits) % 8)
                for parser in (False, True):
                    self.compare(bits, 64, parser)

    def test_end_and_tails(self):
        bits = encode([31] * 32, False)
        for suffix in ('', '11111111', '11101111'):
            for parser in (False, True):
                self.compare(bits + suffix, 32, parser)

    def test_truncated_cases(self):
        for bits in ('0' * 184, '0' * 192, '1' * 31 + '0' * 161,
                     '1' * 32 + '0' * 160, '0' * 190 + '10'):
            for parser in (False, True):
                self.compare(bits, 32, parser)

    def test_incompatible_count(self):
        with self.assertRaises(ValueError):
            probe.scan(b'', 31, True)

    def test_locator_and_cli_snapshot(self):
        # A synthetic one-IFD TIFF with the protocol dimensions and one strip.
        tags = [(256, 4, 1, 5220), (257, 4, 1, 3912),
                (273, 4, 1, 62), (279, 4, 1, 24)]
        data = (b'II' + struct.pack('<HIH', 42, 8, len(tags)) +
                b''.join(struct.pack('<HHII', *t) for t in tags) +
                struct.pack('<I', 0) + bytes([255]) * 24)
        payload, off = probe.locate(data)
        self.assertEqual((off, len(payload)), (62, 24))
        output = io.StringIO()
        digest = hashlib.sha256(data).hexdigest()
        with mock.patch.object(probe, 'IDENTITIES', {'fake': digest}), \
             mock.patch.object(probe, 'N', 32), \
             mock.patch.object(sys, 'argv', ['probe', 'fake', 'unshared']), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'measured')
        self.assertTrue(report['interleaved']['strict_end'])
        self.assertTrue(report['separated']['hypothetical_all_ones_tail'])
        for field, val in ((256, 100), (279, 0)):
            altered = [(t, ty, n, val if t == field else v) for t, ty, n, v in tags]
            invalid = (b'II' + struct.pack('<HIH', 42, 8, len(tags)) +
                       b''.join(struct.pack('<HHII', *t) for t in altered) +
                       struct.pack('<I', 0) + bytes([255]) * 24)
            with self.assertRaises(ValueError):
                probe.locate(invalid)

    def test_private_path_not_printed(self):
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', 'PA200010.ORF', 'secret-path']), \
             mock.patch('builtins.open', side_effect=OSError('secret-path')), \
             mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 1)
        self.assertNotIn('secret-path', output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['status'], 'unknown_metadata_or_read')


if __name__ == '__main__':
    unittest.main()
