with open('app/mcp_market_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_try = """                            except Exception as e:
                                print(f"Errore MCP: {e}")"""

new_try = """                            except Exception as e:
                                print(f"Errore MCP: {e}")
                                consecutive_errors += 1
                                if consecutive_errors >= 5:
                                    print("[PAUSA SICUREZZA] 5 errori consecutivi rilevati! Raffreddamento IP per 120 secondi...")
                                    await asyncio.sleep(120)
                                    consecutive_errors = 0
                            else:
                                consecutive_errors = 0"""

if 'consecutive_errors = 0' not in content:
    content = content.replace('market_data = {}', 'market_data = {}\n    consecutive_errors = 0')
    content = content.replace(old_try, new_try)
    with open('app/mcp_market_scanner.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully patched mcp_market_scanner.py with IP cooldown protection!')
else:
    print('Already patched!')
