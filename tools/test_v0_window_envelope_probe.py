"""Synthetic checks for V0 window envelope study."""
import os
import io
import json
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sensor_rejection_controls as c
import v0_sensor_controls as old
import v0_window_envelope_probe as p


def fixture(endian):
    order = '<' if endian == 'II' else '>'
    width, height, offset = 320, 240, 62
    tags = [(256, width), (257, height), (273, offset), (279, width*height*2)]
    header = endian.encode() + struct.pack(order+'HIH', 0x4f52, 8, 4)
    header += b''.join(struct.pack(order+'HHII', tag, 4, 1, value) for tag, value in tags) + bytes(4)
    words = [((x + y) % 4096) * 16 for y in range(height) for x in range(width)]
    return header + struct.pack(order + str(len(words)) + 'H', *words)


class Tests(unittest.TestCase):
    def test_cli_and_unknown(self):
        data = fixture('II')
        output = io.StringIO()
        with mock.patch.object(p, 'read_verified', side_effect=[data, ValueError('private path'), data]), mock.patch('sys.stdout', output):
            status = p.main(['--phase', 'discovery', '--sample', '1800', 'x', '--sample', '2151', 'y', '--sample', '5424', 'z'])
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual([s['status'] for s in report['samples']], ['ok', 'unknown', 'ok'])
        self.assertNotIn('private path', output.getvalue())
        self.assertEqual(len(report['samples'][0]['windows']), 9)
        self.assertEqual(sum(report['samples'][0]['counts']['1']['fixed']['identity'].values()), 3)

    def test_training_and_transforms(self):
        fixed = p.training(1)['limits']
        self.assertEqual(fixed, c.envelope([x for x in c.cohort(c.DEVELOPMENT_SEEDS) if x['mapping'] == 'identity']))
        for m in (1, 2, 4, 8):
            n = 32*24*m*m
            values = list(range(n))
            transformed = c.transform(values, 'affine_permutation')
            self.assertEqual(len(set(transformed)), n)
            self.assertEqual(c.transform(transformed, 'affine_permutation', True), values)
            width, height = 32*m, 24*m
            ramp = [x+y for y in range(height) for x in range(width)]
            f = c.features(ramp, width, height)
            self.assertEqual(f['scalars']['lag2_mean_abs'], 2)
            self.assertEqual(f['scalars']['lane_mean_spread'], 2)
            self.assertEqual(f['scalars']['seam_mean_abs'], 1)

    def test_synthetic_container_and_old_baseline(self):
        refitted = {m: p.training(m) for m in (1, 2, 4)}
        fixed = refitted[1]['limits']
        for endian in ('II', 'MM'):
            data = fixture(endian)
            result = p.measure(data, (1, 2, 4), fixed, refitted)
            old_rows = old.diagnostic(data, fixed)['windows']
            self.assertEqual(len(result['windows']), 9)
            for new, previous in zip(result['windows'][:3], old_rows):
                self.assertEqual((new['x'], new['y']), (previous['x'], previous['y']))
                for key in ('stored_word_features', 'stored_min', 'stored_max', 'nonzero_low_nibbles', 'shift4_min', 'shift4_max'):
                    self.assertEqual(new[key], previous[key])
                for actual, expected in zip(new['trials'], previous['trials']):
                    self.assertEqual(actual['features'], expected['features'])
                    self.assertEqual(actual['changed_values'], expected['changed_values'])
                    self.assertEqual(actual['fixed_rejected_by'], expected['rejected_by'])
            for pos in range(3):
                small, big = result['windows'][pos], result['windows'][pos+6]
                self.assertLessEqual(big['x'], small['x'])
                self.assertLessEqual(big['y'], small['y'])
                self.assertGreaterEqual(big['x']+big['width'], small['x']+small['width'])
                self.assertGreaterEqual(big['y']+big['height'], small['y']+small['height'])


if __name__ == '__main__':
    unittest.main()
