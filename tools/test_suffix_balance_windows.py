"""Synthetic checks for local candidate suffix-balance windows."""
import math
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_balance_windows as probe
from suffix_joint_probe import scan_prefix


class BalanceWindows(unittest.TestCase):
    def test_generated_tiff_cli_modes_and_short_input(self):
        bits = '100000' * 9
        payload = int(bits + '0' * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, 'big')
        tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
        fixture = (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                   + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                   + struct.pack('<I', 0) + payload)
        real_open = open
        def open_fixture(path, *args, **kwargs):
            return io.BytesIO(fixture) if path == 'fixture' else real_open(path, *args, **kwargs)
        for mode in ('discovery', 'verification'):
            for complete in (True, False):
                argv = ['probe', '--mode', mode, '--sample', '1051', 'public.ORF', 'fixture']
                output = io.StringIO()
                scan = mock.patch.object(probe, 'scan_prefix', return_value=([(0, i % 32) for i in range(32)], 192)) if complete else contextlib.nullcontext()
                with self.subTest(mode=mode, complete=complete), mock.patch.object(probe, 'WINDOW', 4), \
                     mock.patch.object(sys, 'argv', argv), mock.patch('builtins.open', side_effect=open_fixture), \
                     scan, contextlib.redirect_stdout(output):
                    status = probe.main()
                result = json.loads(output.getvalue())
                self.assertEqual(status, 0 if complete else 1)
                self.assertEqual(result['mode'], mode)
                self.assertEqual(result['sample']['sha256'], hashlib.sha256(fixture).hexdigest())
                self.assertEqual((result['sample']['pixls_id'], result['sample']['pixls_name']), ('1051', 'public.ORF'))
                for filename, digest in result['source_sha256'].items():
                    with open(os.path.join(os.path.dirname(probe.__file__), filename), 'rb') as source:
                        self.assertEqual(digest, hashlib.sha256(source.read()).hexdigest())
                windows = result['sample']['windows']
                self.assertEqual(len(windows), 4 if mode == 'discovery' else 9)
                self.assertEqual([w['start_token'] for w in windows],
                                 [0, 4, 8, 12] if mode == 'discovery' else [0, 4, 8, 12, 16, 20, 24, 28, 16])
                if not complete:
                    self.assertEqual(result['sample']['returned_tokens'], 9)
                    self.assertIsNone(windows[2]['plugin_mi_bits'])
                    self.assertIsNone(windows[2]['tolerance_pass'])

    def test_uniform_and_escape_index(self):
        tokens = [(0, s) for s in range(32)] + [(17, 31), (0, 0)]
        result = probe.measure(tokens, 0, 33)
        self.assertEqual(result["joint_h_rows_l_columns"], [[1] * 8 for _ in range(4)])
        self.assertEqual(result["escape_tokens"], 1)
        self.assertEqual(result["one_counts"], {"b0": 16, "b1": 16})
        self.assertEqual(result["one_proportions_exact"], {"b0": "1/2", "b1": "1/2"})
        self.assertEqual(result["plugin_mi_bits"], 0.0)
        self.assertTrue(result["tolerance_pass"])
        self.assertEqual(probe.measure(tokens, 33, 1)["retained_tokens"], 1)

    def test_known_dependence_and_boundaries(self):
        result = probe.measure([(0, 0)] * 10 + [(0, 15)] * 10, 0, 20)
        self.assertTrue(math.isclose(result["plugin_mi_bits"], 1.0))
        self.assertFalse(result["tolerance_pass"])
        at_limit = probe.measure([(0, 0)] * 9 + [(0, 3)] * 11, 0, 20)
        self.assertEqual(at_limit["one_proportions_exact"]["b0"], "11/20")
        self.assertTrue(at_limit["tolerance_pass"])
        self.assertFalse(probe.measure([(0, 0)] * 8 + [(0, 3)] * 12, 0, 20)["tolerance_pass"])

    def test_empty_short_and_design(self):
        for result in (probe.measure([(17, 0)], 0, 1), probe.measure([(0, 0)], 0, 2)):
            self.assertIsNone(result["tolerance_pass"])
            self.assertIsNone(result["plugin_mi_bits"])
            self.assertEqual(result["one_proportions_exact"], {"b0": None, "b1": None})
        self.assertEqual(probe.windows("discovery")[-1], (3 * probe.WINDOW, probe.WINDOW))
        self.assertEqual(probe.windows("verification")[-1], (4 * probe.WINDOW, 2 * probe.WINDOW))

    def test_synthetic_bitstream(self):
        values = [(0, 3), (17, 29), (2, 10)]
        bits = "".join("0" * q + "1" + format(s, "05b") for q, s in values)
        payload = int(bits + "0" * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, "big")
        parsed, end = scan_prefix(payload, len(values))
        self.assertEqual((parsed, end), (values, len(bits)))
        result = probe.measure(parsed, 1, 2)
        self.assertEqual((result["escape_tokens"], result["retained_tokens"]), (1, 1))
        self.assertEqual(result["joint_h_rows_l_columns"][1][2], 1)


if __name__ == "__main__":
    unittest.main()
