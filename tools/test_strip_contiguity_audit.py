import hashlib,io,json,os,struct,sys,unittest
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import strip_contiguity_audit as t


def fixture(offsets,counts,width=2,height=2):
 data=bytearray(512);struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
 for i,(tag,values) in enumerate(((256,[width]),(257,[height]),(273,offsets),(279,counts))):
  p=10+i*12
  if len(values)==1:struct.pack_into('<HHII',data,p,tag,4,1,values[0])
  else:
   ptr=80 if tag==273 else 120
   struct.pack_into('<HHII',data,p,tag,4,len(values),ptr)
   struct.pack_into('<'+'I'*len(values),data,ptr,*values)
 return bytes(data)


class Tests(unittest.TestCase):
 def test_single_and_contiguous(self):
  a=t.audit(fixture([200],[10]));self.assertTrue(a['single_strip']);self.assertTrue(a['table_adjacent'])
  a=t.audit(fixture([200,210,220],[10,10,10]));self.assertFalse(a['single_strip']);self.assertTrue(a['table_adjacent']);self.assertFalse(a['physical_overlap'])
 def test_gap_overlap_and_descending(self):
  a=t.audit(fixture([200,215],[10,10]));self.assertEqual(a['forward_gaps'],1);self.assertFalse(a['physical_overlap'])
  a=t.audit(fixture([200,205],[10,10]));self.assertEqual(a['negative_table_deltas'],1);self.assertTrue(a['physical_overlap'])
  a=t.audit(fixture([220,200],[10,10]));self.assertEqual(a['nonascending_transitions'],1);self.assertEqual(a['negative_table_deltas'],1);self.assertFalse(a['physical_overlap'])
 def test_invalid_bounds_lengths_and_dimensions(self):
  for data in (fixture([510],[5]),fixture([200,210],[10]),fixture([200],[0]),fixture([200],[10],width=0)):
   with self.subTest():
    with self.assertRaises(ValueError):t.audit(data)
 def test_largest_ifd_and_tie(self):
  small={256:[1],257:[1],273:[300],279:[5]}
  big={256:[2],257:[3],273:[200,210],279:[10,10]}
  class Fake:
   def __init__(self,data):pass
   def all_ifds(self):return iter([small,big])
  with mock.patch.object(t,'Tiff',Fake):self.assertEqual(t.audit(bytes(512))['width'],2)
  class Tie(Fake):
   def all_ifds(self):return iter([big,big])
  with mock.patch.object(t,'Tiff',Tie):
   with self.assertRaisesRegex(ValueError,'ambiguous'):t.audit(bytes(512))
 def test_nonadjacent_physical_overlap(self):
  a=t.audit(fixture([200,230,205],[10,10,10]))
  self.assertTrue(a['physical_overlap']);self.assertEqual(a['nonascending_transitions'],1)

 def test_public_cc0_identity_without_pixls_id(self):
  data=fixture([200],[10]);digest=hashlib.sha256(data).hexdigest();out=io.StringIO()
  with mock.patch('builtins.open',side_effect=lambda *args:io.BytesIO(data)),mock.patch('sys.stdout',out):
   self.assertEqual(t.main(['--sample','public-cc0:PA200010.ORF','PA200010.ORF',digest,'private-path']),0)
  r=json.loads(out.getvalue());self.assertEqual(r['results'][0]['id'],'public-cc0:PA200010.ORF')
  self.assertNotIn('private-path',out.getvalue())

 def test_hash_failure_batch_keeps_later(self):
  data=fixture([200],[10]);digest=hashlib.sha256(data).hexdigest();out=io.StringIO()
  args=['--sample','1','public.ORF','0'*64,'first','--sample','2','other.ORF',digest,'second']
  with mock.patch('builtins.open',side_effect=lambda *args:io.BytesIO(data)),mock.patch('sys.stdout',out):self.assertEqual(t.main(args),1)
  r=json.loads(out.getvalue());self.assertFalse(r['complete']);self.assertEqual([x['status'] for x in r['results']],['failed','ok'])
  self.assertNotIn('first',out.getvalue());self.assertNotIn('second',out.getvalue())

if __name__=='__main__':unittest.main()
