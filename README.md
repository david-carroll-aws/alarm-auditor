# alarm-auditor
CloudWatch alarms can silently add cost to monthly bills if not correctly managed. This AWS tool runs an audit on all alarms in an account and scanning for alarms which are silent, orphaned, stale or duplicates. After discovery admins can take corrective action to remediate issues. This project could be auto set to run weekly/monthly.
