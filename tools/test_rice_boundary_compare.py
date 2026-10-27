import itertools
import contextlib
import io
import json
import random
from unittest import mock
import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rice_boundary_compare as tool


def reference(bits):
    lists = []
    for k in (4, 5):
        p = 0
        out = []
        while p < len(bits):
            q = p
            while q < len(bits) and bits[q] == '0':
                q += 1
            if q + 1 + k > len(bits):
                break
            p = q + 1 + k
            out.append(p)
        lists.append(out)
    common = sorted(set(lists[0]) & set(lists[1]))
    previous = 0
    spans = []
    words = [0, 0]
    for x in common:
        spans.append(x - previous)
        for i in range(2):
            words[i] += sum(previous < e <= x for e in lists[i])
        previous = x
    return lists, common, spans, words


class BoundaryTests(unittest.TestCase):
    def test_literal_oracle(self):
        for n in range(13):
            for x in itertools.product('01', repeat=n):
                bits = ''.join(x)
                a, common, spans, words = reference(bits)
                got = tool.compare(bits)
                self.assertEqual(got['positive_shared'], len(common))
                self.assertEqual(got['last_shared'], common[-1] if common else None)
                self.assertEqual(got['intervals']['span_sum'], sum(spans))
                self.assertEqual(got['intervals']['span_max'], max(spans) if spans else None)
                self.assertEqual(got['intervals']['word_counts'], words)
                self.assertEqual(sum(b['count'] for b in got['intervals']['bins']), len(common))
                for i in range(2):
                    end = a[i][-1] if a[i] else 0
                    self.assertEqual(got['parses'][i]['words'], len(a[i]))
                    self.assertEqual(got['parses'][i]['last_endpoint'], end)
                    self.assertEqual(got['parses'][i]['residual_bits'], n - end)
                    self.assertEqual(got['parses'][i]['open_tail_words'], sum(v > (common[-1] if common else 0) for v in a[i]))

    def test_period_and_incomplete(self):
        r = tool.compare('1' * 63)
        self.assertEqual(r['positive_shared'], 2)
        self.assertEqual(r['intervals']['span_sum'], 60)
        self.assertEqual(r['intervals']['word_counts'], [12, 10])
        self.assertEqual([p['residual_bits'] for p in r['parses']], [3, 3])
        self.assertEqual(tool.compare('0' * 20)['intervals']['mean_span'], None)

    def test_edges_and_open_tail(self):
        result = tool.compare('1' * 63)
        self.assertEqual(result['intervals']['bins'][0]['count'], 2)
        self.assertEqual(result['parses'][0]['open_tail_words'], 0)
        self.assertEqual(result['parses'][1]['open_tail_bits'], 0)
        tail = tool.compare('1' * 35)
        self.assertEqual([x['open_tail_words'] for x in tail['parses']], [1, 0])
        self.assertEqual(tool.compare('0' * 20)['intervals']['bins'], [])

    def test_cli_shuffles_whole_before_prefix(self):
        payload = bytes(range(20))
        shuffled = bytearray(payload)
        random.Random(20261022).shuffle(shuffled)
        expected = tool.compare(''.join(format(b, '08b') for b in shuffled[:4]))
        output = io.StringIO()
        with mock.patch('builtins.open', mock.mock_open(read_data=b'container')), \
             mock.patch.object(tool.orf_tokens, 'locate_data', return_value=(4, 5, payload)), \
             contextlib.redirect_stdout(output):
            self.assertEqual(tool.main(['sample', '--prefix-bytes', '4', '--shuffle']), 0)
        actual = json.loads(output.getvalue())
        for key in expected:
            self.assertEqual(actual[key], expected[key])
        prefix_only = bytearray(payload[:4])
        random.Random(20261022).shuffle(prefix_only)
        self.assertNotEqual(shuffled[:4], prefix_only)

    def test_mixed(self):
        bits = '001101001011000100111001011101' * 9
        a, common, spans, words = reference(bits)
        result = tool.compare(bits)
        self.assertEqual(result['positive_shared'], len(common))
        self.assertEqual(result['intervals']['word_counts'], words)
        self.assertEqual(result['intervals']['span_sum'], sum(spans))


if __name__ == '__main__':
    unittest.main()
