"""Read-only schema and coverage probe; never infer missing chemistry data."""
import json,time
from collections import Counter
from full_catalog_tradeability_probe import fetch

def main():
    rows={}
    for page in range(1,7):
        obj=fetch({"page":page})
        batch={r["eaId"]:r for r in obj["data"] if type(r.get("eaId")) is int}
        fresh=set(batch)-set(rows)
        rows.update(batch)
        if not fresh or not obj.get("next"): break
        time.sleep(1)
    if not rows: raise ValueError("Empty metadata")
    keys=Counter(k for r in rows.values() for k,v in r.items() if v is not None)
    print("SCHEMA",json.dumps(dict(keys),sort_keys=True))
    terms=("position","league","club","nation","country","team","stat","attribute","playstyle","role","image","baseplayer","chemistry","icon","hero","gender","pace","shoot","pass","dribbl","defen","physical")
    selected=[k for k in keys if any(t in k.lower() for t in terms)]
    for k in sorted(selected):
        values=[r[k] for r in rows.values() if r.get(k) is not None]
        print("FIELD",k,"coverage",len(values),"/",len(rows),"types",dict(Counter(type(v).__name__ for v in values)),"example",json.dumps(values[0],ensure_ascii=False)[:1200])
    for r in list(rows.values())[:3]:
        print("CARD",r["eaId"],r.get("cardName"),json.dumps({k:r.get(k) for k in selected},ensure_ascii=False)[:6500])
    print("SUMMARY",len(rows),"cards",len(selected),"potential metadata fields; no publication")
if __name__=="__main__": main()
