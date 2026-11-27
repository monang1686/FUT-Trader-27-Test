import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from full_market_decoder_probe import decode,get

BASE="https://www.fut.gg/api/fut/players/v2/27/"
def probe(label,ids,page):
    q=urlencode({"ids":",".join(map(str,ids)),"page":page})
    with urlopen(Request(BASE+"?"+q,headers={"Accept":"application/json","User-Agent":"FUT-Trader-27-Diagnostic/1.0"}),timeout=20) as r:
        raw=r.read(2000001)
        if len(raw)>2000000: raise ValueError("response too large")
        obj=json.loads(raw)
    rows=obj["data"]
    if not isinstance(rows,list): raise ValueError("unexpected data schema")
    found=[x.get("eaId") for x in rows if isinstance(x,dict)]
    print(label,"total",obj.get("total"),"page",obj.get("currentPage"),"has_next",bool(obj.get("next")),"rows",len(rows),"matched",len(set(found)&set(ids)),"returned_ids",found[:30])
    for x in rows[:2]:
        print("Identity fields", {k:v for k,v in x.items() if isinstance(v,(str,int)) and any(s in k.lower() for s in ("id","name","rating","rarity","position"))})
        print("Field names",list(x))
    return obj
def main():
    prices=decode(get("https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-ps5.json"))
    feed=get("https://fc27-market.val.run/latest")
    known={c["eaId"]:c for group in feed["groups"].values() for c in group}
    control=[i for i in known if prices.get(i,0)>0][:5]
    new=[i for i in sorted(prices,key=prices.get,reverse=True) if i not in known and prices[i]>0][:25]
    print("Control IDs",control,"New IDs",new)
    probe("control",control,1)
    first=probe("mixed",control+new,1)
    if first.get("next"): probe("mixed page 2",control+new,2)
    probe("new only",new[:5],1)
if __name__=="__main__": main()
