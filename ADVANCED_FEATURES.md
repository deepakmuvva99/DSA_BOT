# Advanced Features Setup

## Included Enhancements

1. Smart revision engine (1d, 7d, 30d) with low-accuracy and low-confidence prioritization.
2. Weekly analytics report (Sunday).
3. Sunday exam set at 2:00 PM IST with midnight deadline reminder in message.
4. Confidence tagging support via `Confidence (1-5)` column (auto-defaults to 3 if missing).
5. Monthly question bank expansion pipeline.
6. Streamlit dashboard for progress visualization.

## GitHub Actions Workflows

- Daily plan at 9:00 AM IST:
  - `.github/workflows/daily-reminder.yml`
- Weekly analytics + Sunday exam at 2:00 PM IST:
  - `.github/workflows/weekly-review-exam.yml`
- Monthly question import (1st day, 10:00 AM IST):
  - `.github/workflows/monthly-question-bank-import.yml`

## Secrets Required

Repository secrets (Settings -> Secrets and variables -> Actions):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TRACKER_XLSX_URL`

## Confidence Column

Optional but recommended in `DSA Problems` sheet:
- Column name: `Confidence (1-5)`
- Scale:
  - 1 = Not confident
  - 5 = Fully confident

If missing, code assumes confidence = 3.

## Monthly Import File Format

Use CSV with columns:
- `Problem Name`
- `LeetCode Link`
- `Category`
- `Pattern`
- `Difficulty`
- `Status`
- `First Attempt Date`
- `Revision 1`
- `Revision 2`
- `Revision 3`
- `Time Taken (min)`
- `Accuracy (%)`
- `Confidence (1-5)`
- `Notes`

Sample file:
- `imports/sample_new_questions.csv`

## Dashboard (optional)

Run locally:

```bash
pip install -r requirements.txt
streamlit run dashboard_app.py
```

You can load tracker from local file or from your Google Sheet URL.
