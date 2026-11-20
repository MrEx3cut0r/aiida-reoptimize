.. _static-workflows:

Static Workflows
================

Static workflows are pre-defined AiiDA WorkChains that are registered as entry points
and can be imported by the AiiDA daemon. They work with both ``run()`` and ``submit()``.

Evaluation WorkChains
---------------------

Five static evaluators are shipped with the package:

.. list-table::
   :widths: 40 40 20
   :header-rows: 1

   * - Class
     - Calculator
     - Entry point
   * - ``CrystalLatticeProblem``
     - ``BaseCrystalWorkChain``
     - ``reoptimize.CrystalLatticeProblem``
   * - ``FleurSCFLatticeProblem``
     - ``FleurScfWorkChain``
     - ``reoptimize.FleurSCFLatticeProblem``
   * - ``FleurRelaxLatticeProblem``
     - ``FleurRelaxWorkChain``
     - ``reoptimize.FleurRelaxLatticeProblem``
   * - ``AbacusSCFLatticeProblem``
     - ``AbacusBaseWorkChain``
     - ``reoptimize.AbacusSCFLatticeProblem``
   * - ``AbacusRelaxLatticeProblem``
     - ``AbacusRelaxWorkChain``
     - ``reoptimize.AbacusRelaxLatticeProblem``

All five inherit from :class:`~aiida_reoptimize.base.Evaluation.StaticEvalLatticeProblem`
and share the same inputs:

- ``structure`` (``StructureData``): the source crystal structure
- ``targets`` (``List``): list of lattice parameter perturbations to evaluate
- ``calculator_parameters`` (``Dict``): inputs forwarded to the calculator workchain
- ``structure_keyword`` (``List``, optional): path to the structure input in the builder

The ``structure_keyword`` default depends on the calculator: top-level
``["structure"]`` for most workchains, but ``["abacus", "structure"]`` for
``AbacusSCFLatticeProblem`` because ``AbacusBaseWorkChain`` exposes its
calculation inputs in the ``abacus`` namespace.

Codes are supplied through the ``codes`` mapping of ``calculator_parameters``
and may use dotted paths to address nested calculator namespaces, e.g.
``{"abacus.code": "abacus@localhost"}`` for ``AbacusSCFLatticeProblem`` or
``{"base.abacus.code": "abacus@localhost"}`` for ``AbacusRelaxLatticeProblem``.

ABACUS-specific notes:

- ``pseudo_family`` selects an ``aiida-pseudo`` family (or ABACUS orbital
  family); the pseudopotentials and, if unspecified, the wavefunction cutoff
  are then resolved automatically by the workchain.
- One of ``kpoints_distance`` or explicit ``kpoints`` is required; for lattice
  optimization ``kpoints_distance`` is usually the right choice.
- The extracted objective is ``misc.total_energy`` (in eV), which both
  ABACUS workchains expose as their ``misc`` output.
- The pseudopotentials are staged in a ``pseudo/`` subfolder of the working
  directory. Verify that this subfolder reaches the machine that actually
  executes the code: some scheduling setups stage task folders without
  subdirectories, in which case ABACUS fails with "Couldn't find
  pseudopotential file". A direct-scheduler computer on the ABACUS host is
  not affected.
- ABACUS binaries are often OpenMP-parallel. Since the evaluator dispatches
  several SCF calculations concurrently, pin the thread count with
  ``metadata.options.environment_variables = {"OMP_NUM_THREADS": "1"}``
  to prevent severe thread oversubscription.

Optimization WorkChains
------------------------

Thirty-five static optimizer workchains are available, combining 7 algorithms with
5 evaluator types:

+--------------+-------------------------------+-------------------------------+
| Algorithm    | CRYSTAL                       | FLEUR SCF                     |
+==============+===============================+===============================+
| Adam         | ``AdamCrystalOptimizer``      | ``AdamFleurSCFOptimizer``     |
+--------------+-------------------------------+-------------------------------+
| CDG          | ``CDGCrystalOptimizer``       | ``CDGFleurSCFOptimizer``      |
+--------------+-------------------------------+-------------------------------+
| RMSprop      | ``RMSpropCrystalOptimizer``   | ``RMSpropFleurSCFOptimizer``  |
+--------------+-------------------------------+-------------------------------+
| BFGS         | ``BFGSCrystalOptimizer``      | ``BFGSFleurSCFOptimizer``     |
+--------------+-------------------------------+-------------------------------+
| PyMOO        | ``PyMOOCrystalOptimizer``     | ``PyMOOFleurSCFOptimizer``    |
+--------------+-------------------------------+-------------------------------+
| G3PCX        | ``G3PCXCrystalOptimizer``     | ``G3PCXFleurSCFOptimizer``    |
+--------------+-------------------------------+-------------------------------+
| NRBO         | ``NRBOCrystalOptimizer``      | ``NRBOFleurSCFOptimizer``     |
+--------------+-------------------------------+-------------------------------+

(The same 7 algorithms are also available for FLEUR relax, e.g.
``AdamFleurRelaxOptimizer``, and for ABACUS SCF and ABACUS relax, e.g.
``AdamAbacusSCFOptimizer`` and ``AdamAbacusRelaxOptimizer``.)

Submitting a Static Optimizer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aiida.engine import submit
   from aiida.orm import Dict, Int, StructureData
   from aiida_reoptimize.workflows import BFGSFleurSCFOptimizer

   result = submit(
       BFGSFleurSCFOptimizer,
       parameters=Dict({
           "algorithm_settings": {...},
           "calculator_parameters": {...},
       }),
       structure=my_structure,
       itmax=Int(50),
   )

Submitting a Static ABACUS Optimizer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aiida.engine import submit
   from aiida.orm import Dict, Int, List, StructureData
   from aiida_reoptimize.workflows import BFGSAbacusSCFOptimizer

   result = submit(
       BFGSAbacusSCFOptimizer,
       structure=StructureData(ase=my_diamond_silicon),
       itmax=Int(50),
       parameters=Dict({
           "algorithm_settings": {"tolerance": 1e-3},
           # Diamond cubic has one free lattice parameter.
           "initial_parameters": List(list=[5.43]),
           "calculator_parameters": {
               # Dotted keys address the `abacus` input namespace.
               "codes": {"abacus.code": "abacus@localhost"},
               "abacus": {
                   "parameters": {"input": {
                       "calculation": "scf",
                       "basis_type": "pw",
                       "scf_thr": 1e-7,
                   }},
                   "metadata": {"options": {
                       "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 2},
                       "environment_variables": {"OMP_NUM_THREADS": "1"},
                       "max_wallclock_seconds": 21600,
                   }},
               },
               "kpoints_distance": 0.15,
               "pseudo_family": "SSSP_1.3_PBE_efficiency",
           },
       }),
   )

For relax-based evaluations use e.g. ``AdamAbacusRelaxOptimizer`` with the
same calculator parameters nested under ``base`` and the code referenced as
``"base.abacus.code"`` (see ``examples/abacus_relax/adam.py``).

Adding Custom Static Workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a custom evaluator and bind optimizers to it:

.. code-block:: python

   from aiida_reoptimize.base.Evaluation import StaticEvalLatticeProblem
   from aiida_reoptimize.workflows.Optimization._common import (
       AdamOptimizer,
       StaticOptimizerBinding,
   )

   class MyLatticeProblem(StaticEvalLatticeProblem):
       calculator_workchain = MyCalculatorWorkChain

   class BaseMyOptimizer(StaticOptimizerBinding):
       evaluator_workchain = MyLatticeProblem
       extractor_path = ("output_parameters", "energy")

   class AdamMyOptimizer(BaseMyOptimizer, AdamOptimizer):
       pass

Then register the entry points in ``pyproject.toml``:

.. code-block:: toml

   [project.entry-points."aiida.workflows"]
   "reoptimize.MyLatticeProblem" = "my_module:MyLatticeProblem"
   "reoptimize.AdamMyOptimizer" = "my_module:AdamMyOptimizer"
