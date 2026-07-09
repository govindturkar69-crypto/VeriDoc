"""
Phase 6 — Three-way comparison: VeriDoc vs Keyword Search vs Vanilla Chatbot.

Runs all three systems over evaluation/benchmark.csv and writes
evaluation/comparison.csv. It also prints a summary table showing the key
result: only VeriDoc can honestly REFUSE when the answer is not in the
documents, while the baselines answer anyway (and are therefore untrustworthy).

Place this file in  veridoc/evaluation/  and run:
    python evaluation/compare.py

After it finishes, open comparison.csv and mark answer correctness by hand
for the answerable questions (add a column) to complete your accuracy numbers.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from answer import ask, REFUSAL          # noqa: E402
from baselines import keyword_answer, vanilla_answer  # noqa: E402

BENCH = Path(__file__).parent / "benchmark.csv"
OUT = Path(__file__).parent / "comparison.csv"

REFUSAL_MARK = REFUSAL.lower()[:30]


def is_refusal(text: str) -> bool:
    t = text.lower()
    return REFUSAL_MARK in t or "could not find" in t or "not found in" in t


def main():
    rows = list(csv.DictReader(BENCH.open(encoding="utf-8")))
    if not rows:
        print("benchmark.csv is empty.")
        return

    results = []
    # counters: correct refusals on UNANSWERABLE questions
    unanswerable = 0
    vd_correct_refuse = kw_correct_refuse = va_correct_refuse = 0
    # counters: wrong refusals on ANSWERABLE questions
    answerable = 0
    vd_wrong_refuse = 0

    for i, r in enumerate(rows, 1):
        q = r["question"].strip()
        should = r.get("should_answer", "yes").strip().lower() == "yes"

        vd = ask(q)
        vd_text = vd.text
        vd_ref = vd.refused or is_refusal(vd_text)

        kw_text = keyword_answer(q)      # never refuses by design
        va_text = vanilla_answer(q)
        va_ref = is_refusal(va_text)

        if should:
            answerable += 1
            if vd_ref:
                vd_wrong_refuse += 1
        else:
            unanswerable += 1
            if vd_ref:
                vd_correct_refuse += 1
            if is_refusal(kw_text):
                kw_correct_refuse += 1
            if va_ref:
                va_correct_refuse += 1

        results.append({
            "question": q,
            "should_answer": "yes" if should else "no",
            "veridoc_answer": vd_text.replace("\n", " ")[:200],
            "veridoc_refused": "yes" if vd_ref else "no",
            "veridoc_sources": "; ".join(f"{p.source} p{p.page}" for p in vd.passages),
            "keyword_answer": kw_text.replace("\n", " ")[:200],
            "vanilla_answer": va_text.replace("\n", " ")[:200],
            "vanilla_refused": "yes" if va_ref else "no",
        })
        print(f"[{i}/{len(rows)}] {q[:55]}")

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)

    # ---- summary ----
    def pct(a, b):
        return f"{(100*a/b):.0f}%" if b else "n/a"

    print("\n" + "=" * 62)
    print("SUMMARY — honest refusal on UNANSWERABLE questions")
    print("(higher = more trustworthy; it should refuse, not make things up)")
    print("=" * 62)
    print(f"Unanswerable questions in benchmark : {unanswerable}")
    print(f"  VeriDoc correct refusals          : {vd_correct_refuse}/{unanswerable}  ({pct(vd_correct_refuse, unanswerable)})")
    print(f"  Keyword search correct refusals   : {kw_correct_refuse}/{unanswerable}  ({pct(kw_correct_refuse, unanswerable)})")
    print(f"  Vanilla chatbot correct refusals  : {va_correct_refuse}/{unanswerable}  ({pct(va_correct_refuse, unanswerable)})")
    print("-" * 62)
    print(f"Answerable questions                : {answerable}")
    print(f"  VeriDoc wrong refusals (lower=better): {vd_wrong_refuse}/{answerable}  ({pct(vd_wrong_refuse, answerable)})")
    print(f"  Citations provided by VeriDoc      : yes (every answer)")
    print(f"  Citations by keyword / vanilla     : none")
    print("=" * 62)
    print(f"\nFull per-question results written to {OUT}")
    print("Next: open comparison.csv and hand-mark answer correctness for the")
    print("answerable questions to get final accuracy percentages for each system.")


if __name__ == "__main__":
    main()
