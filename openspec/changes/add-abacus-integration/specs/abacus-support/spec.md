### Requirement: ABACUS static evaluators
The package SHALL provide static evaluator workchains `AbacusSCFLatticeProblem` (bound to `AbacusBaseWorkChain`) and `AbacusRelaxLatticeProblem` (bound to `AbacusRelaxWorkChain`) that inherit from `StaticEvalLatticeProblem`, are registered as `aiida.workflows` entry points, and inject the generated structure into the calculator builder at the code-specific structure path.

#### Scenario: SCF evaluator injects structure into the abacus namespace
- **WHEN** `AbacusSCFLatticeProblem` is submitted with a `structure`, `targets`, and `calculator_parameters` containing `codes = {"abacus.code": "abacus@<host>"}`
- **THEN** each generated structure is placed at `abacus.structure` of the `AbacusBaseWorkChain` builder and the code is placed at `abacus.code`

#### Scenario: Relax evaluator injects structure at the top level
- **WHEN** `AbacusRelaxLatticeProblem` is submitted with `codes = {"base.abacus.code": "abacus@<host>"}`
- **THEN** the generated structure is placed at the top-level `structure` port of the `AbacusRelaxWorkChain` builder and the code is placed at `base.abacus.code`

### Requirement: ABACUS static optimizers
The package SHALL provide for each of the seven shipped algorithms (Adam, CDG, RMSprop, BFGS, PyMOO, G3PCX, NRBO) a static optimizer workchain for ABACUS SCF and one for ABACUS relax, all registered as `aiida.workflows` entry points and reading the objective value from `("misc", "total_energy")`.

#### Scenario: Optimizer reads the total energy
- **WHEN** an ABACUS evaluation finishes successfully
- **THEN** the bound extractor returns `outputs["misc"]["total_energy"]` (total energy in eV) as the objective value

#### Scenario: Failed evaluations are penalized
- **WHEN** an ABACUS calculation fails or the `misc` output is missing
- **THEN** the extractor returns the configured penalty value instead

### Requirement: Nested calculator parameters
`StructureCalculator` SHALL set dictionary-valued calculator parameters that target an AiiDA input namespace key by key instead of replacing the whole namespace, and SHALL raise `StructureGenerationError` when the builder rejects a parameter.

#### Scenario: Partial namespace parameters are accepted
- **WHEN** calculator parameters contain `{"abacus": {"parameters": {...}}}` without the required `structure` sub-port
- **THEN** the builder accepts each sub-key individually and the structure is injected afterwards without port validation errors

#### Scenario: Unknown parameter is reported as a structure generation failure
- **WHEN** calculator parameters contain a key that is not a port of the calculator builder
- **THEN** `StructureCalculator.get_builder` raises `StructureGenerationError` naming the rejected key

### Requirement: Dotted code references
The `codes` mapping of `calculator_parameters` SHALL accept dotted paths that address nested calculator namespaces, while flat keys keep placing codes at the top level.

#### Scenario: Nested code reference
- **WHEN** `calculator_parameters` contains `codes = {"abacus.code": "abacus@localhost"}`
- **THEN** the loaded `Code` node ends up at `calculator_parameters["abacus"]["code"]` before the builder is assembled

#### Scenario: Flat code reference stays unchanged
- **WHEN** `calculator_parameters` contains `codes = {"fleur": "fleur@host"}`
- **THEN** the loaded `Code` node ends up at the top level of the calculator parameters, as before

### Requirement: ABACUS examples and documentation
The package SHALL ship runnable examples for ABACUS SCF (Adam, CDG) and ABACUS relax (Adam via `OptimizerBuilder`), and its documentation SHALL list the ABACUS evaluators, optimizers, entry points, code referencing conventions, and the `misc.total_energy` objective.

#### Scenario: User submits a static ABACUS optimization
- **WHEN** a user follows the static-workflows documentation or an ABACUS example
- **THEN** they can submit e.g. `BFGSAbacusSCFOptimizer` via `submit()` with a code referenced as `"abacus.code"` and obtain lattice parameters minimizing the total energy
