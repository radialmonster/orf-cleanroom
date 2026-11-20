"""Synthetic JPEG metadata and legacy-score regressions."""
import math
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_cross_body_probe as p


def jpeg(hv=(0x22, 0x11, 0x11), quantizer=3):
    def segment(marker, body):
        return bytes([255, marker]) + (len(body)+2).to_bytes(2, 'big') + body
    dqt = segment(0xdb, bytes([0]) + bytes([quantizer])*64)
    sof = segment(0xc0, bytes([8, 3, 232, 3, 232, 3, 1, hv[0], 0, 2, hv[1], 0, 3, hv[2], 0]))
    sos = segment(0xda, bytes([3, 1, 0, 2, 0, 3, 0, 0, 63, 0]))
    return b'\xff\xd8' + dqt + sof + sos + b'\x00\xff\xd9'


def real_fixture():
    def segment(marker, body):
        return bytes((255, marker)) + (len(body)+2).to_bytes(2, 'big') + body
    dqt = segment(0xdb, bytes([0]) + bytes([3])*64)
    # DC codes 0 -> category 0, 10 -> category 1; AC code 0 -> EOB.
    dc = bytes([0]) + bytes([1, 1] + [0]*14) + bytes([0, 1])
    ac = bytes([0x10]) + bytes([1] + [0]*15) + bytes([0])
    dht = segment(0xc4, dc + ac)
    sof = segment(0xc0, bytes([8, 3, 232, 3, 232, 1, 1, 0x11, 0]))
    sos = segment(0xda, bytes([1, 1, 0, 0, 63, 0]))
    # Alternate +1 and -1 DC differences: row-major DC values alternate 1,0.
    bits = ''.join('1010' if i % 2 == 0 else '1000' for i in range(125*125))
    bits += '1' * (-len(bits) % 8)
    entropy = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    preview = b'\xff\xd8' + dqt + dht + sof + sos + entropy + b'\xff\xd9'
    width, height = 1250, 4
    token_bits = ''.join('1' + format((i // 4 + i // width) % 32, '05b')
                         for i in range(width*height))
    payload = bytes(int(token_bits[i:i+8], 2) for i in range(0, len(token_bits), 8))
    tags = [(256, width), (257, height), (273, 62), (279, len(payload))]
    header = b'II' + struct.pack('<HIH', 0x4f52, 8, 4)
    header += b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags) + bytes(4)
    return header + payload + preview


class Tests(unittest.TestCase):
    def test_end_to_end_generated_container(self):
        data = real_fixture()
        sha = hashlib.sha256(data).hexdigest()
        samples = {sid: ('synthetic.orf', sha, 1250, 4) for sid in p.SAMPLES}
        output = io.StringIO()
        args = ['probe', '--phase', 'discovery', '--train', 'train',
                '--sample', '1997', 'a', '--sample', '3800', 'b', '--sample', '6343', 'c']
        with mock.patch.object(p, 'ROWS', 4), mock.patch.object(p, 'SAMPLES', samples), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch.object(sys, 'argv', args), mock.patch('sys.stdout', output):
            x, y, q, s, info = p.load('1995', 'train')
            self.assertEqual((info['candidate_rows'], info['bits_consumed']), (4, 30000))
            self.assertEqual((info['preview_width_blocks'], info['used_preview_rows']), (125, 125))
            self.assertEqual(y[:4], [0.496, -0.504, 0.496, -0.504])
            self.assertEqual(p.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(len(report['results']), 3)
        self.assertTrue(all(row['status'] == 'ok' for row in report['results']))

    def test_selected_jpeg_sampling_and_quantizer(self):
        info = p.validate_preview_sampling(jpeg())
        self.assertEqual((info['pixel_width'], info['pixel_height']), (1000, 1000))
        self.assertEqual(info['dc_quantizer_value'], 3)
        self.assertEqual(info['sampling'], [(2, 2), (1, 1), (1, 1)])
        with self.assertRaises(ValueError):
            p.validate_preview_sampling(jpeg((0x11, 0x22, 0x11)))
        with self.assertRaises(ValueError):
            p.validate_preview_sampling(jpeg(quantizer=0))
        altered = jpeg().replace(bytes([3, 1, 0, 2, 0, 3, 0, 0, 63, 0]),
                                 bytes([3, 2, 0, 1, 0, 3, 0, 0, 63, 0]))
        with self.assertRaises(ValueError):
            p.validate_preview_sampling(altered)

    def test_legacy_scoring_and_shuffle(self):
        q = bytearray(16)
        s = bytearray(range(16))
        info = {'width': 8, 'used_preview_rows': 2, 'preview_width_blocks': 2}
        x = p.legacy.features(q, s, 2, 8, 2, 2, 's', intercept=False)
        fit = [float(i) for i in range(32)]
        y = [-1., 1., -2., 2.]
        with mock.patch.object(p, 'ROWS', 2):
            result = p.score(x, y, q, s, info, fit)
        self.assertEqual(result['r'], p.legacy.stats(y, p.legacy.predict(x, fit))[0])
        self.assertEqual(len(result['shuffles']), 4)
        self.assertTrue(all(math.isfinite(row['r']) for row in result['shuffles']))
        self.assertEqual(result['positive_above_all_four'],
                         result['r'] > 0 and all(result['r'] > row['r'] for row in result['shuffles']))
        with mock.patch.object(p, 'ROWS', 2):
            with self.assertRaises(ValueError):
                p.score(x, [0.] * 4, q, s, info, fit)

    def test_cli_failures_hide_paths(self):
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--train', 'private-path',
                                           '--sample', '1997', 'a', '--sample', '3800', 'b', '--sample', '6343', 'c']), \
             mock.patch.object(p, 'load', side_effect=OSError('private-path')), mock.patch('sys.stdout', output):
            self.assertEqual(p.main(), 1)
        self.assertEqual(json.loads(output.getvalue())['status'], 'unknown_training')
        self.assertNotIn('private-path', output.getvalue())


if __name__ == '__main__':
    unittest.main()
