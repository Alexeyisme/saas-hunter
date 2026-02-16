#!/usr/bin/env python3
"""
Weekly Data Quality Review
Analyzes the past week of SaaS Hunter data and generates improvement recommendations
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any
from utils import setup_logging

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
REPORTS_DIR = DATA_DIR / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'weekly_review.log')


def load_opportunities_from_week(days_back=7):
    """Load all processed opportunities from the past week"""
    cutoff = datetime.now() - timedelta(days=days_back)
    opportunities = []
    
    for file in sorted(PROCESSED_DIR.glob('opportunities_*.jsonl')):
        file_date = datetime.strptime(file.stem.split('_')[1], '%Y%m%d')
        if file_date >= cutoff:
            with open(file, 'r') as f:
                for line in f:
                    try:
                        opp = json.loads(line.strip())
                        opportunities.append(opp)
                    except json.JSONDecodeError:
                        continue
    
    return opportunities


def analyze_source_quality(opps: List[Dict]) -> Dict[str, Any]:
    """Analyze quality metrics per source"""
    by_source = defaultdict(list)
    
    for opp in opps:
        source = opp.get('source', 'unknown')
        by_source[source].append(opp)
    
    source_stats = {}
    for source, source_opps in by_source.items():
        scores = [o.get('score', 0) for o in source_opps]
        source_stats[source] = {
            'count': len(source_opps),
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'high_quality_count': len([s for s in scores if s >= 60]),
            'top_tier_count': len([s for s in scores if s >= 80])
        }
    
    return source_stats


def analyze_score_distribution(opps: List[Dict]) -> Dict[str, Any]:
    """Analyze overall score distribution"""
    scores = [o.get('score', 0) for o in opps]
    
    buckets = {
        'excellent (80+)': len([s for s in scores if s >= 80]),
        'high (60-79)': len([s for s in scores if 60 <= s < 80]),
        'medium (40-59)': len([s for s in scores if 40 <= s < 60]),
        'low (<40)': len([s for s in scores if s < 40])
    }
    
    return {
        'total': len(scores),
        'average': sum(scores) / len(scores) if scores else 0,
        'median': sorted(scores)[len(scores) // 2] if scores else 0,
        'max': max(scores) if scores else 0,
        'buckets': buckets
    }


def analyze_llm_usage(opps: List[Dict]) -> Dict[str, Any]:
    """Analyze LLM enhancement usage and effectiveness"""
    llm_enhanced = [o for o in opps if 'llm_analysis' in o]
    
    if not llm_enhanced:
        return {
            'enabled': False,
            'count': 0
        }
    
    total_cost = sum(o.get('llm_analysis', {}).get('cost_usd', 0) for o in llm_enhanced)
    total_tokens = sum(o.get('llm_analysis', {}).get('tokens', {}).get('total_tokens', 0) for o in llm_enhanced)
    
    # Calculate impact: how much did LLM change scores?
    score_changes = []
    for o in llm_enhanced:
        llm_data = o.get('llm_analysis', {})
        base = llm_data.get('base_score', 0)
        final = llm_data.get('final_score', 0)
        if base and final:
            score_changes.append(final - base)
    
    return {
        'enabled': True,
        'count': len(llm_enhanced),
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'avg_cost_per_item': total_cost / len(llm_enhanced) if llm_enhanced else 0,
        'score_changes': {
            'avg_change': sum(score_changes) / len(score_changes) if score_changes else 0,
            'max_increase': max(score_changes) if score_changes else 0,
            'max_decrease': min(score_changes) if score_changes else 0
        }
    }


def analyze_engagement_patterns(opps: List[Dict]) -> Dict[str, Any]:
    """Analyze engagement vs. score correlation"""
    high_engagement_low_score = []
    low_engagement_high_score = []
    
    for o in opps:
        engagement = o.get('engagement_data', {})
        score = o.get('score', 0)
        
        comments = engagement.get('comments', 0)
        reactions = engagement.get('reactions', 0)
        
        total_engagement = comments + reactions
        
        # High engagement (10+) but low score (<50)
        if total_engagement >= 10 and score < 50:
            high_engagement_low_score.append({
                'title': o.get('title', '')[:60],
                'score': score,
                'engagement': total_engagement,
                'source': o.get('source', '')
            })
        
        # Low engagement (<5) but high score (60+)
        if total_engagement < 5 and score >= 60:
            low_engagement_high_score.append({
                'title': o.get('title', '')[:60],
                'score': score,
                'engagement': total_engagement,
                'source': o.get('source', '')
            })
    
    return {
        'high_engagement_low_score': high_engagement_low_score[:5],  # Top 5
        'low_engagement_high_score': low_engagement_high_score[:5]
    }


def analyze_domains(opps: List[Dict]) -> Dict[str, int]:
    """Analyze domain distribution"""
    domains = [o.get('domain', 'other') for o in opps]
    return dict(Counter(domains).most_common())


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate actionable improvement recommendations"""
    recommendations = []
    
    # Source quality recommendations
    source_stats = analysis['source_quality']
    low_quality_sources = [
        (source, stats) for source, stats in source_stats.items()
        if stats['avg_score'] < 35 and stats['count'] > 5
    ]
    
    if low_quality_sources:
        for source, stats in low_quality_sources[:3]:
            recommendations.append(
                f"🔴 **Low quality source**: {source} (avg score: {stats['avg_score']:.1f}, "
                f"{stats['count']} items) - Consider removing or adjusting filters"
            )
    
    # High performers
    high_quality_sources = [
        (source, stats) for source, stats in source_stats.items()
        if stats['avg_score'] > 50 and stats['high_quality_count'] > 0
    ]
    
    if high_quality_sources:
        for source, stats in sorted(high_quality_sources, key=lambda x: x[1]['avg_score'], reverse=True)[:3]:
            recommendations.append(
                f"🟢 **High quality source**: {source} (avg score: {stats['avg_score']:.1f}, "
                f"{stats['high_quality_count']} high-quality) - Keep monitoring closely"
            )
    
    # LLM effectiveness
    if analysis['llm_usage']['enabled']:
        llm = analysis['llm_usage']
        weekly_cost = llm['total_cost']
        monthly_projection = weekly_cost * 4.3
        
        if monthly_projection > 15:
            recommendations.append(
                f"🟡 **Budget alert**: LLM costs trending high (${monthly_projection:.2f}/month projected). "
                f"Consider raising threshold or reducing LLM weight."
            )
        
        avg_change = llm['score_changes']['avg_change']
        if abs(avg_change) < 3:
            recommendations.append(
                f"🟡 **LLM impact low**: Average score change is only {avg_change:.1f} points. "
                f"Consider adjusting LLM weight or threshold."
            )
    
    # Score distribution
    dist = analysis['score_distribution']
    if dist['buckets']['low (<40)'] > dist['total'] * 0.5:
        recommendations.append(
            f"🟡 **High noise ratio**: {dist['buckets']['low (<40)']} low-quality items "
            f"({dist['buckets']['low (<40)'] / dist['total'] * 100:.1f}%). "
            f"Consider tightening keyword filters or raising thresholds."
        )
    
    if dist['buckets']['excellent (80+)'] == 0:
        recommendations.append(
            "🟡 **No top-tier opportunities**: Consider expanding sources or adjusting scoring config."
        )
    
    # Engagement patterns
    engagement = analysis['engagement_patterns']
    if len(engagement['high_engagement_low_score']) > 3:
        recommendations.append(
            f"🟡 **Scoring mismatch**: {len(engagement['high_engagement_low_score'])} high-engagement "
            f"items scored low. Review scoring weights for engagement signals."
        )
    
    if not recommendations:
        recommendations.append("✅ **All systems healthy**: No major issues detected this week.")
    
    return recommendations


def generate_report(analysis: Dict[str, Any], recommendations: List[str]) -> str:
    """Generate markdown report"""
    report = []
    report.append("# 📊 SaaS Hunter - Weekly Data Quality Report")
    report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")
    
    # Overview
    report.append("## 📈 Overview")
    dist = analysis['score_distribution']
    report.append(f"- **Total opportunities**: {dist['total']}")
    report.append(f"- **Average score**: {dist['average']:.1f}")
    report.append(f"- **High quality (60+)**: {dist['buckets']['high (60-79)'] + dist['buckets']['excellent (80+)']}")
    report.append(f"- **Top tier (80+)**: {dist['buckets']['excellent (80+)']}")
    
    if analysis['llm_usage']['enabled']:
        llm = analysis['llm_usage']
        report.append(f"- **LLM enhanced**: {llm['count']} (${llm['total_cost']:.4f} cost)")
    
    report.append("")
    
    # Score distribution
    report.append("## 🎯 Score Distribution")
    for bucket, count in dist['buckets'].items():
        pct = (count / dist['total'] * 100) if dist['total'] > 0 else 0
        report.append(f"- {bucket}: {count} ({pct:.1f}%)")
    report.append("")
    
    # Source quality
    report.append("## 🔍 Source Quality")
    source_stats = analysis['source_quality']
    sorted_sources = sorted(
        source_stats.items(),
        key=lambda x: x[1]['avg_score'],
        reverse=True
    )
    
    for source, stats in sorted_sources:
        report.append(f"- **{source}**: {stats['count']} items, avg {stats['avg_score']:.1f}, "
                     f"{stats['high_quality_count']} high-quality")
    report.append("")
    
    # Domains
    report.append("## 🏷️ Top Domains")
    for domain, count in list(analysis['domains'].items())[:10]:
        report.append(f"- {domain}: {count}")
    report.append("")
    
    # LLM analysis
    if analysis['llm_usage']['enabled']:
        report.append("## 🤖 LLM Enhancement")
        llm = analysis['llm_usage']
        report.append(f"- **Enhanced**: {llm['count']} opportunities")
        report.append(f"- **Total cost**: ${llm['total_cost']:.4f}")
        report.append(f"- **Avg cost/item**: ${llm['avg_cost_per_item']:.6f}")
        report.append(f"- **Total tokens**: {llm['total_tokens']:,}")
        report.append(f"- **Avg score change**: {llm['score_changes']['avg_change']:+.1f} points")
        report.append(f"- **Max increase**: {llm['score_changes']['max_increase']:+.1f}")
        report.append(f"- **Max decrease**: {llm['score_changes']['max_decrease']:+.1f}")
        
        monthly_cost = llm['total_cost'] * 4.3
        report.append(f"- **Monthly projection**: ${monthly_cost:.2f}")
        report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    for rec in recommendations:
        report.append(f"{rec}\n")
    
    return '\n'.join(report)


def main():
    """Run weekly review"""
    logger.info("=" * 60)
    logger.info("Weekly Data Quality Review")
    logger.info("=" * 60)
    
    # Load data
    logger.info("Loading opportunities from past 7 days...")
    opps = load_opportunities_from_week(days_back=7)
    logger.info(f"Loaded {len(opps)} opportunities")
    
    if not opps:
        logger.warning("No opportunities found for review period")
        print("⚠️ No data to review")
        return
    
    # Run analyses
    logger.info("Running analyses...")
    analysis = {
        'source_quality': analyze_source_quality(opps),
        'score_distribution': analyze_score_distribution(opps),
        'llm_usage': analyze_llm_usage(opps),
        'engagement_patterns': analyze_engagement_patterns(opps),
        'domains': analyze_domains(opps)
    }
    
    # Generate recommendations
    logger.info("Generating recommendations...")
    recommendations = generate_recommendations(analysis)
    
    # Generate report
    report = generate_report(analysis, recommendations)
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d')
    report_file = REPORTS_DIR / f'weekly_review_{timestamp}.md'
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Report saved to {report_file}")
    logger.info("=" * 60)
    
    # Print summary
    print(f"✅ Weekly review complete")
    print(f"📄 Report: {report_file}")
    print(f"\n{len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"  {rec}")


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Weekly review failed: {e}", exc_info=True)
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
