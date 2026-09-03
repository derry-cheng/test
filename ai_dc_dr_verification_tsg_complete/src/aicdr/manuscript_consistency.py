"""Machine checks for claims, cross-references, and release hygiene.

The checks are intentionally narrow: they do not judge scientific merit, but
they catch stale numerical claims, unreferenced floats, and residual drafting
artifacts that would make the paper fail a reproducibility or typesetting
review.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import sha256, write_json


def run_manuscript_consistency(
    root: Path,
    text: str,
) -> list[dict[str, Any]]:
    """Write the manuscript consistency report and return its checks."""

    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))
    unreferenced = sorted(labels - refs)
    forbidden = {
        "/goal": "forbidden slash-goal drafting residue",
        "TODO": "unfinished TODO marker",
        "TBD": "unfinished TBD marker",
        "FIXME": "unfinished FIXME marker",
        "$10/MWh": "stale Experiment 17 tariff",
        "weight 1.0": "stale Experiment 17 projection weight",
        "daily payment obeys": "overbroad absolute-payment wording",
    }
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    residue = [description for token, description in forbidden.items() if token in text]
    add(
        "no_drafting_or_stale_claim_residue",
        not residue,
        "none found" if not residue else "; ".join(residue),
    )
    add(
        "all_float_labels_are_referenced",
        not unreferenced,
        "all labels have an in-text reference"
        if not unreferenced
        else "unreferenced labels: " + ", ".join(unreferenced),
    )
    add(
        "table_count_within_tsg_limit",
        text.count("\\begin{table}") == 5,
        f"{text.count('\\begin{table}')} tables; the locked paper limit is five",
    )
    figure_count = len(re.findall(r"\\begin\{figure\*?\}", text))
    add(
        "figure_count_is_explicit",
        figure_count == 2,
        f"{figure_count} figures in the manuscript source",
    )

    intro_match = re.search(
        r"\\section\{Introduction\}(.*?)\\section\{System Model",
        text,
        flags=re.DOTALL,
    )
    conclusion_match = re.search(
        r"\\section\{Conclusion\}.*?\\end\{document\}",
        text,
        flags=re.DOTALL,
    )
    add(
        "introduction_has_no_subsections",
        intro_match is not None and "\\subsection{" not in intro_match.group(1),
        "Introduction is a single section",
    )
    add(
        "conclusion_has_no_subsections",
        conclusion_match is not None
        and "\\subsection{" not in conclusion_match.group(0),
        "Conclusion is a single section",
    )
    required_phrases = {
        "Exp~26": "end-to-end lineage certificate is reported",
        "not asserted": "role separation is stated",
        "relative N--1 baseline-cost cap": "payment guarantee scope is bounded",
        "deployment-primary": "deployment panel is distinguished from mechanism isolation",
        "q_{10}": "lower entitlement envelope is named",
    }
    missing_phrases = [
        description for phrase, description in required_phrases.items() if phrase not in text
    ]
    add(
        "critical_claim_scope_and_lineage_phrases_present",
        not missing_phrases,
        "all C1--C5 scope anchors present"
        if not missing_phrases
        else "missing: " + "; ".join(missing_phrases),
    )

    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report_json = {
        "source": "paper/main.tex",
        "source_sha256": sha256(root / "paper/main.tex"),
        "all_checks_passed": all(item["passed"] for item in checks),
        "checks": checks,
        "label_count": len(labels),
        "reference_count": len(refs),
    }
    write_json(reports / "manuscript_consistency.json", report_json)
    import pandas as pd

    pd.DataFrame(checks).to_csv(reports / "manuscript_consistency.csv", index=False)
    return checks
