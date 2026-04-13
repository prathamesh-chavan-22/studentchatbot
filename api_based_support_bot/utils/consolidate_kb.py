"""
consolidate_kb.py
Rebuilds knowledge_base.txt from:
  1. 15 new explicit Q&A pairs (provided by admin)
  2. refined_grievances.txt
  3. fyjc_faq_full.txt
Strips the old database-imported content entirely.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 1. New Q&A pairs
# ---------------------------------------------------------------------------
NEW_QAS = [
    (
        "When will student registration start?",
        "You will receive a notification and announcement on the portal once the registration starts. "
        "Please also check the Admission Schedule for the timetable. Stay tuned. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "I selected the wrong Applicant's 10th School Area at the time of registration. How can I change it now?",
        "Kindly withdraw the form and register again, as changes cannot be made. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "I selected the wrong Applicant's Status at the time of registration. How can I change it now?",
        "Kindly withdraw the form and register again, as changes cannot be made. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "I selected the wrong 10th Standard or Equivalent Examination Board at the time of registration. How can I change it now?",
        "Kindly withdraw the form and register again, as changes cannot be made. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "I entered wrong seat number at the time of registration. How can I change it now?",
        "Kindly withdraw the form and register again, as changes cannot be made. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "I selected the wrong month of examination or year of examination at the time of registration. How can I change it now?",
        "Kindly withdraw the form and register again, as changes cannot be made. "
        "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    ),
    (
        "Why am I unable to fill out Part 2?",
        "Please ensure that you have locked Part 1. Kindly refresh and check once."
    ),
    (
        "Why didn't I get admission even after filling the CAP option form when seats are available in my selected colleges?",
        "Please ensure that you have locked Part 2. Then, go to the CAP Allotment Status tab. "
        "Kindly check the reason for not being allotted by clicking on the \"Check Reason for Not Allotted\" button."
    ),
    (
        "Why am I unable to apply minority quota?",
        "Please ensure that you have selected yes to \"Do You belong to Minority?\" question on "
        "Category & Reservation Details screen in Part 1."
    ),
    (
        "Why am I unable to apply inhouse quota?",
        "Please ensure that you have selected \"Yes\" for the \"Do you want to take admission through the "
        "In-house Quota?\" question on the Category & Reservation Details screen in Part 1. "
        "Also, make sure that your school has an in-house college."
    ),
    (
        "How can I withdraw a form?",
        "To withdraw a form, please log in to your account and go to the application dashboard. "
        "Click on \"Withdraw Application\" from the left-side menu. Before withdrawing, make sure that "
        "Part 1 and Part 2 are unlocked. Then click on \"Withdraw Application Form.\""
    ),
    (
        "How can I confirm admission?",
        "Please log in to your account and go to the application dashboard. Click on \"CAP Allotment Status\" "
        "from the left-side menu. Upload all required documents, click \"Proceed for Admission\" to continue "
        "and visit the allotted college to take admission."
    ),
    (
        "How can I print allotment letter?",
        "Please log in to your account and go to the application dashboard. Click on \"CAP Allotment Status\" "
        "from the left-side menu and click on \"Print Allotment Letter\"."
    ),
    (
        "How can I print admission letter?",
        "Please log in to your account and go to the application dashboard. Make sure you are admitted, "
        "then click on \"CAP Allotment Status\" from the left-side menu and click on \"Print Admission Letter\"."
    ),
    (
        "How can I cancel admission?",
        "Make sure you are admitted, then visit the admitted college and cancel your admission."
    ),
]


def text_to_kb_line(text: str) -> str:
    """Collapse multi-line text to a single line using [BREAK] markers."""
    return text.strip().replace("\n", " [BREAK] ")


def load_refined_grievances(path: Path) -> list[str]:
    """
    Parse refined_grievances.txt.
    Entries are separated by lines containing only '---'.
    Each entry may span multiple lines (Q: ... A: ...).
    """
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r'\n\s*-{2,}\s*\n', content)
    entries = []
    for block in blocks:
        block = block.strip()
        if block:
            entries.append(text_to_kb_line(block))
    return entries


def load_faq(path: Path) -> list[str]:
    """
    Parse fyjc_faq_full.txt.
    Format: Q: … (newline) A: … (blank line) Q: …
    Group each Q+A pair into one entry.
    """
    content = path.read_text(encoding="utf-8")
    # Find every Q:…A: block
    pattern = re.compile(
        r'(Q:.*?A:.*?)(?=\nQ:|\Z)',
        re.DOTALL
    )
    entries = []
    for m in pattern.finditer(content):
        entry = text_to_kb_line(m.group(0))
        if entry:
            entries.append(entry)
    return entries


def main():
    output_lines: list[str] = []

    # --- Part 1: New Q&A ---
    for q, a in NEW_QAS:
        line = f"Q: {q} [BREAK] A: {a}"
        output_lines.append(line)
    print(f"[1] Added {len(NEW_QAS)} new Q&A entries.")

    # --- Part 2: Refined Grievances ---
    rg_path = BASE_DIR / "refined_grievances.txt"
    if rg_path.exists():
        rg_entries = load_refined_grievances(rg_path)
        output_lines.extend(rg_entries)
        print(f"[2] Added {len(rg_entries)} refined grievance entries.")
    else:
        print("[2] WARNING: refined_grievances.txt not found — skipped.")

    # --- Part 3: FAQ ---
    faq_path = BASE_DIR / "fyjc_faq_full.txt"
    if faq_path.exists():
        faq_entries = load_faq(faq_path)
        output_lines.extend(faq_entries)
        print(f"[3] Added {len(faq_entries)} FAQ entries.")
    else:
        print("[3] WARNING: fyjc_faq_full.txt not found — skipped.")

    # --- Write output ---
    kb_path = BASE_DIR / "knowledge_base.txt"
    with open(kb_path, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print(f"\n✅ knowledge_base.txt rebuilt with {len(output_lines)} total entries.")
    print(f"   File size: {kb_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
