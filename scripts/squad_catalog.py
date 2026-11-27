from chemistry_engine import normalize
import unittest

def enrich(row):
    p=normalize(row)
    for key in ("club","league","nation"):
        obj=row.get(key)
        p[key+"Name"]=obj.get("name") if isinstance(obj,dict) else None
    p["weakFoot"]=row.get("weakFoot")
    p["skillMoves"]=row.get("skillMoves")
    p["foot"]=row.get("foot")
    p["gender"]=row.get("gender")
    p["completeStats"]=row.get("hasCompleteFaceStats") is True
    p["chemistryFlags"]={k:row.get(k) for k in ("isIcon","isHero","hasExtraChemistry","isFullChemistry","extraClubChemistry","extraLeagueChemistry","extraNationChemistry","extraSquadLeagueChemistry","extraSquadNationChemistry")}
    p["chemistryVerified"]=False
    return p

class Tests(unittest.TestCase):
    def test_identity(self):
        p=enrich({"eaId":123,"basePlayerEaId":42,"position":"ST","alternativePositions":["LW"],"league":{"eaId":53,"name":"Liga"}})
        self.assertEqual((p["eaId"],p["baseId"],p["league"],p["leagueName"]),(123,42,53,"Liga"))
        self.assertEqual(p["alternatives"],["LW"])
    def test_missing(self):
        p=enrich({})
        self.assertIsNone(p["club"])
        self.assertTrue(p["special"])
        self.assertFalse(p["chemistryVerified"])
    def test_special(self):
        p=enrich({"isHero":True,"extraLeagueChemistry":1})
        self.assertTrue(p["special"])
        self.assertEqual(p["chemistryFlags"]["extraLeagueChemistry"],1)
    def test_stats(self):
        p=enrich({"faceStatsV2":{"facePace":93},"hasCompleteFaceStats":True,"playStylePlusEaIds":[16]})
        self.assertEqual(p["stats"]["facePace"],93)
        self.assertEqual(p["playStylesPlus"],[16])
        self.assertTrue(p["completeStats"])

if __name__=="__main__": unittest.main()
