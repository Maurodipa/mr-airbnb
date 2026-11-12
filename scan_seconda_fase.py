import os
import sys
from datetime import datetime, timedelta
from app.mcp_market_scanner import run_mcp_custom_dates

# Dates requested: dal 13 novembre 2026 al 31 gennaio 2027
dates_list = []
start_continuous = datetime.strptime('2026-11-13', '%Y-%m-%d')
end_continuous = datetime.strptime('2027-01-31', '%Y-%m-%d')

curr = start_continuous
while curr <= end_continuous:
    d_str = curr.strftime('%Y-%m-%d')
    if d_str not in dates_list:
        dates_list.append(d_str)
    curr += timedelta(days=1)

print(f"=== AVVIO SCANSIONE SECONDO PASSAGGIO (SERIE STORICA) ===")
print(f"Totale date da scansionare: {len(dates_list)}")
print(f"Prime date: {dates_list[:5]}")
print(f"Ultime date: {dates_list[-5:]}")

if __name__ == '__main__':
    run_mcp_custom_dates(dates_list)
    print("\n=== SCANSIONE SECONDA FASE COMPLETATA AL 100%! ===")
