"""Official WCVP release downloader. Requires operator-supplied official direct ZIP URL.

The release page is https://kew.iro.bl.uk/entities/product/998399a0-4b87-4a93-8303-6abc8a2de281
No HTML scraping and no unverified guessed attachment URL.
"""
import argparse,hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True,help="Direct HTTPS ZIP URL copied from official Kew repository")
    p.add_argument("--version",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    parsed=urlparse(a.url)
    if parsed.scheme!="https" or parsed.hostname not in ("kew.iro.bl.uk","powo.science.kew.org"):
        raise SystemExit("Only official Kew HTTPS hosts are accepted")
    if not a.output.name.lower().endswith(".zip"):
        raise SystemExit("Output must end in .zip")
    print(f"WCVP version={a.version} destination={a.output} apply={a.apply}")
    if not a.apply:return
    req=Request(a.url,headers={"User-Agent":"GardnAIze-research/0.1"})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=a.output.with_suffix(".zip.part")
    h=hashlib.sha256()
    try:
        with urlopen(req,timeout=90) as resp, tmp.open("wb") as f:
            final=urlparse(resp.geturl())
            if final.scheme!="https":
                raise ValueError("Unsafe download redirect")
            total=0
            while True:
                chunk=resp.read(1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>250*1024*1024:raise ValueError("Download exceeds 250 MiB")
                h.update(chunk);f.write(chunk)
        with tmp.open("rb") as f:
            if f.read(4)!=b"PK\\x03\\x04":raise ValueError("Not a ZIP archive")
        tmp.replace(a.output)
    finally:
        if tmp.exists():tmp.unlink()
    manifest={"source":"WCVP","version":a.version,"official_url":a.url,
              "sha256":h.hexdigest(),"file":str(a.output)}
    a.output.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
