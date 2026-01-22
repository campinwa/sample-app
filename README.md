# EXECUTIVE SUMMARY
## System Modeling - Reinsurance Management System (BRINS-TUGURE)

**Date:** January 22, 2026  
**Version:** 2.0 (Updated with new business requirements)

---

## 📋 OVERVIEW

Dokumen ini merangkum 5 aspek modeling sistem:

1. **Master Data Analysis** - Identifikasi data master
2. **Information Modelling** - Aliran informasi dan ownership
3. **Data Modelling** - Struktur database dengan update
4. **Process Modelling** - Workflow 5 proses utama
5. **Interaction Modelling** - Interaksi antar aktor dan sistem

---

## 1. MASTER DATA ANALYSIS

### Jawaban Pertanyaan 1: Berapa banyak Master Data?

**Total: 6 Master Data Entities**

| No | Entity | Type | Update Frequency | Impact |
|----|--------|------|------------------|--------|
| 1 | **MasterContract** | Primary Master | Yearly + Addendum | HIGH |
| 2 | **Contract** | Operational Master | Per MasterContract | HIGH |
| 3 | **SystemConfig** | System Master | Low-Medium | MEDIUM-HIGH |
| 4 | **SlaRule** | Monitoring Master | Medium | MEDIUM |
| 5 | **EmailTemplate** | Content Master | Low | LOW |
| 6 | **NotificationSetting** | User Master | User-controlled | LOW |

**14 Transactional Entities:**
Batch, Debtor, Record, Nota, Payment, PaymentIntent, Reconciliation, DebitCreditNote, Bordero, Invoice, Claim, Subrogation, Notification, AuditLog

### Master Data Characteristics

**MasterContract (Primary):**
- ✅ Version control dengan parent-child relationship
- ✅ Two-level approval (BRINS → TUGURE)
- ✅ Validity: 1 year
- ✅ Addendum creates new version
- ✅ Defines business rules untuk semua transaksi

**Contract (Operational):**
- ✅ Auto-generated dari approved MasterContract
- ✅ One ACTIVE contract per credit_type
- ✅ Referenced by semua transactional entities

---

## 2. INFORMATION MODELLING

### 2.1 Key Actors & Responsibilities

| Actor | Primary Role | Key Responsibilities |
|-------|-------------|---------------------|
| **BRINS** | Cedant, Submitter | Submit contract, batches, claims, pay premiums |
| **TUGURE** | Reinsurer, Approver | Review & approve, process claims, verify payments |
| **BSM (Broker)** | Data Provider | Collect & send debtor data to BRINS |
| **Finance BRINS** | Payer | Process premium payments, reconcile accounts |
| **Finance TUGURE** | Receiver | Verify payments, generate invoices, pay claims |
| **System** | Automator | Validate, generate nota, match payments, notify |

### 2.2 Information Flow Summary

**Premium Flow (Monthly):**
```
BSM → BRINS (3 batches) → System validation → 
TUGURE review → Nota generation (with claim offset) → 
Payment → Reconciliation
```

**Claim Flow (Ad-hoc):**
```
BRINS submit → System validation (via nomor_polis) → 
TUGURE review → Nota claim → TUGURE pays → 
Claim amount used for next month premium offset
```

**Subrogation Flow (Ad-hoc):**
```
BRINS submit (references Claim) → System validation → 
TUGURE review → Nota subrogation → BRINS pays back
```

### 2.3 Critical Information Updates

**Update 1: Claim Reference** ✨
- **OLD:** Claim references Debtor via `debtor_id` (cover_id)
- **NEW:** Claim references Debtor via `nomor_polis` (policy number)
- **Rationale:** More stable, matches business process

**Update 2: Premium Offset** ✨
- Previous month's approved claims automatically offset current month's premium
- Formula: `Net Premium = Gross Premium - Previous Month Claims`
- Example:
  - Dec 2025: Claims = Rp 100M
  - Jan 2026: Gross Premium = Rp 500M
  - Jan 2026: Net Payable = Rp 400M (500M - 100M)

**Update 3: Batch Collection** ✨
- Exactly **3 batches** required per month
- Nota generated **end of month** after all 3 batches validated
- New entity: `BatchCollection` untuk tracking

---

## 3. DATA MODELLING UPDATES

### 3.1 New/Updated Tables

**New Table: BATCH_COLLECTION**
```sql
Purpose: Track 3-batch monthly collection
Key Fields:
- collection_id (PK)
- contract_id (FK)
- collection_month (YYYY-MM)
- batch_1_id, batch_2_id, batch_3_id (FK to Batch)
- all_validated (BOOLEAN)
- nota_generated (BOOLEAN)
- nota_id (FK to Nota)
- total_gross_premium
- claim_offset_amount
- net_premium
```

**Updated Table: BATCH**
```sql
New Fields:
- batch_sequence (1, 2, or 3)
- collection_month (YYYY-MM)

Constraint:
- Must have unique (contract_id, collection_month, batch_sequence)
```

**Updated Table: NOTA**
```sql
New Fields for Premium Nota:
- gross_amount (before offset)
- claim_offset_amount (from previous month)
- claim_offset_period (YYYY-MM)
- offset_claim_ids (comma-separated)
- amount (net = gross - offset)
```

**Updated Table: CLAIM**
```sql
Key Change:
- nomor_polis VARCHAR(50) NOT NULL ← PRIMARY REFERENCE
- debtor_id BIGINT NULL ← Resolved for reference only

New Fields:
- claim_month (YYYY-MM when approved)
- used_for_offset (BOOLEAN)
- offset_nota_id (which nota used this claim)
```

**Updated Table: SUBROGATION**
```sql
Key Field:
- claim_id VARCHAR(50) NOT NULL ← MUST reference Claim
- nomor_polis VARCHAR(50) ← Inherited from Claim
```

### 3.2 Updated Relationships

```
Contract (1) → BatchCollection (0..*)
BatchCollection (1) → Batch (3 exactly)
Batch (1) → Debtor (1..*)

Debtor.nomor_polis ← (reference) ← Claim.nomor_polis
Claim (1) → Subrogation (0..*)

BatchCollection (1) → Nota Premium (0..1)
Claim (1) → Nota Claim (0..1)
Subrogation (1) → Nota Subrogation (0..1)

Previous Month Claims → Current Month Nota (offset)
```

### 3.3 Key Business Rules

**BR-001: Batch Collection**
- Exactly 3 batches required per contract per month
- Batches collected with sequence 1, 2, 3
- Nota generated only after all 3 validated
- Generation timing: End of month

**BR-002: Claim Offset**
- All approved claims in Month N-1 offset premium in Month N
- Offset calculated: `SUM(share_tugure_amount)` from previous month
- Claims marked as `used_for_offset = TRUE`
- If `Net Premium < 0`, set to 0 (carry-forward TBD)

**BR-003: Claim Reference**
- Claims MUST use `nomor_polis` to reference Debtor
- System resolves `debtor_id` for internal tracking
- Validation: DOL must be within coverage period
- Validation: Claim amount ≤ max_coverage

**BR-004: Subrogation Link**
- MUST reference existing Claim via `claim_id`
- Inherits `nomor_polis` from Claim
- Recovery amount ≤ original claim amount
- Payment direction: BRINS → TUGURE (recovery payback)

---

## 4. PROCESS MODELLING

### 4.1 Five Core Workflows

#### **Workflow 1: Master Contract Acknowledgement**

```
Duration: 5-15 business days
Frequency: Yearly + ad-hoc addendum

[Draft] → BRINS Submit → [Pending BRINS Ack]
  → BRINS Acknowledge → [Pending TUGURE Ack]
  → TUGURE Review
    ├─ Approve → [Active] (valid 1 year)
    └─ Reject → [Rejected] → BRINS Revise → [Draft]

Addendum: Creates new version with parent_contract_id
```

**Key Steps:**
1. BRINS creates MasterContract (Draft)
2. BRINS submits & acknowledges
3. TUGURE reviews terms, rates, eligibility
4. If approved → Active (generate Contract instance)
5. If rejected → BRINS revises (new version)

**Actors:** BRINS (creator), TUGURE (approver)

---

#### **Workflow 2: Batch & Nota Premium (3-Batch Collection)**

```
Duration: 1 month (full cycle)
Frequency: Monthly
Requirement: Exactly 3 batches

Week 1: BSM → BRINS → [Batch 1 Uploaded] → Validated
Week 2: BSM → BRINS → [Batch 2 Uploaded] → Validated  
Week 3: BSM → BRINS → [Batch 3 Uploaded] → Validated
Week 4 (End of Month):
  ├─ System checks: 3 batches complete?
  ├─ Calculate previous month claims
  ├─ Generate Nota Premium
  │  • Gross = SUM(3 batches)
  │  • Offset = Previous month claims
  │  • Net = Gross - Offset
  └─ Notify BRINS Finance & TUGURE
```

**Key Steps:**
1. **BSM** sends debtor data to **BRINS** (per batch)
2. **BRINS** reviews & uploads batch (status: Uploaded)
3. **System** validates data (status: Validated)
4. **BRINS** reviews batch (status: Matched)
5. **Repeat** for batches 2 & 3
6. **End of Month:** System generates Nota
   - Look up previous month's approved claims
   - Calculate offset amount
   - Generate Nota with net payable amount
7. **TUGURE** reviews batches → Approve/Reject debtors
8. If revisions needed → BRINS revises → Nota recalculates

**Actors:** BSM (provider), BRINS (submitter), TUGURE (reviewer), System (automator)

**Critical Rule:** Nota IMMUTABLE after status = 'Issued'

---

#### **Workflow 3: Premium Payment & Reconciliation**

```
Duration: 7-15 business days
Frequency: Monthly (after Nota issued)

[Nota Issued (Net Amount)]
  ↓
BRINS Finance reviews
  ↓
BRINS creates PaymentIntent (optional)
  ↓
BRINS executes payment (Bank transfer)
  ↓
System receives payment notification
  ↓
System auto-reconciliation: Compare amounts
  ├─ Match → [Nota: Paid] ✅
  └─ Variance → Exception flow
       ↓
     Notify BRINS Finance (ACTION_REQUIRED)
       ↓
     BRINS confirms exception
       ↓
     TUGURE generates DN/CN
       • Underpayment → Debit Note
       • Overpayment → Credit Note
       ↓
     BRINS verifies DN/CN
       ↓
     System updates Nota amount
       ↓
     [Reconciliation: FINAL] ✅
```

**Key Steps:**
1. Nota issued with **net payable amount** (after claim offset)
2. BRINS Finance reviews & confirms
3. BRINS pays via bank transfer
4. System matches payment to Nota
5. **If match:** Nota status → Paid
6. **If variance:** 
   - Exception notification
   - BRINS confirms
   - TUGURE generates DN/CN
   - BRINS verifies
   - System adjusts Nota

**Actors:** Finance BRINS (payer), Finance TUGURE (verifier), System (matcher)

---

#### **Workflow 4: Claim Processing**

```
Duration: 15-30 business days
Frequency: Ad-hoc (as claims occur)

BRINS receives claim from debtor
  ↓
BRINS prepares claim (links via nomor_polis)
  ↓
BRINS uploads claim (status: Draft)
  ↓
System validates claim
  • Check debtor exists (via nomor_polis) ✅
  • Check coverage period (DOL within dates) ✅
  • Check claim amount ≤ max_coverage ✅
  • Check contract eligibility ✅
  ├─ Valid → status: Checked
  └─ Invalid → Return to BRINS with errors
       ↓
TUGURE reviews claim
  • Verify documents
  • Calculate share_tugure_amount
  ├─ Approve → status: Doc Verified
  └─ Reject → BRINS revises
       ↓
System generates Nota Claim
  • nota_type = 'Claim'
  • amount = share_tugure_amount
  • No claim offset (only Premium nota has offset)
       ↓
Nota issued → BRINS confirms
       ↓
TUGURE processes claim payment
       ↓
System records payment
       ↓
BRINS verifies payment received
       ↓
[Claim: Paid] ✅
       ↓
System marks claim for next month offset
  • claim_month = current month
  • used_for_offset = FALSE (will be TRUE next month)
```

**Key Steps:**
1. BRINS submits claim with **nomor_polis**
2. System validates against MasterContract
3. TUGURE reviews & approves
4. System generates Claim Nota
5. TUGURE pays claim amount
6. Claim amount used for **next month's premium offset**

**Actors:** BRINS Claims (submitter), TUGURE Claims (reviewer), Finance TUGURE (payer)

**Critical Rule:** Claim references Debtor via `nomor_polis` (not cover_id)

---

#### **Workflow 5: Subrogation Processing**

```
Duration: 30-90 days
Frequency: Ad-hoc (after claim paid, if recovery)

Claim paid (recovery opportunity identified)
  ↓
BRINS prepares subrogation
  • MUST reference claim_id
  • Inherits nomor_polis from Claim
  ↓
BRINS uploads subrogation (status: Draft)
  ↓
System validates subrogation
  • Claim exists & paid ✅
  • Recovery amount ≤ claim amount ✅
  • No duplicate subrogation ✅
  ├─ Valid → Continue
  └─ Invalid → Return with errors
       ↓
TUGURE reviews subrogation
  • Verify recovery documents
  • Verify legal basis
  ├─ Approve → status: Invoiced
  └─ Reject → BRINS revises
       ↓
System generates Nota Subrogation
  • nota_type = 'Subrogation'
  • amount = recovery_amount × share_%
  • Payment direction: BRINS → TUGURE
       ↓
Nota issued → BRINS confirms
       ↓
BRINS pays recovery share to TUGURE
       ↓
System records payment
       ↓
TUGURE verifies payment received
       ↓
[Subrogation: Paid/Closed] ✅
```

**Key Steps:**
1. BRINS submits subrogation (must reference Claim)
2. System validates recovery details
3. TUGURE reviews & approves
4. System generates Subrogation Nota
5. **BRINS pays TUGURE** (recovery payback)
6. Mark as closed

**Actors:** BRINS Claims (submitter), TUGURE Claims (reviewer), Finance BRINS (payer)

**Payment Direction:** BRINS → TUGURE (opposite of Claim)

---

### 4.2 Process Flow Summary Table

| Workflow | Duration | Frequency | Key Actor | Critical Output |
|----------|----------|-----------|-----------|-----------------|
| Master Contract | 5-15 days | Yearly + Addendum | BRINS, TUGURE | Active Contract |
| Batch & Nota | 1 month | Monthly | BRINS, TUGURE | Nota Premium (with offset) |
| Premium Payment | 7-15 days | Monthly | Finance BRINS | Paid Nota |
| Claim | 15-30 days | Ad-hoc | BRINS, TUGURE | Paid Claim (for offset) |
| Subrogation | 30-90 days | Ad-hoc | BRINS, TUGURE | Recovery Payback |

---

## 5. INTERACTION MODELLING

### 5.1 Actor Interactions Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM CONTEXT                            │
└─────────────────────────────────────────────────────────────┘

     BSM                    BRINS Users              TUGURE Users
     (Broker)               (Multi-role)             (Multi-role)
        │                        │                        │
        │ Send debtor data       │                        │
        └───────────────────────►│                        │
                                 │                        │
                                 │ Submit batches         │
                                 ├───────────────────────►│
                                 │                        │
                                 │ Review & approve ◄─────┤
                                 │                        │
                                 │ Submit claims          │
                                 ├───────────────────────►│
                                 │                        │
                                 │ Pay premium           │
                                 ├───────────────────────►│
                                 │                        │
                                 │ ◄───────────── Receive │
                                 │    claim payment       │
                                 │                        │
                                 ↓                        ↓
                    ┌────────────────────────────────────────┐
                    │    REINSURANCE MANAGEMENT SYSTEM       │
                    │                                        │
                    │  • Validate data                       │
                    │  • Generate nota (with offset)         │
                    │  • Match payments                      │
                    │  • Reconcile                           │
                    │  • Send notifications                  │
                    │  • Audit trail                         │
                    └────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ↓                         ↓
            External Systems           Database
            • Bank Gateway              • 20 Tables
            • Email Service             • 6 Master Data
            • Document Storage          • 14 Transactional
```

### 5.2 Key Sequence Diagrams

#### **Sequence 1: Premium Nota Generation with Claim Offset**

```
BSM  →  BRINS  →  System  →  TUGURE  →  Finance

Week 1-3: Collect 3 batches
  BSM sends data → BRINS uploads → System validates
  (Repeat 3 times)

Week 4 (End of Month):
  System: Check 3 batches complete?
    ↓ Yes
  System: Query previous month claims
    SELECT SUM(share_tugure_amount)
    FROM Claim  
    WHERE claim_month = 'YYYY-MM-prev'
      AND status IN ('Doc Verified', 'Invoiced', 'Paid')
      AND used_for_offset = FALSE
    ↓ Result: Rp 100,000,000
  
  System: Calculate net premium
    Gross = SUM(Batch1 + Batch2 + Batch3) = Rp 500,000,000
    Offset = Rp 100,000,000
    Net = Rp 400,000,000
  
  System: Generate Nota
    nota_type = 'Batch'
    gross_amount = 500,000,000
    claim_offset_amount = 100,000,000
    amount = 400,000,000
    status = 'Draft'
  
  System → BRINS Finance: "Nota ready"
  System → TUGURE: "Nota generated"
  
  BRINS Finance: Review nota
    ✓ Verify gross premium
    ✓ Check offset calculation
    ✓ Confirm net payable
  
  BRINS Finance → System: Confirm nota
  System: Update status = 'Issued', is_immutable = TRUE
```

#### **Sequence 2: Claim Validation via nomor_polis**

```
BRINS  →  System  →  TUGURE

BRINS Claims: Submit claim
  claim_no = "CLM-2026-001"
  nomor_polis = "POL-123456"  ← KEY REFERENCE
  nilai_klaim = 50,000,000
  dol = "2025-12-15"

System: Validate claim
  Step 1: Look up debtor
    SELECT cover_id, tanggal_mulai_covering, tanggal_akhir_covering
    FROM Debtor
    WHERE nomor_rekening_pinjaman = 'POL-123456'
       OR nomor_peserta = 'POL-123456'
    ↓ Found: cover_id = 789
  
  Step 2: Check coverage period
    IF dol BETWEEN tanggal_mulai_covering AND tanggal_akhir_covering
    ✓ Valid
  
  Step 3: Check max coverage
    IF nilai_klaim <= max_coverage
    ✓ Valid
  
  Step 4: Update claim
    SET debtor_id = 789
    SET status = 'Checked'

System → TUGURE Claims: "Claim ready for review"

TUGURE Claims: Review & approve
  status = 'Doc Verified'
  Calculate: share_tugure_amount = nilai_klaim × share_%

System: Generate Nota Claim
  nota_type = 'Claim'
  amount = share_tugure_amount
  status = 'Draft' → 'Issued'

... (continue with payment flow)
```

#### **Sequence 3: Payment Exception & DN/CN**

```
Finance BRINS  →  System  →  Finance TUGURE

Payment Scenario: Underpayment

BRINS pays: Rp 390,000,000
Expected (Nota): Rp 400,000,000
Variance: -10,000,000 (underpayment)

System: Detect variance
  actual < expected
  exception_type = 'UNDER'
  match_status = 'PARTIALLY_MATCHED'

System → BRINS Finance: Exception notification
  "Payment variance detected"
  "Expected: 400,000,000"
  "Received: 390,000,000"
  "Shortage: 10,000,000"

BRINS Finance: Confirm exception
  "We acknowledge the shortage"
  "Reason: Bank transfer fee deduction"

BRINS Finance → System: Exception confirmed

System → TUGURE Finance: "Exception confirmed by BRINS"

TUGURE Finance: Generate Debit Note
  note_type = 'Debit Note'
  adjustment_amount = +10,000,000
  reason_code = 'Payment Difference'
  status = 'Draft' → 'Under Review' → 'Approved'

TUGURE Finance → BRINS Finance: "DN generated"

BRINS Finance: Verify DN
  ✓ Check calculation
  ✓ Acknowledge DN
  status = 'Acknowledged'

System: Update Nota
  Original: 400,000,000
  DN: +10,000,000
  New balance: 410,000,000
  reconciliation_status = 'FINAL'
```

### 5.3 Interaction Matrix

| From ↓ To → | BSM | BRINS Ops | BRINS Finance | TUGURE | TUGURE Finance | System |
|-------------|-----|-----------|---------------|--------|----------------|--------|
| **BSM** | - | Debtor data | - | - | - | - |
| **BRINS Ops** | - | - | - | Batch submit | - | Upload data |
| **BRINS Finance** | - | - | - | - | Payment | Payment intent |
| **TUGURE** | - | Approve/reject | - | - | - | Review result |
| **TUGURE Finance** | - | - | DN/CN verify | - | - | Payment verify |
| **System** | - | Notification | Notification | Notification | Notification | - |

---

## 6. KEY TAKEAWAYS

### ✅ What's New

1. **Master Data:** 6 entities identified dengan clear governance
2. **Claim Reference:** Via `nomor_polis` instead of `debtor_id`
3. **Premium Offset:** Previous month claims auto-offset premium
4. **Batch Collection:** Exactly 3 batches required, nota at month-end
5. **New Table:** `BatchCollection` untuk tracking 3-batch logic

### ✅ Critical Business Rules

1. **Two-level Approval:** MasterContract requires BRINS + TUGURE acknowledgement
2. **3-Batch Collection:** Must collect exactly 3 batches before Nota generation
3. **Claim Offset:** All approved claims in Month N-1 offset premium in Month N
4. **Nota Immutability:** Amount cannot change after status = 'Issued'
5. **Exception Handling:** Payment variances trigger DN/CN workflow

### ✅ Payment Directions

| Transaction | From | To | Note |
|-------------|------|-----|------|
| Premium Payment | BRINS | TUGURE | Monthly, with offset |
| Claim Payment | TUGURE | BRINS | As approved |
| Subrogation Payment | BRINS | TUGURE | Recovery payback |
| DN/CN Adjustment | Per variance | Per variance | Reconciliation |

---

## 7. DOCUMENT REFERENCES

Semua modeling dijelaskan secara detail dalam dokumen-dokumen berikut:

1. **Comprehensive_Modeling_Document.md** (135+ KB)
   - Semua 5 modeling lengkap dengan diagrams
   
2. **Comprehensive_Modeling_Document_Part1.md** (95+ KB)
   - Master Data Analysis detail
   - Information Modelling
   - Data Modelling updates

3. **Data_Modeling_Document.md** (44 KB)
   - Conceptual, Logical, Physical model
   - Normalization analysis
   - Business rules

4. **DDL_MySQL_Complete.sql** (40 KB)
   - Complete MySQL DDL dengan triggers
   - Updated schema dengan semua changes

5. **Detailed_ERD_with_Cardinality.md** (20 KB)
   - ERD lengkap dengan cardinality notation
   - Relationship details

---

**END OF EXECUTIVE SUMMARY**

**For full details, refer to the complete modeling documents.**
