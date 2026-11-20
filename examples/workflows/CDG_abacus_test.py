"""Conjugate-gradient lattice optimization of SrTiO3 with ABACUS SCF evaluations."""

from aiida import load_profile
from aiida.engine import submit
from aiida.orm import Dict, Int, List, StructureData
from ase.spacegroup import crystal

from aiida_reoptimize.workflows.Optimization.Abacus import (
    CDGAbacusSCFOptimizer,
)

load_profile()

# Setup structure: tetragonal SrTiO3 (space group 140)
a = 5.51
c = 7.79

atoms = crystal(
    ["Sr", "Ti", "O", "O"],
    basis=[(0, 0, 0.25), (0.0, 0.5, 0.0), (0.2451, 0.7451, 0), (0, 0.5, 0.25)],
    spacegroup=140,
    cellpar=[a, a, c, 90, 90, 90],
)

optimizer_parameters = {
    "itmax": Int(100),
    "structure": StructureData(ase=atoms),
    "parameters": Dict(
        {
            "algorithm_settings": {
                "tolerance": 1e-3,
                "learning_rate": 1e-2,
                "lr_increase": 1.2,
                "lr_decrease": 0.2,
                "delta": 1e-3,
            },
            # The tetragonal lattice has two free lattice parameters: `a` and `c`.
            "initial_parameters": List(list=[a, c]),
            "calculator_parameters": {
                "codes": {
                    "abacus.code": "abacus@localhost",
                },
                "abacus": {
                    "parameters": {
                        "input": {
                            "calculation": "scf",
                            "basis_type": "pw",
                            "ecutwfc": 100.0,
                            "scf_thr": 1e-7,
                            "smearing_method": "gauss",
                            "smearing_sigma": 0.01,
                        }
                    },
                    "metadata": {
                        "options": {
                            "resources": {
                                "num_machines": 1,
                                "num_mpiprocs_per_machine": 2,
                            },
                            # Prevent thread oversubscription when several
                            # ABACUS calculations run in parallel.
                            "environment_variables": {"OMP_NUM_THREADS": "1"},
                            "max_wallclock_seconds": 6 * 60 * 60,
                        }
                    },
                },
                "kpoints_distance": 0.15,
                "pseudo_family": "SSSP_1.3_PBE_efficiency",
                "max_iterations": 5,
                "clean_workdir": False,
            },
        }
    ),
}

results = submit(CDGAbacusSCFOptimizer, **optimizer_parameters)
print(f"Submitted CDGAbacusSCFOptimizer: {results.pk}")
