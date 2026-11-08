"""Writes sets/l05_dialogs.jsonl: the five dialog cases of the homework test plan.

Every case is a PayPilot dispute dialog for CUS-0004 (TX-0401, 240.00 EUR,
goods_not_received, deadline 2026-10-18). The same customer also has TX-0402
(240.00 EUR, deadline 2026-10-12): when the agent loses the case it lists both
charges, so the 12 October deadline is used as the "wrong charge" signal.

Run:  python generate_dialogs.py > l05_dialogs.jsonl   (use bash or pwsh,
not Windows PowerShell 5.1: it writes UTF-16)
"""
import json
import sys

CTX = {"customer_id": "CUS-0004", "clock": "2026-09-15T10:00:00Z"}

OPEN = ("I'm CUS-0004. Transaction TX-0401, 240.00 EUR: the goods never arrived. "
        "Which reason code applies?")
DISPUTE = "Can I dispute it?"
LIMIT = "What is my daily card limit?"
SPREAD = "And the FX spread if I pay in USD?"
BACK = "Fine. Back to that charge, what do I do next?"
AMOUNT = "240 euro, as I said at the start."
TIME = "And I still have time to file, right?"

DEADLINE = r"October 18, 2026|18 October 2026|2026-10-18"
WRONG_DEADLINE = r"October 12|12 October|2026-10-12|\b60\b|\b56\b"
OTHER_CODES = r"duplicate[_ ]charge|service[_ ]not[_ ]rendered|fraud_card_not_present|unauthorized_debit"


def turns(*texts):
    return [{"role": "user", "content": t} for t in texts]


def amount(probes, from_turn=1):
    return {"entity": "dispute_amount", "from_turn": from_turn, "level": 2,
            "expected_number": 240.0, "tolerance": 0.01, "probe_turns": probes,
            "probe_any": True, "oracle_turn": 1, "oracle_by": "engine:transactions",
            "defect": "D06"}


def deadline(probes, oracle_turn=2):
    return {"entity": "filing_deadline", "from_turn": 2, "level": 3,
            "pattern": DEADLINE, "forbid": WRONG_DEADLINE, "probe_turns": probes,
            "oracle_turn": oracle_turn, "oracle_by": "engine:disputes", "defect": "D07"}


def code(probes):
    return {"entity": "reason_code", "from_turn": 1, "level": 3,
            "pattern": r"goods[_ -]not[_ -]received", "forbid": OTHER_CODES,
            "probe_turns": probes, "oracle_turn": 1, "oracle_by": "engine:disputes",
            "defect": "D07"}


def case(cid, scenario, dialog, invariants, axes, role, failure_mode, severity,
         source="plan", control=False, why=""):
    meta = {"layer": "memory", "oracle": "engine:disputes", "assertion": "invariant",
            "invariants": invariants, "min_turns": len(dialog), "axes": axes,
            "plan_role": role, "source": source, "failure_mode": failure_mode,
            "severity": severity, "runs": 5, "gate": "release", "added_in": "hw4",
            "defects": ["D06", "D07"], "summarize_after": 8 if control else 2,
            "why_this_level": why}
    if control:
        meta["expect_summarize"] = False
    return {"id": cid, "scenario": scenario, "context": CTX, "turns": dialog,
            "additional_metadata": meta}


CASES = [
    case("CONV-H01",
         "Control: a five-step dispute dialog with one topic switch and the summary "
         "threshold above the dialog length, so no summary is made and nothing may be lost",
         turns(OPEN, DISPUTE, LIMIT, BACK, TIME),
         [amount([4, 5]), deadline([5])],
         {"length": 5, "entities": 2, "topic_switches": 1}, "контроль",
         "summarization_drop", "medium", control=True,
         why="amount is a number (level 2), the deadline is a date string (level 3); "
             "the control has no summary, so both stay green on lesson-05"),
    case("CONV-H02",
         "Main scenario, equal to complaint C-07: amount and filing deadline are "
         "stated at steps 1-2, then two unrelated questions, then the client returns "
         "to the charge",
         turns(OPEN, DISPUTE, LIMIT, SPREAD, BACK, AMOUNT, TIME),
         [amount([5, 6, 7]), deadline([7])],
         {"length": 7, "entities": 2, "topic_switches": 1}, "основний",
         "summarization_drop", "high", source="complaint",
         why="the amount is checked as a number, the deadline as a pattern plus a "
             "forbidden second-charge deadline, because the lost case makes the agent list both charges"),
    case("CONV-H03",
         "Worst case: ten steps, three entities and two topic switches before the "
         "agent is asked to recall the charge, the code, the amount and the deadline",
         turns(OPEN, DISPUTE, LIMIT, SPREAD, BACK, AMOUNT,
               "Unrelated question: what is the fee for an international transfer?",
               "OK, back to the dispute. Remind me which reason code we are talking about.",
               "And what amount are we disputing?",
               TIME),
         [amount([9]), code([8]), deadline([10])],
         {"length": 10, "entities": 3, "topic_switches": 2}, "найгірший",
         "summarization_drop", "critical",
         why="three entities probed after the second switch; each probe asks for exactly one entity"),
    case("CONV-H04",
         "Isolates length: four steps, one entity, no topic switch; the summary still "
         "fires at step 3 with the threshold of 2 steps",
         turns(OPEN, DISPUTE, "OK. What documents do I need to prepare for the dispute?",
               "And what was the amount we are disputing?"),
         [amount([4])],
         {"length": 4, "entities": 1, "topic_switches": 0}, "ізоляція осі",
         "summarization_drop", "high",
         why="the shortest dialog that still crosses the threshold; one probe at the last step"),
    case("CONV-H05",
         "Isolates entity competition: seven steps on one topic, three entities, "
         "no topic switch",
         turns(OPEN, DISPUTE, "How does the review process work and how long does it take?",
               "What happens after I file?",
               "Remind me: which reason code and which amount are we disputing?",
               "Is the deadline the same for every reason code?",
               "OK, so for my case, what is the deadline?"),
         [amount([5]), code([5]), deadline([7])],
         {"length": 7, "entities": 3, "topic_switches": 0}, "ізоляція осі",
         "summarization_drop", "high",
         why="same length as the main scenario but three entities and no switch; the "
             "difference to CONV-H02 is the number of entities"),
]

if __name__ == "__main__":
    sys.stdout.reconfigure(newline="\n", encoding="utf-8")
    for c in CASES:
        print(json.dumps(c, ensure_ascii=False))
