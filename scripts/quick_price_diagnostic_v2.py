import asyncio
from datetime import datetime, timezone
from futbin_sdk import FutbinClient, Platform

async def main():
    successes=0
    async with FutbinClient(year=27, timeout=15) as client:
        for name in ["Rashford","Pedri","Mbappe","Haaland","Oblak"]:
            try:
                hits=await client.search_players(query=name)
                print(name, "matches:",len(hits))
                for h in hits[:3]:
                    print("identity:",h.name,h.futbin_id,h.resource_id,getattr(h,"rating",None))
                if hits:
                    h=hits[0]
                    p=await client.get_player_price(h.futbin_id,Platform.PS)
                    print("PS:",p.price,"source timestamp:",getattr(p,"updated_at",None),"retrieved:",datetime.now(timezone.utc).isoformat())
                    if isinstance(p.price,int) and p.price>0: successes+=1
            except Exception as e:
                print(name,type(e).__name__,str(e)[:200])
                if any(s in str(e) for s in ("403","429","401")): break
            await asyncio.sleep(3)
    print("Successful price queries:",successes)
    if not successes: raise SystemExit(1)
if __name__=="__main__": asyncio.run(main())
