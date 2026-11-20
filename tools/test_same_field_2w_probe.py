"""Synthetic checks of fixed disjoint-band context support and scoring."""
import os
import io
import json
import hashlib
import random
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import same_field_2w_probe as probe


class Tests(unittest.TestCase):
    def test_report_endpoints_and_short_cli(self):
        tokens = [(i % 3, i % 2) for i in range(1200)]

        def run_report(words, phase):
            bits = ''.join('0' * q + '1' + format(s, '05b') for q, s in words)
            bits += '0' * (-len(bits) % 8)
            payload = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
            entries = [(0x100, 129), (0x101, 10), (0x103, 1), (0x111, 74), (0x117, len(payload))]
            data = b'II' + struct.pack('<HIH', 0x4f52, 8, len(entries))
            data += b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in entries)
            data += bytes(4) + payload
            metadata = ('public.ORF', hashlib.sha256(data).hexdigest(), 129, 10)
            with mock.patch.object(probe, 'BAND', 400), \
                 mock.patch.dict(probe.SAMPLES, {'1993': metadata}), \
                 mock.patch('builtins.open', mock.mock_open(read_data=data)):
                return probe.report('1993', 'unused', phase)

        result = run_report(tokens, 'verification')
        self.assertEqual(result['bands']['1']['end_bit_exclusive'], sum(q + 6 for q, _ in tokens[:800]))
        self.assertEqual(result['bands']['2']['end_bit_exclusive'], result['bits_consumed'])
        short = run_report(tokens[:12], 'discovery')
        self.assertEqual((short['status'], short['reason']), ('unknown', 'short_input'))
        self.assertEqual((short['requested_tokens'], short['returned_tokens'], short['bits_consumed']), (800, 12, 84))
        self.assertEqual(short['payload_bytes'], 11)
        self.assertNotIn('pairs', short)
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--sample', '1993', 'secret', '--sample', '5283', 'secret']), \
             mock.patch.object(probe, 'report', return_value=short), mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 1)
        self.assertNotIn('secret', output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['samples'][0]['reason'], 'short_input')

    def test_all_omission_sites_and_bands(self):
        width, size = 129, 410
        offsets = (0, 1, 2, 3, 4, 5, 2 * width - 128, 2 * width, 2 * width + 128)
        t = 2 * width + 128
        for off in offsets:
            tokens = [(0, 0)] * (2 * size)
            tokens[t - off] = (17, 0)
            band = probe.measure(tokens, width, 0, size)
            self.assertGreater(band['omitted'], 0)
            self.assertEqual(band['candidate'], band['retained'] + band['omitted'])
            self.assertEqual(probe.measure(tokens, width, 1, size)['omitted'], 0)

    def test_planted_donor_and_empty(self):
        width, size = 129, 8192
        rng = random.Random(29)
        bits = [rng.randrange(2) for _ in range(size * 2)]
        for start in (0, size):
            for t in range(start + 2 * width, start + size):
                bits[t] = bits[t - 2 * width]
        tokens = [(0, b) for b in bits]
        a, b = (probe.measure(tokens, width, i, size) for i in (0, 1))
        rows = probe.pair(a, b, width)
        planted = next(x for x in rows if x['field'] == 'suffix_b0' and x['model'] == '2w')
        self.assertGreater(planted['gain_vs_local_bits'], .5)
        empty = probe.measure([(17, 0)] * (size * 2), width, 0, size)
        self.assertTrue(all(x['status'] == 'unknown' and x['gain_vs_local_bits'] is None
                            for x in probe.pair(empty, b, width)))
        with self.assertRaises(ValueError):
            probe.measure(tokens[:-1], width, 1, size)

    def test_no_donor_and_unseen_context(self):
        width, size = 129, 8192
        rng = random.Random(123)
        tokens = [(0, rng.randrange(2)) for _ in range(size * 2)]
        a, b = (probe.measure(tokens, width, i, size) for i in (0, 1))
        rows = probe.pair(a, b, width)
        donor = next(x for x in rows if x['field'] == 'suffix_b0' and x['model'] == '2w')
        self.assertLess(abs(donor['gain_vs_local_bits']), .03)
        a['tables']['suffix_b0'][1][0] = [0, 0]
        b['tables']['suffix_b0'][1][0] = [1, 0]
        donor = next(x for x in probe.pair(a, b, width) if x['field'] == 'suffix_b0' and x['model'] == '2w')
        self.assertGreater(donor['test_targets_in_unseen_contexts'], 0)


if __name__ == '__main__':
    unittest.main()
