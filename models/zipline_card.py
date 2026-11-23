import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch
r = min(json.load(open("out/zipline_final.json")) + json.load(open("out/zipline_tall_check.json")), key=lambda x: x["usd"])
INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#b9c4ca", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG)
f.text(.06, .95, "Zipline Sail", fontsize=27, weight="bold", color=INK)
f.text(.06, .915, f"New machine, simulated: ${r['usd']:.0f}/MWh. Dandelion still wins.", fontsize=13.5, color=MUTE)
a = f.add_axes([.04, .47, .92, .42]); a.set_xlim(-8, 108); a.set_ylim(-5, 34); a.axis("off"); a.set_facecolor(BG)
a.fill_between([-8, 108], -5, 0, color="#cfe3e8")
for x in (0, 100):
    a.plot([x, x], [0, 25], color=INK, lw=5); a.plot([x, x + (-13 if x == 0 else 13)], [25, 0], color=MUTE, lw=1)
a.plot([0, 50, 100], [24, 22.8, 24], color=INK, lw=1.5); a.plot([0, 50, 100], [5, 3.8, 5], color=INK, lw=1.5)
for x in (34, 43, 52, 61):
    a.add_patch(Polygon([[x, 23.2], [x + 5, 23.2], [x + 6.5, 4.5], [x + 1, 4.5]], color=ACC, alpha=.92))
a.add_patch(FancyArrowPatch((70, 14), (90, 14), arrowstyle="-|>", mutation_scale=22, color=INK, lw=2))
a.add_patch(FancyArrowPatch((30, 14), (10, 14), arrowstyle="-|>", mutation_scale=22, color=INK, lw=2))
a.text(50, 29, "sails shuttle back and forth on cables", ha="center", fontsize=13, color=INK)
a.add_patch(plt.Rectangle((-4, 0), 8, 2.6, color=INK)); a.text(6, -3.2, "generator on the pad, driven by a rope loop", fontsize=11.5, color=INK)
b = f.add_axes([.31, .13, .6, .27]); N = ["Dandelion", "Sail Ladder", "Zipline Sail", "Giant Whisk"]; V = [100, 130, round(r["usd"]), 254]
b.barh(N[::-1], V[::-1], color=[GR, ACC, GR, INK], height=.58); b.set_facecolor(BG); b.set_xlim(0, 300); b.set_xticks([])
for s in b.spines.values(): s.set_visible(False)
b.tick_params(left=False, labelsize=13, colors=INK)
for i, v in enumerate(V[::-1]): b.text(v + 5, i, f"${v}", va="center", fontsize=13, weight="bold", color=INK)
f.text(.06, .415, "Lifetime cost per MWh, 20 years", fontsize=13, weight="bold", color=INK)
f.text(.06, .065, f"{r['n']} sails, {r['S']:.0f} m² · {r['L']} m span · {r['W']:.0f} W average · ${r['cap']:,.0f}", fontsize=12.5, color=INK)
f.text(.06, .035, "Simulation only. Goal of $10/MWh not reached.", fontsize=12, color=MUTE)
f.savefig("zipline_summary.png", dpi=150, facecolor=BG); print(r["n"], r["h"], r["c"], r["L"], round(r["usd"]), round(r["W"]), round(r["cap"]), round(r["usd13"]))
