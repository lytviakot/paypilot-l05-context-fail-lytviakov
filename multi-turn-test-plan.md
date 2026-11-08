# Multi-turn Test Plan + Degradation Profile

Scenario C-07 (CUS-0004): the agent loses the dispute amount between two messages, and nobody sees it in any single answer.

## 1. Context and prediction

```
system             PayPilot (local stand, localhost:8000)
profiles           clean, lesson-05 (D06, D07)
agent model        claude-haiku-5-5 (Anthropic)
main scenario      C-07, 7 steps, customer CUS-0004
summarize after    2 steps (set with PUT /api/_test/summarize_after)
set                sets/l05.jsonl, 4 cases, set_hash 947ef71be283
dialog cases       l05_dialogs.jsonl, 5 cases (CONV-H01 to CONV-H05), set_hash 546d67fb0eb3
lab length cases   sets/l05_len.jsonl, 2 cases, set_hash 93a0b5eae73d
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

**Control on the homework set:** the five cases of `l05_dialogs.jsonl` ran 5 times each on `clean` (report `l05_dialogs-clean-20261108T123855.json`). 24 of 25 runs are green, including the main scenario CONV-H02 (5 of 5). The one red run is CONV-H03 run 5, step 8: the agent named the right code (goods_not_received) for TX-0401 and then offered a `duplicate_charge` dispute for TX-0402 as an alternative. The check forbids any other code, so it fired on a correct answer. I count it as a false alarm of the check, not as a defect (see 4.2).

### 3.4. Failures on the other scenarios of the plan

Runs: 5 per case on `lesson-05` (report `l05_dialogs-lesson-05-20261108T124809.json`, traces read from the same run). In every case the summary at step 3 is the first place where the values are gone.

| Scenario | Failure (symptom) | Mechanism | Loss step | Manifestation step | Proof: history and retrieval context |
| --- | --- | --- | --- | --- | --- |
| CONV-H01 control, 5 steps | none, 5 of 5 green on both profiles | none: no summary is made (threshold 8) | none | none | History stays verbatim; the check "agent.summarize did NOT run" passed in all 10 runs. The defect needs the summary. |
| CONV-H02 main, 7 steps | step 7: the agent lists both charges and gives 12 October and 18 October; 5 of 5 runs | forgot (D06) | 3 | 7 (check), 5 (agent) | Summary at step 3, run 1: "The assistant identified the matching code and confirmed the transaction is eligible ... waiting for the customer to confirm". No amount, code, date, window or TX id. Retrieval at step 7: no search call, so the case values did not come from the documents. |
| CONV-H03 worst case, 10 steps | step 10: both deadlines listed in 4 of 5 runs; step 8 in 1 of 5 (run 2); run 4 green | forgot (D06); run 2 also a substituted code (D07) | 3 | 10 (8 in run 2) | Run 1 summary: "disputing a card transaction for goods that never arrived ... No dispute has been opened yet", no values. Step 10 reply: "Both TechMart Online charges are eligible ... Which charge is the order that didn't arrive?" Retrieval: no search at steps 8 to 10. Run 4 summary kept `goods_not_received`, and that run is the green one. Run 2 summary names `service_not_rendered`. |
| CONV-H04 length, 4 steps | none by the check (5 of 5 green), but in 4 of 5 runs the agent says "I can't tell ... which transaction the dispute is for" at step 4 | forgot (D06), not seen by the check | 3 | 4 (agent) | Run 1 summary has no values. Step 4 calls `get_account` and `get_transactions`, gets two charges of EUR 240.00, so "240" appears in the answer and the amount check passes. No search call. |
| CONV-H05 entity competition, 7 steps | code check red at step 5 in 3 of 5 runs (1 to 3); deadline red at step 7 in 4 of 5 (1 to 4); run 5 green | forgot (D06) and substituted code (D07) | 3 | 5 (code), 7 (deadline) | Run 1 summary: "The eligibility check confirmed the service_not_rendered code" (wrong code written by the summarizer). Step 5 reply states "Reason code: service_not_rendered ... Amount: Not recorded in what I have". The case code is goods_not_received (steps 1 and 2 of the dialog). Retrieval at step 5: tools `get_account` and `get_transactions` only. |

Counts over the 20 summaries of the four cases that make one (H02 to H05): 20 of 20 contain no amount or date; 4 of 20 keep `goods_not_received`; 5 of 20 name a different code (H03 run 2, H04 runs 3 and 5, H05 runs 1 and 3). Only H05 run 1 was read as a confident substitution in the answer; in the other runs the agent lists other codes as options, which I do not count as D07.

The dispute amount check (level 2) did not turn red in any of the 25 `lesson-05` runs, because after the loss the agent reads the transactions again and both charges are EUR 240.00.

---

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

Ladder level 2 is a number with tolerance, level 3 is a pattern. The loader accepts only these two levels for invariants (level 1 is not available for a pattern check), so the reason code is level 3, not 1 as in 4.1. "Oracle" is the step where the value was first said and who checks that it is right. Failure share is on `lesson-05`, 5 runs per case; `clean` in the last column.

| Case | Invariant: entity, from step, level | Oracle: step and who checks | Failed on `lesson-05` (by invariant) | `clean` |
| --- | --- | --- | --- | --- |
| CONV-H01 | dispute_amount, 1, L2 | step 1, `engine:transactions` (240.00) | 0 of 5 | 0 of 5 |
|  | filing_deadline, 2, L3 | step 2, `engine:disputes` (2026-10-18) | 0 of 5 | 0 of 5 |
| CONV-H02 | dispute_amount, 1, L2 | step 1, `engine:transactions` | 0 of 5 | 0 of 5 |
|  | filing_deadline, 2, L3 | step 2, `engine:disputes` | 5 of 5 (step 7) | 0 of 5 |
| CONV-H03 | dispute_amount, 1, L2 | step 1, `engine:transactions` | 0 of 5 | 0 of 5 |
|  | reason_code, 1, L3 | step 1, `engine:disputes` (goods_not_received) | 1 of 5 (step 8) | 1 of 5 (false alarm) |
|  | filing_deadline, 2, L3 | step 2, `engine:disputes` | 4 of 5 (step 10) | 0 of 5 |
| CONV-H04 | dispute_amount, 1, L2 | step 1, `engine:transactions` | 0 of 5 | 0 of 5 |
| CONV-H05 | dispute_amount, 1, L2 | step 1, `engine:transactions` | 0 of 5 | 0 of 5 |
|  | reason_code, 1, L3 | step 1, `engine:disputes` | 3 of 5 (step 5) | 0 of 5 |
|  | filing_deadline, 2, L3 | step 2, `engine:disputes` | 4 of 5 (step 7) | 0 of 5 |

**Agreed error** (the agent repeats a wrong value and the invariant is green). The oracle in this set that catches it: the expected values come from the engines (`engine:transactions` for the amount, `engine:disputes` for the code and the deadline), so a value that is wrong from the start, or wrong after the summary, fails against them. The set does not catch the opposite case: a right value without the case behind it. CONV-H04 is green in 5 of 5 runs while in 4 of 5 the agent says it cannot tell which transaction is meant (see 6.2).

**One check is too strict.** The "no other reason code" part of the reason_code invariant fires when the agent names another code as an option. It gave the only false alarm on `clean` (CONV-H03 run 5, step 8). The next version should forbid a wording like "reason code is <other code>" and not any mention.

---

## 5. Test plan and cost

### 5.1. Axes and full combinatorics

| Axis | Values | What it catches |
| --- | --- | --- |
| Length | 5, 7, 10 steps (and 4 for the isolation case) | the threshold of the summary and its effect |
| Number of entities | 1, 2, 3 numeric case values | competition for the place in the summary |
| Topic switches | 0, 1, 2 | whether the agent comes back to the case values |

**Full combinatorics:** 3 x 3 x 3 = 27 scenarios
**Cost of one run of the full combinatorics:** 27 scenarios x 7.33 steps on average x 5 runs = about 990 steps. At the measured cost of USD 0.00091 (`clean`) to USD 0.00108 (`lesson-05`) per step this is about USD 0.90 to USD 1.07, and about 55 minutes. This is a lower bound, because long dialogs cost more per step.

A step is one client message with the agent's answer; each step is one to four model calls (traces), so the model calls are roughly twice the steps.

### 5.2. Chosen scenarios

| ID | Length | Entities | Switches | Role in the plan | Question it closes |
| --- | --- | --- | --- | --- | --- |
| CONV-H01 | 5 | 2 | 1 | control | does anything get lost when no summary is made |
| CONV-H02 | 7 | 2 | 1 | main (equals C-07) | the original complaint |
| CONV-H03 | 10 | 3 | 2 | worst case | how bad it gets with everything at once |
| CONV-H04 | 4 | 1 | 0 | isolates length | does the shortest dialog that crosses the threshold already lose the case |
| CONV-H05 | 7 | 3 | 0 | isolates entities | does the number of entities matter at the same length and no switch |

### 5.3. Cost and schedule

**Cost of the chosen plan:** 33 steps x 5 runs = 165 steps. Measured: USD 0.15 on `clean` (552.8 s) and USD 0.18 on `lesson-05` (667.8 s), from the `cost_usd` of the reports (1.13M and 1.29M input tokens, 75K and 98K output tokens).
**Comparison with the one-step set `golden.jsonl`:** about 88 agent calls and USD 0.03 to 0.035 per daily run (homework 2 and 3). The dialog set is about five times more expensive and takes about four times longer.
**When we run the dialog set:** before every release, and after any change to the summarizer, its threshold or the system prompt. Not daily.
**Why:** in dollars daily would be cheap (30 runs a month is about USD 5), but a run takes 9 to 11 minutes and the result is noisy: 1 false alarm in 25 clean runs, and a defect that fails 4 of 5 or 5 of 5 runs on the broken profile. What moves the result is the summarizer settings, and those change rarely, so a release gate plus a run after such a change gives the same protection for a small part of the time. This matches `gate: release` in the cases.

---

## 6. Residual risk and decision

### 6.1. Uncovered combinations

```
1. what is not covered              5 steps with 3 entities and 2 switches, and 10 steps with 1 entity and 2 switches
   what happens if it breaks        the same loss from step 3; these dialogs sit between the covered ends
   why we live with it now          the control (H01) stays green and the worst case (H03) fails in 4 of 5 runs,
                                    so the two ends are known and the middle is predictable
   postpone / accept                accept

2. what is not covered              dialogs longer than 10 steps (a second summary, a summary of a summary)
   what happens if it breaks        the first summary can already be wrong; a second one can lose what is left,
                                    and the damage grows with every step
   why we live with it now          at 10 steps only one summary was made in all 5 runs, and no complaint is that long yet
   postpone / accept                postpone: run a 15-step case when the summarizer or its threshold changes

3. what is not covered              the default threshold of 8 messages (all runs use 2 steps)
   what happens if it breaks        in production the loss moves later, so the safe length is longer than the 3 steps measured here
   why we live with it now          we know the mechanism, but not the real step at the default
   postpone / accept                postpone: run the set with --summarize-after 8 before the release that changes the threshold

4. what is not covered              two disputes in one conversation (the customer has two charges of EUR 240.00)
   what happens if it breaks        the agent mixes the two cases; the amount check cannot tell them apart
   why we live with it now          we saw the mix-up as a consequence of the loss, not as a separate cause
   postpone / accept                postpone: add a case with two real disputes and a transaction-id invariant
```

### 6.2. Blind spots of the method

| Blind spot | What closes it or why we accept it |
| --- | --- |
| The profile does not explain why the summary drops a value at this step | Accepted for now: the summary text shows what is gone, the trace of the summarize call would show why. Closes with full tracing in L08. |
| Agreed error: the invariant is green on a value that is present but not tied to the case. CONV-H04: 5 of 5 green, 4 of 5 answers say "I can't tell ... which transaction" | Add a check that the answer does not contain "can't tell / can't confirm / which transaction" at the probe step, and a transaction-id invariant (TX-0401). Not done in this set, because a change of the file changes the `set_hash` of the runs above. |
| Axes that are not in the plan (language switch, return after a day, two disputes in one chat) | Two disputes: see 6.1, item 4. The other two: accepted, one market and one session for now. |

### 6.3. Recommended fix for D06

| Option | Chosen? | Cost | What breaks instead |
| --- | --- | --- | --- |
| Move the case entities into a structured field outside the summary | yes | Engineering time, assumption: 8 to 16 hours at USD 20 per hour = USD 160 to 320. Extra tokens: about 100 per step, which at USD 0.10 per million is about USD 0.01 per 1,000 steps. | We must know in advance which entities matter, and that list is the test plan. The orchestration code changes. |
| Raise `SUMMARIZE_AFTER` | no | Tokens per step grow with the history. Not measured here. | The window fills sooner, and dialogs longer than the new threshold lose the case again. |
| Add "keep the numbers" to the summarizer prompt | no | One edit, minutes. | The same model that already wrote `service_not_rendered` instead of `goods_not_received` in 5 of 20 summaries has to follow it. Reliability is the lowest. |

**Why this option under the Ship it mandate:** it is the only one that removes the cause. In 20 of 20 summaries the amount and date are gone, and in 16 of 20 the code is gone or wrong (4 keep `goods_not_received`), so instructions to a model that already fails at this are not enough. The cost is a few days of work and almost nothing in tokens, against a loss of customer money (complaint C-07). The fix can be checked with this set: the same five cases on `lesson-05` should turn green.

---

## Last line

```
what we traded                   engineering time (a structured field) for a prompt line that costs minutes
                                 and cannot be trusted; and 5 scenarios x 5 runs (USD 0.15 to 0.18 a run)
                                 instead of the 27-scenario grid (about USD 1)
what we do not do                run the dialog set daily; cover the 22 other combinations; cover the axes
                                 outside the plan (language, a return after a day); the simulated-dialog option
when the decision changes        a complaint about a dialog longer than 10 steps; a change of the summary
                                 threshold or of the summarizer model; the run cost above USD 1; the fix is
                                 shipped and the set is green (then the set can move to a daily gate)
```

---

## Checklist

**After the lab**

- [x] Prediction written in section 1
- [x] Record sheets 2.1 and 2.2 filled for all seven steps, with history and retrieval context
- [x] 2.3: five runs, range and median
- [x] 2.4: loss and manifestation in different rows
- [x] 3.1: loss step named, and the retrieval context at the manifestation step shown to be out of the picture
- [x] 3.2: self-contradiction classified with proof
- [x] 4.1: two checks with the result on `clean` and `lesson-05`

**Before the homework is handed in**

- [x] Section 1 filled, with the number of cases and `set_hash`
- [x] 2.3 names the length limit
- [x] 3.3 has the control on `clean`, 3.4 the failures of the other scenarios
- [x] 4.2: every case has an invariant with a ladder level and an oracle
- [x] Section 5: three axes, five scenarios with a role (one control), cost of the full combinatorics and of the plan, schedule
- [x] 6.1: four uncovered combinations, one of them "accept"
- [x] 6.3: fix chosen and its cost named
- [x] Last line filled with all three points
