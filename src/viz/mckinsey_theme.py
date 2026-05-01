from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.axes
import matplotlib.figure
import numpy as np
from cycler import cycler

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
BG_DARK        = "#0A1628"
GRID_COLOR     = "#1E3A5F"
TEXT_WHITE     = "#FFFFFF"
TEXT_DARK      = "#0A1628"
LINE_NOMINAL   = "#4FC3F7"
LINE_VOLUME    = "#4DB6AC"
LINE_REAL      = "#1A73E8"
LINE_TREND     = "#FFFFFF"
ANNOTATION_BG  = "#FFFFFF"
ANNOTATION_EDGE = "#FFFFFF"
ARROW_COLOR    = "#FFFFFF"
HIGHLIGHT      = "#FFD600"

DEFAULT_LINE_COLORS: list[str] = [
    LINE_NOMINAL,
    LINE_VOLUME,
    LINE_REAL,
    LINE_TREND,
    HIGHLIGHT,
]

# ---------------------------------------------------------------------------
# rcParams
# ---------------------------------------------------------------------------
MCKINSEY_RC: dict = {
    "figure.facecolor":       BG_DARK,
    "figure.figsize":         (14, 7),
    "figure.dpi":             150,
    "axes.facecolor":         BG_DARK,
    "axes.edgecolor":         GRID_COLOR,
    "axes.labelcolor":        TEXT_WHITE,
    "axes.titlecolor":        TEXT_WHITE,
    "axes.titlesize":         14,
    "axes.titleweight":       "bold",
    "axes.titlepad":          16,
    "axes.labelsize":         10,
    "axes.spines.top":        False,
    "axes.spines.right":      False,
    "axes.spines.left":       False,
    "axes.spines.bottom":     False,
    "axes.grid":              True,
    "axes.grid.axis":         "y",
    "grid.color":             GRID_COLOR,
    "grid.linestyle":         "--",
    "grid.linewidth":         0.6,
    "grid.alpha":             0.8,
    "lines.linewidth":        2.5,
    "lines.solid_capstyle":   "round",
    "xtick.color":            TEXT_WHITE,
    "ytick.color":            TEXT_WHITE,
    "xtick.labelsize":        9,
    "ytick.labelsize":        9,
    "xtick.major.size":       0,
    "ytick.major.size":       0,
    "xtick.bottom":           False,
    "legend.facecolor":       BG_DARK,
    "legend.edgecolor":       GRID_COLOR,
    "legend.labelcolor":      TEXT_WHITE,
    "legend.fontsize":        9,
    "legend.framealpha":      0.0,
    "font.family":            "sans-serif",
    "font.sans-serif":        ["Arial", "Helvetica Neue", "DejaVu Sans"],
    "text.color":             TEXT_WHITE,
    "savefig.facecolor":      BG_DARK,
    "savefig.bbox":           "tight",
    "savefig.dpi":            150,
}


# ---------------------------------------------------------------------------
# Theme application
# ---------------------------------------------------------------------------

def apply_mckinsey_theme() -> None:
    """Apply MCKINSEY_RC to matplotlib's global rcParams."""
    matplotlib.rcParams.update(MCKINSEY_RC)


@contextmanager
def mckinsey_style() -> Generator[None, None, None]:
    """Context manager: apply McKinsey theme, then restore original rcParams."""
    original = matplotlib.rcParams.copy()
    try:
        matplotlib.rcParams.update(MCKINSEY_RC)
        yield
    finally:
        matplotlib.rcParams.update(original)


def set_mckinsey_color_cycle(ax: matplotlib.axes.Axes) -> None:
    """Set the axes prop_cycle to the McKinsey line color sequence."""
    ax.set_prop_cycle(cycler(color=DEFAULT_LINE_COLORS))


# ---------------------------------------------------------------------------
# Figure factory
# ---------------------------------------------------------------------------

def create_mckinsey_figure(
    nrows: int = 1,
    ncols: int = 1,
    figsize: tuple[float, float] | None = None,
    title: str = "",
    subtitle: str = "",
) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes | np.ndarray]:
    """
    Create a Figure + Axes pre-configured with the McKinsey dark theme.

    Returns (fig, ax) for a single subplot, or (fig, axes_array) for multi-subplot.
    Applies facecolor explicitly to survive backend-specific rcParam quirks.
    """
    apply_mckinsey_theme()
    fs = figsize or MCKINSEY_RC["figure.figsize"]
    fig, axes = plt.subplots(nrows, ncols, figsize=fs)

    fig.patch.set_facecolor(BG_DARK)

    ax_list = [axes] if nrows * ncols == 1 else np.array(axes).flatten().tolist()
    for ax in ax_list:
        ax.set_facecolor(BG_DARK)
        for spine in ax.spines.values():
            spine.set_visible(False)
        set_mckinsey_color_cycle(ax)

    ax_first = ax_list[0]
    if title:
        ax_first.set_title(title, fontweight="bold", color=TEXT_WHITE, pad=16)
    if subtitle:
        ax_first.text(
            0, 1.04, subtitle,
            transform=ax_first.transAxes,
            color=TEXT_WHITE, fontsize=9, ha="left", va="bottom",
        )

    return fig, axes


# ---------------------------------------------------------------------------
# Annotation helpers
# ---------------------------------------------------------------------------

def add_oval_annotation(
    ax: matplotlib.axes.Axes,
    text: str,
    xy: tuple[float, float],
    xytext: tuple[float, float] | None = None,
    fontsize: int = 9,
    text_color: str = TEXT_DARK,
    bubble_color: str = ANNOTATION_BG,
    edge_color: str = ANNOTATION_EDGE,
    fontweight: str = "bold",
    zorder: int = 10,
) -> matplotlib.text.Annotation:
    """
    Draw a white oval callout bubble with dark text anchored to a data point.

    When xytext is None the bubble is placed directly at xy (no connector).
    When xytext differs from xy a thin white line connects them.
    """
    arrow_props = None
    if xytext is not None and xytext != xy:
        arrow_props = dict(arrowstyle="-", color=ARROW_COLOR, lw=1)

    ann = ax.annotate(
        text,
        xy=xy,
        xytext=xytext if xytext is not None else xy,
        fontsize=fontsize,
        fontweight=fontweight,
        color=text_color,
        ha="center",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor=bubble_color,
            edgecolor=edge_color,
            linewidth=1.5,
        ),
        arrowprops=arrow_props,
        zorder=zorder,
    )
    return ann


def add_end_label(
    ax: matplotlib.axes.Axes,
    text: str,
    x: float,
    y: float,
    color: str = TEXT_WHITE,
    fontsize: int = 9,
    fontweight: str = "bold",
    x_offset_frac: float = 0.01,
    ha: str = "left",
    va: str = "center",
    zorder: int = 9,
) -> matplotlib.text.Text:
    """
    Place a numeric label to the right of the last data point on a line.

    Call AFTER ax.set_xlim() so the fraction-to-data conversion is accurate.
    """
    x_range = ax.get_xlim()[1] - ax.get_xlim()[0]
    x_offset = x_offset_frac * x_range
    return ax.text(
        x + x_offset, y, text,
        color=color, fontsize=fontsize, fontweight=fontweight,
        ha=ha, va=va, zorder=zorder,
    )


def add_bracket_arrow(
    ax: matplotlib.axes.Axes,
    x: float,
    y_bottom: float,
    y_top: float,
    label: str = "",
    color: str = ARROW_COLOR,
    linewidth: float = 1.5,
    mutation_scale: float = 12,
    label_offset_frac: float = 0.015,
    fontsize: int = 8,
    fontweight: str = "bold",
    label_color: str = TEXT_WHITE,
    zorder: int = 8,
) -> None:
    """
    Draw a double-headed vertical arrow between y_bottom and y_top at x.

    Optionally places a text label at the midpoint to the right of the arrow.
    """
    ax.annotate(
        "",
        xy=(x, y_top),
        xytext=(x, y_bottom),
        arrowprops=dict(
            arrowstyle="<->",
            color=color,
            lw=linewidth,
            mutation_scale=mutation_scale,
        ),
        zorder=zorder,
    )
    if label:
        x_range = ax.get_xlim()[1] - ax.get_xlim()[0]
        x_label = x + label_offset_frac * x_range
        y_mid = (y_top + y_bottom) / 2
        ax.text(
            x_label, y_mid, label,
            color=label_color, fontsize=fontsize, fontweight=fontweight,
            ha="left", va="center", zorder=zorder,
        )
