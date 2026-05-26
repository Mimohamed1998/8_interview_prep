"""
Build h1_analysis.ipynb via nbformat — clean ASCII cells only.
"""
import nbformat
from pathlib import Path

BASE   = Path(
    "/Users/mohamedinas/Desktop/SE_projects"
    "/9_fathima_stat_support/version_v1/8_interview_prep"
)
OUT_NB = BASE / "pipelines/eda_research_proposals/h1_analysis.ipynb"

nb     = nbformat.v4.new_notebook()
cells  = []

# Cell 0 — title
cells.append(nbformat.v4.new_markdown_cell(
    "# H1 Analysis: AI Preparedness -> Sustainability Performance\n\n"
    "**H1:** AI preparedness has a positive impact on sustainability performance.  \n"
    "**H0:** beta1 <= 0 (one-tailed, alpha=.05)  \n"
    "**Selected model:** Fixed Effects (Two-Way) per RQ1 Hausman test (chi2=209.66, p<.001)"
))

# Cells 1-11: load run_h1_analysis.py content as individual cells split by '# ──'
script = (BASE / "pipelines/eda_research_proposals/run_h1_analysis.py").read_text()

# Split at the section headers but keep them together with their code
import re
sections = re.split(r'\n(?=# ── \d+\.)', script)

# First section is the docstring + imports
cells.append(nbformat.v4.new_code_cell(sections[0].strip()))
for sec in sections[1:]:
    cells.append(nbformat.v4.new_code_cell(sec.strip()))

nb.cells = cells
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nbformat.write(nb, str(OUT_NB))
print(f"Notebook written: {OUT_NB}")
print(f"Total cells: {len(nb.cells)}")
