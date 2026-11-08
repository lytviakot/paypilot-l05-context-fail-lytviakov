"""Loss step, invented amounts and unsure steps for the 5/7/10-step versions of C-07.

Usage: python analyze_length.py CASE_ID TRACE_STAMP N_STEPS [RUNS]
Example: python analyze_length.py CONV-002-L10 20261108T121142 10 5
"""
import json, os, re, sys

TRACES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "traces")
KNOWN = {"240.00", "5,000.00", "500.00", "15.00", "1,500.00", "50,000.00", "35.50",
         "0.00", "5000.00", "49,964.50", "1,000.00", "3.00", "18.00"}  # limits, fees, examples
UNSURE = re.compile(r"can't tell|haven't identified|which (one|transaction|charge)|cannot", re.I)


def spans(s, out):
    out.append(s)
    for c in s.get("children", []):
        spans(c, out)
    return out


def main(case, stamp, n, runs=5):
    for r in range(1, runs + 1):
        loss, summary_amounts, odd, unsure = None, [], [], []
        for t in range(1, n + 1):
            d = json.load(open(f"{TRACES}/{stamp}/{case}-run{r}-turn{t}.json", encoding="utf-8"))
            for s in spans(d["trace"], []):
                if s["name"] == "agent.summarize":
                    text = s["attributes"].get("summary.text", "")
                    if "240" not in text and loss is None:
                        loss = t
                    summary_amounts += re.findall(r"(?:EUR|€)\s?(\d[\d,]*\.\d\d)", text)
            for m in re.findall(r"(?:EUR|€)\s?(\d[\d,]*\.\d\d)", d["answer"]):
                if m not in KNOWN:
                    odd.append((t, m))
            if t >= 8 and UNSURE.search(d["answer"]):
                unsure.append(t)
        print(f"run {r}: loss step {loss}, amounts in summary {summary_amounts}, "
              f"odd amounts in answers {odd}, unsure steps >= 8 {unsure}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 5)
