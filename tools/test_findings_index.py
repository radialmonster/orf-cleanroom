"""Synthetic finding-index identity checks."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work' / 'test-findings-index'
sys.path.insert(0, str(ROOT / 'tools'))
import findings_index as index


def finding(folder):
    return ('# Synthetic finding\n\nAuthor: @tester\nVerified by: @tester\n'
            'Lead: #1\nVariant: %s\n\n## Claim\n\nSynthetic.\n'
            '## Original evidence\n\nSynthetic.\n## Verification\n\nSynthetic.\n'
            '## Reproduce\n\nSynthetic.\n' % folder)


class FindingIds(unittest.TestCase):
    def test_distinct_ids_across_folders_are_retained(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            base = Path(folder) / 'findings'
            for variant in ('container', 'V0'):
                dest = base / variant
                dest.mkdir(parents=True)
                (dest / ('2026-01-01--tester--' + variant.lower() + '.md')).write_text(
                    finding(variant), encoding='utf-8')
            found, errors = {}, []
            index.scan(folder, found, errors)
            index.resolve(found, errors)
            self.assertEqual(errors, [])
            self.assertEqual(len(found), 2)

    def test_duplicate_id_across_folders_fails_check(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            base = Path(folder) / 'findings'
            for variant in ('container', 'V0'):
                dest = base / variant
                dest.mkdir(parents=True)
                (dest / '2026-01-01--tester--same.md').write_text(finding(variant), encoding='utf-8')
            output = io.StringIO()
            with patch.object(sys, 'argv', ['findings_index', '--root', folder, '--check']), \
                 contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    index.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertIn('duplicate', output.getvalue().lower())
            self.assertIn('container', output.getvalue())
            self.assertIn('V0', output.getvalue())
            found, errors = {}, []
            index.scan(folder, found, errors)
            self.assertEqual(len(found), 1)
            self.assertEqual(len(errors), 1)


if __name__ == '__main__':
    unittest.main()
