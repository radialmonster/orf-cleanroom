"""Generated common-support, parity and binary-sign checks."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import common_support_donor as p


class Tests(unittest.TestCase):
    def test_common_donor_exclusion_and_nonzero_start(self):
        w=8; start=5; end=100
        q=[0]*end; s=[(i%2)*4 for i in range(end)]
        base=p.band(q,s,w,start,end)
        target=49
        donor=target-(2*w+2)
        q[donor]=17
        changed=p.band(q,s,w,start,end)
        self.assertGreater(changed['pooled']['q_omitted'],0)
        self.assertLess(changed['pooled']['retained'],base['pooled']['retained'])
        for row in changed['parities'].values():
            self.assertEqual(row['candidate'],row['geometry_omitted']+row['q_omitted']+row['retained'])
            for item in row['tables'].values():
                self.assertEqual(sum(map(sum,item['table'])),row['retained'])
        self.assertEqual(set(changed['parities']),{'00','01','10','11'})
        self.assertTrue(all(x['candidate']>0 for x in changed['parities'].values()))
        self.assertGreater(changed['pooled']['geometry_omitted'],0)
        self.assertEqual(changed['window'],[start,end])

    def test_single_target_removed_for_one_donor_in_every_table(self):
        w=8; q=[0]*45; s=[0]*45
        before=p.band(q,s,w,26,45)
        self.assertEqual(before['pooled']['retained'],1)
        q[26]=17
        after=p.band(q,s,w,26,45)
        self.assertEqual((after['pooled']['q_omitted'],after['pooled']['retained']),(1,0))
        for lag in after['lags']:
            self.assertEqual(sum(map(sum,before['pooled']['tables'][str(lag)]['table'])),1)
            self.assertEqual(sum(map(sum,after['pooled']['tables'][str(lag)]['table'])),0)

    def test_exact_pattern_classification(self):
        stats={str(k):{'sign':v} for k,v in [(8,'negative'),(14,'positive'),(16,'negative'),(18,'positive')]}
        self.assertEqual(p.pattern(stats,8),'match')
        stats['14']['sign']='negative'
        self.assertEqual(p.pattern(stats,8),'no_match')
        stats['14']['sign']='undefined'
        self.assertEqual(p.pattern(stats,8),'undefined')
    def test_sign_and_undefined(self):
        self.assertEqual(p.table_stat([[4,0],[0,4]])['sign'],'positive')
        self.assertEqual(p.table_stat([[0,4],[4,0]])['sign'],'negative')
        r=p.table_stat([[4,4],[0,0]])
        self.assertEqual(r['sign'],'undefined')
        self.assertIsNone(r['correlation'])

    def test_mask_geometry_specific_target(self):
        w=8; end=48
        q=[0]*end;s=[0]*end
        r=p.band(q,s,w,0,end)
        candidates=list(range(2*w+2,end))
        omitted=sum(t%w<2 or t%w>=w-2 for t in candidates)
        self.assertEqual(r['pooled']['geometry_omitted'],omitted)
        self.assertEqual(r['pooled']['retained'],len(candidates)-omitted)


if __name__=='__main__':unittest.main()
