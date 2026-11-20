## 1. Generic mechanism fixes

- [x] 1.1 `StructureCalculator`: assign dict-valued calculator parameters key by key when they target an AiiDA input namespace, wrapping failures in `StructureGenerationError`
- [x] 1.2 `_StaticEvalStructureBase`: support dotted paths in the `codes` mapping (`_place_loaded_code`), keeping flat keys at the top level

## 2. ABACUS evaluators

- [x] 2.1 Create `aiida_reoptimize/workflows/Evaluation/abacus_evaluation.py` with `AbacusSCFLatticeProblem` (structure keyword default `["abacus", "structure"]`)
- [x] 2.2 Add `AbacusRelaxLatticeProblem` (structure keyword default `["structure"]`)
- [x] 2.3 Export both from `aiida_reoptimize/workflows/Evaluation/__init__.py`

## 3. ABACUS optimizers

- [x] 3.1 Create `aiida_reoptimize/workflows/Optimization/Abacus.py` with `BaseAbacusSCFOptimizer` and `BaseAbacusRelaxOptimizer` bound to extractor path `("misc", "total_energy")`
- [x] 3.2 Add Adam/CDG/RMSprop/BFGS/PyMOO/G3PCX/NRBO variants for both evaluators (14 workchains)
- [x] 3.3 Export all from `aiida_reoptimize/workflows/Optimization/__init__.py` and `aiida_reoptimize/workflows/__init__.py`

## 4. Packaging

- [x] 4.1 Add `aiida-abacus>=0.3.1,<0.4` dependency and `abacus` keyword to `pyproject.toml`
- [x] 4.2 Register 16 entry points (2 evaluators + 14 optimizers) and verify they resolve via `WorkflowFactory`

## 5. Tests

- [x] 5.1 `tests/test_abacus_integration.py`: evaluator bindings, structure-keyword defaults, extractor-path validity, optimizer bindings
- [x] 5.2 Builder generation through `StructureCalculator` for both ABACUS workchains (nested parameters, structure injection, scalar serialization, unknown-key error)
- [x] 5.3 `_place_loaded_code` unit tests and end-to-end `generate_structures` tests with dotted `codes` (label and PK forms)
- [x] 5.4 Full suite and ruff pass

## 6. Documentation and examples

- [x] 6.1 Add `examples/workflows/adam_abacus_test.py` and `examples/workflows/CDG_abacus_test.py`
- [x] 6.2 Add `examples/abacus_relax/adam.py` (dynamic `OptimizerBuilder` path)
- [x] 6.3 Update `docs/source/static-workflows.rst` (evaluator/optimizer tables, ABACUS notes, submit example)
- [x] 6.4 Update `docs/source/api/workflows.rst` and `docs/source/examples.rst`
- [x] 6.5 Update `README.md` (supported engines, workchain lists, structure-keyword note)
- [x] 6.6 Add openspec change documents (proposal, design, spec delta)

## 7. Review follow-ups

- [x] 7.1 Regenerate `uv.lock` after adding the `aiida-abacus` dependency (`uv lock`; adds aiida-abacus 0.3.1 and its dependency chain only, no version churn)
- [x] 7.2 Add `tearDown` cleanup to `TestAbacusEvaluatorWorkchain` so `instantiate_process`-created WorkChainNodes no longer accumulate in the profile
- [x] 7.3 Replace `find_nodes` with `load_code("abacus")` in `examples/abacus_relax/adam.py` to avoid the Fleur-specific error message
- [x] 7.4 Document the scheduler-staging caveat for the `pseudo/` subfolder in `docs/source/static-workflows.rst` and in the design risks
- [x] 7.5 Validate against a real ABACUS calculation: SCF evaluation via `AbacusSCFLatticeProblem` and a lattice optimization via `AdamAbacusSCFOptimizer` with the ABACUS v3.10.1 binary, confirming `misc.total_energy` is parsed and optimized end to end
