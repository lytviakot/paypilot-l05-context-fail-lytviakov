# L05 · Multi-turn Test Plan — PayPilot

Homework 4: where a dialog with the PayPilot agent falls apart, how to catch it automatically, and which dialogs to cover.

- `multi-turn-test-plan.md`: the Multi-turn Test Plan + Degradation Profile (six sections and the last line)
- `l05_dialogs.jsonl`: five dialog cases, `layer: memory`
- `reports/`: raw reports of the runs (and the traces they were read from)
- `generate_dialogs.py`: writes `l05_dialogs.jsonl`
- `analyze_traces.py`, `analyze_length.py`: read the traces and print the loss step, the entities in the history and the invented values used in the document
- `sets/l05.jsonl`, `sets/l05_len.jsonl`: the lab sets (the course demo set and the 5-step and 10-step versions of C-07)

## Run

Put `l05_dialogs.jsonl` into `sets/` of the course kit (`paypilot-l05-eval`, next to a running PayPilot stand) and run:

    docker compose run --rm eval --set l05_dialogs --profile clean
    docker compose run --rm eval --set l05_dialogs --profile lesson-05

`set_hash`: `546d67fb0eb3`

Agent model: `claude-haiku-5-5`. The summary threshold is set by the runner from each case (2 steps; 8 in the control case CONV-H01).

## Dialog cases

| id | Role in the plan | Length · entities · switches | Invariants |
| --- | --- | --- | --- |
| CONV-H01 | контроль (control) | 5 · 2 · 1 | dispute amount (level 2), filing deadline (level 3); threshold 8, so no summary is made |
| CONV-H02 | основний (main) | 7 · 2 · 1 | dispute amount (level 2), filing deadline (level 3); equals complaint C-07 |
| CONV-H03 | найгірший (worst case) | 10 · 3 · 2 | dispute amount (level 2), reason code (level 3), filing deadline (level 3) |
| CONV-H04 | ізоляція осі (isolates length) | 4 · 1 · 0 | dispute amount (level 2) |
| CONV-H05 | ізоляція осі (isolates entities) | 7 · 3 · 0 | dispute amount (level 2), reason code (level 3), filing deadline (level 3) |

The role names in the file are in Ukrainian because the course loader accepts only these values.

## Runs

Each case is run 5 times (`runs: 5`). The result is given as cases passed (a case passes when all 5 of its runs are green) and runs passed.

| Run | Profile | Result | Report |
| --- | --- | --- | --- |
| Baseline | `clean` | 4/5 cases, 24/25 runs | `reports/l05_dialogs-clean-20261108T123855.json` |
| Lesson profile | `lesson-05` | 2/5 cases, 12/25 runs | `reports/l05_dialogs-lesson-05-20261108T124809.json` |

Prediction before the run on `lesson-05`:

- `CONV-H01` stays green: the threshold is above the dialog length, no summary is made.
- `CONV-H02` fails at step 7: the agent lists both charges and names the 12 October deadline.
- `CONV-H03` fails at step 8 (reason code) or step 10 (deadline).
- `CONV-H04` most likely stays green: the agent re-reads the transactions and both are 240 EUR, so the amount check passes. If it fails, it fails at step 4.
- `CONV-H05` fails at step 5 (reason code) or step 7 (deadline).

Commit with the prediction: `737a5dd`

What failed on `lesson-05`: `CONV-H02` (5 of 5 runs, step 7), `CONV-H03` (4 of 5 runs, step 10; run 2 also at step 8), `CONV-H05` (4 of 5 runs, step 5 in three of them, step 7 in four).

Difference from the prediction: none in direction. `CONV-H01` and `CONV-H04` stayed green, the other three failed at the predicted steps. Two details differ from a clean "fails": `CONV-H03` and `CONV-H05` each have one green run out of five (the defect is probabilistic), and `CONV-H04` is green although in 4 of 5 runs the agent answers "I can't tell which transaction", so a green check does not mean the case was kept (section 6.2 of the document). On `clean` one run of `CONV-H03` is red because the check forbids any other reason code and the agent named one as an option (a false alarm of the check, section 4.2).

Run cost: USD 0.15 (`clean`) and USD 0.18 (`lesson-05`), 165 steps each, 553 s and 668 s.
