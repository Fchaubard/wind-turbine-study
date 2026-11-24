import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
B = json.load(open("out/final_bom.json")); F = B["design"]; INK, MUTE, ACC, BG = "#1b2a33", "#6b7a83", "#e4572e", "#f7f4ee"
f = plt.figure(figsize=(7.2, 11), facecolor=BG); f.text(.06, .955, "16 m Dandelion", fontsize=28, weight="bold", color=INK); f.text(.06, .927, "Final design for your ocean pad", fontsize=14, color=MUTE)
a = f.add_axes([.14, .55, .72, .365]); a.imshow(mpimg.imread("out/cad5/iso.png")); a.axis("off")
f.text(.06, .515, rf"\${F['usd']:.0f}/MWh", fontsize=26, weight="bold", color=ACC); f.text(.40, .522, rf"or \${F['usd_weak']:.0f} if the weaker wind data is right", fontsize=12.5, color=INK); f.text(.06, .485, f"{F['W']:.0f} W average, or {F['W_weak']:.0f} W on the weaker wind", fontsize=13, color=INK); y = .445
for n, c in B["items"]: f.text(.06, y, n, fontsize=13, color=INK); f.text(.94, y, rf"\${c:,.0f}", ha="right", fontsize=13, weight="bold", color=INK); y -= .033
f.add_artist(plt.Line2D([.06, .94], [y + .017, y + .017], color=INK, lw=1.2)); f.text(.06, y - .012, "Build cost", fontsize=15, weight="bold", color=INK); f.text(.94, y - .012, rf"\${B['total']:,.0f}", ha="right", fontsize=15, weight="bold", color=INK)
f.text(.06, .075, f"12 m tower, 4 in legs, 3 generators, {F['pad_t']:.0f} t pad", fontsize=12.5, color=INK); f.text(.06, .045, "Simulated, not physically tested. Prices are estimates.", fontsize=11.5, color=MUTE); f.savefig("final_design.png", dpi=150, facecolor=BG)
