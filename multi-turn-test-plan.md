# Multi-turn Test Plan + Degradation Profile

Scenario C-07 (CUS-0004): the agent loses the dispute amount between two messages, and nobody sees it in any single answer.

Sections 1 to 4.1 are filled from the lab. Sections 3.4, 4.2, 5, 6 and the last line are for the homework.

## 1. Context and prediction

```
system             PayPilot (local stand, localhost:8000)
profiles           clean, lesson-05 (D06, D07)
agent model        claude-haiku-5-5 (Anthropic)
main scenario      C-07, 7 steps, customer CUS-0004
summarize after    2 steps (set with PUT /api/_test/summarize_after)
set                sets/l05.jsonl, 4 cases, set_hash 947ef71be283
length cases       sets/l05_len.jsonl, 2 cases, set_hash 93a0b5eae73d
clock              2026-09-15T10:00:00Z (fixed)
run date           2026-11-08
```

**Prediction before the lab:** the dispute amount (240 EUR) will disappear from the history at step 3 (loss step), and the loss will become visible in the agent reply at step 5 (manifestation step). Reason: the history is summarized after the first few steps, so the summary replaces the opening message before the agent needs the amount again at step 5. (Written before any run. Revised once from "loss at step 5" after thinking about the difference between loss and manifestation; the first version is in the git history. Compared with the measured distribution in 2.3.)

**Facts about this stand that differ from the lesson text:**
- The filing window for `goods_not_received` is **90 days**, not 120. The deadline for TX-0401 is 2026-10-18. I use the measured numbers.
- CUS-0004 has **two** charges of 240.00 EUR to the same merchant: TX-0401 (20 July) and TX-0402 (14 July). Once the case details are lost, the amount alone does not tell them apart.

How the data was collected: the course runner (`--traces`, `--repeat 5`) played the 7 client messages in a fresh conversation each time and saved the full trace of every step. History and retrieval context were read from the traces, not from the answer text. The tables below are computed from those traces by `analyze_traces.py`.

---

## 2. Degradation profile

### 2.1. Record sheet: control run on `clean`

Profile `clean`, customer CUS-0004, new conversation, 1 run (report `l05-clean-20261108T114806.json`).

Entities: A = amount 240.00, D = date 20 July, C = reason code, W = window 90 days, T = TX-0401. "In history" means what the model can see at that step, including the current client message.

| Step | Client message (short) | Agent reply (short) | Entities in history | Retrieval context |
| --- | --- | --- | --- | --- |
| 1 | I'm CUS-0004, TX-0401, 240.00 EUR, goods never arrived, which code? | goods_not_received, TX-0401 EUR 240.00 | A T (current message) | none (no search) |
| 2 | Can I dispute it? | Yes, eligible, goods_not_received | A C T | none (eligibility tool) |
| 3 | daily card limit | EUR 5,000.00. **History summarized here** | A D C W T (all kept in the summary) | none |
| 4 | FX spread in USD | Tier 1 spread 1.5% | A D C W T | `fees-detail.md#s2`, `tariffs.md#s3`, `tariffs.md#s2`, `fx-guide.md#s1` |
| 5 | Back to that charge, what next? | asks for explicit go-ahead, shows TX-0401, EUR 240 | A D C W T | none |
| 6 | 240 euro, as I said | opens the dispute, ID 1 | A D C W T | none |
| 7 | still have time to file? | dispute 1 already open, deadline 2026-10-18 | A D C W T | none |

On `clean` the summary written at step 3 keeps the amount, date, code, window and TX id. Check set result: 4/4.

### 2.2. Record sheet: run on `lesson-05`

Profile `lesson-05`, same customer, this is run 1 of the 5 in 2.3 (report `l05-lesson-05-20261108T115229.json`).

| Step | Agent reply (short) | Entities in history | Retrieval context | Visible in the answer that something is lost? |
| --- | --- | --- | --- | --- |
| 1 | goods_not_received | A T (current message) | none | no |
| 2 | eligible, goods_not_received, window to 18 Oct | A C T | none | no |
| 3 | EUR 5,000. **History summarized** | none (summary: "goods never arrived, code identified, not opened yet") | none | no |
| 4 | spread 1.5% | none | `tariffs.md#s2`, `fx-guide.md#s1`, `fees-detail.md#s2`, `tariffs.md#s3` | no |
| 5 | lists two EUR 240.00 charges (TX-0402, TX-0401) | none (re-fetched with `get_transactions`) | none | **yes**: agent cannot say which charge |
| 6 | "the amount matches both charges, which one is the problem?" | A D C T (back after the tool result and the client message) | none | yes |
| 7 | "deadline depends on the reason code": goods_not_received 90 days, duplicate_charge 60 days | A D C T | `disputes.md#s1`, `disputes-process.md#s6`, `disputes-process.md#s1`, `disputes.md#s2` | no, it sounds competent |

The summary at step 3 replaced 6 to 12 messages and kept none of the four case values.

### 2.3. Loss step over five runs

Profile `lesson-05`, each run in a new conversation, 35 agent calls.

| Run | Loss step (summary has no case values) | Manifestation step (agent cannot name the charge) | First failing check of the case |
| --- | --- | --- | --- |
| 1 | 3 | 5 | step 7 |
| 2 | 3 | 5 | none |
| 3 | 3 | 5 | none |
| 4 | 3 | 5 | step 4 |
| 5 | 3 | 5 | none |

**Sorted loss steps:** 3, 3, 3, 3, 3
**Range:** 3 to 3, **median:** 3
**Length limit after which we do not trust the agent's memory:** from step 3 on. With the threshold at 2 steps, steps 1 and 2 are safe and every dialog of three or more steps loses the case details.
**Did the prediction match?** Yes, both numbers: loss at step 3, manifestation at step 5.

The loss step did not move between runs here. Lesson text says it should move. With the threshold fixed at 2 steps the summary always fires at step 3, so the loss step is a property of the threshold. What varied between runs is what the agent does afterwards (the last column).

Note on the check: the automatic check at step 5 ("answer mentions TX-0401 or 240") was green in all 5 runs, because the answer lists both charges. The step where the loss shows is not caught by the check of that step.

One earlier single run of the full set on `lesson-05` gave 4/4 green. One run does not show the defect.

### 2.4. Degradation profile of the main scenario

Same in all 5 runs unless a number is given.

| Step | What holds | What is lost | What was in the step input | Mechanism | Visible in the answer |
| --- | --- | --- | --- | --- | --- |
| 1 | amount, TX id, intent | none | verbatim message | none | no |
| 2 | amount, code, TX id, window | none | verbatim history | none | no |
| 3 | intent ("goods never arrived") | **amount, date, code, window, TX id** | summary only | summarize after 2 steps, D06 | no (limit answer is correct) |
| 4 | intent | nothing more | summary + step 3 | none | no (spread 1.5% correct; run 4 asked for an amount first) |
| 5 | intent | agent has to re-fetch the data | summary + step 4, no retrieval call | consequence of step 3 | **yes** in 5/5: two charges listed, cannot choose |
| 6 | amount (client repeated it), both charges from the tool | which one is the disputed charge | summary + tool result + client message | consequence of step 3 | yes in 5/5: asks which charge |
| 7 | amount, window via tool or search | the code, in some runs | summary + tool result + 2 steps | consequence of step 3 | no: answers sound normal; see 3.2 |

**Loss moment:** step 3. **Manifestation moment:** step 5.
**Steps with "visible in the answer: no":** 1, 2, 3, 4 and 7 (step 7 sounds fine, it only hedges between two charges). Steps 3 and 4 are the first ones, and they carry the loss.

### 2.5. Length axis: shorter and longer scenario

Two extra cases in `sets/l05_len.jsonl` (set_hash `93a0b5eae73d`): `CONV-002-S5` is the first 5 steps of C-07, `CONV-002-L10` is C-07 plus three steps (a question about the international transfer fee, then "back to the dispute, which transaction?", then "amount and deadline for it"). Each was run 5 times on `lesson-05` and once on `clean` (report `l05_len-lesson-05-20261108T121142.json`, `l05_len-clean-20261108T121049.json`).

| Scenario version | Profile | Amount lost? At which step | What else is lost |
| --- | --- | --- | --- |
| 5 steps | `lesson-05` | step 3 in 5 of 5 runs; shown at step 5 in 5 of 5 | date, code, window, TX id (same four). In 1 of 5 the summary invented a value (EUR 180.00) |
| 7 steps (main) | `lesson-05` | step 3 in 5 of 5 (from 2.3) | the same four; no invented value in 5 runs |
| 10 steps (+1 topic switch) | `lesson-05` | step 3 in 5 of 5 | the same four; after the return to the dispute (steps 9 and 10) the agent cannot name the charge in 5 of 5; in 1 of 5 the invented EUR 180.00 is carried from step 3 to step 10 |
| 5 and 10 steps | `clean` | not lost (1 run each) | nothing |

**Conclusion on the length axis:** with the threshold at 2 steps even the 5-step version loses the case at step 3, so the short version is not a safe control here. The lesson expects the defect not to fire at 5 steps, but that assumes the threshold of 5 messages; our stand is set lower. The only safe dialogs are the ones shorter than 3 steps. The 10-step version adds no new lost values, it makes the damage longer (steps 3 to 10 without the case).

Across the 15 `lesson-05` runs of all three versions, the summary **invented** a value in 2 (EUR 180.00 instead of 240.00, both times in the 5-step and 10-step runs, never in the 7-step runs). That is a different failure from forgetting: the agent then states a wrong amount with confidence. See 4.1.

---

## 3. Failure mechanisms

On each step the model gets three inputs: the summarized history, the retrieval context of the step, and the system prompt. A cause is named only after the inputs are opened.

### 3.1. Loss step and proof of cause

```
loss step                          3 (5 of 5 runs)
in history before the loss         amount 240.00, date 20 July, code goods_not_received, window 90, TX-0401
in history after the loss          "goods never arrived, code identified, dispute not opened yet" (no values)
manifestation step                 5 (5 of 5 runs)
agent reply at the manifestation   lists TX-0402 and TX-0401, both EUR 240.00, cannot tell which one
retrieval context at manifestation not involved: no search call at step 5 (the case values are not documents)
mechanism                          D06: summary written by the model drops the values of the case
```

**Conclusion:** the amount, date, code and window disappear from the history at step 3 because the summary does not keep numbers, and the agent shows it two steps later, so the cause is the summarize step and not retrieval.

Proof from the control run: on `clean` the same summary at step 3 keeps all five values.

### 3.2. Self-contradiction (D07)

```
first reply about the window       step 2: 90 days, deadline 2026-10-18
second reply about the window      step 7: 90 days in 4 of 5 runs
                                   step 7, run 1: lists "goods_not_received 90 days, duplicate_charge 60 days"
reason code in history of step 7   present again (returned by tool at step 5/6)
retrieval context of step 7        whole (disputes.md chunks returned)
classification                     D07 did not reproduce as a contradiction
```

**On what basis:** in 4 of 5 runs the agent repeats 90 days at step 7. In run 1 the agent lists 60 days as the window of another code and asks which code applies. It does not claim 60 days for this dispute, which is close to the honest "I don't know which code" that the case needs. The automatic check flagged it because it looks for the word "60" and cannot tell a claim from a list.

The D06 loss happened in all 5 runs. The D07 effect (a wrong confident number) did not appear. I do not write it as reproduced.

### 3.3. Control on `clean`

**Entities hold until step:** 7 (all five values in history at every step).
**At step 7 the agent said:** the dispute (ID 1) is already open for TX-0401, EUR 240.00, deadline 2026-10-18.
**What this proves:** without the defect the same dialog keeps the case, so the loss on `lesson-05` comes from the defect and not from the model or the scenario.
**Limit of the proof:** one run. On `clean` the agent also opened the dispute at step 6, so the later steps are not identical to `lesson-05`.

### 3.4. Failures on the other scenarios of the plan

*Homework, step 3.*

| Scenario | Failure (symptom) | Mechanism | Loss step | Manifestation step | Proof: history and retrieval context |
| --- | --- | --- | --- | --- | --- |
| CONV-… |  |  |  |  |  |

---

## 4. Invariants and oracles

An invariant checks that a value did not change between steps. An oracle checks that the value is correct, at the step where it was first said. Every case needs both.

### 4.1. Two checks for the main scenario

Checked on the traces of the same runs as in 2.3 (`analyze_traces.py`, function `invariants`).

| Check | Entity | From step | Ladder level | `clean` | `lesson-05`: failed in … of 5 runs |
| --- | --- | --- | --- | --- | --- |
| 1 | dispute amount 240.00 EUR | 1 | 2, number with tolerance | green | 0 of 5 |
| 2 | reason code goods_not_received | 2 | 1, exact equality | green | 1 of 5 (run 1, step 7: `duplicate_charge` named) |

Oracle: the engine (`disputes` tool result: window 90, deadline 2026-10-18) at step 2, where the value was first said.

Over all 15 `lesson-05` runs of the 5, 7 and 10-step versions, check 1 (amount) is **red in 2 of 15**: `CONV-002-S5` run 4 (step 5: "TX-0401 (EUR 180.00)") and `CONV-002-L10` run 1 (EUR 180.00 from step 3 to step 10). The case's own check at step 5 ("answer mentions TX-0401 or 240") stayed green in both runs, so here the invariant catches what the pattern check does not. In `CONV-002-L10` run 1 the agent noticed at step 9 that its summary says 180.00 and the account says 240.00, and said so.

**What the checks showed:** on the 7-step scenario the invariants stay green almost everywhere, because the agent does not change the number, it loses the case and asks again. The only red result (run 1) is the same hedge as in 3.2, so an invariant on its own finds the divergence but not the loss. The loss is caught by checking that the case values are still available at the later steps (retention), which is not an invariant.

The case checks in `sets/l05.jsonl` failed in 2 of 5 runs: run 1 at step 7 (the pattern "60"), run 4 at step 4 (the agent asked for an amount before giving the spread). The first is the pattern weakness in 3.2, the second is a real effect of the lost amount.

### 4.2. Invariants and oracles for all cases

*Homework, step 4.*

| Case | Invariant: entity, from step, level | Oracle: step and who checks | Share of runs where it failed |
| --- | --- | --- | --- |
| CONV-… |  |  | of 5 |

**Agreed error** (the agent repeats a wrong value and the invariant is green). The oracle in this set that catches it: to fill.

---

## 5. Test plan and cost

*Homework, step 5.*

### 5.1. Axes and full combinatorics
### 5.2. Chosen scenarios
### 5.3. Cost and schedule

---

## 6. Residual risk and decision

*Homework, step 6.*

### 6.1. Uncovered combinations
### 6.2. Blind spots of the method
### 6.3. Recommended fix for D06

---

## Last line

*Homework, step 6.*

```
what we traded                   ...
what we do not do                ...
when the decision changes        ...
```
