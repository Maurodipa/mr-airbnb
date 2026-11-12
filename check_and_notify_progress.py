import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = os.path.join(os.path.dirname(__file__), 'progress_alert_state.json')
DB_FILE = os.path.join(os.path.dirname(__file__), 'banca_dati_airbnb_MCPserver.json')
SESS_FILE = os.path.join(os.path.dirname(__file__), '.current_scan_session.json')

if not os.path.exists(STATE_FILE):
    state = {'last_reported_count': 43, 'step_size': 15, 'next_threshold': 58}
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
else:
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)

if not os.path.exists(DB_FILE) or not os.path.exists(SESS_FILE):
    print("Database o sessione non trovati.")
    sys.exit(0)

with open(SESS_FILE, 'r', encoding='utf-8') as f:
    sess = json.load(f)
s_time = sess.get('start_time')

with open(DB_FILE, 'r', encoding='utf-8') as f:
    db = json.load(f)

dates = sorted([d for d in db.keys() if '2026-11-08' <= d <= '2027-02-28'])
completed = []
in_prog = None

for d in dates:
    scanned = sum(1 for apt, v in db[d].items() if v.get('collected_at', '') >= s_time)
    if scanned == 37:
        completed.append(d)
    else:
        in_prog = (d, scanned)
        break

curr_count = len(completed)
next_thresh = state.get('next_threshold', 58)

print(f"Current completed: {curr_count}/{len(dates)} dates. Next threshold: {next_thresh}")
if curr_count >= next_thresh or curr_count == len(dates):
    print("THRESHOLD_REACHED: YES")
    state['last_reported_count'] = curr_count
    state['next_threshold'] = curr_count + state.get('step_size', 15)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
else:
    print("THRESHOLD_REACHED: NO")
