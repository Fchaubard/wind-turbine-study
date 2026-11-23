import json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
R = [r for r in json.load(open("out/kite_window.json")) if r["wind"] == "gusty"]; pick = lambda p, l, e: min((r for r in R if r["price"] == p and r["life"] == l and r["ex"] == e), key=lambda r: r["usd"]); a_, b_ = pick(50, 5000, .7), pick(150, 1500, 1.)
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#b9c4ca", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG); win = a_["usd"] < 76
f.text(.06, .95, "Kite Train", fontsize=27, weight="bold", color=INK); f.text(.06, .915, rf"Best case \${a_['usd']:.0f}/MWh. Realistic \${b_['usd']:.0f}. Dandelion \$76.", fontsize=14, color=MUTE)
a = f.add_axes([.04, .47, .92, .42]); a.set_xlim(0, 100); a.set_ylim(0, 58); a.axis("off"); a.add_patch(Rectangle((0, 0), 100, 7, color="#cfe3e8")); a.add_patch(Rectangle((8, 7), 7, 2, color=INK)); xs = np.linspace(11, 88, 9); ys = 9 + (xs - 11) * .58; a.plot([11, 88], [9, ys[-1]], color=INK, lw=1.3)
for x, y in zip(xs[2:], ys[2:]): a.add_patch(Polygon([(x - 5, y + 1), (x - 2, y + 4.5), (x + 3, y + 3.5), (x + 5, y - 1), (x + 1, y + 1.2)], color=ACC, ec="#a93518"))
a.text(20, 3, "winch and generator on the pad", fontsize=12, color=INK); a.text(4, 50, "many cheap kites, one line", fontsize=14, weight="bold", color=INK)
c = f.add_axes([.42, .14, .48, .25]); N = ["14 m Dandelion", "Kites, best case", "Kites, realistic"]; V = [76, round(a_["usd"]), round(b_["usd"])]; c.barh(N[::-1], V[::-1], color=[GR, ACC, INK], height=.56); c.set_facecolor(BG); c.set_xlim(0, max(V) * 1.28); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12.5, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + max(V) * .02, i, rf"\${v}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .41, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK); f.text(.06, .075, "Reeled in outside 3.5 to 6 m/s wind.", fontsize=13, weight="bold", color=INK); f.text(.06, .04, "Simulation only. Launch and landing not simulated.", fontsize=12, color=MUTE); f.savefig("kite_train_summary.png", dpi=150, facecolor=BG)
