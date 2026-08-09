"""
Evaluation Logger
Stores only metrics (no resume content) for research purposes.
"""

import csv
import os
from datetime import datetime
from typing import Dict, Optional

LOG_FILE = "evaluation_logs.csv"

# Header for the CSV
HEADERS = [
    "timestamp",
    "overall_score",
    "keyword_score",
    "structural_score",
    "rating",
    "attempts_used",
    "target_score",
    "target_reached",
    "original_text_length",
    "job_description_length"
]


def init_log_file():
    """Create the CSV file with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)


def log_evaluation(
    score_report: Dict,
    attempts_used: int,
    target_score: float,
    original_text_length: int = 0,
    job_description_length: int = 0
):
    """
    Append one evaluation result to the CSV.
    Only metrics are stored — no resume content.
    """
    init_log_file()

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        score_report.get("overall_score", ""),
        score_report.get("keyword_score", ""),
        score_report.get("structural_score", ""),
        score_report.get("rating", ""),
        attempts_used,
        target_score,
        score_report.get("overall_score", 0) >= target_score,
        original_text_length,
        job_description_length
    ]

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def get_all_logs() -> list:
    """Read all logged evaluations (for later analysis)."""
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)