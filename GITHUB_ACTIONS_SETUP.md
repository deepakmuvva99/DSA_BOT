# GitHub Actions Setup (No Card Needed)

This runs your daily Telegram reminder from GitHub Actions at **9:00 AM IST** every day.

## 1) Confirm workflow file exists

Workflow path:
- `.github/workflows/daily-reminder.yml`

Schedule configured:
- `30 3 * * *` (UTC) = **9:00 AM IST**

## 2) Add GitHub repository secrets

In your repo:
1. Go to **Settings** -> **Secrets and variables** -> **Actions**
2. Click **New repository secret**
3. Add these 3 secrets exactly:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TRACKER_XLSX_URL`

## 3) How to get TRACKER_XLSX_URL

Keep `DSA_Master_Tracker.xlsx` in OneDrive and share as **Anyone with the link can view**.
Use a direct download link that works in incognito.

## 4) Test immediately (manual run)

1. Open repo -> **Actions** tab
2. Open workflow **Daily DSA Telegram Reminder**
3. Click **Run workflow**
4. Choose `main` branch and run
5. Verify Telegram message arrives

## 5) Daily automation behavior

- GitHub Actions runs daily at 9:00 AM IST
- It downloads your latest Excel from `TRACKER_XLSX_URL`
- Generates adaptive plan
- Sends plan to your Telegram

## 6) Update Excel from phone or laptop

Use the same OneDrive file:
- Phone: Excel mobile app
- Laptop: Excel desktop/web

Save updates anytime before 9:00 AM IST for next day’s plan.
