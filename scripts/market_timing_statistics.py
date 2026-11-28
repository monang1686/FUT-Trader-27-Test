"""Historical conditional frequencies, not calibrated purchase probabilities."""
import json, unittest
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROME=ZoneInfo("Europe/Rome")
BANDS=((8,12),(12,18),(18,23))
def samples(rows):
    # One independent-ish observation per card/date/band; baseline before band.
    days=defaultdict(list)
    for t,p in sorted(rows):
        days[t.astimezone(ROME).date()].append((t,p))
    out=defaultdict(list)
    for day,obs in days.items():
        for i,(a,b) in enumerate(BANDS):
            start=datetime(day.year,day.month,day.day,a,tzinfo=ROME)
            end=datetime(day.year,day.month,day.day,b,tzinfo=ROME)
            before=[(t,p) for t,p in obs if start-timedelta(hours=2)<=t<start]
            inside=[(t,p) for t,p in obs if start<=t<end]
            if not before or len(inside)<3: continue
            times=[start]+[t for t,p in inside]+[end]
            if max((y-x).total_seconds() for x,y in zip(times,times[1:]))>5400: continue
            base=before[-1][1]
            out[f"{day.weekday()}:{i}"].append(round(min(p for t,p in inside)/base,5))
    return dict(out)

def cohort_key(c):
    p=c.get("quote")
    rating=c.get("overall")
    rarity=c.get("rarity")
    if type(p) is not int or p<=0 or type(rating) is not int or not rarity: return None
    edges=(0,5000,10000,20000,40000,80000,160000,320000,640000,1280000)
    band=sum(p>=e for e in edges)-1
    return json.dumps([rarity,rating//2,band],ensure_ascii=False,separators=(",",":"))

def build(directory, catalog):
    series=defaultdict(list)
    seen={}
    for path in sorted(directory.glob("????-??-??.json")):
        for snap in json.loads(path.read_text()):
            t=datetime.fromisoformat(snap["t"])
            seen[t]=snap["p"]
    now=datetime.fromisoformat(catalog["quoteTimestamp"])
    for t,prices in sorted(seen.items()):
        if t>now: continue
        for key,p in prices.items():
            if type(p) is int and p>0: series[key].append((t,p))
    cards={}
    for c in catalog["cards"]:
        if c["state"]!="candidate": continue
        key=str(c["eaId"])
        v=samples(series[key])
        if v: cards[key]=v
    groups=defaultdict(list)
    membership={}
    for c in catalog["cards"]:
        if c["state"]!="candidate": continue
        k=cohort_key(c)
        if k is None: continue
        key=str(c["eaId"])
        membership[key]=k
        if key in cards: groups[k].append(key)
    return {"cohorts":dict(groups),"membership":membership,"quoteTimestamp":catalog["quoteTimestamp"],"method":"same-day pre-band baseline to observed minimum; historical frequency only","minimumWindows":8,"snapshots":len(seen),"cards":cards}

def frequency(values,ratio):
    if len(values)<8: return None
    return {"hits":sum(v<=ratio for v in values),"n":len(values)}

def main():
    c=json.loads(Path("market-catalog.json").read_text())
    d=build(Path("market-archive"),c)
    Path("market-timing-statistics.json").write_text(json.dumps(d,separators=(",",":")))
    print("TIMING",d["snapshots"],"CARDS",len(d["cards"]))

class Tests(unittest.TestCase):
    def test_cohort(self):
        a={"quote":13000,"overall":86,"rarity":"Thunderstruck"}
        self.assertEqual(cohort_key(a),cohort_key(dict(a,quote=16000,overall=87)))
        self.assertNotEqual(cohort_key(a),cohort_key(dict(a,rarity="Rare")))
        self.assertIsNone(cohort_key(dict(a,quote=None)))
    def test_threshold(self):
        self.assertIsNone(frequency([.8]*7,.8))
        self.assertEqual(frequency([.8]*4+[.9]*4,.85),{"hits":4,"n":8})
    def test_band(self):
        rows=[(datetime(2026,11,27,h,m,tzinfo=ROME),p) for h,m,p in [(7,30,100),(8,0,95),(9,0,90),(10,0,80),(11,0,90)]]
        self.assertEqual(samples(rows),{"4:0":[.8]})
        self.assertEqual(samples(rows[:3]),{})
if __name__=="__main__": main()
