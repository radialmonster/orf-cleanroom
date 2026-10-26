#!/usr/bin/env python3
"""Independent hand arithmetic and malformed aggregate controls."""
import copy
import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body_label_holdout as probe


class Tests(unittest.TestCase):
    def test_training_only_scaling_and_distances(self):
        rows = [{'pixls_id': str(i), 'body': (label, ''), 'features': [x, 7]}
                for i, (label, x) in enumerate([('A', 0), ('A', 2), ('B', 10), ('B', 12)])]
        fold = probe.classify(rows, (0, 1))['folds'][0]
        # Training 2,10,12: mean 8, population variance 56/3.
        self.assertEqual(fold['training_means'], [8, 7])
        self.assertEqual(fold['training_population_variances'], [56 / 3, 0])
        self.assertAlmostEqual(fold['distances'][0]['squared_distance'], 3 / 14)
        self.assertAlmostEqual(fold['distances'][1]['squared_distance'], 363 / 56)
        self.assertEqual(fold['predicted'], ('A', ''))

    def test_ties_singletons_and_zero_variance(self):
        rows = [{'pixls_id': str(i), 'body': (label, ''), 'features': [1]}
                for i, label in enumerate(['Z', 'B', 'A'])]
        result = probe.classify(rows, (0,))
        self.assertEqual(result['target_absent_folds'], 3)
        self.assertEqual(result['folds'][0]['predicted'], ('A', ''))
        self.assertEqual(result['folds'][0]['active_features'], [])
        self.assertEqual(result['correct'], 0)

    def test_nearest_centroid_not_nearest_member(self):
        rows = [{'pixls_id': str(i), 'body': (label, ''), 'features': [x]}
                for i, (label, x) in enumerate([('T', 0), ('A', -1), ('A', 101), ('B', 5)])]
        self.assertEqual(probe.classify(rows, (0,))['folds'][0]['predicted'], ('B', ''))

    def fixture(self):
        samples, manifest = [], []
        for key in ('1', '2', '3'):
            digest = key * 64
            samples.append({'pixls_id': key, 'pixls_name': key, 'sha256': digest,
                'size_class': 'variable', 'payload_width': 100, 'payload_height': 100,
                'payload_bytes': 196608, 'payload_bits_per_pixel': 196608 * 8 / 10000,
                'windows': [{'payload_byte_start': start, 'features': {'bytes': 65536,
                    'one_fraction': 0.5, 'transition_fraction': 0.5, 'byte_entropy_bits': 8}}
                    for start in (0, 65536, 131072)]})
            manifest.append({'pixls_id': key, 'pixls_name': key, 'sha256': digest,
                'make': 'M', 'model': key, 'licence': 'CC0', 'source': 'pixls',
                'payload_w': '100', 'payload_h': '100'})
        return {'schema': 'raw-bit-window-features-v1', 'window_count': 3,
                'window_bytes': 65536, 'samples': samples, 'errors': []}, manifest

    def test_cohort_and_manifest_duplicate(self):
        report, manifest = self.fixture()
        self.assertEqual(len(probe.cohort(report, manifest + manifest, ['1', '2', '3'])), 3)
        manifest[0]['model'] = 'conflict'
        with self.assertRaises(ValueError):
            probe.cohort(report, manifest + self.fixture()[1], ['1', '2', '3'])

    def test_invalid_inputs(self):
        for change in ('hash', 'window', 'infinite', 'identity', 'error', 'duplicate', 'coordinates', 'bpp'):
            report, manifest = copy.deepcopy(self.fixture())
            row = report['samples'][0]
            if change == 'hash':
                row['sha256'] = '0' * 64
            elif change == 'window':
                row['windows'].pop()
            elif change == 'infinite':
                row['windows'][0]['features']['one_fraction'] = float('inf')
            elif change == 'identity':
                manifest[0]['licence'] = 'unknown'
            elif change == 'error':
                report['errors'] = [{'pixls_id': '1'}]
            elif change == 'duplicate':
                report['samples'].append(row)
            elif change == 'coordinates':
                row['windows'][1]['payload_byte_start'] = 17
            else:
                row['payload_bits_per_pixel'] = 8
            with self.subTest(change=change), self.assertRaises(ValueError):
                probe.cohort(report, manifest, ['1', '2', '3'])

    def test_matching_invalid_digest_is_rejected(self):
        report, manifest = self.fixture()
        report['samples'][0]['sha256'] = 'not-a-sha256'
        manifest[0]['sha256'] = 'not-a-sha256'
        with self.assertRaises(ValueError):
            probe.cohort(report, manifest, ['1', '2', '3'])

    def test_geometry_conflict_with_manifest_is_rejected(self):
        for field in ('payload_width', 'payload_height'):
            report, manifest = self.fixture()
            sample = report['samples'][0]
            sample[field] = 200
            sample['payload_bits_per_pixel'] = sample['payload_bytes'] * 8 / 20000
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.cohort(report, manifest, ['1', '2', '3'])

    def test_blank_manifest_geometry_is_not_a_conflict(self):
        report, manifest = self.fixture()
        manifest[0]['payload_w'] = manifest[0]['payload_h'] = ''
        del manifest[1]['payload_w']
        del manifest[1]['payload_h']
        self.assertEqual(len(probe.cohort(report, manifest, ['1', '2', '3'])), 3)

    def test_conflicting_duplicate_manifest_geometry_is_rejected(self):
        for field in ('payload_w', 'payload_h'):
            report, manifest = self.fixture()
            conflicting = dict(manifest[0], **{field: '200'})
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.cohort(report, manifest + [conflicting], ['1', '2', '3'])

    def test_non_numeric_public_id_is_rejected(self):
        report, manifest = self.fixture()
        report['samples'][0]['pixls_id'] = 'not-a-public-id'
        manifest[0]['pixls_id'] = 'not-a-public-id'
        with self.assertRaises(ValueError):
            probe.cohort(report, manifest, ['not-a-public-id', '2', '3'])

    def test_cli_rejects_non_object_report(self):
        error = io.StringIO()
        with patch('builtins.open', side_effect=[io.BytesIO(b'[]'), io.BytesIO(b'pixls_id\n')]):
            with contextlib.redirect_stderr(error):
                self.assertEqual(probe.main(['--features', 'x', '--manifest', 'y', '--ids', '1', '2', '3']), 1)
        self.assertIn('invalid diagnostic input', error.getvalue())


if __name__ == '__main__':
    unittest.main()
