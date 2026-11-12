import asyncio
import json
import math
import os

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MY_LAT = 41.8987
MY_LNG = 12.4698

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def extract_coords(obj):
    if isinstance(obj, dict):
        if 'latitude' in obj and 'longitude' in obj:
            return obj['latitude'], obj['longitude']
        if 'lat' in obj and 'lng' in obj:
            return obj['lat'], obj['lng']
        for v in obj.values():
            res = extract_coords(v)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = extract_coords(item)
            if res: return res
    return None

async def check_distances():
    env = os.environ.copy()
    env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

    params = StdioServerParameters(
        command="node",
        args=["--use-system-ca", r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"],
        env=env
    )

    competitors = []
    with open("competitors.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("1589943047991118285"):
                continue
            parts = line.split(":")
            if len(parts) >= 3:
                competitors.append((parts[0], parts[2]))

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            for apt_id, name in competitors:
                try:
                    res_det = await session.call_tool("airbnb_listing_details", arguments={"id": apt_id, "ignoreRobotsText": True})
                    if not res_det.content or not res_det.content[0].text.strip():
                        print(f"{name} ({apt_id}): errore (risposta vuota)")
                        continue

                    content_det = json.loads(res_det.content[0].text)
                    coords = None

                    if "details" in content_det:
                        coords = extract_coords(content_det["details"])
                    elif "sections" in content_det:
                        coords = extract_coords(content_det["sections"])

                    if coords:
                        dist = haversine(MY_LAT, MY_LNG, coords[0], coords[1])
                        print(f"{name} ({apt_id}): {dist:.1f} metri")
                    else:
                        print(f"{name} ({apt_id}): coordinate non trovate nel JSON")
                except Exception as e:
                    print(f"{name} ({apt_id}): errore - {e}")

                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(check_distances())
