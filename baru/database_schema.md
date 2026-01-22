# Database Schema - Technical Specification

## Database Design Principles

### 1. Normalization
- Third Normal Form (3NF) applied to reduce redundancy
- Strategic denormalization for performance (e.g., total amounts in Batch)

### 2. Data Integrity
- Primary keys on all tables
- Foreign key constraints with appropriate cascade rules
- Check constraints for enum values and business rules
- Not null constraints for critical fields

### 3. Performance Optimization
- Indexes on foreign keys and frequently queried columns
- Composite indexes for common query patterns
- Partitioning strategy for high-volume tables

### 4. Audit Trail
- All tables include created_at, updated_at timestamps
- Soft delete pattern where applicable
- Complete audit log in separate table

---

## Core Tables DDL

### MasterContract

```sql
CREATE TABLE master_contract (
    -- Primary Key
    contract_id VARCHAR(50) PRIMARY KEY,
    
    -- Basic Information
    policy_no VARCHAR(50) NOT NULL,
    program_id VARCHAR(50) NOT NULL,
    product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Treaty', 'Facultative', 'Retro')),
    credit_type VARCHAR(20) NOT NULL CHECK (credit_type IN ('Individual', 'Corporate')),
    loan_type VARCHAR(20),
    loan_type_desc VARCHAR(200),
    
    -- Coverage Dates
    coverage_start_date DATE NOT NULL,
    coverage_end_date DATE NOT NULL,
    effective_date DATE,
    
    -- Limits
    max_tenor_month INTEGER,
    max_plafond DECIMAL(20, 2),
    
    -- Rates
    share_tugure_percentage DECIMAL(5, 2) NOT NULL,
    premium_rate DECIMAL(5, 4) NOT NULL,
    ric_rate DECIMAL(5, 4),
    bf_rate DECIMAL(5, 4),
    
    -- Rules
    allowed_kolektabilitas VARCHAR(50), -- e.g., "1,2,3"
    allowed_region TEXT,
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Status & Versioning
    effective_status VARCHAR(30) NOT NULL DEFAULT 'Draft' 
        CHECK (effective_status IN ('Draft', 'Pending First Approval', 'Pending Second Approval', 
                                     'Active', 'Inactive', 'Archived')),
    version INTEGER DEFAULT 1,
    parent_contract_id VARCHAR(50) REFERENCES master_contract(contract_id),
    
    -- Approval Tracking
    first_approved_by VARCHAR(100),
    first_approved_date TIMESTAMP,
    second_approved_by VARCHAR(100),
    second_approved_date TIMESTAMP,
    rejection_reason TEXT,
    
    -- Notes
    remark TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    
    -- Constraints
    CONSTRAINT chk_dates CHECK (coverage_end_date > coverage_start_date),
    CONSTRAINT chk_percentages CHECK (
        share_tugure_percentage BETWEEN 0 AND 100 AND
        premium_rate > 0
    )
);

-- Indexes
CREATE INDEX idx_mc_status ON master_contract(effective_status);
CREATE INDEX idx_mc_parent ON master_contract(parent_contract_id);
CREATE INDEX idx_mc_dates ON master_contract(coverage_start_date, coverage_end_date);
CREATE INDEX idx_mc_program ON master_contract(program_id);
```

### Contract

```sql
CREATE TABLE contract (
    -- Primary Key
    contract_number VARCHAR(50) PRIMARY KEY,
    
    -- Basic Information
    contract_name VARCHAR(200) NOT NULL,
    cedant VARCHAR(20) DEFAULT 'BRINS' CHECK (cedant = 'BRINS'),
    reinsurer VARCHAR(20) DEFAULT 'TUGURE' CHECK (reinsurer = 'TUGURE'),
    credit_type VARCHAR(20) NOT NULL CHECK (credit_type IN ('Individual', 'Corporate')),
    
    -- Terms
    coverage_percentage DECIMAL(5, 2) NOT NULL,
    premium_rate DECIMAL(5, 4) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE' 
        CHECK (status IN ('ACTIVE', 'EXPIRED', 'TERMINATED')),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    
    -- Constraints
    CONSTRAINT chk_contract_dates CHECK (end_date > start_date),
    CONSTRAINT chk_contract_coverage CHECK (coverage_percentage BETWEEN 0 AND 100)
);

-- Indexes
CREATE INDEX idx_contract_status ON contract(status);
CREATE INDEX idx_contract_dates ON contract(start_date, end_date);
```

### Batch

```sql
CREATE TABLE batch (
    -- Primary Key
    batch_id VARCHAR(50) PRIMARY KEY,
    
    -- Period
    batch_month INTEGER NOT NULL CHECK (batch_month BETWEEN 1 AND 12),
    batch_year INTEGER NOT NULL CHECK (batch_year >= 2020),
    
    -- Foreign Key
    contract_id VARCHAR(50) NOT NULL REFERENCES contract(contract_number),
    
    -- Counts and Raw Amounts
    total_records INTEGER DEFAULT 0,
    total_exposure DECIMAL(20, 2) DEFAULT 0,
    total_premium DECIMAL(20, 2) DEFAULT 0,
    
    -- Final Amounts (after debtor review)
    final_exposure_amount DECIMAL(20, 2) DEFAULT 0,
    final_premium_amount DECIMAL(20, 2) DEFAULT 0,
    
    -- Review Flags
    debtor_review_completed BOOLEAN DEFAULT FALSE,
    batch_ready_for_nota BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'Uploaded'
        CHECK (status IN ('Uploaded', 'Validated', 'Matched', 'Approved', 'Nota Issued',
                          'Branch Confirmed', 'Paid', 'Closed', 'Rejected', 
                          'Reopen Requested', 'Reopened')),
    
    -- Lock
    operational_locked BOOLEAN DEFAULT FALSE,
    
    -- Reopen Tracking
    reopen_requested_by VARCHAR(100),
    reopen_requested_date TIMESTAMP,
    reopen_reason TEXT,
    reopen_impact VARCHAR(20) CHECK (reopen_impact IN ('Data', 'Financial')),
    reopen_approved_by VARCHAR(100),
    reopen_approved_date TIMESTAMP,
    
    -- Status Tracking
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
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_batch_contract ON batch(contract_id);
CREATE INDEX idx_batch_period ON batch(batch_year, batch_month);
CREATE INDEX idx_batch_status ON batch(status);
CREATE INDEX idx_batch_locked ON batch(operational_locked);
CREATE INDEX idx_batch_ready ON batch(batch_ready_for_nota);

-- Unique constraint on contract + period
CREATE UNIQUE INDEX idx_batch_unique_period ON batch(contract_id, batch_year, batch_month);
```

### Debtor

```sql
CREATE TABLE debtor (
    -- Primary Key
    cover_id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys
    program_id VARCHAR(50),
    batch_id VARCHAR(50) NOT NULL REFERENCES batch(batch_id),
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Identification
    nomor_rekening_pinjaman VARCHAR(50),
    nomor_peserta VARCHAR(50) NOT NULL,
    cif_rekening_pinjaman VARCHAR(50),
    nomor_perjanjian_kredit VARCHAR(100),
    
    -- Loan Information
    loan_type VARCHAR(20),
    loan_type_desc VARCHAR(200),
    jenis_pengajuan_desc VARCHAR(100),
    jenis_covering_desc VARCHAR(100),
    
    -- Coverage Period
    tanggal_mulai_covering DATE,
    tanggal_akhir_covering DATE,
    tanggal_terima TIMESTAMP,
    tanggal_validasi TIMESTAMP,
    teller_premium_date TIMESTAMP,
    
    -- Amounts
    plafon DECIMAL(20, 2),
    nominal_premi DECIMAL(20, 2),
    premi_percentage DECIMAL(5, 2),
    ric_percentage DECIMAL(5, 2),
    bf_percentage DECIMAL(5, 2),
    net_premi DECIMAL(20, 2),
    
    -- Organization
    unit_code VARCHAR(20),
    unit_desc VARCHAR(200),
    branch_desc VARCHAR(200),
    region_desc VARCHAR(200),
    
    -- Debtor Details
    nama_peserta VARCHAR(200) NOT NULL,
    alamat_usaha TEXT,
    
    -- Status Fields
    status_aktif INTEGER CHECK (status_aktif IN (0, 1)),
    flag_restruktur INTEGER CHECK (flag_restruktur IN (0, 1)),
    kolektabilitas INTEGER CHECK (kolektabilitas BETWEEN 1 AND 5),
    
    -- Remarks
    remark_premi TEXT,
    validation_remarks TEXT,
    rejection_reason TEXT,
    
    -- Version Control
    version_no INTEGER DEFAULT 1,
    
    -- Underwriting Status
    status VARCHAR(20) DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'CONDITIONAL')),
    
    -- Lock
    is_locked BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_debtor_batch ON debtor(batch_id);
CREATE INDEX idx_debtor_contract ON debtor(contract_id);
CREATE INDEX idx_debtor_status ON debtor(status);
CREATE INDEX idx_debtor_locked ON debtor(is_locked);
CREATE INDEX idx_debtor_peserta ON debtor(nomor_peserta);
CREATE INDEX idx_debtor_rekening ON debtor(nomor_rekening_pinjaman);
CREATE INDEX idx_debtor_kol ON debtor(kolektabilitas);
```

### Record

```sql
CREATE TABLE record (
    -- Composite Primary Key
    batch_id VARCHAR(50) NOT NULL REFERENCES batch(batch_id),
    debtor_id BIGINT NOT NULL REFERENCES debtor(cover_id),
    
    -- Status
    record_status VARCHAR(20) DEFAULT 'Accepted'
        CHECK (record_status IN ('Accepted', 'Rejected', 'Revised')),
    
    -- Amounts (snapshot at time of review)
    exposure_amount DECIMAL(20, 2),
    premium_amount DECIMAL(20, 2),
    
    -- Revision Tracking
    revision_reason TEXT,
    revision_count INTEGER DEFAULT 0,
    
    -- Status Tracking
    accepted_by VARCHAR(100),
    accepted_date DATE,
    rejected_by VARCHAR(100),
    rejected_date DATE,
    rejection_reason TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (batch_id, debtor_id)
);

-- Indexes
CREATE INDEX idx_record_status ON record(record_status);
CREATE INDEX idx_record_debtor ON record(debtor_id);
```

### Claim

```sql
CREATE TABLE claim (
    -- Primary Key
    claim_no VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    batch_id VARCHAR(50) REFERENCES batch(batch_id),
    debtor_id BIGINT REFERENCES debtor(cover_id),
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Policy Information
    policy_no VARCHAR(50),
    nomor_sertifikat VARCHAR(50),
    nama_tertanggung VARCHAR(200) NOT NULL,
    no_ktp_npwp VARCHAR(50),
    no_fasilitas_kredit VARCHAR(50),
    
    -- Premium Period
    bdo_premi VARCHAR(7), -- YYYY-MM
    check_bdo_premi BOOLEAN DEFAULT FALSE,
    
    -- Dates
    tanggal_realisasi_kredit DATE,
    dol DATE, -- Date of Loss
    
    -- Amounts
    plafond DECIMAL(20, 2),
    max_coverage DECIMAL(20, 2),
    nilai_klaim DECIMAL(20, 2) NOT NULL,
    share_tugure_percentage DECIMAL(5, 2),
    share_tugure_amount DECIMAL(20, 2),
    
    -- Status
    kol_debitur VARCHAR(10),
    version_no INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Checked', 'Doc Verified', 'Invoiced', 'Paid')),
    
    -- Status Tracking
    checked_by VARCHAR(100),
    checked_date DATE,
    doc_verified_by VARCHAR(100),
    doc_verified_date DATE,
    invoiced_by VARCHAR(100),
    invoiced_date DATE,
    paid_by VARCHAR(100),
    paid_date DATE,
    reviewed_by VARCHAR(100),
    review_date DATE,
    rejection_reason TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_claim_batch ON claim(batch_id);
CREATE INDEX idx_claim_debtor ON claim(debtor_id);
CREATE INDEX idx_claim_contract ON claim(contract_id);
CREATE INDEX idx_claim_status ON claim(status);
CREATE INDEX idx_claim_dol ON claim(dol);
CREATE INDEX idx_claim_policy ON claim(policy_no);
```

### Subrogation

```sql
CREATE TABLE subrogation (
    -- Primary Key
    subrogation_id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    claim_id VARCHAR(50) NOT NULL REFERENCES claim(claim_no),
    debtor_id BIGINT REFERENCES debtor(cover_id),
    
    -- Recovery
    recovery_amount DECIMAL(20, 2) NOT NULL,
    recovery_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Invoiced', 'Paid / Closed')),
    
    -- Status Tracking
    invoiced_by VARCHAR(100),
    invoiced_date DATE,
    closed_by VARCHAR(100),
    closed_date DATE,
    remarks TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_subrogation_claim ON subrogation(claim_id);
CREATE INDEX idx_subrogation_debtor ON subrogation(debtor_id);
CREATE INDEX idx_subrogation_status ON subrogation(status);
```

### Nota

```sql
CREATE TABLE nota (
    -- Primary Key
    nota_number VARCHAR(50) PRIMARY KEY,
    
    -- Type and Reference
    nota_type VARCHAR(20) NOT NULL CHECK (nota_type IN ('Batch', 'Claim', 'Subrogation')),
    reference_id VARCHAR(50) NOT NULL, -- batch_id, claim_id, or subrogation_id
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Amount (IMMUTABLE after Issued)
    amount DECIMAL(20, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Payment Tracking
    total_actual_paid DECIMAL(20, 2) DEFAULT 0,
    payment_reference VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Issued', 'Confirmed', 'Paid')),
    reconciliation_status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (reconciliation_status IN ('PENDING', 'PARTIAL', 'MATCHED', 'OVERPAID', 'FINAL')),
    
    -- Immutability Flag
    is_immutable BOOLEAN DEFAULT FALSE,
    
    -- Status Tracking
    issued_by VARCHAR(100),
    issued_date DATE,
    confirmed_by VARCHAR(100),
    confirmed_date DATE,
    paid_date DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_nota_type ON nota(nota_type);
CREATE INDEX idx_nota_reference ON nota(nota_type, reference_id);
CREATE INDEX idx_nota_contract ON nota(contract_id);
CREATE INDEX idx_nota_status ON nota(status);
CREATE INDEX idx_nota_recon_status ON nota(reconciliation_status);
```

### DebitCreditNote

```sql
CREATE TABLE debit_credit_note (
    -- Primary Key
    note_number VARCHAR(50) PRIMARY KEY,
    
    -- Type
    note_type VARCHAR(20) NOT NULL CHECK (note_type IN ('Debit Note', 'Credit Note')),
    
    -- Foreign Keys
    original_nota_id VARCHAR(50) NOT NULL REFERENCES nota(nota_number),
    batch_id VARCHAR(50) REFERENCES batch(batch_id),
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Adjustment
    adjustment_amount DECIMAL(20, 2) NOT NULL,
    reason_code VARCHAR(50) NOT NULL
        CHECK (reason_code IN ('Payment Difference', 'FX Adjustment', 
                               'Premium Correction', 'Coverage Adjustment', 'Other')),
    reason_description TEXT,
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Status
    status VARCHAR(20) DEFAULT 'Draft'
        CHECK (status IN ('Draft', 'Under Review', 'Approved', 'Rejected', 'Acknowledged')),
    
    -- Workflow Tracking
    drafted_by VARCHAR(100),
    drafted_date TIMESTAMP,
    reviewed_by VARCHAR(100),
    reviewed_date TIMESTAMP,
    approved_by VARCHAR(100),
    approved_date TIMESTAMP,
    acknowledged_by VARCHAR(100),
    acknowledged_date TIMESTAMP,
    rejection_reason TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_dncn_nota ON debit_credit_note(original_nota_id);
CREATE INDEX idx_dncn_batch ON debit_credit_note(batch_id);
CREATE INDEX idx_dncn_contract ON debit_credit_note(contract_id);
CREATE INDEX idx_dncn_status ON debit_credit_note(status);
CREATE INDEX idx_dncn_type ON debit_credit_note(note_type);
```

### Bordero

```sql
CREATE TABLE bordero (
    -- Primary Key
    bordero_id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    contract_id VARCHAR(50) NOT NULL REFERENCES contract(contract_number),
    batch_id VARCHAR(50) REFERENCES batch(batch_id),
    
    -- Period
    period VARCHAR(7) NOT NULL, -- YYYY-MM
    
    -- Aggregates
    total_debtors INTEGER,
    total_exposure DECIMAL(20, 2),
    total_premium DECIMAL(20, 2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Status
    status VARCHAR(20) DEFAULT 'GENERATED'
        CHECK (status IN ('GENERATED', 'UNDER_REVIEW', 'FINAL', 'ADJUSTED')),
    
    -- Tracking
    reviewed_by VARCHAR(100),
    reviewed_date DATE,
    finalized_by VARCHAR(100),
    finalized_date DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_bordero_contract ON bordero(contract_id);
CREATE INDEX idx_bordero_batch ON bordero(batch_id);
CREATE INDEX idx_bordero_period ON bordero(period);
CREATE INDEX idx_bordero_status ON bordero(status);
```

### Invoice

```sql
CREATE TABLE invoice (
    -- Primary Key
    invoice_number VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    bordero_id VARCHAR(50) REFERENCES bordero(bordero_id),
    contract_id VARCHAR(50) NOT NULL REFERENCES contract(contract_number),
    
    -- Period
    period VARCHAR(7), -- YYYY-MM
    
    -- Amounts
    total_amount DECIMAL(20, 2) NOT NULL,
    paid_amount DECIMAL(20, 2) DEFAULT 0,
    outstanding_amount DECIMAL(20, 2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Due Date
    due_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'ISSUED'
        CHECK (status IN ('ISSUED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'ADJUSTED')),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_invoice_bordero ON invoice(bordero_id);
CREATE INDEX idx_invoice_contract ON invoice(contract_id);
CREATE INDEX idx_invoice_status ON invoice(status);
CREATE INDEX idx_invoice_due_date ON invoice(due_date);
```

### PaymentIntent

```sql
CREATE TABLE payment_intent (
    -- Primary Key
    intent_id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    invoice_id VARCHAR(50) NOT NULL REFERENCES invoice(invoice_number),
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Payment Type
    payment_type VARCHAR(20) DEFAULT 'FULL'
        CHECK (payment_type IN ('FULL', 'PARTIAL', 'INSTALMENT')),
    
    -- Plan
    planned_amount DECIMAL(20, 2) NOT NULL,
    planned_date DATE NOT NULL,
    remarks TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'CANCELLED')),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_payment_intent_invoice ON payment_intent(invoice_id);
CREATE INDEX idx_payment_intent_contract ON payment_intent(contract_id);
CREATE INDEX idx_payment_intent_status ON payment_intent(status);
CREATE INDEX idx_payment_intent_date ON payment_intent(planned_date);
```

### Payment

```sql
CREATE TABLE payment (
    -- Primary Key
    payment_ref VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Keys
    invoice_id VARCHAR(50) REFERENCES nota(nota_number), -- Can be Invoice or Nota
    intent_id VARCHAR(50) REFERENCES payment_intent(intent_id),
    contract_id VARCHAR(50) REFERENCES contract(contract_number),
    
    -- Payment Details
    amount DECIMAL(20, 2) NOT NULL,
    payment_date DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    bank_reference VARCHAR(100),
    
    -- Matching Status
    match_status VARCHAR(20) DEFAULT 'RECEIVED'
        CHECK (match_status IN ('RECEIVED', 'MATCHED', 'PARTIALLY_MATCHED', 'UNMATCHED')),
    exception_type VARCHAR(20) DEFAULT 'NONE'
        CHECK (exception_type IN ('NONE', 'PARTIAL', 'OVER', 'UNDER', 'LATE', 'FX')),
    
    -- Matching Tracking
    matched_by VARCHAR(100),
    matched_date DATE,
    
    -- Flag
    is_actual_payment BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_payment_invoice ON payment(invoice_id);
CREATE INDEX idx_payment_intent ON payment(intent_id);
CREATE INDEX idx_payment_contract ON payment(contract_id);
CREATE INDEX idx_payment_date ON payment(payment_date);
CREATE INDEX idx_payment_match_status ON payment(match_status);
CREATE INDEX idx_payment_exception ON payment(exception_type);
```

### Reconciliation

```sql
CREATE TABLE reconciliation (
    -- Primary Key
    recon_id VARCHAR(50) PRIMARY KEY,
    
    -- Foreign Key
    contract_id VARCHAR(50) NOT NULL REFERENCES contract(contract_number),
    
    -- Period
    period VARCHAR(7) NOT NULL, -- YYYY-MM
    
    -- Amounts
    total_invoiced DECIMAL(20, 2),
    total_paid DECIMAL(20, 2),
    difference DECIMAL(20, 2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'IDR',
    
    -- Status
    status VARCHAR(20) DEFAULT 'IN_PROGRESS'
        CHECK (status IN ('IN_PROGRESS', 'EXCEPTION', 'READY_TO_CLOSE', 'CLOSED')),
    
    -- Closure
    closed_by VARCHAR(100),
    closed_date DATE,
    remarks TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_reconciliation_contract ON reconciliation(contract_id);
CREATE INDEX idx_reconciliation_period ON reconciliation(period);
CREATE INDEX idx_reconciliation_status ON reconciliation(status);
```

---

## Supporting Tables DDL

### AuditLog

```sql
CREATE TABLE audit_log (
    -- Primary Key
    audit_id BIGSERIAL PRIMARY KEY,
    
    -- Action Details
    action VARCHAR(100) NOT NULL,
    module VARCHAR(20) NOT NULL
        CHECK (module IN ('AUTH', 'DEBTOR', 'DOCUMENT', 'BORDERO', 'INVOICE',
                          'PAYMENT', 'RECONCILIATION', 'CLAIM', 'CONFIG', 'SYSTEM')),
    
    -- Entity
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    
    -- Changes
    old_value TEXT,
    new_value TEXT,
    
    -- User Context
    user_email VARCHAR(100) NOT NULL,
    user_role VARCHAR(20),
    ip_address VARCHAR(45), -- IPv6 compatible
    
    -- Reason
    reason TEXT,
    
    -- Timestamp (automatically set, cannot be modified)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON audit_log(user_email);
CREATE INDEX idx_audit_module ON audit_log(module);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- Partition by month for performance
CREATE TABLE audit_log_y2025m01 PARTITION OF audit_log
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Notification

```sql
CREATE TABLE notification (
    -- Primary Key
    notification_id BIGSERIAL PRIMARY KEY,
    
    -- Content
    title VARCHAR(200),
    message TEXT,
    
    -- Type
    type VARCHAR(20) DEFAULT 'INFO'
        CHECK (type IN ('ACTION_REQUIRED', 'WARNING', 'INFO', 'DECISION')),
    
    -- Module
    module VARCHAR(20)
        CHECK (module IN ('DEBTOR', 'DOCUMENT', 'BORDERO', 'INVOICE', 
                          'PAYMENT', 'RECONCILIATION', 'CLAIM', 'SYSTEM')),
    
    -- Reference
    reference_id VARCHAR(100),
    reference_type VARCHAR(50),
    
    -- Target
    target_role VARCHAR(20) CHECK (target_role IN ('ADMIN', 'BRINS', 'TUGURE', 'ALL')),
    target_user VARCHAR(100),
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    
    -- Action
    action_url TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notification_user ON notification(target_user, is_read);
CREATE INDEX idx_notification_role ON notification(target_role, is_read);
CREATE INDEX idx_notification_type ON notification(type);
CREATE INDEX idx_notification_created ON notification(created_at);
```

### NotificationSetting

```sql
CREATE TABLE notification_setting (
    -- Primary Key
    user_email VARCHAR(100) PRIMARY KEY,
    
    -- User Info
    full_name VARCHAR(200),
    user_role VARCHAR(20) NOT NULL CHECK (user_role IN ('BRINS', 'TUGURE', 'ADMIN')),
    
    -- Contact
    notification_email VARCHAR(100),
    whatsapp_number VARCHAR(20),
    
    -- Channel Preferences
    email_enabled BOOLEAN DEFAULT TRUE,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    
    -- Module Preferences
    notify_batch_status BOOLEAN DEFAULT TRUE,
    notify_record_status BOOLEAN DEFAULT TRUE,
    notify_nota_status BOOLEAN DEFAULT TRUE,
    notify_claim_status BOOLEAN DEFAULT TRUE,
    notify_subrogation_status BOOLEAN DEFAULT TRUE,
    notify_bordero_status BOOLEAN DEFAULT TRUE,
    notify_invoice_status BOOLEAN DEFAULT TRUE,
    notify_reconciliation_status BOOLEAN DEFAULT TRUE,
    notify_payment_received BOOLEAN DEFAULT TRUE,
    notify_approval_required BOOLEAN DEFAULT TRUE,
    notify_document_verification BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notification_setting_role ON notification_setting(user_role);
```

### SlaRule

```sql
CREATE TABLE sla_rule (
    -- Primary Key
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL UNIQUE,
    
    -- Entity
    entity_type VARCHAR(50) NOT NULL
        CHECK (entity_type IN ('Debtor', 'Batch', 'Claim', 'Subrogation',
                               'Nota', 'Invoice', 'Payment', 'Reconciliation')),
    
    -- Trigger
    trigger_condition VARCHAR(50) NOT NULL
        CHECK (trigger_condition IN ('STATUS_DURATION', 'CREATED_DURATION', 
                                      'UPDATED_DURATION', 'DUE_DATE_APPROACHING', 
                                      'DUE_DATE_PASSED')),
    status_value VARCHAR(50),
    duration_value INTEGER,
    duration_unit VARCHAR(10) DEFAULT 'HOURS' CHECK (duration_unit IN ('HOURS', 'DAYS')),
    
    -- Notification
    notification_type VARCHAR(10) DEFAULT 'BOTH' CHECK (notification_type IN ('EMAIL', 'SYSTEM', 'BOTH')),
    recipient_role VARCHAR(20) CHECK (recipient_role IN ('BRINS', 'TUGURE', 'ADMIN', 'ALL')),
    email_subject VARCHAR(200),
    email_body TEXT,
    
    -- Priority
    priority VARCHAR(10) DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_interval INTEGER, -- in hours
    
    -- Tracking
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_sla_entity ON sla_rule(entity_type);
CREATE INDEX idx_sla_active ON sla_rule(is_active);
CREATE INDEX idx_sla_priority ON sla_rule(priority);
```

### EmailTemplate

```sql
CREATE TABLE email_template (
    -- Primary Key
    template_id SERIAL PRIMARY KEY,
    
    -- Object
    object_type VARCHAR(20) NOT NULL
        CHECK (object_type IN ('Batch', 'Record', 'Nota', 'Claim', 'Subrogation')),
    
    -- Status Transition
    status_from VARCHAR(50),
    status_to VARCHAR(50) NOT NULL,
    
    -- Recipient
    recipient_role VARCHAR(20) NOT NULL CHECK (recipient_role IN ('BRINS', 'TUGURE', 'ADMIN', 'ALL')),
    
    -- Template
    email_subject VARCHAR(200) NOT NULL,
    email_body TEXT NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_email_template_object ON email_template(object_type, status_to);
CREATE INDEX idx_email_template_active ON email_template(is_active);
```

### SystemConfig

```sql
CREATE TABLE system_config (
    -- Primary Key
    config_key VARCHAR(100) PRIMARY KEY,
    
    -- Type
    config_type VARCHAR(50) NOT NULL
        CHECK (config_type IN ('STATUS_REFERENCE', 'ELIGIBILITY_RULE', 
                               'FINANCIAL_THRESHOLD', 'APPROVAL_MATRIX',
                               'NOTIFICATION_RULE', 'NOTIFICATION_CHANNEL')),
    
    -- Value
    config_value TEXT NOT NULL,
    description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE,
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'APPROVED'
        CHECK (status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_system_config_type ON system_config(config_type);
CREATE INDEX idx_system_config_active ON system_config(is_active);
```

---

## Views for Common Queries

### Batch Summary View

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
    b.total_exposure,
    b.total_premium,
    b.final_exposure_amount,
    b.final_premium_amount,
    b.debtor_review_completed,
    b.batch_ready_for_nota,
    b.operational_locked,
    COUNT(DISTINCT d.cover_id) as actual_debtor_count,
    SUM(CASE WHEN r.record_status = 'Accepted' THEN 1 ELSE 0 END) as accepted_count,
    SUM(CASE WHEN r.record_status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count,
    n.nota_number,
    n.amount as nota_amount,
    n.status as nota_status
FROM batch b
LEFT JOIN contract c ON b.contract_id = c.contract_number
LEFT JOIN debtor d ON b.batch_id = d.batch_id
LEFT JOIN record r ON b.batch_id = r.batch_id AND d.cover_id = r.debtor_id
LEFT JOIN nota n ON b.batch_id = n.reference_id AND n.nota_type = 'Batch'
GROUP BY b.batch_id, c.contract_name, n.nota_number, n.amount, n.status;
```

### Payment Reconciliation View

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
    SUM(p.amount) as total_payments,
    STRING_AGG(p.payment_ref, ', ') as payment_refs
FROM nota n
LEFT JOIN payment p ON n.nota_number = p.invoice_id
GROUP BY n.nota_number, n.nota_type, n.amount, n.total_actual_paid, n.reconciliation_status;
```

### Claim Pipeline View

```sql
CREATE VIEW v_claim_pipeline AS
SELECT 
    c.claim_no,
    c.status,
    c.nama_tertanggung,
    c.nilai_klaim,
    c.share_tugure_amount,
    d.nomor_peserta,
    d.nama_peserta,
    ct.contract_name,
    n.nota_number,
    n.status as nota_status,
    CASE 
        WHEN c.status = 'Paid' AND s.subrogation_id IS NOT NULL THEN 'Subrogation Created'
        WHEN c.status = 'Paid' THEN 'Completed'
        ELSE 'In Progress'
    END as overall_status
FROM claim c
LEFT JOIN debtor d ON c.debtor_id = d.cover_id
LEFT JOIN contract ct ON c.contract_id = ct.contract_number
LEFT JOIN nota n ON c.claim_no = n.reference_id AND n.nota_type = 'Claim'
LEFT JOIN subrogation s ON c.claim_no = s.claim_id;
```

---

## Triggers for Auto-Update

### Update Timestamps

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables
CREATE TRIGGER trg_batch_update BEFORE UPDATE ON batch
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_debtor_update BEFORE UPDATE ON debtor
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ... (apply to all other tables)
```

### Lock Debtors on Batch Close

```sql
CREATE OR REPLACE FUNCTION lock_debtors_on_batch_close()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'Closed' AND OLD.status != 'Closed' THEN
        UPDATE debtor 
        SET is_locked = TRUE 
        WHERE batch_id = NEW.batch_id;
        
        NEW.operational_locked = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lock_debtors 
BEFORE UPDATE ON batch
FOR EACH ROW 
EXECUTE FUNCTION lock_debtors_on_batch_close();
```

### Auto-Calculate Outstanding Amount

```sql
CREATE OR REPLACE FUNCTION calculate_outstanding()
RETURNS TRIGGER AS $$
BEGIN
    NEW.outstanding_amount = NEW.total_amount - NEW.paid_amount;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invoice_outstanding 
BEFORE INSERT OR UPDATE ON invoice
FOR EACH ROW 
EXECUTE FUNCTION calculate_outstanding();
```

---

## Database Maintenance Scripts

### Vacuum and Analyze

```sql
-- Run weekly
VACUUM ANALYZE batch;
VACUUM ANALYZE debtor;
VACUUM ANALYZE payment;
VACUUM ANALYZE audit_log;
```

### Archive Old Data

```sql
-- Archive batches older than 2 years
CREATE TABLE batch_archive (LIKE batch INCLUDING ALL);

INSERT INTO batch_archive 
SELECT * FROM batch 
WHERE closed_date < CURRENT_DATE - INTERVAL '2 years' 
AND status = 'Closed';

DELETE FROM batch 
WHERE closed_date < CURRENT_DATE - INTERVAL '2 years' 
AND status = 'Closed';
```

---

## Performance Tuning Recommendations

1. **Partitioning**
   - Partition `audit_log` by month
   - Partition `payment` by year
   - Partition `batch` by year

2. **Materialized Views**
   - Create materialized views for dashboards
   - Refresh daily or on-demand

3. **Connection Pooling**
   - Use PgBouncer for connection pooling
   - Recommended pool size: 50-100

4. **Query Optimization**
   - Use EXPLAIN ANALYZE for slow queries
   - Add indexes based on actual query patterns
   - Avoid SELECT * in production code

5. **Caching Strategy**
   - Cache reference data (contracts, configs)
   - Use Redis for session data
   - Cache commonly accessed reports

---

**Version**: 1.0  
**Database**: PostgreSQL 14+  
**Last Updated**: 2025-01-22
