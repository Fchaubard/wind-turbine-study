# wind-turbine-study

Concept study: what is the cheapest way to turn wind into electricity?

**Read the report:** open `index.html` (self-contained, interactive 3D model, charts, sources).

It starts from a windsock that funnels wind into a small turbine (it does not work: a funnel cannot concentrate the wind's energy), moves to kites that fly across the wind, and ends with a global search for the lowest cost per MWh and the conditions for reaching $10/MWh.

| Step | Result |
|---|---|
| Windsock d → d/100 | about 1/3,000 of the target power; ruled out by momentum theory, 2D CFD, membrane FEA and frame FEA |
| Rotary kite ring with a rope shaft to a ground generator | parity with a 5 MW turbine ($47 vs $51/MWh), FEA-checked |
| Global optimum, every design variable free | fly-gen kite ring, $38/MWh vs $50 for the best conventional turbine on the same site (7.5 m/s, 7 %, 25 yr) |
| Stretch technology + utility finance + 10.5 m/s site | $16/MWh |
| Road to $10/MWh | reachable only if flying generators cost about $100/kW (car-industry drive units), on a ≥ 9 m/s site at < 6 % finance |

| Prototype for Punta Mita | nine concepts simulated in local wind; a 4 m cloth-sail windmill on a pole wins (about $1,000 in parts, 44 W average). See `SAIL_WINDMILL.md` |

All numbers are concept-level (±30–40 %).

## Layout

- `index.html`: the report
- `models/`: Python sources. `models.py` momentum model and costs; `lbm_cfd.py` 2D lattice-Boltzmann CFD; `lbm3d.py` 3D lattice-Boltzmann of stacked tilted rotors; `fea_membrane.py`, `fea_frame.py` structural FEA; `rotary.py` kite-ring rotor, shaft FEA and design levers; `lcoe_opt.py` global LCOE optimiser; `target10.py` what must be true for $10/MWh; `build_page.py` builds the report
- `results/`: JSON outputs and CFD images
- `export/`: OBJ geometry

## Run

```bash
uv venv -p 3.12 && uv pip install numpy scipy matplotlib
cd models && mkdir -p out && python lcoe_opt.py && python target10.py 10
```

## Deploy

`render.yaml` describes a static site; GitHub Pages serves the same `index.html`.
