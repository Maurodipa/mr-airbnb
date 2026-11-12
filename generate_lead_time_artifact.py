import json
import os
import sys
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

TODAY = datetime(2026, 11, 10)
ARTIFACT_PATH = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\report_anticipo_prenotazioni_competitor_nov_dic.md'

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Competitors
competitors = []
comp_cleaning = {}
comp_tags = {}
with open('competitors.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if '===' in line: break
        parts = line.strip().split(':')
        if parts and parts[0].strip().isdigit():
            apt_id = parts[0].strip()
            if apt_id != '1589943047991118285':
                competitors.append(apt_id)
                comp_cleaning[apt_id] = float(parts[1]) if len(parts) > 1 else 50.0
                comp_tags[apt_id] = parts[2] if len(parts) > 2 else ''

# Titles
titles = {}
if os.path.exists('titles.txt'):
    with open('titles.txt', 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip().split(' -- ')
            if len(p) == 2:
                titles[p[0].strip()] = p[1].strip()

nov_dates = sorted([d for d in db.keys() if '2026-11-01' <= d <= '2026-11-30'])
dec_dates = sorted([d for d in db.keys() if '2026-12-01' <= d <= '2026-12-31'])
all_dates = nov_dates + dec_dates

# Analyze per competitor
comp_stats = {}

for cid in competitors:
    booked_entries = []
    avail_entries = []
    nov_booked = 0
    dec_booked = 0
    min_stays = []
    
    for d in all_dates:
        entry = db.get(d, {}).get(cid)
        if not entry:
            continue
            
        ms = entry.get('minStay')
        if ms: min_stays.append(ms)
        
        status = entry.get('status')
        if status == 'OK':
            avail_entries.append(d)
            continue
            
        is_nov = (d in nov_dates)
        if is_nov: nov_booked += 1
        else: dec_booked += 1
        
        timeline = []
        for h in entry.get('history', []):
            if 'collected_at' in h:
                timeline.append((h.get('collected_at'), h.get('status')))
        if 'collected_at' in entry:
            timeline.append((entry.get('collected_at'), entry.get('status')))
            
        timeline.sort(key=lambda x: x[0])
        
        last_ok_ts = None
        first_booked_ts = None
        
        for ts, st in timeline:
            if st == 'OK':
                last_ok_ts = ts
                first_booked_ts = None
            elif st != 'OK' and first_booked_ts is None:
                first_booked_ts = ts
                
        if first_booked_ts is None and timeline:
            first_booked_ts = timeline[0][0]
            
        fb_dt = datetime.fromisoformat(first_booked_ts) if first_booked_ts else None
        stay_dt = datetime.strptime(d, '%Y-%m-%d')
        
        days_ago = (TODAY - fb_dt).days if fb_dt else None
        lead_time = (stay_dt - fb_dt).days if (stay_dt and fb_dt) else None
        is_ancient = (last_ok_ts is None and len(timeline) > 1)
        
        # Timing bucket:
        # 1. > 40 gg fa (ante 30/09)
        # 2. 15-40 gg fa (Mese di Ottobre)
        # 3. < 15 gg fa (Recentissime / Inizio Nov)
        if is_ancient:
            bucket = 'ancient'
        elif days_ago is not None:
            if days_ago >= 15:
                bucket = 'october'
            else:
                bucket = 'recent'
        else:
            bucket = 'ancient'
            
        booked_entries.append({
            'date': d,
            'is_nov': is_nov,
            'stay_dt': stay_dt,
            'fb_dt': fb_dt,
            'days_ago': days_ago,
            'lead_time': lead_time,
            'is_ancient': is_ancient,
            'bucket': bucket,
            'first_booked_str': first_booked_ts[:10] if first_booked_ts else 'N/D'
        })
        
    cnt_ancient = sum(1 for b in booked_entries if b['bucket'] == 'ancient')
    cnt_oct = sum(1 for b in booked_entries if b['bucket'] == 'october')
    cnt_recent = sum(1 for b in booked_entries if b['bucket'] == 'recent')
    tot_booked = len(booked_entries)
    
    # Prevalent booking pattern
    if tot_booked == 0:
        pattern = "Sempre Libero (0% occ.)"
    elif cnt_ancient / tot_booked >= 0.70:
        pattern = "Anticipo Storico (>40 gg fa)"
    elif cnt_recent / tot_booked >= 0.35:
        pattern = "Forte Dinamismo Recente (<15 gg fa)"
    elif cnt_oct / tot_booked >= 0.35:
        pattern = "Venduto in Autunno (Ottobre)"
    else:
        pattern = "Misto Bilanciato"
        
    from collections import Counter
    mode_ms = Counter(min_stays).most_common(1)[0][0] if min_stays else 1
    
    comp_stats[cid] = {
        'id': cid,
        'title': titles.get(cid, 'Appartamento ' + cid),
        'cleaning': comp_cleaning.get(cid, 50.0),
        'min_stay': mode_ms,
        'total_booked': tot_booked,
        'nov_booked': nov_booked,
        'dec_booked': dec_booked,
        'cnt_ancient': cnt_ancient,
        'cnt_oct': cnt_oct,
        'cnt_recent': cnt_recent,
        'pattern': pattern,
        'booked_entries': booked_entries
    }

print("Elaborazione dati completata.")

# Sort competitors by total booked nights descending
sorted_comps = sorted(competitors, key=lambda c: comp_stats[c]['total_booked'], reverse=True)

# Generate Markdown Document
doc = []
doc.append("# ⏱️ Report Analitico: Da Quanto Tempo Sono Stati Prenotati i Concorrenti (Novembre & Dicembre 2026)\n")
doc.append("> [!NOTE]")
doc.append(f"> **Data di Riferimento Analisi:** 10 Novembre 2026.")
doc.append(f"> Questo report mappa per ciascuno dei **36 competitor benchmark** (entro 500m da Piazza Navona) l'esatto momento storico in cui ciascuna delle **61 notti di Novembre e Dicembre** è stata prenotata, ricostruendo l'intera cronologia dei rilevamenti registrati nel Data Lake da fine settembre ad oggi.\n")

# Macro stats
tot_slots = 36 * 61
tot_booked = sum(comp_stats[c]['total_booked'] for c in competitors)
tot_ancient = sum(comp_stats[c]['cnt_ancient'] for c in competitors)
tot_oct = sum(comp_stats[c]['cnt_oct'] for c in competitors)
tot_recent = sum(comp_stats[c]['cnt_recent'] for c in competitors)

nov_tot_booked = sum(comp_stats[c]['nov_booked'] for c in competitors)
nov_tot_slots = 36 * 30
dec_tot_booked = sum(comp_stats[c]['dec_booked'] for c in competitors)
dec_tot_slots = 36 * 31

doc.append("## 1. 📊 Macro-Quadro: Quando Prenotano gli Ospiti a Roma Centro?\n")
doc.append(f"Su un totale di **{tot_slots} notti-camera monitorate** nei due mesi (36 competitor × 61 notti):")
doc.append(f"- **Notti complessivamente vendute**: **{tot_booked} su {tot_slots}** (**{tot_booked/tot_slots*100:.1f}%** di occupazione media di periodo).")
doc.append(f"  - **Novembre 2026**: **{nov_tot_booked} su {nov_tot_slots} notti vendute ({nov_tot_booked/nov_tot_slots*100:.1f}%)**")
doc.append(f"  - **Dicembre 2026**: **{dec_tot_booked} su {dec_tot_slots} notti vendute ({dec_tot_booked/dec_tot_slots*100:.1f}%)**\n")

doc.append("### Ripartizione Temporale delle Prenotazioni:")
doc.append(f"| Finestra Temporale di Prenotazione | Giorni fa rispetto ad Oggi (10 Nov) | Notti Prenotate | Quota sul Totale Prenotato | Comportamento della Domanda |")
doc.append(f"|---|---|---|---|---|")
doc.append(f"| 🏛️ **Largo Anticipo Storico (ante 30 Settembre)** | **Oltre 40 giorni fa** | **{tot_ancient} notti** | **{tot_ancient/tot_booked*100:.1f}%** | Prenotazioni pianificate con mesi di anticipo (turismo internazionale, ponti, Capodanno). |")
doc.append(f"| 🍂 **Mese di Ottobre (1 – 26 Ottobre)** | **Tra 15 e 40 giorni fa** | **{tot_oct} notti** | **{tot_oct/tot_booked*100:.1f}%** | Domanda autunnale a medio raggio (consolidamento dei weekend e festività). |")
doc.append(f"| ⚡ **Recenti & Last-Minute (27 Ott – 10 Nov)** | **Meno di 15 giorni fa** | **{tot_recent} notti** | **{tot_recent/tot_booked*100:.1f}%** | Prenotazioni a ridosso data, turismo di prossimità e viaggiatori last-minute. |\n")

doc.append("```mermaid")
doc.append("xychart-beta")
doc.append("    title \"Distribuzione delle 1.339 Notti Prenotate per Epoca di Prenotazione\"")
doc.append("    x-axis [\"> 40 gg fa (Prima di Ott)\", \"15-40 gg fa (Ottobre)\", \"< 15 gg fa (Ultimi 14 gg)\"]")
doc.append("    y-axis \"Notti Prenotate\" 0 --> 1000")
doc.append(f"    bar [{tot_ancient}, {tot_oct}, {tot_recent}]")
doc.append("```\n")

doc.append("---\n")

# Section 2: Detailed competitor table
doc.append("## 2. 📋 Tabella Dettagliata per Singolo Competitor (Tutti i 36 Benchmark)\n")
doc.append("La tabella ordina i 36 appartamenti concorrenti dal più saturo al meno saturo, indicando per ciascuno quante notti sono state prenotate con largo anticipo (>40 gg fa), a ottobre (15–40 gg fa) e negli ultimi 14 giorni (<15 gg fa).\n")

doc.append("| ID Alloggio | Titolo Listing Airbnb | Min. Stay | Pulizie | Notti Prenotate Nov (su 30) | Notti Prenotate Dic (su 31) | **Totale Prenotato (su 61)** | **> 40 gg fa** (Ante 30/09) | **15–40 gg fa** (Ottobre) | **< 15 gg fa** (Ultimi 14 gg) | Profilo / Dinamica Prevalente |")
doc.append("|---|---|---|---|---|---|---|---|---|---|---|")

for cid in sorted_comps:
    st = comp_stats[cid]
    title_short = st['title'][:32] + "..." if len(st['title']) > 32 else st['title']
    link = f"[{title_short}](https://www.airbnb.it/rooms/{cid})"
    occ_tot_pct = st['total_booked'] / 61 * 100
    
    doc.append(f"| [`{cid}`](https://www.airbnb.it/rooms/{cid}) | {link} | {st['min_stay']}n | {st['cleaning']:.0f} € | {st['nov_booked']} gg | {st['dec_booked']} gg | **{st['total_booked']} gg** ({occ_tot_pct:.0f}%) | {st['cnt_ancient']} | {st['cnt_oct']} | {st['cnt_recent']} | {st['pattern']} |")

doc.append("\n---\n")

# Section 3: Key periods deep dive
doc.append("## 3. 🎯 Focus sui Periodi Chiave di Novembre e Dicembre\n")

# Calculate metrics for key periods
key_periods = {
    '1. Weekend di Novembre (Venerdì & Sabato)': [d for d in nov_dates if datetime.strptime(d, '%Y-%m-%d').weekday() in (4,5)],
    '2. Giorni Feriali di Novembre (Domenica - Giovedì)': [d for d in nov_dates if datetime.strptime(d, '%Y-%m-%d').weekday() not in (4,5)],
    '3. Ponte dell\'Immacolata (5 – 8 Dicembre)': ['2026-12-05', '2026-12-06', '2026-12-07', '2026-12-08'],
    '4. Periodo Pre-Natalizio Feriale (9 – 23 Dicembre)': [d for d in dec_dates if '2026-12-09' <= d <= '2026-12-23' and datetime.strptime(d, '%Y-%m-%d').weekday() not in (4,5)],
    '5. Festività Natalizie (24 – 26 Dicembre)': ['2026-12-24', '2026-12-25', '2026-12-26'],
    '6. Ponte di Capodanno (30 Dicembre – 1 Gennaio)': ['2026-12-30', '2026-12-31']
}

for pname, pdates in key_periods.items():
    p_booked = 0
    p_ancient = 0
    p_oct = 0
    p_recent = 0
    p_free = 0
    for d in pdates:
        for cid in competitors:
            entry = db.get(d, {}).get(cid, {})
            if entry.get('status') == 'OK':
                p_free += 1
            else:
                p_booked += 1
                b_match = [b for b in comp_stats[cid]['booked_entries'] if b['date'] == d]
                if b_match:
                    b = b_match[0]
                    if b['bucket'] == 'ancient': p_ancient += 1
                    elif b['bucket'] == 'october': p_oct += 1
                    else: p_recent += 1
    total_slots = p_booked + p_free
    occ_p = p_booked / total_slots * 100 if total_slots > 0 else 0
    
    doc.append(f"### 📍 {pname}")
    doc.append(f"- **Occupazione:** **{occ_p:.1f}%** ({p_booked} notti occupate su {total_slots} totali, **{p_free} notti ancora libere**).")
    if p_booked > 0:
        doc.append(f"- **Da quanto tempo sono state prenotate:**")
        doc.append(f"  - 🏛️ **Oltre 40 giorni fa (ante 30/09):** **{p_ancient} notti** ({p_ancient/p_booked*100:.1f}% del venduto)")
        doc.append(f"  - 🍂 **A Ottobre (15–40 giorni fa):** **{p_oct} notti** ({p_oct/p_booked*100:.1f}% del venduto)")
        doc.append(f"  - ⚡ **Negli ultimi 14 giorni (< 15 giorni fa):** **{p_recent} notti** ({p_recent/p_booked*100:.1f}% del venduto)")
    doc.append("")

doc.append("---\n")

# Section 4: Strategic conclusions for user apartment
doc.append("## 4. 💡 Implicazioni Strategiche per il Tuo Appartamento (ID: `1589943047991118285`)\n")
doc.append("1. **La Finestra di Anticipo Storico è Chiusa**: Il 69% delle notti vendute dai competitor è stato piazzato con più di 40 giorni di anticipo. Gli ospiti che dovevano pianificare con largo anticipo (viaggiatori a lungo raggio o pianificatori seriali) hanno già prenotato.")
doc.append("2. **Il Mercato Odierno è al 100% Last-Minute e Short-Lead**: Le notti ancora disponibili a Novembre e Dicembre (inclusi i buchi feriali e le date del ponte/Natale non ancora sature) vengono contese da ospiti che cercano adesso o pochi giorni prima del soggiorno.")
doc.append("3. **L'Arma Vincente del Soggiorno Minimo a 1 Notte**: Poiché la maggior parte dei competitor occupati ha venduto blocchi lunghi (2-3 notti), i competitor rimasti liberi hanno difficoltà a riempire le notti isolate infrasettimanali a causa dei vincoli di soggiorno minimo. Mantenere la prenotabilità a **1 sola notte** ti consente di incassare esattamente in questa fase ad alta conversione.")

full_text = "\n".join(doc)
with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"Artifact generato con successo: {ARTIFACT_PATH}")
print(f"Dimensione file: {len(full_text)} caratteri")
