from app.mcp_market_scanner import run_mcp_scan_and_process

print("Avvio scan per il 10 Settembre 2026...")
run_mcp_scan_and_process("2026-09-10", "2026-09-10")

print("\nAvvio scan per il 20 Settembre 2026...")
run_mcp_scan_and_process("2026-09-20", "2026-09-20")

print("\nFinito!")
