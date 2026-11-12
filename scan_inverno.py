from app.mcp_market_scanner import run_mcp_scan_and_process

print("Avvio scan per il periodo invernale (14 Novembre - 31 Dicembre)...")
print("I ritardi addizionali random sono stati attivati per aggirare il blocco di Airbnb.")
run_mcp_scan_and_process("2026-11-14", "2026-12-31")
print("Scansione completata!")
