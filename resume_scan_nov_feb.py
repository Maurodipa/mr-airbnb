import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.mcp_market_scanner import run_mcp_scan_and_process

print("Ripresa scansione incrementale dall'8 novembre 2026 al 28 febbraio 2027 (Resume=True)...", flush=True)
res = run_mcp_scan_and_process('2026-11-08', '2027-02-28', resume=True)
print("Scansione completata:", res, flush=True)
