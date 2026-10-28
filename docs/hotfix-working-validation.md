# Working validation and reproducible experiments

## Problem

The LP implementation used APIs incompatible with the declared PuLP 4.0.0
dependency. Its failures could silently trigger KK in the orchestrator. Benchmark
validation checked preserved numbers but not the requested group count, and
benchmark exceptions were printed without a failing process exit status.

## Changes

- Create binary assignment variables and sum bounds using the PuLP 4 problem API.
- Read solver results through `has_solution` and `LpSolveStatus`. Accept feasible
  solutions after a time limit without presenting them as proven optimal.
- Verify integral, exactly-once assignments before returning a partition.
- Validate positive group counts and non-negative inputs in LP and KK; return
  empty groups for empty input. Reject a negative singleton in the orchestrator.
- Require exactly `k` groups and preserve every original value, including duplicates.
- Reject dataset files whose declared count does not match their contents.
- Propagate benchmark failures instead of silently excluding failed algorithms.
- Record the orchestrator strategy, LP attempt/status, model scope and fallback
  reason. An optimum for the large-number subproblem is not a global guarantee.
- Add configurable repetitions (CLI default: three), CV threshold and solver limit.
- Export one CSV row per dataset/algorithm/repetition, including normalized
  quality metrics, timing, parameters, dependency versions and input SHA-256.
- Seed input generation (default: zero); use a single solver thread and solver
  seed zero. Generation failures now propagate to the caller.
- Ignore all `*.csv` files and all directories named `results` in Git.
- Add standard-library regression tests and Windows/Linux GitHub Actions using
  the existing `uv.lock`.

## Behavior and compatibility

The MILP objective (maximum minus minimum group sum), binary assignment model,
KK/GNP strategy and default CV threshold of 0.6 are unchanged. LP now actually
runs where it previously failed, so orchestrator results can change. The default
solver limit remains one second. The two-argument algorithm calls still return
lists of groups; optional metadata is collected separately.

`validate_partitions` now requires `k`. Invalid benchmark inputs and algorithm
failures now raise exceptions and produce an unsuccessful CLI exit. CSV output
overwrites its selected destination only after all requested runs succeed.

`--generate --seed 42` replaces the standard example datasets, including the
million-element files. The seed does not regenerate data during benchmarking.
Time limits and measurements can vary across machines even with fixed seeds.

## Verification

```powershell
python -m unittest discover -s tests -v
python src/main.py --algorithm all -k 4 --repeats 2
git diff --check
```

The 14 test methods cover known optima, exhaustive enumeration of small
assignments, integrity and invalid inputs, feasible time-limit status, LP
fallback, seeded exports and CLI-to-CSV integration. CI is configured for Windows
and Linux; its remote results must be checked after pushing.

## Follow-up work

Benchmark and calibrate algorithm-selection thresholds on representative data.
The default example data does not exercise LP selection in the orchestrator;
regression tests include an input that does. CSV exports currently abort with the
experiment on error rather than preserving partial results. Runtime versions and
input checksums are recorded, but elapsed times are not fully reproducible.
