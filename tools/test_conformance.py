"""Synthetic CLI output tests; the decoder is stubbed and no images are read."""
import contextlib
import csv
import io
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conformance


class Tests(unittest.TestCase):
    def setUp(self):
        self.first = dict(sha256='a' * 64, variant='V0', model='Synthetic', packing='packed-16',
                          order='le', width=4, height=2, payload_bytes=16, consumed_bytes=16,
                          exact_end=True, min=0, max=240, out_of_range=0, smooth=1.23456,
                          output_sha256='1' * 64, row_layout='natural', status='verified')
        self.second = dict(self.first, sha256='b' * 64, exact_end=False, consumed_bytes=15,
                           out_of_range=2, output_sha256='2' * 64, status='unverified')
        self.compressed = dict(sha256='c' * 64, variant='compressed', model='Compressed')

    def run_cli(self, options):
        outputs = {'first.orf': self.first, 'second.orf': self.second, 'compressed.orf': self.compressed}

        def decode(path):
            if path == 'bad.orf':
                raise ValueError('synthetic failure')
            return outputs[path]

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(conformance.orf_decode, 'decode_file', side_effect=decode), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = conformance.main(options)
        return status, out.getvalue(), err.getvalue()

    def test_csv_sorts_valid_rows_preserves_hashes_and_reports_errors(self):
        status, out, err = self.run_cli(['--csv', 'second.orf', 'bad.orf', 'compressed.orf', 'first.orf'])
        self.assertEqual(status, 1)
        reader = csv.DictReader(io.StringIO(out))
        with (Path(__file__).resolve().parent.parent / 'samples' / 'conformance-V0.csv').open(newline='', encoding='utf-8') as f:
            self.assertEqual(reader.fieldnames, next(csv.reader(f)))
        rows = list(reader)
        self.assertEqual([r['input_sha256'] for r in rows], ['a' * 64, 'b' * 64])
        self.assertEqual([r['output_sha256'] for r in rows], ['1' * 64, '2' * 64])
        self.assertEqual([r['exact_end'] for r in rows], ['True', 'False'])
        self.assertEqual(rows[0]['smooth'], '1.235')
        self.assertEqual(rows[0]['row_layout'], 'natural')
        self.assertIn('ERROR bad.orf: synthetic failure', err)
        self.assertIn('summary: V0 decoded 2, exact-end 1, out-of-range values 2, compressed (not yet specified) 1, errors 1', err)

    def test_human_output_and_v0_only(self):
        for options, shows_compressed in (([], True), (['--v0-only'], False)):
            with self.subTest(options=options):
                status, out, err = self.run_cli(options + ['first.orf', 'compressed.orf', 'second.orf'])
                self.assertEqual((status, err), (0, ''))
                self.assertEqual('compressed  not yet specified' in out, shows_compressed)
                self.assertIn('smooth 1.23  out ' + '1' * 64, out)
                self.assertIn('out ' + '2' * 64 + '  UNVERIFIED', out)
                self.assertIn('summary: V0 decoded 2, exact-end 1, out-of-range values 2, compressed (not yet specified) 1, errors 0', out)

    def test_csv_v0_only_omits_compressed_row(self):
        status, out, err = self.run_cli(['--csv', '--v0-only', 'compressed.orf', 'first.orf'])
        self.assertEqual(status, 0)
        self.assertEqual([r['input_sha256'] for r in csv.DictReader(io.StringIO(out))], ['a' * 64])
        self.assertIn('compressed (not yet specified) 1, errors 0', err)


if __name__ == '__main__':
    unittest.main()
