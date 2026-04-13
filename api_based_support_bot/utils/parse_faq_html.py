"""
parse_faq_html.py
Parses the official FAQ HTML and writes all Q&A pairs to fyjc_faq_full.txt
"""

from bs4 import BeautifulSoup
from pathlib import Path

HTML_FILE = Path(__file__).parent / "faq_source.html"
OUT_FILE  = Path(__file__).parent / "fyjc_faq_full.txt"

html = HTML_FILE.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

accordions = soup.select(".MuiAccordion-root")

entries = []
for acc in accordions:
    # Question text
    q_el = acc.select_one(".MuiAccordionSummary-content p")
    # Answer text (all <li> inside the details region)
    a_els = acc.select(".MuiAccordionDetails-root li")

    if not q_el:
        continue

    q = q_el.get_text(separator=" ", strip=True)
    # Remove leading "प्र.X)" pattern for cleaner text
    a_parts = [li.get_text(separator=" ", strip=True) for li in a_els if li.get_text(strip=True)]
    a = " ".join(a_parts)

    if q and a:
        entries.append(f"Q: {q}\nA: {a}")

output = "\n\n".join(entries)
OUT_FILE.write_text(output, encoding="utf-8")
print(f"✅ Extracted {len(entries)} FAQ entries → {OUT_FILE}")
print("\nFirst 3 entries preview:")
for e in entries[:3]:
    print("---")
    print(e[:200])
