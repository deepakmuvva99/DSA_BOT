"""
Cloud runner for Render scheduled execution.

Supports two tracker sources:
1) TRACKER_XLSX_URL (recommended for phone+laptop updates through cloud storage)
2) Local DSA_Master_Tracker.xlsx (fallback for local/manual runs)
"""

import os
import tempfile
from datetime import datetime

import requests

from ai_coach import DSAPreparationCoach
from telegram_notifier import TelegramNotifier


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_TRACKER_FILE = os.path.join(BASE_DIR, "DSA_Master_Tracker.xlsx")


def _normalize_tracker_url(url: str) -> str:
    """
    Accept normal Google Sheets share URLs and convert to direct xlsx export URL.
    """
    cleaned = url.strip()

    # Google Sheets browser URL -> direct xlsx export URL
    # Example: https://docs.google.com/spreadsheets/d/<ID>/edit?... -> /export?format=xlsx
    if "docs.google.com/spreadsheets/d/" in cleaned and "/export?" not in cleaned:
        parts = cleaned.split("/spreadsheets/d/", 1)[1]
        sheet_id = parts.split("/", 1)[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    return cleaned


def _get_env(name: str, required: bool = True) -> str:
    value = os.getenv(name, "").strip()
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _resolve_tracker_path() -> str:
    tracker_url = os.getenv("TRACKER_XLSX_URL", "").strip()
    if not tracker_url:
        if not os.path.exists(LOCAL_TRACKER_FILE):
            raise FileNotFoundError(
                "Tracker not found. Set TRACKER_XLSX_URL or provide local DSA_Master_Tracker.xlsx."
            )
        return LOCAL_TRACKER_FILE

    resolved_url = _normalize_tracker_url(tracker_url)
    response = requests.get(resolved_url, timeout=30)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name


def run_daily_job() -> None:
    bot_token = _get_env("TELEGRAM_BOT_TOKEN")
    chat_id = _get_env("TELEGRAM_CHAT_ID")

    tracker_path = _resolve_tracker_path()
    print(f"Running daily cloud job at {datetime.now().isoformat()}")

    coach = DSAPreparationCoach(tracker_path)
    daily_plan = coach.generate_daily_plan()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as plan_file:
        coach.save_daily_plan(daily_plan, plan_file.name)
        plan_path = plan_file.name

    notifier = TelegramNotifier(bot_token, chat_id)
    success = notifier.send_daily_plan(plan_path)

    if not success:
        raise RuntimeError("Failed to send Telegram daily plan notification.")

    print("Cloud job completed successfully.")


def run_weekly_review_job() -> None:
    bot_token = _get_env("TELEGRAM_BOT_TOKEN")
    chat_id = _get_env("TELEGRAM_CHAT_ID")

    tracker_path = _resolve_tracker_path()
    print(f"Running weekly review job at {datetime.now().isoformat()}")

    coach = DSAPreparationCoach(tracker_path)
    report = coach.get_weekly_analytics()
    exam = coach.generate_weekly_exam(question_count=8)

    report_text = coach.format_weekly_report(report)
    exam_text = coach.format_weekly_exam(exam)

    notifier = TelegramNotifier(bot_token, chat_id)
    ok_report = notifier.send_message(report_text)
    ok_exam = notifier.send_message(exam_text)

    if not (ok_report and ok_exam):
        raise RuntimeError("Failed to send weekly report and/or weekly exam.")

    print("Weekly review job completed successfully.")


if __name__ == "__main__":
    run_mode = os.getenv("RUN_MODE", "daily").strip().lower()
    if run_mode == "weekly":
        run_weekly_review_job()
    else:
        run_daily_job()
