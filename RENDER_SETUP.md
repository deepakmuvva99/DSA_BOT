# Render Cloud Setup (Free-Friendly)

This setup sends your daily Telegram plan from Render, so your laptop does not need to be on.

## 1) Push this project to GitHub

Render deploys from a Git repository.

## 2) Prepare your Excel for phone + laptop updates

Best approach: keep `DSA_Master_Tracker.xlsx` in OneDrive so you can edit from:
- Laptop (Excel desktop)
- Phone (Excel mobile app)

Then create a share/download URL for that file and set it as `TRACKER_XLSX_URL` in Render.

Notes:
- The URL must return the `.xlsx` file content directly.
- If using OneDrive share link, use its download form (usually with `download=1`).
- Test by opening the URL in an incognito browser; it should download/open the Excel file without login prompts.

## 3) Deploy on Render

1. Go to Render dashboard -> **New** -> **Blueprint**.
2. Connect your GitHub repo.
3. Render detects `render.yaml` and creates the cron service.
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TRACKER_XLSX_URL`
5. Deploy.

## 4) Time zone and schedule

Current cron schedule in `render.yaml`:
- `0 4 * * *` (UTC)

Change this if needed. Example:
- 9:00 AM IST is `30 3 * * *` (UTC)

## 5) Verify

- Trigger a manual run from Render.
- Confirm Telegram receives a full daily plan.
- Update Excel from phone, save, rerun manual job, and verify plan changes.

## 6) Daily usage

1. Update the OneDrive Excel file from phone or laptop.
2. Render runs daily and fetches latest tracker.
3. Telegram receives your updated adaptive plan automatically.
