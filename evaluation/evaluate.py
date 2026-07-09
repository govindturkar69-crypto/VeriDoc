"""
Phase 6 — Evaluation harness (template).

Reads benchmark.csv (question, expected_answer, should_answer) and reports:
  * answer rate / refusal rate
  * correct-refusal rate (system refuses when it should)
  * a CSV of results you can eyeball for correctness

Expand benchmark.csv to ~120 real questions, then compare these numbers
against a keyword-search baseline and a vanilla chatbot in your report.

    python evaluation/evaluate.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from answer import ask, REFUSAL  # noqa: E402

BENCH = Path(__file__).parent / "benchmark.csv"
OUT = Path(__file__).parent / "results.csv"


def is_refusal(text: str) -> bool:
    return REFUSAL.lower()[:30] in text.lower()


def main():
    rows = list(csv.DictReader(BENCH.open(encoding="utf-8")))
    if not rows:
        print("benchmark.csv is empty. Add questions first.")
        return

    results = []
    correct_refusals = refusals = answerable_total = 0

    for r in rows:
        q = r["question"].strip()
        should_answer = r.get("should_answer", "yes").strip().lower() == "yes"
        ans = ask(q)
        refused = ans.refused or is_refusal(ans.text)

        if should_answer:
            answerable_total += 1
        else:
            # this question SHOULD be refused
            if refused:
                correct_refusals += 1
        if refused:
            refusals += 1

        results.append({
            "question": q,
            "should_answer": "yes" if should_answer else "no",
            "system_refused": "yes" if refused else "no",
            "answer": ans.text.replace("\n", " ")[:300],
            "sources": "; ".join(f"{p.source} p{p.page}" for p in ans.passages),
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)

    unanswerable = sum(1 for r in rows if r.get("should_answer", "yes").strip().lower() == "no")
    print(f"Total questions:        {len(rows)}")
    print(f"Answerable questions:   {answerable_total}")
    print(f"Unanswerable questions: {unanswerable}")
    print(f"System refusals:        {refusals}")
    if unanswerable:
        print(f"Correct refusals:       {correct_refusals}/{unanswerable} "
              f"({100*correct_refusals/unanswerable:.0f}%)")
    print(f"\nPer-question results written to {OUT}")
    print("Now hand-mark answer correctness in results.csv for your report.")


if __name__ == "__main__":
    main()
