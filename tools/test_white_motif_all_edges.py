"""Synthetic all-edge selection, aggregation and preregistration checks."""
import io
import json
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import white_motif_all_edges as worker


class AllEdges(unittest.TestCase):
    def setUp(self):
        self.payload = bytes((40 + 800 * (6 * 5220 + 12) + 7) // 8)

    def test_ambiguous_edges_degree_and_masks(self):
        pitch = 31332
        points = [40, 41, 40 + pitch, 41 + pitch]
        def parse(payload, start, end, k, capped):
            success = (start == 88 and end == 40 + pitch and k == 5)
            return {'endpoint': success, 'words': 5214 if success else 0,
                    'escapes': 0, 'reason': 'exact_end' if success else 'stop_overrun'}
        with patch.object(worker.old, 'motif_positions', return_value=points), \
             patch.object(worker.old, 'interior', side_effect=parse):
            r = worker.analyze(self.payload, 5220, expected=(4, 4))
        self.assertEqual(r['eligible_directed_edges'], 4)
        self.assertEqual(r['source_motifs_without_edges'], 2)
        self.assertEqual(r['target_motifs_without_edges'], 2)
        self.assertEqual(r['joint_success_masks'], {'0000': 3, '0101': 1})
        self.assertEqual(r['edge_strata_masks']['source_degree'], {'2:0000': 3, '2:0101': 1})
        self.assertEqual(r['source_outcomes']['literal_k5'], {'all': 0, 'some': 1, 'none': 1})

    def test_gate_precedes_parser_and_window(self):
        with patch.object(worker.old, 'motif_positions', return_value=[40]), \
             patch.object(worker.old, 'interior') as parse:
            with self.assertRaisesRegex(ValueError, 'discovery_selector_mismatch'):
                worker.analyze(self.payload, 5220, expected=(791, 1568))
            parse.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'incomplete_window'):
            worker.analyze(b'\0', 5220)
        with self.assertRaisesRegex(ValueError, 'unsupported_width'):
            worker.analyze(self.payload, 100)

    def test_cli_reports_safe_selector_reason(self):
        fake = type('Hash', (), {'hexdigest': lambda self: worker.SHA})()
        output = io.StringIO()
        with patch.object(sys, 'argv', ['tool', '--sample', 'private']), \
             patch('builtins.open', return_value=io.BytesIO(b'fake')), \
             patch.object(worker.hashlib, 'sha256', return_value=fake), \
             patch.object(worker.old, 'independent_strips', return_value=({'width': 5220, 'height': 1}, b'payload')), \
             patch.object(worker, 'analyze', side_effect=ValueError('discovery_selector_mismatch')), \
             patch('sys.stdout', output):
            self.assertEqual(worker.main(), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result['reason'], 'discovery_selector_mismatch')
        self.assertNotIn('private', output.getvalue())
    def test_repeat_uses_disjoint_window(self):
        with patch.object(worker.old, 'motif_positions', return_value=[]) as positions:
            r = worker.analyze(self.payload, 5220, repeat=True)
        start = 40 + 400 * 31332
        self.assertEqual(positions.call_args.args[1:], (start, start + 400 * 31332))
        self.assertEqual(r['status'], 'sparse_no_edges')
        self.assertEqual(r['source_outcomes']['literal_k4'], {'all': 0, 'some': 0, 'none': 0})


if __name__ == '__main__':
    unittest.main()
