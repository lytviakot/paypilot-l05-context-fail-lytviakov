# L05 · Multi-turn Test Plan — PayPilot

Homework 4: where a dialog with the PayPilot agent falls apart, how to catch it automatically, and which dialogs to cover. The document is `multi-turn-test-plan.md`, the dialog cases are in `l05_dialogs.jsonl`.

## Run

Put `l05_dialogs.jsonl` into `sets/` of the course kit and run:

    docker compose run --rm eval --set l05_dialogs --profile clean
    docker compose run --rm eval --set l05_dialogs --profile lesson-05

`set_hash`: `546d67fb0eb3`

Agent model: `claude-haiku-5-5`. Stand profile and the summary threshold (2 steps) are set by the runner from each case.

## Dialog cases

| id | Role in the plan | Length · entities · switches | Invariants |
| --- | --- | --- | --- |
| CONV-H01 | контроль | 5 · 2 · 1 | dispute amount (level 2), filing deadline (level 3); summary threshold 8, so no summary is made |
| CONV-H02 | основний | 7 · 2 · 1 | dispute amount (level 2), filing deadline (level 3); equals complaint C-07 |
| CONV-H03 | найгірший | 10 · 3 · 2 | dispute amount (level 2), reason code (level 3), filing deadline (level 3) |
| CONV-H04 | ізоляція осі | 4 · 1 · 0 | dispute amount (level 2) |
| CONV-H05 | ізоляція осі | 7 · 3 · 0 | dispute amount (level 2), reason code (level 3), filing deadline (level 3) |

The role names are in Ukrainian because the course loader accepts only these values.

## Prediction

Written before the run on `lesson-05` (before any final run of this set). Basis: the lab runs, where the summary always fired at step 3 and dropped the case values, and where the agent listed both 240 EUR charges (TX-0401 and TX-0402) after the loss.

- `CONV-H01` stays green: the threshold is above the dialog length, no summary is made.
- `CONV-H02` fails at step 7: the agent lists both charges and names the 12 October deadline.
- `CONV-H03` fails at step 8 (reason code) or step 10 (deadline).
- `CONV-H04` most likely stays green: the agent re-reads the transactions and both are 240 EUR, so the amount check passes. If it fails, it fails at step 4.
- `CONV-H05` fails at step 5 (reason code) or step 7 (deadline).

Commit with the prediction: to fill in after the commit.

## Runs

| Run | Profile | Result | Report |
| --- | --- | --- | --- |
| Baseline | `clean` | to fill | to fill |
| Lesson profile | `lesson-05` | to fill | to fill |

What failed: to fill. Difference from the prediction: to fill.
