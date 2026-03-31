import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRACKER_FILE = os.path.join(BASE_DIR, 'DSA_Master_Tracker.xlsx')
DEFAULT_PLAN_TXT = os.path.join(BASE_DIR, 'daily_plan.txt')
DEFAULT_PLAN_JSON = os.path.join(BASE_DIR, 'daily_plan.json')

class DSAPreparationCoach:
    """
    AI Preparation Coach for DSA, System Design, and SQL
    Analyzes your progress and generates personalized daily plans
    """
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.dsa_df = None
        self.sd_df = None
        self.sql_df = None
        self.load_data()
        
    def load_data(self):
        """Load all sheets from Excel"""
        try:
            self.dsa_df = pd.read_excel(self.excel_path, sheet_name='DSA Problems')
            self.sd_df = pd.read_excel(self.excel_path, sheet_name='System Design')
            self.sql_df = pd.read_excel(self.excel_path, sheet_name='SQL Problems')
            print("Data loaded successfully.")
        except Exception as e:
            print(f"Error loading Excel: {e}")
    
    def analyze_weak_patterns(self):
        """Identify patterns with low accuracy or high time taken"""
        weak_patterns = []
        
        if self.dsa_df is not None:
            # Filter completed problems
            completed = self.dsa_df[self.dsa_df['Status'] == 'Completed'].copy()
            
            if len(completed) > 0:
                # Group by pattern and calculate metrics
                pattern_stats = completed.groupby('Pattern').agg({
                    'Accuracy (%)': 'mean',
                    'Time Taken (min)': 'mean',
                    'Problem Name': 'count'
                }).reset_index()
                
                pattern_stats.columns = ['Pattern', 'Avg_Accuracy', 'Avg_Time', 'Count']
                
                # Identify weak patterns (accuracy < 70% or time > 45 min)
                weak = pattern_stats[
                    (pattern_stats['Avg_Accuracy'] < 70) | 
                    (pattern_stats['Avg_Time'] > 45)
                ]
                
                for _, row in weak.iterrows():
                    weak_patterns.append({
                        'pattern': row['Pattern'],
                        'avg_accuracy': row['Avg_Accuracy'],
                        'avg_time': row['Avg_Time'],
                        'problems_solved': row['Count']
                    })
        
        return weak_patterns
    
    def identify_gaps(self):
        """Find patterns/topics that haven't been touched"""
        gaps = {
            'dsa_patterns': [],
            'system_design': [],
            'sql_patterns': []
        }
        
        # DSA patterns not started
        if self.dsa_df is not None:
            not_started = self.dsa_df[self.dsa_df['Status'] == 'Not Started']
            unique_patterns = not_started['Pattern'].unique()
            gaps['dsa_patterns'] = list(unique_patterns)[:10]  # Top 10
        
        # System Design not started
        if self.sd_df is not None:
            not_started_sd = self.sd_df[self.sd_df['Status'] == 'Not Started']
            gaps['system_design'] = not_started_sd['Topic Name'].head(5).tolist()
        
        # SQL not started
        if self.sql_df is not None:
            not_started_sql = self.sql_df[self.sql_df['Status'] == 'Not Started']
            unique_sql_patterns = not_started_sql['Pattern'].unique()
            gaps['sql_patterns'] = list(unique_sql_patterns)[:5]
        
        return gaps
    
    def calculate_streak(self):
        """Calculate current study streak"""
        # This would track consecutive days of practice
        # For now, returning a placeholder
        return 0  # Implement by tracking dates in Excel
    
    def get_next_problems(self, pattern, difficulty='Medium', count=3):
        """Get next problems for a specific pattern"""
        problems = []
        
        if self.dsa_df is not None:
            available = self.dsa_df[
                (self.dsa_df['Pattern'] == pattern) & 
                (self.dsa_df['Status'] == 'Not Started') &
                (self.dsa_df['Difficulty'] == difficulty)
            ]
            
            for _, row in available.head(count).iterrows():
                problems.append({
                    'name': row['Problem Name'],
                    'link': row['LeetCode Link'],
                    'pattern': row['Pattern'],
                    'difficulty': row['Difficulty'],
                    'expected_time': 30 if difficulty == 'Easy' else 45 if difficulty == 'Medium' else 60
                })
        
        return problems
    
    def get_system_design_topic(self):
        """Get next system design topic to study"""
        if self.sd_df is not None:
            not_started = self.sd_df[self.sd_df['Status'] == 'Not Started']
            
            if len(not_started) > 0:
                # Alternate between LLD and HLD
                lld_topics = not_started[not_started['Type'] == 'LLD']
                hld_topics = not_started[not_started['Type'] == 'HLD']
                
                # Choose based on what was studied less
                if len(lld_topics) > len(hld_topics):
                    topic = lld_topics.iloc[0]
                else:
                    topic = hld_topics.iloc[0] if len(hld_topics) > 0 else lld_topics.iloc[0]
                
                return {
                    'name': topic['Topic Name'],
                    'type': topic['Type'],
                    'category': topic['Category'],
                    'link': topic['Reference Link']
                }
        
        return None
    
    def get_sql_problems(self, count=2):
        """Get next SQL problems"""
        problems = []
        
        if self.sql_df is not None:
            not_started = self.sql_df[self.sql_df['Status'] == 'Not Started']
            
            # Prioritize Easy and Medium
            easy_medium = not_started[not_started['Difficulty'].isin(['Easy', 'Medium'])]
            
            for _, row in easy_medium.head(count).iterrows():
                problems.append({
                    'name': row['Problem Name'],
                    'link': row['LeetCode Link'],
                    'difficulty': row['Difficulty'],
                    'pattern': row['Pattern']
                })
        
        return problems
    
    def generate_daily_plan(self):
        """Generate today's personalized study plan"""
        plan = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'dsa_problems': [],
            'system_design': None,
            'sql_problems': [],
            'weak_areas': [],
            'motivation': '',
            'streak': self.calculate_streak()
        }
        
        # Analyze weak patterns
        weak_patterns = self.analyze_weak_patterns()
        plan['weak_areas'] = weak_patterns
        
        # Get gaps
        gaps = self.identify_gaps()
        
        # Generate DSA problems (3-5 problems)
        if len(weak_patterns) > 0:
            # Focus on weak patterns
            target_pattern = weak_patterns[0]['pattern']
            plan['dsa_problems'] = self.get_next_problems(target_pattern, count=3)
        else:
            # Work on gaps
            if len(gaps['dsa_patterns']) > 0:
                target_pattern = gaps['dsa_patterns'][0]
                plan['dsa_problems'] = self.get_next_problems(target_pattern, count=3)
        
        # Add 2 more problems from different patterns for variety
        if len(gaps['dsa_patterns']) > 1:
            second_pattern = gaps['dsa_patterns'][1]
            additional_problems = self.get_next_problems(second_pattern, count=2)
            plan['dsa_problems'].extend(additional_problems)
        
        # Get System Design topic
        plan['system_design'] = self.get_system_design_topic()
        
        # Get SQL problems
        plan['sql_problems'] = self.get_sql_problems(count=2)
        
        # Motivation message
        completed_dsa = len(self.dsa_df[self.dsa_df['Status'] == 'Completed']) if self.dsa_df is not None else 0
        total_dsa = len(self.dsa_df) if self.dsa_df is not None else 0
        progress_pct = (completed_dsa / total_dsa * 100) if total_dsa > 0 else 0
        
        plan['motivation'] = f"You've completed {completed_dsa}/{total_dsa} DSA problems ({progress_pct:.1f}%). Keep pushing! 🚀"
        
        return plan
    
    def format_daily_plan(self, plan):
        """Format the daily plan as readable text"""
        output = []
        output.append("=" * 80)
        output.append(f"📅 DAILY STUDY PLAN - {plan['date']}")
        output.append("=" * 80)
        output.append("")
        
        # Streak
        output.append(f"🔥 Current Streak: {plan['streak']} days")
        output.append("")
        
        # Motivation
        output.append(f"💪 {plan['motivation']}")
        output.append("")
        output.append("-" * 80)
        
        # DSA Problems
        output.append("📚 DSA PROBLEMS (3-5 problems)")
        output.append("-" * 80)
        for i, problem in enumerate(plan['dsa_problems'], 1):
            output.append(f"{i}. {problem['name']}")
            output.append(f"   Pattern: {problem['pattern']} | Difficulty: {problem['difficulty']}")
            output.append(f"   Link: {problem['link']}")
            output.append(f"   ⏱️  Expected Time: {problem['expected_time']} minutes")
            output.append("")
        
        # System Design
        output.append("-" * 80)
        output.append("🏗️  SYSTEM DESIGN (1 topic)")
        output.append("-" * 80)
        if plan['system_design']:
            sd = plan['system_design']
            output.append(f"Topic: {sd['name']} ({sd['type']})")
            output.append(f"Category: {sd['category']}")
            output.append(f"Reference: {sd['link']}")
        else:
            output.append("✅ All system design topics completed!")
        output.append("")
        
        # SQL Problems
        output.append("-" * 80)
        output.append("🗄️  SQL PROBLEMS (2 problems)")
        output.append("-" * 80)
        for i, problem in enumerate(plan['sql_problems'], 1):
            output.append(f"{i}. {problem['name']}")
            output.append(f"   Pattern: {problem['pattern']} | Difficulty: {problem['difficulty']}")
            output.append(f"   Link: {problem['link']}")
            output.append("")
        
        # Weak Areas
        if len(plan['weak_areas']) > 0:
            output.append("-" * 80)
            output.append("⚠️  FOCUS AREAS (Weak Patterns)")
            output.append("-" * 80)
            for weak in plan['weak_areas']:
                output.append(f"• {weak['pattern']}")
                output.append(f"  Avg Accuracy: {weak['avg_accuracy']:.1f}% | Avg Time: {weak['avg_time']:.1f} min")
                output.append(f"  Problems Solved: {weak['problems_solved']}")
                output.append("")
        
        output.append("=" * 80)
        output.append("✨ Stay consistent. Success is the sum of small efforts repeated daily!")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def save_daily_plan(self, plan, filename='daily_plan.txt'):
        """Save daily plan to file"""
        formatted_plan = self.format_daily_plan(plan)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(formatted_plan)
        return formatted_plan

# Main execution
if __name__ == "__main__":
    # Initialize coach
    coach = DSAPreparationCoach(DEFAULT_TRACKER_FILE)
    
    # Generate daily plan
    daily_plan = coach.generate_daily_plan()
    
    # Format and save
    plan_text = coach.save_daily_plan(daily_plan, DEFAULT_PLAN_TXT)
    
    print(plan_text)
    print("\nDaily plan saved to 'daily_plan.txt'")
    
    # Also save as JSON for programmatic access
    with open(DEFAULT_PLAN_JSON, 'w') as f:
        json.dump(daily_plan, f, indent=2)
    
    print("Daily plan saved as JSON to 'daily_plan.json'")
