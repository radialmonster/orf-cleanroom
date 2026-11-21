#!/usr/bin/env python3
"""Synthetic coverage, privacy and frozen-phase controls."""
import contextlib
import hashlib
import io
import json
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_locator_cohort as probe
from test_preview_relative_locator import make_candidate


class Tests(unittest.TestCase):
    def test_published_roster_pin_and_partition(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'findings', 'container',
                            '2026-10-27--radialmonster--capture-metadata-104-cohort.md')
        with open(path, encoding='utf-8') as f:
            rows = probe.roster(f.read())
        self.assertEqual(len(rows), 104)
        self.assertEqual(sum(r[0] not in probe.RESERVED for r in rows), 97)
        self.assertEqual({r[0] for r in rows if r[0] in probe.RESERVED}, probe.RESERVED)
        with self.assertRaisesRegex(ValueError, 'roster_mismatch'):
            probe.roster('')

    def test_identity_conflicts_and_size_class(self):
        record = ('1', 'public.ORF', 'a' * 64)
        inventory = [{'id': '1', 'name': 'public.ORF', 'sha256': 'a' * 64,
                      'licence': 'CC0', 'local_name': '1_public.ORF'}]
        manifest = [{'source': 'pixls', 'pixls_id': '1', 'pixls_name': 'public.ORF',
                     'sha256': 'a' * 64, 'licence': 'CC0', 'size_class': 'variable'}]
        self.assertEqual(probe.identity(record, inventory, manifest)[1:], ('variable', None))
        without_local = [dict(inventory[0])]
        del without_local[0]['local_name']
        self.assertEqual(probe.identity(record, without_local, manifest)[0], '1_public.ORF')
        without_local[0]['local_name'] = '../escape'
        self.assertEqual(probe.identity(record, without_local, manifest)[2], 'inventory_local_name')
        manifest.append(dict(manifest[0], size_class='packed-12'))
        self.assertEqual(probe.identity(record, inventory, manifest)[1], 'unknown')
        inventory.append(dict(inventory[0], licence='restricted'))
        self.assertEqual(probe.identity(record, inventory, manifest)[2], 'inventory_identity')

    def test_missing_path_privacy(self):
        record = ('1', 'public.ORF', 'a' * 64)
        inventory = [{'id': '1', 'name': 'public.ORF', 'sha256': 'a' * 64,
                      'licence': 'CC0', 'local_name': '1_public.ORF'}]
        manifest = [{'source': 'pixls', 'pixls_id': '1', 'pixls_name': 'public.ORF',
                     'sha256': 'a' * 64, 'licence': 'CC0', 'size_class': 'variable'}]
        with mock.patch.object(probe, 'open', side_effect=OSError('private/path'), create=True):
            row = probe.run_one(record, inventory, manifest, 'private/path')
        self.assertEqual(row['candidate']['status'], 'unknown')
        self.assertNotIn('private/path', json.dumps(row))

    def test_candidate_valid_scanner_unknown_counted(self):
        rows = [{'candidate': {'status': 'ok'}, 'scanner': {'status': 'unknown'}, 'relation': 'unknown'}]
        self.assertEqual(probe.summarize(rows), [{'candidate': 'ok', 'scanner': 'unknown', 'relation': 'unknown', 'count': 1}])

    def test_resolved_path_escape_is_unknown_without_open(self):
        record = ('1', 'public.ORF', 'a' * 64)
        inventory = [{'id': '1', 'name': 'public.ORF', 'sha256': 'a' * 64,
                      'licence': 'CC0', 'local_name': '1_public.ORF'}]
        manifest = [{'source': 'pixls', 'pixls_id': '1', 'pixls_name': 'public.ORF',
                     'sha256': 'a' * 64, 'licence': 'CC0', 'size_class': 'variable'}]
        root, entry, target = mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        root.__truediv__.return_value = entry
        entry.resolve.return_value = target
        target.parent = object()
        with mock.patch.object(probe, 'Path') as path, mock.patch.object(probe, 'open', create=True) as opened:
            path.return_value.resolve.return_value = root
            row = probe.run_one(record, inventory, manifest, 'private')
        self.assertEqual(row['candidate']['reason'], 'outside_corpus')
        opened.assert_not_called()

    def test_generated_tiff_single_snapshot(self):
        data = make_candidate()
        digest = hashlib.sha256(data).hexdigest()
        record = ('1', 'public.ORF', digest)
        inventory = [{'id': '1', 'name': 'public.ORF', 'sha256': digest,
                      'licence': 'CC0', 'local_name': '1_public.ORF'}]
        manifest = [{'source': 'pixls', 'pixls_id': '1', 'pixls_name': 'public.ORF',
                     'sha256': digest, 'licence': 'CC0', 'size_class': 'variable'}]
        root, entry, target = mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        root.__truediv__.return_value = entry
        entry.resolve.return_value = target
        target.parent = root
        with mock.patch.object(probe, 'Path') as path, mock.patch.object(probe, 'open', return_value=io.BytesIO(data), create=True) as opened:
            path.return_value.resolve.return_value = root
            row = probe.run_one(record, inventory, manifest, 'private')
        self.assertEqual((row['candidate']['status'], row['scanner']['status'], row['relation']), ('ok', 'ok', 'match'))
        opened.assert_called_once()

    def test_frozen_gate_stops_reserved(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'findings', 'container',
                            '2026-10-27--radialmonster--capture-metadata-104-cohort.md')
        with open(path, encoding='utf-8') as f:
            text = f.read()
        entries = probe.roster(text)
        opened = []
        frozen = [None]
        def fake_open(name, mode='r', **kwargs):
            if name == 'roster':
                return io.StringIO(text)
            if name == 'inventory':
                return io.BytesIO(b'{"files":[]}')
            if name == 'manifest':
                return io.BytesIO(b'source,pixls_id\n')
            if name == 'frozen':
                return io.StringIO(frozen[0])
            raise AssertionError('unexpected file')
        def fake_run(record, *args):
            opened.append(record[0])
            return {'id': record[0], **probe.unknown('synthetic')}
        def argv(phase):
            result = ['probe', '--phase', phase, '--inventory', 'inventory', '--corpus', 'private',
                      '--manifest', 'manifest', '--roster', 'roster']
            return result + (['--frozen', 'frozen'] if phase == 'verification' else [])
        with mock.patch.object(probe, 'open', fake_open, create=True), mock.patch.object(probe, 'run_one', fake_run):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 1)
            previous = json.loads(out.getvalue())
            frozen[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(), 1)
            self.assertEqual(len(opened), 104)
            self.assertTrue(probe.RESERVED.issubset(opened))
            previous['samples'][0]['id'] = 'changed'
            frozen[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    probe.main()
            self.assertEqual(len(opened), 97)
            self.assertTrue(probe.RESERVED.isdisjoint(opened))


if __name__ == '__main__':
    unittest.main()
