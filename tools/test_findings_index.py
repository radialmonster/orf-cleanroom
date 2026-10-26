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
    def test_correction_cycles_rejected_and_chain_retained(self):
        WORK.mkdir(parents=True, exist_ok=True)
        for edges in ((1, 0), (1, 2, 0), (None, 0, 1)):
            with self.subTest(edges=edges), tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
                dest = Path(folder) / 'findings' / 'container'
                dest.mkdir(parents=True)
                ids = ['2026-01-01--tester--item%d' % n for n in range(len(edges))]
                for fid, target in zip(ids, edges):
                    content = finding('container')
                    if target is not None:
                        content = content.replace('Variant: container\n',
                                                  'Variant: container\nCorrects: %s\n' % ids[target])
                    (dest / (fid + '.md')).write_text(content, encoding='utf-8')
                found, errors = {}, []
                index.scan(folder, found, errors)
                index.resolve(found, errors)
                if edges[0] is None:
                    self.assertEqual(errors, [])
                    self.assertEqual([index.statuses(found)[fid][0] for fid in ids],
                                     ['superseded', 'superseded', 'self-verified'])
                else:
                    self.assertTrue(any('circular' in error.lower() for error in errors), errors)

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

    def test_repeated_reproducer_of_same_finding_is_not_a_new_verifier(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(WORK)) as folder:
            dest = Path(folder) / 'findings' / 'container'
            dest.mkdir(parents=True)
            target = '2026-01-01--tester--original'
            (dest / (target + '.md')).write_text(finding('container'), encoding='utf-8')
            for n, verifier in ((2, 'bob'), (3, 'BoB')):
                body = finding('container').replace('Verified by: @tester', 'Verified by: @' + verifier)
                body = body.replace('Variant: container\n', 'Variant: container\nReproduces: ' + target + '\n')
                (dest / ('2026-01-0%d--tester--reproduction.md' % n)).write_text(body, encoding='utf-8')
            found, errors = {}, []
            index.scan(folder, found, errors)
            index.resolve(found, errors)
            self.assertTrue(any('already verified' in error for error in errors), errors)
            # A different human verifier is allowed and contributes separate credit.
            latest = dest / '2026-01-03--tester--reproduction.md'
            latest.write_text(latest.read_text(encoding='utf-8').replace('@BoB', '@charlie'), encoding='utf-8')
            found, errors = {}, []
            index.scan(folder, found, errors)
            index.resolve(found, errors)
            self.assertEqual(errors, [])
            self.assertEqual(set(index.statuses(found)[target][2]), {'bob', 'charlie'})

    def test_reproduction_reference_rejects_unknown_self_and_mismatched_credit(self):
        target_id = '2026-01-01--tester--original'
        for defect in ('missing', 'self', 'author', 'lead', 'prior-verifier'):
            with self.subTest(defect=defect):
                target = index.Finding(target_id, 'container', 'original', 'tester', 'Original', 'alice', '#1')
                repro = index.Finding('2026-01-02--tester--again', 'container', 'again',
                                      'other' if defect == 'author' else 'tester', 'Again',
                                      'alice' if defect == 'prior-verifier' else 'bob',
                                      '#2' if defect == 'lead' else '#1')
                repro.reproduces = ('2026-01-01--tester--missing' if defect == 'missing' else
                                    repro.id if defect == 'self' else target_id)
                errors = []
                index.resolve({target.id: target, repro.id: repro}, errors)
                self.assertTrue(errors, defect)

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
