"""Adam-driven lattice optimization with ABACUS relax evaluations (dynamic workflow)."""

from aiida import load_profile
from aiida.engine import run
from aiida.orm import Dict, Int, List, load_code
from aiida_abacus.workflows.relax import AbacusRelaxWorkChain
from ase.spacegroup import crystal

from aiida_reoptimize.base.Extractors import BasicExtractor
from aiida_reoptimize.base.OptimizerBuilder import OptimizerBuilder
from aiida_reoptimize.optimizers.convex.GD import AdamOptimizer

load_profile()

# `misc.total_energy` holds the final total energy in eV of the relax run.
extractor = BasicExtractor(node_extractor=lambda outputs: outputs["misc"]["total_energy"])

code = load_code("abacus")

# Setup structure: silicon diamond (space group 227)
atoms = crystal(
    "Si",
    basis=(0.0, 0.0, 0.0),
    spacegroup=227,
    cellpar=[5.43, 5.43, 5.43, 90, 90, 90],
)

# Set up the optimizer for structure optimization. The relax workchain
# consumes its ABACUS calculation inputs from the `base.abacus` namespace.
builder = OptimizerBuilder.from_ase(
    optimizer_workchain=AdamOptimizer,
    calculator_workchain=AbacusRelaxWorkChain,
    extractor=extractor,
    calculator_parameters={
        "base": {
            "abacus": {
                "code": code,
                "parameters": {
                    "input": {
                        "calculation": "cell-relax",
                        "basis_type": "pw",
                        "scf_thr": 1e-7,
                        "relax_nmax": 30,
                        "force_thr_ev": 0.02,
                        "stress_thr": 10,
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
        }
    },
    bulk=atoms,
    structure_keyword=("structure",),
)

# Setup lattice parameters: the diamond cubic lattice is described by `a` alone.
a = 5.43

optimizer_parameters = {
    "itmax": Int(20),
    "parameters": Dict(
        {
            "algorithm_settings": {"tolerance": 1e-3},
            "initial_parameters": List(list=[a]),
        }
    ),
}

optimizer = builder.get_optimizer()
results = run(optimizer, **optimizer_parameters)

print("Optimization Results:")
print(f"Best position: {results['optimized_parameters']}")
print(f"Best value: {results['final_value']}")
