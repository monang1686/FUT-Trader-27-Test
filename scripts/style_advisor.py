"""Heuristic style suitability, not actual attribute boosts.
Source for affected categories: https://www.fut.gg/chemistry-styles/
"""
from squad_optimizer import KEYS, WEIGHTS, quality
import unittest
OUT={"Anchor":[0,4,5],"Architect":[2,5],"Artist":[2,3],"Backbone":[2,4,5],"Basic":list(range(6)),"Catalyst":[0,2],"Deadeye":[1,2],"Engine":[0,2,3],"Finisher":[1,3],"Gladiator":[1,3,4],"Guardian":[3,4],"Hawk":[0,1,5],"Hunter":[0,1],"Maestro":[1,2,3],"Marksman":[1,3,5],"Powerhouse":[2,4],"Sentinel":[4,5],"Shadow":[0,4],"Sniper":[1,5]}
GK={"Cat":[3,4,5],"GK Basic":list(range(6)),"Glove":[0,1,5],"Shield":[2,3,4],"Wall":[0,1,2]}
GK_KEYS=["gkFaceDiving","gkFaceHandling","gkFaceKicking","gkFaceReflexes","gkFaceSpeed","gkFacePositioning"]
def advise(player,position,chemistry):
    if type(chemistry) is not int or not 0<=chemistry<=3:
        return {"status":"unknown_chemistry","styles":[]}
    if position!=player.get("position") and position not in (player.get("alternatives") or []):
        return {"status":"out_of_position","styles":[]}
    if chemistry==0: return {"status":"no_boost","styles":[]}
    if quality(player,position) is None: return {"status":"missing_stats","styles":[]}
    keys=GK_KEYS if position=="GK" else KEYS
    styles=GK if position=="GK" else OUT
    weights=WEIGHTS.get(position,[3,3,1,4,1,3] if position=="GK" else [4,3,3,4,0,1])
    stats=player["stats"]
    ranked=[]
    for name,indices in styles.items():
        # Equal notional emphasis distributed over targeted categories.
        # Headroom is a preference, not a predicted face-stat change.
        scores=[weights[i]*min(1,(99-stats[keys[i]])/15) for i in indices]
        score=sum(scores)/len(indices)
        ranked.append({"name":name,"suitability":round(score,3),"targets":[keys[i] for i in indices],"actualBoosts":None})
    ranked.sort(key=lambda x:(-x["suitability"],x["name"]))
    return {"status":"heuristic_only","chemistry":chemistry,"styles":[x for x in ranked if x["suitability"]>0][:3],"source":"https://www.fut.gg/chemistry-styles/"}
class Tests(unittest.TestCase):
    def player(self,pos="ST"):
        return {"position":pos,"alternatives":[],"stats":{k:80 for k in KEYS+GK_KEYS}}
    def test_three(self):
        self.assertEqual(len(advise(self.player(),"ST",3)["styles"]),3)
    def test_zero(self):
        self.assertEqual(advise(self.player(),"ST",0)["styles"],[])
    def test_unknown(self):
        self.assertEqual(advise(self.player(),"ST",None)["status"],"unknown_chemistry")
    def test_gk(self):
        self.assertTrue(all(x["name"] in GK for x in advise(self.player("GK"),"GK",3)["styles"]))
    def test_cap(self):
        p=self.player();p["stats"]={k:99 for k in KEYS}
        self.assertEqual(advise(p,"ST",3)["styles"],[])
    def test_missing(self):
        p=self.player();p["stats"]={}
        self.assertEqual(advise(p,"ST",3)["status"],"missing_stats")
    def test_position(self):
        self.assertEqual(advise(self.player(),"CB",3)["status"],"out_of_position")
if __name__=="__main__": unittest.main()
