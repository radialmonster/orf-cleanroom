#!/usr/bin/env python3
"""Original in-memory aggregate/CLI regressions for unit_order_probe.py."""
import contextlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unit_order_probe as probe


def fixture(rows):
    width, height = len(rows[0]), len(rows)
    payload = bytearray()
    for row in rows:
        for begin in range(0, width, 10):
            # Independent 24-bit little-endian construction for two values.
            for i in range(begin, begin+10, 2):
                payload.extend((row[i] | row[i+1] << 12).to_bytes(3, 'little'))
            payload.append(0)
    offset = 8+2+5*12+4
    entries = [(256, width), (257, height), (259, 1), (273, offset), (279, len(payload))]
    header = b'IIRO'+struct.pack('<I', 8)+struct.pack('<H', len(entries))
    table = b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag,value in entries)
    return header+table+bytes(4)+payload


class Tests(unittest.TestCase):
    def run_cli(self, arguments, files):
        def read(path, mode='r', *args, **kwargs):
            if path in files:
                return io.BytesIO(files[path])
            raise OSError('PRIVATE_PATH_MUST_NOT_APPEAR')
        out = io.StringIO()
        with mock.patch('builtins.open', side_effect=read), contextlib.redirect_stdout(out):
            code = probe.main(arguments)
        return code, json.loads(out.getvalue())

    def test_hand_counts_and_swapped_selection(self):
        row = list(range(0, 100, 10))
        self.assertEqual(probe.accum_row(row, 0), (30, 30, 3))
        self.assertEqual(probe.accum_row(row, 0, True), (30, 90, 3))
        self.assertEqual(probe.accum_row(row, 80), (0, 0, 0))
        self.assertEqual(probe.accum_row(row, 79), (30, 30, 3))

    def test_empty_and_zero_within(self):
        self.assertEqual(probe.summarize(0,0,0), {'within_sum':0,'cross_sum':0,
            'selected_units':0,'within_mean':None,'cross_mean':None,'cross_over_within':None})
        self.assertIsNone(probe.summarize(0, 4, 2)['cross_over_within'])
        self.assertEqual(probe.summarize(0,4,2)['cross_mean'], 2)

    def test_actual_cli_empty_selection(self):
        code, report = self.run_cli(['8190','--sample','test','Synthetic','good'],
                                   {'good':fixture([list(range(10))]*2)})
        self.assertEqual(code,0)
        self.assertTrue(report['complete'])
        self.assertEqual(report['samples'][0]['emitted']['selected_units'],0)
        self.assertIsNone(report['samples'][0]['emitted']['within_mean'])

    def test_actual_cli_known_packing_and_arbitrary_path(self):
        code, report = self.run_cli(['0','--sample','test','Synthetic','arbitrary'],
                                   {'arbitrary':fixture([list(range(0,100,10))]*2)})
        self.assertEqual(code,0)
        sample=report['samples'][0]
        self.assertEqual(sample['rows_measured'],2)
        self.assertEqual(sample['eligible_units'],6)
        self.assertEqual(sample['emitted'],probe.summarize(60,60,6))
        self.assertEqual(sample['swapped'],probe.summarize(60,180,6))

    def test_full_frame_and_default_central_band(self):
        row = list(range(0, 100, 10))
        data = fixture([row] * 402)
        for options, start, stop in (([], 51, 351), (['--all-rows'], 0, 402)):
            with self.subTest(options=options):
                code, report = self.run_cli(['0', '--sample', 'test', 'Synthetic', 'frame'] + options,
                                            {'frame': data})
                self.assertEqual(code, 0)
                sample = report['samples'][0]
                self.assertEqual((sample['stored_row_start'], sample['stored_row_stop']), (start, stop))
                n = stop - start
                self.assertEqual(sample['emitted']['selected_units'], 3*n)
                self.assertEqual(sample['swapped']['selected_units'], 3*n)
                self.assertEqual((sample['emitted']['within_sum'], sample['emitted']['cross_sum']), (30*n, 30*n))
                self.assertEqual((sample['swapped']['within_sum'], sample['swapped']['cross_sum']), (30*n, 90*n))

    def test_actual_cli_mixed_error_retains_success(self):
        code, report = self.run_cli(['0','--sample','bad','Malformed','bad',
            '--sample','ok','Synthetic','good','--sample','missing','Missing','absent'],
            {'bad':b'bad', 'good':fixture([list(range(10))])})
        self.assertEqual(code,1)
        self.assertFalse(report['complete'])
        self.assertEqual([r['sample_id'] for r in report['samples']],['bad','ok','missing'])
        self.assertIn('error',report['samples'][0])
        self.assertEqual(report['samples'][1]['emitted']['selected_units'],3)
        self.assertNotIn('PRIVATE',json.dumps(report))

    def test_directory_malformed_does_not_abort(self):
        with mock.patch.object(probe.os, 'listdir', return_value=['bad','good']), \
             mock.patch.object(probe.os.path, 'isfile', return_value=True):
            code, report=self.run_cli(['0','synthetic'],{
                os.path.join('synthetic','bad'):b'bad',
                os.path.join('synthetic','good'):fixture([list(range(10))])})
        self.assertEqual(code,1)
        self.assertEqual(len(report['samples']),2)
        self.assertEqual(report['samples'][1]['emitted']['selected_units'],3)

    def test_invalid_threshold(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            probe.main(['-1','unused'])
        self.assertEqual(error.exception.code,2)


if __name__ == '__main__':
    unittest.main()
