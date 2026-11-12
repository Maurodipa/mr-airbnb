import argparse
import json
import random
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://127.0.0.1:9222"
USER_APT = "1589943047991118285"

def random_delay(min_s=1.2, max_s=2.5):
    time.sleep(random.uniform(min_s, max_s))

def close_side_panel(page):
    try:
        for selector in ['button[aria-label="Chiudi"]', 'button[aria-label="Close"]', 'button[aria-label="Indietro"]', 'button[aria-label="Back"]']:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                btn.click()
                page.wait_for_timeout(400)
                break
    except Exception:
        pass

def apply_updates(updates_list):
    successful = []
    skipped_booked = []
    failed = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"Errore connessione CDP su {CDP_URL}: {e}")
            sys.exit(1)

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        total = len(updates_list)
        print(f"\n🚀 Inizio aggiornamento di {total} date sul calendario Airbnb (Alloggio {USER_APT})...\n")

        for idx, item in enumerate(updates_list, start=1):
            d = item['date']
            target_price = int(item['price'])
            print(f"[{idx}/{total}] {d} -> {target_price} € ...", end=" ", flush=True)

            target_url = f"https://www.airbnb.it/multicalendar/{USER_APT}/edit-selected-dates/{d}/{d}"
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(800)

                # Verifica se l'input del prezzo è già visibile
                inp = page.locator('#PriceInput-nightlyPrice').first
                if not inp.is_visible():
                    price_btn = page.locator('button:has-text("Prezzo per notte")').first
                    try:
                        price_btn.wait_for(state="visible", timeout=3000)
                        price_btn.click()
                        page.wait_for_timeout(600)
                    except Exception:
                        # Se il bottone prezzo non c'è, controlla se la data è prenotata o non modificabile
                        body_txt = page.evaluate("() => document.body.innerText")
                        if "Prenotazione" in body_txt or "Non disponibile" in body_txt or "Riservato" in body_txt:
                            print("🔒 Prenotata su calendario reale, salto!", flush=True)
                            skipped_booked.append(d)
                            close_side_panel(page)
                            continue
                        else:
                            raise RuntimeError("Bottone 'Prezzo per notte' non visibile")

                inp = page.locator('#PriceInput-nightlyPrice').first
                inp.wait_for(state="visible", timeout=4000)

                current_val = inp.input_value().strip()
                if current_val == str(target_price):
                    print(f"✅ Già allineato ({target_price} €)!", flush=True)
                    successful.append((d, target_price))
                    close_side_panel(page)
                    random_delay(0.8, 1.5)
                    continue

                # Inserisci il nuovo prezzo
                inp.click(click_count=3)
                inp.fill(str(target_price))
                page.wait_for_timeout(300)

                # Clicca Salva se abilitato
                save_btn = page.locator('button:has-text("Salva")').first
                save_btn.wait_for(state="visible", timeout=3000)
                
                if save_btn.is_enabled():
                    save_btn.click(timeout=4000)
                    page.wait_for_timeout(1000)
                    print(f"✅ Impostato a {target_price} €!", flush=True)
                    successful.append((d, target_price))
                else:
                    print(f"✅ Già salvato ({target_price} €)", flush=True)
                    successful.append((d, target_price))

                close_side_panel(page)

            except Exception as e:
                err_msg = str(e).split("\n")[0]
                print(f"❌ Errore: {err_msg}", flush=True)
                failed.append((d, target_price, err_msg))
                close_side_panel(page)

            random_delay(1.0, 2.0)

    print("\n" + "=" * 60)
    print("📊 RIEPILOGO AGGIORNAMENTO")
    print("=" * 60)
    print(f"✅ Tariffe aggiornate con successo: {len(successful)}")
    if skipped_booked:
        print(f"🔒 Date saltate (già prenotate su calendario): {len(skipped_booked)}")
    if failed:
        print(f"❌ Errori non gestiti: {len(failed)}")
        for d, p, err in failed:
            print(f"   - {d} ({p} €): {err}")
    print("=" * 60 + "\n")
    return successful, failed

def main():
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", type=str, help="Filtra per mese (es. 2026-11)")
    parser.add_argument("--all", action="store_true", help="Aggiorna tutte le date in pending_price_updates.json")
    parser.add_argument("--dates", type=str, help="Date specifiche separate da virgola (YYYY-MM-DD)")
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

    apply_updates(selected)

if __name__ == "__main__":
    main()
