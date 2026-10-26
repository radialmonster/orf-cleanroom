"""Synthetic checks for the optional Partial finding header."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work' / 'test-findings-partial'
sys.path.insert(0, str(ROOT / 'tools'))
import findings_index as index


def text(partial):
    return ('# Synthetic finding\n\nAuthor: @tester\nVerified by: @tester\n'
            'Lead: #1\nVariant: container\n' + partial + '\n'
            '## Claim\n\nSynthetic.\n## Original evidence\n\nSynthetic.\n'
            '## Verification\n\nSynthetic.\n## Reproduce\n\nSynthetic.\n')


class PartialHeader(unittest.TestCase):
    def test_empty_partial_is_rejected_and_scoped_or_absent_are_valid(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            dest = Path(folder) / 'findings' / 'container'
            dest.mkdir(parents=True)
            file = dest / '2026-01-01--tester--synthetic.md'
            for partial, valid in (('', True), ('Partial: rows only\n', True),
                                   ('Partial:\n', False), ('Partial:   \n', False)):
                with self.subTest(partial=partial):
                    file.write_text(text(partial), encoding='utf-8')
                    found, errors = {}, []
                    index.scan(folder, found, errors)
                    index.resolve(found, errors)
                    self.assertEqual(not errors, valid, errors)
                    if not valid:
                        self.assertTrue(any('Partial' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
