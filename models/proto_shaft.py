"""Punta Mita prototype, step 3: rope-shaft (TRPT) sizing and nonlinear FEA, lines, anchor, lifter, generator match.
Chosen rotor: 6 foam blades 1.2 m x 0.20 m on a 2.4 m ring (4.8 m rotor), shaft elevation 30 deg."""
import json, math, sys
import numpy as np
import rotary as RT
import proto as PR

ROT = PR.evaluate(6, 1.2, 1.2, 0.20)
K = PR.K_MID
R_SHAFT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
L_AX = float(sys.argv[2]) if len(sys.argv) > 2 else 2.8
N_SEG = int(sys.argv[3]) if len(sys.argv) > 3 else 5
RING_D, RING_ID = 0.010, 0.0073          # DragonPlate pultruded carbon tube .394" x .288"
LINE_D = 2.0                             # mm, 1000 lb UHMWPE
LIFT = 120.0                             # N, steady lifter-kite line pull added to the shaft tension
out = dict(rotor=ROT, K=K, shaft=dict(r=R_SHAFT, l_ax=L_AX, n_seg=N_SEG, length=L_AX * N_SEG, hub_height=L_AX * N_SEG * math.sin(PR.BETA)), cases=[])
print(f"rotor: dia {2*ROT['R_out']:.1f} m, area {ROT['A']:.1f} m², Cp(model) {ROT['cp']:.3f}; shaft r {R_SHAFT} m, {N_SEG} bays of {L_AX} m, hub at {out['shaft']['hub_height']:.1f} m")
for v, torque_basis in ((4.0, "model"), (6.0, "model"), (6.0, "calibrated"), (9.0, "model"), (12.0, "model")):
    a = PR.evaluate.__globals__["RT"].best_rotor(PR.geo(6, 1.2, 1.2, 0.20), PR.BETA)
    Vn = v * math.cos(PR.BETA); Om = a["lam"] * Vn / 1.8
    Pm = a["cp_on_V"] * 0.5 * PR.RHO * v**3 * ROT["A"]
    Q = Pm / Om * (1.0 if torque_basis == "model" else K / 0.7)      # calibrated: electrical/0.7 drivetrain
    F = a["ct_on_Vn"] * 0.5 * PR.RHO * Vn**2 * ROT["A"] + LIFT
    sd = Q * L_AX / (F * R_SHAFT**2)
    case = dict(v=v, basis=torque_basis, rpm=Om * 60 / 2 / math.pi, Q=Q, F_ax=F, sin_delta=sd)
    if sd < 0.95:
        delta = math.degrees(math.asin(sd))
        d = dict(n_lines=6, n_seg=N_SEG, r_shaft=R_SHAFT, l_ax=L_AX, delta_deg=delta, beta_deg=30, ring_D=RING_D, ring_t=(RING_D - RING_ID) / 2,
                 line_dia_mm=LINE_D, F_ax=F, opt=dict(ring_mat="cfrp", ring_spokes=0, top_ring_stiff=1.0), T_line=F / 6)
        f = RT.trpt_fea(d, Q, max_it=60000)
        case.update(delta_deg=delta, fea={k: (float(v_) if isinstance(v_, (int, float, np.floating)) else v_) for k, v_ in f.items() if k not in ("x", "bars", "kinds", "seg_twist_deg")},
                    max_seg_twist=float(max(f["seg_twist_deg"])) if "seg_twist_deg" in f else None)
        I = math.pi / 64 * (RING_D**4 - RING_ID**4); C_cr = 3.0 * 100e9 * I / R_SHAFT**2
        case["ring_buckling_SF"] = C_cr / max(f.get("max_ring_C", 1.0), 1.0)
        print(f"  {v:4.1f} m/s ({torque_basis:10s}) rpm {case['rpm']:4.0f}  Q {Q:6.1f} N·m  F {F:5.0f} N  twist/bay {delta:4.1f}° → FEA: collapsed {f['collapsed']}, converged {f['converged']}, "
              f"max twist {case['max_seg_twist']}, line T {f.get('min_line_T', 0):.0f}–{f.get('max_line_T', 0):.0f} N, ring C {f.get('max_ring_C', 0):.0f} N (buckling SF {case['ring_buckling_SF']:.1f})")
    else:
        case.update(over_twist=True); print(f"  {v:4.1f} m/s ({torque_basis}) Q {Q:.1f} F {F:.0f}: needs sin δ = {sd:.2f} → shaft cannot carry this torque")
    out["cases"].append(case)
json.dump(out, open(f"out/proto_shaft_{R_SHAFT}_{L_AX}_{N_SEG}.json", "w"), indent=1, default=float)
