"""Synthetic metadata and retained-record tests; no catalogue or image decoding."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import capture_metadata_audit as audit
import pixls_samples


def fixture(model, dto, marker):
    make = b'Olympus\0'
    body = model.encode('ascii') + b'\0'
    stamp = dto.encode('ascii') + b'\0' if dto is not None else b''
    start = 8 + 2 + 8 * 12 + 4
    payload = start
    make_at = payload + 8
    body_at = make_at + len(make)
    exif_at = body_at + len(body)
    date_at = exif_at + 2 + 12 + 4
    body_value = struct.unpack('<I', body.ljust(4, b'\0'))[0] if len(body) <= 4 else body_at
    entries = [(256, 4, 1, 2), (257, 4, 1, 2), (273, 4, 1, payload),
               (279, 4, 1, 8), (271, 2, len(make), make_at),
               (272, 2, len(body), body_value), (34665, 4, 1, exif_at), (258, 4, 1, 16)]
    exif = struct.pack('<H', 1) + struct.pack('<HHII', 36867, 2, len(stamp), date_at) + struct.pack('<I', 0)
    return (struct.pack('<2sHIH', b'II', 0x5352, 8, len(entries)) +
            b''.join(struct.pack('<HHII', *entry) for entry in entries) +
            struct.pack('<I', 0) + bytes([marker]) * 8 + make + body + exif + stamp)


class Tests(unittest.TestCase):
    def setUp(self):
        work = ROOT / 'work' / 'test-capture-metadata'
        work.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=str(work))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.records = []
        self.args = []

    def add(self, rid, model, dto, marker):
        data = fixture(model, dto, marker)
        path = self.root / ('private%d.ORF' % marker)
        path.write_bytes(data)
        self.records.append({'id': rid, 'name': 'public%s.ORF' % rid,
                             'sha256': hashlib.sha256(data).hexdigest(), 'licence': 'CC0'})
        self.args += ['--sample', rid, str(path)]

    def run_cli(self, args=None):
        path = self.root / 'records.json'
        path.write_text(json.dumps(self.records), encoding='utf-8')
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(pixls_samples, 'rows', side_effect=AssertionError('network')), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                audit.main(['--licence-records', str(path)] + (self.args if args is None else args))
                status = 0
            except SystemExit as exc:
                status = exc.code
        return status, out.getvalue(), err.getvalue()

    def test_grouping_and_missing_dates(self):
        self.add('1', 'Body One', '2022:01:01 12:00:00', 1)
        self.add('2', 'Body One', '2022:01:01 12:00:00', 2)
        self.add('3', 'Body Two', '2022:01:01 12:00:00', 3)
        self.add('4', 'Body One', '2022:01:01 12:00:01', 4)
        self.add('5', 'Body One', '0000:00:00 00:00:00', 5)
        self.add('6', 'Body One', None, 6)
        self.add('7', '', '2022:01:01 12:00:00', 7)
        self.add('8', 'X', '2022:01:01 12:00:00', 8)
        status, out, err = self.run_cli()
        self.assertEqual((status, err), (0, ''))
        report = json.loads(out)
        self.assertEqual(report['schema_version'], 1)
        self.assertEqual(report['summary'], {'total': 8, 'camera_model_available': 7,
            'datetime_original_available': 6, 'model_and_time_available': 5,
            'distinct_model_time_groups': 4, 'repeated_model_time_groups': 1})
        self.assertEqual(report['same_model_time_groups'], [{'make': 'Olympus', 'model': 'Body One', 'ids': ['1', '2']}])
        self.assertEqual([r['datetime_original_available'] for r in report['samples']], [True] * 4 + [False] * 2 + [True] * 2)
        self.assertEqual(report['samples'][-1]['model'], 'X')
        self.assertNotIn('2022:01:01', out)
        self.assertNotIn(str(self.root), out)
        self.assertIn('independent captures', report['interpretation'])
        self.assertIn('Timezone, subseconds, and clock accuracy', report['interpretation'])

    def test_late_invalid_input_prevents_all_metadata_reads(self):
        self.add('1', 'Body One', '2022:01:01 12:00:00', 1)
        self.add('2', 'Body One', '2022:01:01 12:00:00', 2)
        for kind in ('hash', 'restricted'):
            with self.subTest(kind=kind):
                saved = dict(self.records[1])
                self.records[1]['sha256' if kind == 'hash' else 'licence'] = 'a' * 64 if kind == 'hash' else 'CC-BY-4.0'
                with mock.patch.object(audit, 'file_meta', side_effect=AssertionError('metadata read')) as read:
                    status, out, _ = self.run_cli()
                self.assertEqual((status, out), (2, ''))
                read.assert_not_called()
                self.records[1] = saved

    def test_multiple_exif_pointers_are_not_valid_capture_times(self):
        self.add('1', 'Body One', '2022:01:01 12:00:00', 1)
        self.add('2', 'Body One', '2022:01:01 12:00:00', 2)
        path = Path(self.args[2])
        data = bytearray(path.read_bytes())
        pointer_entry = 10 + 6 * 12
        first = struct.unpack_from('<I', data, pointer_entry + 8)[0]
        pointers_at = len(data)
        data.extend(struct.pack('<II', first, first))
        struct.pack_into('<II', data, pointer_entry + 4, 2, pointers_at)
        path.write_bytes(data)
        self.records[0]['sha256'] = hashlib.sha256(data).hexdigest()
        status, out, err = self.run_cli()
        self.assertEqual((status, err), (0, ''))
        report = json.loads(out)
        self.assertEqual([r['datetime_original_available'] for r in report['samples']], [False, True])
        self.assertEqual(report['summary']['model_and_time_available'], 1)
        self.assertEqual(report['same_model_time_groups'], [])

    def test_conflicting_exif_dates_are_not_counted_as_valid(self):
        first = b'2022:01:01 12:00:00\0'
        other = b'2022:01:01 12:00:01\0'
        for left, right, wrong_type, available in ((first, other, None, False), (other, first, None, False),
                                                    (first, first, None, True), (first, first, 0, False),
                                                    (first, first, 1, False)):
            with self.subTest(left=left, right=right, wrong_type=wrong_type):
                data = bytearray(fixture('Body One', '2022:01:01 12:00:00', 1))
                exif_at = len(data)
                value_at = exif_at + 2 + 2 * 12 + 4
                data.extend(struct.pack('<H', 2))
                data.extend(struct.pack('<HHII', 36867, 2, len(left), value_at))
                data.extend(struct.pack('<HHII', 36867, 2, len(right), value_at + len(left)))
                data.extend(struct.pack('<I', 0) + left + right)
                if wrong_type is not None:
                    struct.pack_into('<H', data, exif_at + 2 + wrong_type * 12 + 2, 7)
                struct.pack_into('<I', data, 10 + 6 * 12 + 8, exif_at)
                path = self.root / 'sample.ORF'
                path.write_bytes(data)
                self.records = [dict(id='1', name='public.ORF',
                    sha256=hashlib.sha256(data).hexdigest(), licence='CC0')]
                status, out, err = self.run_cli(['--sample', '1', str(path)])
                self.assertEqual((status, err), (0, ''))
                report = json.loads(out)
                self.assertEqual(report['samples'][0]['datetime_original_available'], available)

    def test_rejects_wrong_ids_hashes_duplicates_and_restrictions(self):
        self.add('1', 'Body One', '2022:01:01 12:00:00', 1)
        original = list(self.args)
        bad_cases = [original + original, ['--sample', '2', original[-1]],
                     ['--sample', '01', original[-1]], ['--sample', '1', str(self.root / 'missing')]]
        for args in bad_cases:
            with self.subTest(args=args):
                status, out, err = self.run_cli(args)
                self.assertEqual((status, out), (2, ''))
                self.assertNotIn(str(self.root), err)
        digest = self.records[0]['sha256']
        self.records[0]['sha256'] = 'a' * 64
        status, out, _ = self.run_cli()
        self.assertEqual((status, out), (2, ''))
        self.records[0]['sha256'] = digest
        self.records.append(dict(self.records[0], id='2', licence='CC-BY-4.0'))
        for records in (self.records, list(reversed(self.records))):
            self.records = records
            status, out, _ = self.run_cli()
            self.assertEqual((status, out), (2, ''))
        self.records[0]['licence'] = 'CC0'
        self.records[1]['licence'] = 'CC0'
        status, out, _ = self.run_cli(original + ['--sample', '2', original[-1]])
        self.assertEqual((status, out), (2, ''))


if __name__ == '__main__':
    unittest.main()
