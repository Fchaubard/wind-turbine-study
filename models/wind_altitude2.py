"""Wind by altitude off Punta Mita. Long-term 10 m and 100 m from ERA5 (2023-2025); higher levels from the last 92 days of a public weather model, which is only a seasonal sample."""
import json, urllib.request, urllib.parse
import numpy as np
def get(base, **p):
    q = urllib.parse.urlencode(dict(latitude=20.75, longitude=-105.60, wind_speed_unit="ms", timezone="GMT", **p)); return json.load(urllib.request.urlopen(urllib.request.Request(base + "?" + q, headers={"User-Agent": "wind-study"}), timeout=60))["hourly"]
out = {}
try:
    h = get("https://archive-api.open-meteo.com/v1/archive", hourly="wind_speed_10m,wind_speed_100m", start_date="2023-01-01", end_date="2025-12-31"); out["era5"] = h
    for k in ("wind_speed_10m", "wind_speed_100m"):
        v = np.array(h[k], float); v = v[np.isfinite(v)]; print("ERA5 3 yr", k, "mean", round(v.mean(), 2), "W/m2", round(.5 * 1.18 * np.mean(v**3), 1), "hours", len(v))
except Exception as e: print("ERA5 failed", type(e).__name__, e)
LV = [1000, 975, 950, 925, 900, 850]
try:
    h = get("https://api.open-meteo.com/v1/forecast", hourly=",".join(["wind_speed_10m", "wind_speed_80m", "wind_speed_120m"] + [f"wind_speed_{p}hPa" for p in LV] + [f"geopotential_height_{p}hPa" for p in LV]), past_days=92, forecast_days=1); out["recent"] = h
    for k in ("wind_speed_10m", "wind_speed_80m", "wind_speed_120m"):
        v = np.array(h[k], float); v = v[np.isfinite(v)]; print("recent 92 d", k, "mean", round(v.mean(), 2), "W/m2", round(.5 * 1.18 * np.mean(v**3), 1))
    for p in LV:
        v, z = np.array(h[f"wind_speed_{p}hPa"], float), np.array(h[f"geopotential_height_{p}hPa"], float); ok = np.isfinite(v) & np.isfinite(z); print("recent", p, "hPa", round(z[ok].mean()), "m mean", round(v[ok].mean(), 2), "W/m2", round(.5 * 1.18 * p / 1000 * np.mean(v[ok]**3), 1), "hours", int(ok.sum()))
except Exception as e: print("recent failed", type(e).__name__, e)
json.dump(out, open("out/wind_altitude.json", "w"))
