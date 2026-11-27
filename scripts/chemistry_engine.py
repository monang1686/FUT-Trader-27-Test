"""Experimental chemistry model. Thresholds are legacy assumptions, not verified FC27 rules."""
from collections import Counter
import unittest

def normalize(row):
    def ident(obj):
        v=(obj or {}).get("eaId")
        return v if type(v) is int and v>0 else None
    return dict(eaId=row.get("eaId"),baseId=row.get("basePlayerEaId"),
        name=row.get("cardName"),position=row.get("position"),
        alternatives=row.get("alternativePositions") or [],
        club=ident(row.get("club")),uniqueClub=ident(row.get("uniqueClub")),
        league=ident(row.get("league")),nation=ident(row.get("nation")),
        special=any(row.get(k) is not False for k in
            ("isIcon","isHero","hasExtraChemistry","isFullChemistry",
             "extraSquadLeagueChemistry","extraSquadNationChemistry"))
            or any(row.get(k)!=0 for k in
            ("extraClubChemistry","extraLeagueChemistry","extraNationChemistry")),
        stats=row.get("faceStatsV2"),image=row.get("cardImageUrl"),
        playStyles=row.get("playStyleEaIds"),playStylesPlus=row.get("playStylePlusEaIds"),
        rolesPlus=row.get("rolesPlus"),rolesPlusPlus=row.get("rolesPlusPlus"))

def chemistry(slots, manager=None):
    """Ordinary cards only; unknown special rules invalidate total rather than guess."""
    if len(slots)>11: raise ValueError("Maximum eleven starters")
    ids=[p.get("baseId") for _,p in slots]
    if any(type(i) is not int or i<=0 for i in ids) or len(set(ids))!=len(ids):
        raise ValueError("Missing or duplicate base player")
    eligible=[pos==p.get("position") or pos in p.get("alternatives",[]) for pos,p in slots]
    unsupported=any(p.get("special",True) or any(not p.get(k) for k in ("club","league","nation")) for _,p in slots)
    if unsupported:
        return {"total":None,"individual":[None if ok else 0 for ok in eligible],"status":"unsupported_metadata_or_special_rules"}
    counts={k:Counter(p[k] for (_,p),ok in zip(slots,eligible) if ok) for k in ("club","league","nation")}
    if manager:
        for k in ("league","nation"):
            if manager.get(k): counts[k][manager[k]]+=1
    thresholds={"club":(2,4,7),"league":(3,5,8),"nation":(2,5,8)}
    individual=[min(3,sum(sum(counts[k][p[k]]>=t for t in ts) for k,ts in thresholds.items())) if ok else 0 for (_,p),ok in zip(slots,eligible)]
    return {"total":sum(individual),"individual":individual,"status":"legacy_rules_unverified_fc27"}

class Tests(unittest.TestCase):
    def player(self,i,**kw):
        return dict(baseId=i,position="CM",alternatives=["CDM"],club=1,league=2,nation=3,special=False,**kw)
    def test_full(self):
        self.assertEqual(chemistry([("CM",self.player(i)) for i in range(1,12)])["total"],33)
    def test_wrong_position(self):
        self.assertEqual(chemistry([("ST",self.player(1)),("CM",self.player(2))])["individual"],[0,0])
    def test_alternative(self):
        self.assertEqual(chemistry([("CDM",self.player(1)),("CM",self.player(2))])["total"],4)
    def test_duplicate(self):
        with self.assertRaises(ValueError): chemistry([("CM",self.player(1)),("CM",self.player(1))])
    def test_special(self):
        p=self.player(1);p["special"]=True
        self.assertIsNone(chemistry([("CM",p)])["total"])
    def test_manager(self):
        self.assertEqual(chemistry([("CM",self.player(1))],{"nation":3})["total"],1)
    def test_missing_club(self):
        p=self.player(1);p["club"]=None
        self.assertIsNone(chemistry([("CM",p)])["total"])
if __name__=="__main__": unittest.main()
