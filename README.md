# LinuxGuard – Intelligent Linux Server Monitoring & Auto-Remediation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-092E20.svg)](https://www.djangoproject.com/)
[![Ubuntu](https://img.shields.io/badge/Platform-Ubuntu%20%2F%20Linux-E95420.svg)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-36%20Passed-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Frontend-SSR%20(No%20JS)-success.svg)](templates/)

---

## 1. Project Overview

**LinuxGuard** is an enterprise-grade, real-time Linux server monitoring, incident correlation, and controlled auto-remediation platform built strictly with **Python**, **Django**, **Bash**, **SQL**, and **HTML5/CSS3**—with **zero client-side JavaScript**.

Designed for high-reliability infrastructure operations, system administrators, and DevSecOps teams, LinuxGuard continuously ingests real host metrics (CPU, Memory, Disk, Network, Systemd daemons, SSH authentication logs, system journals), detects anomalies, correlates root causes using rule-based diagnostic engines, and provides automated, self-healing remediation for predefined safe operations while enforcing strict human-in-the-loop approval workflows for sensitive actions.

---

## 2. Problem Statement

Modern server infrastructure management faces critical operational challenges:
1. **Alert Fatigue & Delayed MTTR**: Monitoring tools bombard engineers with raw metric alerts without identifying the underlying root cause (e.g., alert on high CPU without pointing out runaway process PID).
2. **Fragile Client-Side Dashboards**: Heavy client-side JavaScript frameworks (React, Vue, Node.js) introduce complex dependencies, browser memory overhead, and security vulnerabilities in locked-down operational environments.
3. **Risky Auto-Remediation**: Uncontrolled automation scripts that execute arbitrary shell commands can lead to unintended outages, data loss, or command injection vulnerabilities.
4. **Lack of Auditability**: Automated corrective actions frequently lack comprehensive audit trails recording what ran, who approved it, and whether the system successfully recovered.

---

## 3. Objectives

- **100% Server-Side Rendered (SSR) Dashboard**: Deliver a fast, responsive, and secure UI using pure HTML5 and CSS3 without requiring JavaScript.
- **Real Linux Telemetry**: Gather real kernel and system hardware metrics using `psutil`, `/proc`, and safe Linux utilities (`top`, `df`, `free`, `uptime`, `systemctl`, `journalctl`, `ss`, `ip`).
- **Intelligent Anomaly Detection & Deduplication**: Detect threshold violations across CPU, RAM, Disk, dead services, and SSH brute-force attacks while avoiding duplicate incident spamming.
- **Rule-Based Root Cause Diagnosis**: Correlate system symptoms with actionable root causes, confidence ratings, and evidence summaries.
- **Safe & Audited Auto-Remediation**: Execute predefined, allowlisted remediation commands via `subprocess.run(shell=False)` with post-restart verification and full audit logging.
- **Enterprise RBAC**: Enforce Role-Based Access Control (`ADMIN`, `OPERATOR`, `VIEWER`) across all views and action endpoints.

---

## 4. Features

- **Real-Time Telemetry & Gauges**: Live CPU utilization, per-core metrics, RAM/Swap utilization, disk partition saturation, load averages (1m, 5m, 15m), and network I/O counters.
- **Process Monitoring & Inspection**: Live sorted process tables (Top CPU, Top Memory, PID search, user filtering).
- **Systemd Daemon Health**: Safe monitoring of critical Linux daemons (`ssh`, `nginx`, `docker`, `mysql`, `postgresql`) with automatic existence verification.
- **Storage & Disk Diagnostic Reports**: Multi-partition capacity inspection, inode exhaustion tracking, and `/var/log` consumption breakdowns.
- **SSH Security & Brute-Force Detection**: Detection of repeated authentication failures within configurable time windows with severity escalation.
- **Automated Self-Healing**: Safe automatic recovery restarts for allowlisted daemons (e.g., `nginx`, `docker`, `mysql`, `postgresql`) with state validation.
- **Manual & Admin-Approved Remediation**: Safe manual triggers for Operators; approval queue for sensitive actions.
- **Immutable Audit Logging**: Every login, telemetry refresh, incident update, settings change, and remediation execution is permanently recorded.
- **Configurable Thresholds**: Dynamic UI configuration for CPU, RAM, Disk thresholds, SSH attempt limits, and auto-remediation policies.

---

## 5. Architecture

```
                      +------------------------------------------+
                      |         Target Linux / Ubuntu Server     |
                      |   (psutil, systemctl, journalctl, /proc) |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |       Python Monitoring Services         |
                      | (System, Process, Service, SSH, Disk)    |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |      Detection & Anomaly Engine          |
                      |    (Threshold Evaluation & Deduplication)|
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |           Incident Engine                |
                      |   (Severity Assessment: Low -> Critical) |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |          Root Cause Engine               |
                      |  (Probable Cause + Confidence + Evidence)|
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |         Remediation Engine               |
                      | (Safe Allowlist + Approval + Verification)|
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |          SQL Database (SQLite/MySQL)     |
                      |   (Servers, Metrics, Incidents, Audits)  |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |         Django Application (SSR)         |
                      | (Forms, Views, RBAC, Sessions, CSRF)     |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |        Pure HTML5 + CSS3 Dashboard       |
                      |          (ZERO JavaScript Engine)        |
                      +------------------------------------------+
```

---

## 6. Complete Operational Workflow

```
1. Ingest Telemetry ---> 2. Threshold Check ---> 3. Anomaly Detected
                                                          |
                                                          v
                                                 4. Incident Created
                                                          |
                                                          v
                                                 5. Root Cause Diagnosis
                                                          |
                                                          v
                        +---------------------------------+-------------------------------+
                        |                                                                 |
                [Safe Daemon Crash]                                           [Sensitive / High-Risk]
                        |                                                                 |
                        v                                                                 v
             6a. Auto-Remediation Triggered                                  6b. Queued for Admin Approval
                        |                                                                 |
                        v                                                                 v
             7a. `systemctl restart <svc>`                                   7b. Admin Reviews & Approves
                        |                                                                 |
                        v                                                                 v
             8a. Verify `systemctl is-active`                                8b. Safe Subprocess Execution
                        |                                                                 |
            +-----------+-----------+                                                     |
            |                       |                                                     |
        [Active]                [Failed]                                                  |
            |                       |                                                     |
            v                       v                                                     v
    Incident RESOLVED       Incident INVESTIGATING                                 Audit Log Recorded
```

---

## 7. Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+, Django 5.0+ | Server-side web framework, ORM, authentication, and management commands |
| **System Telemetry** | `psutil` | Hardware counters, CPU, RAM, Disk, network metrics, and process tables |
| **OS / Shell** | Linux / Ubuntu, Bash | System commands (`systemctl`, `journalctl`, `df`, `free`, `uptime`, `ss`, `ip`) |
| **Database** | SQLite (Default Dev) / MySQL | Relational persistence for models, telemetry history, and audit trails |
| **Testing** | `pytest`, `pytest-django` | Automated test suite with mocked Linux execution fixtures |
| **Frontend** | Pure HTML5 & CSS3 | Zero-JavaScript Server-Side Rendered (SSR) responsive user interface |
| **VCS** | Git | Distributed version control |

> **Strict Constraint Compliance**: No JavaScript, No TypeScript, No Node.js, No React, No Vue, No Angular, No Java. All interactions utilize standard HTML forms, GET/POST requests, HTTP redirects, and Django templates.

---

## 8. Folder Structure

```
linuxguard-server-monitoring-auto-remediation/
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules
├── manage.py                        # Django management CLI entrypoint
├── pytest.ini                       # Pytest configuration
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
│
├── linuxguard/                      # Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                  # Core settings, DB config, RBAC setup, thresholds
│   ├── urls.py                      # Global URL dispatcher
│   └── wsgi.py
│
├── monitoring/                      # Core LinuxGuard Application
│   ├── admin.py                     # Django admin integration
│   ├── apps.py                      # App configuration
│   ├── context_processors.py        # Global navigation badges context processor
│   ├── decorators.py                # RBAC decorators (@admin_required, @operator_required)
│   ├── forms.py                     # Standard HTML forms (Server, Filters, Settings)
│   ├── models.py                    # Relational DB models (Server, Incident, AuditLog, etc.)
│   ├── urls.py                      # Application URL routes
│   ├── views.py                     # SSR view handlers
│   │
│   ├── engines/                     # Modular Monitoring & Remediation Engines
│   │   ├── __init__.py
│   │   ├── anomaly_detector.py      # Threshold evaluation, deduplication, alert dispatch
│   │   ├── command_security.py      # Strict command allowlist, pattern sanitization
│   │   ├── disk_monitor.py          # Filesystem capacity, du /var/log analysis
│   │   ├── log_analyzer.py          # Linux journalctl & log analysis
│   │   ├── network_monitor.py       # Socket connections, network counters, ping
│   │   ├── process_monitor.py       # psutil process enumeration & sorting
│   │   ├── remediation_engine.py    # Self-healing workflow & post-execution verification
│   │   ├── root_cause_engine.py     # Rule-based diagnostic correlation engine
│   │   ├── service_monitor.py       # Safe systemctl service health checker
│   │   ├── severity_engine.py       # Dynamic incident severity calculator
│   │   ├── ssh_monitor.py           # SSH brute-force & auth failure detector
│   │   └── system_monitor.py        # psutil hardware snapshot collector
│   │
│   └── management/
│       └── commands/
│           ├── monitor_server.py    # Periodic monitoring background worker CLI
│           └── seed_demo_data.py    # Initial RBAC users and seed node generator
│
├── scripts/                         # Linux Bash Automation Scripts
│   ├── collect_logs.sh              # System log archiving utility
│   ├── disk_report.sh               # Disk and directory space report
│   ├── health_check.sh              # Terminal-based host health diagnostic
│   └── setup_ubuntu.sh              # Ubuntu deployment and provisioning script
│
├── static/
│   └── css/
│       └── style.css                # Enterprise design system CSS
│
├── templates/                       # Server-Side Rendered Django Templates
│   ├── base.html                    # Base layout with sidebar navigation
│   ├── audit/index.html             # Audit trail search and logs
│   ├── auth/login.html              # Authentication login screen
│   ├── auth/profile.html            # User profile and role permissions
│   ├── dashboard/index.html         # Main command center dashboard
│   ├── incidents/list.html          # Incident management table
│   ├── incidents/detail.html        # Root cause analysis & remediation action view
│   ├── metrics/index.html           # Detailed hardware telemetry & partition tables
│   ├── processes/index.html         # Live process table with sorting/filtering
│   ├── remediation/list.html        # Remediation actions & approval queue
│   ├── security/index.html          # Security events & attacking IP analytics
│   ├── servers/list.html            # Monitored server inventory
│   ├── servers/detail.html          # Server health view & aggregate stats
│   ├── servers/form.html            # Add / Edit server form
│   ├── servers/delete_confirm.html  # Server deletion confirmation
│   ├── services/index.html          # Systemd daemon health & restart controls
│   └── settings/index.html          # Dynamic threshold configuration
│
└── tests/                           # Pytest Test Suite
    ├── conftest.py                  # Pytest fixtures and mock setups
    ├── test_anomaly_detector.py     # Threshold and deduplication tests
    ├── test_audit_logging.py        # Audit trail and view SSR tests
    ├── test_auth_rbac.py            # RBAC roles and permission tests
    ├── test_command_security.py     # Command allowlisting and safety tests
    ├── test_disk_monitor.py         # Disk and network telemetry tests
    ├── test_log_analyzer.py         # Log parser and brute force tests
    ├── test_process_monitor.py      # Process enumeration tests
    ├── test_service_monitor.py      # Service checker and mock tests
    ├── test_severity_engine.py      # Severity and root cause diagnosis tests
    └── test_system_monitor.py       # psutil hardware extraction tests
```

---

## 9. Linux Commands Used

LinuxGuard strictly utilizes standard, safe Linux commands:

| Command | Purpose | Invocation Method | Safety Control |
| :--- | :--- | :--- | :--- |
| `systemctl is-active <svc>` | Query service running state | `subprocess.run(shell=False)` | Service allowlist validation |
| `systemctl restart <svc>` | Safe service recovery | `subprocess.run(shell=False)` | Service allowlist validation |
| `systemctl list-unit-files` | Verify unit existence | `subprocess.run(shell=False)` | Service allowlist validation |
| `journalctl -u <svc> -n 50` | Extract service crash logs | `subprocess.run(shell=False)` | Service allowlist validation |
| `journalctl -p err..alert` | Ingest system error logs | `subprocess.run(shell=False)` | Predefined token list |
| `df -h` | Mounted partition usage | `subprocess.run(shell=False)` | Predefined token list |
| `du -sh /var/log/*` | Storage breakdown | `scripts/disk_report.sh` | Bash script |
| `free -m` / `free -h` | RAM and swap inspection | `scripts/health_check.sh` | Bash script |
| `uptime` | System uptime & load averages | `subprocess.run(shell=False)` | Predefined token list |
| `ss -tuln` | Open TCP/UDP ports | `subprocess.run(shell=False)` | Predefined token list |
| `ip -brief address` | Network interfaces and IPs | `subprocess.run(shell=False)` | Predefined token list |
| `top -b -n 1` | Head process snapshot | `scripts/health_check.sh` | Bash script |

---

## 10. Database Design & SQL Concepts

LinuxGuard utilizes the **Django ORM** for persistent relational storage while adhering strictly to standard SQL concepts:

### Relational Schema Entities

1. **`monitoring_user`**: Custom user table with role column (`ADMIN`, `OPERATOR`, `VIEWER`), department, and hashed credentials.
2. **`monitoring_server`**: Monitored hosts with hostname, IP address, OS, status, and heartbeat timestamps.
3. **`monitoring_systemmetric`**: Time-series telemetry snapshots (CPU %, RAM %, Disk %, Network I/O, Load average).
4. **`monitoring_processmetric`**: Process snapshot records linked to host servers.
5. **`monitoring_servicestatus`**: Health states of monitored systemd units.
6. **`monitoring_incident`**: Detected incidents with root cause analysis, confidence scores, and recommendations.
7. **`monitoring_remediationaction`**: Remediation proposals, execution logs, and approval links.
8. **`monitoring_auditlog`**: Immutable operational audit trail.
9. **`monitoring_securityevent`**: SSH brute force events and authentication anomalies.
10. **`monitoring_systemsetting`**: Dynamic threshold key-value configuration.

### SQL Equivalency & Demonstration

| SQL Operation | Django ORM Equivalent in Code | Purpose |
| :--- | :--- | :--- |
| **`SELECT` / `WHERE`** | `Incident.objects.filter(status='OPEN', severity='CRITICAL')` | Querying open critical incidents |
| **`INSERT`** | `SystemMetric.objects.create(server=server, cpu_usage=88.5, ...)` | Recording metric snapshots |
| **`UPDATE`** | `incident.status = 'RESOLVED'; incident.save()` | Updating incident status |
| **`DELETE`** | `server.delete()` | Removing decommissioned server |
| **`ORDER BY`** | `Incident.objects.order_by('-detected_at')` | Ordering incidents chronologically |
| **`GROUP BY` & `COUNT`** | `SecurityEvent.objects.values('source_ip').annotate(attack_count=Count('id'))` | Aggregating attacks per IP |
| **`JOIN`** | `Incident.objects.select_related('server')` | Single-query SQL inner join |
| **`AVG`, `MAX`, `MIN`** | `server.system_metrics.aggregate(Avg('cpu_usage'), Max('cpu_usage'), Min('cpu_usage'))` | Statistical telemetry aggregation |

---

## 11. Installation & Quickstart

### Prerequisites

- **Python**: 3.10, 3.11, or 3.12
- **Operating System**: Ubuntu 20.04 / 22.04 / 24.04 LTS (or compatible Linux / development host)
- **Git**

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/Vishal-Bhavar96/linuxguard-server-monitoring-auto-remediation.git
cd linuxguard-server-monitoring-auto-remediation

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment configuration
cp .env.example .env

# 5. Apply database migrations
python manage.py makemigrations monitoring
python manage.py migrate

# 6. Seed demo accounts & nodes
python manage.py seed_demo_data
```

### Pre-Configured Demo Accounts

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **`admin`** | `Admin123!` | **`ADMIN`** | Full access, modify settings, approve remediations, manage servers |
| **`operator`** | `Operator123!` | **`OPERATOR`** | Monitor telemetry, manage incidents, trigger safe remediations |
| **`viewer`** | `Viewer123!` | **`VIEWER`** | Read-only observation across all dashboards |

---

## 12. Ubuntu Setup

For complete Ubuntu provisioning, run the automated setup script:

```bash
chmod +x scripts/*.sh
./scripts/setup_ubuntu.sh
```

### Optional MySQL Setup on Ubuntu

If using MySQL instead of SQLite:

```bash
sudo apt-get install -y mysql-server libmysqlclient-dev
sudo mysql -e "CREATE DATABASE linuxguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'linuxguard'@'localhost' IDENTIFIED BY 'StrongPassword123!';"
sudo mysql -e "GRANT ALL PRIVILEGES ON linuxguard.* TO 'linuxguard'@'localhost'; FLUSH PRIVILEGES;"
```

Update `.env`:
```ini
DB_ENGINE=mysql
DB_NAME=linuxguard
DB_USER=linuxguard
DB_PASSWORD=StrongPassword123!
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

## 13. Running Django Web Console

```bash
python manage.py runserver 0.0.0.0:8000
```

Open your browser at: **`http://localhost:8000/`**

---

## 14. Running Monitor Command

LinuxGuard includes a background telemetry collection and self-healing management command:

```bash
# Continuous monitoring with a 30-second interval
python manage.py monitor_server --interval 30

# Single execution cycle (useful for cron jobs or CI verification)
python manage.py monitor_server --once

# Monitor a specific server ID
python manage.py monitor_server --server-id 1 --interval 15
```

### Automated Monitoring Cycle Execution

1. Ingests real hardware snapshot via `psutil`.
2. Enumerates top consuming CPU/RAM processes.
3. Queries systemd daemon states (`ssh`, `nginx`, `docker`, `mysql`, `postgresql`).
4. Ingests auth logs and detects repeated SSH brute-force attempts.
5. Evaluates threshold violations and creates deduplicated incidents.
6. Invokes rule-based diagnostic engine to infer root causes and recommendations.
7. Executes safe automatic remediation (e.g., restarting stopped `nginx`) if configured.
8. Writes all operations to the immutable `AuditLog`.

---

## 15. Running Tests

LinuxGuard includes a comprehensive test suite covering RBAC, models, monitoring engines, command security, and views:

```bash
pytest
```

To run with detailed test execution output:

```bash
pytest -v
```

---

## 16. Security & Command Allowlisting

LinuxGuard implements a defense-in-depth security architecture:

1. **No Client-Side JavaScript**: Eliminates DOM-based XSS, vulnerable NPM dependencies, and script injection vectors.
2. **Strict Command Allowlisting**: Only allowlisted commands with predefined token templates can be executed.
3. **Safe Subprocess Execution**: All system operations are invoked with `shell=False`, preventing shell injection vulnerabilities.
4. **Forbidden Pattern Prevention**: Explicitly blocks dangerous patterns (`rm`, `rm -rf`, `shutdown`, `reboot`, `kill -9`, `chmod -R`, `chown -R`, `mkfs`, `dd`).
5. **Service Name Validation**: Validates all service parameters against a strict set of alphanumeric identifiers (`ssh`, `sshd`, `nginx`, `docker`, `mysql`, `mariadb`, `postgresql`).
6. **Timeouts**: All system subprocess calls enforce strict execution timeouts (10s – 30s).
7. **CSRF & Session Security**: All state-modifying requests require valid Django CSRF tokens and authenticated sessions.
8. **RBAC Enforcement**: Server management and threshold changes require `@admin_required`; remediation actions require `@operator_required`.

---

## 17. Auto-Remediation & Self-Healing Engine

### Remediation Matrix

| Incident Type | Detected Condition | Remediation Action | Approval Requirement | Post-Execution Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Service Failure** | `nginx` status: `INACTIVE` / `FAILED` | `systemctl restart nginx` | Safe Automated (or Manual) | Checks `systemctl is-active`; marks `RESOLVED` on success |
| **Service Failure** | `docker` status: `FAILED` | `systemctl restart docker` | Safe Automated (or Manual) | Verifies running state |
| **Service Crash** | Unresponsive database | `journalctl -u <svc> -n 50` | Manual Operator Trigger | Captures diagnostic stack traces |
| **Disk Warning** | Partition > 80% capacity | Clear temp files > 7 days old | Requires Admin Approval | Re-evaluates disk usage |
| **High CPU Process** | Single process > 80% CPU | Graceful reload / restart worker | Requires Admin Approval | Verifies CPU reduction |

---

## 18. User Interface & Dashboard Showcase

The LinuxGuard UI is designed using an enterprise Linux palette:
- **Background**: `#F8FAFC`
- **Cards & Panels**: `#FFFFFF`
- **Primary Navy**: `#1E3A5F`
- **Accent Blue**: `#2563EB`
- **Success**: `#15803D`
- **Warning**: `#B45309`
- **Critical**: `#B91C1C`

### ASCII UI Layout Overview

```
+-------------------------------------------------------------------------------------------+
| [LG] LinuxGuard  |  Platform Overview                            [↻ Sample Telemetry] [👤] |
+------------------+------------------------------------------------------------------------+
| CORE             |                                                                        |
| > Dashboard      |  +----------------+ +----------------+ +----------------+ +------------+ |
| > Servers (3)    |  | TOTAL SERVERS  | | HEALTHY NODES  | | OPEN INCIDENTS | | CRITICAL   | |
|                  |  |      3         | |      2         | |      2         | |    1       | |
| TELEMETRY        |  +----------------+ +----------------+ +----------------+ +------------+ |
| > System Metrics |                                                                        |
| > Process Table  |  LOCAL HOST TELEMETRY: ubuntu-srv-prod (192.168.1.10)                  |
| > Service Health |  +--------------------------------------------------------------------+ |
|                  |  | CPU Utilization   [████████████████░░░░░░░░] 68.4% (8 Cores)      | |
| INCIDENTS        |  | RAM Usage         [████████████████████░░░░] 81.2% (13.0 / 16.0 GB)| |
| > Incidents (2)  |  | Root Disk Space   [██████████████████████░░] 88.0% (88.0 / 100 GB) | |
| > Auto-Healing   |  | Load Average      0.85, 0.92, 0.78  |  Uptime: 14d 6h 32m          | |
|                  |  +--------------------------------------------------------------------+ |
| SECURITY         |                                                                        |
| > Security (1)   |  CRITICAL INCIDENTS & ROOT CAUSE                                       |
| > Audit Trail    |  +--------------------------------------------------------------------+ |
| > Settings       |  | [CRITICAL] Memory Exhaustion on Web Node 01                        | |
|                  |  | Probable Cause: High RAM allocation in worker process (PID 4821)   | |
|                  |  | Confidence: 90% | Recommendation: Restart daemon and profile memory | |
|                  |  +--------------------------------------------------------------------+ |
+------------------+------------------------------------------------------------------------+
```

---

## 19. Bash Automation Scripts

### 1. `scripts/health_check.sh`
Performs an instant command-line health audit of the host server:
- System uptime and load averages
- CPU usage via `mpstat` or `top`
- Memory and Swap usage via `free -h`
- Filesystem capacity via `df -h`
- Active network interfaces via `ip -brief address`
- Listening ports via `ss -tuln`
- Systemd daemon health states (`ssh`, `nginx`, `docker`, `mysql`, `postgresql`)

### 2. `scripts/disk_report.sh`
Generates a detailed storage utilization report:
- Mounted filesystem capacity and inode consumption
- Top 10 largest directories in `/var/log`
- `/tmp` dump size

### 3. `scripts/collect_logs.sh`
Collects and archives diagnostic logs into a timestamped directory:
- Systemd error journals (`journalctl -p err..alert`)
- Authentication logs (`/var/log/auth.log`)
- Nginx and MySQL error logs
- Host hardware summary manifest

---

## 20. Future Scope

- **Multi-Node SSH Agent Ingestion**: Distributed telemetry collection over encrypted SSH tunnels.
- **Webhook & Alert Integrations**: Outbound email, Slack, and PagerDuty notification channels.
- **Automated Memory Profiling**: Deep process heap profiling triggers for sustained RAM leaks.
- **Custom Remediation Playbooks**: User-defined YAML runbooks with step-by-step verification gates.

---

## 21. License

This project is licensed under the **MIT License**.
