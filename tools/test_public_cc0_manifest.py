#!/usr/bin/env python3
"""Synthetic public CC0 record and manifest generation tests."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest_rows as m

DIGEST = 'a' * 64
RECORD = dict(name='capture.ORF', sha256=DIGEST, licence='CC0',
              owner_declaration_url='https://example.org/owner',
              public_source_url='https://example.org/capture')


class PublicTests(unittest.TestCase):
    def parse(self, text):
        with patch('builtins.open', return_value=io.StringIO(text)):
            return m.public_cc0_records('record')

    def test_record_validation_and_duplicate_keys(self):
        self.assertEqual(self.parse(json.dumps([RECORD]))[DIGEST], RECORD)
        for changed in (dict(RECORD, licence='CC-BY'), dict(RECORD, name='../x.ORF'),
                        dict(RECORD, sha256='x'), dict(RECORD, public_source_url='file:///x'),
                        dict(RECORD, owner_declaration_url=''), dict(RECORD, public_source_url=None)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.parse(json.dumps([changed]))
        with self.assertRaises(ValueError):
            self.parse('[{"name":"a.ORF","name":"b.ORF"}]')
        with self.assertRaises(ValueError):
            self.parse(json.dumps([RECORD, dict(RECORD, name='other.ORF')]))

    def test_mode_outputs_public_identity_without_network(self):
        signature = dict(sha256=DIGEST, payload_w=10, payload_h=10, size_class='variable',
                         make='Maker', model='Body', bpp=7, compression_tag=1)
        out = io.StringIO()
        with patch.object(sys, 'argv', ['manifest_rows.py','--by','@tester','--header',
                                        '--public-cc0-records','records','sample']), \
             patch.object(m, 'public_cc0_records', return_value={DIGEST: RECORD}), \
             patch.object(m, 'signature', return_value=signature), patch.object(m, 'commit', return_value='abc'), \
             patch.object(m, 'rows') as network, contextlib.redirect_stdout(out):
            self.assertEqual(m.main(), 0)
        network.assert_not_called()
        rows = list(m.csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual((rows[0]['source'], rows[0]['pixls_id'], rows[0]['pixls_name'],
                          rows[0]['licence'], rows[0]['sha256']),
                         ('public-cc0', '', 'capture.ORF', 'CC0', DIGEST))
        self.assertTrue(rows[0]['measured_by'].startswith('@tester '))

    def test_unknown_hash_is_failure_without_row(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['manifest_rows.py','--by','@tester',
                                        '--public-cc0-records','records','sample']), \
             patch.object(m, 'public_cc0_records', return_value={}), \
             patch.object(m, 'signature', return_value={'sha256': DIGEST}), \
             patch.object(m, 'commit', return_value='abc'), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(m.main(), 1)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('hash absent', err.getvalue())

    def test_real_synthetic_signature_and_invalid_late_record(self):
        work = Path(__file__).resolve().parent.parent / 'work' / 'test-public-cc0'
        work.mkdir(parents=True, exist_ok=True)
        tags = [(256, 2), (257, 2), (259, 1), (273, 74), (279, 8)]
        data = (struct.pack('<2sHIH', b'II', 0x5352, 8, len(tags)) +
                b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags) +
                struct.pack('<I', 0) + bytes(8))
        record = dict(RECORD, sha256=hashlib.sha256(data).hexdigest())
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            sample, records, dest = root / 'sample.ORF', root / 'records.json', root / 'out.csv'
            sample.write_bytes(data)
            records.write_text(json.dumps([record]), encoding='utf-8')
            prefix = (','.join(m.COLUMNS) + '\n').encode('utf-8')
            dest.write_bytes(prefix)
            args = ['manifest_rows', '--by', '@tester', '--append', str(dest),
                    '--public-cc0-records', str(records), str(sample)]
            with patch.object(m, 'rows', side_effect=AssertionError('network')), \
                    patch.object(m, 'commit', return_value='test'), patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
            written = dest.read_bytes()
            self.assertTrue(written.startswith(prefix))
            row = next(m.csv.DictReader(io.StringIO(written.decode('utf-8'))))
            self.assertEqual((row['source'], row['pixls_name'], row['sha256']),
                             ('public-cc0', record['name'], record['sha256']))
            records.write_text(json.dumps([record, dict(record, licence='restricted')]), encoding='utf-8')
            with patch.object(m, 'rows', side_effect=AssertionError('network')), \
                    patch.object(m, 'signature') as measure, patch.object(sys, 'argv', args), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    m.main()
            self.assertEqual(raised.exception.code, 2)
            measure.assert_not_called()
            self.assertEqual(dest.read_bytes(), written)


if __name__ == '__main__':
    unittest.main()
