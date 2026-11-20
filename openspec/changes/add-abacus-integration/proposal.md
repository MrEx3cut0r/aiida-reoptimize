## Why

aiida-reoptimize currently ships static evaluators and optimizers for CRYSTAL and FLEUR only. ABACUS (via the `aiida-abacus` plugin) is a third widely used DFT engine whose `AbacusBaseWorkChain` and `AbacusRelaxWorkChain` are ready-made calculator workchains. Supporting ABACUS requires no changes to the optimizer algorithms — only code-specific evaluators, optimizer bindings, and two generic mechanism fixes (nested builder namespaces and nested code references).

## What Changes

- Add `AbacusSCFLatticeProblem` and `AbacusRelaxLatticeProblem` static evaluators
- Add 14 static ABACUS optimizer workchains (7 algorithms x 2 evaluators) registered as entry points
- Make `StructureCalculator` assign nested calculator parameters key by key when they target an AiiDA input namespace (required because ABACUS calculation inputs live in the `abacus` / `base.abacus` namespaces and partial whole-namespace assignment fails port validation)
- Allow dotted paths in the `codes` mapping of `calculator_parameters` so codes can be referenced inside nested namespaces (`"abacus.code"`, `"base.abacus.code"`)
- Add `aiida-abacus>=0.3.1,<0.4` as a dependency and register the new entry points
- Add ABACUS examples and update README/docs accordingly

## Capabilities

### New Capabilities

- `abacus-support`: static evaluators and optimizers for ABACUS SCF and relax lattice problems

### Modified Capabilities

## Impact

- New module `aiida_reoptimize/workflows/Evaluation/abacus_evaluation.py` and `aiida_reoptimize/workflows/Optimization/Abacus.py`
- `aiida_reoptimize/structure/dynamic_structure.py`: `StructureCalculator.get_builder` now routes parameter assignment through `_set_builder_input`; dict values on AiiDA input namespaces are set per key, and failures raise `StructureGenerationError` (previously raw `AttributeError`/`ValueError` escaped). Flat parameters are unaffected.
- `aiida_reoptimize/base/Evaluation.py`: `prepare_calculator_parameters` places loaded codes at dotted paths; flat code keys behave exactly as before.
- `pyproject.toml`: new dependency and 16 new entry points (2 evaluators + 14 optimizers)
- New tests in `tests/test_abacus_integration.py`
- Existing CRYSTAL and FLEUR workflows are unaffected (flat parameter/code keys keep their behavior; existing tests pass unchanged)
