# Product Requirements Document (PRD)

## Secure Employee Document Intake, Compliance & HRIS Sync Platform

**Working Name:** DocFlow HR (placeholder)
**Product Type:** B2B SaaS – HR / People Ops / Compliance
**Primary Buyers:** HR Directors, People Ops Leaders, Compliance Officers
**Secondary Buyers:** Legal, Payroll, IT

---

## 1. Executive Summary

DocFlow HR is a **secure, multi-channel employee document intake and compliance platform** that allows employees to submit employment-related documents via upload, email, SMS, or cloud storage. Documents are automatically classified, validated, retained by **state-specific rules**, and **bi-directionally synced** with leading HRIS platforms.

The system is designed to be **audit-ready by default**, with native **legal hold workflows**, immutable audit trails, and tight integration with **ADP**, **Gusto**, and **Workday**.

---

## 2. Target Market

### Launch Market

* **Florida**

### Expansion Markets (Fastest-Growing Employment Hubs)

* Austin, TX
* Phoenix, AZ
* Raleigh, NC
* Nashville, TN
* Tampa, FL

### Core Industries

* Healthcare
* Hospitality
* Construction
* Staffing & Recruiting
* Professional Services

---

## 3. Problem Statement

### Core Challenges

* Employee documents arrive via fragmented channels (email, text, screenshots)
* HRIS systems lack structured document intake workflows
* Manual filing creates compliance risk and audit gaps
* Retention requirements vary by state and document type
* Legal holds are handled ad-hoc and inconsistently

### Business Impact

* 5–10 hours/week lost per HR manager
* Increased litigation and regulatory exposure
* Incomplete or stale HRIS records
* Poor employee trust during onboarding and disputes

---

## 4. Solution Overview

DocFlow HR functions as the **authoritative intake, compliance, and audit layer**, while maintaining **bi-directional synchronization** with HRIS systems.

**Design Principles**

* Employee-first submission experience
* Compliance enforced automatically
* HRIS as a first-class integration, not an afterthought
* Legal readiness built into the core system

---

## 5. User Personas

### HR Administrator

* Owns employee records
* Manages compliance, audits, and retention
* Controls workflows and access

### Employee

* Submits documents from phone, email, or cloud drives
* Expects confirmation and transparency

### Legal / Compliance

* Initiates legal holds
* Requires immutable audit trails
* Oversees retention suspensions and discovery

---

## 6. Document Submission Channels

### 6.1 Web Upload

* Desktop & mobile
* Drag-and-drop
* Supported formats: PDF, JPG, PNG, DOCX, HEIC

### 6.2 Email Intake

* Employer-specific or employee-specific intake addresses
* HRIS-based sender-to-employee mapping
* Auto-confirmation emails

### 6.3 SMS Intake

**Provider:** **Twilio**

* Dedicated number per employer
* MMS file uploads
* One-time employee verification
* Submission receipts via SMS

### 6.4 Cloud Drive Imports

OAuth-based, file-level imports from:

* Dropbox
* Box
* Google Drive
* OneDrive

No full-drive sync; access is revocable at any time.

---

## 7. HRIS Integrations – Bi-Directional Sync (REQUIRED)

### Supported Systems (Phase 1)

* ADP
* Gusto
* Workday

### 7.1 Sync Directionality

#### HRIS → DocFlow HR

* Employee identity & profile data
* Employment status (active, LOA, terminated)
* Job role, department, location
* Lifecycle events (hire, role change, termination, rehire)

#### DocFlow HR → HRIS

* Document metadata (type, status, timestamps)
* Compliance status flags (complete / missing / expired)
* Secure document reference links
* Legal hold indicators (read-only flag in HRIS)

---

### 7.2 Sync Triggers

* New hire created
* Employee update
* Document submission or approval
* Termination event
* Legal hold applied or released

### 7.3 Conflict Resolution

* HRIS is source of truth for identity & status
* DocFlow HR is source of truth for documents & compliance
* Conflicts logged and surfaced to HR admins

---

## 8. Document Intelligence & Processing

### Auto-Classification

* I-9
* W-4
* Offer Letters
* IDs / Passports
* Benefits & Medical
* Performance & Disciplinary
* Custom employer categories

### Metadata Extraction

* Employee
* Employer
* Document type
* Issue date
* Expiration date
* Submission channel

---

## 9. State-Based Retention Defaults

### 9.1 Retention Engine

Retention policies are applied **automatically based on employee work location**, with employer-level overrides.

| State          | Default Retention        |
| -------------- | ------------------------ |
| Florida        | 5 years post-termination |
| Texas          | 4 years                  |
| Arizona        | 4 years                  |
| North Carolina | 3 years                  |
| Tennessee      | 3 years                  |

### Capabilities

* Per-document retention rules
* Automated deletion scheduling
* Secure deletion with audit records
* Retention suspension under legal hold

---

## 10. Legal Hold Workflows (NEW)

### 10.1 Legal Hold Initiation

* Triggered manually by Legal/Admin
* Triggered automatically via HRIS flag (optional)
* Scoped to:

  * Individual employee
  * Group (department, role)
  * Document category
  * Time range

### 10.2 Legal Hold Effects

* Retention countdown paused
* Deletion disabled
* Documents marked **“Under Legal Hold”**
* Read-only enforcement (no edits or removal)

### 10.3 Legal Hold Visibility

* Clearly labeled in HR dashboard
* Status synced to HRIS (metadata flag)
* Full audit trail of:

  * Who placed the hold
  * When
  * Scope
  * Reason (optional)

### 10.4 Legal Hold Release

* Authorized roles only
* Automatic resumption of retention timers
* Release event logged immutably

---

## 11. HR Admin Dashboard

### Core Features

* Employee document timelines
* Submission and approval statuses
* Bulk document requests
* Expiration alerts
* Retention & legal hold views
* Audit & export tools

### Admin Controls

* HRIS sync configuration
* Twilio SMS settings
* Intake channel enable/disable
* Retention overrides
* Legal hold permissions
* Role-based access control

---

## 12. Employee Experience

### Employee Portal

* Secure login (magic link or HRIS SSO)
* Submission history
* Status tracking
* Resubmission requests
* Mobile-first UX

### Trust & Transparency

* Timestamped receipts
* “Received by employer” confirmation
* Clear compliance status indicators

---

## 13. Security & Compliance

### Security

* Encryption in transit & at rest
* Signed upload URLs
* Malware scanning
* RBAC & least-privilege access

### Compliance

* Florida employment record compliance
* SOC 2-ready architecture
* Immutable audit logs
* HRIS-aligned access governance

---

## 14. Architecture Overview (High-Level)

**Core Components**

* Web App (HR + Employee)
* API Gateway
* Document Processing Service
* Object Storage (employer-isolated)
* Metadata Database
* Audit Log Store
* Notification Service (Twilio + Email)
* HRIS Integration Layer
* Retention & Legal Hold Engine

---

## 15. MVP Scope (Phase 1 – Final)

✅ Web upload
✅ Email intake
✅ Twilio SMS intake
✅ Cloud drive imports
✅ **Bi-directional HRIS sync (ADP, Gusto, Workday)**
✅ State-based retention defaults
✅ **Legal hold workflows**
✅ HR admin dashboard
✅ Employee portal
✅ Immutable audit logs

---

## 16. Phase 2 Roadmap

* Advanced AI document validation
* Auto-compliance scoring
* Additional HRIS systems
* E-signature workflows
* Mobile applications
* Staffing firm white-labeling
* Legal discovery export packages

---

## 17. Success Metrics (KPIs)

* Average document submission time
* % documents auto-classified
* HR hours saved per month
* Compliance issues reduced
* Legal hold response time
* Audit readiness score

---

## 18. Status Summary

✅ Bi-directional HRIS sync
✅ Legal hold workflows
✅ State-based retention defaults
✅ Twilio SMS integration

---
