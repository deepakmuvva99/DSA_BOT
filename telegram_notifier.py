"""
FREE TELEGRAM NOTIFICATION SYSTEM
No paid services required - uses free Telegram Bot API

SETUP INSTRUCTIONS:
1. Create a Telegram Bot:
   - Open Telegram and search for @BotFather
   - Send /newbot command
   - Follow instructions to create your bot
   - Save the API TOKEN you receive
   
2. Get Your Chat ID:
   - Start a chat with your new bot
   - Send any message to it
   - Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   - Look for "chat":{"id": YOUR_CHAT_ID}
   - Save your CHAT_ID

3. Update the config below with your TOKEN and CHAT_ID

4. Schedule this script to run daily using:
   - Windows: Task Scheduler
   - Linux/Mac: cron job
   - Or use Python's schedule library (shown below)
"""

import requests
import json
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRACKER_FILE = os.path.join(BASE_DIR, 'DSA_Master_Tracker.xlsx')
DEFAULT_PLAN_FILE = os.path.join(BASE_DIR, 'daily_plan.txt')

# ============================================
# CONFIGURATION
# ============================================
TELEGRAM_CONFIG = {
    'BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', '')
}

class TelegramNotifier:
    """Send notifications via Telegram (100% FREE)"""
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode=None):
        """Send a message to Telegram"""
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("Notification sent successfully.")
                return True
            else:
                print(f"Failed to send notification: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False
    
    def send_daily_plan(self, plan_file_path):
        """Send the daily plan as a formatted message"""
        try:
            with open(plan_file_path, 'r', encoding='utf-8') as f:
                plan_text = f.read()
            
            # Format for Telegram (Markdown)
            telegram_message = self._format_for_telegram(plan_text)
            
            # Split if message is too long (Telegram limit: 4096 chars)
            if len(telegram_message) > 4000:
                # Send in parts
                parts = self._split_message(telegram_message, 4000)
                for part in parts:
                    self.send_message(part)
            else:
                self.send_message(telegram_message)
            
            return True
        except Exception as e:
            print(f"❌ Error reading plan file: {e}")
            return False
    
    def _format_for_telegram(self, plan_text):
        """Format plan for Telegram Markdown"""
        # Convert to Telegram-friendly format
        lines = plan_text.split('\n')
        formatted = []
        
        for line in lines:
            if line.startswith('==='):
                formatted.append('━' * 40)
            elif line.startswith('---'):
                formatted.append('─' * 40)
            elif line.startswith('📅') or line.startswith('🔥') or line.startswith('💪'):
                formatted.append(f"*{line}*")
            elif line.startswith('📚') or line.startswith('🏗️') or line.startswith('🗄️'):
                formatted.append(f"\n*{line}*")
            elif '. ' in line and line[0].isdigit():
                formatted.append(f"\n`{line}`")
            else:
                formatted.append(line)
        
        return '\n'.join(formatted)
    
    def _split_message(self, message, max_length=4000):
        """Split message into chunks"""
        parts = []
        current = ""
        
        for line in message.split('\n'):
            if len(current) + len(line) + 1 > max_length:
                parts.append(current)
                current = line
            else:
                current += '\n' + line if current else line
        
        if current:
            parts.append(current)
        
        return parts

# ============================================
# DAILY REMINDER SCHEDULER (FREE)
# ============================================

def send_daily_reminder():
    """Main function to generate and send daily plan"""
    from ai_coach import DSAPreparationCoach
    
    print(f"Running daily reminder at {datetime.now()}")
    
    # Generate daily plan
    coach = DSAPreparationCoach(DEFAULT_TRACKER_FILE)
    daily_plan = coach.generate_daily_plan()
    plan_text = coach.save_daily_plan(daily_plan, DEFAULT_PLAN_FILE)
    
    # Send via Telegram
    notifier = TelegramNotifier(
        TELEGRAM_CONFIG['BOT_TOKEN'], 
        TELEGRAM_CONFIG['CHAT_ID']
    )
    
    success = notifier.send_daily_plan(DEFAULT_PLAN_FILE)
    
    if success:
        print("Daily reminder sent successfully.")
    else:
        print("Failed to send daily reminder.")

# ============================================
# OPTION 1: MANUAL TRIGGER
# ============================================
def manual_trigger():
    """Run this manually to test"""
    send_daily_reminder()

# ============================================
# OPTION 2: SCHEDULED EXECUTION (Python)
# ============================================
def run_scheduler():
    """
    Run this script continuously to send reminders daily
    Uses the 'schedule' library (free)
    
    Install: pip install schedule
    """
    import schedule
    import time
    
    # Schedule daily reminder at 9:00 AM
    schedule.every().day.at("09:00").do(send_daily_reminder)
    
    print("Scheduler started. Waiting for scheduled time...")
    print("Daily reminder will be sent at 9:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# ============================================
# OPTION 3: CRON JOB (Linux/Mac) - RECOMMENDED
# ============================================
"""
Add this to your crontab (run: crontab -e):

# Send daily reminder at 9:00 AM
0 9 * * * /usr/bin/python3 /path/to/telegram_notifier.py

# Or multiple times per day:
0 9 * * * /usr/bin/python3 /path/to/telegram_notifier.py  # Morning
0 18 * * * /usr/bin/python3 /path/to/telegram_notifier.py  # Evening
"""

# ============================================
# OPTION 4: WINDOWS TASK SCHEDULER
# ============================================
"""
Windows Task Scheduler Setup:
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
5. Program: python.exe
6. Arguments: "C:\\path\\to\\telegram_notifier.py"
"""

if __name__ == "__main__":
    # Test the notification
    print("Testing Telegram notification...")
    
    if not TELEGRAM_CONFIG['BOT_TOKEN'] or TELEGRAM_CONFIG['BOT_TOKEN'] == 'YOUR_BOT_TOKEN_HERE':
        print("\nSETUP REQUIRED!")
        print("=" * 60)
        print("Please follow these steps:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions")
        print("3. Copy your BOT_TOKEN")
        print("4. Message your bot and get your CHAT_ID")
        print("5. Update TELEGRAM_CONFIG in this script")
        print("=" * 60)
    else:
        # Run manual trigger for testing
        manual_trigger()
