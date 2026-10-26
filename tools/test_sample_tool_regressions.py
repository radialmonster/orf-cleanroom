"""Offline regressions for sample licence precedence and manifest append behavior."""
import csv
import hashlib
import io
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
                        pixls.cmd_check(mock.Mock(files=[path]))
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
