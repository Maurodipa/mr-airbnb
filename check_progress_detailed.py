import json
import os
from datetime import datetime

import time

OUT_FILE = "C:/Docs/Personnel et confidentiel/Corsi e Formazioni/2026-06-14 Kaggle_5-Day AI Agents/agy2-projects/my-first-project/mr-airbnb/banca_dati_airbnb_MCPserver.json"

try:
    data = None
    for attempt in range(5):
        try:
            with open(OUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            break
        except json.JSONDecodeError:
            time.sleep(2)
            
    if not data:
        raise Exception("Impossibile leggere il JSON dopo 5 tentativi (file in scrittura).")

    
    # Trova la data più recente che ha MENO di 51 appartamenti
    dates = [k for k in data.keys() if k != 'static_details' and k >= '2026-11-13']
    dates.sort()
    
    latest_time = ""
    latest_date = None
    apts_updated_today = 0
    
    # Per statistica tempo e sintesi
    completed_today_dates = []
    
    # Trova la prima data con meno di 51 appartamenti in Fase 2
    for d in dates:
        updated_today_count = 0
        date_max_time = ""
        date_min_time = "9999-99-99"
        
        for apt_data in data[d].values():
            if isinstance(apt_data, dict):
                c_at = apt_data.get('collected_at', '')
                if c_at > date_max_time:
                    date_max_time = c_at
                if c_at and c_at < date_min_time:
                    date_min_time = c_at
                    
                if c_at >= "2026-09-28T15:30:00":
                    updated_today_count += 1
                    
        if updated_today_count == 51:
            completed_today_dates.append((d, date_min_time, date_max_time))
        elif latest_date is None:
            latest_date = d
            apts_updated_today = updated_today_count

    if latest_date:
        print(f"Data attualmente in scansione (dal JSON): {latest_date}")
        print(f"Appartamenti RE-interrogati (Fase 3) per questa data: {apts_updated_today} su 51 totali")
    else:
        print("Nessuna data trovata.")
        
    if completed_today_dates:
        total_seconds = 0
        valid_dates = 0
        for d, tmin, tmax in completed_today_dates:
            try:
                t1 = datetime.fromisoformat(tmin)
                t2 = datetime.fromisoformat(tmax)
                total_seconds += (t2 - t1).total_seconds()
                valid_dates += 1
            except:
                pass
        if valid_dates > 0:
            avg_minutes = (total_seconds / valid_dates) / 60
            print(f"Tempo medio di scansione giornaliero: {avg_minutes:.1f} minuti per data.")
            
            # Calcolo tempo reale dell'ultima data completata
            last_d, last_tmin, last_tmax = completed_today_dates[-1]
            try:
                lt1 = datetime.fromisoformat(last_tmin)
                lt2 = datetime.fromisoformat(last_tmax)
                last_duration_min = (lt2 - lt1).total_seconds() / 60
                print(f"Tempo reale di scansione dell'ultima data completata ({last_d}): {last_duration_min:.1f} minuti.")
            except:
                pass
            
        # Controlla se abbiamo un multiplo di 5 date completate OGGI
        if valid_dates > 0 and valid_dates % 5 == 0:
            # Ordina le date
            completed_strs = [x[0] for x in completed_today_dates]
            completed_strs.sort()
            
            # Prendi le ultime 5
            last_5 = completed_strs[-5:]
            start_5 = last_5[0]
            end_5 = last_5[-1]
            
            sintesi_file = f"C:/Users/mauro/.gemini/antigravity/brain/b63ef745-8fc3-4ec8-a1a4-9341f241e9c5/sintesi_mercato_{start_5}_to_{end_5}.md"
            if not os.path.exists(sintesi_file):
                print(f"--> Trigger automatico: 5 nuove date completate. Generazione sintesi per {start_5} - {end_5}...")
                # Run the synthesis script via os.system or subprocess
                # But since we just need to run it, we can create the file to mark it as done, 
                # then run the generator
                with open(sintesi_file, "w") as f:
                    f.write(f"# Sintesi Automatica {start_5} a {end_5}\n\n*Generazione in corso...*\n")
                
                # We can call genera_sintesi_mercato.py using uv run
                os.system(f"uv run python genera_sintesi_mercato.py > \"{sintesi_file}\"")
                print(f"Sintesi generata con successo!")

except Exception as e:
    print(f"Errore lettura JSON: {e}")
