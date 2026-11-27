import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
from full_market_decoder_probe import decode, get

def main():
    prices=decode(get("https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-ps5.json"))
    feed=get("https://fc27-market.val.run/latest")
    known={c["eaId"]:c for group in feed["groups"].values() for c in group}
    ids=[i for i in known if prices.get(i,0)>0][:5]
    ids+= [i for i in sorted(prices,key=prices.get,reverse=True) if i not in known and prices[i]>0][:25]
    assert len(ids)==len(set(ids)) and 0<len(ids)<=30
    url="https://www.fut.gg/api/fut/players/v2/27/?"+urlencode({"ids":",".join(map(str,ids))})
    try:
        with urlopen(Request(url,headers={"Accept":"application/json","User-Agent":"FUT-Trader-27-Diagnostic/1.0"}),timeout=25) as r:
            raw=r.read(2000001)
            if len(raw)>2000000: raise ValueError("Response too large")
            data=json.loads(raw)
            print("Metadata HTTP",r.status)
    except HTTPError as e:
        print("Metadata access refused:",e.code,"Retry-After:",e.headers.get("Retry-After"))
        raise SystemExit(1)
    print("Requested IDs:",ids)
    print("Root type:",type(data).__name__)
    if isinstance(data,dict): print("Root keys:",list(data))
    def walk(x):
        if isinstance(x,dict):
            if type(x.get("eaId")) is int and x["eaId"] in ids: yield x
            for v in x.values(): yield from walk(v)
        elif isinstance(x,list):
            for v in x: yield from walk(v)
    records={x["eaId"]:x for x in walk(data)}
    print("Matched IDs:",len(records),"New IDs:",sum(i not in known for i in records))
    for i,x in list(records.items())[:5]:
        print("EA ID",i,"fields",list(x),"price",prices[i],"metadata sample",json.dumps(x,ensure_ascii=False)[:1800])
    if not records: raise ValueError("No exact EA ID matches; inspect schema before integration")
if __name__=="__main__": main()
