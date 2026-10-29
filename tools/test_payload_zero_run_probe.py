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
  with mock.patch.object(Path,'read_bytes',read),mock.patch.object(sys,'argv',['probe','--sample','1','public',sha,'synthetic','--phase17']),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(p.main(),0);self.assertIn('real_phase17',json.loads(out.getvalue())['result'])
 def test_phase17_equal_multiset_and_censor(self):
  a=b'\xff'*6+bytes([0,0,0,32,1]);b=b'\xff'*6+bytes([0,32,0,0,1]);self.assertEqual(collections.Counter(a[6:]),collections.Counter(b[6:]))
  x,y=p.phase17(a),p.phase17(b);self.assertEqual(x['later_phase_counts'],[0,0,1,0,0,0,0,0]);self.assertEqual(y['later_phase_counts'],[0,0,0,0,0,0,0,1]);self.assertEqual(x['tail_one_counts_by_phase'],y['tail_one_counts_by_phase']);self.assertIsNone(x['terminal_zero_run']);self.assertIsNone(y['terminal_zero_run'])
  empty=p.phase17(b'\xff'*6);self.assertEqual(empty['later_qualifying_total'],0);self.assertIsNone(empty['later_phase_proportions'])
  seam=p.phase17(pack('1'*30+'0'*39+'1'));self.assertEqual(seam['excluded_qualifying_terminated']['seam_crossing'],1);self.assertEqual(seam['later_qualifying_total'],0)
  censored=p.phase17(b'\xff'*6+b'\x00'*3);self.assertEqual(censored['terminal_zero_run']['length'],24);self.assertEqual(censored['later_qualifying_total'],0)
  result=p.measure(a,True)
  for control in result['controls']:self.assertEqual(control['phase17']['tail_one_counts_by_phase'],result['real_phase17']['tail_one_counts_by_phase'])
 def test_phase17_naive_bit_oracle_and_default(self):
  rng=random.Random(197);data=bytes(rng.randrange(256) for _ in range(100));bits=''.join(format(x,'08b') for x in data);r=p.phase17(data);phase=[0]*8;excluded={k:0 for k in ('startup','preserved_internal','seam_crossing')};start=None
  for i,bit in enumerate(bits):
   if bit=='0' and start is None:start=i
   if bit=='1' and start is not None:
    if i-start>=17:
     region='startup' if start==0 else ('seam_crossing' if start<48<=i else 'preserved_internal' if start<48 else 'later')
     if region=='later':phase[i%8]+=1
     else:excluded[region]+=1
    start=None
  self.assertEqual(r['later_phase_counts'],phase);self.assertEqual(r['excluded_qualifying_terminated'],excluded)
  default=p.measure(data);self.assertNotIn('real_phase17',default);self.assertTrue(all('phase17' not in x for x in default['controls']))
 def test_phase17_threshold_all_phases_and_long_runs(self):
  for length in (16,17,39,80):
   for desired in range(8):
    filler=(desired-length)%8;data=pack('1'*48+'1'*filler+'0'*length+'1'+'1'*8);bits=''.join(format(x,'08b') for x in data)
    phase=[0]*8;start=None
    for i,bit in enumerate(bits):
     if bit=='0' and start is None:start=i
     if bit=='1' and start is not None:
      if start>=48 and i-start>=17:phase[i%8]+=1
      start=None
    r=p.phase17(data);self.assertEqual(r['later_phase_counts'],phase)
    self.assertEqual(sum(phase),0 if length==16 else 1)
    if length>=17:self.assertEqual(phase[desired],1)
if __name__=='__main__':unittest.main()
