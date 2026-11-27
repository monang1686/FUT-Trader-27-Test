import json
import time
from collections import Counter
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from full_catalog_general_probe import BASE, PRICE
from full_market_decoder_probe import decode, get

TARGETS = {50572286, 50578894, 67316992}
FLAGS = ("isSbc", "isObjective", "isEvolutionPlayerItem", "isProvisional", "hasPrice")

def evidence(row):
    return {k: v for k, v in row.items() if k in FLAGS or any(s in k.lower() for s in ("tradable", "tradeable", "untrade", "market", "auction", "transfer", "price"))}

def fetch(params):
    with urlopen(Request(BASE+"?"+urlencode(params), headers={"Accept":"application/json","User-Agent":"FUT-Trader-27-Diagnostic/1.0"}), timeout=25) as r:
        raw = r.read(8000001)
        if len(raw)>8000000:
            raise ValueError("Response too large")
    obj=json.loads(raw)
    if not isinstance(obj.get("data"),list):
        raise ValueError("Unexpected schema")
    return obj

def main():
    assert evidence({"isSbc":True,"hasPrice":True}) == {"isSbc":True,"hasPrice":True}
    prices=decode(get(PRICE))
    rows={}
    for page in range(1,7):
        obj=fetch({"page":page})
        batch={x["eaId"]:x for x in obj["data"] if type(x.get("eaId")) is int}
        fresh=set(batch)-set(rows)
        rows.update(batch)
        print("PAGE",page,"new",len(fresh))
        if not fresh or not obj.get("next"):
            break
        time.sleep(1)
    missing=TARGETS-set(rows)
    if missing:
        obj=fetch({"ids":",".join(map(str,sorted(missing))),"page":1})
        rows.update({x["eaId"]:x for x in obj["data"] if x.get("eaId") in missing})
    counts=Counter()
    examples=set()
    for i,row in rows.items():
        flags=tuple(row.get(k) for k in FLAGS)
        positive=prices.get(i,0)>0
        counts[(flags,positive)]+=1
        category=(flags,positive,row.get("rarityName"))
        if i in TARGETS or (category not in examples and len(examples)<24):
            print("TARGET" if i in TARGETS else "SAMPLE",i,row.get("cardName"),row.get("overall"),row.get("rarityName"),"feed_quote",prices.get(i),json.dumps(evidence(row),ensure_ascii=False)[:2500])
            examples.add(category)
    print("FLAG ORDER",FLAGS)
    for (flags,positive),n in counts.items():
        print("GROUP",flags,"positive_quote",positive,"count",n)
    print("SUMMARY rows",len(rows),"targets_found",len(TARGETS&set(rows)),"targets_missing",sorted(TARGETS-set(rows)))
    print("No card certified tradeable: compare flags against manually verified EA market controls. No publication.")
if __name__=="__main__":
    main()
