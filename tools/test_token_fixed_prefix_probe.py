"""Synthetic constant-prefix and literal bit-window tests."""
import sys,unittest,random,struct,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import token_fixed_prefix_probe as p

def payload(tokens):
 bits="".join("0"*q+"1"+format(s,"05b") for q,s in tokens);return int(bits+"0"*((-len(bits))%8),2).to_bytes((len(bits)+7)//8,"big"),bits

class TestPrefix(unittest.TestCase):
 def test_constant_and_variable_prefix(self):
  tokens=[(0,0)]*(64*3);data,bits=payload(tokens);result=p.measure(data,tokens,64,3)
  self.assertEqual(result["eligible_rows"],3)
  self.assertTrue(all((x["distinct"],x["modal_multiplicity"],x["equal_pairs"])==(1,3,3) for x in result["cells"]))
  tokens[64]=(0,31);data,bits=payload(tokens);result=p.measure(data,tokens,64,3);x=result["cells"][0]
  self.assertEqual((x["distinct"],x["modal_multiplicity"],x["equal_pairs"]),(2,2,1))
 def test_common_short_window_excludes_whole_row(self):
  tokens=[(0,0)]*(49*3);data,_=payload(tokens);r=p.measure(data,tokens,49,3)
  self.assertEqual((r["eligible_rows"],r["excluded_rows"]),(0,3));self.assertTrue(all(x["distinct"]==0 for x in r["cells"]))
 def test_constant_short_prefix_variable_72(self):
  tokens=[(0,0)]*(64*3);tokens[64+3]=(0,31);data,_=payload(tokens);r=p.measure(data,tokens,64,3)
  cells={(x["offset_tokens"],x["length_bits"]):x for x in r["cells"]}
  self.assertEqual(cells[0,8]["modal_multiplicity"],3);self.assertEqual(cells[0,16]["modal_multiplicity"],3);self.assertEqual(cells[0,72]["modal_multiplicity"],2)
 def test_independent_bit_index_and_all_cells(self):
  rng=random.Random(30);tokens=[(rng.randrange(3),rng.randrange(32)) for _ in range(64*4)];tokens[65]=(17,3);data,bits=payload(tokens);r=p.measure(data,tokens,64,4);self.assertEqual(r["escape_count"],1)
  positions=[0]
  for q,s in tokens:positions.append(positions[-1]+q+6)
  for cell in r["cells"]:
   offset=cell["offset_tokens"];n=cell["length_bits"]
   strings=[bits[positions[row*64+offset]:positions[row*64+offset]+n] for row in range(4)]
   counts=[strings.count(v) for v in set(strings)]
   self.assertEqual((cell["distinct"],cell["modal_multiplicity"],cell["equal_pairs"]),(len(counts),max(counts),sum(k*(k-1)//2 for k in counts)))
 def test_window_crosses_bytes(self):
  data=bytes.fromhex("123456789a");bits="".join(format(x,"08b") for x in data)
  for start in range(8):
   for n in (8,16,32):self.assertEqual(p.window(data,start,n),int(bits[start:start+n],2))
 def test_tiff_cli_and_shortfall(self):
  raw,_=payload([(0,0)]*(64*300))
  def tiff(data):
   tags=((256,64),(257,100),(273,62),(279,len(data)))
   return b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+data
  original=Path.read_bytes
  for data,expected in ((tiff(raw),0),(tiff(raw[:-1]),1)):
   def read(path):return data if str(path)=="synthetic" else original(path)
   with mock.patch.object(Path,"read_bytes",read),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--rows","300"]),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(p.main(),expected)
    if not expected:
     result=json.loads(out.getvalue());self.assertEqual(result["sample"]["result"]["eligible_rows"],300);self.assertIn("token_fixed_prefix_probe.py",result["source_sha256"])
if __name__=="__main__":unittest.main()
