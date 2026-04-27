#!/usr/bin/env python3
"""Convert behavioraudit.md to behavioraudit_body.tex for MDPI Education Sciences."""
import re

INPUT = "behavioraudit.md"
OUTPUT = "behavioraudit_body.tex"

def read_md():
    with open(INPUT, "r") as f:
        return f.read()

# ── Citation mapping ──────────────────────────────────────────────────────
# Maps "display text as it appears in markdown" → "bibtex key"
# We'll handle both \citet (textual) and \citep (parenthetical) patterns.

def convert_citations(text):
    """Convert author-year markdown citations to natbib commands."""

    # ── Multi-citation parenthetical: (A; B; C) ──
    # e.g. "(Northcutt et al., 2021; Recht et al., 2019; Bouthillier et al., 2021)"
    multi_parens = [
        (r'\(Northcutt et al\., 2021; Recht et al\., 2019; Bouthillier et al\., 2021\)',
         r'\\citep{Northcutt2021,Recht2019,Bouthillier2021}'),
        (r'\(Chejara et al\., 2023, 2024\)',
         r'\\citep{Chejara2023,Chejara2024}'),
        (r'\(Zheng et al\., 2023; Wang et al\., 2023; Huang et al\., 2024\)',
         r'\\citep{Zheng2023,Wang2024,Huang2024llm}'),
        (r'\(Messick, 1995; Kane, 2006\)',
         r'\\citep{Messick1995,Kane2006}'),
    ]
    for pat, repl in multi_parens:
        text = re.sub(pat, repl, text)

    # ── Special patterns ──
    # "(G-theory; Brennan, 2001)" → (G-theory; \citealt{Brennan2001})
    text = re.sub(
        r'\(G-theory; Brennan, 2001\)',
        r'(G-theory; \\citealt{Brennan2001})',
        text
    )
    # "Datasheets for Datasets (Gebru et al., 2021)" → textual with citep
    # "data-cascade critiques (Sambasivan et al., 2021)" → same
    # These are parenthetical already — handled by single-cite below.

    # "Messick-style (1995)" → Messick-style \\citep{Messick1995}
    text = re.sub(
        r'Messick-style \(1995\)',
        r'\\citet{Messick1995}-style',
        text
    )

    # ── Textual citations: "Author et al. (Year)" → \citet{key} ──
    textual = [
        (r'Northcutt et al\. \(2021\)', 'Northcutt2021'),
        (r'Recht et al\. \(2019\)', 'Recht2019'),
        (r'Bouthillier et al\. \(2021\)', 'Bouthillier2021'),
        (r'Baker and Inventado \(2014\)', 'Baker2014'),
        (r'Gardner et al\. \(2019\)', 'Gardner2019'),
    ]
    for pat, key in textual:
        text = re.sub(pat, rf'\\citet{{{key}}}', text)

    # ── Single parenthetical citations: "(Author et al., Year)" → \citep{key} ──
    single_parens = {
        'Northcutt et al., 2021': 'Northcutt2021',
        'Recht et al., 2019': 'Recht2019',
        'Bouthillier et al., 2021': 'Bouthillier2021',
        'Romero and Ventura, 2020': 'Romero2020',
        'Gebru et al., 2021': 'Gebru2021',
        'Sambasivan et al., 2021': 'Sambasivan2021',
        'Zheng et al., 2023': 'Zheng2023',
        'Wang et al., 2023': 'Wang2024',
        'Huang et al., 2024': 'Huang2024llm',
        'Ioannidis, 2005': 'Ioannidis2005',
        'Mitchell et al., 2019': 'Mitchell2019',
        'Holland et al., 2020': 'Holland2020',
        'Brennan, 2001': 'Brennan2001',
        'Messick, 1995': 'Messick1995',
        'Kane, 2006': 'Kane2006',
        'Huang et al., 2025': 'Huang2025',
        'Cortez and Silva, 2008': 'Cortez2008',
        'Kuzilek et al., 2017': 'Kuzilek2017',
        'Amrieh et al., 2016': 'Amrieh2016',
        'Bora and Dey, 2021': 'Bora2021',
        'Realinho et al., 2022': 'Realinho2022',
        'Yilmaz and Sekeroglu, 2020': 'Yilmaz2020',
        'Chejara et al., 2023': 'Chejara2023',
        'Chejara et al., 2024': 'Chejara2024',
    }
    for display, key in single_parens.items():
        # Match "(Display Text)" but not already converted
        escaped = re.escape(display)
        text = re.sub(rf'\({escaped}\)', rf'\\citep{{{key}}}', text)

    # ── Table footnote citations (no parens): "Author et al., Year" → \citealt{key} ──
    # These appear in table footnotes without parentheses
    footnote_cites = {
        'Huang et al., 2025': 'Huang2025',
        'Cortez and Silva, 2008': 'Cortez2008',
        'Kuzilek et al., 2017': 'Kuzilek2017',
        'Amrieh et al., 2016': 'Amrieh2016',
        'Bora and Dey, 2021': 'Bora2021',
        'Realinho et al., 2022': 'Realinho2022',
        'Yilmaz and Sekeroglu, 2020': 'Yilmaz2020',
    }
    for display, key in footnote_cites.items():
        escaped = re.escape(display)
        # Only replace bare citations not already inside \cite commands
        text = re.sub(rf'(?<!\\citealt\{{){escaped}',
                      rf'\\citealt{{{key}}}', text)

    return text


def convert_sections(text):
    """Convert markdown headers to LaTeX sections."""
    # ### Subsection → \subsection{}
    text = re.sub(r'^### (.+)$', r'\\subsection{\1}', text, flags=re.MULTILINE)
    # ## Section → \section{}
    text = re.sub(r'^## (.+)$', r'\\section{\1}', text, flags=re.MULTILINE)
    return text


def convert_bold_italic(text):
    """Convert **bold** and *italic* outside of LaTeX environments."""
    # Bold: **text** → \textbf{text}
    # Be careful not to match inside LaTeX commands
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    # Italic: *text* → \textit{text}
    # Only match single * not preceded/followed by another *
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
    return text


def convert_enumerate(text):
    """Convert markdown numbered lists to LaTeX enumerate.

    Handles blank lines between numbered items by looking ahead to see if
    the next non-blank line is also a numbered item.
    """
    lines = text.split('\n')
    result = []
    in_list = False
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()
        is_item = bool(re.match(r'^\d+\.\s', stripped))

        if is_item and not in_list:
            in_list = True
            result.append('\\begin{enumerate}')
            content = re.sub(r'^\d+\.\s+', '', stripped)
            result.append(f'\\item {content}')
        elif is_item and in_list:
            content = re.sub(r'^\d+\.\s+', '', stripped)
            result.append(f'\\item {content}')
        elif not is_item and in_list:
            # Check if there's a numbered item coming after blank lines
            j = i
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and re.match(r'^\d+\.\s', lines[j].strip()):
                # Skip blank lines; next item is coming
                i = j
                continue
            else:
                in_list = False
                result.append('\\end{enumerate}')
                result.append(lines[i])
        else:
            result.append(lines[i])
        i += 1

    if in_list:
        result.append('\\end{enumerate}')

    return '\n'.join(result)


def convert_special_chars(text):
    """Handle special LaTeX characters in prose text (not inside LaTeX environments)."""
    # Fix .png references to .pdf for figures
    text = text.replace(
        'figure1_radar_audit_profiles.png',
        'figure1_radar_audit_profiles.pdf'
    )
    text = text.replace(
        'figure2_iid_vs_group_holdout.png',
        'figure2_iid_vs_group_holdout.pdf'
    )
    text = text.replace(
        'figure3_instability_strip.png',
        'figure3_instability_strip.pdf'
    )

    # Convert Unicode special characters to LaTeX equivalents
    text = text.replace('—', '---')      # em-dash
    text = text.replace('–', '--')       # en-dash
    text = text.replace('→', '$\\to$')   # arrow
    text = text.replace('\u2009', '\\,')  # thin space (if any)

    return text


def build_backmatter():
    """Generate MDPI back matter commands."""
    return r"""
\authorcontributions{Conceptualization, Y.M. and L.Z.; methodology, Y.M.; software, Y.M.; validation, Y.M. and L.Z.; formal analysis, Y.M.; investigation, Y.M.; data curation, Y.M.; visualization, Y.M.; writing---original draft preparation, Y.M.; writing---review and editing, Y.M. and L.Z.; supervision, L.Z. All authors have read and agreed to the published version of the manuscript.}

\funding{This research received no external funding.}

\institutionalreview{According to the institutional policy governing secondary analysis of existing public datasets at Hunan Agricultural University, ethical review and approval were waived for this study because it used existing public dataset releases, involved no direct interaction with human participants, and analyzed no newly collected personal data.}

\informedconsent{Not applicable.}

\dataavailability{All seven datasets are publicly available from their original maintainers. The audit protocol implementation and analysis scripts are available at \url{https://github.com/zhanglizhuo/BehaviorAudit}.}

\acknowledgments{The authors thank the teams behind the seven audited datasets for their commitment to open data.}

\conflictsofinterest{The authors declare no conflicts of interest.}

\abbreviations{Abbreviations}{
The following abbreviations are used in this manuscript:\\

\noindent
\begin{tabular}{@{}ll}
MM-TBA & Multi-Modal Dataset for Teacher Behavior Analysis\\
OULAD & Open University Learning Analytics Dataset\\
MAE & Mean Absolute Error\\
EDM & Educational Data Mining\\
RF & Random Forest\\
GBT & Gradient Boosting\\
\end{tabular}
}
"""


def main():
    md = read_md()

    # ── Extract body: skip front matter (Title, Abstract, Keywords) and References ──
    # Find where Introduction starts
    intro_match = re.search(r'^## Introduction', md, re.MULTILINE)
    if not intro_match:
        raise ValueError("Cannot find ## Introduction")

    # Find where References starts
    ref_match = re.search(r'^## References', md, re.MULTILINE)
    if not ref_match:
        raise ValueError("Cannot find ## References")

    # Also find sections after Conclusion that are back matter
    backmatter_sections = [
        '## Data Availability Statement',
        '## Author Contributions',
        '## Funding',
        '## Institutional Review Board Statement',
        '## Informed Consent Statement',
        '## Conflicts of Interest',
        '## Acknowledgments',
        '## Abbreviations',
    ]

    # Find the first back matter section
    backmatter_start = None
    for sec in backmatter_sections:
        m = re.search(re.escape(sec), md)
        if m:
            if backmatter_start is None or m.start() < backmatter_start:
                backmatter_start = m.start()

    # Body is from Introduction to either first backmatter section or References
    end_pos = min(p for p in [backmatter_start, ref_match.start()] if p is not None)
    body = md[intro_match.start():end_pos].strip()

    # ── Apply transformations ──
    body = convert_citations(body)
    body = convert_sections(body)
    body = convert_bold_italic(body)
    body = convert_enumerate(body)
    body = convert_special_chars(body)

    # ── Post-processing ──
    # Remove any double blank lines → single blank line
    body = re.sub(r'\n{3,}', '\n\n', body)

    # ── Add bibliography and back matter ──
    backmatter = build_backmatter()

    full_tex = body + "\n\n" + backmatter.strip() + "\n\n"
    full_tex += r"\bibliography{behavioraudit}" + "\n"

    with open(OUTPUT, "w") as f:
        f.write(full_tex)

    print(f"Wrote {OUTPUT} ({len(full_tex)} chars, {full_tex.count(chr(10))} lines)")

    # Verify all citations were converted
    remaining = re.findall(r'\([A-Z][a-z]+ (?:et al\.|and [A-Z])[^)]*\d{4}\)', full_tex)
    if remaining:
        print(f"WARNING: Possible unconverted citations: {remaining}")
    else:
        print("All citations appear converted.")

    # Check for remaining markdown
    md_headers = re.findall(r'^#{1,3} ', full_tex, re.MULTILINE)
    if md_headers:
        print(f"WARNING: Remaining markdown headers: {md_headers}")

    md_bold = re.findall(r'\*\*[^*]+\*\*', full_tex)
    if md_bold:
        print(f"WARNING: Remaining markdown bold: {md_bold[:5]}")


if __name__ == "__main__":
    main()
