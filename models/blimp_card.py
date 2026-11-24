import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle, Polygon
d = json.load(open("out/blimp.json")); b = d["best"]; H, O, X = b["NASA|helium, base"], b["NASA|helium, optimistic"], b["NASA|hydrogen, optimistic"]
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#aab5ba", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG); f.text(.06, .95, "Blimp Turbine", fontsize=27, weight="bold", color=INK); f.text(.06, .915, rf"Works, but costs \${O['usd']:.0f}/MWh with helium. Tower: \$76.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .49, .92, .40]); a.set_xlim(0, 100); a.set_ylim(0, 60); a.axis("off"); a.add_patch(Rectangle((0, 0), 100, 7, color="#cfe3e8")); a.add_patch(Rectangle((8, 7), 9, 3, color=INK)); a.plot([12.5, 66], [10, 37], color=INK, lw=1.3); a.add_patch(Ellipse((70, 47), 42, 15, color=GR)); a.add_patch(Polygon([(50, 47), (43, 54), (47, 47), (43, 40)], color=MUTE)); a.plot([70, 70], [39.5, 35], color=INK, lw=2); a.add_patch(Circle((70, 34), 1, color=INK))
for t in (90, 210, 330): a.plot([70, 70 + 10 * np.cos(np.radians(t))], [34, 34 + 10 * np.sin(np.radians(t))], color=ACC, lw=4, solid_capstyle="round")
a.text(70, 46, "gas leaks every day", ha="center", fontsize=12, color=INK); a.text(20, 3, "anchor and winch on your pad", fontsize=12, color=INK); a.text(32, 18, "power tether", fontsize=11, color=MUTE, rotation=24)
c = f.add_axes([.42, .14, .48, .27]); N = ["14 m tower Dandelion", "Blimp, hydrogen", "Blimp, cheap helium", "Blimp, normal helium"]; V = [76, round(X["usd"]), round(O["usd"]), round(H["usd"])]; c.barh(N[::-1], V[::-1], color=[ACC, ACC, ACC, INK], height=.56); c.set_facecolor(BG); c.set_xlim(0, 3500); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 50, i, rf"\${v:,}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .43, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK); f.text(.06, .075, "Height helps. Paying to float it costs more.", fontsize=14, weight="bold", color=INK); f.text(.06, .04, "Simulation only. Hydrogen is a serious fire risk.", fontsize=12, color=MUTE); f.savefig("blimp_summary.png", dpi=150, facecolor=BG)
