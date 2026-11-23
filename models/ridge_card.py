import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
d = json.load(open("out/ridge2.json"))["best"]; r = json.load(open("out/ridge.json")); one, four = d["1"], d["4"]; fence = r["base"]["Crest Fence"]
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#b9c4ca", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG)
f.text(.06, .95, "Hilltop Dandelion", fontsize=27, weight="bold", color=INK)
f.text(.06, .915, rf"New leader: \${one['usd']:.0f}/MWh for one, \${four['usd']:.0f} for four.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .49, .92, .40]); a.set_xlim(0, 100); a.set_ylim(0, 60); a.axis("off")
x = np.linspace(0, 100, 300); y = 7 + 29 * np.exp(-((x - 58) / 17)**2); a.fill_between(x, 0, y, color="#a9b98f"); a.fill_between(x[x < 30], 0, 6, color="#cfe3e8")
for px in (46, 58, 70):
    py = 7 + 29 * np.exp(-((px - 58) / 17)**2); a.plot([px, px], [py, py + 10], color=INK, lw=3); a.add_patch(Circle((px, py + 10), .9, color=ACC))
    for t in (90, 210, 330): a.plot([px, px + 5.5 * np.cos(np.radians(t))], [py + 10, py + 10 + 5.5 * np.sin(np.radians(t))], color=ACC, lw=2.5)
for yy in (20, 27, 34): a.annotate("", xy=(25, yy + 7), xytext=(4, yy), arrowprops=dict(arrowstyle="-|>", color=MUTE, lw=1.8))
a.text(3, 45, "sea wind speeds up\nover the hill", fontsize=13, color=INK); a.text(58, 3, "real 126 m hill", ha="center", fontsize=12, color=INK)
c = f.add_axes([.42, .13, .48, .28]); N = ["4 on the hill", "1 on the hill", "Dandelion on beach", "Crest Fence"]; V = [round(four["usd"]), round(one["usd"]), 100, round(fence["usd"])]
c.barh(N[::-1], V[::-1], color=[GR, INK, ACC, ACC], height=.58); c.set_facecolor(BG); c.set_xlim(0, 145); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12.5, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 2, i, rf"\${v}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .425, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK)
f.text(.06, .075, rf"One machine could land anywhere from \${one['high']:.0f} to \${one['low']:.0f}.", fontsize=13, weight="bold", color=INK)
f.text(.06, .04, "Hill wind is estimated, not measured. Still far from $10.".replace("$", r"\$"), fontsize=12, color=MUTE)
f.savefig("ridge_summary.png", dpi=150, facecolor=BG)
