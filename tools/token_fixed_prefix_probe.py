"""Fixed-value prefix repetition at nominal candidate row starts for #30.

This tests a narrower constant-value hypothesis. A fixed-length header can vary;
candidate token boundaries and nominal rows are not established physical framing.
Only aggregate identity counts are emitted; no window bit values are output.
"""
import argparse,collections,hashlib,json,os,struct,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix

OFFSETS=(0,24,48)
LENGTHS=(8,16,32,72)

def window(data,start,n):
 first=start//8;shift=start%8;count=(shift+n+7)//8
 if first+count>len(data):raise ValueError("window outside payload")
 return (int.from_bytes(data[first:first+count],"big")>>(count*8-shift-n))&((1<<n)-1)

def measure(data,tokens,w,rows):
 if w<=max(OFFSETS) or len(tokens)!=w*rows:raise ValueError("incomplete nominal rows")
 tables={(offset,n):collections.Counter() for offset in OFFSETS for n in LENGTHS};position=0;eligible=0;excluded=0
 for r in range(rows):
  row=tokens[r*w:(r+1)*w];starts={};begin=position
  for i,(q,s) in enumerate(row):
   if i in OFFSETS:starts[i]=position
   position+=q+6
  if position>len(data)*8:raise ValueError("endpoint outside payload")
  if any(starts[i]+72>position for i in OFFSETS):excluded+=1;continue
  eligible+=1
  for offset in OFFSETS:
   for n in LENGTHS:tables[offset,n][window(data,starts[offset],n)]+=1
 cells=[]
 for offset in OFFSETS:
  for n in LENGTHS:
   counts=tables[offset,n].values();cells.append({"offset_tokens":offset,"length_bits":n,"distinct":len(tables[offset,n]),"modal_multiplicity":max(counts,default=0),"equal_pairs":sum(x*(x-1)//2 for x in counts)})
 return {"rows":rows,"width":w,"tokens":len(tokens),"bits_consumed":position,"eligible_rows":eligible,"excluded_rows":excluded,"escape_count":sum(q>=17 for q,s in tokens),"cells":cells}

def report(sid,name,data,rows):
 d=max(Tiff(data).all_ifds(),key=lambda v:sum(v.get(0x117) or []));offs,lens=d[0x111],d[0x117]
 if len(offs)!=1 or len(lens)!=1:raise ValueError("single strip required")
 off,n=offs[0],lens[0];w,h=d[0x100][0],d[0x101][0]
 if off<0 or n<=0 or off+n>len(data) or w<=max(OFFSETS) or h<=0 or size_class(n,w,h)!="variable":raise ValueError("invalid payload")
 payload=data[off:off+n];tokens,end=scan_prefix(payload,w*rows)
 if len(tokens)!=w*rows:raise ValueError("incomplete prefix")
 result=measure(payload,tokens,w,rows)
 if result["bits_consumed"]!=end:raise ValueError("endpoint mismatch")
 return {"pixls_id":sid,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":n,"result":result}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));p.add_argument("--rows",type=int,choices=(300,600),required=True);a=p.parse_args();sid,name,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\"):p.error("invalid public identity")
 try:
  data=Path(path).read_bytes();result=report(sid,name,data,a.rows)
  names=("token_fixed_prefix_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"sample":result},allow_nan=False));return 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error):
  print("measurement failed: input, locator, signature or parser error",file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
