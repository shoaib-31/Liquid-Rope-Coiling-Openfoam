#!/bin/bash
# ============================================================
# Liquid Rope Coiling - OpenFOAM Run Script
# ============================================================
# This script runs the full simulation pipeline inside Docker.
#
# WHAT EACH STEP DOES:
#   1. blockMesh      - Creates the 3D mesh from blockMeshDict
#   2. topoSet (x2)   - Selects cells near the jet path for refinement
#   3. refineMesh (x2) - Splits those cells to get finer resolution where it matters
#   4. cp alpha file   - Copies the boundary condition template for the oil phase
#   5. setFields       - Fills the nozzle region with oil (alpha=1)
#   6. interFoam       - Runs the actual VOF two-phase simulation!
#
# USAGE:
#   ./run.sh           - Run full pipeline
#   ./run.sh mesh      - Only generate and refine mesh
#   ./run.sh solve     - Only run the solver (mesh must exist)
#   ./run.sh clean     - Remove all generated files
# ============================================================

DOCKER_IMG="openfoam/openfoam6-paraview56"
CASE_DIR="/Users/shoaib31/BTP"

run_of() {
    echo ""
    echo ">>> Running: $1"
    echo "------------------------------------------------------------"
    docker run --rm --platform linux/amd64 \
        -v "$CASE_DIR":/case -w /case \
        --entrypoint /bin/bash "$DOCKER_IMG" \
        -c "source /opt/openfoam6/etc/bashrc; $1" 2>&1
    echo "------------------------------------------------------------"
    echo ">>> Done: $1 (exit: $?)"
}

case "${1:-full}" in
    mesh)
        run_of "blockMesh"
        run_of "topoSet -dict system/topoSetDict1"
        run_of "refineMesh -overwrite"
        run_of "topoSet -dict system/topoSetDict2"
        run_of "refineMesh -overwrite"
        ;;
    setfields)
        cp "$CASE_DIR/0/alpha.siliconoil.orig" "$CASE_DIR/0/alpha.siliconoil"
        run_of "setFields"
        ;;
    solve)
        run_of "interFoam"
        ;;
    clean)
        run_of "foamCleanCase"
        rm -rf "$CASE_DIR/dynamicCode"
        echo "Case cleaned."
        ;;
    full)
        # Step 1: Mesh generation
        run_of "blockMesh"

        # Step 2: First mesh refinement (coarser region)
        run_of "topoSet -dict system/topoSetDict1"
        run_of "refineMesh -overwrite"

        # Step 3: Second mesh refinement (finer region)
        run_of "topoSet -dict system/topoSetDict2"
        run_of "refineMesh -overwrite"

        # Step 4: Set initial conditions
        cp "$CASE_DIR/0/alpha.siliconoil.orig" "$CASE_DIR/0/alpha.siliconoil"
        run_of "setFields"

        # Step 5: Run the solver
        echo ""
        echo "=========================================="
        echo "  Starting interFoam solver..."
        echo "  This will take a LONG time."
        echo "  Simulating 4.5 seconds of real time."
        echo "=========================================="
        run_of "interFoam"
        ;;
    *)
        echo "Usage: $0 {full|mesh|setfields|solve|clean}"
        ;;
esac
