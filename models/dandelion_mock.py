"""To-scale concept picture of the Dandelion, drawn from the checked dimensions with a simple perspective camera and shading."""
import json, math
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon, Circle, FancyArrowPatch
F = json.load(open("out/dandelion_final.json")); HUB, R, OV = F["pick"]["hub"], F["pick"]["D"] / 2, F["overhang"]; NBR = F["nbr"]; AZ = HUB - .25; CONE = math.radians(8)
cam = np.array([25., -10., 2.6]); tgt = np.array([.4, .2, 8.0]); f_ = (tgt - cam) / np.linalg.norm(tgt - cam); r_ = np.cross(f_, [0, 0, 1.]); r_ /= np.linalg.norm(r_); u_ = np.cross(r_, f_); FOC = 4.05
def pj(P):
    P = np.atleast_2d(P) - cam; d = P @ f_; return np.column_stack([FOC * (P @ r_) / d, FOC * (P @ u_) / d]), d
LIGHT = np.array([.45, -.62, .64]); LIGHT /= np.linalg.norm(LIGHT)
def shade(c, n):
    k = .52 + .55 * abs(float(n @ LIGHT)); return tuple(np.clip(np.array(matplotlib.colors.to_rgb(c)) * k, 0, 1))
Q = []
def quad(P, c):
    P = np.array(P); n = np.cross(P[1] - P[0], P[2] - P[0]); L = np.linalg.norm(n)
    if L < 1e-9: return
    xy, d = pj(P); Q.append((float(d.mean()), xy, shade(c, n / L)))
def tube(a, b, od, c, k=10):
    a, b = np.array(a, float), np.array(b, float); x = (b - a) / np.linalg.norm(b - a); y = np.cross(x, [.3, .5, .8]); y /= np.linalg.norm(y); z = np.cross(x, y); t = np.linspace(0, 2 * np.pi, k + 1); ring = np.cos(t)[:, None] * y + np.sin(t)[:, None] * z
    m = max(1, int(np.linalg.norm(b - a) / .25))
    for q_ in range(m):
        a2, b2 = a + (b - a) * q_ / m, a + (b - a) * (q_ + 1) / m
        for i in range(k): quad([a2 + ring[i] * od / 2, b2 + ring[i] * od / 2, b2 + ring[i + 1] * od / 2, a2 + ring[i + 1] * od / 2], c)
def box(lo, hi, c):
    x0, y0, z0 = lo; x1, y1, z1 = hi
    for P in ([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)], [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)]): quad(P, c)
box((-2.3, -2.3, -.45), (2.3, 2.3, .22), "#c9c4b6")
feet = [np.array([2 * math.cos(a), 2 * math.sin(a), .22]) for a in np.radians((90, 210, 330))]; apex = np.array([0, 0, AZ])
for p in feet: box(p + [-.17, -.17, 0], p + [.17, .17, .025], "#3a3d42"); tube(p, apex, .11, "#7c828a")
for k in range(NBR):
    z = AZ * (k + 1) / (NBR + 1); pts = [p + (apex - p) * z / AZ for p in feet]
    for a, b in ((0, 1), (1, 2), (2, 0)): tube(pts[a], pts[b], .055, "#979da4", 6)
hb = np.array([OV, 0, HUB]); tube(apex, [0, 0, HUB], .15, "#d85a30"); tube([0, 0, HUB], hb, .13, "#2b2e33"); tube(hb + [-.48, 0, -.32], hb + [-.22, 0, -.32], .36, "#1d9e75", 18); tube(hb + [-.35, 0, 0], hb + [-.35, 0, -.32], .035, "#e06c2f", 6); tube(hb, hb + [.13, 0, 0], .66, "#3a3d42", 22); tube(hb + [.13, 0, 0], hb + [.32, 0, 0], .2, "#24272b", 14)
def foil(n=16, tc=.12):
    x = (1 - np.cos(np.linspace(0, math.pi, n))) / 2; yt = 5 * tc * (.2969 * np.sqrt(x) - .126 * x - .3516 * x**2 + .2843 * x**3 - .1036 * x**4); yc = .06 * np.sin(math.pi * x); return np.vstack([np.column_stack([x, yc + yt])[::-1], np.column_stack([x, yc - yt])[1:-1]])
F0 = foil(); tips = []
for i in range(3):
    a = math.radians(102) + 2 * math.pi * i / 3; dr = np.array([math.sin(CONE), math.cos(CONE) * math.cos(a), math.cos(CONE) * math.sin(a)]); tg = np.array([0, -math.sin(a), math.cos(a)]); ax_ = np.cross(dr, tg); o = hb + [.08, 0, 0]; sec = []
    for s in np.linspace(.48, R, 26):
        x = (s - .48) / (R - .48); c = (1.1 + (.25 - 1.1) * x) * R / 6; th = math.radians(18 - 20 * x); sec.append([o + dr * s + tg * c * ((u - .3) * math.cos(th) - v * math.sin(th)) + ax_ * c * ((u - .3) * math.sin(th) + v * math.cos(th)) for u, v in F0])
    sec = np.array(sec)
    for j in range(len(sec) - 1):
        col = "#f4efe2" if j % 5 else "#d9d1bd"
        for k in range(sec.shape[1]): quad([sec[j, k], sec[j + 1, k], sec[j + 1, (k + 1) % sec.shape[1]], sec[j, (k + 1) % sec.shape[1]]], col)
    tube(o + dr * .16, o + dr * .55, .13, "#d85a30", 12); tube(o, o + dr * .2, .09, "#3a3d42", 8); tips.append(o + dr * 3.1 + tg * .15)
Q.sort(key=lambda q: -q[0])
fig = plt.figure(figsize=(6.4, 9.6), dpi=190); ax = fig.add_axes([0, 0, 1, 1]); XL, YL = (-1.02, 1.02), (-1.42, 1.62); ax.set_xlim(XL); ax.set_ylim(YL); ax.axis("off")
hz = pj(cam + np.array([f_[0], f_[1], 0]) * 3000 + [0, 0, -cam[2]])[0][0, 1]
sky = np.linspace(0, 1, 400)[:, None]; c1, c2, c3 = np.array([.13, .36, .60]), np.array([.55, .78, .90]), np.array([.99, .86, .67]); G = np.where(sky < .55, c1 + (c2 - c1) * sky / .55, c2 + (c3 - c2) * (sky - .55) / .45)[:, None, :]
ax.imshow(G, extent=(XL[0], XL[1], hz, YL[1]), origin="upper", aspect="auto", zorder=0); W = np.linspace(0, 1, 300)[:, None]; S = np.array([.47, .72, .76]) + (np.array([.05, .31, .43]) - np.array([.47, .72, .76])) * W**.65; ax.imshow(S[:, None, :], extent=(XL[0], XL[1], YL[0], hz), origin="upper", aspect="auto", zorder=0)
ax.add_patch(Circle((-.62, hz + .17), .085, color="#fff3cf", alpha=.95, zorder=1)); ax.add_patch(Polygon([(-1.02, hz), (-1.02, hz + .10), (-.82, hz + .13), (-.62, hz + .06), (-.40, hz + .035), (-.2, hz)], color="#4f7180", alpha=.75, zorder=1))
rng = np.random.default_rng(4)
for _ in range(210):
    t = rng.random()**1.6; y = hz - .012 - t * (hz - YL[0]); x = rng.uniform(*XL); w = .018 + .12 * t; ax.plot([x - w, x + w], [y, y + .004 * rng.normal()], color="white", alpha=.13 + .3 * rng.random(), lw=.35 + 1.2 * t, solid_capstyle="round", zorder=1)
ax.add_collection(PolyCollection([q[1] for q in Q], facecolors=[q[2] for q in Q], edgecolors=[q[2] for q in Q], linewidths=.12, zorder=3))
base = pj([[-2.3, 2.3, -.45], [2.3, 2.3, -.45], [2.3, -2.3, -.45], [-2.3, -2.3, -.45]])[0]; ax.add_patch(Polygon(base + [0, -.016], closed=True, fill=False, ec="white", lw=1.6, alpha=.65, zorder=2))
pf = np.array([1.5, -1.5, .22]); h = 1.75; pa = pj([pf, pf + [0, 0, h * .84], pf + [0, 0, h * .93]])[0]; ax.plot(pa[:2, 0], pa[:2, 1], color="#202226", lw=3.6, solid_capstyle="round", zorder=5); ax.add_patch(Circle(pa[2], .014, color="#202226", zorder=5))
def note(P, tx, ty, title, sub=None, ha="left"):
    q = pj(P)[0][0]; ax.plot([q[0], tx], [q[1], ty], color="#17202a", lw=.75, zorder=7); ax.add_patch(Circle(q, .008, color="#17202a", zorder=7)); ax.text(tx + (.012 if ha == "left" else -.012), ty + .012, title, ha=ha, va="bottom", fontsize=11.2, weight="bold", color="#10151b", zorder=8)
    if sub: ax.text(tx + (.012 if ha == "left" else -.012), ty + .006, sub, ha=ha, va="top", fontsize=8.7, color="#17202a", zorder=8)
ax.text(-.94, 1.53, "The Dandelion", fontsize=26, weight="bold", color="white", va="center", zorder=9); ax.text(-.94, 1.43, "Concept mock, drawn to scale. 10 m rotor on your pad.", fontsize=10.5, color="white", va="center", zorder=9)
note(tips[0], .38, 1.20, "Fabric wing blades", "sleeve over a pine spar")
note(hb + [.08, -.28, .3], .46, .50, "Free hinges", "blades cone back in gusts")
note(hb + [-.35, -.18, -.32], -.50, .52, "Generator", "makes the electricity", ha="right")
m = feet[1] + (apex - feet[1]) * .42; note(m, -.52, -.42, "Steel tripod", "10 m to the hub", ha="right")
note(np.array([-.6, -2.3, .22]), -.56, -1.20, "Your pad", "4 × 4 m, about 9 t", ha="right"); q = pa[1]; ax.text(q[0] + .035, q[1] - .03, "person, 1.75 m", fontsize=8.2, color="#10151b", weight="bold", zorder=8)
ax.add_patch(FancyArrowPatch((-.92, 1.20), (-.60, 1.09), arrowstyle="-|>", mutation_scale=18, lw=2.4, color="white", zorder=8)); ax.text(-.93, 1.25, "WIND", fontsize=10, weight="bold", color="white", zorder=8)
ia = fig.add_axes([.67, .235, .30, .185]); ia.set_xlim(-1.4, 5.1); ia.set_ylim(-5.5, 5.6); ia.set_aspect("equal"); ia.axis("off"); ia.add_patch(plt.Rectangle((-1.4, -5.5), 6.5, 11.1, color="white", alpha=.92, zorder=0))
ia.text(-1.1, 4.75, "In a gust", fontsize=9, weight="bold", color="#10151b"); ia.plot([0, 0], [-5.2, .1], color="#7c828a", lw=2); ia.plot([0, .75], [0, 0], color="#2b2e33", lw=2.4)
for b, col, ls in ((8, "#c9bea5", "-"), (28, "#d85a30", "-")):
    for sgn in (-1, 1): ia.plot([.75, .75 + 3.8 * math.sin(math.radians(b))], [0, sgn * 3.8 * math.cos(math.radians(b))], color=col, lw=2.6, ls=ls, solid_capstyle="round")
ia.text(-1.1, -5.0, "calm", fontsize=7.5, color="#6c6556"); ia.text(2.65, -4.95, "gust", fontsize=7.5, color="#d85a30", weight="bold")
fig.savefig("out/dandelion_mock.png")
