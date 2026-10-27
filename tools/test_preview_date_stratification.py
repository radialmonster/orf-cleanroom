import itertools
import hashlib
import io
from unittest.mock import patch
import os
import sys
import struct
import tempfile
from pathlib import Path
import unittest
from datetime import datetime
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import preview_date_stratification as p


def meta(s):
 return {'dto':s,'time':datetime.strptime(s,'%Y:%m:%d %H:%M:%S') if s else None,'base':'x','hires':False,'ori':False}


class Tests(unittest.TestCase):
 def test_bins_and_pair_denominators(self):
  ids=['%064x'%i for i in range(1,7)]
  dates=['2025:01:01 10:00:00','2025:01:01 10:00:00','2025:01:01 10:10:00','2025:01:01 10:10:01','2025:01:02 00:00:00',None]
  cohort={v:('A' if i<4 else 'B','original' if i<5 else 'extension') for i,v in enumerate(ids)}
  metadata={v:meta(dates[i]) for i,v in enumerate(ids)}
  records=[{'sample':{'sha256':v,'status':'ok' if i<5 else 'unsupported'}} for i,v in enumerate(ids)]
  for a,b in itertools.combinations(ids,2):
   i,j=ids.index(a),ids.index(b)
   records.append({'pair':[a,b],'r':None if j==5 else (.99 if i==0 else .2)})
  records.append({'summary':{'grid':12,'min_sd':1.0,'threshold':.98,'alignment':'identity_only','samples':6,'pairs':15,'eligible_pairs':10,'screen_positive':4}})
  result=p.aggregate(records,cohort,metadata)
  self.assertEqual(result['total_pairs'],15)
  allbins=result['counts']['all']['all_pairs']
  self.assertEqual(sum(x['eligible'] for x in allbins.values()),10)
  self.assertEqual(sum(x['positive'] for x in allbins.values()),4)
  self.assertEqual(allbins['same_second'],{'eligible':1,'positive':1})
  self.assertEqual(allbins['same_day_within_600s'],{'eligible':3,'positive':1})
  self.assertEqual(allbins['same_day_after_600s'],{'eligible':2,'positive':1})
  self.assertEqual(allbins['different_day'],{'eligible':4,'positive':1})
  self.assertEqual(result['unscored']['all']['original_extension'],5)
  same=result['counts']['same_model']['all_pairs']
  self.assertEqual(sum(x['eligible'] for x in same.values()),6)
  self.assertEqual(sum(x['positive'] for x in same.values()),3)
  with self.assertRaises(ValueError):p.aggregate(records[:-2]+records[-1:],cohort,metadata)

 def test_unavailable_date_and_status_score_consistency(self):
  a,b='a'*64,'b'*64
  cohort={a:('A','original'),b:('A','extension')}
  metadata={a:meta('2025:01:01 10:00:00'),b:meta(None)}
  records=[{'sample':{'sha256':a,'status':'ok'}},{'sample':{'sha256':b,'status':'ok'}},
           {'pair':[a,b],'r':.98},{'summary':{'grid':12,'min_sd':1.0,'threshold':.98,'alignment':'identity_only','samples':2,'pairs':1,'eligible_pairs':1,'screen_positive':1}}]
  result=p.aggregate(records,cohort,metadata)
  self.assertEqual(result['counts']['same_model']['original_extension']['unavailable'],{'eligible':1,'positive':1})
  records[1]['sample']['status']='unsupported'
  with self.assertRaisesRegex(ValueError,'status'):p.aggregate(records,cohort,metadata)
  records[2]['r']=None
  records[-1]['summary']['eligible_pairs']=0
  records[-1]['summary']['screen_positive']=0
  result=p.aggregate(records,cohort,metadata)
  self.assertEqual(result['unscored']['same_model']['original_extension'],1)
  records[-1]['summary']['grid']=24
  with self.assertRaises(ValueError):p.aggregate(records,cohort,metadata)

 def test_invalid_calendar_date_becomes_unavailable(self):
  fake=b'container'
  with patch('builtins.open',return_value=io.BytesIO(fake)), \
       patch.object(p.calibration,'date_time_original',return_value='2025:02:30 10:00:00'), \
       patch.object(p.calibration,'signature',return_value={'sha256':hashlib.sha256(fake).hexdigest(),'payload_w':5000}):
   _,m=p.calibration.file_meta('public.ORF')
  self.assertIsNone(m['dto'])
  self.assertEqual(p.bucket(m,meta('2025:01:01 10:00:00')),'unavailable')

 def test_real_tiff_conflicting_dates_unavailable(self):
  stamp1=b'2025:01:01 10:00:00\0';stamp2=b'2025:01:02 10:00:00\0'
  data=bytearray(160)
  struct.pack_into('<2sHIH',data,0,b'II',42,8,1)
  struct.pack_into('<HHII',data,10,0x8769,4,1,32)
  struct.pack_into('<H',data,32,2)
  struct.pack_into('<HHII',data,34,0x9003,2,len(stamp1),80)
  struct.pack_into('<HHII',data,46,0x9003,2,len(stamp2),110)
  data[80:80+len(stamp1)]=stamp1;data[110:110+len(stamp2)]=stamp2
  root=Path(__file__).resolve().parent.parent/'work'/'test-date-stratification';root.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=str(root)) as folder:
   path=Path(folder)/'synthetic.ORF';path.write_bytes(data)
   with patch.object(p.calibration,'signature',return_value={'sha256':hashlib.sha256(data).hexdigest(),'payload_w':5000}):
    _,m=p.calibration.file_meta(str(path))
  self.assertIsNone(m['dto'])
  self.assertEqual(p.bucket(m,meta('2025:01:01 10:00:00')),'unavailable')

 def test_boundaries_and_missing(self):
  a=meta('2025:01:01 10:00:00')
  self.assertEqual(p.bucket(a,meta('2025:01:01 10:10:00')),'same_day_within_600s')
  self.assertEqual(p.bucket(a,meta('2025:01:01 10:10:01')),'same_day_after_600s')
  self.assertEqual(p.bucket(a,meta(None)),'unavailable')

if __name__=='__main__':unittest.main()
