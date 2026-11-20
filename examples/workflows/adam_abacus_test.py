"""Adam lattice optimization of silicon diamond with ABACUS SCF evaluations."""

from aiida import load_profile
from aiida.engine import submit
from aiida.orm import Dict, Int, List, StructureData
from ase.spacegroup import crystal

from aiida_reoptimize.workflows.Optimization.Abacus import (
    AdamAbacusSCFOptimizer,
)

load_profile()

# Setup structure: silicon diamond (space group 227)
a = 5.43

atoms = crystal(
    "Si",
    basis=(0.0, 0.0, 0.0),
    spacegroup=227,
    cellpar=[a, a, a, 90, 90, 90],
)

optimizer_parameters = {
    "itmax": Int(50),
    "structure": StructureData(ase=atoms),
    "parameters": Dict(
        {
            "algorithm_settings": {
                "learning_rate": 0.05,
                "beta1": 0.75,
                "beta2": 0.999,
                "delta": 5e-3,
                "tolerance": 1e-3,
            },
            # The diamond cubic lattice has a single free lattice parameter `a`.
            "initial_parameters": List(list=[a]),
            "calculator_parameters": {
                # The ABACUS calculation inputs live in the `abacus` namespace,
                # so the code is referenced with a dotted path.
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

results = submit(AdamAbacusSCFOptimizer, **optimizer_parameters)
print(f"Submitted AdamAbacusSCFOptimizer: {results.pk}")
