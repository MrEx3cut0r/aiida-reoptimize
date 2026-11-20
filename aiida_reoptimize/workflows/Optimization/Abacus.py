"""Static optimization workchains for ABACUS lattice problems."""

from ..Evaluation.abacus_evaluation import AbacusRelaxLatticeProblem, AbacusSCFLatticeProblem
from ._common import (
    AdamOptimizer,
    BFGSOptimizer,
    ConjugateGradientOptimizer,
    FixedPyMOOAlgorithmMixin,
    PyMOO_Optimizer,
    RMSpropOptimizer,
    StaticOptimizerBinding,
)


class BaseAbacusSCFOptimizer(StaticOptimizerBinding):
    """Bind the generic optimizers to the ABACUS SCF lattice evaluator."""

    evaluator_workchain = AbacusSCFLatticeProblem
    extractor_path = ("misc", "total_energy")


class AdamAbacusSCFOptimizer(BaseAbacusSCFOptimizer, AdamOptimizer):
    """Adam optimizer registered for ABACUS SCF lattice optimization."""


class CDGAbacusSCFOptimizer(BaseAbacusSCFOptimizer, ConjugateGradientOptimizer):
    """Conjugate-gradient optimizer registered for ABACUS SCF lattice optimization."""


class RMSpropAbacusSCFOptimizer(BaseAbacusSCFOptimizer, RMSpropOptimizer):
    """RMSprop optimizer registered for ABACUS SCF lattice optimization."""


class BFGSAbacusSCFOptimizer(BaseAbacusSCFOptimizer, BFGSOptimizer):
    """BFGS optimizer registered for ABACUS SCF lattice optimization."""


class PyMOOAbacusSCFOptimizer(BaseAbacusSCFOptimizer, PyMOO_Optimizer):
    """PyMOO-backed optimizer registered for ABACUS SCF lattice optimization."""


class G3PCXAbacusSCFOptimizer(
    FixedPyMOOAlgorithmMixin,
    BaseAbacusSCFOptimizer,
    PyMOO_Optimizer,
):
    """Fixed G3PCX PyMOO optimizer for ABACUS SCF lattice optimization."""

    fixed_algorithm_name = "G3PCX"


class NRBOAbacusSCFOptimizer(
    FixedPyMOOAlgorithmMixin,
    BaseAbacusSCFOptimizer,
    PyMOO_Optimizer,
):
    """Fixed NRBO PyMOO optimizer for ABACUS SCF lattice optimization."""

    fixed_algorithm_name = "NRBO"


class BaseAbacusRelaxOptimizer(StaticOptimizerBinding):
    """Bind the generic optimizers to the ABACUS relax lattice evaluator."""

    evaluator_workchain = AbacusRelaxLatticeProblem
    extractor_path = ("misc", "total_energy")


class AdamAbacusRelaxOptimizer(BaseAbacusRelaxOptimizer, AdamOptimizer):
    """Adam optimizer registered for ABACUS relax lattice optimization."""


class CDGAbacusRelaxOptimizer(BaseAbacusRelaxOptimizer, ConjugateGradientOptimizer):
    """Conjugate-gradient optimizer registered for ABACUS relax lattice optimization."""


class RMSpropAbacusRelaxOptimizer(BaseAbacusRelaxOptimizer, RMSpropOptimizer):
    """RMSprop optimizer registered for ABACUS relax lattice optimization."""


class BFGSAbacusRelaxOptimizer(BaseAbacusRelaxOptimizer, BFGSOptimizer):
    """BFGS optimizer registered for ABACUS relax lattice optimization."""


class PyMOOAbacusRelaxOptimizer(BaseAbacusRelaxOptimizer, PyMOO_Optimizer):
    """PyMOO-backed optimizer registered for ABACUS relax lattice optimization."""


class G3PCXAbacusRelaxOptimizer(
    FixedPyMOOAlgorithmMixin,
    BaseAbacusRelaxOptimizer,
    PyMOO_Optimizer,
):
    """Fixed G3PCX PyMOO optimizer for ABACUS relax lattice optimization."""

    fixed_algorithm_name = "G3PCX"


class NRBOAbacusRelaxOptimizer(
    FixedPyMOOAlgorithmMixin,
    BaseAbacusRelaxOptimizer,
    PyMOO_Optimizer,
):
    """Fixed NRBO PyMOO optimizer for ABACUS relax lattice optimization."""

    fixed_algorithm_name = "NRBO"
