"""Synthetic independent bit-string phase and EOF tests."""
import sys,unittest,random,hashlib,struct,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import token_start_bit_phase_probe as p

def naive(data):
 bits=''.join(format(x,'08b') for x in data);start=0;count=0;rows=[{'q0':0,'q1_to_16':0,'escape':0,'ordinary':0,'suffix_ones':[0]*5} for _ in range(8)]
 while start<len(bits):
  stop=bits.find('1',start)
  if stop<0:return {'tokens':count,'bits_consumed':start,'residual_bits':len(bits)-start,'eof_state':'missing_stop','phase_table':rows}
  if stop+6>len(bits):return {'tokens':count,'bits_consumed':start,'residual_bits':len(bits)-start,'eof_state':'partial_suffix','phase_table':rows}
  q=stop-start;suffix=bits[stop+1:stop+6];row=rows[start%8];count+=1
  if q>=17:row['escape']+=1
  else:
   row['ordinary']+=1;row['q0' if q==0 else 'q1_to_16']+=1
   for i,v in enumerate(suffix):row['suffix_ones'][i]+=v=='1'
  start=stop+6
 return {'tokens':count,'bits_consumed':start,'residual_bits':0,'eof_state':'boundary','phase_table':rows}

class TestStartPhase(unittest.TestCase):
 def test_generated_exact(self):
  rng=random.Random(11696)
  for _ in range(1000):
   data=bytes(rng.randrange(256) for _ in range(rng.randrange(0,40)));self.assertEqual(p.scan(data),naive(data))
 def test_missing_stop_partial_suffix_and_escape(self):
  self.assertEqual(p.scan(b'\0')['eof_state'],'missing_stop');self.assertEqual(p.scan(b'\x01')['eof_state'],'partial_suffix')
  data=b'\0\0\x40\xff';r=p.scan(data);self.assertEqual(r,naive(data));self.assertEqual(sum(x['escape'] for x in r['phase_table']),1)
  bits='0'*16+'1'+'11111'+'0'*17+'1'+'11111';bits+='0'*((-len(bits))%8);r=p.scan(int(bits,2).to_bytes(len(bits)//8,'big'));self.assertEqual(sum(x['ordinary'] for x in r['phase_table']),1);self.assertEqual(sum(x['escape'] for x in r['phase_table']),1);self.assertEqual(sum(sum(x['suffix_ones']) for x in r['phase_table']),5);self.assertEqual(sum(x['q0']+x['q1_to_16']+x['escape'] for x in r['phase_table']),r['tokens'])
 def test_control_order_and_same_window(self):
  data=bytes(range(32));r=p.measure(data)
  for c in r['controls']:
   v=bytearray(data);rng=random.Random(c['seed'])
   for i in range(len(v)-1,0,-1):j=rng.randrange(i+1);v[i],v[j]=v[j],v[i]
   self.assertEqual(c['window_sha256'],hashlib.sha256(v).hexdigest());self.assertEqual(c['result'],naive(v))
 def test_tiff_cli_short_window_and_source_hash(self):
  raw=b'\xff'*262144;tags=((256,64),(257,100),(273,62),(279,len(raw)));data=b'II'+struct.pack('<HIH',42,8,len(tags))+b''.join(struct.pack('<HHII',t,4,1,v) for t,v in tags)+struct.pack('<I',0)+raw;sha=hashlib.sha256(data).hexdigest();original=Path.read_bytes
  def read(path):return data if str(path)=='synthetic' else original(path)
  for length,given,expected in ((131072,sha,0),(262144,sha,0),(131072,'0'*64,1)):
   with mock.patch.object(Path,'read_bytes',read),mock.patch.object(sys,'argv',['probe','--sample','1','public',given,'synthetic','--bytes',str(length)]),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(p.main(),expected)
    if not expected:
     r=json.loads(out.getvalue());self.assertEqual(r['result']['window_bytes'],length);self.assertIn('token_start_bit_phase_probe.py',r['source_sha256'])
  shorttags=((256,64),(257,100),(273,62),(279,131071));short=b'II'+struct.pack('<HIH',42,8,len(shorttags))+b''.join(struct.pack('<HHII',t,4,1,v) for t,v in shorttags)+struct.pack('<I',0)+raw[:131071];shortsha=hashlib.sha256(short).hexdigest()
  def shortread(path):return short if str(path)=='synthetic' else original(path)
  with mock.patch.object(Path,'read_bytes',shortread),mock.patch.object(sys,'argv',['probe','--sample','1','public',shortsha,'synthetic','--bytes','131072']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(p.main(),1)
if __name__=='__main__':unittest.main()
