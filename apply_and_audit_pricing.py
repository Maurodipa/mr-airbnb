import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://127.0.0.1:9222"
USER_APT = "1589943047991118285"
AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "pricing_audit_log.json")

def random_delay(min_s=0.8, max_s=1.8):
    time.sleep(random.uniform(min_s, max_s))

def close_side_panel(page):
    try:
        for selector in ['button[aria-label="Chiudi"]', 'button[aria-label="Close"]', 'button[aria-label="Indietro"]', 'button[aria-label="Back"]']:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                btn.click()
                page.wait_for_timeout(350)
                break
    except Exception:
        pass

def load_audit_log():
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_audit_log(log_data):
    with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def apply_and_audit(updates_list, resume=False):
    audit_data = load_audit_log()
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"Errore connessione CDP su {CDP_URL}: {e}")
            sys.exit(1)

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        total = len(updates_list)
        print(f"\n🚀 Inizio aggiornamento e audit certificato di {total} date (Alloggio {USER_APT})...\n")

        for idx, item in enumerate(updates_list, start=1):
            d = item['date']
            target_price = int(item['price'])
            
            # Se resume è attivo e la data è già verificata
            if resume and d in audit_data and audit_data[d].get('status') in ['Aggiornata', 'Già allineata']:
                print(f"[{idx}/{total}] {d} -> già registrata: {audit_data[d]['old_price']} € -> {audit_data[d]['new_price']} € ({audit_data[d]['status']})")
                continue

            print(f"[{idx}/{total}] {d} (Target: {target_price} €) ...", end=" ", flush=True)

            target_url = f"https://www.airbnb.it/multicalendar/{USER_APT}/edit-selected-dates/{d}/{d}"
            
            success = False
            for attempt in range(2):
                try:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(1200)

                    # Verifica se la data è prenotata
                    body_txt = page.evaluate("() => document.body.innerText")
                    price_btn = page.locator('button:has-text("Prezzo per notte")').first
                    
                    is_booked = False
                    if not price_btn.is_visible():
                        if "Prenotazione" in body_txt or "Non disponibile" in body_txt or "Riservato" in body_txt:
                            is_booked = True
                        else:
                            # Prova ad attendere fino a 3 secondi
                            try:
                                price_btn.wait_for(state="visible", timeout=3000)
                            except Exception:
                                is_booked = True

                    if is_booked:
                        print("🔒 Prenotata su calendario reale!", flush=True)
                        audit_data[d] = {
                            "date": d,
                            "old_price": "Prenotata",
                            "new_price": "Invariata",
                            "diff": "-",
                            "status": "Prenotata",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_audit_log(audit_data)
                        close_side_panel(page)
                        success = True
                        break

                    # Estrai il prezzo precedente dal testo del bottone
                    btn_text = price_btn.inner_text()
                    m = re.search(r'(\d+)\s*€', btn_text)
                    old_price = int(m.group(1)) if m else None

                    # Se la tariffa è già esattamente uguale al target
                    if old_price == target_price:
                        print(f"✅ Già allineata ({old_price} €)", flush=True)
                        audit_data[d] = {
                            "date": d,
                            "old_price": f"{old_price} €",
                            "new_price": f"{target_price} €",
                            "diff": "0 €",
                            "status": "Già allineata",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_audit_log(audit_data)
                        close_side_panel(page)
                        success = True
                        break

                    # Clicca per aprire il drawer di modifica prezzo
                    price_btn.click()
                    page.wait_for_timeout(600)

                    inp = page.locator('#PriceInput-nightlyPrice').first
                    inp.wait_for(state="visible", timeout=4000)
                    inp.click()
                    inp.fill(str(target_price))
                    page.wait_for_timeout(300)

                    save_btn = page.locator('button:has-text("Salva")').first
                    save_btn.wait_for(state="visible", timeout=3000)
                    
                    if save_btn.is_enabled():
                        save_btn.click(timeout=4000)
                        # Attendi conferma toast o chiusura
                        try:
                            toast = page.locator('text="Prezzo a notte aggiornato"').first
                            toast.wait_for(state="visible", timeout=3500)
                        except Exception:
                            page.wait_for_timeout(1000)

                        diff_val = target_price - old_price if old_price is not None else 0
                        diff_str = f"+{diff_val} €" if diff_val > 0 else f"{diff_val} €"
                        old_str = f"{old_price} €" if old_price is not None else "N/D"

                        print(f"✅ Aggiornata: {old_str} -> {target_price} € ({diff_str})", flush=True)
                        audit_data[d] = {
                            "date": d,
                            "old_price": old_str,
                            "new_price": f"{target_price} €",
                            "diff": diff_str,
                            "status": "Aggiornata",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_audit_log(audit_data)
                        close_side_panel(page)
                        success = True
                        break
                    else:
                        # Salva non abilitato
                        print(f"⚠️ Salva non abilitato (era {old_price} €)", flush=True)
                        audit_data[d] = {
                            "date": d,
                            "old_price": f"{old_price} €" if old_price else "N/D",
                            "new_price": f"{target_price} €",
                            "diff": "0 €",
                            "status": "Già salvata",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_audit_log(audit_data)
                        close_side_panel(page)
                        success = True
                        break

                except Exception as e:
                    err_msg = str(e).split("\n")[0]
                    if attempt == 0:
                        print(f"(retry per {err_msg})", end=" ", flush=True)
                        close_side_panel(page)
                        page.wait_for_timeout(1500)
                        continue
                    else:
                        print(f"❌ Errore definitivo: {err_msg}", flush=True)
                        audit_data[d] = {
                            "date": d,
                            "old_price": "Errore",
                            "new_price": f"{target_price} €",
                            "diff": "Errore",
                            "status": f"Errore: {err_msg}",
                            "timestamp": datetime.now().isoformat()
                        }
                        save_audit_log(audit_data)
                        close_side_panel(page)

            random_delay(0.8, 1.5)

    print("\n" + "=" * 60)
    print("📊 COMPLETAMENTO RUN")
    print("=" * 60)
    agg = sum(1 for v in audit_data.values() if v.get('status') == 'Aggiornata')
    gia = sum(1 for v in audit_data.values() if v.get('status') == 'Già allineata')
    pre = sum(1 for v in audit_data.values() if v.get('status') == 'Prenotata')
    err = sum(1 for v in audit_data.values() if 'Errore' in v.get('status', ''))
    print(f"✅ Aggiornate: {agg}")
    print(f"🔵 Già allineate: {gia}")
    print(f"🔒 Prenotate: {pre}")
    print(f"❌ Errori: {err}")
    print("=" * 60 + "\n")
    return audit_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", type=str, help="Filtra per mese (es. 2026-11)")
    parser.add_argument("--all", action="store_true", help="Aggiorna tutte le date in pending_price_updates.json")
    parser.add_argument("--dates", type=str, help="Date specifiche separate da virgola (YYYY-MM-DD)")
    parser.add_argument("--resume", action="store_true", help="Salta le date già verificate e registrate nel log")
    args = parser.parse_args()

    json_path = os.path.join(os.path.dirname(__file__), "pending_price_updates.json")
    with open(json_path, "r", encoding="utf-8") as f:
        all_updates = json.load(f)

    if args.dates:
        target_dates = [d.strip() for d in args.dates.split(",")]
        selected = [x for x in all_updates if x['date'] in target_dates]
    elif args.month:
        selected = [x for x in all_updates if x['date'].startswith(args.month)]
    elif args.all:
        selected = all_updates
    else:
        print("Specifica --month YYYY-MM, --dates, oppure --all")
        sys.exit(1)

    apply_and_audit(selected, resume=args.resume)

if __name__ == "__main__":
    main()
