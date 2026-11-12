from datetime import datetime, timedelta
from app.mcp_market_scanner import run_mcp_custom_dates

# Build exact date list
dates_list = ['2026-09-20', '2026-10-16', '2026-10-20']

start_d = datetime.strptime('2026-10-28', '%Y-%m-%d')
end_d = datetime.strptime('2027-01-31', '%Y-%m-%d')

curr = start_d
while curr <= end_d:
    d_str = curr.strftime('%Y-%m-%d')
    if d_str not in dates_list:
        dates_list.append(d_str)
    curr += timedelta(days=1)

print(f"Avvio scansione Fase 2 per {len(dates_list)} date libere specifiche...")
print(f"Prime date: {dates_list[:5]}")
print(f"Ultime date: {dates_list[-5:]}")

run_mcp_custom_dates(dates_list)
print("Scansione Fase 2 completata al 100%!")
