"""Generated literal-bit maximal-run and seam tests."""
import sys,unittest,random,collections,struct,hashlib,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import payload_zero_run_probe as p

def naive(data):
 bits=''.join(format(x,'08b') for x in data);out={k:{'exact39':0,'exact47':0,'at_least39':0} for k in ('startup','preserved_internal','seam_crossing','later')};i=0;terminal=None
 while i<len(bits):
  if bits[i]=='1':i+=1;continue
  start=i
  while i<len(bits) and bits[i]=='0':i+=1
  if i==len(bits):
   name='startup' if start==0 else ('seam_crossing' if start<48<i else 'preserved_internal' if start<48 else 'later')
   terminal={'length':i-start,'region':name,'crosses_seam':start<48 and i>48};break
  name='startup' if start==0 else ('seam_crossing' if start<48<=i else 'preserved_internal' if start<48 else 'later')
  n=i-start;out[name]['exact39']+=n==39;out[name]['exact47']+=n==47;out[name]['at_least39']+=n>=39
 return {'bits':len(bits),'terminated':out,'terminal_zero_run':terminal}
def pack(bits):
 bits+='1'*((-len(bits))%8);return int(bits,2).to_bytes(len(bits)//8,'big')
class TestZeroRuns(unittest.TestCase):
 def test_exhaustive_two_bytes(self):
  for i in range(65536):
   data=i.to_bytes(2,'big');self.assertEqual(p.census(data),naive(data))
 def test_start_seam_later_and_censor(self):
  for bits in ('0'*39+'1'+'1'*16,'0'*47+'1'+'1'*8,'1'*30+'0'*39+'1','1'*48+'0'*47+'1','1'*40+'0'*40):
   data=pack(bits);self.assertEqual(p.census(data),naive(data))
  # One terminating bit on the seam belongs to seam_crossing; startup wins precedence.
  r=p.census(pack('1'*9+'0'*39+'1'+'1'*7));self.assertEqual(r['terminated']['seam_crossing']['exact39'],1)
  r=p.census(pack('0'*47+'1'+'1'*8));self.assertEqual(r['terminated']['startup']['exact47'],1);self.assertEqual(r['terminated']['seam_crossing']['at_least39'],0)
  r=p.census(pack('1'+'0'*39+'1'+'1'*7+'0'*47+'1'));self.assertEqual(sum(v['at_least39'] for v in r['terminated'].values()),2);self.assertEqual(r['terminated']['preserved_internal']['exact39'],1);self.assertEqual(r['terminated']['later']['exact47'],1)
  r=p.census(b'\xff'*5+b'\0');self.assertEqual(r['terminal_zero_run'],{'length':8,'region':'preserved_internal','crosses_seam':False})
  r=p.census(pack('0'*55+'1'));self.assertEqual(r['terminated']['startup']['at_least39'],1)
 def test_controls_preserve_prefix_and_tail_multiset(self):
  data=bytes(range(32));result=p.measure(data)
  for control in result['controls']:
   tail=bytearray(data[6:]);rng=random.Random(control['seed'])
   for i in range(len(tail)-1,0,-1):j=rng.randrange(i+1);tail[i],tail[j]=tail[j],tail[i]
   self.assertEqual(collections.Counter(tail),collections.Counter(data[6:]));self.assertEqual(control['result'],naive(data[:6]+tail))
 def test_too_short(self):
  with self.assertRaises(ValueError):p.measure(b'12345')
 def test_tiff_cli_and_hash(self):
  raw=bytes(range(32));tags=((256,64),(257,100),(273,62),(279,len(raw)));data=b'II'+struct.pack('<HIH',42,8,len(tags))+b''.join(struct.pack('<HHII',t,4,1,v) for t,v in tags)+struct.pack('<I',0)+raw;sha=hashlib.sha256(data).hexdigest();original=Path.read_bytes
  def read(path):return data if str(path)=='synthetic' else original(path)
  for given,expected in ((sha,0),('0'*64,1)):
   with mock.patch.object(Path,'read_bytes',read),mock.patch.object(sys,'argv',['probe','--sample','1','public',given,'synthetic']),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(p.main(),expected)
    if not expected:
     r=json.loads(out.getvalue());self.assertEqual(r['result']['payload_bytes'],32);self.assertEqual(len(r['result']['controls']),4);self.assertIn('payload_zero_run_probe.py',r['source_sha256'])
if __name__=='__main__':unittest.main()
