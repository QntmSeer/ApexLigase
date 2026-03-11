import openmm as mm
from openmm import app
from openmm import unit
import sys

def main():
    print("Loading 4AKE.pdb...")
    pdb = app.PDBFile('structures/4AKE.pdb')
    
    print("Setting up forcefield...")
    forcefield = app.ForceField('amber14-all.xml', 'amber14/tip3pfb.xml')

    print("Adding missing hydrogens...")
    modeller = app.Modeller(pdb.topology, pdb.positions)
    modeller.addHydrogens(forcefield)
    
    print("Saving protonated structure to structures/4AKE_h.pdb...")
    with open('structures/4AKE_h.pdb', 'w') as f:
        app.PDBFile.writeFile(modeller.topology, modeller.positions, f)
    
    print("Creating system in vacuum for fast test...")
    system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.NoCutoff, 
                                     constraints=app.HBonds)
    
    print("Setting up Langevin integrator...")
    integrator = mm.LangevinMiddleIntegrator(300*unit.kelvin, 1/unit.picosecond, 0.002*unit.picoseconds)
    
    print("Initializing simulation...")
    # Try CUDA/OpenCL if available, otherwise fallback to Reference/CPU
    platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
    print(f"Available platforms: {platforms}")
    
    simulation = app.Simulation(modeller.topology, system, integrator)
    simulation.context.setPositions(modeller.positions)
    
    print("Minimizing energy...")
    simulation.minimizeEnergy()
    
    print("Running 5000 steps (10ps) test simulation...")
    # Add reporter to save state data to stdout
    simulation.reporters.append(app.StateDataReporter(sys.stdout, 500, step=True, 
                                                      potentialEnergy=True, temperature=True))
    # Add reporter to save the trajectory frames
    simulation.reporters.append(app.DCDReporter('test_traj.dcd', 50))
    
    simulation.step(5000)
    print("Test successful! Trajectory saved to test_traj.dcd")

if __name__ == '__main__':
    main()
