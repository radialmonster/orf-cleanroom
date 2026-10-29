"""Literal long maximal zero runs, independent of candidate token boundaries.

Six startup bytes remain fixed while the entire remaining payload is shuffled.
These counts do not identify a marker, restart, codec or calibrated significance.
"""
import argparse,hashlib,json,os,random,sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
SEAM=48
SEEDS=(20261022,20261023,20261024,20261025)

def segments(byte):
 bits=[(byte>>(7-i))&1 for i in range(8)];out=[];current=bits[0];n=0
 for bit in bits:
  if bit!=current:out.append((current,n));current=bit;n=0
  n+=1
 out.append((current,n));return out
TABLE=tuple(segments(b) for b in range(256))

def region(start,end):
 if start==0:return 'startup'
 if start<SEAM and end>=SEAM:return 'seam_crossing'
 if start<SEAM:return 'preserved_internal'
 return 'later'

def census(payload):
 counts={k:{'exact39':0,'exact47':0,'at_least39':0} for k in ('startup','preserved_internal','seam_crossing','later')}
 pos=0;start=None
 for byte in payload:
  for bit,n in TABLE[byte]:
   if bit==0:
    if start is None:start=pos
   elif start is not None:
    length=pos-start;cell=counts[region(start,pos)]
    cell['exact39']+=int(length==39);cell['exact47']+=int(length==47);cell['at_least39']+=int(length>=39);start=None
   pos+=n
 terminal=None if start is None else {'length':pos-start,'region':region(start,pos-1),'crosses_seam':start<SEAM and pos>SEAM}
 return {'bits':pos,'terminated':counts,'terminal_zero_run':terminal}

def phase17(payload):
 phase=[0]*8;ones=[0]*8;excluded={'startup':0,'preserved_internal':0,'seam_crossing':0};pos=0;start=None
 for byte in payload:
  if pos>=SEAM:
   for i in range(8):ones[i]+=(byte>>(7-i))&1
  for bit,n in TABLE[byte]:
   if bit==0:
    if start is None:start=pos
   elif start is not None:
    if pos-start>=17:
     bucket=region(start,pos)
     if bucket=='later':phase[pos%8]+=1
     else:excluded[bucket]+=1
    start=None
   pos+=n
 total=sum(phase)
 return {'later_phase_counts':phase,'later_qualifying_total':total,'later_phase_proportions':None if total==0 else [str(Fraction(n,total)) for n in phase], 'tail_one_counts_by_phase':ones,'excluded_qualifying_terminated':excluded,'terminal_zero_run':None if start is None else {'length':pos-start,'region':region(start,pos-1),'crosses_seam':start<SEAM and pos>SEAM}}

def measure(payload,include_phase17=False):
 if len(payload)<6:raise ValueError('payload shorter than preserved prefix')
 out={'payload_bytes':len(payload),'seam_bit':SEAM,'real':census(payload),'controls':[]}
 if include_phase17:out['real_phase17']=phase17(payload)
 for seed in SEEDS:
  tail=bytearray(payload[6:]);random.Random(seed).shuffle(tail);shuffled=payload[:6]+tail
  control={'seed':seed,'tail_sha256':hashlib.sha256(tail).hexdigest(),'result':census(shuffled)}
  if include_phase17:control['phase17']=phase17(shuffled)
  out['controls'].append(control)
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sample',nargs=4,required=True,metavar=('ID','PUBLIC_NAME','SHA256','FILE'));p.add_argument('--phase17',action='store_true');a=p.parse_args();sid,name,sha,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in '/\\') or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):p.error('invalid public identity')
 try:
  data=Path(path).read_bytes()
  if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('snapshot hash mismatch')
  w,h,payload=locate_data(data);names=('payload_zero_run_probe.py','orf_tokens.py','orf_signature.py');sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({'pixls_id':sid,'pixls_name':name,'sha256':sha,'payload_w':w,'payload_h':h,'source_sha256':sources,'result':measure(payload,a.phase17)},allow_nan=False));return 0
 except (OSError,ValueError,KeyError,IndexError,TypeError):
  print('measurement failed: input, locator or census error',file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
