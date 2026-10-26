"""Offline retained licence tests with synthetic TIFF data only."""
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import manifest_rows as manifest


def sample():
    tags = [(256, 2), (257, 2), (259, 1), (273, 74), (279, 8)]
    return (struct.pack('<2sHIH', b'II', 0x5352, 8, len(tags)) +
            b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags) +
            struct.pack('<I', 0) + bytes(8))


class Tests(unittest.TestCase):
    def test_invalid_handle_cannot_emit_offline_row(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            data = sample()
            path = root / 'sample.ORF'
            path.write_bytes(data)
            records = root / 'records.json'
            records.write_text(json.dumps([dict(id='42', name='a.ORF',
                sha256=hashlib.sha256(data).hexdigest(), licence='CC0')]), encoding='utf-8')
            out = io.StringIO()
            args = ['manifest_rows', '--by', 'tester', '--header', '--licence-records', str(records), str(path)]
            with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                    mock.patch.object(manifest, 'commit', return_value='test'), \
                    mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    manifest.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(out.getvalue(), '')

    def test_invalid_handles_fail_before_catalogue_or_output(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        for handle in ('tester', '', '@', '@tester other', '@tester @other', '@-tester',
                       '@tester-', '@test--er', '@test_er'):
            with self.subTest(handle=handle), tempfile.TemporaryDirectory(dir=str(work)) as folder:
                dest = Path(folder) / 'output.csv'
                dest.write_bytes(b'existing,row\n')
                args = ['manifest_rows', '--by', handle, '--append', str(dest), 'sample']
                out, err = io.StringIO(), io.StringIO()
                with mock.patch.object(manifest, 'rows', return_value=[]) as catalogue, \
                        mock.patch.object(manifest, 'signature') as signature, \
                        mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), \
                        contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as raised:
                        manifest.main()
                self.assertEqual(raised.exception.code, 2)
                catalogue.assert_not_called()
                signature.assert_not_called()
                self.assertEqual(dest.read_bytes(), b'existing,row\n')
                self.assertEqual(out.getvalue(), '')

    def test_valid_handles_work_with_live_listing(self):
        data = sample()
        record = dict(id='42', name='a.ORF', sha256=hashlib.sha256(data).hexdigest(), licence='CC0')
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            path = Path(folder) / 'sample.ORF'
            path.write_bytes(data)
            for handle in ('@tester', '@A', '@a-b', '@' + 'a' * 39):
                out = io.StringIO()
                with self.subTest(handle=handle), mock.patch.object(manifest, 'rows', return_value=[record]), \
                        mock.patch.object(manifest, 'commit', return_value='test'), \
                        mock.patch.object(sys, 'argv', ['manifest_rows', '--by', handle, '--header', str(path)]), \
                        contextlib.redirect_stdout(out):
                    manifest.main()
                row = next(csv.DictReader(io.StringIO(out.getvalue())))
                self.assertEqual(row['measured_by'], handle + ' tools/orf_signature.py test')

    def test_offline_hash_match_and_no_catalogue(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            data = sample()
            (root / 'renamed.ORF').write_bytes(data)
            record = dict(id='42', name='Camera - Test (4:3).ORF', sha256=hashlib.sha256(data).hexdigest(), licence='CC0', status='verified')
            for payload in ([record], {'files': [record]}):
                (root / 'records.json').write_text(json.dumps(payload), encoding='utf-8')
                output = io.StringIO()
                args = ['manifest_rows', '--by', '@tester', '--header', '--licence-records', str(root / 'records.json'), str(root / 'renamed.ORF')]
                with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                        mock.patch.object(manifest, 'commit', return_value='test'), \
                        mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(output):
                    manifest.main()
                row = next(csv.DictReader(io.StringIO(output.getvalue())))
                self.assertEqual((row['source'], row['pixls_id'], row['pixls_name'], row['sha256']),
                                 ('pixls', '42', record['name'], record['sha256']))
            (root / 'renamed.ORF').write_bytes(data[:-1] + b'\x01')
            output = io.StringIO()
            with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                    mock.patch.object(manifest, 'commit', return_value='test'), \
                    mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(io.StringIO()):
                manifest.main()
            self.assertEqual(list(csv.DictReader(io.StringIO(output.getvalue()))), [])

    def test_restricted_duplicate_wins_and_own_cannot_override(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        good = dict(id='1', name='a.ORF', sha256=hashlib.sha256(sample()).hexdigest(), licence='CC0')
        restricted = dict(good, id='2', licence='CC-BY-4.0')
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            (root / 'sample.ORF').write_bytes(sample())
            for records in ([good, restricted], [restricted, good]):
                (root / 'records.json').write_text(json.dumps(records), encoding='utf-8')
                with self.subTest(records=records), mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                        mock.patch.object(manifest, 'commit', return_value='test'), \
                        mock.patch.object(sys, 'argv', ['manifest_rows', '--by', '@tester', '--own', '--licence-records', str(root / 'records.json'), str(root / 'sample.ORF')]), \
                        contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                    manifest.main()
                    self.assertEqual(out.getvalue(), '')

    def test_malformed_records_fail_before_output(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        valid = dict(id='1', name='a.ORF', sha256='a' * 64, licence='CC0')
        bad = [None, {}, [dict(valid, id='bad')], [dict(valid, name='../a.ORF')],
               [dict(valid, sha256='bad')], [dict(valid, licence='')],
               [valid, dict(valid, name='other.ORF')]]
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            path = Path(folder) / 'records.json'
            for payload in bad:
                path.write_text(json.dumps(payload), encoding='utf-8')
                out = io.StringIO()
                with self.subTest(payload=payload), mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                        mock.patch.object(manifest, 'signature', side_effect=AssertionError('file read')), \
                        mock.patch.object(sys, 'argv', ['manifest_rows', '--by', '@tester', '--header', '--licence-records', str(path), 'sample']), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        manifest.main()
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(out.getvalue(), '')

    def test_invalid_or_missing_records_do_not_create_append_destination(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            bad = root / 'private-records.json'
            bad.write_text('{invalid PRIVATE', encoding='utf-8')
            for path in (bad, root / 'missing-private.json'):
                dest = root / 'output.csv'
                err, out = io.StringIO(), io.StringIO()
                args = ['manifest_rows', '--by', '@tester', '--header', '--append', str(dest), '--licence-records', str(path), 'sample']
                with self.subTest(path=path.name), mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                        mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as raised:
                        manifest.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse(dest.exists())
                self.assertEqual(out.getvalue(), '')
                self.assertIn('invalid or unreadable licence records', err.getvalue())
                self.assertNotIn('PRIVATE', err.getvalue())
                self.assertNotIn(str(path), err.getvalue())

    def test_empty_record_path_does_not_use_catalogue(self):
        err = io.StringIO()
        with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                mock.patch.object(manifest, 'signature', side_effect=AssertionError('file read')), \
                mock.patch.object(sys, 'argv', ['manifest_rows', '--by', '@tester', '--licence-records', '', 'sample']), \
                contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as raised:
                manifest.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('invalid or unreadable licence records', err.getvalue())

    def test_late_invalid_record_preserves_existing_append_destination(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            records = [dict(id='1', name='a.ORF', sha256='a' * 64, licence='CC0'),
                       dict(id='2', name='b.ORF', sha256='bad', licence='CC0')]
            path, dest = root / 'records.json', root / 'output.csv'
            path.write_text(json.dumps(records), encoding='utf-8')
            original = b'existing,row\n'
            dest.write_bytes(original)
            err = io.StringIO()
            args = ['manifest_rows', '--by', '@tester', '--append', str(dest), '--licence-records', str(path), 'sample']
            with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                    mock.patch.object(manifest, 'signature', side_effect=AssertionError('file read')), \
                    mock.patch.object(sys, 'argv', args), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    manifest.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertIn('invalid or unreadable licence records', err.getvalue())
            self.assertEqual(dest.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
