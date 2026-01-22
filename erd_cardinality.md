# DETAILED ENTITY RELATIONSHIP DIAGRAM
## Reinsurance Management System

This document provides detailed ERD with cardinality notation, relationship types, and normalization notes.

---

## ERD NOTATION GUIDE

**Cardinality Symbols:**
- `1` = One (exactly one)
- `0..1` = Zero or One (optional)
- `1..*` = One or Many (at least one)
- `0..*` = Zero or Many (optional many)

**Relationship Types:**
- `→` = Non-identifying relationship (foreign key, not part of PK)
- `⇒` = Identifying relationship (foreign key is part of PK)
- `◇` = Optional relationship
- `◆` = Mandatory relationship

---

## 1. CORE CONTRACT HIERARCHY

```
┌─────────────────────────────────────┐
│      MasterContract                 │ PK: contract_id
│  ────────────────────────────────   │
│  • contract_id (PK)                 │ Attributes:
│  • policy_no                        │ - product_type: ENUM
│  • product_type                     │ - credit_type: ENUM
│  • credit_type                      │ - coverage dates
│  • coverage_start_date              │ - rates & percentages
│  • coverage_end_date                │ - eligibility rules
│  • share_tugure_percentage          │
│  • premium_rate                     │ Business Rules:
│  • allowed_kolektabilitas           │ - Two-level approval
│  • allowed_region                   │ - Version control
│  • parent_contract_id (FK)          │ - Self-referential
│  • version                           │
└─────────────────────────────────────┘
         │ 0..1
         │ (parent_contract_id)
         │ Self-Referential
         ↓ 0..*
┌─────────────────────────────────────┐
│      MasterContract (Child)         │
│  ────────────────────────────────   │
│  [Addendum/Version of parent]       │
└─────────────────────────────────────┘

         │ 1
         │ (generates)
         ↓ 0..*
┌─────────────────────────────────────┐
│         Contract                    │ PK: contract_number
│  ────────────────────────────────   │
│  • contract_number (PK)             │ Attributes:
│  • contract_name                    │ - status: ENUM
│  • cedant = 'BRINS'                 │ - dates
│  • reinsurer = 'TUGURE'             │
│  • credit_type                      │ Business Rules:
│  • start_date                       │ - One ACTIVE per credit_type
│  • end_date                         │ - Cannot delete with batches
│  • status                           │
└─────────────────────────────────────┘
```

**Relationship Details:**
- MasterContract ◆→ MasterContract (0..1 : 0..*) - Parent/Child for versioning
- MasterContract ◆→ Contract (1 : 0..*) - Template generates instances
- Constraint: Only one ACTIVE Contract per credit_type

---

## 2. BATCH & DEBTOR WORKFLOW

```
┌─────────────────────────────────────┐
│         Contract                    │
└─────────────────────────────────────┘
         │ 1
         │ (contract_id)
         ↓ 0..*
┌─────────────────────────────────────┐
│           Batch                     │ PK: batch_id
│  ────────────────────────────────   │ UK: (contract_id, batch_year, batch_month)
│  • batch_id (PK)                    │
│  • contract_id (FK) ◆               │ Attributes:
│  • batch_month (1-12)               │ - Workflow status (11 states)
│  • batch_year                       │ - Financial amounts
│  • total_records                    │ - Review flags
│  • total_exposure                   │ - Reopen tracking
│  • total_premium                    │ - Audit trail dates
│  • final_exposure_amount            │
│  • final_premium_amount             │ Business Rules:
│  • debtor_review_completed          │ - Strict status workflow
│  • batch_ready_for_nota             │ - Unique per contract-period
│  • status                           │ - Reopen requires approval
│  • operational_locked               │ - final_* = SUM(approved records)
└─────────────────────────────────────┘
         │ 1
         │ (batch_id)
         ↓ 1..*
┌─────────────────────────────────────┐
│          Debtor                     │ PK: cover_id
│  ────────────────────────────────   │ UK: (batch_id, nomor_peserta)
│  • cover_id (PK)                    │
│  • batch_id (FK) ◆                  │ Attributes:
│  • nomor_peserta ◆                  │ - Personal data
│  • nama_peserta ◆                   │ - Financial data
│  • plafon                           │ - Coverage dates
│  • nominal_premi                    │ - Calculated fields
│  • net_premi (calculated)           │ - Eligibility fields
│  • kolektabilitas                   │
│  • region_desc                      │ Business Rules:
│  • status                           │ - Validated against master
│  • is_locked                        │ - net_premi calculated
│  • version_no                       │ - Locked when approved
└─────────────────────────────────────┘
         │ 1
         │ (debtor_id)
         ↓ 1
┌─────────────────────────────────────┐
│          Record                     │ PK: (batch_id, debtor_id)
│  ────────────────────────────────   │
│  • batch_id (PK, FK) ◆              │ Attributes:
│  • debtor_id (PK, FK) ◆             │ - Review results
│  • record_status ◆                  │ - Revision tracking
│  • exposure_amount                  │
│  • premium_amount                   │ Business Rules:
│  • revision_reason                  │ - Updates Batch.final_*
│  • revision_count                   │ - Triggers review completion
│  • accepted/rejected metadata       │
└─────────────────────────────────────┘
```

**Relationship Details:**
- Contract ◆→ Batch (1 : 0..*) - One contract, many batches
- Batch ◆→ Debtor (1 : 1..*) - One batch, at least one debtor
- Batch ◆⇒ Record (1 : 1..*) - Identifying relationship
- Debtor ◆⇒ Record (1 : 1) - One-to-one relationship
- Composite PK in Record: (batch_id, debtor_id)

**Dependency:**
- Record.record_status changes → Triggers Batch final amount recalculation
- All Records reviewed → Sets Batch.debtor_review_completed = TRUE

---

## 3. FINANCIAL FLOW (NOTA & PAYMENT)

```
┌─────────────────────────────────────┐
│           Batch                     │
└─────────────────────────────────────┘
         │ 1
         │ (reference_id when nota_type='Batch')
         ↓ 0..*
┌─────────────────────────────────────┐
│            Nota                     │ PK: nota_number
│  ────────────────────────────────   │
│  • nota_number (PK)                 │ Attributes:
│  • nota_type ◆                      │ - Type: Batch/Claim/Subrogation
│  • reference_id ◆                   │ - Financial tracking
│  • amount ◆ (IMMUTABLE)             │ - Payment reconciliation
│  • total_actual_paid                │
│  • reconciliation_status            │ Business Rules:
│  • is_immutable                     │ - Immutable when Issued
│  • status                           │ - Amount from source entity
└─────────────────────────────────────┘
         │ 1                          │ 1
         │                            │
         ↓ 0..*                       ↓ 0..*
┌──────────────────────┐    ┌──────────────────────┐
│  DebitCreditNote     │    │      Payment         │ PK: payment_ref
│  ──────────────────  │    │  ──────────────────  │
│  • note_number (PK)  │    │  • payment_ref (PK)  │ Attributes:
│  • note_type ◆       │    │  • invoice_id (FK) ◆ │ - Bank reference
│  • original_nota_id  │    │  • amount ◆          │ - Matching status
│    (FK) ◆            │    │  • payment_date ◆    │ - Exception tracking
│  • adjustment_amount │    │  • match_status      │
│  • reason_code ◆     │    │  • exception_type    │ Business Rules:
│  • status            │    │  • matched_by        │ - Auto-match to Nota
└──────────────────────┘    └──────────────────────┘ - Update total_actual_paid
                                     │ 0..1           - Set exception_type
                                     │ (intent_id)
                                     ↑ 0..*
                            ┌──────────────────────┐
                            │   PaymentIntent      │ PK: intent_id
                            │  ──────────────────  │
                            │  • intent_id (PK)    │ Attributes:
                            │  • invoice_id (FK) ◆ │ - Payment planning
                            │  • planned_amount ◆  │ - Approval workflow
                            │  • planned_date ◆    │
                            │  • payment_type      │ Business Rules:
                            │  • status            │ - Plan before payment
                            └──────────────────────┘ - Approval required

         ┌─────────────────────────────────────┐
         │            Nota                     │
         └─────────────────────────────────────┘
                  │ 1
                  │
                  ↓ 1
         ┌─────────────────────────────────────┐
         │       Reconciliation                │ PK: recon_id
         │  ────────────────────────────────   │ UK: (contract_id, period)
         │  • recon_id (PK)                    │
         │  • contract_id (FK) ◆               │ Attributes:
         │  • period ◆                         │ - Totals comparison
         │  • total_invoiced                   │ - Difference tracking
         │  • total_paid                       │
         │  • difference                       │ Business Rules:
         │  • status                           │ - One per contract-period
         └─────────────────────────────────────┘ - difference = invoiced - paid
```

**Relationship Details:**
- Batch/Claim/Subrogation ◆→ Nota (1 : 0..*) - Polymorphic via nota_type
- Nota ◆→ DebitCreditNote (1 : 0..*) - Adjustment notes
- Nota ◆→ Payment (1 : 0..*) - Actual payments
- Nota ◆→ Reconciliation (1 : 1) - One reconciliation per nota
- PaymentIntent ◆→ Payment (0..1 : 0..*) - Plan may have many payments

**Payment Flow:**
1. Nota issued (amount locked)
2. PaymentIntent created (optional)
3. Payment received → match to Nota
4. Update Nota.total_actual_paid
5. Calculate reconciliation_status
6. If variance → create DebitCreditNote

---

## 4. BORDERO & INVOICE FLOW

```
┌─────────────────────────────────────┐
│         Contract                    │
└─────────────────────────────────────┘
         │ 1                          │ 1
         │                            │
         ↓ 0..*                       ↓ 0..*
┌─────────────────────┐      ┌─────────────────────┐
│       Batch         │      │      Bordero        │ PK: bordero_id
└─────────────────────┘      │  ──────────────────  │
         │ 1                 │  • bordero_id (PK)  │ Attributes:
         │                   │  • contract_id (FK) │ - Period statement
         │                   │  • batch_id (FK) ◇  │ - Aggregated totals
         │                   │  • period ◆         │ - Review workflow
         └───────────────────┤  • total_debtors    │
                   0..1      │  • total_exposure   │ Business Rules:
                             │  • total_premium    │ - One per batch
                             │  • status           │ - Aggregates batch data
                             └─────────────────────┘
                                      │ 1
                                      │
                                      ↓ 0..*
                             ┌─────────────────────┐
                             │      Invoice        │ PK: invoice_number
                             │  ──────────────────  │
                             │  • invoice_number   │ Attributes:
                             │    (PK)             │ - Billing document
                             │  • bordero_id (FK)◇ │ - Payment tracking
                             │  • contract_id (FK) │
                             │  • total_amount ◆   │ Business Rules:
                             │  • paid_amount      │ - Links to Nota
                             │  • outstanding      │ - Tracks payments
                             │  • due_date         │
                             │  • status           │
                             └─────────────────────┘
```

**Relationship Details:**
- Contract ◆→ Bordero (1 : 0..*) - Statement per contract
- Batch ◇→ Bordero (0..1 : 1) - Optional one-to-one
- Bordero ◆→ Invoice (1 : 0..*) - Generates invoices
- Invoice ◇→ Nota (0..1 : 0..*) - May link to notas

---

## 5. CLAIM & SUBROGATION FLOW

```
┌─────────────────────────────────────┐
│          Batch                      │
└─────────────────────────────────────┘
         │ 1
         │
         ↓ 0..*
┌─────────────────────────────────────┐
│         Debtor                      │
└─────────────────────────────────────┘
         │ 1
         │
         ↓ 0..*
┌─────────────────────────────────────┐
│           Claim                     │ PK: claim_no
│  ────────────────────────────────   │
│  • claim_no (PK)                    │ Attributes:
│  • nama_tertanggung ◆               │ - Insured data
│  • nilai_klaim ◆                    │ - Loss details
│  • dol (Date of Loss)               │ - TUGURE share calc
│  • share_tugure_percentage          │ - Approval workflow
│  • share_tugure_amount              │
│  • batch_id (FK) ◇                  │ Business Rules:
│  • debtor_id (FK) ◇                 │ - Links to debtor coverage
│  • status                           │ - Validates eligibility
│  • version_no                       │ - Generates nota when approved
└─────────────────────────────────────┘
         │ 1                          │ 1
         │                            │
         ↓ 0..*                       ↓ 0..1
┌──────────────────────┐    ┌──────────────────────┐
│   Subrogation        │    │        Nota          │
│  ──────────────────  │    │  (nota_type='Claim') │
│  • subrogation_id    │    └──────────────────────┘
│    (PK)              │
│  • claim_id (FK) ◆   │    Attributes:
│  • recovery_amount ◆ │    - Recovery tracking
│  • recovery_date     │    - Workflow status
│  • status            │
└──────────────────────┘    Business Rules:
         │ 1                 - Requires claim
         │                   - Generates nota
         ↓ 0..1
┌──────────────────────┐
│        Nota          │
│  (nota_type=         │
│   'Subrogation')     │
└──────────────────────┘
```

**Relationship Details:**
- Debtor ◇→ Claim (1 : 0..*) - Optional claims
- Batch ◇→ Claim (1 : 0..*) - Claims from batch
- Claim ◆→ Subrogation (1 : 0..*) - Recovery from claims
- Claim ◆→ Nota (1 : 0..1) - One claim nota
- Subrogation ◆→ Nota (1 : 0..1) - One subrogation nota

**Claim Flow:**
1. Claim submitted (references Debtor)
2. Validation against MasterContract
3. Approval workflow
4. Nota generated (nota_type='Claim')
5. If recovery → Subrogation record
6. Subrogation nota generated

---

## 6. SYSTEM & MONITORING

```
┌─────────────────────────────────────┐
│       SystemConfig                  │ PK: (config_type, config_key)
│  ────────────────────────────────   │
│  • config_type (PK) ◆               │ Attributes:
│  • config_key (PK) ◆                │ - Key-value configuration
│  • config_value ◆                   │ - Versioned
│  • version                          │ - Active flag
│  • is_active                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          SlaRule                    │ PK: rule_name
│  ────────────────────────────────   │
│  • rule_name (PK)                   │ Attributes:
│  • entity_type ◆                    │ - Monitoring rules
│  • trigger_condition ◆              │ - Notification config
│  • duration_value                   │ - Recurrence settings
│  • recipient_role ◆                 │
│  • priority                         │ Business Rules:
│  • is_recurring                     │ - Monitors entity states
└─────────────────────────────────────┘ - Triggers notifications
         │ 1
         │ (triggers)
         ↓ 0..*
┌─────────────────────────────────────┐
│       Notification                  │ PK: notification_id
│  ────────────────────────────────   │
│  • notification_id (PK)             │ Attributes:
│  • title ◆                          │ - Alert data
│  • message ◆                        │ - Routing info
│  • type ◆                           │ - Read status
│  • target_role                      │
│  • target_user                      │ Business Rules:
│  • is_read                          │ - Created by SLA or manual
└─────────────────────────────────────┘ - Delivered per settings

┌─────────────────────────────────────┐
│    NotificationSetting              │ PK: user_email
│  ────────────────────────────────   │
│  • user_email (PK)                  │ Attributes:
│  • user_role ◆                      │ - User preferences
│  • email_enabled                    │ - Channel settings
│  • notify_* (many flags)            │ - Event subscriptions
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      EmailTemplate                  │ PK: template_id
│  ────────────────────────────────   │
│  • template_id (PK)                 │ Attributes:
│  • object_type ◆                    │ - Template per status change
│  • status_to ◆                      │ - Variable substitution
│  • recipient_role ◆                 │
│  • email_subject ◆                  │ Business Rules:
│  • email_body ◆                     │ - Used for notifications
└─────────────────────────────────────┘ - Supports variables

┌─────────────────────────────────────┐
│        AuditLog                     │ PK: audit_id
│  ────────────────────────────────   │ (Partitioned by year)
│  • audit_id (PK)                    │
│  • action ◆                         │ Attributes:
│  • module ◆                         │ - Change tracking
│  • entity_type                      │ - User tracking
│  • entity_id                        │ - Value comparison
│  • old_value                        │
│  • new_value                        │ Business Rules:
│  • user_email ◆                     │ - Auto-created by triggers
│  • created_at                       │ - Immutable
└─────────────────────────────────────┘ - 7-year retention
```

**Relationship Details:**
- SlaRule ◆→ Notification (1 : 0..*) - Rules trigger alerts
- EmailTemplate ◆→ Notification (1 : 0..*) - Templates format emails
- NotificationSetting ◇→ Notification (0..1 : 0..*) - User preferences
- All entities → AuditLog (for critical changes)

---

## 7. NORMALIZATION ANALYSIS

### Third Normal Form (3NF) Compliance

**MasterContract:** ✓ 3NF
- No transitive dependencies
- All non-key attributes depend only on contract_id

**Batch:** ✓ 3NF with Denormalization
- Denormalized: final_exposure_amount, final_premium_amount
- Reason: Performance (frequent queries)
- Maintained by triggers

**Debtor:** ✓ 3NF with Denormalization
- Denormalized: net_premi (calculated field)
- Denormalized: unit_desc, branch_desc, region_desc
- Reason: Avoid joins on reads; infrequent updates

**Record:** ✓ 3NF
- Composite PK: (batch_id, debtor_id)
- All attributes depend on full key

**Nota:** ✓ 3NF with Denormalization
- Denormalized: total_actual_paid
- Reason: Performance (updated by trigger)

**Claim:** ✓ 3NF with Denormalization
- Denormalized: share_tugure_amount (calculated)
- Reason: Historical accuracy (rate may change)

### Denormalization Decisions Summary

| Table | Denormalized Field | Reason | Maintenance |
|-------|-------------------|--------|-------------|
| Batch | final_*_amount | Performance | Trigger on Record |
| Debtor | net_premi | Calculation cost | Calculated on save |
| Debtor | *_desc fields | Avoid joins | Rarely updated |
| Nota | total_actual_paid | Query frequency | Trigger on Payment |
| Claim | share_tugure_amount | Historical accuracy | Set once |

---

## 8. REFERENTIAL INTEGRITY CONSTRAINTS

### CASCADE Rules

**ON DELETE CASCADE:**
- Record → Debtor (when debtor deleted, remove records)
- Record → Batch (when batch deleted, remove records)

**ON DELETE RESTRICT:**
- All other foreign keys (prevent deletion of referenced records)

**ON UPDATE CASCADE:**
- Implicit for all foreign keys

### Check Constraints Summary

| Table | Constraint | Rule |
|-------|-----------|------|
| Batch | chk_batch_month | month BETWEEN 1 AND 12 |
| Batch | chk_batch_amounts | final amounts >= 0 |
| Debtor | chk_debtor_kolektabilitas | kolektabilitas BETWEEN 1 AND 5 |
| Debtor | chk_debtor_percentages | percentages >= 0 |
| Nota | chk_nota_amount | amount > 0 |
| Payment | chk_payment_amount | amount > 0 |
| Contract | chk_contract_dates | end_date > start_date |

---

## 9. INDEXING STRATEGY SUMMARY

### Primary Indexes (Clustered)
All PKs are clustered indexes by default

### Secondary Indexes by Query Pattern

**High-Frequency Queries:**
```sql
-- Batch lookup by contract and period
idx_batch_contract_period (contract_id, batch_year, batch_month)

-- Debtor search by name
idx_debtor_nama (nama_peserta) + FULLTEXT

-- Payment matching
idx_payment_nota (invoice_id, match_status)

-- Nota reconciliation
idx_nota_type_status (nota_type, status)
```

**Partial Indexes (MySQL 8.0+):**
```sql
-- Only index active batches
idx_batch_active WHERE status NOT IN ('Closed', 'Rejected')

-- Only index unmatched payments
idx_payment_unmatched WHERE match_status = 'UNMATCHED'
```

### Covering Indexes

For queries that don't need table lookups:
```sql
CREATE INDEX idx_batch_summary ON Batch(
  contract_id, status, batch_year, batch_month, 
  final_premium_amount
) WHERE status IN ('Approved', 'Nota Issued');
```

---

## APPENDIX: CARDINALITY SUMMARY TABLE

| Parent Entity | Child Entity | Cardinality | Type | FK Nullable | Notes |
|---------------|--------------|-------------|------|-------------|-------|
| MasterContract | MasterContract | 1:0..* | Non-ID | Yes | Self-referential |
| MasterContract | Contract | 1:0..* | Non-ID | No | Template to instance |
| Contract | Batch | 1:0..* | Non-ID | No | Monthly submissions |
| Batch | Debtor | 1:1..* | Non-ID | No | At least one debtor |
| Batch | Record | 1:1..* | Identifying | No | Composite PK |
| Debtor | Record | 1:1 | Identifying | No | One-to-one |
| Batch | Nota | 1:0..* | Non-ID | Yes | Premium notas |
| Batch | Bordero | 1:0..1 | Non-ID | Yes | Optional bordero |
| Contract | Bordero | 1:0..* | Non-ID | No | Statement generation |
| Bordero | Invoice | 1:0..* | Non-ID | Yes | Invoice generation |
| Nota | DebitCreditNote | 1:0..* | Non-ID | No | Adjustments |
| Nota | Payment | 1:0..* | Non-ID | Yes | Payments |
| Nota | Reconciliation | 1:1 | Non-ID | No | One-to-one |
| PaymentIntent | Payment | 1:0..* | Non-ID | Yes | Optional planning |
| Debtor | Claim | 1:0..* | Non-ID | Yes | Optional claims |
| Batch | Claim | 1:0..* | Non-ID | Yes | Claim source |
| Claim | Subrogation | 1:0..* | Non-ID | No | Recovery |
| Claim | Nota | 1:0..1 | Non-ID | Yes | Claim nota |
| Subrogation | Nota | 1:0..1 | Non-ID | Yes | Subrogation nota |
| SlaRule | Notification | 1:0..* | Non-ID | Yes | Rule triggers |
| EmailTemplate | Notification | 1:0..* | Non-ID | Yes | Template usage |

---

**END OF DETAILED ERD DOCUMENT**
