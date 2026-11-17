"""Synthetic checks of origin mapping and unknown-preserving intersections."""
import os
import sys
import unittest
from unittest import mock
import contextlib
import hashlib
import io
import json
import struct
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_anchor_origin as probe
import free_anchor_origin_summary as summary


class Synthetic(unittest.TestCase):
    def test_generated_tiff_full_grid_and_shortfall(self):
        bits = '100000' * 15
        payload = int(bits + '0' * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, 'big')
        tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
        data = (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                + struct.pack('<I', 0) + payload)
        real_open = open
        def open_fixture(path, *args, **kwargs):
            return io.BytesIO(data) if path == 'fixture' else real_open(path, *args, **kwargs)
        output = io.StringIO()
        with mock.patch.object(probe, 'WINDOW', 4), mock.patch.object(probe, 'STARTS', (0, 4, 8, 12)), \
             mock.patch.object(sys, 'argv', ['probe', '--sample', '1', 'public.ORF', 'fixture']), \
             mock.patch('builtins.open', side_effect=open_fixture), contextlib.redirect_stdout(output):
            status = probe.main()
        result = json.loads(output.getvalue())['sample']
        self.assertEqual(status, 1)
        self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual([w['returned_tokens'] for w in result['windows']], [4, 4, 4, 3])
        for window in result['windows']:
            self.assertEqual(sum(len(f['cases']) for f in window['families']), 128)
        self.assertTrue(all(c['status'] == 'short' for f in result['windows'][-1]['families'] for c in f['cases']))

    def test_alphabets(self):
        for mapping, origins in probe.ORIGINS.items():
            self.assertEqual((min(probe.mapped(s, mapping) for s in range(32)),
                              max(probe.mapped(s, mapping) for s in range(32))),
                             (min(origins), max(origins)))

    def test_unknown_does_not_eliminate_origin(self):
        ok = lambda passes: {'status': 'ok', 'passes': passes}
        unknown = {'status': 'timeout', 'passes': None}
        windows = [{0: ok(False), 1: ok(True), 2: unknown},
                   {0: unknown, 1: unknown, 2: ok(True)}]
        self.assertEqual(probe.summarize((0, 1, 2), windows),
                         {'possible': [1, 2], 'complete_pass': [], 'conclusion': 'not_rejected'})
        self.assertEqual(probe.summarize((0,), [{0: ok(False)}, {0: unknown}])['conclusion'], 'rejected')
        self.assertEqual(probe.summarize((0,), [{0: unknown}]),
                         {'possible': [0], 'complete_pass': [], 'conclusion': 'undefined'})
        self.assertEqual(probe.summarize((0,), [{0: ok(True)}])['complete_pass'], [0])
        self.assertEqual(probe.summarize((0,), [{0: ok(True)}, {0: {'status': 'escape', 'passes': None}}])['complete_pass'], [0])
        self.assertEqual(probe.summarize((0,), [{0: {'status': 'escape', 'passes': None}}]),
                         {'possible': [0], 'complete_pass': [], 'conclusion': 'undefined'})

    def test_short_escape_and_origin_zero(self):
        self.assertEqual(probe.case([], 4, 16, 'signed_low3', 1, 0)['status'], 'short')
        self.assertEqual(probe.case([(17, 0)] * 4, 4, 16, 'signed_low3', 1, 0)['status'], 'escape')
        tokens = [(0, s) for s in (0, 1, 2, 3, 4)]
        for mapping in probe.ORIGINS:
            for stride in (1, 2):
                result = probe.case(tokens, 5, 12, mapping, stride, 0)
                values = [probe.mapped(s, mapping) for _, s in tokens]
                self.assertEqual(result['segments'], [probe.segments(values[i::stride], 4095) for i in range(stride)])

    def test_known_lane_failure_dominates_timeout(self):
        tokens = [(0, 0)] * 4
        with mock.patch.object(probe, 'segments', side_effect=[3, TimeoutError()]):
            result = probe.case(tokens, 4, 12, 'signed_low3', 2, 0)
        self.assertEqual(result['segments'], [3, None])
        self.assertEqual(result['lane_status'], ['ok', 'timeout'])
        self.assertIs(result['passes'], False)
        self.assertEqual(probe.summarize((0,), [{0: result}])['conclusion'], 'rejected')
        with mock.patch.object(probe, 'segments', side_effect=[2, TimeoutError()]):
            result = probe.case(tokens, 4, 12, 'signed_low3', 2, 0)
        self.assertIsNone(result['passes'])
        self.assertEqual(probe.summarize((0,), [{0: result}])['possible'], [0])
        with mock.patch.object(probe.time, 'monotonic', return_value=10):
            self.assertEqual(probe.case(tokens, 4, 12, 'signed_low3', 1, 0, file_deadline=10)['status'], 'file_budget_not_run')
        with mock.patch.object(probe.time, 'monotonic', side_effect=[0, 10]), \
             mock.patch.object(probe, 'segments', side_effect=TimeoutError()):
            self.assertEqual(probe.case(tokens, 4, 12, 'signed_low3', 1, 0, file_deadline=10)['status'], 'file_timeout')

    def test_frozen_possible_never_reintroduces_and_unknown_new(self):
        def report(status_for):
            families = []
            for bits in (16, 12):
                for mapping, origins in probe.ORIGINS.items():
                    for stride in (1, 2):
                        cases = [{'origin': c, **status_for(c)} for c in origins]
                        families.append({'bits': bits, 'mapping': mapping, 'stride': stride, 'cases': cases})
            return {'sample': {'windows': [{'families': families}]}}
        ok = lambda c: {'status': 'ok', 'passes': c != 0}
        unknown = lambda c: {'status': 'timeout', 'passes': None}
        initial = report(ok)
        late = report(unknown)
        for result in probe.summarize_stages([initial], [late]):
            self.assertNotIn(0, result['discovery']['possible'])
            self.assertNotIn(0, result['combined_restricted']['possible'])
            self.assertEqual(result['combined_restricted']['conclusion'], 'undefined')
            self.assertEqual(result['combined_restricted']['complete_pass'], [])

    def test_window_status_counts_keep_mixed_unknown(self):
        family = {'bits': 16, 'mapping': 'signed_low3', 'stride': 2,
                  'cases': [{'status': 'timeout', 'passes': False}, {'status': 'timeout', 'passes': None}]}
        report = {'sample': {'windows': [{'families': [family]}]}}
        cases, windows = summary.status_counts(report)
        self.assertEqual(cases, {'timeout': 2})
        self.assertEqual(windows['signed_low3/B16/d2']['partly_adjudicated'], 1)

    def test_missing_file_stays_unknown_and_no_new_evidence(self):
        discovery = summary.missing_report('1993')
        verification = summary.missing_report('1995')
        for result in probe.summarize_stages([discovery], [verification]):
            self.assertEqual(result['discovery']['conclusion'], 'undefined')
            self.assertEqual(result['combined_restricted']['conclusion'], 'undefined')
            self.assertEqual(result['discovery']['possible'], list(probe.ORIGINS[result['mapping']]))
            self.assertEqual(result['combined_restricted']['complete_pass'], [])
        completed = summary.complete_fixed([], ('1993', '5283'))
        self.assertEqual([report['sample']['pixls_id'] for _, report in completed], ['1993', '5283'])
        self.assertTrue(all(digest is None for digest, _ in completed))
        valid = summary.missing_report('1993')
        with self.assertRaises(ValueError):
            summary.complete_fixed([('a', valid), ('b', valid)], ('1993', '5283'))
        valid['sample']['sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            summary.complete_fixed([('a', valid)], ('1993', '5283'))


def pilot():
    """Synthetic-only full fixed grid; no sample files."""
    start = time.monotonic()
    deadline = start + 570
    tokens = [(0, 0)] * 4096
    counts = {}
    for _ in range(4):
        for bits in (16, 12):
            for name, origins in probe.ORIGINS.items():
                for stride in (1, 2):
                    for origin in origins:
                        result = probe.case(tokens, 4096, bits, name, stride, origin,
                                            min(time.monotonic() + 20, deadline), deadline)
                        counts[result['status']] = counts.get(result['status'], 0) + 1
    print(json.dumps({'scope': 'synthetic constant suffix zero full grid',
                      'seconds': time.monotonic() - start, 'statuses': counts}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--pilot']:
        pilot()
    else:
        unittest.main()
