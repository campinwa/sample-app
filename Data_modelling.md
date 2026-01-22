# DATA MODELING DOCUMENT
## Reinsurance Management System (BRINS - TUGURE)

**Document Version:** 1.0  
**Date:** January 22, 2026  
**Prepared By:** Data Architecture Team

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [Conceptual Data Model](#2-conceptual-data-model)
3. [Logical Data Model](#3-logical-data-model)
4. [Physical Data Model](#4-physical-data-model)
5. [Normalization Analysis](#5-normalization-analysis)
6. [Business Rules](#6-business-rules)
7. [Data Dictionary](#7-data-dictionary)
8. [Indexing Strategy](#8-indexing-strategy)
9. [Data Volume Estimates](#9-data-volume-estimates)
10. [Performance Considerations](#10-performance-considerations)

---

## 1. INTRODUCTION

### 1.1 Purpose
This document provides comprehensive data modeling for the Reinsurance Management System that manages the relationship between BRINS (cedant) and TUGURE (reinsurer).

### 1.2 Scope
The data model covers:
- Contract and batch management
- Debtor/participant coverage tracking
- Premium calculation and billing (Nota)
- Payment processing and reconciliation
- Claims and subrogation management
- System configuration and monitoring

### 1.3 Stakeholders
- **BRINS**: Cedant, submits batches and claims
- **TUGURE**: Reinsurer, reviews and approves coverage
- **System Administrators**: Manage configurations and monitoring

---

## 2. CONCEPTUAL DATA MODEL

### 2.1 Major Subject Areas

#### Subject Area 1: CONTRACT MANAGEMENT
**Purpose:** Manage reinsurance contracts and master agreements

**Key Entities:**
- MasterContract
- Contract

**Business Function:**
- Define coverage terms and conditions
- Set premium rates and share percentages
- Establish eligibility criteria

#### Subject Area 2: BATCH & DEBTOR MANAGEMENT
**Purpose:** Process batch submissions and debtor coverage

**Key Entities:**
- Batch
- Debtor
- Record

**Business Function:**
- Submit monthly batches
- Review and approve debtors
- Track revision history

#### Subject Area 3: FINANCIAL MANAGEMENT
**Purpose:** Handle billing, payment, and reconciliation

**Key Entities:**
- Nota
- DebitCreditNote
- Payment
- PaymentIntent
- Reconciliation
- Bordero
- Invoice

**Business Function:**
- Issue premium bills
- Process payments
- Reconcile differences
- Handle adjustments

#### Subject Area 4: CLAIM MANAGEMENT
**Purpose:** Process claims and recovery

**Key Entities:**
- Claim
- Subrogation

**Business Function:**
- Submit and review claims
- Calculate claim amounts
- Process subrogation/recovery

#### Subject Area 5: SYSTEM ADMINISTRATION
**Purpose:** Configure and monitor system operations

**Key Entities:**
- SystemConfig
- SlaRule
- Notification
- NotificationSetting
- EmailTemplate
- AuditLog

**Business Function:**
- Configure business rules
- Monitor SLA compliance
- Send notifications
- Track changes

### 2.2 High-Level Entity Relationships

```
MasterContract (1) ----< (N) Contract
Contract (1) ----< (N) Batch
Batch (1) ----< (N) Debtor
Batch (1) ----< (N) Record
Debtor (1) ---- (1) Record

Contract (1) ----< (N) Bordero
Batch (1) ---- (1) Bordero
Bordero (1) ----< (N) Invoice

Batch (N) ----< (N) Nota [Premium]
Claim (1) ---- (1) Nota [Claim]
Subrogation (1) ---- (1) Nota [Subrogation]

Nota (1) ----< (N) DebitCreditNote
Nota (1) ----< (N) Payment
Nota (1) ---- (1) Reconciliation

Debtor (1) ----< (N) Claim
Claim (1) ----< (N) Subrogation
```

---

## 3. LOGICAL DATA MODEL

### 3.1 Entity Definitions with Attributes

#### 3.1.1 MASTER_CONTRACT

**Purpose:** Master template for reinsurance contracts with version control

**Primary Key:** contract_id

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| contract_id | VARCHAR(50) | NOT NULL | - | Unique contract identifier (PK) |
| policy_no | VARCHAR(50) | NOT NULL | - | Policy/contract number |
| program_id | VARCHAR(50) | NULL | - | Program identifier |
| product_type | ENUM | NOT NULL | - | Treaty/Facultative/Retro |
| credit_type | ENUM | NOT NULL | - | Individual/Corporate |
| loan_type | VARCHAR(20) | NULL | - | Loan type code |
| loan_type_desc | VARCHAR(200) | NULL | - | Loan type description |
| coverage_start_date | DATE | NOT NULL | - | Coverage start date (1 year) |
| coverage_end_date | DATE | NOT NULL | - | Coverage end date |
| max_tenor_month | INT | NULL | - | Maximum tenor in months |
| max_plafond | DECIMAL(18,2) | NULL | - | Maximum coverage limit |
| share_tugure_percentage | DECIMAL(5,2) | NULL | - | TUGURE's share percentage |
| premium_rate | DECIMAL(5,4) | NULL | - | Premium rate percentage |
| ric_rate | DECIMAL(5,4) | NULL | - | RIC rate percentage |
| bf_rate | DECIMAL(5,4) | NULL | - | BF rate percentage |
| allowed_kolektabilitas | VARCHAR(20) | NULL | - | Allowed collectibility values |
| allowed_region | VARCHAR(500) | NULL | - | Allowed regions (comma-separated) |
| currency | VARCHAR(3) | NOT NULL | 'IDR' | Currency code |
| effective_status | ENUM | NOT NULL | 'Draft' | Status of contract |
| version | INT | NOT NULL | 1 | Version number for addendum |
| parent_contract_id | VARCHAR(50) | NULL | - | Parent contract ID (FK) |
| effective_date | DATE | NULL | - | Effective date |
| first_approved_by | VARCHAR(100) | NULL | - | First approver user |
| first_approved_date | DATETIME | NULL | - | First approval timestamp |
| second_approved_by | VARCHAR(100) | NULL | - | Second approver user |
| second_approved_date | DATETIME | NULL | - | Second approval timestamp |
| rejection_reason | TEXT | NULL | - | Reason for rejection |
| remark | TEXT | NULL | - | Additional remarks |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |
| created_by | VARCHAR(100) | NOT NULL | - | User who created record |
| updated_by | VARCHAR(100) | NOT NULL | - | User who last updated |

**Business Rules:**
1. parent_contract_id must reference valid contract_id (self-referential)
2. coverage_end_date must be >= coverage_start_date
3. version increments when addendum created
4. Two-level approval required for Active status
5. Only Draft/Inactive contracts can be edited

**Indexes:**
- PRIMARY KEY (contract_id)
- INDEX idx_policy_no (policy_no)
- INDEX idx_status (effective_status)
- INDEX idx_parent (parent_contract_id)

---

#### 3.1.2 CONTRACT

**Purpose:** Active reinsurance contract instances

**Primary Key:** contract_number

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| contract_number | VARCHAR(50) | NOT NULL | - | Contract number (PK) |
| contract_name | VARCHAR(200) | NOT NULL | - | Contract name |
| cedant | ENUM | NOT NULL | 'BRINS' | Cedant name |
| reinsurer | ENUM | NOT NULL | 'TUGURE' | Reinsurer name |
| credit_type | ENUM | NOT NULL | - | Individual/Corporate |
| coverage_percentage | DECIMAL(5,2) | NULL | - | Coverage percentage |
| premium_rate | DECIMAL(5,4) | NULL | - | Premium rate |
| start_date | DATE | NOT NULL | - | Contract start date |
| end_date | DATE | NOT NULL | - | Contract end date |
| status | ENUM | NOT NULL | 'ACTIVE' | Contract status |
| currency | VARCHAR(3) | NOT NULL | 'IDR' | Currency |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. end_date must be > start_date
2. Only one ACTIVE contract per credit_type at a time
3. Cannot delete contract with associated batches

**Indexes:**
- PRIMARY KEY (contract_number)
- UNIQUE INDEX idx_unique_active (credit_type, status) WHERE status='ACTIVE'
- INDEX idx_dates (start_date, end_date)

---

#### 3.1.3 BATCH

**Purpose:** Monthly submission batch from BRINS

**Primary Key:** batch_id

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| batch_id | VARCHAR(50) | NOT NULL | - | Unique batch ID (PK) |
| batch_month | TINYINT | NOT NULL | - | Month (1-12) |
| batch_year | SMALLINT | NOT NULL | - | Year |
| contract_id | VARCHAR(50) | NOT NULL | - | Contract reference (FK) |
| total_records | INT | NOT NULL | 0 | Total number of records |
| total_exposure | DECIMAL(18,2) | NOT NULL | 0 | Raw total exposure |
| total_premium | DECIMAL(18,2) | NOT NULL | 0 | Raw total premium |
| final_exposure_amount | DECIMAL(18,2) | NOT NULL | 0 | Final exposure (approved only) |
| final_premium_amount | DECIMAL(18,2) | NOT NULL | 0 | Final premium (approved only) |
| debtor_review_completed | BOOLEAN | NOT NULL | FALSE | All debtors reviewed flag |
| batch_ready_for_nota | BOOLEAN | NOT NULL | FALSE | Ready for nota flag |
| status | ENUM | NOT NULL | 'Uploaded' | Batch workflow status |
| operational_locked | BOOLEAN | NOT NULL | FALSE | Locked when Closed |
| reopen_requested_by | VARCHAR(100) | NULL | - | User requesting reopen |
| reopen_requested_date | DATETIME | NULL | - | Reopen request timestamp |
| reopen_reason | TEXT | NULL | - | Reason for reopen |
| reopen_impact | ENUM | NULL | - | Data/Financial impact |
| reopen_approved_by | VARCHAR(100) | NULL | - | Approver of reopen |
| reopen_approved_date | DATETIME | NULL | - | Reopen approval timestamp |
| validated_by | VARCHAR(100) | NULL | - | Validator user |
| validated_date | DATE | NULL | - | Validation date |
| matched_by | VARCHAR(100) | NULL | - | Matcher user |
| matched_date | DATE | NULL | - | Matching date |
| approved_by | VARCHAR(100) | NULL | - | Approver user |
| approved_date | DATE | NULL | - | Approval date |
| nota_issued_by | VARCHAR(100) | NULL | - | Nota issuer |
| nota_issued_date | DATE | NULL | - | Nota issue date |
| branch_confirmed_by | VARCHAR(100) | NULL | - | Branch confirmer |
| branch_confirmed_date | DATE | NULL | - | Branch confirmation date |
| paid_by | VARCHAR(100) | NULL | - | Payment processor |
| paid_date | DATE | NULL | - | Payment date |
| closed_by | VARCHAR(100) | NULL | - | Closer user |
| closed_date | DATE | NULL | - | Close date |
| rejection_reason | TEXT | NULL | - | Rejection reason |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. Strict status workflow (state machine)
2. final_* amounts recalculated when debtor approved/rejected
3. batch_ready_for_nota = TRUE only when debtor_review_completed AND at least 1 approved debtor
4. operational_locked = TRUE when status = 'Closed'
5. Reopen requires supervisor approval
6. Unique constraint on (contract_id, batch_month, batch_year)

**Indexes:**
- PRIMARY KEY (batch_id)
- UNIQUE INDEX idx_unique_batch (contract_id, batch_month, batch_year)
- INDEX idx_contract (contract_id)
- INDEX idx_status (status)
- INDEX idx_period (batch_year, batch_month)

**Foreign Keys:**
- contract_id REFERENCES Contract(contract_number)

---

#### 3.1.4 DEBTOR

**Purpose:** Individual debtor/participant coverage record

**Primary Key:** cover_id

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| cover_id | BIGINT | NOT NULL | AUTO_INCREMENT | Cover ID (PK) |
| program_id | VARCHAR(50) | NULL | - | Program identifier |
| batch_id | VARCHAR(50) | NOT NULL | - | Batch reference (FK) |
| nomor_rekening_pinjaman | VARCHAR(50) | NULL | - | Loan account number |
| nomor_peserta | VARCHAR(50) | NOT NULL | - | Participant number |
| loan_type | VARCHAR(20) | NULL | - | Loan type code |
| loan_type_desc | VARCHAR(200) | NULL | - | Loan type description |
| cif_rekening_pinjaman | VARCHAR(50) | NULL | - | CIF account |
| jenis_pengajuan_desc | VARCHAR(200) | NULL | - | Submission type |
| jenis_covering_desc | VARCHAR(200) | NULL | - | Coverage type |
| tanggal_mulai_covering | DATE | NULL | - | Coverage start date |
| tanggal_akhir_covering | DATE | NULL | - | Coverage end date |
| plafon | DECIMAL(18,2) | NULL | - | Credit limit |
| nominal_premi | DECIMAL(18,2) | NULL | - | Premium amount |
| premi_percentage | DECIMAL(5,4) | NULL | - | Premium percentage |
| ric_percentage | DECIMAL(5,4) | NULL | - | RIC percentage |
| bf_percentage | DECIMAL(5,4) | NULL | - | BF percentage |
| net_premi | DECIMAL(18,2) | NULL | - | Net premium |
| unit_code | VARCHAR(20) | NULL | - | Unit code |
| unit_desc | VARCHAR(200) | NULL | - | Unit description |
| branch_desc | VARCHAR(200) | NULL | - | Branch description |
| region_desc | VARCHAR(200) | NULL | - | Region description |
| nama_peserta | VARCHAR(200) | NOT NULL | - | Participant name |
| alamat_usaha | TEXT | NULL | - | Business address |
| nomor_perjanjian_kredit | VARCHAR(50) | NULL | - | Credit agreement number |
| tanggal_terima | DATETIME | NULL | - | Receipt timestamp |
| tanggal_validasi | DATETIME | NULL | - | Validation timestamp |
| teller_premium_date | DATETIME | NULL | - | Teller premium timestamp |
| status_aktif | TINYINT | NULL | - | Active status (0/1) |
| remark_premi | TEXT | NULL | - | Premium remark |
| flag_restruktur | TINYINT | NULL | 0 | Restructuring flag |
| kolektabilitas | TINYINT | NULL | - | Collectibility (1-5) |
| contract_id | VARCHAR(50) | NULL | - | Contract reference (FK) |
| version_no | INT | NOT NULL | 1 | Version number |
| status | ENUM | NOT NULL | 'DRAFT' | Underwriting status |
| is_locked | BOOLEAN | NOT NULL | FALSE | Lock flag |
| rejection_reason | TEXT | NULL | - | Rejection reason |
| validation_remarks | TEXT | NULL | - | Validation remarks |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. net_premi = nominal_premi - (nominal_premi * ric_percentage) - (nominal_premi * bf_percentage)
2. kolektabilitas must match master contract allowed_kolektabilitas
3. region_desc must match master contract allowed_region
4. is_locked = TRUE when batch is Closed or when status = APPROVED
5. Unique constraint on (batch_id, nomor_peserta)

**Indexes:**
- PRIMARY KEY (cover_id)
- UNIQUE INDEX idx_unique_debtor (batch_id, nomor_peserta)
- INDEX idx_batch (batch_id)
- INDEX idx_contract (contract_id)
- INDEX idx_status (status)
- INDEX idx_nama (nama_peserta)

**Foreign Keys:**
- batch_id REFERENCES Batch(batch_id)
- contract_id REFERENCES Contract(contract_number)

---

#### 3.1.5 RECORD

**Purpose:** Tracking record for debtor review results

**Primary Key:** (batch_id, debtor_id) - Composite

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| batch_id | VARCHAR(50) | NOT NULL | - | Batch reference (FK, PK) |
| debtor_id | BIGINT | NOT NULL | - | Debtor reference (FK, PK) |
| record_status | ENUM | NOT NULL | 'Accepted' | Record status |
| exposure_amount | DECIMAL(18,2) | NULL | - | Exposure amount |
| premium_amount | DECIMAL(18,2) | NULL | - | Premium amount |
| revision_reason | TEXT | NULL | - | Revision reason |
| revision_count | INT | NOT NULL | 0 | Revision count |
| accepted_by | VARCHAR(100) | NULL | - | Acceptor user |
| accepted_date | DATE | NULL | - | Acceptance date |
| rejected_by | VARCHAR(100) | NULL | - | Rejector user |
| rejected_date | DATE | NULL | - | Rejection date |
| rejection_reason | TEXT | NULL | - | Rejection reason |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. When record_status = 'Accepted', update Batch.final_* amounts
2. When record_status = 'Rejected', exclude from Batch.final_* amounts
3. Check if all records reviewed to set Batch.debtor_review_completed

**Indexes:**
- PRIMARY KEY (batch_id, debtor_id)
- INDEX idx_status (record_status)
- INDEX idx_debtor (debtor_id)

**Foreign Keys:**
- batch_id REFERENCES Batch(batch_id)
- debtor_id REFERENCES Debtor(cover_id)

---

#### 3.1.6 NOTA

**Purpose:** Invoice/billing document for premium, claim, or subrogation

**Primary Key:** nota_number

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| nota_number | VARCHAR(50) | NOT NULL | - | Nota number (PK) |
| nota_type | ENUM | NOT NULL | - | Batch/Claim/Subrogation |
| reference_id | VARCHAR(50) | NOT NULL | - | Reference to source entity |
| contract_id | VARCHAR(50) | NULL | - | Contract reference (FK) |
| amount | DECIMAL(18,2) | NOT NULL | - | Nota amount (IMMUTABLE after Issued) |
| currency | VARCHAR(3) | NOT NULL | 'IDR' | Currency |
| status | ENUM | NOT NULL | 'Draft' | Nota status |
| issued_by | VARCHAR(100) | NULL | - | Issuer user |
| issued_date | DATE | NULL | - | Issue date |
| confirmed_by | VARCHAR(100) | NULL | - | Confirmer user |
| confirmed_date | DATE | NULL | - | Confirmation date |
| paid_date | DATE | NULL | - | Payment date |
| payment_reference | VARCHAR(100) | NULL | - | Payment reference |
| total_actual_paid | DECIMAL(18,2) | NOT NULL | 0 | Accumulation of payments |
| reconciliation_status | ENUM | NOT NULL | 'PENDING' | Reconciliation status |
| is_immutable | BOOLEAN | NOT NULL | FALSE | Immutability flag |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. is_immutable = TRUE when status = 'Issued'
2. amount cannot be changed when is_immutable = TRUE
3. total_actual_paid updated from Payment table
4. reconciliation_status calculated based on amount vs total_actual_paid
5. For nota_type = 'Batch', reference_id is batch_id
6. For nota_type = 'Claim', reference_id is claim_no
7. For nota_type = 'Subrogation', reference_id is subrogation_id

**Indexes:**
- PRIMARY KEY (nota_number)
- INDEX idx_type (nota_type)
- INDEX idx_reference (reference_id)
- INDEX idx_contract (contract_id)
- INDEX idx_status (status)

**Foreign Keys:**
- contract_id REFERENCES Contract(contract_number)

---

#### 3.1.7 DEBIT_CREDIT_NOTE

**Purpose:** Adjustment notes for payment differences

**Primary Key:** note_number

**Attributes:**

| Attribute | Type | Null | Default | Description |
|-----------|------|------|---------|-------------|
| note_number | VARCHAR(50) | NOT NULL | - | DN/CN number (PK) |
| note_type | ENUM | NOT NULL | - | Debit Note/Credit Note |
| original_nota_id | VARCHAR(50) | NOT NULL | - | Original nota reference (FK) |
| batch_id | VARCHAR(50) | NULL | - | Batch reference (FK) |
| contract_id | VARCHAR(50) | NULL | - | Contract reference (FK) |
| adjustment_amount | DECIMAL(18,2) | NOT NULL | - | Adjustment amount |
| reason_code | ENUM | NOT NULL | - | Reason code |
| reason_description | TEXT | NULL | - | Detailed explanation |
| status | ENUM | NOT NULL | 'Draft' | DN/CN status |
| drafted_by | VARCHAR(100) | NULL | - | Drafter user |
| drafted_date | DATETIME | NULL | - | Draft timestamp |
| reviewed_by | VARCHAR(100) | NULL | - | Reviewer user |
| reviewed_date | DATETIME | NULL | - | Review timestamp |
| approved_by | VARCHAR(100) | NULL | - | Approver user |
| approved_date | DATETIME | NULL | - | Approval timestamp |
| acknowledged_by | VARCHAR(100) | NULL | - | Acknowledger user |
| acknowledged_date | DATETIME | NULL | - | Acknowledgment timestamp |
| rejection_reason | TEXT | NULL | - | Rejection reason |
| currency | VARCHAR(3) | NOT NULL | 'IDR' | Currency |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Update timestamp |

**Business Rules:**
1. adjustment_amount > 0 for Debit Note
2. adjustment_amount < 0 for Credit Note
3. Update Nota.amount when status = 'Approved'
4. Cannot approve DN/CN if original Nota not in 'Issued' status

**Indexes:**
- PRIMARY KEY (note_number)
- INDEX idx_nota (original_nota_id)
- INDEX idx_batch (batch_id)
- INDEX idx_status (status)

**Foreign Keys:**
- original_nota_id REFERENCES Nota(nota_number)
- batch_id REFERENCES Batch(batch_id)
- contract_id REFERENCES Contract(contract_number)

---

[DOCUMENT CONTINUES WITH REMAINING ENTITIES...]

---

## 4. PHYSICAL DATA MODEL

### 4.1 Database Platform
**Target DBMS:** MySQL 8.0+ or PostgreSQL 14+

### 4.2 Storage Engines
- **InnoDB** (MySQL) for all tables (supports transactions and foreign keys)
- **PostgreSQL default** for PostgreSQL implementation

### 4.3 Character Set & Collation
- **Character Set:** utf8mb4 (MySQL) / UTF8 (PostgreSQL)
- **Collation:** utf8mb4_unicode_ci (MySQL) / en_US.UTF-8 (PostgreSQL)

### 4.4 Partitioning Strategy

#### 4.4.1 BATCH Table Partitioning
**Strategy:** RANGE partitioning by batch_year and batch_month

```sql
-- MySQL Example
CREATE TABLE Batch (
  -- columns...
) PARTITION BY RANGE (batch_year) 
  SUBPARTITION BY HASH(batch_month) 
  SUBPARTITIONS 12 (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pMAX VALUES LESS THAN MAXVALUE
);
```

#### 4.4.2 AUDIT_LOG Table Partitioning
**Strategy:** RANGE partitioning by created_at (monthly)

```sql
-- PostgreSQL Example
CREATE TABLE AuditLog (
  -- columns...
) PARTITION BY RANGE (created_at);

CREATE TABLE AuditLog_2026_01 PARTITION OF AuditLog
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
-- Create partitions for each month
```

### 4.5 Indexing Strategy

#### Critical Indexes for Performance

**1. Foreign Key Indexes**
All foreign key columns must have indexes for:
- JOIN performance
- CASCADE operation performance
- Referential integrity checks

**2. Query Pattern Indexes**

```sql
-- BATCH table
CREATE INDEX idx_batch_contract_period ON Batch(contract_id, batch_year, batch_month);
CREATE INDEX idx_batch_status ON Batch(status) WHERE status != 'Closed';

-- DEBTOR table
CREATE INDEX idx_debtor_batch_status ON Debtor(batch_id, status);
CREATE INDEX idx_debtor_nama ON Debtor(nama_peserta) USING GIN; -- Full-text search

-- NOTA table
CREATE INDEX idx_nota_type_status ON Nota(nota_type, status);
CREATE INDEX idx_nota_contract_period ON Nota(contract_id, issued_date);

-- PAYMENT table
CREATE INDEX idx_payment_nota ON Payment(invoice_id, match_status);
CREATE INDEX idx_payment_date ON Payment(payment_date DESC);

-- CLAIM table
CREATE INDEX idx_claim_batch ON Claim(batch_id, status);
CREATE INDEX idx_claim_debtor ON Claim(debtor_id);
```

**3. Covering Indexes for Common Queries**

```sql
-- Get all active batches with summary
CREATE INDEX idx_batch_summary ON Batch(
  contract_id, 
  status, 
  batch_year, 
  batch_month, 
  final_premium_amount
) WHERE status IN ('Approved', 'Nota Issued');
```

### 4.6 Constraints

#### 4.6.1 Check Constraints

```sql
-- BATCH
ALTER TABLE Batch ADD CONSTRAINT chk_batch_month 
  CHECK (batch_month BETWEEN 1 AND 12);
  
ALTER TABLE Batch ADD CONSTRAINT chk_batch_amounts 
  CHECK (final_exposure_amount >= 0 AND final_premium_amount >= 0);

-- DEBTOR
ALTER TABLE Debtor ADD CONSTRAINT chk_debtor_kolektabilitas 
  CHECK (kolektabilitas BETWEEN 1 AND 5);
  
ALTER TABLE Debtor ADD CONSTRAINT chk_debtor_percentages 
  CHECK (premi_percentage >= 0 AND ric_percentage >= 0 AND bf_percentage >= 0);

-- NOTA
ALTER TABLE Nota ADD CONSTRAINT chk_nota_amount 
  CHECK (amount > 0);

-- RECONCILIATION
ALTER TABLE Reconciliation ADD CONSTRAINT chk_recon_difference 
  CHECK (difference = total_invoiced - total_paid);
```

#### 4.6.2 Unique Constraints

```sql
-- BATCH: One batch per contract-period
ALTER TABLE Batch ADD CONSTRAINT uk_batch_period 
  UNIQUE (contract_id, batch_year, batch_month);

-- DEBTOR: One debtor per batch
ALTER TABLE Debtor ADD CONSTRAINT uk_debtor_batch 
  UNIQUE (batch_id, nomor_peserta);

-- CLAIM: Unique claim number
ALTER TABLE Claim ADD CONSTRAINT uk_claim_no 
  UNIQUE (claim_no);
```

### 4.7 Triggers

#### 4.7.1 Batch Finalization Trigger

```sql
-- Update Batch final amounts when Record status changes
CREATE TRIGGER trg_record_update_batch
AFTER INSERT OR UPDATE ON Record
FOR EACH ROW
BEGIN
  IF NEW.record_status = 'Accepted' THEN
    UPDATE Batch SET
      final_exposure_amount = (
        SELECT COALESCE(SUM(r.exposure_amount), 0)
        FROM Record r
        WHERE r.batch_id = NEW.batch_id 
          AND r.record_status = 'Accepted'
      ),
      final_premium_amount = (
        SELECT COALESCE(SUM(r.premium_amount), 0)
        FROM Record r
        WHERE r.batch_id = NEW.batch_id 
          AND r.record_status = 'Accepted'
      )
    WHERE batch_id = NEW.batch_id;
  END IF;
END;
```

#### 4.7.2 Nota Immutability Trigger

```sql
-- Prevent amount changes when nota is issued
CREATE TRIGGER trg_nota_immutable
BEFORE UPDATE ON Nota
FOR EACH ROW
BEGIN
  IF OLD.is_immutable = TRUE AND NEW.amount != OLD.amount THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot change amount on immutable nota';
  END IF;
END;
```

#### 4.7.3 Audit Log Trigger

```sql
-- Auto-create audit log for critical changes
CREATE TRIGGER trg_audit_batch_status
AFTER UPDATE ON Batch
FOR EACH ROW
BEGIN
  IF NEW.status != OLD.status THEN
    INSERT INTO AuditLog (
      action, module, entity_type, entity_id,
      old_value, new_value, user_email, user_role
    ) VALUES (
      'STATUS_CHANGE', 'BATCH', 'Batch', NEW.batch_id,
      OLD.status, NEW.status, NEW.updated_by, 'SYSTEM'
    );
  END IF;
END;
```

### 4.8 Views

#### 4.8.1 Batch Summary View

```sql
CREATE VIEW v_batch_summary AS
SELECT 
  b.batch_id,
  b.batch_month,
  b.batch_year,
  b.contract_id,
  c.contract_name,
  b.status,
  b.total_records,
  b.final_exposure_amount,
  b.final_premium_amount,
  COUNT(DISTINCT d.cover_id) as debtor_count,
  SUM(CASE WHEN r.record_status = 'Accepted' THEN 1 ELSE 0 END) as accepted_count,
  SUM(CASE WHEN r.record_status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count,
  b.debtor_review_completed,
  b.batch_ready_for_nota
FROM Batch b
JOIN Contract c ON b.contract_id = c.contract_number
LEFT JOIN Debtor d ON b.batch_id = d.batch_id
LEFT JOIN Record r ON b.batch_id = r.batch_id AND d.cover_id = r.debtor_id
GROUP BY b.batch_id;
```

#### 4.8.2 Payment Reconciliation View

```sql
CREATE VIEW v_payment_reconciliation AS
SELECT 
  n.nota_number,
  n.nota_type,
  n.amount as nota_amount,
  n.total_actual_paid,
  n.amount - n.total_actual_paid as outstanding,
  n.reconciliation_status,
  COUNT(p.payment_ref) as payment_count,
  GROUP_CONCAT(p.payment_ref) as payment_references
FROM Nota n
LEFT JOIN Payment p ON n.nota_number = p.invoice_id
GROUP BY n.nota_number;
```

---

## 5. NORMALIZATION ANALYSIS

### 5.1 Normal Forms Compliance

#### First Normal Form (1NF) ✓
- All tables have atomic values
- No repeating groups
- Primary keys defined for all tables

#### Second Normal Form (2NF) ✓
- All non-key attributes fully dependent on primary key
- No partial dependencies

#### Third Normal Form (3NF) ✓
- No transitive dependencies
- Example: region_desc in Debtor depends on unit_code, but kept for denormalization benefits

### 5.2 Denormalization Decisions

#### 5.2.1 Batch Final Amounts
**Normalized Approach:** Calculate from Record table on demand
**Denormalized:** Store final_exposure_amount and final_premium_amount in Batch

**Rationale:**
- Frequent queries on batch totals
- Performance improvement (avoid aggregation)
- Maintained via trigger on Record changes

#### 5.2.2 Debtor Descriptive Fields
**Normalized Approach:** Separate tables for Unit, Branch, Region
**Denormalized:** Store descriptions directly in Debtor

**Rationale:**
- Read-heavy operations
- Avoid multiple JOINs
- Descriptive data rarely changes

### 5.3 Dependency Diagrams

```
BATCH
  batch_id → {all other attributes}
  (contract_id, batch_month, batch_year) → batch_id

DEBTOR
  cover_id → {all other attributes}
  (batch_id, nomor_peserta) → cover_id
  
NOTA
  nota_number → {all other attributes}
  (nota_type, reference_id) → nota_number
```

---

## 6. BUSINESS RULES

### 6.1 Batch Lifecycle Rules

**BR-001:** Batch Status Workflow
- Status must follow: Uploaded → Validated → Matched → Approved → Nota Issued → Branch Confirmed → Paid → Closed
- Cannot skip statuses
- Cannot go backwards except via Reopen process

**BR-002:** Batch Finalization
- final_exposure_amount = SUM(Record.exposure_amount WHERE record_status='Accepted')
- final_premium_amount = SUM(Record.premium_amount WHERE record_status='Accepted')
- Recalculated whenever Record status changes

**BR-003:** Batch Ready for Nota
- batch_ready_for_nota = TRUE when:
  - debtor_review_completed = TRUE
  - At least 1 Record with record_status = 'Accepted'

**BR-004:** Batch Reopen
- Can only reopen Closed batches
- Requires supervisor approval
- Must specify impact type (Data or Financial)
- Audit log created for reopen action

### 6.2 Debtor Validation Rules

**BR-101:** Kolektabilitas Validation
- debtor.kolektabilitas must be in master_contract.allowed_kolektabilitas
- Validation occurs on INSERT and UPDATE

**BR-102:** Region Validation
- debtor.region_desc must be in master_contract.allowed_region
- Validation occurs on INSERT and UPDATE

**BR-103:** Premium Calculation
- net_premi = nominal_premi - (nominal_premi × ric_percentage) - (nominal_premi × bf_percentage)
- Automatically calculated on INSERT/UPDATE

**BR-104:** Debtor Lock
- is_locked = TRUE when:
  - Debtor status = 'APPROVED', OR
  - Parent Batch status = 'Closed'
- Locked debtors cannot be modified

### 6.3 Nota Rules

**BR-201:** Nota Generation
- For Premium Nota (nota_type='Batch'):
  - Created when Batch status → 'Approved'
  - amount = Batch.final_premium_amount
  
**BR-202:** Nota Immutability
- is_immutable = TRUE when status = 'Issued'
- amount cannot be changed when is_immutable = TRUE
- Only DN/CN can adjust immutable notas

**BR-203:** Payment Accumulation
- total_actual_paid = SUM(Payment.amount WHERE invoice_id = nota_number)
- Updated automatically when Payment inserted

**BR-204:** Reconciliation Status
- PENDING: total_actual_paid = 0
- PARTIAL: 0 < total_actual_paid < amount
- MATCHED: total_actual_paid = amount
- OVERPAID: total_actual_paid > amount
- FINAL: Reconciliation completed and closed

### 6.4 Payment Rules

**BR-301:** Payment Matching
- Automatic matching when Payment.invoice_id matches Nota.nota_number
- match_status = 'MATCHED' when payment amount matches nota amount
- match_status = 'PARTIALLY_MATCHED' when payment amount < nota amount
- exception_type set based on payment variance

**BR-302:** Payment Reconciliation
- Create Reconciliation record when Payment received
- Update Reconciliation.total_paid
- Calculate difference = total_invoiced - total_paid

**BR-303:** Debit/Credit Note Generation
- DN created when payment < nota amount (underpayment)
- CN created when payment > nota amount (overpayment)
- DN/CN requires approval before affecting nota amount

### 6.5 Claim Rules

**BR-401:** Claim Eligibility
- Debtor must be in 'APPROVED' status
- Debtor must be in valid coverage period
- Claim amount cannot exceed max_coverage

**BR-402:** Claim Calculation
- share_tugure_amount = nilai_klaim × share_tugure_percentage
- Percentage comes from master contract

**BR-403:** Claim Nota Generation
- Nota created when Claim status = 'Approved'
- nota_type = 'Claim'
- amount = share_tugure_amount

### 6.6 Audit Rules

**BR-501:** Mandatory Audit Events
- All status changes on Batch, Nota, Claim
- All approval/rejection actions
- All amount changes on financial records
- All Batch reopen actions

**BR-502:** Audit Log Retention
- Audit logs retained for minimum 7 years
- Cannot be deleted or modified
- Partition by month for performance

---

## 7. DATA DICTIONARY

### 7.1 Data Type Standards

| Business Type | MySQL Type | PostgreSQL Type | Description |
|---------------|------------|-----------------|-------------|
| Identifier | VARCHAR(50) | VARCHAR(50) | Unique IDs |
| Name | VARCHAR(200) | VARCHAR(200) | Person/entity names |
| Description | TEXT | TEXT | Long text descriptions |
| Amount | DECIMAL(18,2) | NUMERIC(18,2) | Monetary values |
| Percentage | DECIMAL(5,4) | NUMERIC(5,4) | Rate percentages (0.0000-9.9999) |
| Share Percentage | DECIMAL(5,2) | NUMERIC(5,2) | Share percentages (0.00-100.00) |
| Date | DATE | DATE | Date without time |
| Timestamp | DATETIME | TIMESTAMP | Date with time |
| Flag | BOOLEAN | BOOLEAN | True/false values |
| Count | INT | INTEGER | Whole numbers |
| Small Count | TINYINT | SMALLINT | Small whole numbers (0-255) |
| Year | SMALLINT | SMALLINT | Year values |
| Month | TINYINT | SMALLINT | Month (1-12) |

### 7.2 Enumeration Values

#### status (Batch)
```
'Uploaded', 'Validated', 'Matched', 'Approved', 
'Nota Issued', 'Branch Confirmed', 'Paid', 'Closed', 
'Rejected', 'Reopen Requested', 'Reopened'
```

#### status (Debtor)
```
'DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'CONDITIONAL'
```

#### record_status (Record)
```
'Accepted', 'Rejected', 'Revised'
```

#### nota_type (Nota)
```
'Batch', 'Claim', 'Subrogation'
```

#### status (Nota)
```
'Draft', 'Issued', 'Confirmed', 'Paid'
```

#### reconciliation_status (Nota)
```
'PENDING', 'PARTIAL', 'MATCHED', 'OVERPAID', 'FINAL'
```

#### note_type (DebitCreditNote)
```
'Debit Note', 'Credit Note'
```

#### reason_code (DebitCreditNote)
```
'Payment Difference', 'FX Adjustment', 'Premium Correction', 
'Coverage Adjustment', 'Other'
```

#### match_status (Payment)
```
'RECEIVED', 'MATCHED', 'PARTIALLY_MATCHED', 'UNMATCHED'
```

#### exception_type (Payment)
```
'NONE', 'PARTIAL', 'OVER', 'UNDER', 'LATE', 'FX'
```

### 7.3 Code Standards

#### Naming Conventions
- Table names: PascalCase (e.g., MasterContract, DebitCreditNote)
- Column names: snake_case (e.g., batch_id, final_premium_amount)
- Index names: idx_tablename_columns (e.g., idx_batch_contract_period)
- Foreign key names: fk_childtable_parenttable (e.g., fk_batch_contract)
- Trigger names: trg_tablename_action (e.g., trg_nota_immutable)

#### ID Generation
- Auto-increment for numeric IDs (e.g., cover_id)
- Format: PREFIX-YYYY-MM-SEQUENCE for business IDs
  - Batch: BTH-2026-01-0001
  - Nota: NTA-2026-01-0001
  - Claim: CLM-2026-01-0001

---

## 8. INDEXING STRATEGY

### 8.1 Index Types

#### B-Tree Indexes (Default)
- Used for equality and range queries
- All primary keys and foreign keys

#### Full-Text Indexes
```sql
-- MySQL
CREATE FULLTEXT INDEX idx_debtor_nama_fulltext ON Debtor(nama_peserta);

-- PostgreSQL
CREATE INDEX idx_debtor_nama_gin ON Debtor USING GIN(to_tsvector('indonesian', nama_peserta));
```

#### Partial Indexes
```sql
-- Index only active batches
CREATE INDEX idx_batch_active ON Batch(contract_id, batch_year, batch_month) 
WHERE status NOT IN ('Closed', 'Rejected');

-- Index only unmatched payments
CREATE INDEX idx_payment_unmatched ON Payment(payment_date, amount) 
WHERE match_status = 'UNMATCHED';
```

### 8.2 Composite Index Strategy

**Order Matters:**
- Most selective column first
- Columns used in WHERE clauses before ORDER BY
- Equality conditions before range conditions

**Example:**
```sql
-- Good: contract_id (high selectivity) before batch_year
CREATE INDEX idx_batch_lookup ON Batch(contract_id, batch_year, batch_month, status);

-- Query can use this index:
SELECT * FROM Batch 
WHERE contract_id = 'CTR-001' 
  AND batch_year = 2026 
  AND batch_month = 1;

-- Query can partially use this index (contract_id only):
SELECT * FROM Batch 
WHERE contract_id = 'CTR-001' 
  AND status = 'Approved';
```

### 8.3 Index Maintenance

#### Regular Maintenance Tasks
```sql
-- MySQL
OPTIMIZE TABLE Batch;
ANALYZE TABLE Batch;

-- PostgreSQL
VACUUM ANALYZE Batch;
REINDEX TABLE Batch;
```

#### Monitoring Index Usage
```sql
-- PostgreSQL: Find unused indexes
SELECT 
  schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 
  AND indexname NOT LIKE '%_pkey';

-- MySQL: Check index cardinality
SHOW INDEX FROM Batch;
```

---

## 9. DATA VOLUME ESTIMATES

### 9.1 Annual Volume Projections

| Entity | Records/Year | Growth Rate | 5-Year Total |
|--------|-------------|-------------|--------------|
| MasterContract | 10 | 10% | 61 |
| Contract | 5 | 5% | 28 |
| Batch | 60 | 15% | 405 |
| Debtor | 60,000 | 20% | 446,064 |
| Record | 60,000 | 20% | 446,064 |
| Nota | 180 | 15% | 1,215 |
| Payment | 360 | 15% | 2,430 |
| Claim | 600 | 10% | 3,663 |
| Subrogation | 60 | 10% | 366 |
| AuditLog | 180,000 | 25% | 1,681,200 |

### 9.2 Storage Estimates

**Per Record Storage (avg):**
- Batch: 2 KB
- Debtor: 1.5 KB
- Record: 0.5 KB
- Nota: 1 KB
- Payment: 0.8 KB
- Claim: 2 KB
- AuditLog: 0.5 KB

**5-Year Total Storage:**
- Data: ~1.2 GB
- Indexes: ~600 MB
- Total: ~1.8 GB

**Partitioning Benefit:**
- Active data (current year): ~200 MB
- Historical data: Archived/partitioned

---

## 10. PERFORMANCE CONSIDERATIONS

### 10.1 Query Optimization

#### Critical Query Patterns

**Q1: Get Batch Summary**
```sql
-- Optimized with covering index
SELECT 
  b.batch_id, b.status, b.final_premium_amount,
  COUNT(d.cover_id) as debtor_count
FROM Batch b
LEFT JOIN Debtor d ON b.batch_id = d.batch_id
WHERE b.contract_id = ? 
  AND b.batch_year = ?
GROUP BY b.batch_id;

-- Index: idx_batch_contract_period (contract_id, batch_year, batch_month, status, final_premium_amount)
```

**Q2: Payment Reconciliation**
```sql
-- Use materialized view for complex reconciliation
CREATE MATERIALIZED VIEW mv_reconciliation AS
SELECT 
  n.nota_number,
  n.amount,
  COALESCE(SUM(p.amount), 0) as total_paid,
  n.amount - COALESCE(SUM(p.amount), 0) as difference
FROM Nota n
LEFT JOIN Payment p ON n.nota_number = p.invoice_id
GROUP BY n.nota_number, n.amount;

-- Refresh daily
REFRESH MATERIALIZED VIEW mv_reconciliation;
```

### 10.2 Caching Strategy

**Application-Level Cache:**
- MasterContract (rarely changes): 24-hour cache
- SystemConfig: 1-hour cache
- Lookup tables (enums): Permanent cache

**Database Query Cache:**
- Enable for read-heavy queries
- Clear on related table updates

### 10.3 Archival Strategy

**Batch/Debtor Archival:**
- Archive batches older than 3 years to archive database
- Keep summary data in main database
- Implement archive retrieval API

**AuditLog Archival:**
- Partition by month
- Archive partitions older than 2 years
- Retain for 7 years (compliance)

---

## APPENDIX A: DDL SCRIPTS

### Complete DDL for Core Tables

```sql
-- =====================================================
-- MASTER_CONTRACT TABLE
-- =====================================================
CREATE TABLE MasterContract (
  contract_id VARCHAR(50) NOT NULL,
  policy_no VARCHAR(50) NOT NULL,
  program_id VARCHAR(50),
  product_type ENUM('Treaty', 'Facultative', 'Retro') NOT NULL,
  credit_type ENUM('Individual', 'Corporate') NOT NULL,
  loan_type VARCHAR(20),
  loan_type_desc VARCHAR(200),
  coverage_start_date DATE NOT NULL,
  coverage_end_date DATE NOT NULL,
  max_tenor_month INT,
  max_plafond DECIMAL(18,2),
  share_tugure_percentage DECIMAL(5,2),
  premium_rate DECIMAL(5,4),
  ric_rate DECIMAL(5,4),
  bf_rate DECIMAL(5,4),
  allowed_kolektabilitas VARCHAR(20),
  allowed_region VARCHAR(500),
  currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
  effective_status ENUM('Draft', 'Pending First Approval', 'Pending Second Approval', 'Active', 'Inactive', 'Archived') NOT NULL DEFAULT 'Draft',
  version INT NOT NULL DEFAULT 1,
  parent_contract_id VARCHAR(50),
  effective_date DATE,
  first_approved_by VARCHAR(100),
  first_approved_date DATETIME,
  second_approved_by VARCHAR(100),
  second_approved_date DATETIME,
  rejection_reason TEXT,
  remark TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by VARCHAR(100) NOT NULL,
  updated_by VARCHAR(100) NOT NULL,
  
  PRIMARY KEY (contract_id),
  INDEX idx_policy_no (policy_no),
  INDEX idx_status (effective_status),
  INDEX idx_parent (parent_contract_id),
  
  CONSTRAINT fk_master_parent FOREIGN KEY (parent_contract_id) 
    REFERENCES MasterContract(contract_id),
  CONSTRAINT chk_master_dates CHECK (coverage_end_date >= coverage_start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CONTRACT TABLE
-- =====================================================
CREATE TABLE Contract (
  contract_number VARCHAR(50) NOT NULL,
  contract_name VARCHAR(200) NOT NULL,
  cedant ENUM('BRINS') NOT NULL DEFAULT 'BRINS',
  reinsurer ENUM('TUGURE') NOT NULL DEFAULT 'TUGURE',
  credit_type ENUM('Individual', 'Corporate') NOT NULL,
  coverage_percentage DECIMAL(5,2),
  premium_rate DECIMAL(5,4),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status ENUM('ACTIVE', 'EXPIRED', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
  currency VARCHAR(3) NOT NULL DEFAULT 'IDR',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (contract_number),
  INDEX idx_dates (start_date, end_date),
  INDEX idx_status (status),
  
  CONSTRAINT chk_contract_dates CHECK (end_date > start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- BATCH TABLE  
-- =====================================================
CREATE TABLE Batch (
  batch_id VARCHAR(50) NOT NULL,
  batch_month TINYINT NOT NULL,
  batch_year SMALLINT NOT NULL,
  contract_id VARCHAR(50) NOT NULL,
  total_records INT NOT NULL DEFAULT 0,
  total_exposure DECIMAL(18,2) NOT NULL DEFAULT 0,
  total_premium DECIMAL(18,2) NOT NULL DEFAULT 0,
  final_exposure_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  final_premium_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  debtor_review_completed BOOLEAN NOT NULL DEFAULT FALSE,
  batch_ready_for_nota BOOLEAN NOT NULL DEFAULT FALSE,
  status ENUM('Uploaded', 'Validated', 'Matched', 'Approved', 'Nota Issued', 'Branch Confirmed', 'Paid', 'Closed', 'Rejected', 'Reopen Requested', 'Reopened') NOT NULL DEFAULT 'Uploaded',
  operational_locked BOOLEAN NOT NULL DEFAULT FALSE,
  reopen_requested_by VARCHAR(100),
  reopen_requested_date DATETIME,
  reopen_reason TEXT,
  reopen_impact ENUM('Data', 'Financial'),
  reopen_approved_by VARCHAR(100),
  reopen_approved_date DATETIME,
  validated_by VARCHAR(100),
  validated_date DATE,
  matched_by VARCHAR(100),
  matched_date DATE,
  approved_by VARCHAR(100),
  approved_date DATE,
  nota_issued_by VARCHAR(100),
  nota_issued_date DATE,
  branch_confirmed_by VARCHAR(100),
  branch_confirmed_date DATE,
  paid_by VARCHAR(100),
  paid_date DATE,
  closed_by VARCHAR(100),
  closed_date DATE,
  rejection_reason TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (batch_id),
  UNIQUE INDEX uk_batch_period (contract_id, batch_year, batch_month),
  INDEX idx_contract (contract_id),
  INDEX idx_status (status),
  INDEX idx_period (batch_year, batch_month),
  INDEX idx_contract_period (contract_id, batch_year, batch_month),
  
  CONSTRAINT fk_batch_contract FOREIGN KEY (contract_id) 
    REFERENCES Contract(contract_number),
  CONSTRAINT chk_batch_month CHECK (batch_month BETWEEN 1 AND 12),
  CONSTRAINT chk_batch_amounts CHECK (final_exposure_amount >= 0 AND final_premium_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Continue with remaining tables...
```

---

## APPENDIX B: Sample Queries

### Business Intelligence Queries

#### Monthly Premium Report
```sql
SELECT 
  DATE_FORMAT(CONCAT(batch_year, '-', LPAD(batch_month, 2, '0'), '-01'), '%Y-%m') as period,
  c.contract_name,
  COUNT(DISTINCT b.batch_id) as batch_count,
  SUM(b.total_records) as total_debtors,
  SUM(b.final_exposure_amount) as total_exposure,
  SUM(b.final_premium_amount) as total_premium,
  AVG(b.final_premium_amount) as avg_premium_per_batch
FROM Batch b
JOIN Contract c ON b.contract_id = c.contract_number
WHERE b.status IN ('Approved', 'Nota Issued', 'Paid', 'Closed')
  AND b.batch_year = 2026
GROUP BY period, c.contract_name
ORDER BY period, c.contract_name;
```

#### Payment Variance Analysis
```sql
SELECT 
  n.nota_number,
  n.nota_type,
  n.amount as billed_amount,
  n.total_actual_paid as paid_amount,
  n.amount - n.total_actual_paid as variance,
  CASE
    WHEN n.total_actual_paid = 0 THEN 'Not Paid'
    WHEN n.total_actual_paid < n.amount THEN 'Underpaid'
    WHEN n.total_actual_paid = n.amount THEN 'Exact'
    WHEN n.total_actual_paid > n.amount THEN 'Overpaid'
  END as payment_status,
  COUNT(dcn.note_number) as adjustment_count
FROM Nota n
LEFT JOIN DebitCreditNote dcn ON n.nota_number = dcn.original_nota_id
WHERE n.status = 'Issued'
GROUP BY n.nota_number
HAVING variance != 0
ORDER BY ABS(variance) DESC;
```

---

**END OF DATA MODELING DOCUMENT**
