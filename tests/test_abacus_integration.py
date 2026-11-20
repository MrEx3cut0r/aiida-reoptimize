import unittest

from aiida import load_profile
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.orm import Bool, Computer, Dict, Float, Int, List, QueryBuilder, StructureData
from aiida.orm.nodes.data.code.installed import InstalledCode
from aiida.tools import delete_nodes
from aiida_abacus.workflows.base import AbacusBaseWorkChain
from aiida_abacus.workflows.relax import AbacusRelaxWorkChain
from ase import Atoms

from aiida_reoptimize.base.Evaluation import (
    StaticEvalLatticeProblem,
    _StaticEvalStructureBase,
)
from aiida_reoptimize.base.Extractors import BasicExtractor
from aiida_reoptimize.optimizers.convex.GD import AdamOptimizer
from aiida_reoptimize.optimizers.convex.QN import BFGSOptimizer
from aiida_reoptimize.structure.dynamic_structure import (
    StructureCalculator,
    StructureGenerationError,
)
from aiida_reoptimize.workflows.Evaluation.abacus_evaluation import (
    AbacusRelaxLatticeProblem,
    AbacusSCFLatticeProblem,
)
from aiida_reoptimize.workflows.Optimization._common import output_path_extractor
from aiida_reoptimize.workflows.Optimization.Abacus import (
    AdamAbacusRelaxOptimizer,
    AdamAbacusSCFOptimizer,
    BaseAbacusRelaxOptimizer,
    BaseAbacusSCFOptimizer,
    BFGSAbacusRelaxOptimizer,
    BFGSAbacusSCFOptimizer,
    CDGAbacusRelaxOptimizer,
    CDGAbacusSCFOptimizer,
    G3PCXAbacusRelaxOptimizer,
    G3PCXAbacusSCFOptimizer,
    NRBOAbacusRelaxOptimizer,
    NRBOAbacusSCFOptimizer,
    PyMOOAbacusRelaxOptimizer,
    PyMOOAbacusSCFOptimizer,
    RMSpropAbacusRelaxOptimizer,
    RMSpropAbacusSCFOptimizer,
)


def setUpModule():
    load_profile()


def _silicon_atoms():
    """Return a cubic reference structure with a single free lattice parameter."""
    return Atoms(
        "Si2",
        scaled_positions=[[0.0, 0.0, 0.0], [0.25, 0.25, 0.25]],
        cell=[[5.43, 0.0, 0.0], [0.0, 5.43, 0.0], [0.0, 0.0, 5.43]],
        pbc=True,
    )


def _abacus_code():
    """Return a stored ABACUS code (creating a minimal one if necessary)."""
    label = "aiida-reoptimize-test-abacus"
    computer_label = "aiida-reoptimize-test-host"
    existing = QueryBuilder().append(InstalledCode, filters={"label": label}).first()
    if existing:
        return existing[0]
    try:
        computer = Computer.collection.get(label=computer_label)
    except Exception:
        computer = Computer(
            label=computer_label,
            hostname=computer_label,
            transport_type="core.local",
            scheduler_type="core.direct",
            workdir="/tmp/opencode/aiida-reoptimize-test",
        )
        computer.store()
        computer.configure()
    return InstalledCode(
        computer=computer,
        filepath_executable="/usr/bin/true",
        default_calc_job_plugin="abacus.abacus",
        label=label,
    ).store()


SCF_CALCULATOR_PARAMETERS = {
    "abacus": {
        "parameters": {
            "input": {
                "calculation": "scf",
                "basis_type": "pw",
                "ecutwfc": 100.0,
                "scf_thr": 1e-7,
            }
        },
        "metadata": {
            "options": {
                "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
                "max_wallclock_seconds": 3600,
            }
        },
    },
    "kpoints_distance": 0.15,
    "max_iterations": 5,
}

RELAX_CALCULATOR_PARAMETERS = {
    "base": {
        "abacus": {
            "parameters": {
                "input": {
                    "calculation": "cell-relax",
                    "basis_type": "pw",
                    "ecutwfc": 100.0,
                    "scf_thr": 1e-7,
                    "relax_nmax": 30,
                    "force_thr_ev": 0.01,
                }
            },
            "metadata": {
                "options": {
                    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
                    "max_wallclock_seconds": 3600,
                }
            },
        },
        "kpoints_distance": 0.15,
    },
}


class TestAbacusEvaluators(unittest.TestCase):
    def test_scf_evaluator_binds_abacus_base_workchain(self):
        self.assertIs(AbacusSCFLatticeProblem.calculator_workchain, AbacusBaseWorkChain)

    def test_relax_evaluator_binds_abacus_relax_workchain(self):
        self.assertIs(AbacusRelaxLatticeProblem.calculator_workchain, AbacusRelaxWorkChain)

    def test_scf_evaluator_defaults_structure_keyword_to_abacus_namespace(self):
        default = AbacusSCFLatticeProblem.spec().inputs["structure_keyword"].default()
        self.assertEqual(default.get_list(), ["abacus", "structure"])

    def test_relax_evaluator_keeps_top_level_structure_keyword(self):
        default = AbacusRelaxLatticeProblem.spec().inputs["structure_keyword"].default()
        self.assertEqual(default.get_list(), ["structure"])

    def test_evaluators_expose_total_energy_output(self):
        """Both calculators must expose the Dict output the extractor reads."""
        for evaluator in (AbacusSCFLatticeProblem, AbacusRelaxLatticeProblem):
            outputs = evaluator.calculator_workchain.spec().outputs
            self.assertIn("misc", outputs)
            self.assertIs(outputs["misc"].valid_type, Dict)

    def test_evaluators_inherit_from_static_eval_lattice_problem(self):
        for evaluator in (AbacusSCFLatticeProblem, AbacusRelaxLatticeProblem):
            self.assertTrue(issubclass(evaluator, StaticEvalLatticeProblem))


class TestAbacusOptimizers(unittest.TestCase):
    def test_scf_optimizers_bind_scf_evaluator(self):
        for optimizer in (
            AdamAbacusSCFOptimizer,
            BFGSAbacusSCFOptimizer,
            CDGAbacusSCFOptimizer,
            RMSpropAbacusSCFOptimizer,
            PyMOOAbacusSCFOptimizer,
            G3PCXAbacusSCFOptimizer,
            NRBOAbacusSCFOptimizer,
        ):
            self.assertIs(optimizer.evaluator_workchain, AbacusSCFLatticeProblem)
            self.assertIsNotNone(optimizer.extractor)

    def test_relax_optimizers_bind_relax_evaluator(self):
        for optimizer in (
            AdamAbacusRelaxOptimizer,
            BFGSAbacusRelaxOptimizer,
            CDGAbacusRelaxOptimizer,
            RMSpropAbacusRelaxOptimizer,
            PyMOOAbacusRelaxOptimizer,
            G3PCXAbacusRelaxOptimizer,
            NRBOAbacusRelaxOptimizer,
        ):
            self.assertIs(optimizer.evaluator_workchain, AbacusRelaxLatticeProblem)
            self.assertIsNotNone(optimizer.extractor)

    def test_extractor_reads_total_energy_from_misc(self):
        self.assertEqual(BaseAbacusSCFOptimizer.extractor_path, ("misc", "total_energy"))
        self.assertEqual(BaseAbacusRelaxOptimizer.extractor_path, ("misc", "total_energy"))

        outputs = {"misc": {"total_energy": -15.2}}
        extractor = BasicExtractor(node_extractor=output_path_extractor(("misc", "total_energy")))
        self.assertEqual(extractor([{"pk": None, "status": "failed"}]), [extractor.get_penalty()])
        self.assertEqual(extractor.node_extractor(outputs), -15.2)

    def test_pymoo_optimizers_pin_fixed_algorithm(self):
        self.assertEqual(G3PCXAbacusSCFOptimizer.fixed_algorithm_name, "G3PCX")
        self.assertEqual(NRBOAbacusSCFOptimizer.fixed_algorithm_name, "NRBO")
        self.assertEqual(G3PCXAbacusRelaxOptimizer.fixed_algorithm_name, "G3PCX")
        self.assertEqual(NRBOAbacusRelaxOptimizer.fixed_algorithm_name, "NRBO")

    def test_optimizer_algorithm_mro(self):
        self.assertTrue(issubclass(AdamAbacusSCFOptimizer, AdamOptimizer))
        self.assertTrue(issubclass(BFGSAbacusRelaxOptimizer, BFGSOptimizer))


class TestPlaceLoadedCode(unittest.TestCase):
    def test_flat_key_places_code_at_top_level(self):
        parameters = {"options": {}}
        _StaticEvalStructureBase._place_loaded_code(parameters, "fleur", "code-node")
        self.assertEqual(parameters["fleur"], "code-node")
        self.assertEqual(parameters["options"], {})

    def test_dotted_key_places_code_in_nested_namespace(self):
        parameters = {"abacus": {"parameters": {}}}
        _StaticEvalStructureBase._place_loaded_code(parameters, "abacus.code", "code-node")
        self.assertEqual(parameters["abacus"]["code"], "code-node")
        self.assertEqual(parameters["abacus"]["parameters"], {})

    def test_deeply_dotted_key_creates_intermediate_namespaces(self):
        parameters = {}
        _StaticEvalStructureBase._place_loaded_code(parameters, "base.abacus.code", "code-node")
        self.assertEqual(parameters["base"]["abacus"]["code"], "code-node")

    def test_non_mapping_intermediate_raises_value_error(self):
        with self.assertRaises(ValueError):
            _StaticEvalStructureBase._place_loaded_code({"abacus": "not-a-namespace"}, "abacus.code", "code-node")


class TestAbacusBuilderGeneration(unittest.TestCase):
    def test_scf_builder_receives_structure_and_nested_parameters(self):
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusBaseWorkChain,
            calculator_parameters=dict(SCF_CALCULATOR_PARAMETERS),
            structure_keyword=("abacus", "structure"),
        )

        builder = structure_calculator.get_builder([5.5])

        self.assertIs(builder.process_class, AbacusBaseWorkChain)
        self.assertEqual(builder.abacus.parameters.get_dict()["input"]["calculation"], "scf")
        self.assertEqual(builder.kpoints_distance, Float(0.15))
        self.assertEqual(builder.max_iterations, Int(5))
        self.assertEqual([5.5, 5.5, 5.5], builder.abacus.structure.cell_lengths)

    def test_relax_builder_receives_structure_and_nested_parameters(self):
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusRelaxWorkChain,
            calculator_parameters=dict(RELAX_CALCULATOR_PARAMETERS),
            structure_keyword=("structure",),
        )

        builder = structure_calculator.get_builder([5.5])

        self.assertIs(builder.process_class, AbacusRelaxWorkChain)
        self.assertEqual(
            builder.base.abacus.parameters.get_dict()["input"]["calculation"],
            "cell-relax",
        )
        self.assertEqual(builder.base.kpoints_distance, Float(0.15))
        self.assertEqual([5.5, 5.5, 5.5], builder.structure.cell_lengths)

    def test_dict_parameter_set_serializes_scalars(self):
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusBaseWorkChain,
            calculator_parameters={"kpoints_distance": 0.2, "clean_workdir": True},
            structure_keyword=("abacus", "structure"),
        )

        builder = structure_calculator.get_builder([5.5])

        self.assertEqual(builder.kpoints_distance, Float(0.2))
        self.assertEqual(builder.clean_workdir, Bool(True))

    def test_unknown_builder_key_raises_structure_generation_error(self):
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusBaseWorkChain,
            calculator_parameters={"unknown_input": 1},
            structure_keyword=("abacus", "structure"),
        )

        with self.assertRaises(StructureGenerationError) as ctx:
            structure_calculator.get_builder([5.5])

        self.assertIn("unknown_input", str(ctx.exception))

    def test_unknown_nested_key_error_includes_namespace_path(self):
        """Rejections inside nested namespaces report the full dotted path.

        E.g. a mis-targeted ``codes`` entry would place a Code node at
        ``abacus.structure``, which is not a StructureData.
        """
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusBaseWorkChain,
            calculator_parameters={"abacus": {"structure": "not-a-structure"}},
            structure_keyword=("abacus", "structure"),
        )

        with self.assertRaises(StructureGenerationError) as ctx:
            structure_calculator.get_builder([5.5])

        self.assertIn("'abacus.structure'", str(ctx.exception))

    def test_builder_needs_no_code_until_submission(self):
        """The code is supplied at evaluation time via the ``codes`` mapping."""
        structure_calculator = StructureCalculator(
            structure=_silicon_atoms(),
            calculator=AbacusBaseWorkChain,
            calculator_parameters=dict(SCF_CALCULATOR_PARAMETERS),
            structure_keyword=("abacus", "structure"),
        )

        builder = structure_calculator.get_builder([5.5])

        self.assertIsNone(builder.abacus.code)


class TestAbacusEvaluatorWorkchain(unittest.TestCase):
    def setUp(self):
        # `instantiate_process` stores the WorkChainNode in the profile;
        # collect the instances and remove them again after each test.
        self._workchains = []

    def tearDown(self):
        if self._workchains:
            delete_nodes([workchain.node.pk for workchain in self._workchains], dry_run=False)

    def _instantiate(self, evaluator, **inputs):
        runner = get_manager().get_runner()
        workchain = instantiate_process(runner, evaluator, **inputs)
        self._workchains.append(workchain)
        return workchain

    def test_scf_generate_structures_resolves_dotted_code(self):
        code = _abacus_code()
        workchain = self._instantiate(
            AbacusSCFLatticeProblem,
            structure=StructureData(ase=_silicon_atoms()),
            targets=List(list=[[5.5]]),
            calculator_parameters=Dict(
                dict={
                    "codes": {"abacus.code": code.full_label},
                    **SCF_CALCULATOR_PARAMETERS,
                }
            ),
        )

        workchain.generate_structures()

        builder = workchain.ctx.builders[0]
        self.assertIs(builder.process_class, AbacusBaseWorkChain)
        self.assertEqual(builder.abacus.code.uuid, code.uuid)
        self.assertEqual([5.5, 5.5, 5.5], builder.abacus.structure.cell_lengths)

    def test_relax_generate_structures_resolves_dotted_code(self):
        code = _abacus_code()
        workchain = self._instantiate(
            AbacusRelaxLatticeProblem,
            structure=StructureData(ase=_silicon_atoms()),
            targets=List(list=[[5.5]]),
            calculator_parameters=Dict(
                dict={
                    "codes": {"base.abacus.code": code.full_label},
                    **RELAX_CALCULATOR_PARAMETERS,
                }
            ),
        )

        workchain.generate_structures()

        builder = workchain.ctx.builders[0]
        self.assertIs(builder.process_class, AbacusRelaxWorkChain)
        self.assertEqual(builder.base.abacus.code.uuid, code.uuid)
        self.assertEqual([5.5, 5.5, 5.5], builder.structure.cell_lengths)

    def test_scf_generate_structures_accepts_code_pk(self):
        code = _abacus_code()
        workchain = self._instantiate(
            AbacusSCFLatticeProblem,
            structure=StructureData(ase=_silicon_atoms()),
            targets=List(list=[[5.4], [5.6]]),
            calculator_parameters=Dict(
                dict={
                    "codes": {"abacus.code": code.pk},
                    **SCF_CALCULATOR_PARAMETERS,
                }
            ),
        )

        workchain.generate_structures()

        self.assertEqual(len(workchain.ctx.builders), 2)
        self.assertAlmostEqual(workchain.ctx.builders[0].abacus.structure.cell_lengths[0], 5.4)
        self.assertAlmostEqual(workchain.ctx.builders[1].abacus.structure.cell_lengths[0], 5.6)


if __name__ == "__main__":
    unittest.main()
