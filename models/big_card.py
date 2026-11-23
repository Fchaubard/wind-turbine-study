import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
b = json.load(open("out/dandelion_big_14_10.json")); m = json.load(open("out/dandelion_big_12_12.json")); o = json.load(open("out/dandelion_final.json")); pw = min(json.load(open("out/pinwheel.json"))["true_pinwheel"], key=lambda r: r["usd"])
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#b9c4ca", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG)
f.text(.06, .95, "14 m Dandelion", fontsize=27, weight="bold", color=INK)
f.text(.06, .915, rf"New pad leader: \${b['usd']:.0f}/MWh, down from \${o['usd']:.0f}.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .47, .92, .42]); a.set_xlim(-11, 11); a.set_ylim(-1.5, 18.5); a.set_aspect("equal"); a.axis("off")
a.add_patch(Rectangle((-11, -1.5), 22, 2.2, color="#cfe3e8")); a.add_patch(Rectangle((-2, .7), 4, .6, color=INK))
for x in (-1.8, 0, 1.8): a.plot([x, 0], [1.3, 10], color=INK, lw=3)
a.add_patch(Circle((0, 10), 7, fill=False, ec=GR, lw=1.2, ls="--"))
for t in (90, 210, 330): a.plot([0, 7 * np.cos(np.radians(t))], [10, 10 + 7 * np.sin(np.radians(t))], color=ACC, lw=6, solid_capstyle="round")
a.add_patch(Circle((0, 10), .45, color=INK)); a.text(0, -.75, "same 4 × 4 m pad, heavier concrete", ha="center", fontsize=12, color=INK)
c = f.add_axes([.42, .13, .48, .27]); N = ["14 m Dandelion", "12 m Dandelion", "Giant pinwheel", "10 m Dandelion"]; V = [round(b["usd"]), round(m["usd"]), round(pw["usd"]), round(o["usd"])]
c.barh(N[::-1], V[::-1], color=[INK, GR, ACC, ACC], height=.58); c.set_facecolor(BG); c.set_xlim(0, 135); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12.5, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 2, i, rf"\${v}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .415, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK)
f.text(.06, .075, rf"{b['W']:.0f} W average · \${b['capex']:,.0f} · needs a {b['pick']['pad_t']:.0f} t pad", fontsize=13, weight="bold", color=INK)
f.text(.06, .04, r"Simulation only. Extra concrete not priced. Still far from \$10.", fontsize=12, color=MUTE)
f.savefig("big_summary.png", dpi=150, facecolor=BG)
