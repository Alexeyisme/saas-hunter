#!/usr/bin/env python3
"""
Usage Statistics Dashboard
Display token usage and job metrics
"""
from usage_tracker import UsageTracker
from datetime import datetime, timedelta

def print_dashboard():
    """Print usage statistics dashboard"""
    tracker = UsageTracker()
    
    # Today's stats
    today = tracker.get_daily_usage()
    
    # This month's stats
    month = tracker.get_monthly_usage()
    
    # Job breakdown (last 7 days)
    jobs = tracker.get_job_breakdown(days=7)
    
    # Print dashboard
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         SaaS Hunter - Usage Statistics                   ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║                                                          ║")
    print(f"║  📅 Today ({today['date']})                              ")
    print(f"║     Items Processed: {today['items_processed']:<10} ")
    print(f"║     Tokens Used: {today['total_tokens']:<10}             ")
    print(f"║     Cost: ${today['total_cost']:.4f}                      ")
    print(f"║     Jobs: {today['jobs_success']}/{today['jobs_run']} completed                            ")
    print("║                                                          ║")
    print(f"║  📊 This Month ({month['month']})                        ")
    print(f"║     Items Processed: {month['items_processed']:<10}     ")
    print(f"║     Tokens Used: {month['total_tokens']:<10}             ")
    print(f"║     Cost: ${month['total_cost']:.2f} / $15.00 budget            ")
    print(f"║     Budget Remaining: ${month['budget_remaining']:.2f} ({month['budget_remaining']/15*100:.0f}%)              ")
    print(f"║     Jobs Run: {month['jobs_run']:<10}                      ")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    if jobs:
        print("Breakdown by Job Type (Last 7 Days):")
        print("-" * 80)
        print(f"{'Job Name':<25} {'Runs':<8} {'Items':<10} {'Tokens':<10} {'Avg Time':<12}")
        print("-" * 80)
        
        for job in jobs:
            avg_time = f"{job['avg_duration_ms']/1000:.1f}s" if job['avg_duration_ms'] > 0 else "N/A"
            print(f"{job['job_name']:<25} {job['runs']:<8} {job['items']:<10} {job['tokens']:<10} {avg_time:<12}")
        
        print("-" * 80)
    else:
        print("No jobs recorded yet.")
    
    print()

if __name__ == '__main__':
    print_dashboard()
