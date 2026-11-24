import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
S = json.load(open("out/cheaper.json"))["steps"]; best = S[4]; INK, MUTE, ACC, GR, BG = "#1b2a33", "#6b7a83", "#e4572e", "#aab5ba", "#f7f4ee"
f = plt.figure(figsize=(7.2, 9), facecolor=BG); f.text(.06, .95, "Cheaper Dandelion", fontsize=27, weight="bold", color=INK); f.text(.06, .915, rf"\${best['usd_NASA']:.0f}/MWh, \${best['build']:,.0f} to build, same structure.", fontsize=14, color=MUTE)
L = ["Verified 14 m", "Add pad concrete", "Shared open controller", "Used steel pipe", "Used sailcloth", "Washer motors (rejected)"]; V = [round(x["usd_NASA"]) for x in S]; c = f.add_axes([.43, .27, .47, .58]); col = [INK, GR, GR, GR, ACC, GR]; c.barh(L[::-1], V[::-1], color=col[::-1], height=.58); c.set_facecolor(BG); c.set_xlim(0, 110); c.set_xticks([])
for s in c.spines.values(): s.set_visible(False)
c.tick_params(left=False, labelsize=12.5, colors=INK)
for i, v in enumerate(V[::-1]): c.text(v + 1.5, i, rf"\${v}", va="center", fontsize=13.5, weight="bold", color=INK)
f.text(.06, .875, "Lifetime cost per MWh after each change", fontsize=13, weight="bold", color=INK); f.text(.06, .19, rf"If the weaker wind dataset is right: \${best['usd_ERA5']:.0f}/MWh", fontsize=14, weight="bold", color=INK); f.text(.06, .15, f"Average output: {best['W_NASA']:.0f} W, or {best['W_ERA5']:.0f} W on the weaker wind", fontsize=12.5, color=INK); f.text(.06, .045, "Budget estimates, simulation only.", fontsize=12, color=MUTE); f.savefig("cheaper_summary.png", dpi=150, facecolor=BG)
