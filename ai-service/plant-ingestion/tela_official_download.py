"""Download a user-selected official Tela Botanica BDTFX release.

The operator obtains the direct export URL from the official reference portal,
checks the release-specific license, and supplies its version. No page scraping.
"""
import argparse,hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen

HOSTS={"referentiels.tela-botanica.org","www.tela-botanica.org","tela-botanica.org"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True,help="Official direct CSV or ZIP export URL")
    p.add_argument("--version",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    u=urlparse(a.url)
    if u.scheme!="https" or u.hostname not in HOSTS:
        raise SystemExit("Official Tela Botanica HTTPS URL required")
    if a.output.suffix.lower() not in (".csv",".zip"):
        raise SystemExit("Output must be .csv or .zip")
    print(f"BDTFX version={a.version} apply={a.apply}")
    if not a.apply:return
    a.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=a.output.with_suffix(a.output.suffix+".part")
    h=hashlib.sha256()
    try:
        with urlopen(Request(a.url,headers={"User-Agent":"GardnAIze-research/0.1"}),timeout=90) as resp, tmp.open("wb") as f:
            total=0
            while True:
                block=resp.read(1024*1024)
                if not block:break
                total+=len(block)
                if total>250*1024*1024:raise ValueError("Export exceeds 250 MiB")
                h.update(block);f.write(block)
        if a.output.suffix.lower()==".zip":
            with tmp.open("rb") as f:
                if f.read(4)!=bytes((80,75,3,4)):raise ValueError("Not a ZIP")
        tmp.replace(a.output)
    finally:
        if tmp.exists():tmp.unlink()
    manifest={"source":"TELA_BOTANICA","version":a.version,
              "url":a.url,"sha256":h.hexdigest(),"file":str(a.output)}
    a.output.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
