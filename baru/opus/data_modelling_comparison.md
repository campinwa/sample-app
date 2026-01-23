# Data Modelling: Workflow Lama vs Workflow Baru
## Sistem Reasuransi BRINS - TUGURE (A3M)

---

## Daftar Isi
1. [Executive Summary](#1-executive-summary)
2. [Perbandingan Alur Workflow](#2-perbandingan-alur-workflow)
3. [Data Model - Workflow Lama](#3-data-model---workflow-lama)
4. [Data Model - Workflow Baru](#4-data-model---workflow-baru)
5. [Entity Relationship Diagrams](#5-entity-relationship-diagrams)
6. [State Diagrams](#6-state-diagrams)
7. [Perbandingan Schema](#7-perbandingan-schema)

---

## 1. Executive Summary

### Perbedaan Utama

| Aspek | Workflow Lama | Workflow Baru |
|-------|---------------|---------------|
| **Inisiasi Nota** | Nota Premi dibuat terlebih dahulu oleh BRINS, kemudian batch debitur dikirim terpisah | Batch debitur dikumpulkan dulu (3 batch), baru generate Nota di akhir bulan |
| **Sumber Data Batch** | BRINS langsung submit batch | BSM (Broker) kirim data ke BRINS per batch |
| **Urutan Proses** | Nota → Batch → Validation | Batch (3x) → Nota Generation |
| **Nota Status** | Nota bisa ditolak → revisi → upload ulang | Nota mengikuti revisi batch (auto-update) |
| **Kompleksitas** | Lebih kompleks (nota terpisah dari batch) | Lebih sederhana (nota derived dari batch) |

---

## 2. Perbandingan Alur Workflow

### 2.1 Workflow Lama - Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant BRINS
    participant System
    participant TUGURE
    
    rect rgb(230, 240, 255)
    note right of BRINS: 1. Master Contract
    BRINS->>System: Submit Master Contract
    System->>TUGURE: Forward for Review
    alt Contract Approved
        TUGURE->>System: Approve Contract
        System->>BRINS: Confirmation
    else Contract Rejected
        TUGURE->>System: Reject Contract
        System->>BRINS: Request Revision
        BRINS->>System: Resubmit Contract
    end
    end

    rect rgb(255, 240, 230)
    note right of BRINS: 2. Draft Nota Premi (Dibuat Duluan)
    BRINS->>System: Create Nota Premi (ref to contract)
    System->>TUGURE: Send Nota for Review
    alt Nota Approved
        TUGURE->>System: Approve Nota
        System->>BRINS: Confirmation
    else Nota Rejected
        TUGURE->>System: Reject Nota
        System->>BRINS: Request Revision
        BRINS->>System: Revise & Upload Nota
    end
    end

    rect rgb(240, 255, 240)
    note right of BRINS: 3. Batch Debitur (1 Nota = 3 Batch)
    loop 3 Batches
        BRINS->>System: Submit Batch Debitur
        System->>System: Validate vs Master Contract
        System->>TUGURE: Forward for Review
        alt Batch Approved
            TUGURE->>System: Approve Batch
            System->>System: Add to Nota
        else Batch Rejected
            TUGURE->>System: Reject Batch
            System->>BRINS: Request Revision
            BRINS->>System: Revise & Reupload Batch
        end
    end
    System->>System: Generate Nota Final (after 3 batches closed)
    System->>BRINS: Nota Final Ready
    end

    rect rgb(255, 255, 230)
    note right of BRINS: 4. Pembayaran Premi
    BRINS->>System: Submit Payment
    System->>TUGURE: Verify Payment
    TUGURE->>System: Reconciliation
    alt Payment Matched
        System->>System: Mark Nota "Fully Paid"
    else Payment Exception
        System->>BRINS: Notify Exception
        BRINS->>System: Confirm Exception
        TUGURE->>System: Generate DN/CN
        System->>BRINS: DN/CN for Verification
    end
    end
```

### 2.2 Workflow Baru - Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant BSM as BSM (Broker)
    participant BRINS
    participant System
    participant TUGURE
    participant Finance as BRINS Finance
    
    rect rgb(230, 240, 255)
    note right of BRINS: 1. Master Contract
    BRINS->>System: Submit Master Contract
    System->>TUGURE: Forward for Review
    alt Contract Approved
        TUGURE->>System: Acknowledge Contract
    else Contract Rejected
        TUGURE->>System: Reject with Notes
        BRINS->>System: Revise Contract
    end
    end

    rect rgb(240, 255, 240)
    note right of BSM: 2. Batch Collection (Batch Dikumpulkan Dulu)
    BSM->>BRINS: Send Batch 1 Data Debitur
    BRINS->>BRINS: Review Batch 1
    BSM->>BRINS: Send Batch 2 Data Debitur
    BRINS->>BRINS: Review Batch 2
    BSM->>BRINS: Send Batch 3 Data Debitur
    BRINS->>BRINS: Review Batch 3
    
    Note over BRINS: Kumpulkan sampai 3 batch lengkap
    end

    rect rgb(255, 240, 230)
    note right of BRINS: 3. Generate Nota (Setelah 3 Batch Terkumpul)
    BRINS->>System: Submit Combined Batch (3 batches)
    System->>System: Generate Nota per Bulan
    System->>TUGURE: Send Nota + Batch for Review
    System->>Finance: Notify Nota Generated
    
    alt TUGURE Accepts
        TUGURE->>System: Approve with Remarks
    else TUGURE Requests Revision
        TUGURE->>System: Add Remarks/Notes
        System->>BRINS: Request Batch Revision
        BRINS->>System: Revise & Reupload Batch
        System->>System: Auto-Update Nota (mengikuti batch)
    end
    end

    rect rgb(255, 255, 230)
    note right of BRINS: 4. Pembayaran & Rekonsiliasi
    BRINS->>System: Submit Payment (sesuai Nota Final)
    System->>TUGURE: Verify Payment
    TUGURE->>System: Reconciliation
    alt Payment Matched
        System->>System: Mark "Fully Paid"
    else Payment Difference
        System->>BRINS: Exception Notification
        BRINS->>System: Confirm Exception
        TUGURE->>System: Generate DN/CN
        BRINS->>System: Verify DN/CN
    end
    end
```

---

## 3. Data Model - Workflow Lama

### 3.1 Entity Overview

```mermaid
erDiagram
    MASTER_CONTRACT_LAMA ||--o{ NOTA_PREMI_LAMA : "has"
    NOTA_PREMI_LAMA ||--o{ BATCH_LAMA : "contains"
    BATCH_LAMA ||--o{ DEBTOR_LAMA : "has"
    BATCH_LAMA ||--o{ RECORD_LAMA : "has"
    NOTA_PREMI_LAMA ||--o{ PAYMENT_LAMA : "receives"
    NOTA_PREMI_LAMA ||--o{ DN_CN_LAMA : "adjusts"
    MASTER_CONTRACT_LAMA ||--o{ CLAIM_LAMA : "covers"
    CLAIM_LAMA ||--o{ SUBROGATION_LAMA : "triggers"
    DEBTOR_LAMA ||--o{ CLAIM_LAMA : "filed_by"
    
    MASTER_CONTRACT_LAMA {
        string contract_id PK
        string contract_number
        string policy_no
        string cedant
        string reinsurer
        string credit_type
        date effective_start
        date effective_end
        string status
        number coverage_percentage
        number premium_rate
    }
    
    NOTA_PREMI_LAMA {
        string nota_id PK
        string contract_id FK
        string nota_number
        string period
        number draft_amount
        number final_amount
        string status
        date created_date
        date approved_date
        boolean is_final
    }
    
    BATCH_LAMA {
        string batch_id PK
        string nota_id FK
        number batch_sequence
        number total_records
        number total_exposure
        number total_premium
        string status
        date submitted_date
        date approved_date
    }
    
    DEBTOR_LAMA {
        string debtor_id PK
        string batch_id FK
        string nomor_peserta
        string nama_peserta
        number plafon
        number nominal_premi
        string status
    }
```

### 3.2 Schema Detail - Workflow Lama

#### MasterContract_Lama
```json
{
  "name": "MasterContract_Lama",
  "description": "Master Contract entity for old workflow",
  "properties": {
    "contract_id": { "type": "string", "description": "Primary Key" },
    "contract_number": { "type": "string" },
    "policy_no": { "type": "string" },
    "cedant": { "type": "string", "enum": ["BRINS"] },
    "reinsurer": { "type": "string", "enum": ["TUGURE"] },
    "credit_type": { "type": "string", "enum": ["Individual", "Corporate"] },
    "effective_start": { "type": "date" },
    "effective_end": { "type": "date" },
    "status": { 
      "type": "string", 
      "enum": ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "ACTIVE", "EXPIRED"]
    },
    "coverage_percentage": { "type": "number" },
    "premium_rate": { "type": "number" },
    "commission_rate": { "type": "number" },
    "max_plafon": { "type": "number" },
    "approved_by": { "type": "string" },
    "approved_date": { "type": "date" }
  }
}
```

#### NotaPremi_Lama (Dibuat Sebelum Batch)
```json
{
  "name": "NotaPremi_Lama",
  "description": "Nota Premi dibuat terlebih dahulu sebelum batch debitur",
  "properties": {
    "nota_id": { "type": "string", "description": "Primary Key" },
    "contract_id": { "type": "string", "description": "FK to MasterContract" },
    "nota_number": { "type": "string" },
    "period": { "type": "string", "format": "YYYY-MM" },
    "draft_amount": { "type": "number", "description": "Estimasi awal sebelum batch" },
    "final_amount": { "type": "number", "description": "Final setelah 3 batch closed" },
    "status": {
      "type": "string",
      "enum": ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "REVISION_REQUIRED", "FINAL", "PAID"]
    },
    "created_by": { "type": "string" },
    "created_date": { "type": "date" },
    "submitted_date": { "type": "date" },
    "reviewed_by": { "type": "string" },
    "reviewed_date": { "type": "date" },
    "approved_by": { "type": "string" },
    "approved_date": { "type": "date" },
    "rejection_reason": { "type": "string" },
    "revision_count": { "type": "number", "default": 0 },
    "is_final": { "type": "boolean", "default": false }
  }
}
```

#### Batch_Lama (Dikaitkan ke Nota yang Sudah Ada)
```json
{
  "name": "Batch_Lama",
  "description": "Batch debitur yang dikaitkan ke Nota yang sudah dibuat",
  "properties": {
    "batch_id": { "type": "string", "description": "Primary Key" },
    "nota_id": { "type": "string", "description": "FK to NotaPremi (already exists)" },
    "batch_sequence": { "type": "number", "description": "1, 2, or 3" },
    "total_records": { "type": "number" },
    "total_exposure": { "type": "number" },
    "total_premium": { "type": "number" },
    "status": {
      "type": "string",
      "enum": ["UPLOADED", "VALIDATED", "UNDER_REVIEW", "APPROVED", "REJECTED", "CLOSED"]
    },
    "submitted_by": { "type": "string" },
    "submitted_date": { "type": "date" },
    "validated_date": { "type": "date" },
    "reviewed_by": { "type": "string" },
    "reviewed_date": { "type": "date" },
    "approved_by": { "type": "string" },
    "approved_date": { "type": "date" },
    "rejection_reason": { "type": "string" }
  }
}
```

### 3.3 State Flow - Workflow Lama

#### Nota Status Flow (Lama)

```mermaid
stateDiagram-v2
    [*] --> DRAFT: BRINS creates Nota first
    DRAFT --> SUBMITTED: Submit to System
    SUBMITTED --> UNDER_REVIEW: Forward to TUGURE
    UNDER_REVIEW --> APPROVED: TUGURE approves
    UNDER_REVIEW --> REJECTED: TUGURE rejects
    REJECTED --> REVISION_REQUIRED: Need changes
    REVISION_REQUIRED --> DRAFT: BRINS revises
    APPROVED --> WAITING_BATCH: Waiting for batches
    WAITING_BATCH --> BATCH_1_ADDED: Batch 1 approved
    BATCH_1_ADDED --> BATCH_2_ADDED: Batch 2 approved
    BATCH_2_ADDED --> BATCH_3_ADDED: Batch 3 approved
    BATCH_3_ADDED --> FINAL: Generate Final Nota
    FINAL --> PAID: Payment received
    PAID --> [*]
```

#### Batch Status Flow (Lama)

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: BRINS uploads batch
    UPLOADED --> VALIDATED: System validates vs Master Contract
    VALIDATED --> UNDER_REVIEW: Forward to TUGURE
    UNDER_REVIEW --> APPROVED: TUGURE approves
    UNDER_REVIEW --> REJECTED: TUGURE rejects
    REJECTED --> UPLOADED: BRINS revises & reuploads
    APPROVED --> ADDED_TO_NOTA: Add to existing Nota
    ADDED_TO_NOTA --> CLOSED: Finalized
    CLOSED --> [*]
```

---

## 4. Data Model - Workflow Baru

### 4.1 Entity Overview

```mermaid
erDiagram
    MASTER_CONTRACT_BARU ||--o{ BATCH_BARU : "covers"
    BATCH_BARU ||--o{ DEBTOR_BARU : "contains"
    BATCH_BARU ||--o{ RECORD_BARU : "has"
    BATCH_BARU }o--|| NOTA_BARU : "aggregates_to"
    NOTA_BARU ||--o{ PAYMENT_BARU : "receives"
    NOTA_BARU ||--o{ DN_CN_BARU : "adjusts"
    MASTER_CONTRACT_BARU ||--o{ CLAIM_BARU : "covers"
    CLAIM_BARU ||--o{ SUBROGATION_BARU : "triggers"
    DEBTOR_BARU ||--o{ CLAIM_BARU : "filed_by"
    
    MASTER_CONTRACT_BARU {
        string contract_id PK
        string contract_number
        string policy_no
        string program_id
        string loan_type
        date coverage_start
        date coverage_end
        string effective_status
        number share_tugure_percentage
        number premium_rate
        number version
    }
    
    BATCH_BARU {
        string batch_id PK
        string contract_id FK
        number batch_month
        number batch_year
        number total_records
        number total_exposure
        number total_premium
        number final_exposure_amount
        number final_premium_amount
        boolean debtor_review_completed
        boolean batch_ready_for_nota
        string status
    }
    
    NOTA_BARU {
        string nota_number PK
        string nota_type
        string reference_id
        string contract_id FK
        number amount
        string status
        boolean is_immutable
        string reconciliation_status
    }
    
    DEBTOR_BARU {
        string debtor_id PK
        string batch_id FK
        string contract_id FK
        string nomor_peserta
        string nama_peserta
        number plafon
        number nominal_premi
        number net_premi
        string status
        number version_no
    }
```

### 4.2 Schema Detail - Workflow Baru

#### MasterContract_Baru (Enhanced)
```json
{
  "name": "MasterContract_Baru",
  "description": "Master Contract dengan validation matrix terintegrasi",
  "properties": {
    "contract_id": { "type": "string", "description": "Primary Key" },
    "policy_no": { "type": "string" },
    "program_id": { "type": "string" },
    "product_type": { "type": "string", "enum": ["Treaty", "Facultative", "Retro"] },
    "credit_type": { "type": "string", "enum": ["Individual", "Corporate"] },
    "loan_type": { "type": "string" },
    "loan_type_desc": { "type": "string" },
    "coverage_start_date": { "type": "date" },
    "coverage_end_date": { "type": "date" },
    "max_tenor_month": { "type": "number" },
    "max_plafond": { "type": "number" },
    "share_tugure_percentage": { "type": "number" },
    "premium_rate": { "type": "number" },
    "ric_rate": { "type": "number" },
    "bf_rate": { "type": "number" },
    "allowed_kolektabilitas": { "type": "string", "description": "Comma-separated values" },
    "allowed_region": { "type": "string" },
    "effective_status": {
      "type": "string",
      "enum": ["Draft", "Pending First Approval", "Pending Second Approval", "Active", "Inactive", "Archived"]
    },
    "version": { "type": "number", "default": 1 },
    "parent_contract_id": { "type": "string", "description": "For versioning" },
    "first_approved_by": { "type": "string" },
    "first_approved_date": { "type": "datetime" },
    "second_approved_by": { "type": "string" },
    "second_approved_date": { "type": "datetime" }
  }
}
```

#### Batch_Baru (Batch Dikumpulkan Dulu, Nota Auto-Generate)
```json
{
  "name": "Batch_Baru",
  "description": "Batch dari BSM dikumpulkan dulu, nota di-generate setelah 3 batch",
  "properties": {
    "batch_id": { "type": "string", "description": "Primary Key" },
    "batch_month": { "type": "number", "description": "1-12" },
    "batch_year": { "type": "number" },
    "contract_id": { "type": "string", "description": "FK to MasterContract" },
    "total_records": { "type": "number", "default": 0 },
    "total_exposure": { "type": "number", "default": 0, "description": "Raw from upload" },
    "total_premium": { "type": "number", "default": 0, "description": "Raw from upload" },
    "final_exposure_amount": { "type": "number", "default": 0, "description": "After debtor review (approved only)" },
    "final_premium_amount": { "type": "number", "default": 0, "description": "After debtor review (approved only)" },
    "debtor_review_completed": { "type": "boolean", "default": false },
    "batch_ready_for_nota": { "type": "boolean", "default": false, "description": "TRUE after review with >=1 approved debtor" },
    "status": {
      "type": "string",
      "enum": ["Uploaded", "Validated", "Matched", "Approved", "Nota Issued", "Branch Confirmed", "Paid", "Closed", "Rejected", "Reopen Requested", "Reopened"]
    },
    "operational_locked": { "type": "boolean", "default": false, "description": "TRUE when Batch Closed" },
    "reopen_requested_by": { "type": "string" },
    "reopen_reason": { "type": "string" },
    "reopen_impact": { "type": "string", "enum": ["Data", "Financial"] },
    "validated_by": { "type": "string" },
    "validated_date": { "type": "date" },
    "matched_by": { "type": "string" },
    "matched_date": { "type": "date" },
    "approved_by": { "type": "string" },
    "approved_date": { "type": "date" },
    "nota_issued_by": { "type": "string" },
    "nota_issued_date": { "type": "date" },
    "branch_confirmed_by": { "type": "string" },
    "branch_confirmed_date": { "type": "date" },
    "paid_by": { "type": "string" },
    "paid_date": { "type": "date" },
    "closed_by": { "type": "string" },
    "closed_date": { "type": "date" }
  }
}
```

#### Nota_Baru (Auto-Generated dari Batch)
```json
{
  "name": "Nota_Baru",
  "description": "Nota yang di-generate otomatis setelah 3 batch terkumpul",
  "properties": {
    "nota_number": { "type": "string", "description": "Primary Key" },
    "nota_type": { "type": "string", "enum": ["Batch", "Claim", "Subrogation"] },
    "reference_id": { "type": "string", "description": "ID of related Batch/Claim/Subrogation" },
    "contract_id": { "type": "string", "description": "FK to Contract" },
    "amount": { "type": "number", "description": "IMMUTABLE after Issued - derived from final_premium_amount" },
    "currency": { "type": "string", "default": "IDR" },
    "status": {
      "type": "string",
      "enum": ["Draft", "Issued", "Confirmed", "Paid"]
    },
    "issued_by": { "type": "string" },
    "issued_date": { "type": "date" },
    "confirmed_by": { "type": "string" },
    "confirmed_date": { "type": "date" },
    "paid_date": { "type": "date" },
    "payment_reference": { "type": "string" },
    "total_actual_paid": { "type": "number", "default": 0 },
    "reconciliation_status": {
      "type": "string",
      "enum": ["PENDING", "PARTIAL", "MATCHED", "OVERPAID", "FINAL"]
    },
    "is_immutable": { "type": "boolean", "default": false, "description": "TRUE after Issued" }
  }
}
```

#### Debtor_Baru (Enhanced with Validation)
```json
{
  "name": "Debtor_Baru",
  "description": "Data debitur dari BSM dengan validasi terhadap master contract",
  "properties": {
    "debtor_id": { "type": "string", "description": "Auto-generated" },
    "cover_id": { "type": "number" },
    "program_id": { "type": "string" },
    "batch_id": { "type": "string", "description": "FK to Batch" },
    "contract_id": { "type": "string", "description": "FK to MasterContract" },
    "nomor_rekening_pinjaman": { "type": "string" },
    "nomor_peserta": { "type": "string" },
    "loan_type": { "type": "string" },
    "loan_type_desc": { "type": "string" },
    "tanggal_mulai_covering": { "type": "date" },
    "tanggal_akhir_covering": { "type": "date" },
    "plafon": { "type": "number" },
    "nominal_premi": { "type": "number" },
    "premi_percentage": { "type": "number" },
    "ric_percentage": { "type": "number" },
    "bf_percentage": { "type": "number" },
    "net_premi": { "type": "number" },
    "unit_code": { "type": "string" },
    "unit_desc": { "type": "string" },
    "branch_desc": { "type": "string" },
    "region_desc": { "type": "string" },
    "nama_peserta": { "type": "string" },
    "alamat_usaha": { "type": "string" },
    "kolektabilitas": { "type": "number", "description": "1-5" },
    "flag_restruktur": { "type": "number", "description": "0/1" },
    "status_aktif": { "type": "number", "description": "0/1" },
    "version_no": { "type": "number", "default": 1 },
    "status": {
      "type": "string",
      "enum": ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "CONDITIONAL"]
    },
    "is_locked": { "type": "boolean", "default": false },
    "rejection_reason": { "type": "string" },
    "validation_remarks": { "type": "string" }
  }
}
```

### 4.3 State Flow - Workflow Baru

#### Batch Status Flow (Baru)

```mermaid
stateDiagram-v2
    [*] --> Uploaded: BSM sends to BRINS, BRINS uploads
    Uploaded --> Validated: System validates vs Master Contract
    Validated --> Matched: Match with contract rules
    Matched --> Approved: TUGURE approves
    Matched --> Rejected: TUGURE rejects
    Rejected --> Uploaded: Revise & reupload
    
    note right of Approved: Wait for 3 batches
    Approved --> Nota_Issued: 3 batches complete → Generate Nota
    Nota_Issued --> Branch_Confirmed: BRINS Finance confirms
    Branch_Confirmed --> Paid: Payment received
    Paid --> Closed: Reconciliation complete
    Closed --> [*]
    
    Closed --> Reopen_Requested: Request reopen
    Reopen_Requested --> Reopened: Supervisor approves
    Reopened --> Uploaded: Back to revision
```

#### Nota Status Flow (Baru - Auto Generated)

```mermaid
stateDiagram-v2
    [*] --> Draft: Auto-created when 3 batches collected
    Draft --> Issued: TUGURE issues nota
    
    note right of Issued: Amount becomes IMMUTABLE
    Issued --> Confirmed: BRINS confirms
    Confirmed --> Paid: Payment matched
    
    Paid --> [*]: Reconciliation complete
    
    note left of Confirmed: If batch revised
    Confirmed --> Draft: Nota auto-updates with batch changes
```

#### Claim Status Flow (Baru)

```mermaid
stateDiagram-v2
    [*] --> Draft: BRINS uploads claim
    Draft --> Checked: System validates vs Master Contract
    Checked --> Doc_Verified: Document verification
    Doc_Verified --> Invoiced: Generate Claim Nota
    Invoiced --> Paid: TUGURE pays claim
    Paid --> [*]
    
    Draft --> Rejected: Validation fails
    Checked --> Rejected: Check fails
    Rejected --> Draft: Revise & resubmit
```

#### Subrogation Status Flow (Baru)

```mermaid
stateDiagram-v2
    [*] --> Draft: BRINS submits subrogation (ref to claim)
    Draft --> Invoiced: System validates, TUGURE approves
    Invoiced --> Paid_Closed: Payment complete
    Paid_Closed --> [*]
    
    Draft --> Rejected: Validation fails
    Rejected --> Draft: Revise & resubmit
```

---

## 5. Entity Relationship Diagrams

### 5.1 Complete ER Diagram - Workflow Lama

```mermaid
erDiagram
    MASTER_CONTRACT_LAMA ||--o{ NOTA_PREMI_LAMA : "1:N creates"
    NOTA_PREMI_LAMA ||--o{ BATCH_LAMA : "1:N contains"
    BATCH_LAMA ||--o{ DEBTOR_LAMA : "1:N has"
    BATCH_LAMA ||--o{ RECORD_LAMA : "1:N tracks"
    NOTA_PREMI_LAMA ||--o{ PAYMENT_LAMA : "1:N receives"
    NOTA_PREMI_LAMA ||--o{ DN_CN_LAMA : "1:N adjusted_by"
    DEBTOR_LAMA ||--o{ CLAIM_LAMA : "1:N files"
    CLAIM_LAMA ||--o{ SUBROGATION_LAMA : "1:N triggers"
    MASTER_CONTRACT_LAMA ||--o{ CLAIM_LAMA : "1:N covers"
    
    MASTER_CONTRACT_LAMA {
        string contract_id PK
        string contract_number UK
        string policy_no
        string cedant
        string reinsurer
        date effective_start
        date effective_end
        string status
    }
    
    NOTA_PREMI_LAMA {
        string nota_id PK
        string nota_number UK
        string contract_id FK
        string period
        number draft_amount
        number final_amount
        string status
        boolean is_final
    }
    
    BATCH_LAMA {
        string batch_id PK
        string nota_id FK
        number batch_sequence
        number total_records
        number total_premium
        string status
    }
    
    DEBTOR_LAMA {
        string debtor_id PK
        string batch_id FK
        string nomor_peserta
        string nama_peserta
        number plafon
        number nominal_premi
        string status
    }
    
    RECORD_LAMA {
        string record_id PK
        string batch_id FK
        string debtor_id FK
        string record_status
        number exposure_amount
        number premium_amount
    }
    
    PAYMENT_LAMA {
        string payment_id PK
        string nota_id FK
        string payment_ref
        number amount
        date payment_date
        string match_status
    }
    
    DN_CN_LAMA {
        string note_id PK
        string nota_id FK
        string note_type
        number adjustment_amount
        string reason_code
        string status
    }
    
    CLAIM_LAMA {
        string claim_id PK
        string debtor_id FK
        string contract_id FK
        string claim_no
        number nilai_klaim
        string status
    }
    
    SUBROGATION_LAMA {
        string subro_id PK
        string claim_id FK
        number recovery_amount
        string status
    }
```

### 5.2 Complete ER Diagram - Workflow Baru

```mermaid
erDiagram
    MASTER_CONTRACT_BARU ||--o{ BATCH_BARU : "1:N covers"
    BATCH_BARU ||--o{ DEBTOR_BARU : "1:N contains"
    BATCH_BARU ||--o{ RECORD_BARU : "1:N tracks"
    BATCH_BARU }o--|| NOTA_BARU : "N:1 aggregates_to"
    NOTA_BARU ||--o{ PAYMENT_BARU : "1:N receives"
    NOTA_BARU ||--o{ DN_CN_BARU : "1:N adjusted_by"
    DEBTOR_BARU ||--o{ CLAIM_BARU : "1:N files"
    CLAIM_BARU ||--|| NOTA_CLAIM : "1:1 generates"
    CLAIM_BARU ||--o{ SUBROGATION_BARU : "1:N triggers"
    SUBROGATION_BARU ||--|| NOTA_SUBRO : "1:1 generates"
    MASTER_CONTRACT_BARU ||--o{ CLAIM_BARU : "1:N covers"
    MASTER_CONTRACT_BARU ||--o{ VALIDATION_RULE : "1:N defines"
    
    MASTER_CONTRACT_BARU {
        string contract_id PK
        string policy_no UK
        string program_id
        string loan_type
        date coverage_start_date
        date coverage_end_date
        number share_tugure_percentage
        number premium_rate
        string effective_status
        number version
    }
    
    VALIDATION_RULE {
        string rule_id PK
        string contract_id FK
        string rule_name
        string logic_rule
        string fail_action
        string severity
    }
    
    BATCH_BARU {
        string batch_id PK
        string contract_id FK
        number batch_month
        number batch_year
        number total_records
        number final_premium_amount
        boolean debtor_review_completed
        boolean batch_ready_for_nota
        string status
        boolean operational_locked
    }
    
    DEBTOR_BARU {
        string debtor_id PK
        string batch_id FK
        string contract_id FK
        string nomor_peserta UK
        string nama_peserta
        number plafon
        number nominal_premi
        number net_premi
        number kolektabilitas
        string status
        number version_no
    }
    
    RECORD_BARU {
        string record_id PK
        string batch_id FK
        string debtor_id FK
        string record_status
        number exposure_amount
        number premium_amount
    }
    
    NOTA_BARU {
        string nota_number PK
        string nota_type
        string reference_id FK
        string contract_id FK
        number amount
        string status
        boolean is_immutable
        string reconciliation_status
    }
    
    NOTA_CLAIM {
        string nota_number PK
        string claim_id FK
        number amount
        string status
    }
    
    NOTA_SUBRO {
        string nota_number PK
        string subro_id FK
        number amount
        string status
    }
    
    PAYMENT_BARU {
        string payment_id PK
        string nota_number FK
        string payment_ref
        number amount
        date payment_date
        string match_status
        string exception_type
    }
    
    DN_CN_BARU {
        string note_number PK
        string nota_number FK
        string note_type
        number adjustment_amount
        string reason_code
        string status
    }
    
    CLAIM_BARU {
        string claim_no PK
        string debtor_id FK
        string contract_id FK
        string policy_no
        string nomor_sertifikat
        number nilai_klaim
        number share_tugure_amount
        string status
        boolean check_bdo_premi
    }
    
    SUBROGATION_BARU {
        string subro_id PK
        string claim_id FK
        string debtor_id FK
        number recovery_amount
        string status
    }
```

---

## 6. State Diagrams

### 6.1 Complete Process Flow - Workflow Lama

```mermaid
flowchart TB
    subgraph MC["1. Master Contract"]
        MC1[BRINS Create Contract] --> MC2[Submit to System]
        MC2 --> MC3{TUGURE Review}
        MC3 -->|Approved| MC4[Contract Active]
        MC3 -->|Rejected| MC5[Revise Contract]
        MC5 --> MC2
    end
    
    subgraph NP["2. Nota Premi (Dibuat Duluan)"]
        NP1[BRINS Create Nota Premi] --> NP2[Submit to TUGURE]
        NP2 --> NP3{TUGURE Review}
        NP3 -->|Approved| NP4[Nota Approved]
        NP3 -->|Rejected| NP5[Revise Nota]
        NP5 --> NP2
    end
    
    subgraph BD["3. Batch Debitur (Setelah Nota)"]
        BD1[Upload Batch 1] --> BD2[Validate vs Contract]
        BD2 --> BD3{TUGURE Review}
        BD3 -->|Approved| BD4[Add to Nota]
        BD3 -->|Rejected| BD5[Revise Batch]
        BD5 --> BD1
        BD4 --> BD6[Upload Batch 2]
        BD6 --> BD7[Validate & Review]
        BD7 --> BD8[Upload Batch 3]
        BD8 --> BD9[All 3 Batches Closed]
        BD9 --> BD10[Generate Nota Final]
    end
    
    subgraph PAY["4. Payment"]
        PAY1[BRINS Pay Premium] --> PAY2[TUGURE Verify]
        PAY2 --> PAY3{Reconciliation}
        PAY3 -->|Match| PAY4[Fully Paid]
        PAY3 -->|Exception| PAY5[Generate DN/CN]
        PAY5 --> PAY6[BRINS Verify DN/CN]
    end
    
    MC4 --> NP1
    NP4 --> BD1
    BD10 --> PAY1
```

### 6.2 Complete Process Flow - Workflow Baru

```mermaid
flowchart TB
    subgraph MC["1. Master Contract"]
        MC1[BRINS Submit Contract] --> MC2{TUGURE Review}
        MC2 -->|Acknowledged| MC3[Contract Active]
        MC2 -->|Rejected| MC4[Revise & Resubmit]
        MC4 --> MC1
    end
    
    subgraph BC["2. Batch Collection (BSM → BRINS)"]
        BC1[BSM Send Batch 1] --> BC2[BRINS Review]
        BC2 --> BC3[BSM Send Batch 2]
        BC3 --> BC4[BRINS Review]
        BC4 --> BC5[BSM Send Batch 3]
        BC5 --> BC6[BRINS Review]
        BC6 --> BC7{3 Batches Complete?}
        BC7 -->|Yes| BC8[Submit Combined to System]
    end
    
    subgraph NG["3. Nota Generation (Auto)"]
        NG1[System Validates All Batches] --> NG2[Generate Nota per Bulan]
        NG2 --> NG3[Send to TUGURE + Finance]
        NG3 --> NG4{TUGURE Review}
        NG4 -->|Accept| NG5[Nota Issued]
        NG4 -->|Remarks| NG6[Request Batch Revision]
        NG6 --> NG7[BRINS Revise Batch]
        NG7 --> NG8[Nota Auto-Updates]
        NG8 --> NG4
    end
    
    subgraph PAY["4. Payment & Reconciliation"]
        PAY1[BRINS Pay per Nota Final] --> PAY2[TUGURE Verify & Reconcile]
        PAY2 --> PAY3{Match?}
        PAY3 -->|Yes| PAY4[Fully Paid]
        PAY3 -->|Difference| PAY5[Exception Notification]
        PAY5 --> PAY6[BRINS Confirm Exception]
        PAY6 --> PAY7[TUGURE Generate DN/CN]
        PAY7 --> PAY8[BRINS Verify DN/CN]
    end
    
    MC3 --> BC1
    BC8 --> NG1
    NG5 --> PAY1
```

---

## 7. Perbandingan Schema

### 7.1 Tabel Perbandingan Entity

| Entity | Workflow Lama | Workflow Baru | Perubahan |
|--------|---------------|---------------|-----------|
| **MasterContract** | Basic fields | + program_id, loan_type, validation_rules, version, dual approval | Enhanced dengan validation matrix |
| **Nota** | Created first, manually | Auto-generated after 3 batches, immutable after issued | Flow berbeda, auto-generation |
| **Batch** | Links to existing Nota | Independent, aggregates to Nota | Batch independent, nota derived |
| **Debtor** | Basic info | + validation_remarks, version_no, is_locked | Enhanced validation tracking |
| **Record** | Simple tracking | + revision tracking | Enhanced audit |
| **Claim** | Basic | + check_bdo_premi, reference validation | Validation terhadap BDO Premi |
| **Subrogation** | Basic | Reference to claim required | Strict reference validation |
| **DN/CN** | Post-payment only | Can be generated at multiple stages | More flexible |

### 7.2 Key Relationship Changes

```mermaid
graph LR
    subgraph Lama["Workflow Lama"]
        L_MC[MasterContract] --> L_NOTA[Nota Premi]
        L_NOTA --> L_BATCH[Batch 1,2,3]
        L_BATCH --> L_DEBTOR[Debtors]
    end
    
    subgraph Baru["Workflow Baru"]
        B_MC[MasterContract] --> B_BATCH[Batch 1,2,3]
        B_BATCH --> B_DEBTOR[Debtors]
        B_BATCH -.->|aggregates| B_NOTA[Nota Generated]
    end
```

### 7.3 Status Mapping

| Stage | Workflow Lama Status | Workflow Baru Status |
|-------|---------------------|---------------------|
| Contract | DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED | Draft → Pending First Approval → Pending Second Approval → Active |
| Nota | DRAFT → SUBMITTED → APPROVED → FINAL → PAID | Draft → Issued → Confirmed → Paid |
| Batch | UPLOADED → VALIDATED → APPROVED → CLOSED | Uploaded → Validated → Matched → Approved → Nota Issued → Closed |
| Debtor | DRAFT → SUBMITTED → APPROVED/REJECTED | DRAFT → SUBMITTED → APPROVED/REJECTED/CONDITIONAL |
| Claim | Draft → Checked → Invoiced → Paid | Draft → Checked → Doc Verified → Invoiced → Paid |
| Subrogation | Draft → Invoiced → Closed | Draft → Invoiced → Paid/Closed |

---

## Appendix: Info Tambahan

Berdasarkan dokumen `info_tambahan.txt`:

1. **Batch Consolidation**: Batch yang dikirim ke aplikasi berisi gabungan 3 batch + 1 nota dari 3 batch tersebut
2. **Single Submission View**: Di aplikasi, user melihatnya sebagai 1 submit batch debitur saja (bukan batch 1, 2, 3 terpisah)
3. **Claim/Subrogation Reference**: Keyword yang menjadi referensi claim dan subrogasi ke debtor adalah **nomor polis**
4. **Premium Payment Deduction**: Untuk proses pembayaran premi, akan dilihat claim di bulan sebelumnya. Jika ada claim, pembayaran premi langsung dikurangi claim tersebut

### Premium Calculation Flow (Baru)

```mermaid
flowchart LR
    A[Total Premium Due] --> B{Check Claims Previous Month}
    B -->|Has Claims| C[Deduct Claim Amount]
    B -->|No Claims| D[Full Premium]
    C --> E[Net Premium to Pay]
    D --> E
```
