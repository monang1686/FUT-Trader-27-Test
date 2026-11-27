import json
from urllib.request import urlopen
from datetime import datetime, timezone

def decode(x):
    if x.get("v") != 2: raise ValueError("Unknown version")
    first=x["id0"]; d=x["d"]; p=x["p"]
    if type(first) is not int or first<=0 or len(p)!=len(d)+1: raise ValueError("Invalid shape")
    if any(type(n) is not int or n<=0 for n in d): raise ValueError("Invalid delta")
    if any(type(n) is not int or n<0 for n in p): raise ValueError("Invalid price")
    ids=[first]
    for n in d: ids.append(ids[-1]+n)
    return dict(zip(ids,p))

def get(url):
    with urlopen(url,timeout=25) as r:
        raw=r.read(4000001)
        if len(raw)>4000000: raise ValueError("Response too large")
        print("HTTP",r.status,"Last-Modified",r.headers.get("Last-Modified"),"Age",r.headers.get("Age"))
        return json.loads(raw)

def main():
    assert decode({"v":2,"id0":27,"d":[14,10],"p":[100,0,500]})=={27:100,41:0,51:500}
    for bad in [{"v":2,"id0":27,"d":[0],"p":[1,2]},{"v":2,"id0":27,"d":[1],"p":[1]}]:
        try: decode(bad)
        except ValueError: pass
        else: raise AssertionError("Invalid fixture accepted")
    print("Decoder fixtures passed")
    prices=decode(get("https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-ps5.json"))
    positive=sum(v>0 for v in prices.values())
    print("IDs:",len(prices),"positive:",positive,"zero:",len(prices)-positive)
    if positive<5000: raise ValueError("Unexpected low coverage")
    feed=get("https://fc27-market.val.run/latest")
    rows=[c for group in feed["groups"].values() for c in group]
    overlap=[c for c in rows if c["eaId"] in prices and prices[c["eaId"]]>0]
    exact=sum(prices[c["eaId"]]==c["price"] for c in overlap)
    print("Val Town timestamp:",feed["updated"],"overlap:",len(overlap),"exact:",exact)
    print("Retrieved:",datetime.now(timezone.utc).isoformat())
    if not overlap: raise ValueError("No overlap")
    print("Comparison is same-source and may differ by snapshot age; not independent verification.")
if __name__=="__main__": main()
