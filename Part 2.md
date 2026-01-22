# COMPREHENSIVE MODELING DOCUMENT
## Reinsurance Management System (BRINS - TUGURE)

**Document Version:** 2.0  
**Date:** January 22, 2026  
**Prepared By:** System Architecture Team

---

## TABLE OF CONTENTS

1. [Master Data Identification](#1-master-data-identification)
2. [Information Modeling](#2-information-modeling)
3. [Data Modeling (Updated)](#3-data-modeling-updated)
4. [Process Modeling](#4-process-modeling)
5. [Interaction Modeling](#5-interaction-modeling)

---

## 1. MASTER DATA IDENTIFICATION

### 1.1 Master Data Definition

Master data adalah data referensi yang:
- Memiliki lifecycle panjang (jarang berubah)
- Digunakan untuk validasi dan lookup
- Bersifat konfigurasi sistem
- Shared across multiple transactions
- Require governance dan data quality controls

### 1.2 Master Data Entities

Dari 20 entities dalam sistem, **6 entities** termasuk kategori Master Data:

#### **MD-01: MasterContract**
**Type:** Business Master Data  
**Purpose:** Template kontrak reasuransi dengan version control  
**Update Frequency:** Yearly (dengan addendum)  
**Volume:** ~10 records/year  
**Governance:** Requires dual approval (BRINS & TUGURE)

**Key Attributes:**
- contract_id (PK)
- policy_no
- product_type
- credit_type
- coverage rules (kolektabilitas, region)
- financial rates (premium_rate, ric_rate, bf_rate)
- version & parent tracking

**Business Rules:**
- Version controlled for addendum tracking
- Requires BRINS acknowledgement + TUGURE acknowledgement
- Cannot be deleted if has active Contract instances
- Defines eligibility rules for all child entities

---

#### **MD-02: Contract**
**Type:** Business Master Data  
**Purpose:** Active contract instances dari MasterContract  
**Update Frequency:** Quarterly to Yearly  
**Volume:** ~5 active contracts at any time  
**Governance:** Status controlled, only one ACTIVE per credit_type

**Key Attributes:**
- contract_number (PK)
- contract_name
- credit_type
- dates (start_date, end_date)
- status (ACTIVE/EXPIRED/TERMINATED)

**Business Rules:**
- Generated from approved MasterContract
- Only one ACTIVE contract per credit_type
- Cannot be deleted if has batches
- Expiration managed by end_date

---

#### **MD-03: SystemConfig**
**Type:** Technical Master Data  
**Purpose:** System configuration parameters  
**Update Frequency:** Ad-hoc (as needed)  
**Volume:** ~50-100 config parameters  
**Governance:** Admin only, versioned

**Key Attributes:**
- config_type (PK)
- config_key (PK)
- config_value
- version
- is_active

**Configuration Types:**
- STATUS_REFERENCE: Status mappings
- ELIGIBILITY_RULE: Business validation rules
- FINANCIAL_THRESHOLD: Min/max amounts
- APPROVAL_MATRIX: Approval workflows
- NOTIFICATION_RULE: Alert configurations
- NOTIFICATION_CHANNEL: Channel settings (email, SMS)

**Business Rules:**
- Version controlled
- Requires approval before active
- Can be time-bound with effective_date
- Cached for performance

---

#### **MD-04: SlaRule**
**Type:** Technical Master Data  
**Purpose:** SLA monitoring rules dan automatic triggers  
**Update Frequency:** Quarterly  
**Volume:** ~20-30 rules  
**Governance:** Admin configurable

**Key Attributes:**
- rule_name (PK)
- entity_type
- trigger_condition
- duration thresholds
- notification settings
- recurrence settings

**Monitored Entities:**
- Debtor, Batch, Claim, Subrogation
- Nota, Invoice, Payment, Reconciliation

**Trigger Conditions:**
- STATUS_DURATION: Stuck in status too long
- CREATED_DURATION: Not processed after creation
- UPDATED_DURATION: Not updated recently
- DUE_DATE_APPROACHING: Near deadline
- DUE_DATE_PASSED: Past deadline

**Business Rules:**
- Active/inactive flag
- Priority levels (LOW/MEDIUM/HIGH/CRITICAL)
- Recurring vs one-time notifications
- Role-based recipients

---

#### **MD-05: EmailTemplate**
**Type:** Technical Master Data  
**Purpose:** Email templates for status transitions  
**Update Frequency:** Monthly (refinements)  
**Volume:** ~50-100 templates  
**Governance:** Admin configurable, supports variables

**Key Attributes:**
- template_id (PK)
- object_type (Batch/Claim/Nota/etc)
- status_from
- status_to
- recipient_role
- email_subject & email_body

**Supported Variables:**
- {batch_id}, {claim_no}, {nota_number}
- {user_name}, {date}, {amount}
- {contract_name}, {period}

**Business Rules:**
- One template per (object_type, status_to, recipient_role)
- Variable substitution at runtime
- Supports HTML formatting
- Can be deactivated without deletion

---

#### **MD-06: NotificationSetting**
**Type:** User Master Data  
**Purpose:** User notification preferences  
**Update Frequency:** User-controlled  
**Volume:** One record per user (~100-200 users)  
**Governance:** User self-service

**Key Attributes:**
- user_email (PK)
- user_role
- channel preferences (email, WhatsApp)
- event subscriptions (11+ notification types)

**Notification Types:**
- notify_batch_status
- notify_nota_status
- notify_claim_status
- notify_subrogation_status
- notify_payment_received
- notify_approval_required
- etc.

**Business Rules:**
- Per-user customization
- Multiple channels supported
- Can disable specific event types
- Default settings for new users

---

### 1.3 Transactional Data (Non-Master)

**14 entities** are transactional data:

**Transaction Processing:**
- Batch, Debtor, Record (batch submission)
- Nota, DebitCreditNote (billing)
- Payment, PaymentIntent, Reconciliation (payment processing)
- Bordero, Invoice (statement generation)
- Claim, Subrogation (claims management)

**Operational:**
- Notification (runtime alerts)
- AuditLog (change tracking)

### 1.4 Master Data Management Requirements

#### Data Quality Controls
1. **Uniqueness:** Enforced by PKs and unique constraints
2. **Completeness:** Required fields marked NOT NULL
3. **Validity:** Check constraints and enums
4. **Consistency:** Foreign key constraints
5. **Accuracy:** Manual verification workflows

#### Change Management
1. **Version Control:** MasterContract, SystemConfig
2. **Approval Workflow:** Two-level approval for MasterContract
3. **Audit Trail:** All changes logged in AuditLog
4. **Rollback:** Version history allows rollback

#### Data Governance
1. **Ownership:** 
   - MasterContract: Joint (BRINS + TUGURE)
   - SystemConfig: System Admin
   - SlaRule: Operations Team
   - EmailTemplate: Communications Team
   - NotificationSetting: Individual Users

2. **Access Control:**
   - Read: All authenticated users
   - Update: Role-based (Admin, Supervisor)
   - Delete: Restricted (Admin only, with constraints)

---

## 2. INFORMATION MODELING

### 2.1 Business Glossary

#### Core Business Terms

**A**

**Addendum**
- Definition: Revision atau amendment terhadap MasterContract yang telah disepakati
- Synonyms: Amendment, Contract Revision
- Related Terms: MasterContract, Version
- Business Rule: Addendum creates new version with parent_contract_id linkage

**Approval Matrix**
- Definition: Struktur approval bertingkat untuk transaksi
- Levels: Two-level approval (First Approver → Second Approver)
- Related Terms: Acknowledgement, Workflow

**B**

**Batch**
- Definition: Kumpulan data debtor yang disubmit dalam satu periode
- Composition: 3 batches = 1 monthly nota
- Related Terms: Debtor, Nota, Bordero
- Business Rule: Maximum 3 batches per contract per month

**Bordero**
- Definition: Statement yang merangkum batch submission dalam periode tertentu
- Synonyms: Statement, Summary Report
- Related Terms: Batch, Invoice
- Business Rule: Generated after 3 batches collected

**BF (Broker Fee)**
- Definition: Biaya broker yang dipotong dari premi
- Calculation: nominal_premi × bf_percentage
- Related Terms: Premium, RIC

**BRINS (Cedant)**
- Definition: PT Asuransi BRINS - Cedant dalam perjanjian reasuransi
- Role: Submits batches, claims, payments
- Related Terms: Cedant, TUGURE

**C**

**Cedant**
- Definition: Perusahaan asuransi yang mengalihkan risiko ke reinsurer
- In this system: BRINS
- Related Terms: Reinsurer, Cession

**Claim**
- Definition: Klaim kerugian yang diajukan oleh BRINS ke TUGURE
- Reference: Based on nomor_polis (policy number)
- Related Terms: DOL (Date of Loss), Subrogation
- Business Rule: Must reference valid Debtor coverage

**Coverage**
- Definition: Periode dan jumlah proteksi yang diberikan
- Components: 
  - Coverage period (tanggal_mulai_covering - tanggal_akhir_covering)
  - Coverage amount (plafon)
  - Coverage percentage (share_tugure_percentage)

**D**

**Debtor (Debitur)**
- Definition: Nasabah BRINS yang coveragenya di-reinsure ke TUGURE
- Synonyms: Participant, Tertanggung
- Identification: nomor_peserta, nomor_polis
- Related Terms: Coverage, Batch

**Debit Note (DN)**
- Definition: Nota adjustment untuk kekurangan pembayaran (underpayment)
- When Generated: actual_payment < nota_amount
- Effect: Increases receivable amount
- Related Terms: Credit Note, Reconciliation

**Credit Note (CN)**
- Definition: Nota adjustment untuk kelebihan pembayaran (overpayment)
- When Generated: actual_payment > nota_amount
- Effect: Decreases receivable amount
- Related Terms: Debit Note, Reconciliation

**DOL (Date of Loss)**
- Definition: Tanggal terjadinya kerugian/klaim
- Related Terms: Claim, Loss Event

**E**

**Exposure**
- Definition: Total nilai risiko yang di-cover
- Calculation: Sum of plafon amounts
- Related Terms: Premium, Coverage

**F**

**Final Amount**
- Definition: Jumlah final setelah review (hanya approved debtors)
- Components:
  - final_exposure_amount
  - final_premium_amount
- Calculation: SUM(amount WHERE status='Approved')

**K**

**Kolektabilitas**
- Definition: Kategori koleksi kredit (1-5)
- Scale:
  - 1: Lancar
  - 2: Dalam Perhatian Khusus (DPK)
  - 3: Kurang Lancar
  - 4: Diragukan
  - 5: Macet
- Business Rule: Must be in allowed_kolektabilitas from MasterContract

**N**

**Nota**
- Definition: Billing document yang diterbitkan untuk transaksi
- Types:
  - Premium Nota (from Batch)
  - Claim Nota (from Claim)
  - Subrogation Nota (from Subrogation)
- Business Rule: Amount is IMMUTABLE after status='Issued'

**P**

**Plafon**
- Definition: Limit kredit maksimum untuk debtor
- Used in: Coverage calculation, claim validation
- Business Rule: Claim amount cannot exceed plafon

**Premium (Premi)**
- Definition: Biaya reasuransi yang dibayar BRINS ke TUGURE
- Components:
  - Gross Premium (nominal_premi)
  - Less: RIC (nominal_premi × ric_percentage)
  - Less: BF (nominal_premi × bf_percentage)
  - Net Premium (net_premi)

**R**

**Reconciliation**
- Definition: Proses matching pembayaran aktual dengan nota
- Status:
  - PENDING: No payment received
  - PARTIAL: Partial payment received
  - MATCHED: Full payment matched
  - OVERPAID: Excess payment
  - FINAL: Reconciliation closed
- Related Terms: Payment, Exception

**Reinsurer**
- Definition: Perusahaan yang menerima risiko dari cedant
- In this system: TUGURE
- Related Terms: Cedant, Cession

**RIC (Reinsurance Commission)**
- Definition: Komisi reasuransi yang dipotong dari premi
- Calculation: nominal_premi × ric_percentage
- Related Terms: Premium, BF

**S**

**Share TUGURE**
- Definition: Porsi risiko yang ditanggung TUGURE
- Expressed as: Percentage (e.g., 80%)
- Applied to: Premium, Claim, Subrogation
- Related Terms: Coverage, Cession

**Subrogation (Subrogasi)**
- Definition: Hak recovery dari pihak ketiga setelah claim dibayar
- Reference: Must link to existing Claim
- Related Terms: Claim, Recovery

**T**

**TUGURE (Reinsurer)**
- Definition: PT Reasuransi TUGURE - Reinsurer dalam perjanjian
- Role: Reviews and approves batches, processes claims
- Related Terms: Reinsurer, BRINS

---

### 2.2 Data Classification

#### By Sensitivity Level

**PUBLIC**
- Contract names
- Product types
- Status values

**INTERNAL**
- Batch summaries
- Financial aggregates
- System configurations

**CONFIDENTIAL**
- Debtor personal information (nama_peserta, alamat_usaha)
- CIF numbers
- Credit agreement numbers

**RESTRICTED**
- Financial amounts (premi, plafon, klaim)
- Bank references
- Payment details

**HIGHLY RESTRICTED**
- KTP/NPWP numbers
- Complete debtor profiles
- Detailed claim amounts

#### By Regulatory Requirement

**OJK (Otoritas Jasa Keuangan) Compliance**
- Contract documentation
- Premium calculations
- Claim processing records
- Audit trails

**Data Retention:**
- Master data: Permanent (with version history)
- Transactions: 7 years minimum
- Audit logs: 7 years minimum
- Notifications: 2 years

---

### 2.3 Data Quality Dimensions

#### Accuracy
- Definition: Data correctly represents real-world value
- Measurement: Manual verification against source documents
- Target: 99.9% accuracy for financial data

#### Completeness
- Definition: All required fields populated
- Measurement: NOT NULL constraints compliance
- Target: 100% for required fields

#### Consistency
- Definition: Data is uniform across systems
- Measurement: Foreign key constraint violations
- Target: Zero referential integrity violations

#### Timeliness
- Definition: Data is up-to-date and available when needed
- Measurement: Lag between event and data availability
- Target: Near real-time (< 5 minutes)

#### Validity
- Definition: Data conforms to business rules
- Measurement: Check constraint violations
- Target: Zero invalid data entries

#### Uniqueness
- Definition: No duplicate records exist
- Measurement: Primary key violations
- Target: Zero duplicates

---

### 2.4 Information Architecture

#### Data Domains

**Domain 1: Contract Management**
- Entities: MasterContract, Contract
- Owner: Legal & Underwriting
- Quality Steward: Contract Administrator

**Domain 2: Batch & Coverage**
- Entities: Batch, Debtor, Record
- Owner: Operations
- Quality Steward: Batch Processing Team

**Domain 3: Financial Management**
- Entities: Nota, Payment, Reconciliation, DebitCreditNote
- Owner: Finance
- Quality Steward: Finance Controller

**Domain 4: Claims Management**
- Entities: Claim, Subrogation
- Owner: Claims Department
- Quality Steward: Claims Adjuster

**Domain 5: System Administration**
- Entities: SystemConfig, SlaRule, EmailTemplate, Notification
- Owner: IT Operations
- Quality Steward: System Administrator

---

## 3. DATA MODELING (UPDATED)

### 3.1 Updated Entity Relationships

#### Key Update 1: Claim/Subrogation Reference

**Previous:** Claim references Debtor via debtor_id (cover_id)
**Updated:** Claim references Debtor via **nomor_polis** (policy number)

```sql
-- Updated Claim Table
ALTER TABLE Claim 
  ADD COLUMN nomor_polis VARCHAR(50) NOT NULL COMMENT 'Policy number (FK to Debtor)',
  ADD INDEX idx_claim_policy (nomor_polis);

-- Foreign key relationship
ALTER TABLE Claim
  ADD CONSTRAINT fk_claim_debtor_policy 
  FOREIGN KEY (nomor_polis) 
  REFERENCES Debtor(nomor_polis) 
  ON DELETE RESTRICT;

-- Subrogation inherits policy reference from Claim
-- No change needed as it references Claim
```

**Rationale:**
- nomor_polis is the business key for debtor identification
- More intuitive for users (policy-based rather than system-generated ID)
- Aligns with business process (claims filed against policy numbers)

**Data Model Impact:**
```
Debtor (nomor_polis) ←──── Claim (nomor_polis)
                              ↓
                          Subrogation (claim_id)
```

---

#### Key Update 2: Premium Payment Offset with Claims

**Business Rule:** Pembayaran premi bulan ini akan dikurangi dengan klaim bulan sebelumnya

**Implementation:**

```sql
-- Add claim offset tracking to Nota
ALTER TABLE Nota
  ADD COLUMN claim_offset_amount DECIMAL(18,2) DEFAULT 0 
    COMMENT 'Claim amount offset from previous month',
  ADD COLUMN claim_offset_period VARCHAR(7) 
    COMMENT 'Period of claim offset (YYYY-MM)',
  ADD COLUMN net_payable_amount DECIMAL(18,2) 
    COMMENT 'Amount after claim offset = amount - claim_offset_amount';

-- Calculation logic
CREATE TRIGGER trg_nota_calculate_net_payable
BEFORE INSERT ON Nota
FOR EACH ROW
BEGIN
  IF NEW.nota_type = 'Batch' THEN
    -- Get total claims from previous month
    SET @prev_month = DATE_FORMAT(DATE_SUB(STR_TO_DATE(NEW.period, '%Y-%m'), INTERVAL 1 MONTH), '%Y-%m');
    
    SELECT COALESCE(SUM(amount), 0) INTO @claim_amount
    FROM Nota
    WHERE nota_type = 'Claim'
      AND contract_id = NEW.contract_id
      AND DATE_FORMAT(issued_date, '%Y-%m') = @prev_month
      AND status IN ('Issued', 'Confirmed', 'Paid');
    
    SET NEW.claim_offset_amount = @claim_amount;
    SET NEW.claim_offset_period = @prev_month;
    SET NEW.net_payable_amount = NEW.amount - NEW.claim_offset_amount;
  ELSE
    SET NEW.net_payable_amount = NEW.amount;
  END IF;
END;
```

**Process Flow:**
```
Month N-1: Claims processed
  ├─ Claim Nota issued
  └─ Total claim amount = X

Month N: Premium Nota generated
  ├─ Gross Premium = Y
  ├─ Claim Offset = X (from Month N-1)
  └─ Net Payable = Y - X

Payment:
  ├─ BRINS pays: Net Payable (Y - X)
  └─ Reconciliation: Matches against net_payable_amount
```

**Example:**
```
December 2025: Total Claims = Rp 100,000,000
January 2026: Premium Nota
  - Gross Premium: Rp 500,000,000
  - Claim Offset: Rp 100,000,000
  - Net Payable: Rp 400,000,000
  
BRINS Payment: Rp 400,000,000 ✓ (matches net_payable_amount)
```

---

### 3.2 Updated Schema Additions

#### Debtor Table Updates
```sql
ALTER TABLE Debtor
  ADD COLUMN nomor_polis VARCHAR(50) NOT NULL 
    COMMENT 'Policy number - business key',
  ADD UNIQUE INDEX uk_debtor_policy (nomor_polis);
```

#### Nota Table Updates
```sql
ALTER TABLE Nota
  ADD COLUMN claim_offset_amount DECIMAL(18,2) DEFAULT 0,
  ADD COLUMN claim_offset_period VARCHAR(7),
  ADD COLUMN net_payable_amount DECIMAL(18,2),
  ADD INDEX idx_nota_period (period);
```

#### Payment Table Updates
```sql
ALTER TABLE Payment
  ADD COLUMN payment_for ENUM('Premium Net', 'Claim', 'Subrogation', 'DN/CN') 
    COMMENT 'Payment purpose',
  ADD COLUMN offset_applied BOOLEAN DEFAULT FALSE 
    COMMENT 'TRUE if claim offset was applied';
```

---

### 3.3 Updated Business Rules

**BR-001: Claim Reference by Policy**
- Claims MUST reference valid nomor_polis from Debtor table
- Policy must be in active coverage period
- Validation: DOL must be between tanggal_mulai_covering and tanggal_akhir_covering

**BR-002: Premium Payment Offset**
- Premium Nota net_payable_amount = amount - claim_offset_amount
- Claim offset calculated from previous month's approved claims
- Reconciliation matches against net_payable_amount, not gross amount
- If no claims in previous month, claim_offset_amount = 0

**BR-003: Offset Visibility**
- Nota document must show:
  - Gross Premium Amount
  - Less: Claim Offset (with reference to claim period)
  - Net Payable Amount
- Payment receipt references offset calculation

**BR-004: Multi-Month Offset**
- If claims span multiple months, each month's claims offset next month's premium
- No carryover of unused offset (offset only applies to immediate next month)

---

## 4. PROCESS MODELING

### 4.1 Master Contract Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│              MASTER CONTRACT AGREEMENT PROCESS                       │
└─────────────────────────────────────────────────────────────────────┘

Actors: BRINS, TUGURE
Duration: 5-15 business days
Frequency: Yearly + Ad-hoc (Addendum)

┌──────────┐
│  START   │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. BRINS Drafts Master Contract     │
│    - Define coverage terms          │
│    - Set rates & percentages        │
│    - Specify eligibility rules      │
│    Status: Draft                    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. BRINS Submits to TUGURE          │
│    - Upload contract document       │
│    - Status → Pending BRINS Ack     │
│    - Notification sent to TUGURE    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. BRINS Acknowledges               │
│    - BRINS reviews and confirms     │
│    - brins_acknowledged_by filled   │
│    - Status → Pending TUGURE Ack    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. TUGURE Reviews                   │
│    - Review terms & conditions      │
│    - Verify rates                   │
│    - Check eligibility rules        │
└────┬────────────────────────────────┘
     │
     ├─── Approved? ───┐
     │                 │
    YES               NO
     │                 │
     ▼                 ▼
┌──────────────┐  ┌──────────────────────────┐
│ 5A. Approve  │  │ 5B. Reject               │
│ - TUGURE ack │  │ - Provide rejection      │
│ - Status →   │  │   reason                 │
│   Active     │  │ - Status → Rejected      │
└──┬───────────┘  └────┬─────────────────────┘
   │                   │
   │                   ▼
   │              ┌─────────────────────────┐
   │              │ 6. BRINS Revises        │
   │              │ - Address rejection     │
   │              │ - Create new version    │
   │              │ - Version++             │
   │              │ - parent_contract_id set│
   │              └────┬────────────────────┘
   │                   │
   │                   └──────► Back to Step 2
   │
   ▼
┌─────────────────────────────────────┐
│ 7. Generate Contract Instance       │
│    - Create Contract record         │
│    - Copy terms from MasterContract │
│    - Set status = ACTIVE            │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 8. Addendum Process (if needed)     │
│    - Create new MasterContract      │
│    - Set parent_contract_id         │
│    - Version = parent.version + 1   │
│    - Repeat approval process        │
└────┬────────────────────────────────┘
     │
     ▼
┌──────────┐
│   END    │
└──────────┘

Business Rules:
- Two-level acknowledgement required (BRINS → TUGURE)
- Rejection loops back to BRINS for revision
- Addendum creates new version with parent linkage
- Only one ACTIVE contract per credit_type
- Contract expires automatically on end_date
```

**State Machine:**
```
Draft → Pending BRINS Ack → Pending TUGURE Ack → Active
                                      ↓
                                  Rejected → (revision) → Draft
```

---

### 4.2 Batch & Nota Premium Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│            BATCH SUBMISSION & NOTA GENERATION PROCESS                │
└─────────────────────────────────────────────────────────────────────┘

Actors: BSM (Broker), BRINS, TUGURE, System
Duration: 1 month (for 3 batches collection)
Frequency: Monthly

┌──────────┐
│  START   │  ◄─── Month begins
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. BSM Sends Debtor Data            │
│    - Batch of debtors (CSV/Excel)   │
│    - Send to BRINS                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. BRINS Uploads Batch              │
│    Actor: BRINS Operations          │
│    System Actions:                  │
│    - Create Batch record            │
│    - Parse debtor data              │
│    - Create Debtor records          │
│    - Status: Uploaded               │
│    - Batch count for month++        │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. System Validates Batch           │
│    Validations:                     │
│    - Data format checks             │
│    - Required fields present        │
│    - Data type validation           │
│    - Duplicate detection            │
│    If valid → Status: Validated     │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. BRINS Reviews Batch              │
│    Actor: BRINS Reviewer            │
│    Actions:                         │
│    - Verify debtor information      │
│    - Check completeness             │
│    - Validate against contract      │
│    If OK → Status: Matched          │
└────┬────────────────────────────────┘
     │
     ├─── Is this Batch #3? ───┐
     │                          │
    NO                         YES
     │                          │
     │                          ▼
     │              ┌─────────────────────────────────┐
     │              │ 5. System Checks Month Complete │
     │              │    - Count batches for month    │
     │              │    - If count = 3:              │
     │              │      • Generate monthly Bordero │
     │              │      • Generate Nota            │
     │              │      • Status: Approved         │
     │              └────┬────────────────────────────┘
     │                   │
     │                   ▼
     │              ┌─────────────────────────────────┐
     │              │ 6. Generate Nota (End of Month) │
     │              │    Actor: System (automated)    │
     │              │    Nota Components:             │
     │              │    - nota_type = 'Batch'        │
     │              │    - reference_id = 3 batch_ids │
     │              │    - amount = SUM(final_premium)│
     │              │    - Check previous month claims│
     │              │    - Calculate claim_offset     │
     │              │    - net_payable = amount -     │
     │              │      claim_offset               │
     │              │    - Status: Draft              │
     │              └────┬────────────────────────────┘
     │                   │
     │                   ▼
     │              ┌─────────────────────────────────┐
     │              │ 7. Send Nota to TUGURE & BRINS  │
     │              │    Recipients:                  │
     │              │    - TUGURE Operations          │
     │              │    - BRINS Finance              │
     │              │    Nota Status: Issued          │
     │              │    Nota.is_immutable = TRUE     │
     │              └────┬────────────────────────────┘
     │                   │
     └───────────────────┤
                         │
                         ▼
┌─────────────────────────────────────┐
│ 8. TUGURE Reviews Batches           │
│    Actor: TUGURE Underwriter        │
│    For each Debtor:                 │
│    - Validate against MasterContract│
│    - Check kolektabilitas           │
│    - Check region                   │
│    - Verify premium calculation     │
└────┬────────────────────────────────┘
     │
     ├─── For Each Debtor ───┐
     │                        │
     ▼                        ▼
┌──────────────┐      ┌──────────────────┐
│ 9A. Approve  │      │ 9B. Reject/Note  │
│ - Status →   │      │ - Provide remark │
│   APPROVED   │      │ - Status →       │
│ - Create     │      │   REJECTED or    │
│   Record     │      │   CONDITIONAL    │
│   (Accepted) │      │ - Create Record  │
└──┬───────────┘      └────┬─────────────┘
   │                       │
   └───────┬───────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 10. System Updates Batch            │
│     For Batch:                      │
│     - Recalculate final_amounts     │
│     - final_exposure = SUM(approved)│
│     - final_premium = SUM(approved) │
│     - Check all debtors reviewed    │
│     - debtor_review_completed=TRUE  │
│     - batch_ready_for_nota=TRUE     │
└────┬────────────────────────────────┘
     │
     ├─── Has Revisions? ───┐
     │                       │
    NO                      YES
     │                       │
     │                       ▼
     │              ┌─────────────────────────────────┐
     │              │ 11. BRINS Revises Batch         │
     │              │     Actor: BRINS Operations     │
     │              │     - Address TUGURE remarks    │
     │              │     - Update debtor data        │
     │              │     - Re-upload batch           │
     │              │     - Batch.revision_count++    │
     │              └────┬────────────────────────────┘
     │                   │
     │                   ▼
     │              ┌─────────────────────────────────┐
     │              │ 12. Nota Follows Revision       │
     │              │     System Actions:             │
     │              │     - Recalculate Nota.amount   │
     │              │     - Update net_payable_amount │
     │              │     - Nota.version++            │
     │              │     - Notify TUGURE & BRINS     │
     │              └────┬────────────────────────────┘
     │                   │
     └───────────────────┼─────► Continue to Payment Process
                         │
                         ▼
┌─────────────────────────────────────┐
│ 13. Final Nota                      │
│     - All batches approved          │
│     - Nota status: Issued           │
│     - Amount locked (immutable)     │
│     - Ready for payment             │
└────┬────────────────────────────────┘
     │
     ▼
┌──────────┐
│   END    │ ───► Proceed to Payment Workflow
└──────────┘

Key Business Rules:
- Exactly 3 batches per month required for Nota generation
- Nota generated at end of month (after 3rd batch)
- Previous month's claims automatically offset current premium
- Nota amount is IMMUTABLE after status = 'Issued'
- Batch revisions trigger Nota recalculation
- All debtors must be reviewed (approved/rejected) before Nota finalized
```

**Batch State Machine:**
```
Uploaded → Validated → Matched → Approved → Nota Issued → Branch Confirmed → Paid → Closed
                                     ↓
                                 Rejected → (revision) → Uploaded
```

---

### 4.3 Premium Payment Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PREMIUM PAYMENT PROCESS                           │
└─────────────────────────────────────────────────────────────────────┘

Actors: BRINS Finance, TUGURE Finance, System
Duration: 7-15 business days
Frequency: Monthly (after Nota issued)

┌──────────┐
│  START   │  ◄─── After Nota Issued
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. Nota Final Issued                │
│    Prerequisites:                   │
│    - All 3 batches approved         │
│    - Nota status = Issued           │
│    - Nota.is_immutable = TRUE       │
│    Nota Details:                    │
│    - Gross Premium (amount)         │
│    - Claim Offset (claim_offset_amt)│
│    - Net Payable (net_payable_amt)  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. BRINS Finance Reviews Nota       │
│    Actor: BRINS Finance Team        │
│    Review:                          │
│    - Verify gross premium           │
│    - Check claim offset calculation │
│    - Validate net payable amount    │
│    - Check previous month claims    │
│    Action: Confirm Nota             │
│    Nota Status → Confirmed          │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. BRINS Creates Payment Intent     │
│    Actor: BRINS Finance             │
│    PaymentIntent record:            │
│    - invoice_id = nota_number       │
│    - planned_amount = net_payable   │
│    - planned_date                   │
│    - payment_type = FULL/PARTIAL    │
│    - status = DRAFT                 │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. BRINS Submits Payment Intent     │
│    - PaymentIntent status → SUBMITTED│
│    - Notification to TUGURE         │
│    - Await approval if required     │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 5. BRINS Executes Payment           │
│    Actor: BRINS Finance             │
│    Payment Details:                 │
│    - Amount = net_payable_amount    │
│    - Transfer to TUGURE account     │
│    - Bank reference generated       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 6. System Receives Payment          │
│    Actor: System (auto)             │
│    Payment record created:          │
│    - payment_ref = bank_ref         │
│    - invoice_id = nota_number       │
│    - amount = actual_paid           │
│    - payment_date                   │
│    - match_status = RECEIVED        │
│    - is_actual_payment = TRUE       │
│    - offset_applied = TRUE          │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 7. TUGURE Verifies Payment          │
│    Actor: TUGURE Finance            │
│    Verification:                    │
│    - Check bank statement           │
│    - Verify payment amount          │
│    - Confirm payment reference      │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 8. System Auto-Reconciliation       │
│    Actor: System (auto)             │
│    Process:                         │
│    - Match Payment to Nota          │
│    - Compare amounts                │
│    - Update Nota.total_actual_paid  │
│    - Calculate difference           │
│    Expected: actual = net_payable   │
└────┬────────────────────────────────┘
     │
     ├─── Payment Matches? ───┐
     │                         │
    YES                       NO
     │                         │
     ▼                         ▼
┌──────────────┐      ┌──────────────────────────┐
│ 9A. Perfect  │      │ 9B. Exception Detected   │
│  Match       │      │  System Actions:         │
│ - match_     │      │  - Calculate variance    │
│   status →   │      │  - exception_type:       │
│   MATCHED    │      │    • UNDER (underpayment)│
│ - recon_     │      │    • OVER (overpayment)  │
│   status →   │      │    • PARTIAL             │
│   MATCHED    │      │  - match_status →        │
│ - Nota       │      │    PARTIALLY_MATCHED     │
│   status →   │      │  - recon_status →        │
│   Paid       │      │    EXCEPTION             │
└──┬───────────┘      └────┬─────────────────────┘
   │                       │
   │                       ▼
   │              ┌──────────────────────────────┐
   │              │ 10. Exception Notification    │
   │              │     Recipients:               │
   │              │     - BRINS Finance           │
   │              │     - TUGURE Finance          │
   │              │     Notification Type:        │
   │              │     - ACTION_REQUIRED         │
   │              │     Details:                  │
   │              │     - Expected vs Actual      │
   │              │     - Variance amount         │
   │              │     - Suggested action        │
   │              └────┬─────────────────────────┘
   │                   │
   │                   ▼
   │              ┌──────────────────────────────┐
   │              │ 11. BRINS Confirms Exception  │
   │              │     Actor: BRINS Finance      │
   │              │     Actions:                  │
   │              │     - Review variance         │
   │              │     - Verify payment record   │
   │              │     - Acknowledge exception   │
   │              │     - Provide explanation     │
   │              └────┬─────────────────────────┘
   │                   │
   │                   ▼
   │              ┌──────────────────────────────┐
   │              │ 12. TUGURE Generates DN/CN    │
   │              │     Actor: TUGURE Finance     │
   │              │     If UNDERPAYMENT:          │
   │              │     - Create Debit Note       │
   │              │     - adjustment_amount > 0   │
   │              │     - reason_code:            │
   │              │       Payment Difference      │
   │              │     If OVERPAYMENT:           │
   │              │     - Create Credit Note      │
   │              │     - adjustment_amount < 0   │
   │              │     DN/CN Status: Draft       │
   │              └────┬─────────────────────────┘
   │                   │
   │                   ▼
   │              ┌──────────────────────────────┐
   │              │ 13. DN/CN Approval Workflow   │
   │              │     Flow:                     │
   │              │     Draft → Under Review →    │
   │              │     Approved                  │
   │              │     Approver: TUGURE Supervisor│
   │              └────┬─────────────────────────┘
   │                   │
   │                   ▼
   │              ┌──────────────────────────────┐
   │              │ 14. BRINS Verifies DN/CN      │
   │              │     Actor: BRINS Finance      │
   │              │     Verification:             │
   │              │     - Review adjustment       │
   │              │     - Verify calculation      │
   │              │     - Acknowledge DN/CN       │
   │              │     DN/CN Status → Acknowledged│
   │              └────┬─────────────────────────┘
   │                   │
   │                   ▼
   │              ┌──────────────────────────────┐
   │              │ 15. System Updates Nota       │
   │              │     System Actions:           │
   │              │     - Update Nota balance     │
   │              │     - Adjust reconciliation   │
   │              │     - recon_status → FINAL    │
   │              └────┬─────────────────────────┘
   │                   │
   └───────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 16. Final Reconciliation            │
│     - All payments matched          │
│     - DN/CN processed (if any)      │
│     - Nota.status → Paid            │
│     - Nota.recon_status → FINAL     │
│     - Batch.status → Paid           │
└────┬────────────────────────────────┘
     │
     ▼
┌──────────┐
│   END    │
└──────────┘

Key Business Rules:
- Payment amount should equal net_payable_amount (after claim offset)
- Claim offset from previous month applied automatically
- Exception handling required for any variance
- DN for underpayment, CN for overpayment
- BRINS must acknowledge all DN/CN
- Reconciliation not final until all exceptions resolved
```

**Payment State Machine:**
```
RECEIVED → MATCHED → Nota.Paid → FINAL
    ↓
PARTIALLY_MATCHED → Exception → DN/CN → Acknowledged → FINAL
    ↓
UNMATCHED → Investigation → Resolution
```

---

### 4.4 Claim Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLAIM PROCESS                                │
└─────────────────────────────────────────────────────────────────────┘

Actors: BRINS Claims, TUGURE Claims, System
Duration: 15-30 business days
Frequency: Ad-hoc (as claims occur)

┌──────────┐
│  START   │  ◄─── Loss Event Occurs
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. BRINS Receives Claim from Debtor │
│    Actor: BRINS Claims Department   │
│    Information Received:            │
│    - Loss details                   │
│    - Policy number (nomor_polis)    │
│    - Claim amount                   │
│    - Date of Loss (DOL)             │
│    - Supporting documents           │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. BRINS Prepares Claim             │
│    Actor: BRINS Claims              │
│    Actions:                         │
│    - Verify policy exists           │
│    - Check coverage period          │
│    - Calculate claim amount         │
│    - Collect documentation          │
│    - Link to Batch (if available)   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. BRINS Uploads Claim              │
│    Actor: BRINS Claims              │
│    System Actions:                  │
│    - Create Claim record            │
│    - Reference: nomor_polis         │
│    - Link to Debtor via policy      │
│    - Status: Draft                  │
│    - version_no = 1                 │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. System Validates Claim           │
│    Actor: System (auto)             │
│    Validations:                     │
│    ✓ Policy exists in Debtor        │
│    ✓ Coverage period valid          │
│    ✓ DOL within coverage dates      │
│    ✓ Claim <= max_coverage          │
│    ✓ Claim <= plafon                │
│    ✓ Kolektabilitas allowed         │
│    ✓ BDO Premium check              │
│    If ALL pass → Status: Checked    │
│    If FAIL → Status: Draft (errors) │
└────┬────────────────────────────────┘
     │
     ├─── Validation OK? ───┐
     │                       │
    YES                     NO
     │                       │
     ▼                       ▼
┌──────────────┐      ┌────────────────────┐
│ 5. Send to   │      │ 5B. Return to      │
│    TUGURE    │      │     BRINS          │
│ - Status →   │      │ - Show errors      │
│   Checked    │      │ - Request fix      │
│ - Notify     │      │ - Status: Draft    │
│   TUGURE     │      └────┬───────────────┘
└──┬───────────┘           │
   │                       └──► Back to Step 2
   │
   ▼
┌─────────────────────────────────────┐
│ 6. TUGURE Reviews Claim             │
│    Actor: TUGURE Claims Adjuster    │
│    Review Process:                  │
│    - Verify against MasterContract  │
│    - Check documentation            │
│    - Validate claim amount          │
│    - Review loss circumstances      │
│    - Calculate TUGURE share:        │
│      share_tugure_amount =          │
│      nilai_klaim ×                  │
│      share_tugure_percentage        │
└────┬────────────────────────────────┘
     │
     ├─── Decision ───┐
     │                │
  APPROVE          REJECT
     │                │
     ▼                ▼
┌──────────────┐  ┌──────────────────────────┐
│ 7A. Approve  │  │ 7B. Reject               │
│ - Status →   │  │ - Provide rejection      │
│   Doc        │  │   reason                 │
│   Verified   │  │ - Status → Draft         │
│ - Calculate  │  │ - Notify BRINS           │
│   TUGURE     │  └────┬─────────────────────┘
│   share      │       │
└──┬───────────┘       ▼
   │              ┌──────────────────────────┐
   │              │ 8. BRINS Revises Claim   │
   │              │    - Address issues      │
   │              │    - Update claim data   │
   │              │    - version_no++        │
   │              │    - Re-upload           │
   │              └────┬─────────────────────┘
   │                   │
   │                   └──► Back to Step 4
   │
   ▼
┌─────────────────────────────────────┐
│ 9. Generate Claim Nota              │
│    Actor: System (auto)             │
│    Nota Details:                    │
│    - nota_type = 'Claim'            │
│    - reference_id = claim_no        │
│    - amount = share_tugure_amount   │
│    - No claim offset for Claim Nota │
│    - Status: Draft                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 10. Issue Claim Nota                │
│     - Nota Status → Issued          │
│     - Nota.is_immutable = TRUE      │
│     - Claim Status → Invoiced       │
│     - Send to BRINS                 │
│     - Notification sent             │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 11. BRINS Confirms Nota             │
│     Actor: BRINS Finance            │
│     - Review claim nota             │
│     - Verify amount                 │
│     - Nota Status → Confirmed       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 12. TUGURE Processes Payment        │
│     Actor: TUGURE Finance           │
│     Payment Details:                │
│     - Amount = share_tugure_amount  │
│     - Transfer to BRINS account     │
│     - Generate payment reference    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 13. System Records Payment          │
│     Payment record:                 │
│     - payment_ref                   │
│     - invoice_id = nota_number      │
│     - amount                        │
│     - payment_date                  │
│     - match_status = RECEIVED       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 14. BRINS Verifies Payment          │
│     Actor: BRINS Finance            │
│     - Check bank statement          │
│     - Verify amount received        │
│     - match_status → MATCHED        │
└────┬────────────────────────────────┘
     │
     ├─── Payment Matches? ───┐
     │                         │
    YES                       NO
     │                         │
     ▼                         ▼
┌──────────────┐      ┌──────────────────────────┐
│ 15A. Mark    │      │ 15B. Exception Handling  │
│  Paid        │      │  - Calculate variance    │
│ - Claim      │      │  - Notify BRINS & TUGURE │
│   status →   │      │  - BRINS confirms        │
│   Paid       │      │  - TUGURE generates DN/CN│
│ - Nota       │      │  - BRINS verifies DN/CN  │
│   status →   │      │  - System updates        │
│   Paid       │      │  - Final reconciliation  │
└──┬───────────┘      └────┬─────────────────────┘
   │                       │
   └───────────┬───────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 16. Claim Used for Premium Offset   │
│     System Actions:                 │
│     - Record claim amount           │
│     - Mark for next month offset    │
│     - When next Premium Nota:       │
│       claim_offset_amount += this   │
│     - Claim month saved in          │
│       claim_offset_period           │
└────┬────────────────────────────────┘
     │
     ▼
┌──────────┐
│   END    │
└──────────┘

Key Business Rules:
- Claim MUST reference valid nomor_polis
- System validates claim against MasterContract automatically
- TUGURE calculates share_tugure_amount based on contract percentage
- Claim Nota does NOT have claim offset (only Premium Nota does)
- Approved claims are used for next month's Premium Nota offset
- Exception handling same as Premium Payment (DN/CN process)
- Claim amount cannot exceed max_coverage from MasterContract
```

**Claim State Machine:**
```
Draft → Checked → Doc Verified → Invoiced → Paid
  ↓
Rejected → (revision) → Draft
```

---

### 4.5 Subrogation Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SUBROGATION PROCESS                             │
└─────────────────────────────────────────────────────────────────────┘

Actors: BRINS Claims, TUGURE Claims, System
Duration: 30-90 days
Frequency: Ad-hoc (after claim paid, if recovery possible)

┌──────────┐
│  START   │  ◄─── After Claim Paid
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. Recovery Opportunity Identified  │
│    Actor: BRINS Claims              │
│    Scenarios:                       │
│    - Third party liable for loss    │
│    - Collateral liquidation         │
│    - Debtor payment recovery        │
│    Prerequisite:                    │
│    - Related Claim must be paid     │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. BRINS Prepares Subrogation       │
│    Actor: BRINS Claims/Legal        │
│    Information:                     │
│    - Reference claim_id (required)  │
│    - Recovery amount                │
│    - Recovery source                │
│    - Recovery date                  │
│    - Supporting documents           │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. BRINS Uploads Subrogation        │
│    Actor: BRINS Claims              │
│    System Actions:                  │
│    - Create Subrogation record      │
│    - claim_id (FK) required         │
│    - Inherit debtor_id from Claim   │
│    - Inherit nomor_polis from Claim │
│    - Status: Draft                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. System Validates Subrogation     │
│    Actor: System (auto)             │
│    Validations:                     │
│    ✓ Claim exists and status=Paid   │
│    ✓ Recovery amount <= claim amount│
│    ✓ No duplicate subrogation       │
│    ✓ Recovery date >= claim DOL     │
│    ✓ Supporting docs uploaded       │
│    If ALL pass → Continue           │
│    If FAIL → Return with errors     │
└────┬────────────────────────────────┘
     │
     ├─── Validation OK? ───┐
     │                       │
    YES                     NO
     │                       │
     ▼                       ▼
┌──────────────┐      ┌────────────────────┐
│ 5. Send to   │      │ 5B. Return to      │
│    TUGURE    │      │     BRINS          │
│ - Notify     │      │ - Show errors      │
│   TUGURE     │      │ - Request fix      │
└──┬───────────┘      └────┬───────────────┘
   │                       │
   │                       └──► Back to Step 2
   │
   ▼
┌─────────────────────────────────────┐
│ 6. TUGURE Reviews Subrogation       │
│    Actor: TUGURE Claims             │
│    Review Process:                  │
│    - Verify original claim          │
│    - Check recovery amount          │
│    - Review recovery source         │
│    - Validate documentation         │
│    - Verify legal basis             │
└────┬────────────────────────────────┘
     │
     ├─── Decision ───┐
     │                │
  APPROVE          REJECT
     │                │
     ▼                ▼
┌──────────────┐  ┌──────────────────────────┐
│ 7A. Approve  │  │ 7B. Reject               │
│ - Status →   │  │ - Provide rejection      │
│   Invoiced   │  │   reason                 │
│ - Calculate  │  │ - Status → Draft         │
│   TUGURE     │  │ - Notify BRINS           │
│   share      │  └────┬─────────────────────┘
└──┬───────────┘       │
   │                   ▼
   │              ┌──────────────────────────┐
   │              │ 8. BRINS Revises         │
   │              │    - Address issues      │
   │              │    - Update data         │
   │              │    - Re-upload           │
   │              └────┬─────────────────────┘
   │                   │
   │                   └──► Back to Step 4
   │
   ▼
┌─────────────────────────────────────┐
│ 9. Generate Subrogation Nota        │
│    Actor: System (auto)             │
│    Nota Details:                    │
│    - nota_type = 'Subrogation'      │
│    - reference_id = subrogation_id  │
│    - amount = recovery_amount ×     │
│      share_tugure_percentage        │
│    - Direction: TUGURE receives from│
│      BRINS (opposite of Claim)      │
│    - Status: Draft                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 10. Issue Subrogation Nota          │
│     - Nota Status → Issued          │
│     - Nota.is_immutable = TRUE      │
│     - Subrogation Status → Invoiced │
│     - Send to BRINS                 │
│     - Notification sent             │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 11. BRINS Confirms Nota             │
│     Actor: BRINS Finance            │
│     - Review subrogation nota       │
│     - Verify recovery amount        │
│     - Nota Status → Confirmed       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 12. BRINS Pays Recovery Share       │
│     Actor: BRINS Finance            │
│     Payment Details:                │
│     - Amount = TUGURE share of      │
│       recovery                      │
│     - Transfer to TUGURE account    │
│     - Generate payment reference    │
│     Note: BRINS pays TUGURE         │
│     (opposite direction of claim)   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 13. System Records Payment          │
│     Payment record:                 │
│     - payment_ref                   │
│     - invoice_id = nota_number      │
│     - amount                        │
│     - payment_date                  │
│     - match_status = RECEIVED       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 14. TUGURE Verifies Payment         │
│     Actor: TUGURE Finance           │
│     - Check bank statement          │
│     - Verify amount received        │
│     - match_status → MATCHED        │
└────┬────────────────────────────────┘
     │
     ├─── Payment Matches? ───┐
     │                         │
    YES                       NO
     │                         │
     ▼                         ▼
┌──────────────┐      ┌──────────────────────────┐
│ 15A. Mark    │      │ 15B. Exception Handling  │
│  Paid        │      │  - Calculate variance    │
│ - Subrog     │      │  - Notify BRINS & TUGURE │
│   status →   │      │  - BRINS confirms        │
│   Paid/      │      │  - TUGURE generates DN/CN│
│   Closed     │      │  - BRINS verifies DN/CN  │
│ - Nota       │      │  - System updates        │
│   status →   │      │  - Final reconciliation  │
│   Paid       │      │                          │
└──┬───────────┘      └────┬─────────────────────┘
   │                       │
   └───────────┬───────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 16. Close Subrogation               │
│     - Subrogation status: Paid/Close│
│     - Nota fully reconciled         │
│     - Update related Claim record   │
│     - Audit log entry               │
└────┬────────────────────────────────┘
     │
     ▼
┌──────────┐
│   END    │
└──────────┘

Key Business Rules:
- Subrogation MUST reference valid paid Claim
- Inherits policy reference from Claim
- Recovery amount cannot exceed original claim amount
- Payment direction: BRINS → TUGURE (opposite of Claim)
- TUGURE receives their share of recovery
- Exception handling same as other payment flows (DN/CN)
- Multiple subrogations allowed per claim (partial recoveries)
```

**Subrogation State Machine:**
```
Draft → Invoiced → Paid / Closed
  ↓
Rejected → (revision) → Draft
```

---

## 5. INTERACTION MODELING

### 5.1 System Context Diagram

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    │    REINSURANCE MANAGEMENT        │
                    │          SYSTEM                  │
                    │      (BRINS-TUGURE)              │
                    │                                  │
                    └──────────────────────────────────┘
                              ▲         ▲
                              │         │
        ┌─────────────────────┼─────────┼──────────────────────┐
        │                     │         │                      │
        ▼                     │         │                      ▼
┌───────────────┐     ┌──────┴─────────┴──────┐     ┌───────────────┐
│               │     │                        │     │               │
│     BSM       │────►│      BRINS Users       │     │ TUGURE Users  │
│   (Broker)    │     │                        │     │               │
│               │     │  • Operations          │     │  • Underwriter│
└───────────────┘     │  • Claims              │     │  • Claims     │
                      │  • Finance             │     │  • Finance    │
                      │  • Admin               │     │  • Admin      │
                      └────────────────────────┘     └───────────────┘
                              │         │
                              │         │
                              ▼         ▼
                    ┌──────────────────────────────────┐
                    │                                  │
                    │    EXTERNAL SYSTEMS              │
                    │                                  │
                    │  • Bank Payment Gateway          │
                    │  • Email Service (SMTP)          │
                    │  • WhatsApp Gateway              │
                    │  • Document Storage (S3)         │
                    │  • Audit Log Service             │
                    │                                  │
                    └──────────────────────────────────┘
```

### 5.2 Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USE CASE DIAGRAM                              │
└─────────────────────────────────────────────────────────────────────┘

     BSM (Broker)
         │
         │
         ▼
     ┌────────────────────────┐
     │ Submit Debtor Data     │
     │ (to BRINS)             │
     └────────────────────────┘


     BRINS Operations
         │
         ├────► ┌──────────────────────────┐
         │      │ Upload Batch             │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Review Batch             │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Revise Batch             │
                └──────────────────────────┘


     BRINS Claims
         │
         ├────► ┌──────────────────────────┐
         │      │ Upload Claim             │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Upload Subrogation       │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Revise Claim/Subrogation │
                └──────────────────────────┘


     BRINS Finance
         │
         ├────► ┌──────────────────────────┐
         │      │ Review Nota              │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Create Payment Intent    │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Execute Payment          │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Confirm Exception        │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Verify DN/CN             │
                └──────────────────────────┘


     TUGURE Underwriter
         │
         ├────► ┌──────────────────────────┐
         │      │ Review Batch/Debtors     │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Approve/Reject Debtor    │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Provide Remarks          │
                └──────────────────────────┘


     TUGURE Claims
         │
         ├────► ┌──────────────────────────┐
         │      │ Review Claim             │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Review Subrogation       │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Approve/Reject Claim     │
                └──────────────────────────┘


     TUGURE Finance
         │
         ├────► ┌──────────────────────────┐
         │      │ Verify Payment           │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Process Claim Payment    │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Generate DN/CN           │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Reconcile Payments       │
                └──────────────────────────┘


     System (Automated)
         │
         ├────► ┌──────────────────────────┐
         │      │ Validate Data            │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Generate Nota            │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Calculate Claim Offset   │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Auto-match Payments      │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Trigger Notifications    │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ Create Audit Logs        │
                └──────────────────────────┘


     Admin
         │
         ├────► ┌──────────────────────────┐
         │      │ Manage MasterContract    │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Configure System         │
         │      └──────────────────────────┘
         │
         ├────► ┌──────────────────────────┐
         │      │ Manage SLA Rules         │
         │      └──────────────────────────┘
         │
         └────► ┌──────────────────────────┐
                │ View Audit Logs          │
                └──────────────────────────┘
```

---

### 5.3 Sequence Diagram - Premium Payment with Offset

```
SEQUENCE: Premium Payment with Claim Offset

Actor: System, BRINS Finance, TUGURE Finance

┌────────┐       ┌────────┐       ┌──────────────┐       ┌──────────────┐
│ System │       │ BRINS  │       │   TUGURE     │       │   Nota       │
│        │       │Finance │       │  Finance     │       │  Table       │
└───┬────┘       └───┬────┘       └──────┬───────┘       └──────┬───────┘
    │                │                   │                      │
    │ ═══ End of Month: Generate Nota ═══════════════════════  │
    │                │                   │                      │
    ├────────────────────────────────────────────────────────► │
    │ 1. Check previous month claims                           │
    │    SELECT SUM(amount) FROM Nota                          │
    │    WHERE nota_type='Claim'                               │
    │    AND period='YYYY-MM-prev'                             │
    │ ◄────────────────────────────────────────────────────────┤
    │ claim_offset_amount = 100,000,000                        │
    │                │                   │                      │
    ├────────────────────────────────────────────────────────► │
    │ 2. Create Nota (Premium)                                 │
    │    - amount = 500,000,000 (gross premium)                │
    │    - claim_offset_amount = 100,000,000                   │
    │    - net_payable_amount = 400,000,000                    │
    │    - status = 'Draft'                                    │
    │ ◄────────────────────────────────────────────────────────┤
    │ Nota created                                             │
    │                │                   │                      │
    ├───────────────►│                   │                      │
    │ 3. Notify: Nota Generated                                │
    │    Email: "Premium Nota ready"                           │
    │    - Gross: Rp 500,000,000                               │
    │    - Offset: Rp 100,000,000                              │
    │    - Net Payable: Rp 400,000,000                         │
    │ ◄──────────────┤                   │                      │
    │                │                   │                      │
    │                │ 4. Review Nota    │                      │
    │                ├──────────────────►│                      │
    │                │   Send Nota       │                      │
    │                │ ◄──────────────────┤                      │
    │                │   Approve         │                      │
    │                │                   │                      │
    ├────────────────────────────────────────────────────────► │
    │ 5. Update Nota                                           │
    │    - status = 'Issued'                                   │
    │    - is_immutable = TRUE                                 │
    │ ◄────────────────────────────────────────────────────────┤
    │                │                   │                      │
    │                │ 6. Create Payment Intent                 │
    │                │    planned_amount = 400,000,000          │
    │                │ ──────────────────────────────────────► │
    │                │                   │    Nota confirmed    │
    │                │                   │                      │
    │                │ 7. Execute Bank Transfer                 │
    │                │    Amount: Rp 400,000,000                │
    │                │    Reference: "Nota-2026-01-001"         │
    │                ├──────────────────►│                      │
    │                │   Bank Transfer   │                      │
    │                │                   │                      │
    │                │                   │ 8. Verify Payment    │
    │                │                   │    Check bank stmt   │
    │                │                   │    Amount: Rp 400M   │
    │                │                   ├─────────────────────►│
    │                │                   │  Record Payment      │
    │                │                   │ ◄─────────────────────┤
    │                │                   │                      │
    ├────────────────────────────────────────────────────────► │
    │ 9. Auto-reconciliation                                   │
    │    - Expected: net_payable_amount = 400,000,000          │
    │    - Actual: payment.amount = 400,000,000                │
    │    - Match: TRUE ✓                                       │
    │    - Update:                                             │
    │      • total_actual_paid = 400,000,000                   │
    │      • reconciliation_status = 'MATCHED'                 │
    │      • status = 'Paid'                                   │
    │ ◄────────────────────────────────────────────────────────┤
    │                │                   │                      │
    ├───────────────►│                   │                      │
    │ 10. Notify: Payment Matched                              │
    │     "Premium paid successfully"                          │
    │ ◄──────────────┤                   │                      │
    │                │                   │                      │
    ├───────────────────────────────────►│                      │
    │ 11. Notify: Payment Received                             │
    │     "Premium payment confirmed"                          │
    │ ◄───────────────────────────────────┤                      │
    │                │                   │                      │
    │                                                           │
    ▼                ▼                   ▼                      ▼
  [END]            [END]               [END]                 [END]
```

---

### 5.4 Actor-System Interaction Matrix

| Actor | Create | Read | Update | Delete | Approve | Key Interactions |
|-------|--------|------|--------|--------|---------|------------------|
| **BSM (Broker)** | - | - | - | - | - | • Submit debtor data to BRINS |
| **BRINS Operations** | Batch, Debtor | Batch, Debtor, Nota | Batch, Debtor | - | - | • Upload batch<br>• Review batch<br>• Revise batch |
| **BRINS Claims** | Claim, Subrogation | Claim, Subrogation | Claim, Subrogation | - | - | • Upload claims<br>• Revise claims<br>• Upload subrogation |
| **BRINS Finance** | PaymentIntent | Nota, Payment, DN/CN | Nota | - | Acknowledge | • Review nota<br>• Execute payment<br>• Verify DN/CN<br>• Confirm exceptions |
| **TUGURE Underwriter** | Record | Batch, Debtor, MasterContract | Record | - | Approve/Reject | • Review debtors<br>• Approve/reject coverage<br>• Provide remarks |
| **TUGURE Claims** | - | Claim, Subrogation | Claim, Subrogation | - | Approve/Reject | • Review claims<br>• Review subrogation<br>• Approve/reject |
| **TUGURE Finance** | Nota, DN/CN, Payment | Nota, Payment, Reconciliation | Payment, DN/CN | - | Approve | • Verify payments<br>• Process claim payments<br>• Generate DN/CN<br>• Reconcile |
| **System (Automated)** | Nota, Notification, AuditLog, Reconciliation | All | Nota, Payment, Reconciliation | - | - | • Validate data<br>• Generate nota<br>• Calculate offsets<br>• Auto-match payments<br>• Trigger notifications |
| **Admin** | MasterContract, SystemConfig, SlaRule | All | SystemConfig, SlaRule, EmailTemplate | MasterContract (inactive) | Approve contracts | • Manage master data<br>• Configure system<br>• View audit logs<br>• Manage SLA rules |

---

## APPENDIX: KEY SYSTEM BEHAVIORS

### A. Automatic Triggers

**Trigger 1: Batch Finalization**
- Event: Record status changed to 'Accepted' or 'Rejected'
- Action: Recalculate Batch.final_exposure_amount and final_premium_amount
- Check: All debtors reviewed? Set debtor_review_completed = TRUE

**Trigger 2: Nota Generation**
- Event: 3rd batch of month approved
- Action: 
  - Create Bordero for month
  - Calculate previous month's claim total
  - Create Nota with claim offset
  - Set net_payable_amount
  - Notify BRINS Finance and TUGURE

**Trigger 3: Payment Matching**
- Event: Payment record created
- Action:
  - Match to Nota via invoice_id
  - Update Nota.total_actual_paid
  - Calculate reconciliation_status
  - If variance detected → trigger exception notification

**Trigger 4: SLA Monitoring**
- Event: Scheduled (hourly)
- Action:
  - Check all active SlaRules
  - Evaluate trigger conditions
  - Generate notifications if thresholds breached
  - Update trigger_count and last_triggered

**Trigger 5: Audit Logging**
- Event: Critical entity status change
- Action: Automatically create AuditLog entry with before/after values

---

**END OF COMPREHENSIVE MODELING DOCUMENT**
