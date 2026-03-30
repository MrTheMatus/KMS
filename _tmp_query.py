import sqlite3, json
c = sqlite3.connect('kms/data/state.db')
rows = c.execute("select suggested_metadata_json from proposals").fetchall()
domains = {}
empty = 0
for r in rows:
    try:
        d = json.loads(r[0] or "{}").get("triage", {}).get("suggested_domain", "")
        if d: domains[d] = domains.get(d, 0) + 1
        else: empty += 1
    except: empty += 1
for k, v in sorted(domains.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"  empty: {empty}, total: {len(rows)}")
