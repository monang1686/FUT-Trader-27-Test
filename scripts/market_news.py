import json, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
out = {"checked_at": datetime.now(timezone.utc).isoformat(), "status": "unavailable", "items": []}
try:
    req = urllib.request.Request("https://fifauteam.com/category/news/feed/", headers={"User-Agent":"FUT-Trader-News/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read(2000001)
    if len(raw)>2000000: raise ValueError("oversize")
    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None: raise ValueError("not RSS")
    seen=set()
    for item in channel.findall("item"):
        title=(item.findtext("title") or "").strip()
        link=(item.findtext("link") or "").strip()
        url=urlparse(link)
        if url.scheme!="https" or url.hostname not in ("fifauteam.com","www.fifauteam.com") or link in seen: continue
        if not any(x in (title+" "+link).lower() for x in ("fc 27","fc27","fc-27")): continue
        try: published=parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
        except (TypeError, ValueError): continue
        if published>datetime.now(timezone.utc): continue
        seen.add(link)
        out["items"].append({"title":title,"url":link,"published":published.isoformat()})
    out["items"].sort(key=lambda x:x["published"],reverse=True)
    out["items"]=out["items"][:15]
    out["status"]="ok"
except Exception as exc:
    print("Source unavailable:",type(exc).__name__)
print(out["status"],len(out["items"]))
with open("market-news.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
