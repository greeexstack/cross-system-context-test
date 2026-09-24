# Cross-System Context Test

A controlled experiment for testing whether relevant context from a secondary business data source can improve decisions made from a primary-system record.

## What this project tests

The project tests whether a reasoning system can:

- use relevant secondary context when it is informative;
- reject irrelevant or incorrectly attributed context;
- preserve identity integrity;
- respect temporal boundaries and stale information;
- distinguish unavailable data from available data with no evidence;
- handle ambiguous identity matches conservatively;
- change, strengthen, weaken, or preserve an interpretation according to controlled evidence.

The experiment does not claim that secondary-data existence proves causality or root cause.

## Current public experiment

The public CLI runs the frozen v0.2 controlled experiment.

The fixture package contains 20 controlled cases:

- 10 development cases;
- 10 evaluation cases;
- two cases for each F01-F10 family;
- frozen ground-truth assertions;
- deterministic fixture invariants.

Current frozen result:

```text
20/20 cases PASS
```

This result is evidence about the supplied controlled fixtures. It is not a claim of general semantic understanding, production accuracy, or universal cross-system reasoning ability.

## Installation

Python 3.12 or newer is required.

From the repository root:

```powershell
python -m pip install -e ".[dev]"
```

## CLI

Validate the frozen fixture package:

```powershell
cross-system-context validate
```

Run the frozen v0.2 experiment:

```powershell
cross-system-context run
```

Equivalent module invocation:

```powershell
python -m experiment.cli validate
python -m experiment.cli run
```

A failed validation or experiment returns a non-zero process exit status.

## Expected results

Validation:

```text
Invariant groups: PASS
VALIDATION PASS
```

Experiment:

```text
Passed cases: 20/20
Result: PASS
```

## What is frozen

The v0.2 fixture package is research evidence.

Its controlled dimensions include context sensitivity, context resistance, direction correctness, evidence validity, identity integrity, temporal integrity, ambiguity handling, missing-data handling, and generalization within the frozen fixture design.

Changes to frozen v0.2 evidence require an explicit research decision.

## Research methodology

The project follows:

1. research;
2. explicit hypothesis;
3. controlled fixture;
4. machine-checkable invariant;
5. implementation;
6. evaluation;
7. independent validation where applicable;
8. preserved evidence and limitations.

Existing systems and benchmarks may be used for research and comparison. They are not assumed to be components of this project.

## Experimental work

The repository also contains v0.3 research work involving semantic extraction and cross-workflow context handling.

That work is not exposed through the public CLI.

The v0.3 independent replication did not support the preregistered H5 improvement hypothesis. Those results remain research evidence and are not represented as a production capability.

## Scope and limitations

This is a controlled research and evaluation tool.

It does not currently claim production integration with external business systems, general-purpose natural-language understanding, broad paraphrase robustness, universal identity resolution, causal or root-cause inference, production decision automation, or validated performance across arbitrary real-world datasets.

## Development

CLI smoke tests:

```powershell
python -m pytest -q tests\test_cli.py --basetemp=.pytest-tmp
```

Clean the temporary directory afterward:

```powershell
Remove-Item -Recurse -Force ".pytest-tmp" -ErrorAction SilentlyContinue
```

## Versions

Package version:

```text
0.1.1
```

Public experiment:

```text
v0.2
```

These are intentionally separate version concepts.
