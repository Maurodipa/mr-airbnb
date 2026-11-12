import asyncio
import json
import math
import os

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MY_LAT = 41.8987
MY_LNG = 12.4698
RADIUS_METERS = 100.0
LOCATION_QUERY = "Piazza Navona, Rome, Lazio, Italy"
OUT_FILE = "competitors_100m.json"
DETAILS_FILE = "competitori_vicini_details.json"
MAX_PAGES = 15

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


    env = os.environ.copy()
    env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

    params = StdioServerParameters(
        command="node",
        args=["--use-system-ca", r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"],
        env=env
    )

    # Carica o inizializza il database separato per i vicini
    details_db = {}
    if os.path.exists(DETAILS_FILE):
        with open(DETAILS_FILE, encoding="utf-8") as f:
            details_db = json.load(f)

    found_apartments = []

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            page_cursors = []

            for page in range(0, MAX_PAGES):
                print(f"Scansione pagina {page+1}...")
                args = {
                    "location": LOCATION_QUERY,
                    "ignoreRobotsText": True
                }

                # Usa il cursore per le pagine successive alla prima
                if page > 0 and page < len(page_cursors):
                    args["cursor"] = page_cursors[page]
                elif page > 0:
                    print("Pagine terminate.")
                    break

                result = await session.call_tool("airbnb_search", arguments=args)

                content_str = result.content[0].text
                if not content_str or not content_str.strip():
                    print("Risposta vuota dall'API di ricerca (forse blocco anti-bot). Interrompo la scansione.")
                    break

                try:
                    content = json.loads(content_str)
                except Exception as e:
                    print(f"Errore parsing JSON dalla ricerca: {e}")
                    break

                if "error" in content:
                    print(f"Errore API: {content['error']}")
                    break

                results = content.get("searchResults", [])
                if not results:
                    print("Nessun risultato trovato in questa pagina. Fine.")
                    break

                for listing in results:
                    coords = extract_coords(listing)
                    if coords:
                        lat, lng = coords
                        dist = haversine(MY_LAT, MY_LNG, lat, lng)
                        if dist <= RADIUS_METERS:
                            # Extract useful info
                            apt_id = listing.get("id", "Sconosciuto")

                            # Cerca di estrarre il titolo
                            title = "Titolo sconosciuto"
                            try:
                                title = listing["listingParamOverrides"]["seoFeatures"]["title"]
                            except:
                                pass

                            found_apartments.append({
                                "id": apt_id,
                                "distance_meters": dist,
                                "lat": lat,
                                "lng": lng,
                                "title": title
                            })
                            print(f"--> Trovato! {apt_id} a {dist:.1f}m")

                if page == 0:
                    pagination = content.get("paginationInfo", {})
                    page_cursors = pagination.get("pageCursors", [])

                # Piccola pausa per non sovraccaricare il server
                await asyncio.sleep(2)

            # Ora abbiamo tutti gli appartamenti unici entro 100m
            unique_apts_list = list({apt["id"]: apt for apt in found_apartments}.values())

            print(f"\nTrovati {len(unique_apts_list)} appartamenti unici nel raggio di {RADIUS_METERS}m.")
            print("Inizio estrazione dei dettagli completi (descrizione, recensioni, stanze, ecc.)...")

            for apt in unique_apts_list:
                apt_id = apt["id"]
                if apt_id in details_db:
                    print(f"Dettagli completi per {apt_id} già presenti in {DETAILS_FILE}.")
                    continue

                print(f"Recupero dettagli completi per {apt_id}...")
                try:
                    res_det = await session.call_tool("airbnb_listing_details", arguments={"id": apt_id, "ignoreRobotsText": True})
                    if not res_det.content or not res_det.content[0].text.strip():
                        print(f"Risposta vuota per i dettagli di {apt_id}.")
                        await asyncio.sleep(2)
                        continue

                    try:
                        content_det = json.loads(res_det.content[0].text)
                    except Exception as e:
                        print(f"Errore parsing JSON dettagli {apt_id}: {e}")
                        await asyncio.sleep(2)
                        continue

                    if "details" in content_det:
                        details_db[apt_id] = content_det["details"]
                        print(f"--> Dettagli per {apt_id} salvati con successo!")

                        # Salva progressivamente il database in caso di interruzione
                        with open(DETAILS_FILE, "w", encoding="utf-8") as f:
                            json.dump(details_db, f, indent=2)
                    elif "sections" in content_det:
                        details_db[apt_id] = content_det["sections"]
                        print(f"--> Dettagli (sections) per {apt_id} salvati con successo!")
                        with open(DETAILS_FILE, "w", encoding="utf-8") as f:
                            json.dump(details_db, f, indent=2)
                    else:
                        print(f"Formato non riconosciuto per {apt_id}: {list(content_det.keys())}")
                except Exception as e:
                    print(f"Errore nel recupero dettagli per {apt_id}: {e}")

                await asyncio.sleep(1.5)

    final_list = sorted(unique_apts_list, key=lambda x: x["distance_meters"])

    print(f"\nScansione completata. Trovati {len(final_list)} appartamenti unici nel raggio di {RADIUS_METERS}m.")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2)
    print(f"Risultati salvati in {OUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scan_neighborhood())
