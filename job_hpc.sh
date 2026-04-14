#!/bin/bash
# ============================================================
# HPC Job Script for Param Ganga (IIT Roorkee) - PBS/TORQUE
# ============================================================
# HOW TO USE ON PARAM GANGA:
#   1. Copy your entire BTP folder to the cluster:
#      scp -r /Users/shoaib31/BTP username@paramganga.iitr.ac.in:~/BTP
#
#   2. SSH to the cluster:
#      ssh username@paramganga.iitr.ac.in
#
#   3. Load OpenFOAM module (check available with: module avail):
#      module load openfoam/6   (or whatever version is available)
#
#   4. Submit this job:
#      cd ~/BTP
#      qsub job_hpc.sh
#
#   5. Monitor job:
#      qstat -u username
#
#   6. When done, copy results back:
#      scp -r username@paramganga.iitr.ac.in:~/BTP/[0-9]* /Users/shoaib31/BTP/
# ============================================================

#PBS -N liquidRopeCoiling
#PBS -l nodes=2:ppn=24
#PBS -l walltime=12:00:00
#PBS -l mem=96gb
#PBS -q workq
#PBS -j oe
#PBS -o liquid_rope_coiling.log

# Change to case directory
cd $PBS_O_WORKDIR

# Load OpenFOAM (adjust module name for your cluster)
module load openfoam/6 2>/dev/null || source /opt/openfoam6/etc/bashrc

echo "=========================================="
echo " Job started: $(date)"
echo " Working dir: $PBS_O_WORKDIR"
echo " Nodes: $PBS_NODEFILE"
echo "=========================================="

# Full simulation (4.5 seconds)
# Edit controlDict to set endTime 4.5 before submitting!

# Step 1: Generate mesh (serial - fast)
blockMesh > log.blockMesh 2>&1

# Step 2: Refinements (serial - fast)
topoSet -dict system/topoSetDict1 > log.topoSet1 2>&1
refineMesh -overwrite > log.refineMesh1 2>&1
topoSet -dict system/topoSetDict2 > log.topoSet2 2>&1
refineMesh -overwrite > log.refineMesh2 2>&1

# Step 3: Initial conditions (serial - fast)
cp 0/alpha.siliconoil.orig 0/alpha.siliconoil
setFields > log.setFields 2>&1

# Step 4: Decompose for parallel (split mesh into 48 parts)
decomposePar > log.decomposePar 2>&1

# Step 5: Run parallel interFoam
NPROCS=$(wc -l < $PBS_NODEFILE)
echo "Running interFoam on $NPROCS cores..."
mpirun -np $NPROCS -machinefile $PBS_NODEFILE interFoam -parallel > log.interFoam 2>&1

# Step 6: Reconstruct parallel results into single dataset
reconstructPar > log.reconstructPar 2>&1

echo "=========================================="
echo " Job finished: $(date)"
echo "=========================================="
