"""Candidate token start-bit phase statistics on fixed byte windows for #11.

This is a descriptive candidate parse, not a physical byte-alignment claim.
"""
import argparse,hashlib,json,os,random,struct,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
SEEDS=(20261022,20261023,20261024,20261025)

def scan(data):
 bits=len(data)*8;pos=0;count=0;table=[{'q0':0,'q1_to_16':0,'escape':0,'ordinary':0,'suffix_ones':[0]*5} for _ in range(8)]
 while pos<bits:
  start=pos
  while pos<bits and not ((data[pos//8]>>(7-pos%8))&1):pos+=1
  if pos==bits:return {'tokens':count,'bits_consumed':start,'residual_bits':bits-start,'eof_state':'missing_stop','phase_table':table}
  if pos+6>bits:return {'tokens':count,'bits_consumed':start,'residual_bits':bits-start,'eof_state':'partial_suffix','phase_table':table}
  q=pos-start;pos+=1;s=0
  for _ in range(5):s=(s<<1)|((data[pos//8]>>(7-pos%8))&1);pos+=1
  row=table[start%8];count+=1
  if q>=17:row['escape']+=1
  else:
   row['ordinary']+=1;row['q0' if q==0 else 'q1_to_16']+=1
   for b in range(5):row['suffix_ones'][b]+=(s>>(4-b))&1
 return {'tokens':count,'bits_consumed':pos,'residual_bits':0,'eof_state':'boundary','phase_table':table}

def measure(window):
 result={'window_bytes':len(window),'real':scan(window),'controls':[]}
 for seed in SEEDS:
  shuffled=bytearray(window);random.Random(seed).shuffle(shuffled)
  result['controls'].append({'seed':seed,'window_sha256':hashlib.sha256(shuffled).hexdigest(),'result':scan(shuffled)})
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sample',nargs=4,required=True,metavar=('ID','PUBLIC_NAME','SHA256','FILE'));p.add_argument('--bytes',type=int,choices=(131072,262144),required=True);a=p.parse_args();sid,name,sha,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in '/\\') or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):p.error('invalid public identity')
 try:
  data=Path(path).read_bytes()
  if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('snapshot hash mismatch')
  w,h,payload=locate_data(data)
  if len(payload)<a.bytes:raise ValueError('short payload')
  names=('token_start_bit_phase_probe.py','orf_tokens.py','orf_signature.py');sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({'pixls_id':sid,'pixls_name':name,'sha256':sha,'payload_w':w,'payload_h':h,'payload_bytes':len(payload),'source_sha256':sources,'result':measure(payload[:a.bytes])},allow_nan=False));return 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error):
  print('measurement failed: input, locator or short window',file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
