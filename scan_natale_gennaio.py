from app.mcp_market_scanner import run_mcp_scan_and_process

print("Avvio scan per il periodo 23 Novembre 2026 - 31 Gennaio 2027...")
print("Protezione automatica anti-blocco Cloudflare attiva (pausa di 120s su errori consecutivi).")
run_mcp_scan_and_process("2026-11-23", "2027-01-31")
print("Scansione invernale completata con successo!")
