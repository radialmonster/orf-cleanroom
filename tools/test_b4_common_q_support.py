import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from token_b4_gate_probe import measure
from b4_common_q_support import summarize


def sample(ident,tokens):
    return {'pixls_id':ident,'requested_tokens':len(tokens),'returned_tokens':len(tokens),
            'token_shortfall':0,'statistics':measure(tokens,True)}


class CommonSupportTest(unittest.TestCase):
    def test_intersection_and_uniform_weight(self):
        # q0 and q1 in all four, q2 only in the first three; two q's weighted equally.
        base=[(0,3),(0,16),(1,0),(1,18)]
        samples=[sample(str(i),base+([(2,5),(2,16)] if i<3 else [(17,0),(17,0)])) for i in range(4)]
        out=summarize(samples)
        self.assertEqual(out['support_q'],[0,1])
        self.assertEqual(out['excluded_q'],list(range(2,17)))
        # low4 differences -3 and +2 average -1/2; low3 identical here.
        self.assertEqual(out['samples']['0']['low4']['mean'],{'numerator':-1,'denominator':2})
        self.assertEqual(out['samples']['0']['low3']['mean'],{'numerator':-1,'denominator':2})
        self.assertEqual(out['samples']['0']['low4']['excluded_strata'],15)
        self.assertEqual(out['samples']['0']['low4']['local_support_q'],[0,1,2])
        self.assertEqual(out['samples']['0']['low4']['local_equal_weight_mean'],{'numerator':-2,'denominator':1})

    def test_empty_support_and_inconsistent_fields(self):
        samples=[sample(str(i),[(i,0)]) for i in range(4)]
        out=summarize(samples)
        self.assertEqual(out['support_q'],[])
        self.assertIsNone(out['samples']['0']['low4']['mean'])
        broken=copy.deepcopy(samples)
        broken[0]['statistics']['q_stratified_fields']['low3']['strata'][0]['b4_rows_value_columns'][0][0]+=1
        with self.assertRaises(ValueError):summarize(broken)

    def test_incomplete_or_duplicate(self):
        samples=[sample(str(i),[(0,0),(0,16)]) for i in range(4)]
        samples[0]['token_shortfall']=1
        with self.assertRaises(ValueError):summarize(samples)
        samples[0]['token_shortfall']=0;samples[1]['pixls_id']='0'
        with self.assertRaises(ValueError):summarize(samples)

    def test_unequal_extents_rejected(self):
        samples=[sample(str(i),[(0,0),(0,16)]) for i in range(4)]
        samples[0]=sample('0',[(0,0),(0,16),(1,0),(1,16)])
        with self.assertRaises(ValueError):summarize(samples)


if __name__=='__main__':unittest.main()
