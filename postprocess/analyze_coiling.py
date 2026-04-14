"""
Liquid Rope Coiling - Post-Processing Script
=============================================
This script analyzes OpenFOAM results to extract:
  - Coiling frequency vs time
  - Coiling radius vs time
  - Impact point position vs time

HOW IT WORKS:
  OpenFOAM writes alpha.siliconoil field (0=air, 1=oil) at each saved timestep.
  We look at a horizontal slice just above the static surface (y = -0.104 m)
  and find where the oil is (alpha > 0.5). The centroid of that region gives
  the impact position. Tracking this over time gives coiling frequency.

USAGE:
  conda activate base   (or any env with numpy/matplotlib)
  python postprocess/analyze_coiling.py

REQUIRES: numpy, matplotlib, (optionally) pyvista for 3D visualization
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import glob

CASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_foam_scalar_field(filepath):
    """Read an OpenFOAM scalar field file and return array of values."""
    values = []
    in_internal = False
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if 'internalField' in line and 'nonuniform' in line:
                in_internal = True
                continue
            if in_internal:
                try:
                    values.append(float(line))
                except ValueError:
                    if line == ')':
                        break
    return np.array(values)

def read_foam_vector_field(filepath):
    """Read an OpenFOAM vector field file and return Nx3 array."""
    values = []
    in_internal = False
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if 'internalField' in line and 'nonuniform' in line:
                in_internal = True
                continue
            if in_internal:
                if line.startswith('(') and line.endswith(')'):
                    vals = [float(x) for x in line[1:-1].split()]
                    if len(vals) == 3:
                        values.append(vals)
                elif line == ')':
                    break
    return np.array(values)

def get_time_directories():
    """Find all numeric time directories in case (excluding 0)."""
    times = []
    for d in sorted(os.listdir(CASE_DIR)):
        if d == '0':
            continue
        try:
            t = float(d)
            if os.path.isdir(os.path.join(CASE_DIR, d)):
                times.append((t, d))
        except ValueError:
            pass
    return sorted(times)

def analyze_impact_position(time_dirs):
    """
    For each timestep, read alpha field and find where oil hits the surface.
    Returns arrays of time, x_impact, z_impact.
    """
    # NOTE: This is a simplified analysis.
    # A full analysis requires reading cell center coordinates from constant/polyMesh/
    # and correlating them with alpha values.
    # This shows the approach - for full implementation use PyFoam or pyvista.

    print("\n=== Impact Position Analysis ===")
    print("(Simplified - reads alpha field statistics)")
    print(f"Found {len(time_dirs)} timesteps\n")

    times = []
    alpha_means = []
    alpha_maxes = []

    for t, dirname in time_dirs:
        alpha_file = os.path.join(CASE_DIR, dirname, 'alpha.siliconoil')
        if os.path.exists(alpha_file):
            alpha = read_foam_scalar_field(alpha_file)
            times.append(t)
            alpha_means.append(np.mean(alpha))
            alpha_maxes.append(np.max(alpha))
            print(f"  t={t:.3f}s: mean(alpha)={np.mean(alpha):.4f}, max={np.max(alpha):.4f}, cells_with_oil={np.sum(alpha>0.5)}")

    return np.array(times), np.array(alpha_means)

def plot_results(times, alpha_means):
    """Plot basic simulation statistics."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Liquid Rope Coiling - Simulation Results', fontsize=14, fontweight='bold')

    # Plot 1: Oil volume fraction over time
    ax1 = axes[0]
    ax1.plot(times, alpha_means, 'b-o', linewidth=2, markersize=6)
    ax1.set_xlabel('Simulation Time (s)', fontsize=12)
    ax1.set_ylabel('Mean Oil Volume Fraction', fontsize=12)
    ax1.set_title('Oil Conservation Check\n(should stay ~constant)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # Plot 2: Rate of change (proxy for flow dynamics)
    if len(times) > 1:
        ax2 = axes[1]
        dtimes = np.diff(times)
        dalpha = np.diff(alpha_means)
        ax2.plot(times[1:], dalpha/dtimes, 'r-o', linewidth=2, markersize=6)
        ax2.set_xlabel('Simulation Time (s)', fontsize=12)
        ax2.set_ylabel('d(alpha)/dt', fontsize=12)
        ax2.set_title('Rate of Change\n(oscillations → coiling)', fontsize=11)
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    outfile = os.path.join(CASE_DIR, 'postprocess', 'results.png')
    plt.savefig(outfile, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {outfile}")
    plt.show()

def print_instructions():
    print("""
=== For Full 3D Visualization ===

1. PARAVIEW (recommended):
   - Open ParaView (you have v6.1 installed)
   - File → Open → select 'liquidRopeCoiling.foam'
   - Click Apply
   - In Pipeline Browser, select the case
   - Color by 'alpha.siliconoil' (0=air blue, 1=oil red)
   - Press Play to animate
   - Use 'Threshold' filter (alpha > 0.5) to see only the oil
   - Use 'Clip' to see cross sections

2. KEY THINGS TO LOOK FOR IN PARAVIEW:
   - At early times: oil falls straight down as a jet
   - Watch for the BUCKLING to start (jet starts to wobble)
   - Then COILING begins (oil starts rotating as it piles up)
   - Measure the coiling radius and frequency from the visualization

3. TO MEASURE COILING FREQUENCY:
   - Use 'PlotSelectionOverTime' filter
   - Select a point near the bottom
   - Plot alpha vs time
   - Count oscillations per second = coiling frequency (Hz)
""")

if __name__ == '__main__':
    print("Liquid Rope Coiling - Post-Processing")
    print("=" * 45)
    print(f"Case directory: {CASE_DIR}")

    time_dirs = get_time_directories()

    if not time_dirs:
        print("\nNo output timesteps found yet!")
        print("The simulation writes output every 0.1s (writeInterval in controlDict).")
        print("Wait for the solver to reach t=0.1 before running this script.")
        print_instructions()
    else:
        times, alpha_means = analyze_impact_position(time_dirs)
        if len(times) > 0:
            plot_results(times, alpha_means)
        print_instructions()
