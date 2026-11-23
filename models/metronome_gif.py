"""Looping animation of the Metronome Wing at Neon's proposed size (22 m arm, swinging +/-68 degrees). Wing pitch is exaggerated so the flip is visible."""
import math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
INK, MUTE, ACC, BG, SEA, SWEEP = "#1b2a33", "#6b7a83", "#e4572e", "#f7f4ee", "#bcdce4", "#f6d9cd"
R, r1, TH, ZP = 22., 4., 1.19, 2.; AZ, EL = math.radians(28), math.radians(14)
def pj(x, y, z):
    u = x * math.cos(AZ) + y * math.sin(AZ); d = -x * math.sin(AZ) + y * math.cos(AZ); return u, z * math.cos(EL) + d * math.sin(EL)
def arm(r, t, off=0.): return np.array([r * math.sin(t), off, ZP + r * math.cos(t)])
N = 56; frames = []; fig = plt.figure(figsize=(5.4, 4.5), dpi=100, facecolor=BG); seed = np.linspace(0, 1, 7, endpoint=False)
for k in range(N):
    ph = 2 * math.pi * k / N; t = TH * math.sin(ph); w = math.cos(ph); pitch = math.radians(24) * math.tanh(w / .22); fig.clf(); a = fig.add_axes([0, 0, 1, 1]); a.set_xlim(-29, 29); a.set_ylim(-8, 40.3); a.set_aspect("equal"); a.axis("off"); a.set_facecolor(BG)
    a.add_patch(Polygon([(-29, -9), (29, -9), (29, 3), (-29, 3)], color=SEA))
    for yy, off in ((-.5, 0), (1.2, 1.4)): a.plot(np.linspace(-29, 29, 90), yy + .22 * np.sin(np.linspace(0, 16, 90) + ph + off), color="white", lw=1.4, alpha=.8)
    ang = np.linspace(-TH, TH, 50); out = [pj(*arm(R, q)) for q in ang]; inn = [pj(*arm(r1, q)) for q in ang[::-1]]; a.add_patch(Polygon(out + inn, color=SWEEP, alpha=.75, lw=0)); a.plot(*zip(*out), color=ACC, lw=1, ls=(0, (4, 3)), alpha=.75)
    for s in seed:                                                      # wind streaks travelling through the swept area
        f = (s + k / N) % 1; yw = -15 + 30 * f
        for x0, z0 in ((-13, 15), (0, 25), (13, 15), (-6, 8), (7, 9)):
            p, q = pj(x0, yw, z0), pj(x0, yw + 5.5, z0); a.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", shrinkA=0, shrinkB=0, mutation_scale=9, color=MUTE, lw=1.2, alpha=.32 + .35 * math.sin(math.pi * f)))
    pad = [pj(-2, -2, 1.4), pj(2, -2, 1.4), pj(2, 2, 1.4), pj(-2, 2, 1.4)]; a.add_patch(Polygon(pad, color="#8d979c", ec=INK, lw=1)); box = [pj(-1.1, -.8, 1.4), pj(1.1, -.8, 1.4), pj(1.1, -.8, 3.1), pj(-1.1, -.8, 3.1)]; a.add_patch(Polygon(box, color=INK))
    for b in (-3, 3):
        s0, s1 = pj(0, b, ZP), pj(*arm(.68 * R, t)); a.plot([s0[0], s1[0]], [s0[1], s1[1]], color=MUTE, lw=.8); s2 = pj(*arm(.95 * R, t)); a.plot([s0[0], s2[0]], [s0[1], s2[1]], color=MUTE, lw=.6)
    p0, p1 = pj(0, 0, ZP), pj(*arm(R, t)); a.plot([p0[0], p1[0]], [p0[1], p1[1]], color=INK, lw=3.2, solid_capstyle="round"); a.plot(*p0, "o", color=INK, ms=8)
    tx, ty = math.cos(t), -math.sin(t); poly = []
    for r, c in ((r1, 3.4), (R, 1.5)): poly.append((r, c))
    def edge(r, c, sg):
        m = arm(r, t); h = .5 * c * sg; return pj(m[0] + tx * h * math.cos(pitch), h * math.sin(pitch) * 2.0, m[2] + ty * h * math.cos(pitch))
    a.add_patch(Polygon([edge(r1, 3.4, 1), edge(R, 1.5, 1), edge(R, 1.5, -1), edge(r1, 3.4, -1)], color=ACC, ec="#a93518", lw=1, zorder=6))
    a.text(-27, 36, "Metronome Wing", fontsize=20, weight="bold", color=INK); a.text(-27, 32.8, "one wing swings across the wind", fontsize=11.5, color=MUTE); a.text(0, -6.2, "generator on your 4 × 4 m pad", ha="center", fontsize=11.5, color=INK)
    fig.canvas.draw(); im = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB"); frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=64))
    if k == 9: im.save("out/metronome_frame.png")
frames[0].save("metronome.gif", save_all=True, append_images=frames[1:], duration=85, loop=0, optimize=True); print("frames", len(frames))
