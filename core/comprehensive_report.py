"""
Comprehensive colored analysis report for Creator Access.
Includes statistics, pie/bar charts, and error-memory tables.
(No 3-D brain snapshot)
"""

from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.error_memory import load_memory, memory_stats
from core.evaluation_logger import get_all_logs

sns.set_theme(style="whitegrid", palette="muted")


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _safe_df() -> pd.DataFrame:
    logs = get_all_logs()
    if not logs:
        return pd.DataFrame()

    df = pd.DataFrame(logs)
    for col in [
        "overall_score",
        "keyword_score",
        "structural_score",
        "attempts_used",
        "target_score",
        "original_text_length",
        "job_description_length",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "target_reached" in df.columns:
        df["target_reached"] = (
            df["target_reached"].astype(str).str.lower().isin(["true", "1", "yes"])
        )
    return df


def _stats_block(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {}
    return {
        "n": len(df),
        "avg_overall": float(df["overall_score"].mean()),
        "median_overall": float(df["overall_score"].median()),
        "avg_keyword": float(df["keyword_score"].mean()),
        "avg_structure": float(df["structural_score"].mean()),
        "avg_attempts": float(df["attempts_used"].mean()),
        "reach_rate": float(df["target_reached"].mean()) if "target_reached" in df.columns else None,
        "reach_true": int(df["target_reached"].sum()) if "target_reached" in df.columns else 0,
        "reach_false": int((~df["target_reached"]).sum()) if "target_reached" in df.columns else 0,
    }


def _chart_score_hist(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(df["overall_score"].dropna(), bins=12, kde=True, color="#2563EB", ax=ax)
    ax.set_title("Overall Score Distribution", fontsize=13, fontweight="bold", color="#0F172A")
    ax.set_xlabel("Overall Score")
    ax.set_ylabel("Count")
    return _fig_to_base64(fig)


def _chart_keyword_structure(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    if "rating" in df.columns:
        sns.scatterplot(
            data=df,
            x="keyword_score",
            y="structural_score",
            hue="rating",
            ax=ax,
            s=70,
        )
    else:
        sns.scatterplot(
            data=df,
            x="keyword_score",
            y="structural_score",
            ax=ax,
            s=70,
            color="#2563EB",
        )
    ax.set_title("Keyword vs Structure Score", fontsize=13, fontweight="bold", color="#0F172A")
    ax.set_xlabel("Keyword Match %")
    ax.set_ylabel("Structure Score")
    return _fig_to_base64(fig)


def _chart_attempts(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    sns.countplot(data=df, x="attempts_used", color="#2563EB", ax=ax)
    ax.set_title("Attempts Used per Run", fontsize=13, fontweight="bold", color="#0F172A")
    ax.set_xlabel("Attempts")
    ax.set_ylabel("Count")
    return _fig_to_base64(fig)


def _chart_target_pie(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    if "target_reached" not in df.columns:
        ax.text(0.5, 0.5, "No target data", ha="center")
        return _fig_to_base64(fig)

    counts = df["target_reached"].value_counts()
    labels = ["Reached" if bool(i) else "Not reached" for i in counts.index]
    colors = ["#16A34A", "#DC2626"]
    ax.pie(
        counts.values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[: len(counts)],
        textprops={"fontsize": 11},
    )
    ax.set_title("Target Reach Rate", fontsize=13, fontweight="bold", color="#0F172A")
    return _fig_to_base64(fig)


def _chart_target_by_threshold(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    if "target_score" not in df.columns or "target_reached" not in df.columns:
        ax.text(0.5, 0.5, "No target threshold data", ha="center")
        return _fig_to_base64(fig)

    tmp = df.copy()
    tmp["target_score"] = tmp["target_score"].round(0)
    rate = tmp.groupby("target_score")["target_reached"].mean().reset_index()
    sns.barplot(data=rate, x="target_score", y="target_reached", color="#0EA5E9", ax=ax)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Reach rate")
    ax.set_xlabel("Target score")
    ax.set_title("Reach Rate by Target Threshold", fontsize=13, fontweight="bold", color="#0F172A")
    return _fig_to_base64(fig)


def _chart_rating_pie(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    if "rating" not in df.columns:
        ax.text(0.5, 0.5, "No rating data", ha="center")
        return _fig_to_base64(fig)

    counts = df["rating"].value_counts()
    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=sns.color_palette("pastel")[: len(counts)],
        textprops={"fontsize": 11},
    )
    ax.set_title("Rating Distribution", fontsize=13, fontweight="bold", color="#0F172A")
    return _fig_to_base64(fig)


def _chart_error_memory_bars() -> Tuple[str, List[Dict[str, Any]]]:
    data = load_memory()
    learned = [p for p in data.get("patterns", []) if not p.get("seed")]
    if not learned:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.text(0.5, 0.5, "No learned patterns yet", ha="center")
        return _fig_to_base64(fig), []

    dfp = pd.DataFrame(learned)
    dfp["times_seen"] = pd.to_numeric(dfp["times_seen"], errors="coerce").fillna(0)
    dfp["success_rate"] = pd.to_numeric(dfp["success_rate"], errors="coerce").fillna(0)
    dfp["avg_score_gain"] = pd.to_numeric(dfp["avg_score_gain"], errors="coerce").fillna(0)
    dfp = dfp.sort_values("times_seen", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=dfp, x="error_code", y="times_seen", color="#2563EB", ax=ax)
    ax.set_title("Learned Error Patterns by Frequency", fontsize=13, fontweight="bold", color="#0F172A")
    ax.set_xlabel("Error code")
    ax.set_ylabel("Times seen")
    ax.tick_params(axis="x", rotation=25)
    return _fig_to_base64(fig), dfp.to_dict(orient="records")


def build_comprehensive_html_report() -> bytes:
    df = _safe_df()
    stats = _stats_block(df)
    mem = memory_stats()
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if df.empty:
        html = (
            "<!DOCTYPE html><html><body style='font-family:Arial'>"
            "<h1>Resume ATS Optimizer — Analysis Report</h1>"
            f"<p>Generated: {generated}</p>"
            "<p>No evaluation logs found.</p>"
            "</body></html>"
        )
        return html.encode("utf-8")

    img_hist = _chart_score_hist(df)
    img_scatter = _chart_keyword_structure(df)
    img_attempts = _chart_attempts(df)
    img_target_pie = _chart_target_pie(df)
    img_target_bar = _chart_target_by_threshold(df)
    img_rating = _chart_rating_pie(df)
    img_errors, learned_rows = _chart_error_memory_bars()

    reach_rate = stats.get("reach_rate")
    reach_pct = f"{reach_rate * 100:.1f}%" if reach_rate is not None else "n/a"

    learned_table = ""
    for r in learned_rows:
        learned_table += (
            "<tr>"
            f"<td>{r.get('error_code', '')}</td>"
            f"<td>{r.get('times_seen', '')}</td>"
            f"<td>{float(r.get('success_rate') or 0):.2f}</td>"
            f"<td>{float(r.get('avg_score_gain') or 0):.2f}</td>"
            "</tr>"
        )

    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Resume ATS Optimizer — Comprehensive Analysis Report</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; color: #0F172A; background: #F8FAFC; margin: 0; padding: 24px; }
    .wrap { max-width: 1000px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 28px; }
    h1 { color: #0F172A; margin-bottom: 6px; }
    h2 { color: #1E3A8A; margin-top: 28px; }
    .sub { color: #64748B; margin-bottom: 18px; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0 8px; }
    .card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; text-align: center; }
    .card .v { font-size: 22px; font-weight: 700; color: #2563EB; }
    .card .l { font-size: 12px; color: #64748B; margin-top: 4px; }
    img { margin: 10px 0 18px; border-radius: 10px; border: 1px solid #E2E8F0; max-width: 100%; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #E2E8F0; padding: 8px 10px; text-align: left; font-size: 13px; }
    th { background: #EFF6FF; }
    .footer { margin-top: 28px; color: #64748B; font-size: 12px; border-top: 1px solid #E2E8F0; padding-top: 12px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Resume ATS Optimizer</h1>
    <div class="sub">Comprehensive Analysis Report · Generated __GENERATED__</div>

    <h2>1. Executive Statistics</h2>
    <div class="grid">
      <div class="card"><div class="v">__N__</div><div class="l">Completed Runs</div></div>
      <div class="card"><div class="v">__AVG_OVERALL__</div><div class="l">Avg Overall Score</div></div>
      <div class="card"><div class="v">__AVG_KEYWORD__</div><div class="l">Avg Keyword Match</div></div>
      <div class="card"><div class="v">__REACH_PCT__</div><div class="l">Target Reach Rate</div></div>
    </div>
    <div class="grid">
      <div class="card"><div class="v">__MEDIAN__</div><div class="l">Median Overall</div></div>
      <div class="card"><div class="v">__AVG_STRUCT__</div><div class="l">Avg Structure</div></div>
      <div class="card"><div class="v">__AVG_ATTEMPTS__</div><div class="l">Avg Attempts</div></div>
      <div class="card"><div class="v">__REACH_TF__</div><div class="l">Reached / Not</div></div>
    </div>

    <h2>2. Score & Attempt Charts</h2>
    <img src="data:image/png;base64,__IMG_HIST__" />
    <img src="data:image/png;base64,__IMG_SCATTER__" />
    <img src="data:image/png;base64,__IMG_ATTEMPTS__" />

    <h2>3. Target & Rating Breakdown</h2>
    <img src="data:image/png;base64,__IMG_TARGET_PIE__" />
    <img src="data:image/png;base64,__IMG_TARGET_BAR__" />
    <img src="data:image/png;base64,__IMG_RATING__" />

    <h2>4. Error Memory Patterns</h2>
    <p>Learned patterns in memory: <b>__LEARNED__</b> |
       Seed patterns: <b>__SEED__</b> |
       Chroma enabled: <b>__CHROMA__</b></p>
    <img src="data:image/png;base64,__IMG_ERRORS__" />
    <table>
      <thead>
        <tr><th>Error Code</th><th>Times Seen</th><th>Success Rate</th><th>Avg Score Gain</th></tr>
      </thead>
      <tbody>
        __LEARNED_TABLE__
      </tbody>
    </table>

    <h2>5. Notes</h2>
    <ul>
      <li>This report uses metrics and anonymized error patterns only.</li>
      <li>No resume text or personal identifiers are included.</li>
      <li>Target reach depends on selected threshold (e.g., 75 vs 90).</li>
      <li>Interactive 3-D Error Memory Brain remains available in Creator Access.</li>
    </ul>

    <div class="footer">
      Resume ATS Optimizer · Privacy-aware evaluation report · __GENERATED__
    </div>
  </div>
</body>
</html>
"""

    html = (
        html.replace("__GENERATED__", generated)
        .replace("__N__", str(stats["n"]))
        .replace("__AVG_OVERALL__", f"{stats['avg_overall']:.1f}")
        .replace("__AVG_KEYWORD__", f"{stats['avg_keyword']:.1f}%")
        .replace("__REACH_PCT__", reach_pct)
        .replace("__MEDIAN__", f"{stats['median_overall']:.1f}")
        .replace("__AVG_STRUCT__", f"{stats['avg_structure']:.1f}")
        .replace("__AVG_ATTEMPTS__", f"{stats['avg_attempts']:.2f}")
        .replace("__REACH_TF__", f"{stats.get('reach_true', 0)} / {stats.get('reach_false', 0)}")
        .replace("__IMG_HIST__", img_hist)
        .replace("__IMG_SCATTER__", img_scatter)
        .replace("__IMG_ATTEMPTS__", img_attempts)
        .replace("__IMG_TARGET_PIE__", img_target_pie)
        .replace("__IMG_TARGET_BAR__", img_target_bar)
        .replace("__IMG_RATING__", img_rating)
        .replace("__LEARNED__", str(mem.get("learned_patterns", 0)))
        .replace("__SEED__", str(mem.get("seed_patterns", 0)))
        .replace("__CHROMA__", str(mem.get("chroma_enabled", False)))
        .replace("__IMG_ERRORS__", img_errors)
        .replace("__LEARNED_TABLE__", learned_table)
    )

    return html.encode("utf-8")