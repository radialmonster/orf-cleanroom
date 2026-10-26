"""Offline retained licence tests with synthetic TIFF data only."""
import contextlib
import csv
import hashlib
import io
import json
import os
import runpy
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
    def test_missing_dimensions_do_not_invent_mode_or_size_class(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            for entry, missing in ((0, 'width'), (1, 'height')):
                data = bytearray(sample())
                struct.pack_into('<H', data, 10 + entry * 12, 65000)
                path = root / 'sample.ORF'
                path.write_bytes(data)
                record = dict(id='42', name='a.ORF', sha256=hashlib.sha256(data).hexdigest(), licence='CC0')
                out = io.StringIO()
                with self.subTest(missing=missing):
                    with mock.patch.object(manifest, 'rows', return_value=[record]), \
                            mock.patch.object(manifest, 'commit', return_value='test'), \
                            mock.patch.object(sys, 'argv', ['manifest_rows', '--by', '@tester', '--header', str(path)]), \
                            contextlib.redirect_stdout(out):
                        manifest.main()
                    row = next(csv.DictReader(io.StringIO(out.getvalue())))
                    self.assertEqual(row['payload_w' if entry == 0 else 'payload_h'], '')
                    self.assertEqual(row['mode'], '' if entry == 0 else 'normal')
                    self.assertEqual((row['bpp'], row['size_class'], row['variant']), ('', '', 'unassigned'))
        self.assertEqual((manifest.mode(6000), manifest.mode(6001)), ('normal', 'hires'))

    def test_batch_continues_after_bad_files_and_preserves_append_prefix(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            first, bad, missing, last = (root / n for n in ('first.ORF', 'bad.ORF', 'missing.ORF', 'last.ORF'))
            first.write_bytes(sample())
            bad.write_bytes(b'not TIFF')
            last.write_bytes(sample() + b'extra synthetic bytes')
            records = [dict(id=str(i), name=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), licence='CC0')
                       for i, name, path in ((1, 'first.ORF', first), (2, 'last.ORF', last))]
            dest = root / 'out.csv'
            prefix = b'existing,row\n'
            dest.write_bytes(prefix)
            args = ['manifest_rows', '--by', '@tester', '--append', str(dest)] + [str(p) for p in (first, bad, missing, last)]
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(manifest, 'rows', return_value=records), \
                 mock.patch.object(manifest, 'commit', return_value='test'), \
                 mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(manifest.main(), 1)
            written = dest.read_bytes()
            self.assertTrue(written.startswith(prefix))
            appended = list(csv.DictReader(io.StringIO(written[len(prefix):].decode('utf-8')), fieldnames=manifest.COLUMNS))
            self.assertEqual([row['pixls_id'] for row in appended], ['1', '2'])
            self.assertEqual(err.getvalue().splitlines(), ['input 2: ValueError', 'input 3: FileNotFoundError'])
            self.assertNotIn(folder, err.getvalue())
            self.assertEqual(out.getvalue(), '')

    def test_entrypoint_propagates_batch_failure_and_success(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            good, bad = root / 'good.ORF', root / 'bad.ORF'
            good.write_bytes(sample())
            bad.write_bytes(b'not TIFF')
            records = root / 'records.json'
            records.write_text(json.dumps([dict(id='1', name='good.ORF',
                sha256=hashlib.sha256(sample()).hexdigest(), licence='CC0')]), encoding='utf-8')
            script = str(ROOT / 'tools' / 'manifest_rows.py')
            for paths, expected in (([str(good)], 0), ([str(bad), str(good)], 1)):
                args = [script, '--by', '@tester', '--header', '--licence-records', str(records)] + paths
                out, err = io.StringIO(), io.StringIO()
                with self.subTest(expected=expected), mock.patch.object(sys, 'argv', args), \
                     contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as raised:
                        runpy.run_path(script, run_name='__main__')
                self.assertEqual(raised.exception.code, expected)
                self.assertEqual([row['pixls_id'] for row in csv.DictReader(io.StringIO(out.getvalue()))], ['1'])
                self.assertEqual(err.getvalue(), '' if expected == 0 else 'input 1: ValueError\n')
                self.assertNotIn(folder, err.getvalue())

    def test_duplicate_json_keys_fail_before_output_or_append(self):
        work = ROOT / 'work' / 'test-manifest-offline'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            data = sample()
            sample_path = root / 'sample.ORF'
            sample_path.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            record = '{"id":"42","name":"a.ORF","sha256":"%s","licence":"CC0"}' % digest
            ambiguous = record.replace('"licence":"CC0"', '"licence":"CC-BY-4.0","licence":"CC0"')
            payloads = ['[' + ambiguous + ']',
                        '{"files":[],"files":[' + record + ']}',
                        '[' + record + ',' + ambiguous + ']']
            for payload in payloads:
                for append in (False, True):
                    with self.subTest(payload=payload, append=append):
                        records = root / 'records.json'
                        records.write_text(payload, encoding='utf-8')
                        dest = root / 'out.csv'
                        dest.write_bytes(b'existing,row\n')
                        args = ['manifest_rows', '--by', '@tester', '--header', '--licence-records', str(records)]
                        if append:
                            args += ['--append', str(dest)]
                        args.append(str(sample_path))
                        out, err = io.StringIO(), io.StringIO()
                        with mock.patch.object(manifest, 'rows', side_effect=AssertionError('network called')), \
                                mock.patch.object(manifest, 'commit', return_value='test'), \
                                mock.patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), \
                                contextlib.redirect_stderr(err):
                            with self.assertRaises(SystemExit) as raised:
                                manifest.main()
                        self.assertEqual(raised.exception.code, 2)
                        self.assertEqual(out.getvalue(), '')
                        self.assertEqual(dest.read_bytes(), b'existing,row\n')
                        self.assertIn('invalid or unreadable licence records', err.getvalue())
                        self.assertNotIn(str(records), err.getvalue())

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
