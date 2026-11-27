import json
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from full_market_decoder_probe import decode, get

BASE = "https://www.fut.gg/api/fut/players/v2/27/"
PRICE = "https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg/27/cdn-data/player-prices-ps5.json"

def identities(rows, prices, known):
    found = {}
    for row in rows:
        i = row.get("eaId")
        if type(i) is not int or i <= 0:
            continue
        identity = (row.get("cardName"), row.get("overall"), row.get("rarityName"))
        if i in found and found[i] != identity:
            raise ValueError("Conflicting card identity")
        found[i] = identity
    matched = {i for i in found if prices.get(i, 0) > 0}
    return found, matched, matched - known

def main():
    assert identities([{"eaId": 7, "cardName": "Test"}], {7: 100}, set())[2] == {7}
    prices = decode(get(PRICE))
    feed = get("https://fc27-market.val.run/latest")
    known = {c["eaId"] for group in feed["groups"].values() for c in group}
    rows = []
    seen = set()
    for page in range(1, 4):
        url = BASE + "?" + urlencode({"page": page})
        with urlopen(Request(url, headers={"Accept": "application/json", "User-Agent": "FUT-Trader-27-Diagnostic/1.0"}), timeout=25) as r:
            raw = r.read(8000001)
            if len(raw) > 8000000:
                raise ValueError("Response too large")
            obj = json.loads(raw)
        batch = obj["data"]
        if not isinstance(batch, list) or any(not isinstance(x, dict) for x in batch):
            raise ValueError("Unexpected schema")
        ids = {x.get("eaId") for x in batch if type(x.get("eaId")) is int}
        print("PAGE", page, "reported", obj.get("currentPage"), "total", obj.get("total"), "rows", len(batch), "next", bool(obj.get("next")), "new IDs", len(ids-seen))
        if page > 1 and not ids-seen:
            print("Pagination did not advance; stopping")
            break
        rows.extend(batch)
        seen.update(ids)
        if not obj.get("next"):
            break
        time.sleep(1)
    found, matched, new = identities(rows, prices, known)
    print("SUMMARY catalog IDs", len(found), "positive price matches", len(matched), "new matches", len(new))
    for i in sorted(new)[:10]:
        print("NEW MATCH", i, found[i], "quote", prices[i])
    print("Diagnostic only; exact eaId matches, no independent price verification or catalog publication.")
if __name__ == "__main__":
    main()
