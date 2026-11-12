import time
import sys

log_path = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\.system_generated\tasks\task-6686.log'

start_time = time.time()
while time.time() - start_time < 90:
    try:
        with open(log_path, encoding='utf-8') as f:
            content = f.read()
            if '2026-10-16' in content:
                print("DATA 2026-09-20 COMPLETATA!")
                sys.exit(0)
    except Exception as e:
        pass
    time.sleep(5)

print("Ancora in lavorazione su 2026-09-20...")
