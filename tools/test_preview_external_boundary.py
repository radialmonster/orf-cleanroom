#!/usr/bin/env python3
"""Generated metadata-only interval and phase-gate fixtures."""
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_external_boundary as probe


def ifd(data, offset, entries, nxt=0):
    struct.pack_into('<H', data, offset, len(entries))
    for i, entry in enumerate(entries):
        struct.pack_into('<HHII', data, offset + 2 + 12*i, *entry)
    struct.pack_into('<I', data, offset + 2 + 12*len(entries), nxt)


def fixture(declaration='exact', envelope=300, nxt=0):
    data = bytearray(1200)
    struct.pack_into('<2sHI', data, 0, b'II', 42, 8)
    entries = [(256, 4, 1, 16), (257, 4, 1, 16), (273, 4, 1, 800),
               (279, 4, 1, 100), (0x8769, 4, 1, 128)]
    if declaration == 'exact':
        entries += [(513, 4, 1, 600), (514, 4, 1, 30)]
    elif declaration == 'partial':
        entries += [(513, 4, 1, 600)]
    ifd(data, 8, entries, nxt)
    ifd(data, 128, [(0x927c, 7, envelope, 200)])
    blob = bytearray(envelope)
    blob[:12] = b'OLYMPUS\0II\x03\x00'
    ifd(blob, 12, [(0x2020, 13, 1, 64)])
    ifd(blob, 64, [(0x0101, 4, 1, 400), (0x0102, 4, 1, 30)])
    data[200:200+envelope] = blob
    return bytes(data)


class Tests(unittest.TestCase):
    def test_exact_declaration_and_signed_delta(self):
        row = probe.measure(fixture())
        self.assertEqual(row['interval']['end_minus_maker_end'], 130)
        self.assertFalse(row['interval']['contained'])
        self.assertEqual(row['declarations']['exact_count'], 1)
        self.assertEqual(row['declarations']['relation'], 'unique_exact')
        self.assertEqual(row['strips']['overlap_count'], 0)

    def test_absent_declaration_and_containment(self):
        row = probe.measure(fixture('absent', envelope=500))
        self.assertTrue(row['interval']['contained'])
        self.assertEqual(row['interval']['end_minus_maker_end'], -70)
        self.assertEqual(row['declarations']['declared'], [])
        self.assertEqual(row['declarations']['status'], 'ok')
        self.assertEqual(row['declarations']['relation'], 'no_positive_declaration')

    def test_alias_and_conflicting_declaration(self):
        data = bytearray(fixture(nxt=1000))
        ifd(data, 1000, [(513, 4, 1, 600), (514, 4, 1, 30)])
        self.assertEqual(probe.measure(bytes(data))['declarations']['relation'], 'exact_aliases')
        ifd(data, 1000, [(513, 4, 1, 600), (514, 4, 1, 31)])
        self.assertEqual(probe.measure(bytes(data))['declarations']['relation'], 'exact_with_conflict')

    def test_partial_declaration_unknown_independently(self):
        row = probe.measure(fixture('partial'))
        self.assertEqual(row['declarations']['status'], 'unknown')
        self.assertEqual(row['strips']['status'], 'ok')

    def test_ambiguous_and_malformed_graph(self):
        data = bytearray(fixture('absent', nxt=1000))
        ifd(data, 1000, [(273, 4, 1, 900), (279, 4, 1, 100)])
        row = probe.measure(bytes(data))
        self.assertEqual(row['strips']['reason'], 'ambiguous_strip_ifd')
        row = probe.measure(fixture('absent', nxt=1199))
        self.assertEqual(row['declarations']['status'], 'unknown')
        self.assertEqual(row['strips']['status'], 'unknown')

    def test_replay_gate_before_reserved(self):
        ids = probe.DISCOVERY + probe.EXTENSION
        contents = {sid: fixture() for sid in ids}
        samples = {sid: ('name' + sid, hashlib.sha256(contents[sid]).hexdigest()) for sid in ids}
        opened, frozen = [], [None]
        def fake_open(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(frozen[0]) if path == 'frozen' else io.BytesIO(contents[path])
        def argv(phase):
            result = ['probe', '--phase', phase]
            if phase == 'verification':
                result += ['--frozen', 'frozen']
            for sid in (ids if phase == 'verification' else ids[:3]):
                result += ['--sample', sid, sid]
            return result
        with mock.patch.object(probe, 'SAMPLES', samples), mock.patch.object(probe, 'open', fake_open, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            previous = json.loads(out.getvalue())
            previous['samples'][0]['interval']['maker_end'] += 1
            frozen[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')):
                with self.assertRaisesRegex(SystemExit, 'discovery_mismatch'):
                    probe.main()
            self.assertNotIn('2431', opened)


if __name__ == '__main__':
    unittest.main()
