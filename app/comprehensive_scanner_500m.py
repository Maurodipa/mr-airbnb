import asyncio
import json
import math
import os

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MY_LAT = 41.8987
MY_LNG = 12.4698
RADIUS_METERS = 500.0
OUT_FILE = "competitors_500m_nov_10_14.json"
DETAILS_FILE = "competitori_vicini_500m_nov_10_14_details.json"
MAX_PAGES = 15

CHECKIN = "2026-11-10"
CHECKOUT = "2026-11-14"

LOCATION_QUERIES = [
    "Centro Storico, Rome, Lazio, Italy",
    "Piazza Navona, Rome, Lazio, Italy",
    "Campo de' Fiori, Rome, Lazio, Italy",
    "Pantheon, Rome, Lazio, Italy",
    "Palazzo Farnese, Rome, Lazio, Italy",
    "Senato, Rome, Lazio, Italy"
]

PRICE_BRACKETS = [
    {"minPrice": 0, "maxPrice": 120},
    {"minPrice": 120, "maxPrice": 250},
    {"minPrice": 250, "maxPrice": 9999}
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def extract_coords(obj):
    if isinstance(obj, dict):
        if "latitude" in obj and "longitude" in obj:
            return obj["latitude"], obj["longitude"]
        for v in obj.values():
            res = extract_coords(v)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = extract_coords(item)
            if res: return res
    return None

async def scan_neighborhood():
    print(f"Cerco appartamenti vicino a: {MY_LAT}, {MY_LNG}")
    print(f"Raggio: {RADIUS_METERS}m")
    print(f"Date: {CHECKIN} - {CHECKOUT}")

    env = os.environ.copy()
    env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

    params = StdioServerParameters(
        command="node",
        args=["--use-system-ca", r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"],
        env=env
    )

    details_db = {}
    if os.path.exists(DETAILS_FILE):
        with open(DETAILS_FILE, encoding="utf-8") as f:
            details_db = json.load(f)

    found_apartments_dict = {}
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding="utf-8") as f:
            for apt in json.load(f):
                found_apartments_dict[apt["id"]] = apt

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            for loc in LOCATION_QUERIES:
                for bracket in PRICE_BRACKETS:
                    print(f"\n--- Ricerca: {loc} | Prezzo: {bracket['minPrice']}-{bracket['maxPrice']} ---")
                    page_cursors = []

                    for page in range(0, MAX_PAGES):
                        args = {
                            "location": loc,
                            "minPrice": bracket["minPrice"],
                            "maxPrice": bracket["maxPrice"],
                            "checkin": CHECKIN,
                            "checkout": CHECKOUT,
                            "ignoreRobotsText": True
                        }

                        if page > 0 and page < len(page_cursors):
                            args["cursor"] = page_cursors[page]
                        elif page > 0:
                            break

                        result = await session.call_tool("airbnb_search", arguments=args)

                        content_str = result.content[0].text
                        if not content_str or not content_str.strip():
                            break

                        try:
                            content = json.loads(content_str)
                        except Exception:
                            break

                        if "error" in content:
                            break

                        results = content.get("searchResults", [])
                        if not results:
                            break

                        for listing in results:
                            coords = extract_coords(listing)
                            if coords:
                                lat, lng = coords
                                dist = haversine(MY_LAT, MY_LNG, lat, lng)
                                if dist <= RADIUS_METERS:
                                    apt_id = listing.get("id", "Sconosciuto")
                                    if apt_id not in found_apartments_dict:
                                        print(f"--> NUOVO TROVATO! {apt_id} a {dist:.1f}m")

                                        title = "Titolo sconosciuto"
                                        try:
                                            title = listing["listingParamOverrides"]["seoFeatures"]["title"]
                                        except:
                                            pass

                                        # Also extract the price for these dates!
                                        price = None
                                        try:
                                            price_str = listing.get("pricingQuote", {}).get("structuredStayDisplayPrice", {}).get("primaryLine", {}).get("price")
                                            if price_str:
                                                price = price_str
                                        except:
                                            pass

                                        found_apartments_dict[apt_id] = {
                                            "id": apt_id,
                                            "distance_meters": dist,
                                            "lat": lat,
                                            "lng": lng,
                                            "title": title,
                                            "price": price
                                        }

                        if page == 0:
                            pagination = content.get("paginationInfo", {})
                            page_cursors = pagination.get("pageCursors", [])

                        await asyncio.sleep(0.5)


            unique_apts_list = list(found_apartments_dict.values())
            print(f"\nTotale globale: Trovati {len(unique_apts_list)} appartamenti unici nel raggio di {RADIUS_METERS}m.")

            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(unique_apts_list, key=lambda x: x["distance_meters"]), f, indent=2)

            print("Inizio estrazione dei dettagli completi...")
            for apt in unique_apts_list:
                apt_id = apt["id"]
                if apt_id in details_db:
                    continue

                print(f"Recupero dettagli completi per {apt_id}...")
                try:
                    res_det = await session.call_tool("airbnb_listing_details", arguments={"id": apt_id, "ignoreRobotsText": True})
                    if not res_det.content or not res_det.content[0].text.strip():
                        await asyncio.sleep(1)
                        continue

                    try:
                        content_det = json.loads(res_det.content[0].text)
                    except Exception:
                        await asyncio.sleep(1)
                        continue

                    if "details" in content_det:
                        details_db[apt_id] = content_det["details"]
                        print(f"--> Dettagli per {apt_id} salvati con successo!")
                        with open(DETAILS_FILE, "w", encoding="utf-8") as f:
                            json.dump(details_db, f, indent=2)
                    elif "sections" in content_det:
                        details_db[apt_id] = content_det["sections"]
                        print(f"--> Dettagli (sections) per {apt_id} salvati con successo!")
                        with open(DETAILS_FILE, "w", encoding="utf-8") as f:
                            json.dump(details_db, f, indent=2)
                except Exception as e:
                    print(f"Errore nel recupero dettagli per {apt_id}: {e}")

                await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(scan_neighborhood())
