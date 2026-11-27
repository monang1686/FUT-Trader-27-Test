"""Persist observed identities only; never manufacture prices."""
import json
from pathlib import Path
from datetime import datetime, timezone
def merge(previous, snapshots):
    rows={}
    for row in previous:
        rows[tuple(row["identity"])]=row
    for snap in snapshots:
        stamp=snap["updated_at"]
        t=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        if t.tzinfo is None or t>datetime.now(timezone.utc): continue
        for c in snap["cards"]:
            if c.get("ea_id") is None or not c.get("name"): continue
            key=(c["ea_id"],c.get("group"),c.get("rarity_id"))
            old=rows.get(key)
            if old and datetime.fromisoformat(old["last_seen"].replace("Z","+00:00"))>=t: continue
            rows[key]={"identity":list(key),"name":c["name"],"rating":c.get("rating"),"last_seen":stamp}
    return sorted(rows.values(),key=lambda r: str(r["identity"]))
def main():
    p=Path("data/catalog.json")
    old=json.loads(p.read_text())["cards"] if p.exists() else []
    history=json.loads(Path("data/history.json").read_text())["snapshots"]
    latest=json.loads(Path("data/latest.json").read_text())
    cards=merge(old,history+[latest])
    p.write_text(json.dumps({"schema":1,"cards":cards},ensure_ascii=False,separators=(",",":"))+"\n")
    print("Persistent observed identities:",len(cards))
if __name__=="__main__": main()
