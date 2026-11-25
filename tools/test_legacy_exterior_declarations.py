import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct
import unittest
import legacy_exterior_declarations as probe


def fixture(entries, target=(300, 336)):
    data = bytearray(600)
    data[:8] = b'II\x2a\x00\x08\x00\x00\x00'
    struct.pack_into('<H', data, 8, len(entries))
    for i, (tag, typ, count, value) in enumerate(entries):
        struct.pack_into('<HHII', data, 10 + 12*i, tag, typ, count, value)
    return bytes(data), target


class TestExterior(unittest.TestCase):
    def test_header_intersection_is_counted_without_parsing_it(self):
        data, target = fixture([], (4, 10))
        r = probe.audit(data, target)
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['issues'], ['header_target_overlap'])
        self.assertEqual(r['union_overlap_bytes'], 4)
        self.assertEqual(r['overlaps'][0]['kind'], 'header')

    def test_union_and_makernote_exclusion(self):
        data, target = fixture([(100, 1, 20, 290), (101, 1, 20, 310),
                                (0x927c, 7, 100, 300)])
        r = probe.audit(data, target)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['union_overlap_bytes'], 30)
        self.assertEqual([x['tag'] for x in r['overlaps']], [100, 101])

    def test_pointer_array_in_target_is_not_read(self):
        data, target = fixture([(330, 4, 2, 300), (100, 1, 12, 310)])
        r = probe.audit(data, target)
        self.assertEqual(r['status'], 'unknown')
        self.assertIn('link_target_overlap', r['issues'])
        self.assertEqual(r['union_overlap_bytes'], 20)
        self.assertEqual(len(r['overlaps']), 2)

    def test_directory_count_in_target(self):
        data, target = fixture([(330, 4, 1, 300)])
        r = probe.audit(data, target)
        self.assertEqual(r['status'], 'unknown')
        self.assertIn('directory_target_overlap', r['issues'])
        self.assertEqual(r['visited_ifds'], 1)

    def test_strip_jpeg_and_unknown_retains_evidence(self):
        data, target = fixture([(273, 4, 1, 295), (279, 4, 1, 20),
                                (513, 4, 1, 310), (514, 4, 1, 30),
                                (330, 4, 1, 300)])
        r = probe.audit(data, target)
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['union_overlap_bytes'], 36)
        self.assertEqual({x['kind'] for x in r['overlaps']}, {'strip', 'jpeg'})

    def test_orf_magic_and_orphan_jpeg_length(self):
        data, target = fixture([(514, 4, 1, 10)])
        for magic in (0x4f52, 0x5352):
            buf = bytearray(data)
            struct.pack_into('<H', buf, 2, magic)
            r = probe.audit(bytes(buf), target)
            self.assertIn('incomplete_jpeg_pair', r['issues'])
            self.assertNotIn('unsupported_tiff', r['issues'])
    def test_directory_body_overlap(self):
        data = bytearray(600)
        data[:8] = b'II\x2a\x00' + struct.pack('<I', 296)
        struct.pack_into('<H', data, 296, 2)
        r = probe.audit(bytes(data), (300, 336))
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['overlaps'][0]['kind'], 'directory')


if __name__ == '__main__':
    unittest.main()
