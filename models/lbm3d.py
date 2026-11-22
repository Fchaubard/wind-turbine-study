"""3D lattice-Boltzmann (D3Q19, BGK + Smagorinsky) of tilted actuator-annulus rotors stacked along a tether.
Measures the power of each rotor relative to an isolated one, i.e. the stacking wake factor used in lcoe_opt.py.
usage: python lbm3d.py <n_rotors> <spacing_in_D> [steps]"""
import sys, json, math, time
import numpy as np

n_rot = int(sys.argv[1]); spacing = float(sys.argv[2]); steps = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
NX, NY, NZ = 232, 84, 116
D = 32.0; R = D / 2; bR = 0.25; BETA = math.radians(22)
U0, TAU0, CS, K = 0.06, 0.52, 0.16, 0.030
c = np.array([[0,0,0],[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],[1,1,0],[-1,-1,0],[1,-1,0],[-1,1,0],
              [1,0,1],[-1,0,-1],[1,0,-1],[-1,0,1],[0,1,1],[0,-1,-1],[0,1,-1],[0,-1,1]])
w = np.array([1/3] + [1/18]*6 + [1/36]*12, dtype=np.float32)
ax = np.array([math.cos(BETA), 0.0, math.sin(BETA)])            # tether / rotor axis, downwind and up
X, Y, Z = np.meshgrid(np.arange(NX), np.arange(NY), np.arange(NZ), indexing="ij")
x0 = np.array([40.0, NY / 2, 26.0])
masks = []
for i in range(n_rot):
    cen = x0 + ax * spacing * D * i
    dx, dy, dz = X - cen[0], Y - cen[1], Z - cen[2]
    s = dx * ax[0] + dz * ax[2]                                  # axial distance
    rr = np.sqrt(np.maximum(dx**2 + dy**2 + dz**2 - s**2, 0))
    masks.append((np.abs(s) <= 1.0) & (rr <= R * (1 + bR / 2)) & (rr >= R * (1 - bR / 2)))   # thin annulus, width bR·R
act = np.zeros((NX, NY, NZ), bool)
for m in masks: act |= m

def feq(rho, u):
    cu = np.tensordot(c, u, axes=(1, 0)).astype(np.float32)
    uu = (u**2).sum(0)
    return w[:, None, None, None] * rho * (1 + 3 * cu + 4.5 * cu**2 - 1.5 * uu)

u = np.zeros((3, NX, NY, NZ), np.float32); u[0] = U0
rho = np.ones((NX, NY, NZ), np.float32)
f = feq(rho, u)
u1 = np.zeros((3, 1, NY, NZ), np.float32); u1[0] = U0
F_IN = feq(np.ones((1, NY, NZ), np.float32), u1)[:, 0]
t0 = time.time(); hist = []
for it in range(steps):
    rho = f.sum(0)
    u = np.tensordot(c.T.astype(np.float32), f, axes=(1, 0)) / rho
    # actuator: momentum sink along the rotor axis
    un = u[0] * ax[0] + u[2] * ax[2]
    Fn = np.where(act, -K * rho * un, 0).astype(np.float32)
    u[0] += 0.5 * Fn * ax[0] / rho; u[2] += 0.5 * Fn * ax[2] / rho
    fe = feq(rho, u)
    fn = f - fe
    Pi = np.sqrt(sum((np.tensordot((c[:, a] * c[:, b]).astype(np.float32), fn, axes=(0, 0)))**2 for a in range(3) for b in range(3)))
    tau = 0.5 * (TAU0 + np.sqrt(TAU0**2 + 18 * CS**2 * Pi / rho))
    cF = (c[:, 0] * ax[0] + c[:, 2] * ax[2]).astype(np.float32)
    f = f - fn / tau + (1 - 0.5 / tau) * 3 * w[:, None, None, None] * cF[:, None, None, None] * Fn
    for i in range(1, 19):
        f[i] = np.roll(f[i], tuple(c[i]), axis=(0, 1, 2))
    f[:, 0] = F_IN
    f[:, -1] = f[:, -2]
    if it % 250 == 0 or it == steps - 1:
        P = [float((K * rho * un * un)[m].sum()) for m in masks]
        hist.append(P); print(it, [round(p, 5) for p in P], f"{time.time()-t0:.0f}s", flush=True)
        if not np.isfinite(P[0]): break
Pm = np.mean(hist[-3:], axis=0).tolist()
json.dump(dict(n=n_rot, spacing=spacing, P=Pm, hist=hist, grid=[NX, NY, NZ], D=D, beta=22, K=K, cells=[int(m.sum()) for m in masks]),
          open(f"out/lbm3d_{n_rot}_{spacing}.json", "w"))
np.savez_compressed(f"out/lbm3d_field_{n_rot}_{spacing}.npz", ux=u[0][:, NY // 2, :], uz=u[2][:, NY // 2, :], act=act[:, NY // 2, :])
