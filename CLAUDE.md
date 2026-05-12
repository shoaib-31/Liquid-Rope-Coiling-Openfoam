# Liquid Rope Coiling — OpenFOAM BTP Project
## IIT Roorkee | Bachelor's Thesis Project

---

## Project Goal
Simulate and analyze the pattern a viscous liquid makes when it falls from different heights onto static and moving surfaces. The key phenomenon is **liquid rope coiling** — when a viscous stream falls and buckles/coils at the impact point, forming helical patterns.

**Variables being studied:**
- Fall height (H): 20–105 mm in current mesh
- Liquid properties: silicon oil (power-law, n=0.2, shear-thinning)
- Surface type: currently static; moving surface planned next

---

## Key Papers (in `papers/`)

| File | What It Contributes |
|------|-------------------|
| `etfs5 3.pdf` | **Rathaur et al. (IIT Roorkee)** — Most relevant. Silicone oil + epoxy resin on static/moving surfaces. Regimes: dripping, jetting, coiling. On moving surface: translated coil, side-kick, meandering |
| `Neil M. Ribe 2006.pdf` | Stability analysis. 4 regimes: Viscous (V), Gravitational (G), Inertio-gravitational (IG), Inertial (I). Frequency scaling laws |
| `nature1 2.pdf` | Original 1998 paper — first scaling law for coiling frequency |
| `Zhaohuan Zhang...pdf` | Experimental: 1000–10000 cSt silicone oil, frequency vs height, rheological transition |
| `Numerical Shaozhen Hua 2021.pdf` | **Numerical method reference** — VOF + FVM for jet buckling, rubber melt, power-law fluids |
| `Yuan Liu 2024.pdf` | Elastic rope coiling (microfibers) — different from viscous coiling, less directly relevant |

---

## OpenFOAM Case Structure

### Solver: `interFoam` (VOF two-phase incompressible)
- Tracks oil-air interface using volume fraction `alpha.siliconoil` (0=air, 1=oil)
- Laminar flow (Re is low for viscous coiling)
- Power-law viscosity model for silicon oil

### Directory Layout
```
BTP/
├── 0/                          ← Initial & boundary conditions
│   ├── alpha.siliconoil.orig   ← Template: copy to alpha.siliconoil before running
│   ├── p_rgh                   ← Pressure (minus hydrostatic)
│   └── U                       ← Velocity
├── constant/
│   ├── transportProperties     ← Fluid properties (silicon oil + air)
│   ├── turbulenceProperties    ← laminar
│   ├── g                       ← Gravity: (0 -9.81 0)
│   └── polyMesh/               ← GENERATED — not in git (988MB)
├── system/
│   ├── controlDict             ← Solver control (endTime, writeInterval etc.)
│   ├── blockMeshDict           ← Mesh geometry definition
│   ├── fvSchemes               ← Numerical schemes
│   ├── fvSolution              ← Linear solver settings (PIMPLE, GAMG)
│   ├── setFieldsDict           ← Initial oil region (nozzle box)
│   ├── topoSetDict1/2          ← Cell selection for mesh refinement
│   ├── refineMeshDict          ← Refinement settings
│   └── decomposeParDict        ← 48 subdomains for parallel (HPC)
├── postprocess/
│   └── analyze_coiling.py      ← Python post-processing script
├── papers/                     ← Research papers
├── CLAUDE.md                   ← This file
├── Allrun                      ← Full run script (mesh → setfields → solve)
├── Allclean                    ← Clean all generated files
├── run.sh                      ← Docker-based run helper
├── job_hpc.sh                  ← PBS job script for Param Ganga HPC
└── liquidRopeCoiling.foam      ← Open this in ParaView to visualize
```

---

## Geometry (from blockMeshDict)

All in mm (convertToMeters 0.001):
- **Nozzle radius**: 2.5 mm (D_N = 5mm), at y=0 (top)
- **Nozzle exit**: at y = -20 mm
- **Fall height to surface**: 50 mm
- **Static surface (floor)**: at y = -70 mm
- **Tank walls**: ±5 mm in x and z (upper), ±8 mm at bottom
- **Coordinate system**: y is vertical (gravity in -y direction)

---

## Fluid Properties (constant/transportProperties)

| Property | Silicon Oil | Air |
|----------|------------|-----|
| Model | Newtonian | Newtonian |
| Density (ρ) | 920 kg/m³ | 1.2 kg/m³ |
| Dynamic viscosity (μ) | 0.15 Pa.s | — |
| Kinematic viscosity (ν) | 1.63×10⁻⁴ m²/s | 1.5×10⁻⁵ m²/s |
| Surface tension σ | 0.0187 N/m (oil-air) | |

Note: Rathaur et al. measured SO as essentially Newtonian (n=0.99). Previous power-law n=0.2 was incorrect.

---

## How to Run (on Mac with Docker)

### Full pipeline from scratch:
```bash
# Step 1: Generate mesh (212k → 4.5M cells after 2x refinement)
docker run --rm --platform linux/amd64 -v /Users/shoaib31/BTP:/case -w /case \
  --entrypoint /bin/bash openfoam/openfoam6-paraview56 \
  -c "source /opt/openfoam6/etc/bashrc; blockMesh"

# Step 2: First refinement (select ±5mm box, refine)
docker run ... -c "source /opt/openfoam6/etc/bashrc; topoSet -dict system/topoSetDict1 && refineMesh -overwrite"

# Step 3: Second refinement (select ±4mm box, refine again)
docker run ... -c "source /opt/openfoam6/etc/bashrc; topoSet -dict system/topoSetDict2 && refineMesh -overwrite"

# Step 4: Set initial oil region
cp 0/alpha.siliconoil.orig 0/alpha.siliconoil
docker run ... -c "source /opt/openfoam6/etc/bashrc; setFields"

# Step 5: Run solver (WARNING: slow on Mac, see HPC section)
docker run ... -c "source /opt/openfoam6/etc/bashrc; interFoam"
```

### Quick helper:
```bash
./run.sh mesh       # Steps 1–3
./run.sh setfields  # Step 4
./run.sh solve      # Step 5
./run.sh full       # All steps
./run.sh clean      # Reset case
```

### Docker command template:
```bash
docker run --rm --platform linux/amd64 \
  -v /Users/shoaib31/BTP:/case -w /case \
  --entrypoint /bin/bash openfoam/openfoam6-paraview56 \
  -c "source /opt/openfoam6/etc/bashrc; <COMMAND>"
```

---

## Mesh Details (after running)

| Stage | Cells |
|-------|-------|
| After blockMesh | 212,712 |
| After 1st refineMesh | ~818,296 |
| After 2nd refineMesh | ~4,515,304 |

**Cell size in refined jet region**: ~0.088 mm (gives ~7 cells across the rope diameter D_R≈0.63mm)

---

## Simulation Parameters (system/controlDict)

| Parameter | Value | Meaning |
|-----------|-------|---------|
| endTime | 3.0 s | Physical time to simulate |
| writeInterval | 0.1 s | How often to save results |
| maxCo | 0.3 | Courant number limit (stability) |
| maxAlphaCo | 0.25 | Alpha Courant number limit |
| maxDeltaT | 0.01 s | Maximum timestep |
| PIMPLE correctors | 4 | Pressure-velocity coupling iterations |

---

## Performance on Mac (Docker x86 emulation on ARM)

- **Rate**: ~7×10⁻⁵ simulation-seconds per real-second
- **0.1s of simulation**: ~22 minutes
- **Full 4.5s simulation**: ~17 hours
- For real runs, use HPC (see below)

---

## Running on IIT Roorkee HPC (Param Ganga)

```bash
# 1. Copy case to cluster (run on your Mac terminal):
scp -r /Users/shoaib31/BTP username@paramganga.iitr.ac.in:~/BTP

# 2. SSH in and edit controlDict to set endTime 4.5

# 3. Submit job:
qsub job_hpc.sh

# 4. Monitor:
qstat -u username

# 5. Copy results back when done:
scp -r username@paramganga.iitr.ac.in:~/BTP/[0-9]* /Users/shoaib31/BTP/
```

The `job_hpc.sh` script is configured for 16 cores (1 node × 16 cores), ~6h walltime.

---

## Running on AWS Spot Instance

```bash
# Uses aws_spot_run.sh helper script
./aws_spot_run.sh launch        # Launch c6i.4xlarge spot (~$0.25/hr)
./aws_spot_run.sh setup <ip>    # Install OpenFOAM 6
./aws_spot_run.sh upload <ip>   # Upload case files
./aws_spot_run.sh run <ip>      # Mesh + solve (16 cores parallel)
./aws_spot_run.sh monitor <ip>  # Watch solver progress
./aws_spot_run.sh download <ip> # Get results
./aws_spot_run.sh terminate <id> # Kill instance
```

Instance: c6i.4xlarge (16 vCPUs, 32GB RAM). Expected cost: ~$0.50-1.00 total for 3s simulation.

---

## Visualization (ParaView)

1. Open ParaView 6.1 (installed at `/Applications/ParaView-6.1.0-RC1.app`)
2. File → Open → `liquidRopeCoiling.foam`
3. Click Apply
4. Color by `alpha.siliconoil` (0=air, 1=oil)
5. Add **Threshold** filter: `alpha.siliconoil` between 0.5 and 1 → see only the oil rope
6. Press Play to animate coiling behavior
7. Use **Clip** filter to see cross-sections

**What to look for:**
- t~0.1–0.3s: Oil falls straight (jetting regime)
- t~0.3–0.8s: Onset of buckling (jet starts to wobble)
- t>0.8s: Steady coiling (helical pattern forms)

---

## Current Status (as of May 2026)

- [x] OpenFOAM 6 installed via Docker
- [x] First attempt with D_N=9mm, H=80mm — failed (jetting, no coiling, solver stuck at t=2.4s)
- [x] Case redesigned: D_N=5mm, H=50mm, Newtonian SO (matching Rathaur et al.)
- [x] Mesh generated and verified (4.5M cells, Mesh OK)
- [x] setFields verified, render script fixed (full domain view)
- [x] AWS spot instance script prepared (c6i.4xlarge, 16 cores)
- [ ] Run simulation to t=3.0s on AWS spot
- [ ] Render video showing coiling and heap formation
- [ ] Parametric study: vary H (fall height), surface speed
- [ ] Quantitative extraction of coiling frequency vs H
- [ ] Comparison with Rathaur et al. (IIT Roorkee) experimental data

---

## Key Physics Concepts to Know

- **VOF (Volume of Fluid)**: Method to track oil-air interface. `alpha=1` means 100% oil, `alpha=0` means air
- **Courant number (Co)**: Measures how far fluid moves per timestep. Must stay < 0.25 for stability
- **PIMPLE**: Pressure-velocity coupling algorithm used by interFoam
- **Newtonian fluid**: Constant viscosity regardless of shear rate. Rathaur's SO has n=0.99 (effectively Newtonian)
- **Coiling regimes**: Viscous (low H) → Gravitational → Inertio-gravitational → Inertial (high H). For D_N=5mm, H=50mm: coiling regime per Rathaur Fig 5a
- **p_rgh**: Modified pressure = p − ρgh (removes hydrostatic component, easier numerically)

---

## Python Environment

Use miniconda at `/opt/homebrew/Caskroom/miniconda/base`. For post-processing:
```bash
conda activate base  # or create a new env
pip install numpy matplotlib pyvista  # for post-processing
python postprocess/analyze_coiling.py
```
