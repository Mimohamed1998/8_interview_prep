# /mckinsey-viz — McKinsey Dark Blue Visualization Generator

## Role
When this command is invoked, generate **complete, runnable Python matplotlib code** that matches the McKinsey dark navy chart style. The output must be a self-contained `.py` script. Import from `src/viz/mckinsey_theme.py` when it exists in the project; otherwise inline the constants and helpers directly.

---

## Canonical Color Palette

```python
BG_DARK        = "#0A1628"   # figure + axes background
GRID_COLOR     = "#1E3A5F"   # dashed horizontal grid lines
TEXT_WHITE     = "#FFFFFF"   # titles, tick labels, legend
TEXT_DARK      = "#0A1628"   # text inside annotation bubbles
LINE_NOMINAL   = "#4FC3F7"   # light sky blue  — Nominal revenue / 1st series
LINE_VOLUME    = "#4DB6AC"   # teal/mint       — Volume / 2nd series
LINE_REAL      = "#1A73E8"   # medium blue     — Real revenue / 3rd series
LINE_TREND     = "#FFFFFF"   # white           — trend/projection diagonal
ANNOTATION_BG  = "#FFFFFF"   # oval callout bubble fill
ARROW_COLOR    = "#FFFFFF"   # bracket arrows
HIGHLIGHT      = "#FFD600"   # CAGR badge accent (e.g. "+5.3% p.a.")
```

---

## MCKINSEY_RC (rcParams reference)

```python
MCKINSEY_RC = {
    "figure.facecolor": "#0A1628", "figure.figsize": (14, 7), "figure.dpi": 150,
    "axes.facecolor": "#0A1628", "axes.edgecolor": "#1E3A5F",
    "axes.labelcolor": "#FFFFFF", "axes.titlecolor": "#FFFFFF",
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlepad": 16,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": "#1E3A5F", "grid.linestyle": "--", "grid.linewidth": 0.6,
    "lines.linewidth": 2.5, "lines.solid_capstyle": "round",
    "xtick.color": "#FFFFFF", "ytick.color": "#FFFFFF",
    "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.facecolor": "#0A1628", "legend.framealpha": 0.0,
    "legend.labelcolor": "#FFFFFF", "legend.fontsize": 9,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica Neue", "DejaVu Sans"],
    "text.color": "#FFFFFF",
    "savefig.facecolor": "#0A1628", "savefig.bbox": "tight", "savefig.dpi": 150,
}
```

---

## Generation Rules (follow every rule for every chart)

1. **Always** call `fig.patch.set_facecolor("#0A1628")` and `ax.set_facecolor("#0A1628")` explicitly — some backends ignore the rcParam.
2. **Always** hide spines imperatively: `for s in ax.spines.values(): s.set_visible(False)`
3. **Always** call `ax.set_xlim(...)` with right-side padding (≥10% beyond the last x value) **before** placing end-of-line labels, so label offsets compute correctly.
4. **Bold white title**: `ax.set_title("...", fontweight="bold", color="#FFFFFF")`
5. **Legend inside axes, top-left**: `ax.legend(loc="upper left", framealpha=0.0, handlelength=2.0)`
6. **Save**: `plt.savefig("output.png", bbox_inches="tight", facecolor=fig.get_facecolor())`
7. Use `linestyle="--"` for any forecast or projection segment of a line.
8. End-of-line numeric labels: place them to the right of the last data point in bold white using `ax.text(x + offset, y, "123.1", fontweight="bold", color="#FFFFFF", ha="left", va="center")`.
9. Oval callout bubbles: use `ax.annotate()` with `bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#FFFFFF", linewidth=1.5)` and dark text color `#0A1628`.
10. Bracket arrows (showing gap between two lines): use `ax.annotate("", xy=(x, y_top), xytext=(x, y_bottom), arrowprops=dict(arrowstyle="<->", color="#FFFFFF", lw=1.5, mutation_scale=12))`.
11. If the user provides a **data path or DataFrame**: read with pandas, explicitly state any column-name assumptions in a comment at the top of the script.
12. If the user provides **no data**: generate a realistic inline example dataset that matches the requested chart type.
13. Color series in the order: `LINE_NOMINAL → LINE_VOLUME → LINE_REAL → LINE_TREND → HIGHLIGHT`. If the chart has fewer series, use the first N colors in that order.

---

## Available Helper Functions (from `src/viz/mckinsey_theme.py`)

```python
from src.viz.mckinsey_theme import (
    create_mckinsey_figure,    # (nrows, ncols, figsize, title, subtitle) → (fig, ax)
    set_mckinsey_color_cycle,  # (ax) → None
    add_oval_annotation,       # (ax, text, xy, xytext, fontsize, ...) → Annotation
    add_end_label,             # (ax, text, x, y, color, x_offset_frac, ...) → Text
    add_bracket_arrow,         # (ax, x, y_bottom, y_top, label, ...) → None
)
```

---

## Minimal Template (adapt this for every chart)

```python
import matplotlib.pyplot as plt
import matplotlib
from src.viz.mckinsey_theme import (
    MCKINSEY_RC, BG_DARK, TEXT_WHITE, TEXT_DARK,
    LINE_NOMINAL, LINE_VOLUME, LINE_REAL, ARROW_COLOR, HIGHLIGHT,
    create_mckinsey_figure, add_oval_annotation, add_end_label, add_bracket_arrow,
)

# --- Data ---
years = [2019, 2020, 2021, 2022, 2023]
nominal = [100, 104, 110, 114, 123.1]
volume  = [100, 109, 107, 103, 100.3]

# --- Figure ---
fig, ax = create_mckinsey_figure(
    title="Despite high inflation, most was passed to consumers",
    subtitle="Grocery retail market development | Indexed (2019 = 100%)",
)
ax.plot(years, nominal, color=LINE_NOMINAL, label="Nominal revenue", zorder=5)
ax.plot(years, volume,  color=LINE_VOLUME,  label="Volume",           zorder=5)

# --- Axis limits (set BEFORE end labels) ---
ax.set_xlim(2019, 2024.5)
ax.set_ylim(95, 128)

# --- End-of-line labels ---
add_end_label(ax, "123.1", years[-1], nominal[-1])
add_end_label(ax, "100.3", years[-1], volume[-1])

# --- Bracket arrow showing inflation gap ---
add_bracket_arrow(ax, x=2023.6, y_bottom=100.3, y_top=123.1, label="22.9")

# --- Legend ---
ax.legend(loc="upper left", framealpha=0.0, handlelength=2.0)

# --- Save ---
plt.tight_layout()
plt.savefig("output.png", bbox_inches="tight", facecolor=fig.get_facecolor())
plt.show()
```
