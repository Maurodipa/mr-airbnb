import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Read February table from raccomandazioni_prezzi_totali_nov26_feb27.md
with open(r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\raccomandazioni_prezzi_totali_nov26_feb27.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

feb_start = False
feb_rows = []

for line in lines:
    if '## 📅 Febbraio 2027' in line:
        feb_start = True
    if feb_start and line.startswith('| 2027-02-'):
        parts = [p.strip() for p in line.split('|')[1:-1]]
        # parts:
        # 0: Data (2027-02-01)
        # 1: Giorno (Lun, **Ven**, ...)
        # 2: Occ (16.7% ...)
        # 3: Med Cal (152 €)
        # 4: Med Airbnb (170 €)
        # 5: Tua Tariffa Attuale Cal (120 €)
        # 6: Tua Tariffa Attuale Airbnb (179 €)
        # 7: Tariffa Raccomandata Cal (**110 €**)
        # 8: Netto Stimato Host (89 €)
        # 9: Azione
        d = parts[0]
        giorno = parts[1]
        occ = parts[2]
        med_cal = parts[3]
        med_site = parts[4]
        user_curr_cal_str = parts[5]
        user_site_str = parts[6]
        orig_target_cal_str = parts[7].replace('*', '').replace('€', '').strip()
        orig_target_cal = float(orig_target_cal_str)
        
        # Apply 5% discount
        new_target_cal = round(orig_target_cal * 0.95)
        new_target_net = round(new_target_cal * 0.81089)
        
        # User current cal
        if '€' in user_curr_cal_str:
            user_cal = float(user_curr_cal_str.replace('€', '').strip())
            diff = new_target_cal - user_cal
            if abs(diff) <= 3:
                action = "✅ Allineato"
            elif diff > 3:
                action = f"🔺 Aumenta (+{int(diff)} €)"
            else:
                action = f"🔻 Riduci ({int(diff)} €)"
        else:
            action = f"🎯 Imposta {new_target_cal} €"
            
        feb_rows.append({
            'date': d,
            'giorno': giorno,
            'occ': occ,
            'med_cal': med_cal,
            'med_site': med_site,
            'user_cal_str': user_curr_cal_str,
            'user_site_str': user_site_str,
            'orig_cal': int(orig_target_cal),
            'new_cal': int(new_target_cal),
            'new_net': int(new_target_net),
            'action': action,
            'is_weekend': '**' in giorno
        })

print(f"Parsed {len(feb_rows)} February rows.")
for r in feb_rows[:5]:
    print(f"{r['date']} ({r['giorno']}): Orig {r['orig_cal']} € -> New -5% {r['new_cal']} € (Netto {r['new_net']} €) | {r['action']}")
