#!/usr/bin/env python3
"""Coverage bookkeeping and reserved-read controls for the cohort experiment."""
import contextlib
import io
import json
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import om_system_preview_cohort as p


def valid(start=100):
    return dict(status='ok', offset=start, length=30, width=1600, height=1200)


class Tests(unittest.TestCase):
    def test_single_metadata_rule_without_scanner(self):
        unknown = {'status': 'unknown'}
        for name, old, new in (('olympus', valid(), unknown), ('om_system', unknown, valid())):
            combined = p.combine(old, new)
            self.assertEqual(combined['rule'], name)
            self.assertEqual(p.relation(combined, valid()), 'match')
            self.assertEqual(p.relation(combined, valid(200)), 'mismatch')
            self.assertEqual(p.relation(combined, unknown), 'unknown')

    def test_contradictions_and_rule_overlap_are_never_rescued(self):
        bad = {'status': 'contradiction'}
        for old, new in ((bad, valid()), (valid(), bad), (bad, {'status':'unknown'}), (valid(), valid())):
            self.assertEqual(p.combine(old, new)['status'], 'contradiction')

    def test_unknown_metadata_is_not_scanner_success(self):
        result = p.combine({'status':'unknown'}, {'status':'unknown'})
        self.assertEqual(result['reason'], 'no_supported_layout')
        self.assertEqual(p.relation(result, valid()), 'unknown')

    def test_denominator_keeps_every_status(self):
        rows = []
        for state, rel in (('ok','match'), ('ok','mismatch'), ('unknown','unknown'), ('contradiction','unknown')):
            rows.append({**{k:{'status':state} for k in ('olympus','om_system','combined')},
                         'scanner':{'status':'ok'}, 'relations':{k:rel for k in ('olympus','om_system','combined')}})
        for cells in p.counts(rows).values():
            self.assertEqual(sum(cell['count'] for cell in cells), 4)

    def test_changed_discovery_prevents_every_reserved_measurement(self):
        ids = [str(i) for i in range(1, 97)]+sorted(p.RESERVED, key=int)
        roster = [(sid,'public','a'*64) for sid in ids]
        calls, saved = [], [None]
        def read(path, mode='r', **kwargs):
            if path == 'manifest':
                return io.BytesIO(b'header\n')
            return io.StringIO(saved[0] if path == 'frozen' else ('[]' if path == 'inventory' else 'roster'))
        def run(record, *args):
            calls.append(record[0])
            return {'id':record[0], 'input_status':'ok', 'combined':valid(), 'olympus':valid(),
                    'om_system':{'status':'unknown'}, 'scanner':valid(),
                    'relations':{'olympus':'match','om_system':'unknown','combined':'match'}}
        def argv(phase):
            return ['probe','--phase',phase,'--roster','roster','--inventory','inventory',
                    '--manifest','manifest','--corpus','corpus']+(['--frozen','frozen'] if phase=='verification' else [])
        with mock.patch.object(p.cohort,'roster',return_value=roster), mock.patch.object(p,'open',read,create=True), mock.patch.object(p,'run_one',run):
            out = io.StringIO()
            with mock.patch.object(sys,'argv',argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(p.main(), 0)
            report = json.loads(out.getvalue())
            self.assertEqual(len(calls), 96)
            report['samples'][0]['combined']['offset'] += 1
            saved[0] = json.dumps(report)
            calls.clear()
            with mock.patch.object(sys,'argv',argv('verification')):
                with self.assertRaisesRegex(ValueError,'discovery_mismatch'):
                    p.main()
            self.assertFalse(p.RESERVED.intersection(calls))


if __name__ == '__main__':
    unittest.main()
