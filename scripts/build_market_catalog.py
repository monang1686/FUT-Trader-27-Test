import json, time, argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import urlopen
from pathlib import Path
from full_catalog_tradeability_probe import fetch, PRICE, decode
from smart_market_filter import classify

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pages",type=int,default=40)
    p.add_argument("--output",default="market-catalog.json")
    a=p.parse_args()
    if not 1<=a.pages<=100: raise ValueError("Page limit")
    with urlopen(PRICE,timeout=25) as response:
        stamp=parsedate_to_datetime(response.headers["Last-Modified"])
        raw=response.read(4000001)
        if len(raw)>4000000: raise ValueError("Price response too large")
        prices=decode(json.loads(raw))
    now=datetime.now(timezone.utc)
    if not -300 <= (now-stamp).total_seconds() <= 5400:
        raise ValueError("Stale or future quote snapshot")
    rows={}
    for page in range(1,a.pages+1):
        obj=fetch({"page":page})
        fresh=0
        for row in obj["data"]:
            i=row.get("eaId")
            if type(i) is not int or i<=0: continue
            state=classify(row,prices.get(i))
            item={"eaId":i,"name":row.get("cardName"),"overall":row.get("overall"),"rarity":row.get("rarityName"),"state":state,"quote":prices.get(i) if state=="candidate" else None}
            if i in rows and rows[i]!=item: raise ValueError("Conflicting identity")
            if i not in rows: fresh+=1
            rows[i]=item
        print("PAGE",page,"new",fresh)
        if not fresh or not obj.get("next"): break
        time.sleep(1)
    if not rows: raise ValueError("Empty catalog")
    data={"source":"FUT.GG PS5 – unverified","quoteTimestamp":stamp.isoformat(),"retrieved":now.isoformat(),"complete":False,"cards":list(rows.values())}
    Path(a.output).write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    print("SUMMARY",len(rows),"candidates",sum(x["state"]=="candidate" for x in rows.values()))
if __name__=="__main__": main()
