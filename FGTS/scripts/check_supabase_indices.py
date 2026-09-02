import os
import requests

KEY = os.environ.get("SUPABASE_KEY") or "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2NjA2MjMyMCwiZXhwIjo0OTIxNzM1OTIwLCJyb2xlIjoic2VydmljZV9yb2xlIn0.F86oyvNk5BZEVkbY-OEnatXZGZZvyo1_nb641ztIyn0"
BASE = os.environ.get("SUPABASE_URL") or "https://supabase.bildee.com.br"
URL = f"{BASE}/rest/v1/indices_fgts?select=*&limit=10"
headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Accept": "application/json",
}
resp = requests.get(URL, headers=headers, timeout=20)
print("status:", resp.status_code)
if resp.status_code != 200:
    print("error:", resp.text)
else:
    data = resp.json()
    if data:
        # Print keys of the first row to discover column names
        print("columns:", ", ".join(list(data[0].keys())))
    for i, row in enumerate(data, 1):
        print(row)
