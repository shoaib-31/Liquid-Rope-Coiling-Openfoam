# Instructions for Claude on Param Ganga HPC

## What This Is
OpenFOAM 6 liquid rope coiling simulation. Case is ready to run — just needs mesh generation and solver execution.

## Your Task
Run the simulation on Param Ganga HPC (PBS scheduler). The case simulates silicone oil (DN=5mm) falling H=40mm onto a static surface using interFoam (VOF method).

## Step-by-Step

```bash
# 1. Clone repo (if not already done)
git clone https://github.com/shoaib-31/Liquid-Rope-Coiling-Openfoam.git BTP
cd BTP

# 2. Load OpenFOAM
module load openfoam/6
# If that fails, try: module avail | grep -i foam
# Or: source /opt/openfoam6/etc/bashrc

# 3. Option A: Submit as PBS job (preferred)
qsub job_hpc.sh
# Monitor: qstat -u $USER
# Log: tail -f liquid_rope_coiling.log

# 4. Option B: Run interactively (if PBS not available or for testing)
# Mesh generation (serial, takes ~2 min):
blockMesh > log.blockMesh 2>&1
topoSet -dict system/topoSetDict1 > log.topoSet1 2>&1
refineMesh -overwrite > log.refineMesh1 2>&1
topoSet -dict system/topoSetDict2 > log.topoSet2 2>&1
refineMesh -overwrite > log.refineMesh2 2>&1

# Set initial conditions:
cp 0/alpha.siliconoil.orig 0/alpha.siliconoil
setFields > log.setFields 2>&1

# Decompose and run parallel:
decomposePar > log.decomposePar 2>&1
mpirun -np 96 interFoam -parallel > log.interFoam 2>&1

# After solver finishes:
reconstructPar > log.reconstructPar 2>&1
```

## Key Parameters (already set)
- **endTime**: 3.0 s (need at least 1.5s for coiling onset)
- **writeInterval**: 0.1 s
- **maxCo**: 0.5, **maxAlphaCo**: 0.3
- **Mesh**: ~1.49M cells after 2 refinements
- **Decomposition**: 96 subdomains (scotch method)
- **Solver**: interFoam (VOF, PIMPLE, adaptive dt)

## If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| `module load openfoam/6` fails | Try `module avail`, look for openfoam or OpenFOAM |
| refineMesh fails with "tan3 not found" | Use `refineMeshDict2` (copy provided) with only `tan1 tan2` directions |
| Fewer cores available | Edit `system/decomposeParDict` → change `numberOfSubdomains` to match, and change `-np` in mpirun |
| Job walltime too short | Edit `job_hpc.sh` → increase walltime |
| Permission errors | `chmod -R 755 .` |

## Adjusting Core Count
If you don't have 96 cores, change these two things:
1. `system/decomposeParDict` → `numberOfSubdomains <N>;`
2. `mpirun -np <N>` in job_hpc.sh or command line

Good values: 16, 24, 32, 48, 64, 96.

## Expected Output
- Time directories: `0.1/`, `0.2/`, ... `3.0/` (each ~50MB)
- Each contains: `U`, `p_rgh`, `alpha.siliconoil`, `phi`
- Total output: ~1.5 GB for 3.0s
- Expected runtime: 4-8 hours on 96 cores

## After Simulation Completes
```bash
# Check last timestep written
ls -d [0-9]* | sort -n | tail -5

# Quick sanity check — should see max alpha ~1.0
grep "Courant Number" log.interFoam | tail -5

# Push results info back (don't push the actual time dirs — too large)
echo "Simulation completed at $(date). Last timestep: $(ls -d [0-9]* | sort -n | tail -1)" > STATUS.md
git add STATUS.md log.blockMesh log.interFoam
git commit -m "Simulation complete on Param Ganga"
git push
```
