"""Static evaluator workchains for ABACUS-based lattice calculations."""

from aiida.orm import List
from aiida_abacus.workflows.base import AbacusBaseWorkChain
from aiida_abacus.workflows.relax import AbacusRelaxWorkChain

from ...base.Evaluation import StaticEvalLatticeProblem


class AbacusSCFLatticeProblem(StaticEvalLatticeProblem):
    """Evaluate lattice perturbations with the ABACUS base (SCF) workchain.

    Inputs inherited from :class:`StaticEvalLatticeProblem`:

    - ``structure``: source crystal structure.
    - ``targets``: list of lattice parameter perturbations.
    - ``calculator_parameters``: inputs forwarded to ``AbacusBaseWorkChain``.
      The ABACUS calculation inputs live in the ``abacus`` namespace, so the
      code is referenced via ``codes = {"abacus.code": "abacus@<host>"}``.
    - ``structure_keyword``: path to the structure input in the builder
      (defaults to ``["abacus", "structure"]``).
    """

    calculator_workchain = AbacusBaseWorkChain

    @classmethod
    def define(cls, spec):
        super().define(spec)
        # ABACUS calculation inputs are exposed under the `abacus` namespace,
        # so the generated structure has to be injected there.
        spec.inputs["structure_keyword"].default = lambda: List(["abacus", "structure"])


class AbacusRelaxLatticeProblem(StaticEvalLatticeProblem):
    """Evaluate lattice perturbations with the ABACUS relax workchain.

    Inputs inherited from :class:`StaticEvalLatticeProblem`:

    - ``structure``: source crystal structure.
    - ``targets``: list of lattice parameter perturbations.
    - ``calculator_parameters``: inputs forwarded to ``AbacusRelaxWorkChain``.
      The ABACUS calculation inputs live in the ``base.abacus`` namespace, so
      the code is referenced via ``codes = {"base.abacus.code": "abacus@<host>"}``.
    - ``structure_keyword``: path to the structure input in the builder
      (defaults to ``["structure"]``).
    """

    calculator_workchain = AbacusRelaxWorkChain
