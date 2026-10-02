# Alarm Auditor - cost savings
CloudWatch alarms can silently add cost to monthly bills if not correctly managed. This AWS tool runs an audit on all alarms in an account and scanning for alarms which are silent, orphaned, stale or duplicates. After discovery admins can take corrective action to remediate issues. This project could be auto set to run weekly/monthly.

Create an API called 'audit' allowed to GET, integrate it with the lambda function, set CORS appropriately, and ensure the lambda function has sufficient permissions.

View the alarm auditor in action at davidcarroll.cloud
