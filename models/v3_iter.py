import json, os, subprocess, math
PY="../.venv/bin/python"; E=json.load(open("out/v3_design.json"))["e"]; PR={"2-1/2 in Sch 40":520,"3 in Sch 40":680,"4 in Sch 40":960}; res=[]
for hub in (8.5,10.0,12.0):
    for leg in PR:
        for nbr in (2,3,4):
            az=hub-.25; over=round(2*(az-(hub-5))/az+.45,2)
            o=subprocess.run([PY,"v3_verify.py"],env=dict(os.environ,V3_HUB=str(hub),V3_LEG=leg,V3_NBR=str(nbr),V3_OV=str(over)),capture_output=True,text=True).stdout
            r=json.loads([l for l in o.splitlines() if l.startswith("JSON")][0][4:]); s=r["sf"]; steel=3*math.hypot(az,2)*PR[leg]/18.5+nbr*3*2.2*75/18.5
            ok=s["12 m/s, furl fails"]>=2 and s["17 m/s, furl fails"]>=1.25 and s["45 m/s, parked"]>=1.0 and not r["hit"] and r["f"]>=1.5
            r.update(over=over,steel=steel,ok=ok,score=(steel+4300)/E[str(hub)]["2000"]); res.append(r)
            print(f"{hub:4.1f} {leg:16s} br{nbr} f {r['f']:.2f} Hz SF12 {s['12 m/s, furl fails']:.2f} SF17 {s['17 m/s, furl fails']:.2f} SF45 {s['45 m/s, parked']:.2f} pull {r['pull']:.0f} tail {r['tail']:.2f}Hz @{r['where']['17 m/s, furl fails']} pad {r['pad']:.1f}t ${steel:.0f} {'PASS' if ok else ''}",flush=True)
json.dump(res,open("out/v3_iter.json","w"),indent=1); p=[r for r in res if r["ok"]]; print("BEST",min(p,key=lambda r:r["score"]) if p else None)
