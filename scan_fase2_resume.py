from datetime import datetime, timedelta
from app.mcp_market_scanner import run_mcp_custom_dates

# Build remaining date list for Phase 2 resume (ripartenza da 2026-12-22)
dates_list = []

start_d = datetime.strptime('2026-12-22', '%Y-%m-%d')
end_d = datetime.strptime('2027-01-31', '%Y-%m-%d')

curr = start_d
while curr <= end_d:
    d_str = curr.strftime('%Y-%m-%d')
    if d_str not in dates_list:
        dates_list.append(d_str)
    curr += timedelta(days=1)

print(f"Ripresa scansione Fase 2 per {len(dates_list)} date rimaste...")
print(f"Prossime date: {dates_list[:5]}")
print(f"Ultime date: {dates_list[-5:]}")

run_mcp_custom_dates(dates_list)
print("Scansione Fase 2 completata AL 100%!")
