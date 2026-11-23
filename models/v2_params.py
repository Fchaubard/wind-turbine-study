"""Punta Mita machine v2: 7 m cloth-sail rotor, free-yaw head, 12 m tripod on a 4 x 4 m concrete pad. Metres; wind toward +x; z up."""
import math
V2 = dict(pad=4.0, foot_r=2.0, apex_z=11.75, hub_z=12.0, leg_od=0.073, leg_w=0.0012, brace_z=(2.94, 5.87, 8.81), brace_od=0.0295, brace_w=0.0012,
          R=3.5, n=8, spar_od=0.0386, spar_w=0.00165, spar_in=0.25, cone_deg=8.0, hub_d=0.70, hub_t=0.015, bow=1.4, stay_d=0.0063,
          luff=(0.40, 3.40), clew_r=0.78, belly=0.30, overhang=0.90, head_od=0.0603, head_w=0.0055,
          tail_boom=3.2, tail_w=1.6, tail_h=1.2, gear1=(53, 14), gear2=(48, 12), jack_drop=0.34, motor_drop=0.42, rim_d=0.40)
V2["cone"] = math.radians(V2["cone_deg"])
