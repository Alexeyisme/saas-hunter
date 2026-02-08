#!/usr/bin/env python3
"""
Usage Tracker - Track token usage and job metrics
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

class UsageTracker:
    def __init__(self, db_path='../data/usage_stats.db'):
        # Resolve relative to script location
        script_dir = Path(__file__).parent
        self.db_path = script_dir / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            job_type TEXT NOT NULL,
            job_name TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            model TEXT,
            cost_usd REAL DEFAULT 0.0,
            items_processed INTEGER DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT 1,
            notes TEXT
        )''')
        conn.commit()
        conn.close()
    
    @contextmanager
    def track_job(self, job_type, job_name):
        """
        Context manager for automatic job tracking
        
        Usage:
            tracker = UsageTracker()
            with tracker.track_job('collection', 'reddit_monitor') as job:
                results = collect_data()
                job['items_processed'] = len(results)
        """
        start = datetime.now()
        job = {
            'job_type': job_type,
            'job_name': job_name,
            'timestamp': start.isoformat(),
            'items_processed': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'model': None,
            'cost_usd': 0.0,
            'notes': None
        }
        
        try:
            yield job
            job['success'] = True
        except Exception as e:
            job['success'] = False
            job['notes'] = str(e)
            raise
        finally:
            duration = (datetime.now() - start).total_seconds() * 1000
            job['duration_ms'] = int(duration)
            job['total_tokens'] = job['input_tokens'] + job['output_tokens']
            self._save_job(job)
    
    def _save_job(self, job):
        """Save job metrics to database"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''INSERT INTO token_usage 
            (timestamp, job_type, job_name, input_tokens, output_tokens, 
             total_tokens, model, cost_usd, items_processed, duration_ms, success, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (job['timestamp'], job['job_type'], job['job_name'],
             job['input_tokens'], job['output_tokens'], job['total_tokens'],
             job.get('model'), job['cost_usd'], job['items_processed'],
             job['duration_ms'], job['success'], job.get('notes'))
        )
        conn.commit()
        conn.close()
    
    def get_daily_usage(self, date=None):
        """Get usage for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(str(self.db_path))
        result = conn.execute('''
            SELECT 
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost,
                SUM(items_processed) as items,
                COUNT(*) as jobs,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
            FROM token_usage 
            WHERE DATE(timestamp) = ?
        ''', (date,)).fetchone()
        conn.close()
        
        return {
            'date': date,
            'total_tokens': result[0] or 0,
            'total_cost': result[1] or 0.0,
            'items_processed': result[2] or 0,
            'jobs_run': result[3] or 0,
            'jobs_success': result[4] or 0
        }
    
    def get_monthly_usage(self, year_month=None):
        """Get usage for current month"""
        if year_month is None:
            year_month = datetime.now().strftime('%Y-%m')
        
        conn = sqlite3.connect(str(self.db_path))
        result = conn.execute('''
            SELECT 
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost,
                SUM(items_processed) as items,
                COUNT(*) as jobs
            FROM token_usage 
            WHERE strftime('%Y-%m', timestamp) = ?
        ''', (year_month,)).fetchone()
        conn.close()
        
        return {
            'month': year_month,
            'total_tokens': result[0] or 0,
            'total_cost': result[1] or 0.0,
            'items_processed': result[2] or 0,
            'budget_remaining': 15.0 - (result[1] or 0.0),
            'jobs_run': result[3] or 0
        }
    
    def get_job_breakdown(self, days=7):
        """Get breakdown by job type for last N days"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute('''
            SELECT 
                job_name,
                COUNT(*) as runs,
                SUM(items_processed) as items,
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost,
                AVG(duration_ms) as avg_duration
            FROM token_usage 
            WHERE timestamp > datetime('now', '-' || ? || ' days')
            GROUP BY job_name
            ORDER BY runs DESC
        ''', (days,))
        
        results = []
        for row in cursor:
            results.append({
                'job_name': row[0],
                'runs': row[1],
                'items': row[2] or 0,
                'tokens': row[3] or 0,
                'cost': row[4] or 0.0,
                'avg_duration_ms': int(row[5] or 0)
            })
        
        conn.close()
        return results

if __name__ == '__main__':
    # Test the tracker
    tracker = UsageTracker()
    
    with tracker.track_job('test', 'tracker_test') as job:
        job['items_processed'] = 10
        print("Tracker test successful!")
    
    # Show today's stats
    stats = tracker.get_daily_usage()
    print(f"Today: {stats['jobs_run']} jobs, {stats['items_processed']} items processed")
