import re
import sys
from datetime import datetime
import json
import os
import glob

STATE_FILE = 'monitor_state.json'

tasks_dir = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\.system_generated\tasks'
log_files = glob.glob(os.path.join(tasks_dir, 'task-*.log'))

target_log = None
for fpath in sorted(log_files, key=os.path.getmtime, reverse=True):
    try:
        with open(fpath, encoding='utf-8') as f:
            content_sample = f.read(10000)
            if 'SECONDO PASSAGGIO' in content_sample or 'scan_seconda_fase' in content_sample or 'airbnb_listing_price' in content_sample or 'Airbnb MCP Server' in content_sample:
                target_log = fpath
                break

    except:
        pass

if not target_log:
    print("Nessun file di log attivo trovato per lo scanner.")
    sys.exit(0)

with open(target_log, encoding='utf-8', errors='ignore') as f:
    content = f.read()

pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\] \[INFO\] Tool call received:[^{]*?\{[^}]*?\"checkin\":\s*\"(\d{4}-\d{2}-\d{2})\"'
matches = re.findall(pattern, content)

cooldown_count = content.count('[PAUSA SICUREZZA]')
has_100_percent = 'Scansione Fase 2 completata AL 100%!' in content

day_starts = {}
for timestamp_str, checkin_date in matches:
    if checkin_date not in day_starts:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        day_starts[checkin_date] = dt


if not day_starts:
    print(f"Nessun dato ancora per Fase 2. Cooldown attivati: {cooldown_count} volte.")
    sys.exit(0)

sorted_days = sorted(list(day_starts.keys()))
num_started = len(sorted_days)

if num_started <= 1:
    print(f"Scansione Fase 2 in corso per il giorno 1 ({sorted_days[0]}). Non ci sono ancora medie calcolabili. Cooldown attivati: {cooldown_count} volte.")
    sys.exit(0)

num_completed = num_started - 1

first_day_start = day_starts[sorted_days[0]]
last_day_start = day_starts[sorted_days[-1]]

total_duration = (last_day_start - first_day_start).total_seconds()
avg_time_per_day = total_duration / num_completed

print(f"Giorni completati (Fase 2): {num_completed}")
print(f"Ultimo giorno completato: {sorted_days[num_completed-1]}")
print(f"Giorno attualmente in scansione: {sorted_days[-1]}")
print(f"Tempo medio per giorno (su {num_completed} giorni): {avg_time_per_day/60:.1f} minuti")
print(f"Cooldown attivati: {cooldown_count} volte")

state = {'last_reported_block': 0}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, 'r') as f: state = json.load(f)
    except: pass

current_block = num_completed // 5
if has_100_percent or (num_completed >= 41 and '2027-01-31' in sorted_days):
    print(f"\n--- ALLERTA PER AGENTE: SCANSIONE FASE 2 COMPLETATA AL 100%! ---")
    state['completed'] = True
    with open(STATE_FILE, 'w') as f: json.dump(state, f)
elif current_block > state.get('last_reported_block', 0):
    print(f"\n--- ALLERTA PER AGENTE: UN NUOVO BLOCCO DI 5 GIORNI E' STATO COMPLETATO! (Blocco {current_block}) ---")
    state['last_reported_block'] = current_block
    with open(STATE_FILE, 'w') as f: json.dump(state, f)
else:
    print(f"\nSiamo al blocco {current_block} (non ancora 5 nuovi).")

