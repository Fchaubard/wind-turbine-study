"""Download a public elevation grid for the Punta Mita area, paced under the service's per-minute limit, with a resumable cache."""
import json, os, time, urllib.request, urllib.parse
import numpy as np
lats = np.round(np.arange(20.70, 20.8601, .005), 3); lons = np.round(np.arange(-105.60, -105.2999, .005), 3); pts = [(a, o) for a in lats for o in lons]; C = "out/terrain_cache.json"
el = json.load(open(C)) if os.path.exists(C) else []
time.sleep(70)
for i in range(len(el), len(pts), 100):
    ch = pts[i:i + 100]; q = urllib.parse.urlencode({"latitude": ",".join(str(p[0]) for p in ch), "longitude": ",".join(str(p[1]) for p in ch)}); req = urllib.request.Request("https://api.open-meteo.com/v1/elevation?" + q, headers={"User-Agent": "terrain-study"})
    for t in range(3):
        try: el += json.load(urllib.request.urlopen(req, timeout=30))["elevation"]; break
        except Exception as e: print("wait", i, e, flush=True); time.sleep(65)
    else: json.dump(el, open(C, "w")); raise SystemExit("stopped at %d" % len(el))
    json.dump(el, open(C, "w")); time.sleep(13)
E = np.array(el).reshape(len(lats), len(lons)); json.dump(dict(lats=lats.tolist(), lons=lons.tolist(), elev=E.tolist(), source="Open-Meteo elevation API (Copernicus DEM GLO-90)"), open("out/terrain.json", "w"))
print(E.shape, "min", E.min(), "max", E.max(), "land share", round(float((E > 0).mean()), 2)); step = 4
for r in range(len(lats) - 1, -1, -step): print(f"{lats[r]:.2f} " + " ".join(f"{int(E[r, k]):4d}" if E[r, k] > 0 else "   ~" for k in range(0, len(lons), step)))
print("lon   " + " ".join(f"{abs(lons[k]) * 100 % 1000:4.0f}" for k in range(0, len(lons), step)))
