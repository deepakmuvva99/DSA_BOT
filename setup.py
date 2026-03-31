#!/usr/bin/env python3
"""
ONE-CLICK SETUP SCRIPT
Automates the entire DSA preparation system setup
"""

import os
import sys
import subprocess
import json

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(step, text):
    print(f"[{step}] {text}")

def check_python_version():
    """Ensure Python 3.6+"""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required. Current version:", sys.version)
        sys.exit(1)
    print("✅ Python version OK:", sys.version.split()[0])

def install_dependencies():
    """Install required packages"""
    print_step("1/7", "Installing dependencies...")
    
    packages = ['pandas', 'openpyxl', 'numpy', 'requests', 'schedule']
    
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package} already installed")
        except ImportError:
            print(f"  📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            print(f"  ✅ {package} installed")

def verify_files():
    """Check all required files exist"""
    print_step("2/7", "Verifying files...")
    
    required_files = [
        'DSA_Master_Tracker.xlsx',
        'ai_coach.py',
        'telegram_notifier.py',
        'SETUP_GUIDE.md'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            missing.append(file)
    
    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        print("Please ensure all files are in the current directory.")
        sys.exit(1)

def test_excel_tracker():
    """Test Excel file can be read"""
    print_step("3/7", "Testing Excel tracker...")
    
    try:
        import pandas as pd
        df = pd.read_excel('DSA_Master_Tracker.xlsx', sheet_name='DSA Problems', nrows=5)
        print(f"  ✅ Excel file readable ({len(df)} sample rows loaded)")
    except Exception as e:
        print(f"  ❌ Error reading Excel: {e}")
        sys.exit(1)

def test_ai_coach():
    """Test AI Coach functionality"""
    print_step("4/7", "Testing AI Coach...")
    
    try:
        from ai_coach import DSAPreparationCoach
        coach = DSAPreparationCoach('DSA_Master_Tracker.xlsx')
        plan = coach.generate_daily_plan()
        
        if plan and 'dsa_problems' in plan:
            print(f"  ✅ AI Coach working (generated {len(plan['dsa_problems'])} DSA problems)")
        else:
            print("  ⚠️  AI Coach generated empty plan (normal if no data in Excel)")
    except Exception as e:
        print(f"  ❌ Error testing AI Coach: {e}")
        sys.exit(1)

def configure_telegram():
    """Guide user through Telegram setup"""
    print_step("5/7", "Configuring Telegram Bot...")
    
    print("\n📱 TELEGRAM BOT SETUP")
    print("-" * 70)
    
    # Check if already configured
    with open('telegram_notifier.py', 'r') as f:
        content = f.read()
    
    if 'YOUR_BOT_TOKEN_HERE' not in content:
        print("  ✅ Telegram already configured")
        return
    
    print("""
To enable FREE daily notifications on your phone:

1. Open Telegram and search for: @BotFather
2. Send command: /newbot
3. Follow instructions to create your bot
4. You'll receive a TOKEN like: 123456789:ABCdefGHI...
5. Start a chat with your new bot and send any message
6. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
7. Find your CHAT_ID in the response

Once you have both, we'll update the configuration.
""")
    
    choice = input("Do you have your BOT_TOKEN and CHAT_ID? (y/n): ").lower()
    
    if choice == 'y':
        bot_token = input("Enter your BOT_TOKEN: ").strip()
        chat_id = input("Enter your CHAT_ID: ").strip()
        
        # Update telegram_notifier.py
        with open('telegram_notifier.py', 'r') as f:
            content = f.read()
        
        content = content.replace('YOUR_BOT_TOKEN_HERE', bot_token)
        content = content.replace('YOUR_CHAT_ID_HERE', chat_id)
        
        with open('telegram_notifier.py', 'w') as f:
            f.write(content)
        
        print("  ✅ Telegram configuration saved")
        
        # Test notification
        test_choice = input("\nTest notification now? (y/n): ").lower()
        if test_choice == 'y':
            try:
                subprocess.run([sys.executable, 'telegram_notifier.py'], timeout=10)
                print("  ✅ Check your phone for the test message!")
            except Exception as e:
                print(f"  ⚠️  Error sending test: {e}")
    else:
        print("  ⏩ Skipping Telegram setup (you can configure later)")
        print("     Edit telegram_notifier.py manually")

def setup_scheduler():
    """Guide user through scheduler setup"""
    print_step("6/7", "Setting up daily scheduler...")
    
    print("\n⏰ DAILY REMINDER SETUP")
    print("-" * 70)
    
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        print("""
For Linux/Mac, add this to your crontab:

1. Run: crontab -e
2. Add this line (sends reminder at 9 AM daily):

0 9 * * * /usr/bin/python3 {}/telegram_notifier.py

3. Save and exit
""".format(os.path.abspath('.')))
        
    elif sys.platform == 'win32':
        print("""
For Windows, use Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "DSA Daily Reminder"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
6. Program: {}
7. Arguments: "{}"
8. Finish
""".format(sys.executable, os.path.abspath('telegram_notifier.py')))
    
    print("\nAlternatively, you can run the Python scheduler:")
    print(f"  python telegram_notifier.py (keeps running)")
    
    input("\nPress Enter when done setting up the scheduler...")
    print("  ✅ Scheduler configured")

def create_quick_start():
    """Create quick start scripts"""
    print_step("7/7", "Creating quick start scripts...")
    
    # Create Windows batch file
    with open('run_daily_plan.bat', 'w') as f:
        f.write('@echo off\n')
        f.write('echo Generating your daily study plan...\n')
        f.write(f'python ai_coach.py\n')
        f.write('echo.\n')
        f.write('echo Daily plan generated!\n')
        f.write('pause\n')
    
    # Create Linux/Mac shell script
    with open('run_daily_plan.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('echo "Generating your daily study plan..."\n')
        f.write('python3 ai_coach.py\n')
        f.write('echo ""\n')
        f.write('echo "Daily plan generated!"\n')
    
    os.chmod('run_daily_plan.sh', 0o755)
    
    print("  ✅ Created run_daily_plan.bat (Windows)")
    print("  ✅ Created run_daily_plan.sh (Linux/Mac)")

def print_summary():
    """Print setup summary"""
    print_header("🎉 SETUP COMPLETE!")
    
    print("""
Your AI-powered DSA preparation system is ready!

📁 FILES CREATED:
   • DSA_Master_Tracker.xlsx - Your tracking spreadsheet
   • ai_coach.py - AI that analyzes your progress
   • telegram_notifier.py - Sends daily notifications
   • SETUP_GUIDE.md - Complete documentation
   • run_daily_plan.bat/.sh - Quick start scripts

🚀 NEXT STEPS:

1. Open DSA_Master_Tracker.xlsx
2. Solve your first problem
3. Update the Excel (Status, Time, Accuracy)
4. Run: python ai_coach.py
5. Check your daily_plan.txt
6. If Telegram configured, you'll get daily reminders at 9 AM

📚 DAILY WORKFLOW:
   Morning: Get notification → Review plan
   Day: Solve problems → Update Excel
   Next day: AI adapts based on your performance

💡 TIPS:
   • Start with 3 problems per day
   • Be honest with accuracy ratings
   • Focus on understanding patterns
   • Maintain daily consistency

📖 READ: SETUP_GUIDE.md for complete documentation

Good luck with your preparation! 💪
""")

def main():
    print_header("DSA PREPARATION SYSTEM - ONE-CLICK SETUP")
    
    check_python_version()
    install_dependencies()
    verify_files()
    test_excel_tracker()
    test_ai_coach()
    configure_telegram()
    setup_scheduler()
    create_quick_start()
    print_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
