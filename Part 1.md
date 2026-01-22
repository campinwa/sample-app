# COMPREHENSIVE SYSTEM MODELING DOCUMENT
## Reinsurance Management System - BRINS & TUGURE

**Document Version:** 2.0  
**Date:** January 22, 2026  
**Updated:** Based on new business requirements

---

## TABLE OF CONTENTS

1. [Master Data Analysis](#1-master-data-analysis)
2. [Information Modelling](#2-information-modelling)
3. [Data Modelling](#3-data-modelling)
4. [Process Modelling](#4-process-modelling)
5. [Interaction Modelling](#5-interaction-modelling)

---

## 1. MASTER DATA ANALYSIS

### 1.1 Definition of Master Data

Master data adalah data referensi yang:
- Relatif statis dan jarang berubah
- Digunakan oleh banyak proses transaksional
- Memerlukan data governance yang ketat
- Menjadi acuan untuk validasi dan business rules

### 1.2 Master Data Entities

Dari 20 entitas dalam database, terdapat **6 Master Data Entities**:

#### **1.2.1 MasterContract** ⭐ PRIMARY MASTER DATA

**Classification:** Master Data - Core Business Reference

**Purpose:** Template kontrak reasuransi yang mengatur terms & conditions

**Characteristics:**
- Validity: 1 year
- Change Frequency: Annual + ad-hoc addendum
- Versioning: Yes (parent-child relationship)
- Approval: Two-level (BRINS + TUGURE)
- Impact: High (affects all transactions)

**Master Data Attributes:**
- Policy structure and terms
- Coverage rules (allowed_kolektabilitas, allowed_region)
- Rate configuration (premium_rate, ric_rate, bf_rate)
- Limits (max_plafond, max_tenor_month)
- Share percentages (share_tugure_percentage)

**Lifecycle:**
1. Draft → Pending BRINS Acknowledgement
2. → Pending TUGURE Acknowledgement
3. → Active (effective for 1 year)
4. → Inactive/Archived (after expiry)

**Dependencies:** 
- Referenced by: Contract, Batch, Debtor, Claim

---

#### **1.2.2 Contract** ⭐ OPERATIONAL MASTER DATA

**Classification:** Master Data - Operational Reference

**Purpose:** Active contract instance untuk periode tertentu

**Characteristics:**
- Validity: Specified period (start_date to end_date)
- Change Frequency: Low (only status changes)
- Derived from: MasterContract
- Approval: Inherited from MasterContract
- Impact: High (affects monthly operations)

**Master Data Attributes:**
- Contract identification (contract_number, contract_name)
- Parties (cedant, reinsurer)
- Terms (coverage_percentage, premium_rate)
- Validity period (start_date, end_date)
- Status (ACTIVE, EXPIRED, TERMINATED)

**Lifecycle:**
1. Created from MasterContract
2. ACTIVE (during validity)
3. EXPIRED (auto after end_date)
4. TERMINATED (manual closure)

**Dependencies:**
- Referenced by: Batch, Nota, Payment, Bordero, Claim, Reconciliation

---

#### **1.2.3 SystemConfig** 🔧 SYSTEM MASTER DATA

**Classification:** Master Data - System Configuration

**Purpose:** Konfigurasi parameter sistem

**Characteristics:**
- Validity: Per effective_date
- Change Frequency: Low to Medium
- Versioning: Yes
- Approval: Required for critical configs
- Impact: Medium to High

**Configuration Types:**
1. **STATUS_REFERENCE** - Enum values dan status flows
2. **ELIGIBILITY_RULE** - Business validation rules
3. **FINANCIAL_THRESHOLD** - Limit amounts
4. **APPROVAL_MATRIX** - Approval workflows
5. **NOTIFICATION_RULE** - Notification triggers
6. **NOTIFICATION_CHANNEL** - Communication settings

**Example Configurations:**
```json
{
  "config_type": "FINANCIAL_THRESHOLD",
  "config_key": "MIN_PREMIUM_AMOUNT",
  "config_value": "100000",
  "description": "Minimum premium amount in IDR"
}
```

**Dependencies:**
- Used by: All transactional processes for validation

---

#### **1.2.4 SlaRule** ⏱️ OPERATIONAL MASTER DATA

**Classification:** Master Data - Monitoring Configuration

**Purpose:** Define SLA rules untuk monitoring dan alerting

**Characteristics:**
- Validity: Ongoing until deactivated
- Change Frequency: Medium
- Versioning: No (update in place)
- Approval: Admin only
- Impact: Medium (affects notifications)

**Master Data Attributes:**
- Rule definition (entity_type, trigger_condition)
- Thresholds (duration_value, duration_unit)
- Notification settings (recipient_role, priority)
- Recurrence configuration

**Example Rules:**
- "Batch stuck in 'Uploaded' status for >24 hours → Alert BRINS"
- "Nota unpaid 3 days before due → Alert BRINS Finance"
- "Claim pending review >48 hours → Alert TUGURE"

**Dependencies:**
- Triggers: Notification creation

---

#### **1.2.5 EmailTemplate** 📧 CONTENT MASTER DATA

**Classification:** Master Data - Communication Template

**Purpose:** Template email untuk berbagai status transitions

**Characteristics:**
- Validity: Ongoing until deactivated
- Change Frequency: Low
- Versioning: No
- Approval: Admin only
- Impact: Low (cosmetic)

**Master Data Attributes:**
- Template per object and status transition
- Variable placeholders: {batch_id}, {user_name}, {date}, {amount}
- Multi-language support (future)

**Example Template:**
```
Object: Batch
Status From: Validated
Status To: Approved
Subject: "Batch {batch_id} Approved - Action Required"
Body: "Dear {user_name}, Batch {batch_id} for period {period} 
       has been approved. Total premium: {final_premium_amount}..."
```

**Dependencies:**
- Used by: Notification system

---

#### **1.2.6 NotificationSetting** 👤 USER MASTER DATA

**Classification:** Master Data - User Preferences

**Purpose:** User-specific notification preferences

**Characteristics:**
- Validity: Per user, ongoing
- Change Frequency: Low
- Versioning: No
- Approval: Self-service by user
- Impact: Low (user experience)

**Master Data Attributes:**
- Contact information (notification_email, whatsapp_number)
- Channel preferences (email_enabled, whatsapp_enabled)
- Event subscriptions (notify_batch_status, notify_claim_status, etc.)

**Dependencies:**
- Controls: Notification delivery

---

### 1.3 Master Data vs Transactional Data

| Entity | Type | Rationale |
|--------|------|-----------|
| **MasterContract** | Master Data | Reference data, infrequent changes, high impact |
| **Contract** | Master Data | Operational reference, derived from MasterContract |
| **SystemConfig** | Master Data | System parameters, governance required |
| **SlaRule** | Master Data | Monitoring configuration, business rules |
| **EmailTemplate** | Master Data | Content template, centralized management |
| **NotificationSetting** | Master Data | User preferences, relatively static |
| **Batch** | Transactional | Monthly operation, high volume |
| **Debtor** | Transactional | Coverage records, high volume |
| **Record** | Transactional | Review tracking, operational |
| **Nota** | Transactional | Billing documents, monthly |
| **Payment** | Transactional | Financial transactions |
| **PaymentIntent** | Transactional | Payment planning |
| **Reconciliation** | Transactional | Payment matching |
| **DebitCreditNote** | Transactional | Adjustments, ad-hoc |
| **Bordero** | Transactional | Statement generation |
| **Invoice** | Transactional | Billing, monthly |
| **Claim** | Transactional | Insurance claims, ad-hoc |
| **Subrogation** | Transactional | Recovery tracking |
| **Notification** | Operational | System alerts, high volume |
| **AuditLog** | Operational | Audit trail, very high volume |

### 1.4 Master Data Management Requirements

#### 1.4.1 Data Governance

**MasterContract:**
- ✅ Two-level approval (BRINS acknowledgement → TUGURE acknowledgement)
- ✅ Version control via parent_contract_id
- ✅ Immutable after activation
- ✅ Addendum creates new version with parent reference
- ✅ Audit trail for all changes

**Contract:**
- ✅ Auto-created from approved MasterContract
- ✅ Status transitions logged
- ✅ Cannot be deleted if has related Batches
- ✅ One ACTIVE contract per credit_type at a time

**SystemConfig:**
- ✅ Approval workflow for critical configs
- ✅ Version tracking
- ✅ Effective date management
- ✅ Rollback capability via version history

#### 1.4.2 Data Quality Rules

**MasterContract:**
- coverage_end_date must be >= coverage_start_date
- Rates and percentages must be >= 0
- allowed_kolektabilitas must be comma-separated valid values (1-5)
- allowed_region must be valid region codes
- version must increment on addendum

**Contract:**
- end_date must be > start_date
- Only one ACTIVE status per credit_type
- Must reference valid MasterContract

**SystemConfig:**
- config_value must be valid JSON or primitive type
- effective_date must not be in the past for new configs
- version must increment on changes

#### 1.4.3 Master Data Synchronization

**Cross-System Dependencies:**
```
MasterContract (Source of Truth)
    ↓
Contract (Operational Copy)
    ↓
Batch Validation Rules
    ↓
Debtor Validation (kolektabilitas, region)
    ↓
Claim Validation (against contract terms)
```

**Update Propagation:**
- MasterContract addendum → Create new Contract version
- Contract rate change → Does NOT affect existing Batches (historical accuracy)
- SystemConfig update → Applies to new transactions immediately

---

### 1.5 Summary: Master Data Count

**Total Master Data Entities: 6**

1. **MasterContract** - Primary business master
2. **Contract** - Operational master
3. **SystemConfig** - System configuration master
4. **SlaRule** - Monitoring master
5. **EmailTemplate** - Communication master
6. **NotificationSetting** - User preference master

**Transactional Entities: 12**
**Operational Entities: 2** (Notification, AuditLog)

---

## 2. INFORMATION MODELLING

### 2.1 Information Architecture Overview

Information Model menggambarkan bagaimana informasi mengalir dalam sistem, siapa yang memiliki, siapa yang menggunakan, dan bagaimana informasi tersebut berinteraksi.

### 2.2 Actors & Systems

#### 2.2.1 Primary Actors

**BRINS (Cedant)**
- Role: Submitter, Payer, Claimant
- Responsibilities:
  - Create and submit Master Contract
  - Submit batch debtors (via BSM data)
  - Pay premiums
  - Submit claims and subrogation
  - Verify DN/CN
- Access Level: Full access to own data

**TUGURE (Reinsurer)**
- Role: Reviewer, Approver, Payer
- Responsibilities:
  - Review and approve Master Contract
  - Review and approve batch debtors
  - Verify premium payments
  - Process claims and subrogation
  - Generate DN/CN for payment variances
- Access Level: Full access to all data

**BSM (Broker)**
- Role: Data Provider
- Responsibilities:
  - Collect debtor data from field
  - Send batch data to BRINS
- Access Level: Read-only for their batches

**Finance BRINS**
- Role: Financial Controller
- Responsibilities:
  - Confirm nota receipt
  - Process payments
  - Reconcile accounts
- Access Level: Financial data + related documents

**Finance TUGURE**
- Role: Financial Controller
- Responsibilities:
  - Verify payments received
  - Generate invoices
  - Process claim payments
  - Reconciliation
- Access Level: Financial data + related documents

**System Administrator**
- Role: System Manager
- Responsibilities:
  - Configure system parameters
  - Manage SLA rules
  - Monitor system health
- Access Level: Full system access

#### 2.2.2 External Systems

**Bank System**
- Integration: Payment notification via API/file
- Data Provided: Payment reference, amount, date
- Frequency: Real-time or daily

**Email Service (SMTP)**
- Integration: Email notifications
- Trigger: Status changes, SLA breaches
- Frequency: Event-driven

**WhatsApp Gateway (Future)**
- Integration: Instant notifications
- Trigger: Critical alerts
- Frequency: Event-driven

### 2.3 Information Entities & Ownership

| Information Entity | Owner | Creators | Consumers | Update Frequency |
|-------------------|-------|----------|-----------|------------------|
| MasterContract | BRINS & TUGURE | BRINS | BRINS, TUGURE, System | Annual + Addendum |
| Contract | TUGURE | System | BRINS, TUGURE, System | Per MasterContract |
| Batch | BRINS | BRINS (via BSM) | BRINS, TUGURE | Monthly (3 batches) |
| Debtor | BRINS | BRINS (via BSM) | BRINS, TUGURE, System | Monthly (within batch) |
| Nota Premium | TUGURE | System | BRINS, TUGURE, Finance | Monthly |
| Payment | BRINS | Bank → System | BRINS, TUGURE, Finance | Ad-hoc |
| Claim | BRINS | BRINS | BRINS, TUGURE, Finance | Ad-hoc |
| Nota Claim | TUGURE | System | BRINS, TUGURE, Finance | Per approved claim |
| Subrogation | BRINS | BRINS | BRINS, TUGURE, Finance | Ad-hoc |
| DN/CN | TUGURE | TUGURE | BRINS, TUGURE, Finance | Per variance |
| Reconciliation | TUGURE | System | Finance BRINS, Finance TUGURE | Monthly |

### 2.4 Information Flow Diagrams

#### 2.4.1 Master Contract Information Flow

```
┌──────────┐
│  BRINS   │ (1) Create & Submit MasterContract
└─────┬────┘
      │ contract_id, policy_no, terms, rates
      ↓
┌─────────────────┐
│    System       │ (2) Validate & Store (status: Pending BRINS)
│  MasterContract │
└────────┬────────┘
         │
         ↓
┌──────────────┐
│   TUGURE     │ (3) Review MasterContract
└──────┬───────┘
       │ Approve/Reject
       ↓
┌─────────────────┐
│    System       │ (4a) If Approved: Set status = Active
│  MasterContract │     Generate Contract instance
└────────┬────────┘ (4b) If Rejected: Set status = Rejected
         │             Notify BRINS for revision
         ↓
┌──────────────┐
│  Contract    │ (5) Active contract ready for operations
└──────────────┘
```

#### 2.4.2 Premium Nota Information Flow (3-Batch Collection)

```
┌─────┐
│ BSM │ (1) Send debtor data
└──┬──┘
   │ batch 1 data
   ↓
┌──────────┐
│  BRINS   │ (2) Review & Validate
└─────┬────┘
      │ batch 1 approved
      ↓
┌──────────────┐
│   System     │ (3) Store Batch 1 (status: Validated)
│   Batch 1    │
└──────────────┘
      │ Wait for Batch 2 & 3...
      ↓
[Repeat for Batch 2]
      ↓
[Repeat for Batch 3]
      ↓
┌──────────────────────────┐
│  System                  │ (4) After 3 batches collected
│  Batch 1, 2, 3 Complete  │     (End of Month)
└───────────┬──────────────┘
            │
            ↓
┌──────────────────────────┐
│  System                  │ (5) Generate Nota Premium
│  Nota (type: Batch)      │     amount = SUM(3 batches final_premium_amount)
│  reference: Batch1,2,3   │     Check for claims in previous month
└───────────┬──────────────┘
            │ Nota ID, Amount (after claim offset)
            ↓
┌──────────────┐     ┌─────────────────┐
│ Finance      │     │     TUGURE      │
│ BRINS        │     │                 │
└──────────────┘     └─────────────────┘
      │                      │
      └──────────┬───────────┘
                 │ (6) Receive Nota
                 ↓
         [Proceed to Payment Flow]
```

**Key Information:**
- Batch collection period: 1 month
- Collection requirement: Exactly 3 batches
- Nota generation: End of month (after 3 batches validated)
- Nota amount calculation: 
  ```
  Final Amount = SUM(Batch1.final_premium_amount + 
                     Batch2.final_premium_amount + 
                     Batch3.final_premium_amount)
                 - Previous Month Approved Claims (if any)
  ```

#### 2.4.3 Claim Offset Mechanism

```
Month N-1 (Previous Month)
┌──────────────┐
│ Claims       │ (1) Claims approved in previous month
│ Status:      │     claim_month = N-1
│ Approved     │
└──────┬───────┘
       │ SUM(share_tugure_amount) = X
       ↓
       
Month N (Current Month)
┌──────────────────────────┐
│ Generate Nota Premium    │ (2) Calculate premium for current month
│ Month: N                 │
└───────────┬──────────────┘
            │
            ↓
┌────────────────────────────────────┐
│ Nota Amount Calculation            │
│                                    │
│ Gross Premium = SUM(3 Batches)     │
│ Previous Claims = X                │
│                                    │
│ Net Premium = Gross - Claims       │ (3) Offset mechanism
│                                    │
│ If Net < 0:                        │
│   Nota Amount = 0                  │
│   Carry Forward = |Net|            │
│ Else:                              │
│   Nota Amount = Net                │
└────────────┬───────────────────────┘
             │
             ↓
┌──────────────────────────┐
│ Nota (type: Batch)       │ (4) Final nota with offset
│ amount = Net Premium     │
│ remarks = "Offset claims │
│            from month N-1"│
└──────────────────────────┘
```

#### 2.4.4 Payment & Reconciliation Information Flow

```
┌──────────────┐
│ Nota Issued  │ (1) Nota Final
│ Amount: A    │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ BRINS        │ (2) Create Payment Intent (optional)
│ Finance      │
└──────┬───────┘
       │ planned_amount, planned_date
       ↓
┌──────────────────┐
│ PaymentIntent    │ (3) Store payment plan
└──────────────────┘
       │
       ↓
┌──────────────┐
│ Bank         │ (4) Execute payment
│ Transfer     │
└──────┬───────┘
       │ payment_ref, amount: B, date
       ↓
┌──────────────────┐
│ System           │ (5) Receive payment notification
│ Payment Record   │     match_status = RECEIVED
└──────┬───────────┘
       │
       ↓
┌──────────────────────────┐
│ System Reconciliation    │ (6) Match payment to nota
│                          │
│ Compare: A vs B          │
│                          │
│ If A = B:                │
│   match_status = MATCHED │
│   reconciliation = OK    │
│                          │
│ If A ≠ B:                │
│   match_status =         │
│     PARTIALLY_MATCHED    │
│   exception_type =       │
│     OVER/UNDER/PARTIAL   │
└──────────┬───────────────┘
           │
           ├─→ (7a) If Matched: Update Nota (status: Paid)
           │
           └─→ (7b) If Exception:
                    ↓
           ┌────────────────────┐
           │ Notification       │ (8) Alert BRINS Finance
           │ Type: EXCEPTION    │
           └─────────┬──────────┘
                     │
                     ↓
           ┌────────────────────┐
           │ BRINS Confirms     │ (9) Acknowledge exception
           └─────────┬──────────┘
                     │
                     ↓
           ┌────────────────────┐
           │ TUGURE generates   │ (10) Create adjustment
           │ DN/CN              │
           │                    │
           │ If B > A: CN       │
           │ If B < A: DN       │
           └─────────┬──────────┘
                     │
                     ↓
           ┌────────────────────┐
           │ BRINS verifies     │ (11) Verify DN/CN
           │ DN/CN              │
           └─────────┬──────────┘
                     │
                     ↓
           ┌────────────────────┐
           │ Update Nota        │ (12) Adjust nota amount
           │ New Amount =       │      Update reconciliation
           │   A + DN - CN      │
           └────────────────────┘
```

#### 2.4.5 Claim Information Flow

```
┌──────────────┐
│ BRINS        │ (1) Submit Claim
└──────┬───────┘     based on Debtor (via nomor_polis)
       │ claim_no, nomor_polis, nilai_klaim, dol
       ↓
┌──────────────────────────────┐
│ System Validation            │ (2) Validate claim
│                              │
│ Check:                       │
│ - Debtor exists (nomor_polis)│
│ - Coverage active on DOL     │
│ - Claim amount <= max_coverage│
│ - Within contract terms      │
└──────────┬───────────────────┘
           │
           ├─→ (3a) If Invalid: Reject with reason
           │
           └─→ (3b) If Valid: Store (status: Draft)
                    ↓
           ┌────────────────────┐
           │ TUGURE Review      │ (4) Review claim documents
           └─────────┬──────────┘
                     │
                     ├─→ (5a) Approve: status = Doc Verified
                     │         Calculate share_tugure_amount
                     │
                     └─→ (5b) Reject: Request revision
                              ↓
                     ┌────────────────────┐
                     │ Generate Nota      │ (6) Create claim nota
                     │ Type: Claim        │
                     │ Amount = share_    │
                     │   tugure_amount    │
                     └─────────┬──────────┘
                               │
                               ↓
                     ┌────────────────────┐
                     │ TUGURE pays        │ (7) Execute payment
                     │ claim amount       │
                     └─────────┬──────────┘
                               │
                               ↓
                     [Payment Reconciliation Flow]
                               │
                               ↓
                     ┌────────────────────┐
                     │ Update Claim       │ (8) Mark as paid
                     │ status = Paid      │
                     └────────────────────┘
```

**Claim to Debtor Reference:**
- Primary key: nomor_polis (not debtor_id/cover_id)
- Validation: System looks up Debtor.nomor_polis = Claim.nomor_polis
- This allows claims even if cover_id changes due to revision

#### 2.4.6 Subrogation Information Flow

```
┌──────────────┐
│ Claim        │ (1) Approved & Paid Claim exists
│ Status: Paid │
└──────┬───────┘
       │ claim_id, nomor_polis
       ↓
┌──────────────┐
│ BRINS        │ (2) Submit Subrogation
└──────┬───────┘     Recovery from debtor
       │ subrogation_id, claim_id, recovery_amount
       ↓
┌──────────────────────────────┐
│ System Validation            │ (3) Validate subrogation
│                              │
│ Check:                       │
│ - Claim exists & paid        │
│ - Recovery <= claim amount   │
│ - Not duplicate subrogation  │
└──────────┬───────────────────┘
           │
           ├─→ (4a) If Invalid: Reject
           │
           └─→ (4b) If Valid: Store (status: Draft)
                    ↓
           ┌────────────────────┐
           │ TUGURE Review      │ (5) Review recovery docs
           └─────────┬──────────┘
                     │
                     ├─→ (6a) Approve: status = Invoiced
                     │
                     └─→ (6b) Reject: Request revision
                              ↓
                     ┌────────────────────┐
                     │ Generate Nota      │ (7) Create subrogation nota
                     │ Type: Subrogation  │
                     │ Amount = recovery_ │
                     │   amount * share_% │
                     └─────────┬──────────┘
                               │
                               ↓
                     ┌────────────────────┐
                     │ BRINS pays         │ (8) BRINS pays back recovery
                     │ subrogation        │     (money flows back)
                     └─────────┬──────────┘
                               │
                               ↓
                     [Payment Reconciliation Flow]
                               │
                               ↓
                     ┌────────────────────┐
                     │ Update Subrogation │ (9) Mark as closed
                     │ status = Paid/Closed│
                     └────────────────────┘
```

**Subrogation Characteristics:**
- Always references a Claim (claim_id is required)
- Money flows from BRINS to TUGURE (recovery payback)
- Reduces TUGURE's net loss on the claim

### 2.5 Information Lifecycle States

#### 2.5.1 MasterContract Lifecycle

```
[Draft] → (BRINS Submit) → [Pending BRINS Acknowledgement]
                                ↓
                          (BRINS Acknowledge)
                                ↓
                    [Pending TUGURE Acknowledgement]
                                ↓
                          (TUGURE Approve)
                                ↓
                            [Active] → (After 1 year or terminated) → [Inactive]
                                                                            ↓
                                                                       [Archived]
                                ↓
                          (TUGURE Reject)
                                ↓
                           [Rejected] → (BRINS Revise) → [Draft] (new version)
                           
Addendum Flow:
[Active Parent] → (Request Addendum) → [Draft Child]
                                           ↓
                                    (Approval flow...)
                                           ↓
                                    [Active Child]
                                           ↑
                                parent_contract_id = Parent.contract_id
```

#### 2.5.2 Batch Lifecycle (Updated)

```
[Created by BSM] → (BRINS Receive) → [Uploaded]
                                         ↓
                                   (System Validate)
                                         ↓
                                     [Validated] → (Collect 3 batches)
                                         ↓
                              (All 3 batches validated)
                                         ↓
                                     [Matched]
                                         ↓
                                  (BRINS Approve)
                                         ↓
                                     [Approved] → (End of Month: Generate Nota)
                                         ↓
                                   [Nota Issued]
                                         ↓
                             (Finance BRINS Confirm Receipt)
                                         ↓
                              [Branch Confirmed]
                                         ↓
                                  (Payment Made)
                                         ↓
                                      [Paid]
                                         ↓
                              (Reconciliation Complete)
                                         ↓
                                     [Closed]

Rejection Flow:
Any state → (Reject) → [Rejected]
[Rejected] → (BRINS Revise) → [Uploaded] (new version)

Reopen Flow:
[Closed] → (Request Reopen) → [Reopen Requested]
                                      ↓
                              (Supervisor Approve)
                                      ↓
                                  [Reopened] → (Make Changes)
                                      ↓
                                  [Validated] (continue normal flow)
```

#### 2.5.3 Nota Lifecycle

```
[Auto-Generated by System] → [Draft]
                                ↓
                          (Finalize)
                                ↓
                            [Issued] (immutable amount)
                                ↓
                     (Finance BRINS Confirm)
                                ↓
                           [Confirmed]
                                ↓
                      (Payment Received)
                                ↓
                    ┌───────────┴───────────┐
                    ↓                       ↓
            (Amount Matched)          (Amount Variance)
                    ↓                       ↓
                 [Paid]               [Confirmed]
                                           ↓
                                   (DN/CN Generated)
                                           ↓
                                   (DN/CN Approved)
                                           ↓
                              (Amount Adjusted)
                                           ↓
                                       [Paid]
```

### 2.6 Information Security & Access Control

#### 2.6.1 Data Classification

| Data Type | Classification | Access Level | Encryption |
|-----------|---------------|--------------|------------|
| MasterContract | Confidential | BRINS, TUGURE, Admin | At Rest + Transit |
| Debtor Personal Data | Highly Confidential | BRINS, TUGURE (read-only) | At Rest + Transit + Field Level |
| Financial Amounts | Confidential | Finance Teams, Admin | At Rest + Transit |
| Payment Details | Highly Confidential | Finance Teams, Admin | At Rest + Transit |
| Claim Details | Confidential | BRINS, TUGURE, Finance | At Rest + Transit |
| Audit Logs | Confidential | Admin only | At Rest |
| System Config | Internal | Admin only | At Rest |

#### 2.6.2 Role-Based Access Matrix

| Function | BRINS User | BRINS Finance | TUGURE User | TUGURE Finance | BSM | Admin |
|----------|------------|---------------|-------------|----------------|-----|-------|
| Create MasterContract | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Acknowledge MasterContract (BRINS) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Acknowledge MasterContract (TUGURE) | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Submit Batch | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Review Batch | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Approve Batch | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| View Nota | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Confirm Nota (BRINS) | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Issue Nota | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Process Payment | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Verify Payment | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Generate DN/CN | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Verify DN/CN | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Submit Claim | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Review Claim | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Pay Claim | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Submit Subrogation | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Review Subrogation | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Configure System | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| View Audit Logs | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 3. DATA MODELLING

### 3.1 Updated Data Model Based on New Requirements

#### 3.1.1 Key Changes from Original Model

**1. Claim Reference to Debtor via nomor_polis**

Original:
```sql
Claim {
  debtor_id BIGINT FK "Reference to Debtor.cover_id"
}
```

Updated:
```sql
Claim {
  nomor_polis VARCHAR(50) NOT NULL "Reference to Debtor via policy number"
  debtor_id BIGINT NULL "Lookup result (for reference)"
}
```

**Rationale:**
- nomor_polis is more stable than cover_id
- Allows claims even when debtor records are revised
- Matches real-world business process (claims filed by policy number)

**2. Subrogation Reference via Claim**

```sql
Subrogation {
  claim_id VARCHAR(50) NOT NULL FK "Must reference existing claim"
  nomor_polis VARCHAR(50) NOT NULL "Inherited from claim"
}
```

**3. Nota Premium with Claim Offset**

```sql
Nota {
  nota_type ENUM('Batch', 'Claim', 'Subrogation')
  reference_id VARCHAR(50) "Batch IDs or Claim ID or Subrogation ID"
  gross_amount DECIMAL(18,2) "Before offset"
  claim_offset_amount DECIMAL(18,2) "Claims from previous month"
  amount DECIMAL(18,2) "Final = gross - offset"
  claim_offset_period VARCHAR(7) "YYYY-MM of claims"
  offset_claim_ids TEXT "Comma-separated claim IDs"
}
```

**4. Batch Collection Logic (3 Batches)**

```sql
Batch {
  batch_sequence TINYINT "1, 2, or 3"
  collection_month VARCHAR(7) "YYYY-MM"
  collection_complete BOOLEAN "TRUE when 3 batches collected"
}

-- New table: BatchCollection
BatchCollection {
  collection_id VARCHAR(50) PK
  contract_id VARCHAR(50) FK
  collection_month VARCHAR(7) "YYYY-MM"
  batch_1_id VARCHAR(50) FK
  batch_2_id VARCHAR(50) FK  
  batch_3_id VARCHAR(50) FK
  all_validated BOOLEAN
  nota_generated BOOLEAN
  nota_id VARCHAR(50) FK
}
```

#### 3.1.2 Updated Entity Definitions

**BATCH (Updated)**

```sql
CREATE TABLE Batch (
  batch_id VARCHAR(50) NOT NULL PRIMARY KEY,
  batch_sequence TINYINT NOT NULL COMMENT '1, 2, or 3',
  batch_month TINYINT NOT NULL COMMENT 'Batch month (1-12)',
  batch_year SMALLINT NOT NULL COMMENT 'Batch year',
  collection_month VARCHAR(7) NOT NULL COMMENT 'YYYY-MM for 3-batch grouping',
  contract_id VARCHAR(50) NOT NULL,
  total_records INT NOT NULL DEFAULT 0,
  total_exposure DECIMAL(18,2) NOT NULL DEFAULT 0,
  total_premium DECIMAL(18,2) NOT NULL DEFAULT 0,
  final_exposure_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  final_premium_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  debtor_review_completed BOOLEAN NOT NULL DEFAULT FALSE,
  batch_ready_for_nota BOOLEAN NOT NULL DEFAULT FALSE,
  status ENUM('Uploaded', 'Validated', 'Matched', 'Approved', 
    'Nota Issued', 'Branch Confirmed', 'Paid', 'Closed', 
    'Rejected', 'Reopen Requested', 'Reopened') NOT NULL DEFAULT 'Uploaded',
  -- ... other fields ...
  
  CONSTRAINT chk_batch_sequence CHECK (batch_sequence BETWEEN 1 AND 3),
  CONSTRAINT fk_batch_contract FOREIGN KEY (contract_id) 
    REFERENCES Contract(contract_number),
  INDEX idx_collection (contract_id, collection_month, batch_sequence)
) ENGINE=InnoDB;
```

**BATCH_COLLECTION (New)**

```sql
CREATE TABLE BatchCollection (
  collection_id VARCHAR(50) NOT NULL PRIMARY KEY,
  contract_id VARCHAR(50) NOT NULL,
  collection_month VARCHAR(7) NOT NULL COMMENT 'YYYY-MM',
  batch_1_id VARCHAR(50),
  batch_2_id VARCHAR(50),
  batch_3_id VARCHAR(50),
  all_validated BOOLEAN NOT NULL DEFAULT FALSE,
  nota_generated BOOLEAN NOT NULL DEFAULT FALSE,
  nota_id VARCHAR(50),
  total_gross_premium DECIMAL(18,2) COMMENT 'Sum of 3 batches',
  claim_offset_amount DECIMAL(18,2) DEFAULT 0 COMMENT 'Previous month claims',
  net_premium DECIMAL(18,2) COMMENT 'After claim offset',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE INDEX uk_collection_period (contract_id, collection_month),
  INDEX idx_contract (contract_id),
  FOREIGN KEY (contract_id) REFERENCES Contract(contract_number),
  FOREIGN KEY (batch_1_id) REFERENCES Batch(batch_id),
  FOREIGN KEY (batch_2_id) REFERENCES Batch(batch_id),
  FOREIGN KEY (batch_3_id) REFERENCES Batch(batch_id),
  FOREIGN KEY (nota_id) REFERENCES Nota(nota_number),
  
  CONSTRAINT chk_all_batches_present CHECK (
    (batch_1_id IS NOT NULL AND batch_2_id IS NOT NULL AND batch_3_id IS NOT NULL)
    OR all_validated = FALSE
  )
) ENGINE=InnoDB;
```

**NOTA (Updated)**

```sql
CREATE TABLE Nota (
  nota_number VARCHAR(50) NOT NULL PRIMARY KEY,
  nota_type ENUM('Batch', 'Claim', 'Subrogation') NOT NULL,
  reference_id VARCHAR(50) NOT NULL COMMENT 'Collection ID, Claim ID, or Subrogation ID',
  contract_id VARCHAR(50),
  
  -- Premium nota specific
  gross_amount DECIMAL(18,2) COMMENT 'Before offset (for Premium nota)',
  claim_offset_amount DECIMAL(18,2) DEFAULT 0 COMMENT 'Previous month claims',
  claim_offset_period VARCHAR(7) COMMENT 'YYYY-MM of offset claims',
  offset_claim_ids TEXT COMMENT 'Comma-separated claim IDs used for offset',
  
  amount DECIMAL(18,2) NOT NULL COMMENT 'Final amount (gross - offset for Premium, direct for Claim/Subrogation)',
  currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
  status ENUM('Draft', 'Issued', 'Confirmed', 'Paid') NOT NULL DEFAULT 'Draft',
  
  -- ... other fields ...
  
  FOREIGN KEY (contract_id) REFERENCES Contract(contract_number),
  INDEX idx_type_period (nota_type, claim_offset_period),
  INDEX idx_reference (reference_id)
) ENGINE=InnoDB;
```

**CLAIM (Updated)**

```sql
CREATE TABLE Claim (
  claim_no VARCHAR(50) NOT NULL PRIMARY KEY,
  policy_no VARCHAR(50) COMMENT 'Policy number',
  nomor_polis VARCHAR(50) NOT NULL COMMENT 'Reference to Debtor (PRIMARY REFERENCE)',
  nomor_sertifikat VARCHAR(50),
  nama_tertanggung VARCHAR(200) NOT NULL,
  no_ktp_npwp VARCHAR(50),
  no_fasilitas_kredit VARCHAR(50),
  bdo_premi VARCHAR(20),
  tanggal_realisasi_kredit DATE,
  plafond DECIMAL(18,2),
  max_coverage DECIMAL(18,2),
  kol_debitur VARCHAR(10),
  dol DATE COMMENT 'Date of Loss',
  nilai_klaim DECIMAL(18,2) NOT NULL,
  share_tugure_percentage DECIMAL(5,2),
  share_tugure_amount DECIMAL(18,2),
  check_bdo_premi BOOLEAN NOT NULL DEFAULT FALSE,
  
  batch_id VARCHAR(50) COMMENT 'Source batch (optional)',
  debtor_id BIGINT COMMENT 'Resolved debtor ID (for reference)',
  contract_id VARCHAR(50),
  version_no INT NOT NULL DEFAULT 1,
  status ENUM('Draft', 'Checked', 'Doc Verified', 'Invoiced', 'Paid') 
    NOT NULL DEFAULT 'Draft',
  
  claim_month VARCHAR(7) COMMENT 'YYYY-MM when claim approved',
  used_for_offset BOOLEAN DEFAULT FALSE COMMENT 'Used in premium offset',
  offset_nota_id VARCHAR(50) COMMENT 'Nota where this claim was offset',
  
  -- ... other fields ...
  
  FOREIGN KEY (batch_id) REFERENCES Batch(batch_id),
  FOREIGN KEY (contract_id) REFERENCES Contract(contract_number),
  INDEX idx_nomor_polis (nomor_polis),
  INDEX idx_claim_month (claim_month, status),
  INDEX idx_offset (used_for_offset, claim_month)
) ENGINE=InnoDB;
```

**SUBROGATION (Updated)**

```sql
CREATE TABLE Subrogation (
  subrogation_id VARCHAR(50) NOT NULL PRIMARY KEY,
  claim_id VARCHAR(50) NOT NULL COMMENT 'Must reference existing claim',
  nomor_polis VARCHAR(50) NOT NULL COMMENT 'Inherited from claim',
  debtor_id BIGINT COMMENT 'Resolved debtor ID',
  recovery_amount DECIMAL(18,2) NOT NULL,
  recovery_date DATE,
  status ENUM('Draft', 'Invoiced', 'Paid / Closed') NOT NULL DEFAULT 'Draft',
  
  -- ... other fields ...
  
  FOREIGN KEY (claim_id) REFERENCES Claim(claim_no),
  INDEX idx_claim (claim_id),
  INDEX idx_nomor_polis (nomor_polis)
) ENGINE=InnoDB;
```

#### 3.1.3 Business Rules Implementation

**BR-601: Claim Reference via nomor_polis**

```sql
-- Trigger to resolve debtor_id from nomor_polis
DELIMITER $$

CREATE TRIGGER trg_claim_resolve_debtor
BEFORE INSERT ON Claim
FOR EACH ROW
BEGIN
  -- Lookup debtor by nomor_polis
  SET NEW.debtor_id = (
    SELECT cover_id 
    FROM Debtor 
    WHERE nomor_rekening_pinjaman = NEW.nomor_polis 
      OR nomor_peserta = NEW.nomor_polis
    ORDER BY version_no DESC 
    LIMIT 1
  );
  
  -- Validate debtor exists
  IF NEW.debtor_id IS NULL THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Invalid nomor_polis: Debtor not found';
  END IF;
  
  -- Validate coverage is active on DOL
  IF EXISTS (
    SELECT 1 FROM Debtor
    WHERE cover_id = NEW.debtor_id
      AND (NEW.dol < tanggal_mulai_covering 
           OR NEW.dol > tanggal_akhir_covering)
  ) THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'DOL is outside coverage period';
  END IF;
END$$

DELIMITER ;
```

**BR-602: Batch Collection (3 Batches)**

```sql
DELIMITER $$

CREATE TRIGGER trg_batch_check_collection
AFTER UPDATE ON Batch
FOR EACH ROW
BEGIN
  DECLARE v_collection_id VARCHAR(50);
  DECLARE v_batch_count INT;
  DECLARE v_all_validated BOOLEAN;
  
  -- Only process when batch becomes Validated
  IF NEW.status = 'Validated' AND OLD.status != 'Validated' THEN
    
    -- Check or create collection
    SELECT collection_id INTO v_collection_id
    FROM BatchCollection
    WHERE contract_id = NEW.contract_id
      AND collection_month = NEW.collection_month
    LIMIT 1;
    
    IF v_collection_id IS NULL THEN
      -- Create new collection
      SET v_collection_id = CONCAT('COL-', NEW.collection_month, '-', UUID_SHORT());
      INSERT INTO BatchCollection (
        collection_id, contract_id, collection_month
      ) VALUES (
        v_collection_id, NEW.contract_id, NEW.collection_month
      );
    END IF;
    
    -- Assign batch to collection slot
    UPDATE BatchCollection
    SET 
      batch_1_id = CASE 
        WHEN batch_1_id IS NULL AND NEW.batch_sequence = 1 THEN NEW.batch_id
        ELSE batch_1_id END,
      batch_2_id = CASE 
        WHEN batch_2_id IS NULL AND NEW.batch_sequence = 2 THEN NEW.batch_id
        ELSE batch_2_id END,
      batch_3_id = CASE 
        WHEN batch_3_id IS NULL AND NEW.batch_sequence = 3 THEN NEW.batch_id
        ELSE batch_3_id END
    WHERE collection_id = v_collection_id;
    
    -- Check if all 3 batches are collected
    SELECT 
      COUNT(*),
      (batch_1_id IS NOT NULL AND batch_2_id IS NOT NULL AND batch_3_id IS NOT NULL)
    INTO v_batch_count, v_all_validated
    FROM BatchCollection
    WHERE collection_id = v_collection_id;
    
    IF v_all_validated THEN
      UPDATE BatchCollection
      SET all_validated = TRUE
      WHERE collection_id = v_collection_id;
      
      -- Trigger nota generation (handled by separate process at month-end)
    END IF;
    
  END IF;
END$$

DELIMITER ;
```

**BR-603: Premium Offset with Previous Month Claims**

```sql
DELIMITER $$

CREATE PROCEDURE sp_generate_premium_nota(
  IN p_collection_id VARCHAR(50)
)
BEGIN
  DECLARE v_contract_id VARCHAR(50);
  DECLARE v_collection_month VARCHAR(7);
  DECLARE v_previous_month VARCHAR(7);
  DECLARE v_gross_premium DECIMAL(18,2);
  DECLARE v_claim_offset DECIMAL(18,2);
  DECLARE v_net_premium DECIMAL(18,2);
  DECLARE v_nota_number VARCHAR(50);
  DECLARE v_offset_claim_ids TEXT;
  
  -- Get collection details
  SELECT contract_id, collection_month
  INTO v_contract_id, v_collection_month
  FROM BatchCollection
  WHERE collection_id = p_collection_id;
  
  -- Calculate previous month
  SET v_previous_month = DATE_FORMAT(
    DATE_SUB(STR_TO_DATE(CONCAT(v_collection_month, '-01'), '%Y-%m-%d'), INTERVAL 1 MONTH),
    '%Y-%m'
  );
  
  -- Calculate gross premium (sum of 3 batches)
  SELECT 
    COALESCE(SUM(b.final_premium_amount), 0)
  INTO v_gross_premium
  FROM BatchCollection bc
  LEFT JOIN Batch b ON b.batch_id IN (bc.batch_1_id, bc.batch_2_id, bc.batch_3_id)
  WHERE bc.collection_id = p_collection_id;
  
  -- Calculate claim offset (approved claims from previous month)
  SELECT 
    COALESCE(SUM(share_tugure_amount), 0),
    GROUP_CONCAT(claim_no)
  INTO v_claim_offset, v_offset_claim_ids
  FROM Claim
  WHERE contract_id = v_contract_id
    AND claim_month = v_previous_month
    AND status IN ('Doc Verified', 'Invoiced', 'Paid')
    AND used_for_offset = FALSE;
  
  -- Calculate net premium
  SET v_net_premium = v_gross_premium - COALESCE(v_claim_offset, 0);
  
  -- If net is negative, carry forward (not implemented here, business decision needed)
  IF v_net_premium < 0 THEN
    SET v_net_premium = 0;
    -- TODO: Handle carry forward logic
  END IF;
  
  -- Generate nota
  SET v_nota_number = CONCAT('NTA-', v_collection_month, '-', LPAD(NEXT_SEQUENCE(), 4, '0'));
  
  INSERT INTO Nota (
    nota_number, nota_type, reference_id, contract_id,
    gross_amount, claim_offset_amount, claim_offset_period,
    offset_claim_ids, amount, status
  ) VALUES (
    v_nota_number, 'Batch', p_collection_id, v_contract_id,
    v_gross_premium, v_claim_offset, v_previous_month,
    v_offset_claim_ids, v_net_premium, 'Draft'
  );
  
  -- Mark claims as used for offset
  UPDATE Claim
  SET used_for_offset = TRUE,
      offset_nota_id = v_nota_number
  WHERE claim_no IN (
    SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(v_offset_claim_ids, ',', numbers.n), ',', -1)
    FROM (SELECT 1 n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) numbers
    WHERE CHAR_LENGTH(v_offset_claim_ids) - CHAR_LENGTH(REPLACE(v_offset_claim_ids, ',', '')) >= numbers.n - 1
  );
  
  -- Update collection
  UPDATE BatchCollection
  SET nota_generated = TRUE,
      nota_id = v_nota_number,
      total_gross_premium = v_gross_premium,
      claim_offset_amount = v_claim_offset,
      net_premium = v_net_premium
  WHERE collection_id = p_collection_id;
  
  -- Update batch status
  UPDATE Batch
  SET status = 'Nota Issued',
      nota_issued_date = CURDATE()
  WHERE batch_id IN (
    SELECT batch_1_id FROM BatchCollection WHERE collection_id = p_collection_id
    UNION
    SELECT batch_2_id FROM BatchCollection WHERE collection_id = p_collection_id
    UNION
    SELECT batch_3_id FROM BatchCollection WHERE collection_id = p_collection_id
  );
  
END$$

DELIMITER ;
```

### 3.2 Updated ERD with New Relationships

```
┌─────────────────────────────────────┐
│         Contract                    │
└─────────────────┬───────────────────┘
                  │ 1
                  │
                  ↓ 0..*
┌─────────────────────────────────────┐
│       BatchCollection               │ PK: collection_id
│  ────────────────────────────────   │ UK: (contract_id, collection_month)
│  • collection_id (PK)               │
│  • contract_id (FK)                 │
│  • collection_month (YYYY-MM)       │
│  • batch_1_id (FK)                  │
│  • batch_2_id (FK)                  │
│  • batch_3_id (FK)                  │
│  • all_validated                    │
│  • nota_generated                   │
│  • nota_id (FK)                     │
│  • total_gross_premium              │
│  • claim_offset_amount              │
│  • net_premium                      │
└─────────────────┬───────────────────┘
                  │ 1
                  │
                  ↓ 3 (exactly)
┌─────────────────────────────────────┐
│           Batch                     │ PK: batch_id
│  ────────────────────────────────   │ UK: (contract_id, collection_month, batch_sequence)
│  • batch_id (PK)                    │
│  • batch_sequence (1/2/3)           │
│  • collection_month (YYYY-MM)       │
│  • contract_id (FK)                 │
│  • final_premium_amount             │
│  • status                           │
└─────────────────┬───────────────────┘
                  │ 1
                  │
                  ↓ 1..*
┌─────────────────────────────────────┐
│          Debtor                     │ PK: cover_id
│  ────────────────────────────────   │
│  • cover_id (PK)                    │
│  • batch_id (FK)                    │
│  • nomor_polis ◆                    │ ← Used as reference
│  • nomor_peserta                    │
│  • nomor_rekening_pinjaman          │
│  • nama_peserta                     │
│  • plafon                           │
│  • nominal_premi                    │
└─────────────────────────────────────┘
                  ║
                  ║ Referenced by nomor_polis
                  ║ (not direct FK)
                  ↓ 0..*
┌─────────────────────────────────────┐
│           Claim                     │ PK: claim_no
│  ────────────────────────────────   │
│  • claim_no (PK)                    │
│  • nomor_polis ◆                    │ ← PRIMARY REFERENCE
│  • debtor_id (resolved)             │
│  • nilai_klaim                      │
│  • share_tugure_amount              │
│  • claim_month (YYYY-MM)            │
│  • used_for_offset                  │
│  • offset_nota_id                   │
│  • status                           │
└─────────────────┬───────────────────┘
                  │ 1
                  │
                  ↓ 0..*
┌─────────────────────────────────────┐
│       Subrogation                   │ PK: subrogation_id
│  ────────────────────────────────   │
│  • subrogation_id (PK)              │
│  • claim_id (FK) ◆                  │
│  • nomor_polis (inherited)          │
│  • recovery_amount                  │
│  • status                           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      BatchCollection                │
└─────────────────┬───────────────────┘
                  │ 1
                  │ (generates)
                  ↓ 0..1
┌─────────────────────────────────────┐
│    Nota (type: Batch)               │ PK: nota_number
│  ────────────────────────────────   │
│  • nota_number (PK)                 │
│  • nota_type = 'Batch'              │
│  • reference_id = collection_id     │
│  • gross_amount                     │ ← SUM(3 batches)
│  • claim_offset_amount              │ ← Previous month claims
│  • claim_offset_period              │
│  • offset_claim_ids                 │
│  • amount (net)                     │ ← gross - offset
└─────────────────────────────────────┘

Previous Month Claims Offset Flow:
┌─────────────────────────────────────┐
│  Claims (Month N-1)                 │
│  status = 'Doc Verified'            │
│  used_for_offset = FALSE            │
└─────────────────┬───────────────────┘
                  │
                  │ SUM(share_tugure_amount)
                  │
                  ↓
┌─────────────────────────────────────┐
│  Nota Premium (Month N)             │
│  gross_amount = SUM(3 batches)      │
│  claim_offset_amount = Claims(N-1)  │
│  amount = gross - offset            │
└─────────────────────────────────────┘
```

---

## 4. PROCESS MODELLING

[Continued in next part due to length...]

I'll continue with Process Modelling, but this is getting very long. Should I:
1. Create separate documents for Process Modelling and Interaction Modelling?
2. Continue in this single document?
3. Focus on specific workflows first?

