import sys, re
import pandas as pd

txt = open(sys.argv[1], encoding="utf-8", errors="ignore").read()

recs = []
for m in re.finditer(r'<\|(.*?)\|>', txt, re.S):
    r = m.group(1)
    def f(key, cast=str):
        mm = re.search(rf'"{key}" -> ([^,|]+)', r)
        if not mm:
            return None
        v = mm.group(1).strip().strip('"')
        try:
            return cast(v)
        except ValueError:
            return None
    oid = f("OutageID", int)
    t = f("OutAbstime", float)
    dur = f("DurationBAD", float) or 0.0
    volt = f("Voltage", float)
    otype = f("OutageType")
    buses = re.search(r'"BusNames" -> \{([^}]*)\}', r)
    bn = "{" + buses.group(1).replace('"', "") + "}" if buses else "{,}"
    if t is None:
        continue
    recs.append({"OutAbstime": int(t), "InAbstime": int(t + dur * 60),
                 "Voltage": volt, "OutageType": otype,
                 "OutageID": oid, "BusNames": bn})

df = pd.DataFrame(recs).sort_values("OutAbstime")
df.to_csv(sys.argv[2], index=False)
print(len(df), "eventos", df["OutageType"].value_counts().to_dict())