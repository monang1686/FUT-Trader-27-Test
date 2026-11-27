"""Bounded independent catalog history and indicative fluctuation analysis."""
import json, statistics, unittest
from datetime import datetime
from pathlib import Path

def append(history, catalog):
    stamp=catalog["quoteTimestamp"]
    t=datetime.fromisoformat(stamp)
    if history and t<=datetime.fromisoformat(history[-1]["t"]): return history
    prices={str(c["eaId"]):c["quote"] for c in catalog["cards"] if c["state"]=="candidate" and type(c["quote"]) is int and c["quote"]>0}
    return (history+[{"t":stamp,"p":prices}])[-336:]

def analyze(history, catalog):
    out={}
    now=datetime.fromisoformat(catalog["quoteTimestamp"])
    for c in catalog["cards"]:
        if c["state"]!="candidate": continue
        key=str(c["eaId"])
        obs=[(datetime.fromisoformat(s["t"]),s["p"][key]) for s in history if key in s["p"] and 0<=(now-datetime.fromisoformat(s["t"])).total_seconds()<=86400]
        if len(obs)<6 or (obs[-1][0]-obs[0][0]).total_seconds()<7200 or obs[-1][0]!=now: continue
        values=[v for _,v in obs]
        current=c["quote"]
        median=statistics.median(values)
        # Conservative resale reference, not a prediction or executable quote.
        sell=int(min(median,statistics.median(values[-3:])))
        net=sell*95//100
        profit=net-current
        falling=values[-1]<values[-3]*0.95
        out[key]={"samples":len(values),"low":min(values),"high":max(values),"median":median,"sellReference":sell,"netAtQuote":profit,"roi":round(100*profit/current,2),"status":"watch" if profit>=200 and profit/current>=0.05 and not falling else "wait"}
    return out

def main():
    p=Path("market-catalog-history.json")
    catalog=json.loads(Path("market-catalog.json").read_text())
    history=json.loads(p.read_text()) if p.exists() else []
    history=append(history,catalog)
    p.write_text(json.dumps(history,separators=(",",":")))
    analysis=analyze(history,catalog)
    Path("market-catalog-analysis.json").write_text(json.dumps({"quoteTimestamp":catalog["quoteTimestamp"],"snapshots":len(history),"cards":analysis},separators=(",",":")))
    print("HISTORY",len(history),"ANALYZED",len(analysis),"WATCH",sum(v["status"]=="watch" for v in analysis.values()))

class Tests(unittest.TestCase):
    def test_history(self):
        c={"quoteTimestamp":"2026-11-27T10:00:00+00:00","cards":[{"eaId":1,"state":"candidate","quote":3600},{"eaId":2,"state":"excluded","quote":100}]}
        h=append([],c)
        self.assertEqual(h[0]["p"],{"1":3600})
        self.assertEqual(append(h,c),h)
        self.assertEqual(analyze(h,c),{})
    def test_analysis(self):
        h=[{"t":f"2026-11-27T{10+i//2:02d}:{30*(i%2):02d}:00+00:00","p":{"1":v}} for i,v in enumerate([4000,4000,4000,4000,4000,3900])]
        c={"quoteTimestamp":h[-1]["t"],"cards":[{"eaId":1,"state":"candidate","quote":3900}]}
        self.assertEqual(analyze(h,c)["1"]["netAtQuote"],-100)
        self.assertEqual(analyze(h,c)["1"]["status"],"wait")
if __name__=="__main__": main()
