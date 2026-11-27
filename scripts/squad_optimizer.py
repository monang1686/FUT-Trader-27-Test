"""Experimental bounded beam search; not a global optimum or verified market."""
from chemistry_engine import chemistry
import unittest
FORMATIONS={"4-3-3":["GK","LB","CB","CB","RB","CM","CM","CM","LW","ST","RW"],"4-4-2":["GK","LB","CB","CB","RB","LM","CM","CM","RM","ST","ST"],"4-2-3-1":["GK","LB","CB","CB","RB","CDM","CDM","CAM","CAM","CAM","ST"]}
KEYS=["facePace","faceShooting","facePassing","faceDribbling","faceDefending","facePhysicality"]
WEIGHTS={"CB":[2,0,1,0,5,4],"ST":[3,5,1,3,0,1],"CM":[1,1,4,3,3,2],"CDM":[1,0,3,2,5,3],"CAM":[2,3,4,4,0,1],"LB":[4,0,2,2,4,2],"RB":[4,0,2,2,4,2]}
def quality(p,pos):
    s=p.get("stats") or {}
    keys=KEYS if pos!="GK" else ["gkFaceDiving","gkFaceHandling","gkFaceKicking","gkFaceReflexes","gkFaceSpeed","gkFacePositioning"]
    w=WEIGHTS.get(pos,[4,3,3,4,0,1] if pos!="GK" else [3,3,1,4,1,3])
    if any(type(s.get(k)) is not int or not 0<=s[k]<=99 for k in keys): return None
    return sum(s[k]*v for k,v in zip(keys,w))/sum(w)

def optimize(cards,formation,budget,leagues=(),owned=(),locked=None,manager=None,width=100):
    positions=FORMATIONS[formation]
    locked=locked or {}; owned=set(owned); leagues=set(leagues)
    if type(budget) is not int or budget<0 or len(leagues)>3 or not 1<=width<=500: raise ValueError("Invalid constraints")
    if any(type(i) is not int or not 0<=i<11 for i in locked): raise ValueError("Invalid slot")
    pools=[]
    for i,pos in enumerate(positions):
        pool=[]
        for c in cards:
            p=c.get("squad") or {}; eid=c.get("eaId"); base=p.get("baseId")
            if type(eid) is not int or type(base) is not int or base<=0 or eid!=p.get("eaId"): continue
            if i in locked and eid!=locked[i]: continue
            if i not in locked and eid in locked.values(): continue
            if leagues and p.get("league") not in leagues: continue
            if pos!=p.get("position") and pos not in p.get("alternatives",[]): continue
            cost=0 if eid in owned else c.get("quote")
            if eid not in owned and (c.get("state")!="candidate" or type(cost) is not int or cost<=0): continue
            q=quality(p,pos)
            if q is None or cost>budget: continue
            pool.append((p,cost,q))
        pools.append(pool)
    order=sorted(range(11),key=lambda i:len(pools[i]))
    states=[({},0,0)]
    for i in order:
        nxt=[]
        for selected,cost,score in states:
            used={p["baseId"] for p in selected.values()}
            for p,price,q in pools[i]:
                if p["baseId"] in used or cost+price>budget: continue
                new={**selected,i:p}
                if len({v.get("league") for v in new.values()})>3: continue
                ch=chemistry([(positions[j],v) for j,v in new.items()],manager)["total"]
                nxt.append((new,cost+price,score+q,ch))
        nxt.sort(key=lambda x:(x[3] is not None,x[3] or 0,x[2],-x[1]),reverse=True)
        states=[(a,b,c) for a,b,c,_ in nxt[:width]]
        if not states: return {"status":"no_solution_found","exhaustive":False}
    selected,cost,score=states[0]
    slots=[(pos,selected[i]) for i,pos in enumerate(positions)]
    return {"status":"experimental","slots":[{"position":pos,"eaId":p["eaId"]} for pos,p in slots],"cost":cost,"remaining":budget-cost,"quality":round(score/11,2),"chemistry":chemistry(slots,manager),"exhaustive":False}

class Tests(unittest.TestCase):
    def cards(self):
        return [{"eaId":i,"state":"candidate","quote":100,"squad":{"eaId":i,"baseId":i,"position":pos,"alternatives":[],"club":1,"league":2,"nation":3,"special":False,"stats":{k:80 for k in KEYS+["gkFaceDiving","gkFaceHandling","gkFaceKicking","gkFaceReflexes","gkFaceSpeed","gkFacePositioning"]}}} for i,pos in enumerate(FORMATIONS["4-3-3"],1)]
    def test_full(self):
        x=optimize(self.cards(),"4-3-3",1100)
        self.assertEqual(x["chemistry"]["total"],33)
        self.assertEqual(x["cost"],1100)
    def test_budget(self):
        self.assertEqual(optimize(self.cards(),"4-3-3",1099)["status"],"no_solution_found")
    def test_owned_locked(self):
        c=self.cards();c[0]["state"]="excluded";c[0]["quote"]=None
        self.assertEqual(optimize(c,"4-3-3",1000,owned=[1],locked={0:1})["cost"],1000)
    def test_league(self):
        self.assertEqual(optimize(self.cards(),"4-3-3",1100,leagues=[3])["status"],"no_solution_found")
    def test_duplicate(self):
        c=self.cards();c[1]["squad"]["baseId"]=1
        self.assertEqual(optimize(c,"4-3-3",1100)["status"],"no_solution_found")
if __name__=="__main__": unittest.main()
