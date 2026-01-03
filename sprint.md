# 🚀 One-Day Agile Sprint Plan

## DocFlow HR — Core MVP Build

**Sprint Type:** Ultra-Compressed Delivery Sprint (8–10 hours)
**Sprint Goal:**

> Enable end-to-end employee document intake → storage → HR review → audit trail, with foundations for HRIS, retention, and legal hold.

**Definition of “Done Today”**

* Employees can submit documents
* HR can see, review, and approve them
* Documents are stored immutably
* Audit events exist
* Retention + legal hold scaffolding exists (not full automation)

---

## 🧠 Team Assumptions

| Role              | Responsibility                    |
| ----------------- | --------------------------------- |
| Lead Engineer     | Architecture, APIs, ZeroDB schema |
| Frontend Engineer | Minimal HR + employee UI          |
| AI Pair (LLM)     | Code generation, tests, fixtures  |
| Optional          | QA mindset baked into TDD         |

---

## ⏱️ Sprint Timeline Overview

| Time      | Focus                              |
| --------- | ---------------------------------- |
| Hour 0–1  | Architecture + schema + scope lock |
| Hour 1–3  | Core data model + ingestion APIs   |
| Hour 3–5  | Document lifecycle + storage       |
| Hour 5–6  | HR review workflow                 |
| Hour 6–7  | Audit + events                     |
| Hour 7–8  | Retention + legal hold scaffolding |
| Hour 8–9  | UI wiring + happy-path demo        |
| Hour 9–10 | Hardening + demo prep              |

---

# 🏗️ Sprint Breakdown by Phase

---

## PHASE 0 — Scope Lock (30 minutes)

**Rules**

* NO HRIS sync execution (metadata only)
* NO AI classification (manual category)
* NO deletion jobs (schedule only)

**Deliverables**

* Final list of APIs
* Final ZeroDB tables to create today

---

## PHASE 1 — Core Foundation (Hour 0–1)

### Deliverables

* ZeroDB schema created
* Auth + org context working

### Stories

* Create `orgs`, `users`, `roles`, `employees`
* Seed default roles
* Org-scoped middleware

### End State

✅ You can create an org
✅ You can create an employee
✅ Every request is tenant-scoped

---

## PHASE 2 — Intake & Submission (Hour 1–3)

### Goal

Employees can submit documents and receive confirmation.

### Stories (from backlog)

* Enable web upload
* Create submission record
* Save raw file to ZeroDB object storage
* Emit `document.received` event

### APIs to Ship

```http
POST /api/uploads
POST /api/submissions
```

### End State

✅ Upload → submission → stored file
✅ Immutable timestamped receipt exists

---

## PHASE 3 — Document Model & Versioning (Hour 3–5)

### Goal

Documents are immutable, versioned, and reviewable.

### Stories

* Create document shell
* Create document version
* Link submission → document
* Set current version

### APIs

```http
POST /api/documents
POST /api/documents/{id}/versions
```

### End State

✅ Each upload creates a document + version
✅ History preserved
✅ Ready for compliance

---

## PHASE 4 — HR Review Workflow (Hour 5–6)

### Goal

HR can approve or reject documents.

### Stories

* Add document to review queue
* Approve document
* Reject document with notes

### APIs

```http
GET  /api/review-queue
POST /api/documents/{id}/approve
POST /api/documents/{id}/reject
```

### End State

✅ HR sees pending docs
✅ HR approves/rejects
✅ Employee notified

---

## PHASE 5 — Audit & Events (Hour 6–7)

### Goal

Everything is audit-ready.

### Stories

* Emit events on mutations
* Store immutable audit records

### Events to Emit Today

* `document.received`
* `document.version.created`
* `document.review.approved`
* `document.review.rejected`

### End State

✅ Full timeline reconstructable
✅ Compliance story exists

---

## PHASE 6 — Retention & Legal Hold Scaffolding (Hour 7–8)

### Goal

Prove compliance readiness without full automation.

### Stories

* Apply state-based retention policy
* Create legal hold
* Block deletion if hold exists

### APIs

```http
POST /api/retention/schedule
POST /api/legal-holds
```

### End State

✅ Retention dates computed
✅ Legal hold prevents deletion
✅ Ready for enterprise conversations

---

## PHASE 7 — Minimal UI (Hour 8–9)

### Employee UI

* Upload document
* See “Received” confirmation

### HR UI

* Review queue
* Approve / reject buttons
* Audit timeline view (basic)

### End State

✅ End-to-end demoable
✅ Non-technical stakeholder can understand

---

## PHASE 8 — Hardening & Demo Prep (Hour 9–10)

### Checklist

* Seed sample org + employee
* Seed fake documents
* Run happy-path demo
* Confirm audit trail visibility

### Demo Script

1. Employee uploads document
2. Submission receipt appears
3. HR reviews and approves
4. Audit log shows full chain
5. Retention + legal hold visible

---

# 📦 What You Will Have at End of Day

✅ Multi-tenant HR SaaS foundation
✅ Secure document intake
✅ Immutable document storage
✅ HR approval workflow
✅ Audit-ready event system
✅ Retention + legal hold primitives
✅ Investor-grade demo

---

# 🚫 Explicitly Deferred (Smartly)

* HRIS push/pull execution
* AI document classification
* Background deletion workers
* Mobile app
* Advanced permissions UI

(These become Sprint 2.)

---

