import re
import sys
from datetime import datetime

log_path = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\.system_generated\tasks\task-6525.log'
with open(log_path, encoding='utf-8') as f:
    content = f.read()

pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\] \[INFO\] Tool call received:[^{]*?\{[^}]*?\"checkin\":\s*\"(\d{4}-\d{2}-\d{2})\"'
matches = re.findall(pattern, content)

day_starts = {}
for timestamp_str, checkin_date in matches:
    if checkin_date not in day_starts:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        day_starts[checkin_date] = dt

days = sorted(list(day_starts.keys()))
for i in range(len(days)-1):
    d1 = days[i]
    d2 = days[i+1]
    dur = (day_starts[d2] - day_starts[d1]).total_seconds() / 60.0
    print(f"Giorno {d1}: {dur:.1f} minuti")
