"""Double-multiple-streamtube model of lift sails riding a closed horizontal loop of any convex shape (circle = classic H-Darrieus, used to validate).
Each streamtube crosses the loop twice; the downwind pass sees the wake of the upwind pass. Sails trim to a chosen lift coefficient on each tack."""
import math
import numpy as np

def polygon(kind, size, m=720, depth=1.5):
    if kind == "circle":
        a = np.linspace(0, 2 * np.pi, m, endpoint=False); p = size / 2 * np.column_stack([np.cos(a), np.sin(a)])
    else:
        k = {"triangle": 3, "square": 4, "hexagon": 6}.get(kind)
        if kind == "line": c = np.array([[-size / 2, -depth / 2], [size / 2, -depth / 2], [size / 2, depth / 2], [-size / 2, depth / 2]])
        else:
            a = np.arange(k) * 2 * np.pi / k + np.pi / 2; c = size / (2 * math.sin(math.pi / k)) * np.column_stack([np.cos(a), np.sin(a)])
        q = np.vstack([c, c[0]]); L = np.linalg.norm(np.diff(q, axis=0), axis=1); s = np.linspace(0, L.sum(), m, endpoint=False); e = np.r_[0, np.cumsum(L)]
        p = np.column_stack([np.interp(s, e, q[:, 0]), np.interp(s, e, q[:, 1])])
    d = np.roll(p, -1, 0) - np.roll(p, 1, 0); t = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9); ds = np.linalg.norm(np.roll(p, -1, 0) - p, axis=1)
    return p, t, ds, float(ds.sum())

def cp_dir(geo, sigma, lam, theta, CL=1.0, cd0=.08, k=.06, ny=48):
    """returns Cp and Ct on the projected frontal area. sigma = total sail chord / perimeter; lam = sail speed / wind speed"""
    p, t, ds, per = geo; w = np.array([math.cos(theta), math.sin(theta)]); perp = np.array([-w[1], w[0]]); y = p @ perp; x = p @ w
    lo, hi = y.min(), y.max(); width = hi - lo
    if width < 1e-6: return 0.0, 0.0
    b = np.clip(((y - lo) / width * ny).astype(int), 0, ny - 1); dy = width / ny; Pw = T = 0.0; CD = cd0 + k * CL * CL
    for j in range(ny):
        idx = np.where(b == j)[0]
        if len(idx) < 2: continue
        xm = np.average(x[idx], weights=ds[idx]); Vin = 1.0
        for side in (x[idx] < xm, x[idx] >= xm):
            e = idx[side]
            if len(e) == 0: continue
            def loads(a):
                V = Vin * (1 - a) * w; rel = V[None] - lam * t[e]; W = np.linalg.norm(rel, axis=1); u = rel / np.maximum(W[:, None], 1e-9); nrm = np.column_stack([-u[:, 1], u[:, 0]]); sg = np.sign(np.sum(nrm * t[e], axis=1)); l = nrm * sg[:, None]
                f = .5 * W[:, None]**2 * (CL * l + CD * u); ft = np.sum(f * t[e], axis=1); use = ft > 0       # sail feathers when it cannot pull
                f2 = np.where(use[:, None], f, .5 * W[:, None]**2 * .03 * u); return f2, V
            a = .1
            for _ in range(25):
                f, _V = loads(a); Fx = float(np.sum((f @ w) * ds[e]) * sigma); ct = max(Fx / (.5 * Vin * Vin * dy), 0); an = .5 * (1 - math.sqrt(max(1 - ct, 0))) if ct < .96 else .4 + (ct - .96) / 3.2; a = .6 * a + .4 * min(an, .75)
            f, _V = loads(a); Pw += float(np.sum(np.sum(f * t[e], axis=1) * lam * ds[e]) * sigma); T += float(np.sum((f @ w) * ds[e]) * sigma); Vin = max(Vin * (1 - 2 * a), .05)
    ref = .5 * width; return Pw / ref, T / ref

if __name__ == "__main__":
    print("VALIDATION circle, clean airfoil (published straight-blade VAWT peak Cp about .35-.45 at TSR 3-5):")
    g = polygon("circle", 10.0, 360)
    for sig in (.05, .1, .2):
        print(f" solidity {sig}:", max((round(cp_dir(g, sig, l, .3, CL=c, cd0=.015, k=.04)[0], 3), l, c) for l in (2, 3, 4, 5, 6) for c in (.4, .6, .8, 1.0)))
    print("sail polar (CD0 .08):")
    for kind in ("circle", "triangle", "square", "line"):
        g = polygon(kind, 20.0, 360); r = []
        for th in np.radians((0, 30, 60, 90)):
            r.append(max((round(cp_dir(g, .15, l, th, CL=c)[0], 3), l, c) for l in (1, 1.5, 2, 2.5, 3, 4) for c in (.5, .7, 1.0)))
        print(f" {kind:9s}", r)
