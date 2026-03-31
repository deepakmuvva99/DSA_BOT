import json
import os
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRACKER_FILE = os.path.join(BASE_DIR, "DSA_Master_Tracker.xlsx")
DEFAULT_PLAN_TXT = os.path.join(BASE_DIR, "daily_plan.txt")
DEFAULT_PLAN_JSON = os.path.join(BASE_DIR, "daily_plan.json")
DEFAULT_WEEKLY_TXT = os.path.join(BASE_DIR, "weekly_report.txt")
DEFAULT_EXAM_TXT = os.path.join(BASE_DIR, "weekly_exam.txt")


class DSAPreparationCoach:
    """AI coach for daily plans, weekly reports, revisions, and exams."""

    REVISION_INTERVALS = [1, 7, 30]

    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.dsa_df = None
        self.sd_df = None
        self.sql_df = None
        self.load_data()

    def load_data(self):
        try:
            self.dsa_df = pd.read_excel(self.excel_path, sheet_name="DSA Problems")
            self.sd_df = pd.read_excel(self.excel_path, sheet_name="System Design")
            self.sql_df = pd.read_excel(self.excel_path, sheet_name="SQL Problems")
            self._ensure_confidence_column()
            print("Data loaded successfully.")
        except Exception as e:
            print(f"Error loading Excel: {e}")

    def _ensure_confidence_column(self):
        if self.dsa_df is not None and "Confidence (1-5)" not in self.dsa_df.columns:
            self.dsa_df["Confidence (1-5)"] = 3

    def _to_datetime(self, series):
        return pd.to_datetime(series, errors="coerce")

    def _collect_practice_dates(self, row):
        date_cols = ["First Attempt Date", "Revision 1", "Revision 2", "Revision 3"]
        dates = []
        for col in date_cols:
            if col in row.index and pd.notna(row[col]):
                dt = pd.to_datetime(row[col], errors="coerce")
                if pd.notna(dt):
                    dates.append(dt.date())
        return sorted(set(dates))

    def _completed_dsa(self):
        if self.dsa_df is None:
            return pd.DataFrame()
        return self.dsa_df[self.dsa_df["Status"] == "Completed"].copy()

    def analyze_weak_patterns(self):
        weak_patterns = []
        completed = self._completed_dsa()
        if len(completed) == 0:
            return weak_patterns

        pattern_stats = completed.groupby("Pattern").agg(
            {
                "Accuracy (%)": "mean",
                "Time Taken (min)": "mean",
                "Problem Name": "count",
                "Confidence (1-5)": "mean",
            }
        ).reset_index()
        pattern_stats.columns = ["Pattern", "Avg_Accuracy", "Avg_Time", "Count", "Avg_Confidence"]

        weak = pattern_stats[
            (pattern_stats["Avg_Accuracy"] < 70)
            | (pattern_stats["Avg_Time"] > 45)
            | (pattern_stats["Avg_Confidence"] < 3)
        ].sort_values(["Avg_Accuracy", "Avg_Confidence", "Avg_Time"], ascending=[True, True, False])

        for _, row in weak.iterrows():
            weak_patterns.append(
                {
                    "pattern": row["Pattern"],
                    "avg_accuracy": float(row["Avg_Accuracy"]),
                    "avg_time": float(row["Avg_Time"]),
                    "avg_confidence": float(row["Avg_Confidence"]),
                    "problems_solved": int(row["Count"]),
                }
            )
        return weak_patterns

    def identify_gaps(self):
        gaps = {"dsa_patterns": [], "system_design": [], "sql_patterns": []}
        if self.dsa_df is not None:
            not_started = self.dsa_df[self.dsa_df["Status"] == "Not Started"]
            gaps["dsa_patterns"] = list(not_started["Pattern"].dropna().unique())[:10]
        if self.sd_df is not None:
            not_started_sd = self.sd_df[self.sd_df["Status"] == "Not Started"]
            gaps["system_design"] = not_started_sd["Topic Name"].head(5).tolist()
        if self.sql_df is not None:
            not_started_sql = self.sql_df[self.sql_df["Status"] == "Not Started"]
            gaps["sql_patterns"] = list(not_started_sql["Pattern"].dropna().unique())[:5]
        return gaps

    def calculate_streak(self):
        if self.dsa_df is None:
            return 0

        all_dates = set()
        for _, row in self.dsa_df.iterrows():
            all_dates.update(self._collect_practice_dates(row))
        if not all_dates:
            return 0

        sorted_dates = sorted(all_dates, reverse=True)
        streak = 1
        current = sorted_dates[0]
        for dt in sorted_dates[1:]:
            if (current - dt).days == 1:
                streak += 1
                current = dt
            elif (current - dt).days > 1:
                break
        return streak

    def get_next_problems(self, pattern, count=3):
        problems = []
        if self.dsa_df is None:
            return problems

        available = self.dsa_df[
            (self.dsa_df["Pattern"] == pattern) & (self.dsa_df["Status"] == "Not Started")
        ].copy()
        if len(available) == 0:
            return problems

        difficulty_rank = {"Easy": 0, "Medium": 1, "Hard": 2}
        available["difficulty_rank"] = available["Difficulty"].map(difficulty_rank).fillna(1)
        available = available.sort_values(["difficulty_rank", "Problem Name"])

        for _, row in available.head(count).iterrows():
            difficulty = row["Difficulty"]
            problems.append(
                {
                    "name": row["Problem Name"],
                    "link": row["LeetCode Link"],
                    "pattern": row["Pattern"],
                    "difficulty": difficulty,
                    "expected_time": 30 if difficulty == "Easy" else 45 if difficulty == "Medium" else 60,
                }
            )
        return problems

    def get_revision_problems(self, count=3):
        completed = self._completed_dsa()
        if len(completed) == 0:
            return []

        today = datetime.now().date()
        candidates = []

        for _, row in completed.iterrows():
            practice_dates = self._collect_practice_dates(row)
            if not practice_dates:
                continue
            revisions_done = max(0, len(practice_dates) - 1)
            if revisions_done >= len(self.REVISION_INTERVALS):
                continue

            next_interval = self.REVISION_INTERVALS[revisions_done]
            last_practice = practice_dates[-1]
            due_date = last_practice + timedelta(days=next_interval)
            if due_date > today:
                continue

            confidence = row.get("Confidence (1-5)", 3)
            confidence = 3 if pd.isna(confidence) else float(confidence)
            accuracy = row.get("Accuracy (%)", 70)
            accuracy = 70 if pd.isna(accuracy) else float(accuracy)
            days_overdue = (today - due_date).days
            priority = (3 - confidence) * 30 + (70 - accuracy) * 0.5 + days_overdue

            candidates.append(
                {
                    "name": row["Problem Name"],
                    "link": row["LeetCode Link"],
                    "pattern": row["Pattern"],
                    "difficulty": row["Difficulty"],
                    "last_practice": str(last_practice),
                    "due_date": str(due_date),
                    "confidence": confidence,
                    "accuracy": accuracy,
                    "priority": priority,
                }
            )

        ranked = sorted(candidates, key=lambda x: x["priority"], reverse=True)
        return ranked[:count]

    def get_system_design_topic(self):
        if self.sd_df is None:
            return None
        not_started = self.sd_df[self.sd_df["Status"] == "Not Started"]
        if len(not_started) == 0:
            return None
        lld_topics = not_started[not_started["Type"] == "LLD"]
        hld_topics = not_started[not_started["Type"] == "HLD"]
        topic = lld_topics.iloc[0] if len(lld_topics) > len(hld_topics) else (
            hld_topics.iloc[0] if len(hld_topics) > 0 else lld_topics.iloc[0]
        )
        return {
            "name": topic["Topic Name"],
            "type": topic["Type"],
            "category": topic["Category"],
            "link": topic["Reference Link"],
        }

    def get_sql_problems(self, count=2):
        problems = []
        if self.sql_df is None:
            return problems
        not_started = self.sql_df[self.sql_df["Status"] == "Not Started"]
        easy_medium = not_started[not_started["Difficulty"].isin(["Easy", "Medium"])]
        for _, row in easy_medium.head(count).iterrows():
            problems.append(
                {
                    "name": row["Problem Name"],
                    "link": row["LeetCode Link"],
                    "difficulty": row["Difficulty"],
                    "pattern": row["Pattern"],
                }
            )
        return problems

    def _weekly_window(self, reference_date=None):
        ref = reference_date or datetime.now().date()
        week_start = ref - timedelta(days=ref.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    def generate_daily_plan(self):
        plan = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "dsa_problems": [],
            "revision_problems": [],
            "system_design": None,
            "sql_problems": [],
            "weak_areas": [],
            "motivation": "",
            "streak": self.calculate_streak(),
        }

        weak_patterns = self.analyze_weak_patterns()
        plan["weak_areas"] = weak_patterns
        gaps = self.identify_gaps()

        if len(weak_patterns) > 0:
            target_pattern = weak_patterns[0]["pattern"]
            plan["dsa_problems"] = self.get_next_problems(target_pattern, count=3)
        elif len(gaps["dsa_patterns"]) > 0:
            plan["dsa_problems"] = self.get_next_problems(gaps["dsa_patterns"][0], count=3)

        if len(gaps["dsa_patterns"]) > 1:
            plan["dsa_problems"].extend(self.get_next_problems(gaps["dsa_patterns"][1], count=2))

        plan["revision_problems"] = self.get_revision_problems(count=3)
        plan["system_design"] = self.get_system_design_topic()
        plan["sql_problems"] = self.get_sql_problems(count=2)

        completed_dsa = len(self._completed_dsa())
        total_dsa = len(self.dsa_df) if self.dsa_df is not None else 0
        progress_pct = (completed_dsa / total_dsa * 100) if total_dsa > 0 else 0
        plan["motivation"] = (
            f"You have completed {completed_dsa}/{total_dsa} DSA problems ({progress_pct:.1f}%). Keep pushing!"
        )
        return plan

    def get_weekly_analytics(self, reference_date=None):
        week_start, week_end = self._weekly_window(reference_date)
        prev_start = week_start - timedelta(days=7)
        prev_end = week_start - timedelta(days=1)

        completed = self._completed_dsa()
        if len(completed) == 0:
            return {
                "week_start": str(week_start),
                "week_end": str(week_end),
                "solved_count": 0,
                "avg_accuracy": 0.0,
                "avg_time": 0.0,
                "streak": self.calculate_streak(),
                "weak_trends": [],
            }

        completed["First Attempt Date"] = self._to_datetime(completed["First Attempt Date"])
        this_week = completed[
            (completed["First Attempt Date"].dt.date >= week_start)
            & (completed["First Attempt Date"].dt.date <= week_end)
        ]
        prev_week = completed[
            (completed["First Attempt Date"].dt.date >= prev_start)
            & (completed["First Attempt Date"].dt.date <= prev_end)
        ]

        weak_trends = []
        this_by_pattern = this_week.groupby("Pattern")["Accuracy (%)"].mean()
        prev_by_pattern = prev_week.groupby("Pattern")["Accuracy (%)"].mean()
        for pattern, current_acc in this_by_pattern.items():
            prev_acc = prev_by_pattern.get(pattern, np.nan)
            delta = None if pd.isna(prev_acc) else float(current_acc - prev_acc)
            if current_acc < 70 or (delta is not None and delta < -5):
                weak_trends.append(
                    {
                        "pattern": pattern,
                        "current_accuracy": float(current_acc),
                        "delta_vs_prev_week": delta,
                    }
                )

        return {
            "week_start": str(week_start),
            "week_end": str(week_end),
            "solved_count": int(len(this_week)),
            "avg_accuracy": float(this_week["Accuracy (%)"].mean()) if len(this_week) > 0 else 0.0,
            "avg_time": float(this_week["Time Taken (min)"].mean()) if len(this_week) > 0 else 0.0,
            "streak": self.calculate_streak(),
            "weak_trends": weak_trends[:5],
        }

    def generate_weekly_exam(self, reference_date=None, question_count=8):
        week_start, week_end = self._weekly_window(reference_date)
        completed = self._completed_dsa().copy()
        if len(completed) == 0:
            return {
                "title": "Sunday Weekly Exam",
                "week_start": str(week_start),
                "week_end": str(week_end),
                "questions": [],
                "deadline": f"{week_end} 23:59 local time",
            }

        completed["First Attempt Date"] = self._to_datetime(completed["First Attempt Date"])
        this_week = completed[
            (completed["First Attempt Date"].dt.date >= week_start)
            & (completed["First Attempt Date"].dt.date <= week_end)
        ].copy()

        if len(this_week) == 0:
            this_week = completed.sort_values("First Attempt Date", ascending=False).head(question_count)

        this_week["Confidence (1-5)"] = this_week["Confidence (1-5)"].fillna(3)
        this_week["Accuracy (%)"] = this_week["Accuracy (%)"].fillna(70)
        this_week["exam_priority"] = (5 - this_week["Confidence (1-5)"]) * 20 + (
            100 - this_week["Accuracy (%)"]
        )
        selected = this_week.sort_values("exam_priority", ascending=False).head(question_count)

        questions = []
        for i, (_, row) in enumerate(selected.iterrows(), 1):
            questions.append(
                {
                    "no": i,
                    "problem_name": row["Problem Name"],
                    "link": row["LeetCode Link"],
                    "pattern": row["Pattern"],
                    "difficulty": row["Difficulty"],
                    "exam_instruction": "Solve in interview mode without hints. 35 min max per question.",
                }
            )

        deadline = f"{week_end} 23:59 local time"
        return {
            "title": "Sunday Weekly Exam",
            "week_start": str(week_start),
            "week_end": str(week_end),
            "deadline": deadline,
            "questions": questions,
        }

    def format_daily_plan(self, plan):
        output = []
        output.append("=" * 80)
        output.append(f"DAILY STUDY PLAN - {plan['date']}")
        output.append("=" * 80)
        output.append(f"Current Streak: {plan['streak']} days")
        output.append(plan["motivation"])
        output.append("-" * 80)
        output.append("DSA PROBLEMS (3-5 problems)")
        output.append("-" * 80)
        for i, problem in enumerate(plan["dsa_problems"], 1):
            output.append(f"{i}. {problem['name']}")
            output.append(f"   Pattern: {problem['pattern']} | Difficulty: {problem['difficulty']}")
            output.append(f"   Link: {problem['link']}")
            output.append(f"   Expected Time: {problem['expected_time']} minutes")

        output.append("")
        output.append("-" * 80)
        output.append("SMART REVISION QUEUE (1d/7d/30d + confidence)")
        output.append("-" * 80)
        if plan["revision_problems"]:
            for i, problem in enumerate(plan["revision_problems"], 1):
                output.append(f"{i}. {problem['name']} ({problem['pattern']} - {problem['difficulty']})")
                output.append(f"   Last Practice: {problem['last_practice']} | Due Date: {problem['due_date']}")
                output.append(f"   Accuracy: {problem['accuracy']:.1f}% | Confidence: {problem['confidence']:.1f}/5")
                output.append(f"   Link: {problem['link']}")
        else:
            output.append("No revision problems are due today.")

        output.append("")
        output.append("-" * 80)
        output.append("SYSTEM DESIGN (1 topic)")
        output.append("-" * 80)
        if plan["system_design"]:
            sd = plan["system_design"]
            output.append(f"Topic: {sd['name']} ({sd['type']})")
            output.append(f"Category: {sd['category']}")
            output.append(f"Reference: {sd['link']}")
        else:
            output.append("All system design topics completed.")

        output.append("")
        output.append("-" * 80)
        output.append("SQL PROBLEMS (2 problems)")
        output.append("-" * 80)
        for i, problem in enumerate(plan["sql_problems"], 1):
            output.append(f"{i}. {problem['name']}")
            output.append(f"   Pattern: {problem['pattern']} | Difficulty: {problem['difficulty']}")
            output.append(f"   Link: {problem['link']}")

        if plan["weak_areas"]:
            output.append("")
            output.append("-" * 80)
            output.append("FOCUS AREAS (Weak Patterns)")
            output.append("-" * 80)
            for weak in plan["weak_areas"]:
                output.append(
                    f"- {weak['pattern']}: Accuracy {weak['avg_accuracy']:.1f}% | "
                    f"Time {weak['avg_time']:.1f} min | Confidence {weak['avg_confidence']:.1f}/5"
                )

        output.append("=" * 80)
        output.append("Stay consistent. Small daily wins compound.")
        output.append("=" * 80)
        return "\n".join(output)

    def format_weekly_report(self, report):
        lines = [
            "=" * 80,
            "SUNDAY WEEKLY ANALYTICS REPORT",
            "=" * 80,
            f"Week: {report['week_start']} to {report['week_end']}",
            f"Solved this week: {report['solved_count']}",
            f"Average accuracy: {report['avg_accuracy']:.1f}%",
            f"Average time/problem: {report['avg_time']:.1f} minutes",
            f"Current streak: {report['streak']} days",
            "-" * 80,
            "Weak Pattern Trends",
            "-" * 80,
        ]
        if report["weak_trends"]:
            for item in report["weak_trends"]:
                delta = item["delta_vs_prev_week"]
                delta_text = "N/A" if delta is None else f"{delta:+.1f}%"
                lines.append(
                    f"- {item['pattern']}: {item['current_accuracy']:.1f}% this week "
                    f"(vs previous week: {delta_text})"
                )
        else:
            lines.append("No negative pattern trends this week.")
        lines.append("=" * 80)
        return "\n".join(lines)

    def format_weekly_exam(self, exam):
        lines = [
            "=" * 80,
            exam["title"],
            "=" * 80,
            f"Coverage Week: {exam['week_start']} to {exam['week_end']}",
            "Exam Release Time: Sunday 2:00 PM",
            f"Submission Deadline: {exam['deadline']}",
            "-" * 80,
            "Instructions",
            "-" * 80,
            "1) Attempt all questions in timed mode.",
            "2) No hints/solutions while solving.",
            "3) Update tracker before midnight after exam.",
            "-" * 80,
            "Questions",
            "-" * 80,
        ]
        if exam["questions"]:
            for q in exam["questions"]:
                lines.append(
                    f"{q['no']}. {q['problem_name']} | {q['pattern']} | {q['difficulty']}\n"
                    f"   Link: {q['link']}\n"
                    f"   Task: {q['exam_instruction']}"
                )
        else:
            lines.append("No questions available yet. Solve more this week to unlock exam set.")
        lines.append("=" * 80)
        return "\n".join(lines)

    def save_daily_plan(self, plan, filename=DEFAULT_PLAN_TXT):
        formatted_plan = self.format_daily_plan(plan)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_plan)
        return formatted_plan

    def save_weekly_report(self, report, filename=DEFAULT_WEEKLY_TXT):
        formatted = self.format_weekly_report(report)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted)
        return formatted

    def save_weekly_exam(self, exam, filename=DEFAULT_EXAM_TXT):
        formatted = self.format_weekly_exam(exam)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted)
        return formatted


if __name__ == "__main__":
    coach = DSAPreparationCoach(DEFAULT_TRACKER_FILE)
    daily_plan = coach.generate_daily_plan()
    plan_text = coach.save_daily_plan(daily_plan, DEFAULT_PLAN_TXT)
    print(plan_text)
    print("\nDaily plan saved to 'daily_plan.txt'")
    with open(DEFAULT_PLAN_JSON, "w", encoding="utf-8") as f:
        json.dump(daily_plan, f, indent=2, ensure_ascii=False)
    print("Daily plan saved as JSON to 'daily_plan.json'")
