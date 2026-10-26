"""Exercise the reviewed automerge workflow decision function offline."""
import importlib.util
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work" / "test-automerge"


class AutoMergeDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = (ROOT / ".github/workflows/automerge.yml").read_text(encoding="utf-8")
        start = "          python3 - <<'PY'\n"
        end = "          PY\n"
        if workflow.count(start) != 1:
            raise AssertionError("workflow heredoc marker changed")
        source = workflow.split(start, 1)[1]
        if source.count(end) != 1:
            raise AssertionError("workflow closing marker changed")
        source = textwrap.dedent(source.split(end, 1)[0])
        WORK.mkdir(parents=True, exist_ok=True)
        cls.scratch = tempfile.TemporaryDirectory(dir=str(WORK))
        module_path = Path(cls.scratch.name) / "workflow.py"
        module_path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("reviewed_automerge", module_path)
        cls.module = importlib.util.module_from_spec(spec)
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("offline guard")):
            spec.loader.exec_module(cls.module)
        cls.module.gh = mock.Mock(side_effect=AssertionError("offline guard"))

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def setUp(self):
        self.process_guard = mock.patch.object(subprocess, "run", side_effect=AssertionError("offline guard"))
        self.process_guard.start()
        self.addCleanup(self.process_guard.stop)
        self.finding = {"status": "added", "filename": "findings/V0/2026-01-01--finder--test.md"}
        self.body = "Author: @finder\nVerified by: @tester\nLead: #1\n"

    def decide(self, files, total=None):
        return self.module.decide(files, "tester", lambda _: self.body,
                                  lambda _: {"author": "finder", "labels": ["lead"], "pr": False}, total)

    def test_file_list_completeness_and_cap(self):
        self.assertEqual(self.decide([self.finding], 1)[0], "")
        self.assertIn("could not be read in full", self.decide([self.finding], 2)[0])
        self.assertIn("could not be read in full", self.decide([self.finding] * 3000, 3000)[0])

    def test_csv_quoted_commas_and_attribution(self):
        entry = {"status": "modified", "filename": "samples/manifest.csv",
                 "patch": '+pixls,"Model, Special","@tester measured, extra"\n'}
        self.assertEqual(self.decide([entry], 1)[0], "")
        entry["patch"] = '+pixls,"Model, @tester measured",@other measured\n'
        self.assertIn("measured_by", self.decide([entry], 1)[0])

    def test_partial_links(self):
        for part in ("raw.pixls.us", "rows 1/2: V0"):
            self.body = "Author: @finder\nVerified by: @tester\nLead: #1\nPartial: " + part + "\n"
            self.assertEqual(self.decide([self.finding], 1)[0], "")
        for part in ("https://example.com/path", "example.com"):
            self.body = "Author: @finder\nVerified by: @tester\nLead: #1\nPartial: " + part + "\n"
            self.assertIn("or a link", self.decide([self.finding], 1)[0])


if __name__ == "__main__":
    unittest.main()
