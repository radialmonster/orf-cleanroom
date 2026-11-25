"""Generated exact lattice, phase, tie and boundary checks."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import literal_motif_lattice as p


class Tests(unittest.TestCase):
    def test_planted_both_and_decoy(self):
        w1,w2=(40,296),(296,552)
        a=[40,104,168,232,51]
        b=[296,360,424,488,307]
        r=p.evaluate(a,b,w1,w2,[64])
        self.assertEqual((r['full_first'],r['full_second'],r['full_both_same_lattice']),(1,1,1))
        self.assertEqual(r['best_first'],{'pitch':64,'phase':0,'matched':4,'possible':4})
        self.assertEqual(r['same_lattice_second']['matched'],4)

    def test_generated_bits_feed_real_selector(self):
        data=bytearray(69)
        for start in (40,168,296,424):
            for i, bit in enumerate('10000000'*6):
                if bit == '1':
                    pos=start+i
                    data[pos//8] |= 128 >> (pos%8)
        a=p.motif_positions(bytes(data),40,296)
        b=p.motif_positions(bytes(data),296,552)
        self.assertEqual(a,[40,168])
        self.assertEqual(b,[296,424])
        r=p.evaluate(a,b,(40,296),(296,552),[128])
        self.assertEqual(r['full_both_same_lattice'],1)
    def test_shift_breaks_full_and_no_refit(self):
        a=[40,104,168,232]
        b=[297,361,425,489]
        r=p.evaluate(a,b,(40,296),(296,552),[64])
        self.assertEqual((r['full_first'],r['full_second'],r['full_both_same_lattice']),(1,1,0))
        self.assertEqual(r['same_lattice_second']['matched'],0)
        a[-1]+=1
        r=p.evaluate(a,b,(40,296),(296,552),[64])
        self.assertEqual(r['full_first'],0)
        self.assertEqual(r['best_first']['matched'],3)

    def test_terminal_inclusive_and_vacuous(self):
        self.assertEqual(p.possible(40,152,64,0),2)
        self.assertEqual(p.possible(40,151,64,0),1)
        self.assertEqual(p.possible(40,87,64,0),0)
        r=p.evaluate([],[],(40,87),(87,134),[64])
        self.assertEqual((r['full_first'],r['full_second'],r['full_both_same_lattice']),(0,0,0))
        self.assertIsNone(r['best_first'])

    def test_tie_break_coverage_then_count_pitch_phase(self):
        r=p.evaluate([40,104,168,232],[],(40,296),(296,552),[64,128])
        self.assertEqual((r['best_first']['pitch'],r['best_first']['phase']), (64,0))
        r=p.evaluate([40,41,104,105],[],(40,168),(168,296),[64])
        self.assertEqual(r['best_first']['phase'],0)


if __name__=='__main__':
    unittest.main()
