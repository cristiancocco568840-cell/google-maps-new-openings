import base64, hashlib, re, html, unicodedata
from pathlib import Path

_src = Path(__file__).with_name("baseline_filter.py").read_text(encoding="utf-8")
_m = re.search(r'DATA=base64\.b64decode\(\s*"""([A-Za-z0-9+/=\\r\\n]+)"""\s*\)', _src)
if not _m:
    raise RuntimeError("Baseline data not found")
_b64 = re.sub(r"\\s+", "", _m.group(1))
DATA = base64.b64decode(_b64 + "=" * (-len(_b64) % 4))
M_BITS = 180000
K = 12

STOP={'srl','s','r','l','snc','sas','spa','ss','societa','soc','di','del','della','dei','degli','azienda','studio','impresa','fratelli','flli'}

def _norm(v):
    s=html.unescape(str(v or '')).lower()
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return ' '.join(s.split())

def _core(v):
    return ' '.join(t for t in _norm(v).split() if t not in STOP and len(t)>1)

def _contains(v):
    if not v: return False
    raw=v.encode()
    h1=int.from_bytes(hashlib.sha256(b'a'+raw).digest()[:8],'big')
    h2=int.from_bytes(hashlib.sha256(b'b'+raw).digest()[:8],'big') or 1
    for i in range(K):
        pos=(h1+i*h2)%M_BITS
        if not (DATA[pos>>3] & (1<<(pos&7))):
            return False
    return True

def historical_name_match(name):
    n=_norm(name); c=_core(name)
    return _contains(n) or (bool(c) and _contains(c))

BASELINE_SOURCE_ROWS=6334
BASELINE_UNIQUE_NAMES=6270
