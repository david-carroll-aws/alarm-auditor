import boto3
import json
from datetime import datetime, timezone

cloudwatch = boto3.client('cloudwatch')


def lambda_handler(event, context):
    """
    Scan all CloudWatch alarms and identify:
    - Silent alarms (no actions configured)
    - Orphaned alarms (no dimensions)
    - Stale alarms (INSUFFICIENT_DATA for 30+ days)
    - Duplicates (same metric + threshold as another alarm)
    """
    alarms = fetch_all_alarms()
    findings = classify_all(alarms)
    score = calculate_score(alarms, findings)
    
    total_cost = round(sum(f['cost_per_month'] for f in findings), 2)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'score': score,
            'total_alarms': len(alarms),
            'problematic_count': len(findings),
            'potential_monthly_savings': total_cost,
            'findings': findings,
            'scanned_at': datetime.now(timezone.utc).isoformat()
        })
    }


def fetch_all_alarms():
    """Return every alarm in the account."""
    alarms = []
    paginator = cloudwatch.get_paginator('describe_alarms')
    for page in paginator.paginate():
        alarms.extend(page.get('MetricAlarms', []))
    return alarms


def classify_all(alarms):
    """Return a list of findings for alarms that have issues."""
    findings = []
    seen_metrics = {}
    
    for alarm in alarms:
        reasons = classify(alarm, seen_metrics)
        if reasons:
            findings.append({
                'name': alarm['AlarmName'],
                'state': alarm.get('StateValue', 'UNKNOWN'),
                'reasons': reasons,
                'cost_per_month': 0.10,
                'metric': alarm.get('MetricName', ''),
                'namespace': alarm.get('Namespace', '')
            })
        
        # Track metrics for duplicate detection
        key = (
            alarm.get('MetricName'),
            alarm.get('Namespace'),
            alarm.get('Threshold')
        )
        seen_metrics.setdefault(key, []).append(alarm['AlarmName'])
    
    return findings


def classify(alarm, seen_metrics):
    """Return a list of reasons why this alarm is problematic."""
    reasons = []
    
    # 1. Silent — no actions configured
    if not (alarm.get('AlarmActions') or
            alarm.get('OKActions') or
            alarm.get('InsufficientDataActions')):
        reasons.append('No actions configured — nobody would be notified')
    
    # 2. Orphaned — no dimensions
    if not alarm.get('Dimensions'):
        reasons.append('No dimensions — alarm points at no specific resource')
    
    # 3. Stale — stuck in INSUFFICIENT_DATA for 30+ days
    if alarm.get('StateValue') == 'INSUFFICIENT_DATA':
        updated = alarm.get('StateUpdatedTimestamp')
        if updated:
            if isinstance(updated, str):
                updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - updated
            if age.days > 30:
                reasons.append(f'Stuck in INSUFFICIENT_DATA for {age.days} days')
    
    # 4. Duplicate — same metric + threshold as another alarm
    key = (
        alarm.get('MetricName'),
        alarm.get('Namespace'),
        alarm.get('Threshold')
    )
    if len(seen_metrics.get(key, [])) > 1:
        others = [a for a in seen_metrics[key] if a != alarm['AlarmName']]
        if others:
            reasons.append(f'Duplicate of: {", ".join(others[:2])}')
    
    return reasons


def calculate_score(alarms, findings):
    total = len(alarms)
    if total == 0:
        return 100
    problematic = len(findings)
    return max(0, round(((total - problematic) / total) * 100))