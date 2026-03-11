import openmm as mm
from openmm import app
from openmm import unit
import sys
import os
import time

def run_md(pdb_path, output_prefix, production_ns=100.0, test_mode=False, random_seed=None, temp_k=300.0):
    """
    Runs an explicit solvent MD production pipeline.
    If test_mode=True, runs a tiny fraction of the intended time to verify the setup.
    If random_seed is provided, it initializes the Langevin integrator with it for reproducible/independent replicas.
    """
    print(f"--- Starting Pipeline for {pdb_path} at {temp_k}K ---")
    
    # 1. Load Topology
    print("Loading PDB...")
    pdb = app.PDBFile(pdb_path)
    forcefield = app.ForceField('amber14-all.xml', 'amber14/tip3pfb.xml')

    # 2. Add Hydrogens, Solvent, and Ions
    print("Preparing structure with Modeller...")
    modeller = app.Modeller(pdb.topology, pdb.positions)
    print("Adding missing hydrogens...")
    modeller.addHydrogens(forcefield)
    
    print("Adding explicit solvent (TIP3P box with 1.0nm padding) and 0.15M NaCl...")
    modeller.addSolvent(forcefield, padding=1.0*unit.nanometers, ionicStrength=0.15*unit.molar)
    
    # Save the solvated topology so we can use it to view the trajectory later
    solvated_pdb = f"{output_prefix}_solvated.pdb"
    print(f"Saving solvated structure to {solvated_pdb}...")
    with open(solvated_pdb, 'w') as f:
        app.PDBFile.writeFile(modeller.topology, modeller.positions, f)

    # 3. Create System
    print("Creating System with PME (Particle Mesh Ewald) for long-range electrostatics...")
    system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME, 
                                     nonbondedCutoff=1.0*unit.nanometer, constraints=app.HBonds)
    
    # Add Barostat for NPT ensemble (1 atm, target temp)
    print(f"Adding Monte Carlo Barostat (1 atm, {temp_k}K)...")
    system.addForce(mm.MonteCarloBarostat(1*unit.atmospheres, temp_k*unit.kelvin, 25))

    # set up integrator
    integrator = mm.LangevinMiddleIntegrator(temp_k*unit.kelvin, 1/unit.picosecond, 0.002*unit.picoseconds)
    if random_seed is not None:
        integrator.setRandomNumberSeed(random_seed)

    # 4. Initialize Simulation
    simulation = app.Simulation(modeller.topology, system, integrator)
    simulation.context.setPositions(modeller.positions)

    platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
    print(f"Available Platforms: {platforms}")
    print(f"Using Platform: {simulation.context.getPlatform().getName()}")

    # 5. Energy Minimization
    print("Minimizing energy to remove steric clashes...")
    simulation.minimizeEnergy()

    # 6. Equilibration
    # 100ps NVT/NPT equilibration (50,000 steps at 2fs)
    eq_steps = 500 if test_mode else 50000 
    print(f"Running Equilibration for {eq_steps} steps...")
    simulation.context.setVelocitiesToTemperature(300*unit.kelvin)
    simulation.step(eq_steps)

    # 7. Production
    # Calculate steps: 1 ns = 1000 ps = 500,000 steps (at 2fs/step)
    prod_steps = 1000 if test_mode else int((production_ns * 1000.0) / 0.002)
    print(f"Running Production for {prod_steps} steps ({production_ns} ns)...")
    
    # Reporters: Save state data every 10ps (5000 steps), trajectory every 10ps
    report_interval = 100 if test_mode else 5000
    
    simulation.reporters.clear()
    simulation.reporters.append(app.StateDataReporter(sys.stdout, report_interval, step=True, 
                                                      potentialEnergy=True, temperature=True,
                                                      volume=True, density=True, speed=True))
    
    dcd_file = f"{output_prefix}_prod.dcd"
    simulation.reporters.append(app.DCDReporter(dcd_file, report_interval))

    start_time = time.time()
    simulation.step(prod_steps)
    end_time = time.time()
    
    print(f"Production finished in {end_time - start_time:.2f} seconds.")
    print(f"Saved trajectory to {dcd_file}")
    print("-" * 50)

if __name__ == '__main__':
    import argparse
    import concurrent.futures
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run in fast test mode to verify script')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (set to >1 to run replicas simultaneously on HPC)')
    args = parser.parse_args()

    os.makedirs('trajectories', exist_ok=True)
    
    if args.test:
        print("!!! RUNNING IN TEST MODE (Ultra short steps) !!!")
        run_md('structures/4AKE.pdb', 'trajectories/4AKE_test', production_ns=0.002, test_mode=True)
    else:
        target_ns = 600.0 # Extended 600ns production for the "Super-Simulation"
        num_replicas = 3
        
        print(f"!!! RUNNING ENHANCED HPC PRODUCTION MODE ({num_replicas}x {target_ns} ns per state) !!!")
        print(f"Parallel Workers: {args.workers}")
        
        tasks = []
        # Normal 300K Replicas (3.6us total)
        for rep in range(1, num_replicas + 1):
            seed = rep 
            tasks.append(('structures/4AKE.pdb', f'trajectories/4AKE_open_rep{rep}', target_ns, False, seed, 300.0))
            tasks.append(('structures/1AKE.pdb', f'trajectories/1AKE_closed_rep{rep}', target_ns, False, seed, 300.0))
            
        # Thermal Stress Replicas (Added 1AKE closed thermal stress)
        tasks.append(('structures/4AKE.pdb', 'trajectories/4AKE_open_thermal_400K', 100.0, False, 999, 400.0))
        tasks.append(('structures/1AKE.pdb', 'trajectories/1AKE_closed_thermal_400K', 100.0, False, 999, 400.0))

        if args.workers > 1:
            print(f"Dispatching {len(tasks)} tasks to ProcessPoolExecutor...")
            with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(run_md, *task) for task in tasks]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as exc:
                        print(f"A simulation replica generated an exception: {exc}")
        else:
            print("Running tasks sequentially...")
            for task in tasks:
                run_md(*task)
        
        print("\nALL MD SIMULATIONS COMPLETED SUCCESSFULLY.")
