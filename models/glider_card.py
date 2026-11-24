import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle, Polygon
d = json.load(open("out/glider.json"))["best"]; B = json.load(open("out/blimp.json"))["best"]; g = d["NASA|balloon, cheap helium|25"]; n = d["NASA|no balloon, lands|25"]; bl = B["NASA|helium, optimistic"]
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#aab5ba", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG); f.text(.06, .95, "Glider Turbine", fontsize=27, weight="bold", color=INK); f.text(.06, .915, rf"Half the blimp's cost: \${g['usd']:.0f}/MWh. Tower: \$76.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .49, .92, .40]); a.set_xlim(0, 100); a.set_ylim(0, 60); a.axis("off"); a.add_patch(Rectangle((0, 0), 100, 7, color="#cfe3e8")); a.add_patch(Rectangle((8, 7), 9, 3, color=INK)); a.plot([12.5, 68], [10, 34], color=INK, lw=1.3); a.add_patch(Ellipse((72, 52), 22, 9, color=GR)); a.plot([72, 72], [47.5, 39], color=MUTE, lw=1); a.add_patch(Polygon([(38, 37), (72, 41), (98, 36), (72, 37.5)], color=INK)); a.add_patch(Circle((72, 31), 1, color=INK)); a.plot([72, 72], [37.5, 31], color=INK, lw=2)
for t in (90, 210, 330): a.plot([72, 72 + 8 * np.cos(np.radians(t))], [31, 31 + 8 * np.sin(np.radians(t))], color=ACC, lw=4, solid_capstyle="round")
a.text(72, 51, "small balloon", ha="center", fontsize=11, color=INK); a.text(45, 43, "controlled wing", fontsize=12, color=INK); a.text(20, 3, "winch and anchor on your pad", fontsize=12, color=INK)
c = f.add_axes([.42, .14, .48, .27]); N = ["14 m tower Dandelion", "Glider + small balloon", "Blimp only", "Glider, no balloon"]; V = [76, round(g["usd"]), round(bl["usd"]), round(n["usd"])]; c.barh(N[::-1], V[::-1], color=[GR, GR, ACC, INK], height=.56); c.set_facecolor(BG); c.set_xlim(0, 4100); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 55, i, rf"\${v:,}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .43, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK); f.text(.06, .075, "A tripod from a 4 m pad cannot hold it up.", fontsize=14, weight="bold", color=INK); f.text(.06, .04, "Simulation only, cheap helium assumed. Flight dynamics not modeled.", fontsize=11.5, color=MUTE); f.savefig("glider_summary.png", dpi=150, facecolor=BG)
