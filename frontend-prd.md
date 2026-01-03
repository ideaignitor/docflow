# Frontend-Only PRD

## DocFlow HR — Employee Document Intake + HR Review UI (Next.js)

**Product:** DocFlow HR (Frontend)
**Scope:** **UI/UX only** — no backend requirements, no data model, no infra
**Framework:** **Next.js (App Router) + TypeScript + Tailwind + shadcn/ui**
**Rendering:** SSR where it helps (landing/auth), client components where needed (dashboards)
**Target Devices:** Mobile-first for employee intake; desktop-first for HR console
**Primary Markets:** Florida + expansion markets (handled in content/marketing copy only)

---

## 1) Goals

### Primary Goals

* Make it effortless for employees to submit employment documents using:

  * Upload
  * “Email” (UI flow only)
  * “SMS” (UI flow only)
  * Cloud drive import (Dropbox, Box, Google Drive, OneDrive) *(UI selection + connect states only)*
* Give HR a clean workflow to:

  * View document queue
  * Review document details
  * Approve / Reject with notes
  * See a submission timeline and audit-style activity feed (UI only)
* Provide a polished, investor-ready demoable experience in a single day.

### Non-Goals

* No backend APIs, no auth implementation, no storage logic
* No actual third-party OAuth implementation (Drive connect is UI state only)
* No real-time sync (use mocked data / local state)

---

## 2) Personas & Core UX Flows

### Personas

1. **Employee**

   * On mobile
   * Needs “send doc fast” with confirmation and status
2. **HR Admin / HR Manager**

   * On desktop
   * Needs review queue + fast decisions + clarity
3. **Legal / Auditor (Read-only)**

   * Needs timeline + activity feed view, export UI (disabled)

---

## 3) Information Architecture (IA)

### Public / Marketing

* `/` Home / value proposition
* `/pricing` (optional)
* `/security` (optional)
* `/demo` (optional “interactive preview”)

### Auth (UI only)

* `/sign-in` (magic link UI)
* `/verify` (success UI)
* `/select-org` (if multi-org)

### Employee Portal

* `/employee` (landing / start submission)
* `/employee/upload` (upload flow)
* `/employee/history` (submissions list)
* `/employee/submission/[id]` (receipt + status)

### HR Console

* `/hr` (dashboard)
* `/hr/review-queue` (queue list)
* `/hr/documents/[id]` (document review detail)
* `/hr/employees` (employee list)
* `/hr/employees/[id]` (employee timeline)
* `/hr/audit` (activity feed UI)

### Admin Settings (UI only)

* `/settings/intake` (enable channels)
* `/settings/integrations` (HRIS + Drive “connect” states)
* `/settings/retention` (state defaults UI)
* `/settings/legal-holds` (create/active holds UI)
* `/settings/access` (roles UI)

---

## 4) Design System Requirements

### Visual Style

* Clean enterprise SaaS: white/neutral backgrounds, subtle borders, strong typography
* Mobile-first layouts for employee pages
* Desktop tables + filters for HR

### Components (AIKit or shadcn equivalents)

* AppShell (top nav + side nav)
* Stepper (multi-step intake)
* FileDropzone (upload area with file list)
* StatusBadge (received / needs review / approved / rejected / expired / on hold)
* DocumentCard (preview + metadata)
* Timeline / ActivityFeed
* DataTable (sortable, filterable)
* Modal + Drawer (mobile-friendly)
* Toast notifications
* Empty states + skeleton loaders

### Accessibility

* Keyboard navigable
* Focus states visible
* Contrast AA
* Mobile tap targets ≥ 44px

---

## 5) Employee Experience (UI/UX)

### 5.1 Employee Start Screen (`/employee`)

**Primary CTA:** “Submit a Document”
Secondary options: Upload / Email / SMS / Import from Drive

**Content blocks**

* “What documents can I submit?”
* “What happens after I submit?”
* Trust: “Secure, encrypted, and visible to your employer only.”

---

### 5.2 Upload Flow (`/employee/upload`)

**Stepper (3 steps)**

1. Select document type (optional)
2. Add files (drag/drop + camera upload hint)
3. Review & submit

**Upload UI Requirements**

* Multi-file support
* File validation messages (type/size)
* Preview thumbnails for images; PDF icon for PDFs
* Optional fields:

  * Document type dropdown
  * Notes to HR text area

**Success State**

* Receipt screen with:

  * Submission ID
  * Timestamp
  * Status: “Received”
  * Next steps: “HR will review shortly”

---

### 5.3 Email Intake (UI-only)

**Screen:** `/employee?method=email`

* Show unique email address (mock)
* Copy-to-clipboard button
* Instructions: attach files, include employee email in body
* Confirmation: “Once received, you’ll see it in your history.”

---

### 5.4 SMS Intake (UI-only)

**Screen:** `/employee?method=sms`

* Show phone number (mock)
* “Verify your phone” UI:

  * enter phone number
  * OTP input component
* Instructions for MMS upload
* “You’ll receive a text confirmation” (UI only)

---

### 5.5 Cloud Drive Import (UI-only)

**Screen:** `/employee?method=drive`

* Provider selection tiles:

  * Dropbox / Box / Google Drive / OneDrive
* Provider connect states:

  * Disconnected → “Connect”
  * Connecting → loader
  * Connected → show account label (mock) + “Choose files”
* File picker UI (mock):

  * Search
  * Folder breadcrumb
  * Multi-select checkboxes
  * Import button

---

### 5.6 Submission History (`/employee/history`)

* List of submissions (cards on mobile)
* Filters:

  * Status
  * Date range
* Clicking opens `/employee/submission/[id]`

---

### 5.7 Submission Detail (`/employee/submission/[id]`)

* Status header + progress indicator:

  * Received → In review → Approved/Rejected
* Files list with previews
* Activity timeline (submission + updates)
* If rejected: show HR notes + “Resubmit” CTA

---

## 6) HR Console Experience (UI/UX)

### 6.1 HR Dashboard (`/hr`)

Widgets (mock data):

* “Documents needing review”
* “Expiring soon”
* “Missing required documents” (optional)
* “Legal holds active” (optional)

---

### 6.2 Review Queue (`/hr/review-queue`)

**DataTable UI**
Columns:

* Employee
* Document type
* Received timestamp
* Source (upload/email/sms/drive)
* Status badge
* Priority (optional)

Filters:

* Status
* Type
* Date
* Employee search

Bulk actions (disabled or mock):

* Approve selected
* Request resubmission

---

### 6.3 Document Review Detail (`/hr/documents/[id]`)

Layout:

* Left: Document preview panel (PDF viewer / image preview)
* Right: Metadata + actions

Metadata module:

* Employee summary card (name, status, state)
* Document type selector (override)
* Issue/expiration dates (editable UI)
* Source channel
* Version selector (if multiple)

Actions:

* Approve (primary)
* Reject (secondary) → requires notes
* Request resubmission (optional)

Post-action confirmation:

* Toast + status badge update
* Activity feed appended (UI only)

---

### 6.4 Employee Profile (`/hr/employees/[id]`)

Tabs:

* Overview
* Documents
* Activity timeline

Documents tab:

* Categorized sections
* Status badges
* Search within employee

Activity timeline:

* Submission received
* Review completed
* Notes added
* (Hold applied/released)

---

### 6.5 Audit Feed (`/hr/audit`)

**ActivityFeed UI**
Filters:

* Event type
* Actor
* Date
* Employee

Export UI:

* Button exists but shows “Coming soon” modal

---

## 7) Legal Hold UI (Frontend-only)

### 7.1 Legal Holds List (`/settings/legal-holds`)

* Table of holds: title, status, created by, date
* “Create legal hold” CTA

### 7.2 Create Legal Hold (`/settings/legal-holds/new`)

Form fields:

* Title (required)
* Reason (optional)
* Scope selector:

  * Employee picker
  * Department dropdown
  * Document category dropdown
  * Date range
* Submit creates a mock hold and updates UI

### 7.3 Hold Indicator UI

* Show “On Legal Hold” badge on affected documents (mock logic)
* Disable “Delete” actions everywhere (if present)

---

## 8) Retention Policy UI (Frontend-only)

### `/settings/retention`

* State selector: FL, TX, AZ, NC, TN
* Default retention display per state (read-only by default)
* “Override policy” toggle (mock)
* Per-document type override UI (accordion)

---

## 9) Integrations UI (Frontend-only)

### `/settings/integrations`

Sections:

* HRIS: ADP / Gusto / Workday

  * Connect button (mock)
  * Status: disconnected/connected/error
  * “Last sync” label (mock)
* Drives: Dropbox / Box / Google Drive / OneDrive

  * Connect + permissions copy (UI only)

---

## 10) States, Empty States, and Loading

### Required UI States

* Empty queue
* No submissions
* Upload error (file too big/unsupported)
* “Disconnected integration”
* Skeleton loaders for tables
* Offline banner (optional)

---

## 11) Frontend Technical Requirements (Next.js)

### Stack

* Next.js App Router
* TypeScript
* Tailwind
* shadcn/ui components
* react-hook-form + zod for form validation
* Zustand or React Context for mocked state
* MSW (Mock Service Worker) optional for API mocking

### Patterns

* Server Components for marketing pages (SEO)
* Client Components for dashboard interactivity
* Route groups:

  * `(marketing)`
  * `(auth)`
  * `(employee)`
  * `(hr)`
  * `(settings)`

### Testing (Frontend-only)

* Unit: Jest + React Testing Library
* E2E: Playwright (happy-path demo flows)

---

## 12) MVP UI Deliverables (Build Today)

**Employee**

* Start page
* Upload flow + receipt
* History list
* Submission detail

**HR**

* Review queue table
* Document review detail w/ approve/reject modals
* Employee profile + timeline (basic)

**Settings**

* Intake toggles (UI)
* Integrations status (UI)
* Legal holds create/list (UI)
* Retention defaults page (UI)

---

## 13) Success Criteria (Frontend)

* Employee can complete upload in < 30 seconds on mobile
* HR can approve/reject in < 15 seconds per doc
* Demo script runs end-to-end without dead ends
* UI communicates trust (receipts, timestamps, status)

---

## 14) Demo Script (Frontend-only)

1. Employee uploads a document → sees receipt
2. HR sees it in review queue → opens detail
3. HR rejects with notes → employee sees rejected status
4. Employee resubmits → HR approves
5. Admin creates legal hold → document shows “On hold”
6. Retention page shows state defaults for Florida

---

