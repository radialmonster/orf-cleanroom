"""Offline regressions for sample licence precedence and manifest append behavior."""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = Path(ROOT) / "work" / "test-samples"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pixls_samples as pixls
import manifest_rows as manifest


class SampleTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK.mkdir(parents=True, exist_ok=True)

    def test_catalogue_licence_requires_unambiguous_authoritative_link(self):
        cases = [
            ("<a href='https://creativecommons.org/publicdomain/zero/1.0/' title='Creative Commons 0 - Public Domain' class='cc'>co</a>", 'CC0'),
            ("<a href='http://creativecommons.org/licenses/by-nc-sa/4.0/' title='Creative Commons - Attribution, Non-Commercial, ShareAlike 4.0' class='cc'>cbna</a>", 'CC-BY-NC-SA-4.0'),
            ("<a href='https://creativecommons.org/licenses/by-nc-sa/4.0/'>zero/1.0</a>", 'CC-BY-NC-SA-4.0'),
            ("<a href='https://example.com/publicdomain/zero/1.0/'>CC0</a>", 'unknown'),
            ("<a href='https://[broken/publicdomain/zero/1.0/'>CC0</a>", 'unknown'),
            ("zero/1.0", 'unknown'),
            (None, 'unknown'),
            ("<![foo]><a href='https://creativecommons.org/publicdomain/zero/1.0/'>CC0</a>", 'unknown'),
            ("<a href='https://creativecommons.org/publicdomain/zero/1.0/'>CC0</a> "
             "<a href='https://creativecommons.org/licenses/by/4.0/'>BY</a>", 'unknown'),
        ]
        for html, expected in cases:
            row = ['Olympus', 'Synthetic', 'mode', '', '', html, '',
                   "<a href='https://raw.pixls.us/getfile.php/1/nice/a.ORF'>file</a> " + 'a' * 64]
            with self.subTest(html=html), mock.patch.object(pixls, 'fetch', return_value=json.dumps([row]).encode()):
                self.assertEqual(list(pixls.rows())[0]['licence'], expected)

    def test_check_json_retains_known_records_and_unknown_positions(self):
        contents = (b'cc0 synthetic', b'restricted synthetic', b'unlisted synthetic')
        hashes = [hashlib.sha256(data).hexdigest() for data in contents]
        good = dict(id='1', name='CC0.ORF', sha256=hashes[0], licence='CC0')
        cc0_duplicate = dict(id='2', name='duplicate.ORF', sha256=hashes[1], licence='CC0')
        restricted = dict(id='3', name='restricted.ORI', sha256=hashes[1], licence='CC-BY-4.0')
        for listing in ([good, cc0_duplicate, restricted], [restricted, good, cc0_duplicate]):
            with self.subTest(listing=listing), tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
                paths = []
                for i, data in enumerate(contents):
                    path = Path(folder) / ('private%d.ORF' % i)
                    path.write_bytes(data)
                    paths.append(str(path))
                output = io.StringIO()
                with mock.patch.object(pixls, 'rows', return_value=listing), \
                        mock.patch.object(sys, 'argv', ['pixls_samples', 'check', '--json'] + paths + [paths[0]]), \
                        mock.patch.object(sys, 'stdout', output):
                    with self.assertRaises(SystemExit) as result:
                        pixls.main()
                self.assertEqual(result.exception.code, 1)
                parsed = json.loads(output.getvalue())
                self.assertEqual(parsed, {'files': [good, restricted], 'unknown_inputs': [3], 'unreadable_inputs': []})
                self.assertNotIn(folder, output.getvalue())
                record_path = Path(folder) / 'records.json'
                record_path.write_text(output.getvalue(), encoding='utf-8')
                self.assertEqual(list(manifest.licence_records(str(record_path))), [good, restricted])

    def test_check_json_unknown_only_has_success_status(self):
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            path = Path(folder) / 'unknown.ORF'
            path.write_bytes(b'unknown synthetic')
            output = io.StringIO()
            with mock.patch.object(pixls, 'rows', return_value=[]), \
                    mock.patch.object(sys, 'argv', ['pixls_samples', 'check', '--json', str(path)]), \
                    mock.patch.object(sys, 'stdout', output):
                with self.assertRaises(SystemExit) as result:
                    pixls.main()
            self.assertEqual(result.exception.code, 0)
            self.assertEqual(json.loads(output.getvalue()), {'files': [], 'unknown_inputs': [1], 'unreadable_inputs': []})

    def test_check_json_missing_input_keeps_other_results(self):
        data = b'public synthetic'
        record = dict(id='1', name='public.ORF', sha256=hashlib.sha256(data).hexdigest(), licence='CC0')
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            good, unknown, missing = (Path(folder) / n for n in ('good.ORF', 'unknown.ORF', 'missing.ORF'))
            good.write_bytes(data)
            unknown.write_bytes(b'unlisted synthetic')
            output, error = io.StringIO(), io.StringIO()
            with mock.patch.object(pixls, 'rows', return_value=[record]), \
                    mock.patch.object(sys, 'argv', ['pixls_samples', 'check', '--json', str(missing), str(good), str(unknown)]), \
                    mock.patch.object(sys, 'stdout', output), mock.patch.object(sys, 'stderr', error):
                with self.assertRaises(SystemExit) as result:
                    pixls.main()
            self.assertEqual(result.exception.code, 1)
            self.assertEqual(json.loads(output.getvalue()), {'files': [record], 'unknown_inputs': [3], 'unreadable_inputs': [1]})
            self.assertNotIn(folder, output.getvalue())
            self.assertEqual(error.getvalue(), '')

    def test_check_default_remains_human_readable(self):
        data = b'public synthetic'
        record = dict(id='1', name='public.ORF', sha256=hashlib.sha256(data).hexdigest(), licence='CC0')
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            path = Path(folder) / 'sample.ORF'
            path.write_bytes(data)
            output = io.StringIO()
            with mock.patch.object(pixls, 'rows', return_value=[record]), \
                    mock.patch.object(sys, 'argv', ['pixls_samples', 'check', str(path)]), \
                    mock.patch.object(sys, 'stdout', output):
                with self.assertRaises(SystemExit) as result:
                    pixls.main()
            self.assertEqual(result.exception.code, 0)
            self.assertEqual(output.getvalue(), 'CC0         %s  = public.ORF\n' % path)

    def test_duplicate_hash_non_cc0_wins_in_either_order(self):
        data = b"synthetic sample"
        digest = hashlib.sha256(data).hexdigest()
        cc0 = {"sha256": digest, "licence": "CC0", "id": "1", "name": "a.ORF",
               "model": "synthetic", "local_name": "a.ORF", "url": "unused"}
        restricted = dict(cc0, licence="CC-BY-4.0", id="2")
        for listing in ([cc0, restricted], [restricted, cc0]):
            self.assertEqual(pixls.by_hash(listing)[digest]["licence"], "CC-BY-4.0")
            with tempfile.TemporaryDirectory(dir=str(WORK)) as scratch:
                path = os.path.join(scratch, "sample.ORF")
                with open(path, "wb") as f:
                    f.write(data)
                with mock.patch.object(pixls, "rows", return_value=listing):
                    with self.assertRaises(SystemExit) as result:
                        pixls.cmd_check(mock.Mock(files=[path], json=False))
                self.assertEqual(result.exception.code, 1)
                # Keep synthetic scratch in the checkout; bypass only the destination guard.
                with mock.patch.object(pixls, "rows", return_value=listing), \
                     mock.patch.object(pixls.os.path, "commonpath", return_value="outside-repo"), \
                     mock.patch.object(pixls, "fetch", side_effect=AssertionError("offline guard")):
                    pixls.cmd_download(mock.Mock(dir=scratch, model=None, max=None))
                self.assertEqual(sorted(os.listdir(scratch)), ["sample.ORF"])
                signature = {"sha256": digest}
                with mock.patch.object(manifest, "rows", return_value=listing), \
                     mock.patch.object(manifest, "signature", return_value=signature), \
                     mock.patch.object(manifest, "commit", return_value="test"), \
                     mock.patch.object(sys, "argv", ["manifest_rows", "--by", "@tester", "--own", "--header", "--append", os.path.join(scratch, "out.csv"), path]):
                    manifest.main()
                with open(os.path.join(scratch, "out.csv"), newline="", encoding="utf-8") as f:
                    self.assertEqual(len(list(csv.reader(f))), 1)

    def test_stdout_is_not_closed(self):
        output = io.StringIO()
        with mock.patch.object(manifest, "rows", return_value=[]), \
             mock.patch.object(manifest, "commit", return_value="test"), \
             mock.patch.object(manifest, "signature", side_effect=ValueError("synthetic failure")), \
             mock.patch.object(sys, "argv", ["manifest_rows", "--by", "@tester", "synthetic"]), \
             mock.patch.object(sys, "stdout", output):
            with self.assertRaises(ValueError):
                manifest.main()
        self.assertFalse(output.closed)

    def test_append_stream_closes_on_exception(self):
        stream = io.StringIO()
        with mock.patch.object(manifest, "rows", return_value=[]), \
             mock.patch.object(manifest, "commit", return_value="test"), \
             mock.patch.object(manifest, "signature", side_effect=ValueError("synthetic failure")), \
             mock.patch("builtins.open", return_value=stream), \
             mock.patch.object(sys, "argv", ["manifest_rows", "--by", "@tester", "--append", "unused", "synthetic"]):
            with self.assertRaises(ValueError):
                manifest.main()
        self.assertTrue(stream.closed)

    def test_append_rejects_nonterminated_destination_without_mutation(self):
        sample = {"sha256": "a" * 64, "make": "Test", "model": "Test", "payload_w": 10,
                  "payload_h": 10, "bpp": "1", "size_class": "variable", "compression_tag": 1}
        for original in (b"existing,last-field-without-newline", b"existing,last-field\r"):
            with self.subTest(original=original), tempfile.TemporaryDirectory(dir=str(WORK)) as scratch:
                path = os.path.join(scratch, "out.csv")
                with open(path, "wb") as f:
                    f.write(original)
                args = ["manifest_rows", "--by", "@tester", "--own", "--append", path, "synthetic"]
                with mock.patch.object(manifest, "rows", return_value=[]) as listing, \
                     mock.patch.object(manifest, "signature", return_value=sample) as signature, \
                     mock.patch.object(manifest, "commit", return_value="test"), \
                     mock.patch.object(sys, "argv", args), \
                     mock.patch.object(sys, "stderr", io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        manifest.main()
                    self.assertEqual(raised.exception.code, 2)
                    listing.assert_not_called()
                    signature.assert_not_called()
                with open(path, "rb") as f:
                    self.assertEqual(f.read(), original)

    def test_append_header_only_when_empty(self):
        signature = {"sha256": "a" * 64, "make": "Test", "model": "Test", "payload_w": 10,
                     "payload_h": 10, "bpp": "1", "size_class": "variable", "compression_tag": 1}
        with tempfile.TemporaryDirectory(dir=str(WORK)) as scratch:
            path = os.path.join(scratch, "out.csv")
            args = ["manifest_rows", "--by", "@tester", "--own", "--header", "--append", path, "synthetic"]
            with mock.patch.object(manifest, "rows", return_value=[]), \
                 mock.patch.object(manifest, "signature", return_value=signature), \
                 mock.patch.object(manifest, "commit", return_value="test"), \
                 mock.patch.object(sys, "argv", args):
                manifest.main()
                manifest.main()
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], manifest.COLUMNS)
            self.assertEqual(rows[1][0], "own")
            self.assertEqual(rows[2][0], "own")
            empty = os.path.join(scratch, "empty.csv")
            with open(empty, "w", encoding="utf-8"):
                pass
            args[args.index(path)] = empty
            with mock.patch.object(manifest, "rows", return_value=[]), \
                 mock.patch.object(manifest, "signature", return_value=signature), \
                 mock.patch.object(manifest, "commit", return_value="test"), \
                 mock.patch.object(sys, "argv", args):
                manifest.main()
            with open(empty, newline="", encoding="utf-8") as f:
                self.assertEqual(next(csv.reader(f)), manifest.COLUMNS)


if __name__ == "__main__":
    unittest.main()
