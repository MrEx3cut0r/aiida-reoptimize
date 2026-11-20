## Context

aiida-reoptimize wraps "calculator workchains" (a code-specific AiiDA workchain that takes a structure and calculation parameters) behind two generic mechanisms:

1. `StructureCalculator` (dynamic/static structure path): builds a calculator builder per candidate lattice, injecting the generated `StructureData` at a configurable `structure_keyword` path and setting all `calculator_parameters` on the builder.
2. `StaticEvalLatticeProblem` subclasses (static path): resolve codes and optional basis families from a `Dict` input, then reuse mechanism 1.

CRYSTAL and FLEUR calculators keep codes and the structure at the top level of their builders. ABACUS (`aiida-abacus`) differs: `AbacusBaseWorkChain` exposes its calculation inputs in the `abacus` namespace (`abacus.code`, `abacus.parameters`, `abacus.structure`), and `AbacusRelaxWorkChain` nests them under `base` (`base.abacus.code`, top-level `structure`). Both expose the total energy in the `misc` output Dict (`misc.total_energy`, in eV).

## Goals / Non-Goals

**Goals:**

- Static ABACUS evaluators and optimizers with the same shape and behavior as the FLEUR ones
- `submit()`-ready entry points so ABACUS optimizations can run under the AiiDA daemon
- The two generic mechanisms above stay code-agnostic and backward compatible for CRYSTAL and FLEUR

**Non-Goals:**

- Protocol/builder generation via `aiida-abacus` `get_builder_from_protocol` (users specify `abacus.parameters` directly; pseudo families are resolved by the workchain itself)
- Magnetic-structure support for ABACUS (the generic magnetic-moment injection currently emits FLEUR-specific `calc_parameters`; ABACUS magnetic structures therefore raise `MagneticMomentPreservationError` and exit code 492, which is reported but not wired to ABACUS STRU keywords)
- Relaxing via the `relax_settings` port in `calculator_parameters` (its pydantic `Enum` field is not JSON-serializable in `aiida-abacus` 0.3.x; relaxation settings go through `base.abacus.parameters.input` instead)

## Decisions

### D1: Structure keyword defaults per evaluator

**Choice**: `AbacusSCFLatticeProblem` overrides the `structure_keyword` port default to `["abacus", "structure"]`; `AbacusRelaxLatticeProblem` keeps the generic default `["structure"]`.

**Rationale**: The evaluator knows its calculator, so users must not remember code-specific paths. Overriding the default (same pattern as `FixedPyMOOAlgorithmMixin` pinning `algorithm_name`) keeps the input optional and overridable.

### D2: Per-key assignment of namespace parameters

**Choice**: `StructureCalculator` sets dict-valued parameters on AiiDA input namespaces key by key (`_set_builder_input` recursion) instead of replacing the whole namespace.

**Rationale**: Whole-namespace assignment validates the partial dict against all required sub-ports and fails before the generated structure is injected, and it discards previously set namespace content. Per-key assignment validates each port individually, keeps the final structure injection working, and leaves non-namespace dict values (e.g. FLEUR `options`) unchanged. Failures are wrapped in `StructureGenerationError` so static evaluators exit with `ERROR_STRUCTURE_GENERATION_FAILED` instead of crashing.

### D3: Dotted code paths

**Choice**: `codes` keys may be dotted paths (e.g. `"abacus.code"`); `prepare_calculator_parameters` places the loaded node at that nested location via `_place_loaded_code`.

**Rationale**: `calculator_parameters` is an AiiDA `Dict`, so it cannot contain `Code` nodes; the `codes` mechanism is the only loader. Dotted keys generalize it to nested calculators. Keys without a dot keep the previous top-level behavior.

### D4: Extractor path `("misc", "total_energy")`

**Choice**: Both ABACUS optimizers read `outputs["misc"]["total_energy"]`.

**Rationale**: `AbacusBaseWorkChain` exposes the calculation outputs (`misc` Dict); `AbacusRelaxWorkChain` re-exposes them minus `structure`. `total_energy` is the final SCF total energy in eV for both `scf` and `cell-relax` runs.

### D5: Dependency pin `aiida-abacus>=0.3.1,<0.4`

**Choice**: PyPI 0.3.1 already contains `AbacusBaseWorkChain` with the `abacus` namespace, `AbacusRelaxWorkChain`, and `misc.total_energy`; 0.4 may break APIs (plugin is alpha-status), so an upper bound is pinned.

**Rationale**: Verified against the v0.3.1 tag of the upstream repository; the full test suite was additionally executed against a PyPI-installed `aiida-abacus==0.3.1` (46/46 passing), so the lock floor is exercised, not only inspected.

## Risks / Trade-offs

- [Namespace assignment change] → `get_builder` behavior for CRYSTAL/FLEUR is unchanged for flat keys; nested dict values previously replaced namespaces wholesale, which only "worked" when the dict was complete. Covered by new and existing tests.
- [Magnetic ABACUS structures unsupported] → The generic magmom injection is FLEUR-specific; users with magnetic structures get a clear reported exit code (492) instead of silent wrong results. Proper ABACUS STRU magmom wiring can be added later in `aiida-abacus`-specific code.
- [Upstream `relax_settings` serialization bug] → Documented; relaxation is configured through `base.abacus.parameters.input` which is fully serializable.
- [Upstream releases] → `aiida-abacus` is alpha-status; the `<0.4` bound contains the blast radius of breaking changes.
- [Scheduler staging of the pseudo subfolder] → `AbacusCalculation` stages pseudopotentials in `./pseudo/`; scheduling setups that copy task folders without subdirectories (observed with a yascheduler deployment) make ABACUS fail with "Couldn't find pseudopotential file". Documented as a deployment caveat; use a direct-scheduler computer on the ABACUS host in that case.
- [OpenMP oversubscription] → concurrent evaluations run several ABACUS jobs at once; with OpenMP-enabled binaries the default thread counts multiply. `OMP_NUM_THREADS=1` via `metadata.options.environment_variables` is now set in all ABACUS examples and documented.

## Validation

The integration was validated against a real ABACUS v3.10.1 binary (direct scheduler, 2 MPI processes per calculation, the `Si.upf` pseudopotential shipped in the aiida-abacus test fixtures, 14x14x14 k-mesh from `kpoints_distance=0.15`, 2-atom primitive diamond cell):

1. `AbacusSCFLatticeProblem` evaluated a single target: `AbacusBaseWorkChain` finished with exit 0 and `misc.total_energy = -230.2749 eV`.
2. `AdamAbacusSCFOptimizer` (`itmax=8`, tolerance `5e-2`) ran the full loop over 8 real SCF evaluations and **converged after 4 iterations**, optimizing the lattice constant to `a = 5.4779 Angstrom` at `E = -230.2802 eV` — the expected PBE equilibrium for silicon (experiment: 5.431 Angstrom), with outputs `optimized_parameters`, `final_value`, `history`, and `result_node_pk` attached.

The relax evaluator (`AbacusRelaxLatticeProblem`) was validated at the builder/process-instantiation level (see `tests/test_abacus_integration.py`); no real `AbacusRelaxWorkChain` run was executed.
