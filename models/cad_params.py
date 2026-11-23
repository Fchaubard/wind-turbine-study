"""Single source of dimensions for the Punta Mita sail windmill: CAD (cad_model.py) and FEA (sail_fea.py) both read this.
Metres. z up, wind blows toward +x, rotor is upwind of the pole (negative x)."""
import math

P = dict(
    # pole: two galvanised post tubes, 73 mm OD x 1.2 mm wall x 3.05 m, splinted at the joint
    pole_od=0.073, pole_wall=0.0012, pole_seg=3.05, pole_h=6.10,
    splint_len=1.0, n_splints=4,
    # guys: 3/16 in steel cable; three from the top, three from the joint
    # no guy may cross the rotor disc, so fore-aft loads go into a back-prop (two more post tubes) behind the pole
    guy_d=0.0048, guy_top_z=5.80, guy_top_r=4.5, guy_mid_z=3.05, guy_mid_r=2.6, guy_az=(90.0, 270.0),   # side guys only
    prop_base_x=2.20, prop_top_z=5.70,          # chosen by the FEA sweep: best worst-case safety factor
    stay_mid=True,                              # second stay rope to each spar at 0.65 R (FEA: spar safety factor 1.1 -> 1.6 in a squall)
    # rotor
    n_sails=8, R=2.5, spar_od=0.0295, spar_wall=0.0012, spar_in=0.15, cone_deg=8.0,
    hub_z=5.95, hub_x=-0.62, hub_disc_d=0.50, hub_disc_t=0.015,
    bowsprit_len=1.0, stay_d=0.0063,
    sail_luff=(0.30, 2.42), sail_clew_r=0.78, sail_belly=0.22,
    # drivetrain (a bicycle hung on the pole)
    bb_x=-0.50, chainring_d=0.195, chainstay=0.43, jack_cog_big_d=0.113, jack_cog_small_d=0.057,
    motor_drop=0.42, motor_rim_d=0.622, motor_hub_d=0.24, motor_width=0.135, motor_cog_d=0.057,
    plate_t=0.030, plate_w=0.10, standoff=(5.90, 5.15),
)
P["pole_id"] = P["pole_od"] - 2 * P["pole_wall"]
P["spar_id"] = P["spar_od"] - 2 * P["spar_wall"]
P["cone"] = math.radians(P["cone_deg"])
