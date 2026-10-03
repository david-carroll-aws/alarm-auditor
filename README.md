# Alarm Auditor - cost savings
CloudWatch alarms can silently add cost to monthly bills if not correctly managed. This AWS tool runs an audit on all alarms in an account and scanning for alarms which are silent, orphaned, stale or duplicates. After discovery admins can take corrective action to remediate issues. This project could be auto set to run weekly/monthly.

A serverless auditor that scans every CloudWatch alarm in an AWS account and flags the ones that are **silent**, **orphaned**, **stale**, or **duplicated** — with a health score and a monthly cost estimate.

View the alarm auditor in action at davidcarroll.cloud

Read-only by design. Never modifies the account.

<img width="1318" height="584" alt="image" src="https://github.com/user-attachments/assets/6b397ff2-1cc5-4ceb-b431-c43e91e95ddd" />


---

## Architecture

```
┌───────────────────┐
│   Browser         │  Single-page dashboard (alarmaudit.html)
│   (alarmaudit)    │  Renders score, findings list, remediation flow
└─────────┬─────────┘
          │ GET /audit
          ▼
┌───────────────────┐
│   API Gateway     │  HTTP API  ·  CORS enabled
└─────────┬─────────┘
          │ Lambda proxy
          ▼
┌───────────────────┐        ┌──────────────────────┐
│   Lambda          │───────▶│  CloudWatch API      │
│   (audit handler) │        │  describe_alarms     │
│   Python 3.12     │◀───────│  (paginated)         │
└─────────┬─────────┘        └──────────────────────┘
          │
          │  JSON response:
          │  { score, total_alarms, problematic_count,
          │    potential_monthly_savings, findings[], scanned_at }
          ▼
┌───────────────────┐
│   Browser UI      │  Score card + findings list + remediation modal
└───────────────────┘
```

**Read-only by design.** The Lambda calls `DescribeAlarms` only — it never deletes, disables, or modifies anything. Remediation is intentionally not wired up: the UI shows the `aws cloudwatch delete-alarms` command that *would* run in a real deployment, but takes no action.

---

## What It Finds

| Category       | Rule                                                        |
|----------------|-------------------------------------------------------------|
| **Silent**     | No actions configured — nobody would be notified on fire    |
| **Orphaned**   | No dimensions — points at no specific resource              |
| **Stale**      | Stuck in `INSUFFICIENT_DATA` for 30+ days                   |
| **Duplicates** | Same `(MetricName, Namespace, Threshold)` as another alarm  |

Each finding shows the alarm name, state, metric, a plain-language reason, and the estimated $0.10/month cost.

The **health score** is `(total − problematic) / total × 100`.

---

## Behind the Build

**The four heuristics.** AWS has no API for "this alarm is unused" — you have to infer it. Silent and orphaned are trivial field checks. Stale needs a timestamp comparison. Duplicates were the interesting one: you can't compare names, so the classifier builds a key from `(MetricName, Namespace, Threshold)` and tracks it in a single pass across the alarm list.

**Remediation that doesn't remediate.** The UI has a "Remediate selected" flow that opens a modal showing the exact `aws cloudwatch delete-alarms` command for the selected alarms — and takes no action. It's a deliberate choice: demonstrate the workflow, but don't let a portfolio project delete real infrastructure. The modal explains this explicitly.

---

## Stack

| Layer    | Technology                                          |
|----------|-----------------------------------------------------|
| Frontend | Vanilla HTML / CSS / JS — single file, no build     |
| Compute  | AWS Lambda (Python 3.12)                            |
| API      | Amazon API Gateway (HTTP API)                       |
| Data     | CloudWatch `describe_alarms` (paginated, read-only) |
| IAM      | `cloudwatch:DescribeAlarms` — nothing else          |

---

## Project Structure

```
/
├── lambda_handler.py     Lambda source (scan → classify → score)
└── alarmaudit.html       Single-page UI
```
