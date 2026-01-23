# Information, Interaction, and Process Modelling
## Sistem Reasuransi BRINS - TUGURE (A3M)

---

## Daftar Isi
1. [Information Modelling](#1-information-modelling)
2. [Interaction Modelling](#2-interaction-modelling)
3. [Process Modelling](#3-process-modelling)

---

## 1. Information Modelling

### 1.1 Domain Model - Workflow Baru

```mermaid
classDiagram
    class MasterContract {
        +String contractId
        +String policyNo
        +String programId
        +String loanType
        +Date coverageStartDate
        +Date coverageEndDate
        +Number shareTugurePercentage
        +Number premiumRate
        +String effectiveStatus
        +Number version
        +validate()
        +approve()
        +activate()
    }
    
    class ValidationRule {
        +String ruleId
        +String ruleName
        +String logicRule
        +String failAction
        +String severity
        +execute()
        +evaluate()
    }
    
    class Batch {
        +String batchId
        +Number batchMonth
        +Number batchYear
        +Number totalRecords
        +Number finalPremiumAmount
        +Boolean debtorReviewCompleted
        +Boolean batchReadyForNota
        +String status
        +validate()
        +approve()
        +generateNota()
        +lock()
        +requestReopen()
    }
    
    class Debtor {
        +String debtorId
        +String nomorPeserta
        +String namaPeserta
        +Number plafon
        +Number nominalPremi
        +Number netPremi
        +Number kolektabilitas
        +String status
        +Number versionNo
        +validateAgainstContract()
        +approve()
        +reject()
    }
    
    class Nota {
        +String notaNumber
        +String notaType
        +String referenceId
        +Number amount
        +String status
        +Boolean isImmutable
        +String reconciliationStatus
        +issue()
        +confirm()
        +reconcile()
        +makeImmutable()
    }
    
    class Payment {
        +String paymentId
        +String paymentRef
        +Number amount
        +Date paymentDate
        +String matchStatus
        +String exceptionType
        +reconcile()
        +generateException()
    }
    
    class Claim {
        +String claimNo
        +String policyNo
        +String nomorSertifikat
        +Number nilaiKlaim
        +Number shareTugureAmount
        +String status
        +Boolean checkBdoPremi
        +validate()
        +generateNota()
        +approve()
    }
    
    class Subrogation {
        +String subroId
        +Number recoveryAmount
        +String status
        +validate()
        +generateNota()
        +close()
    }
    
    class DebitCreditNote {
        +String noteNumber
        +String noteType
        +Number adjustmentAmount
        +String reasonCode
        +String status
        +generate()
        +verify()
        +apply()
    }
    
    MasterContract "1" --> "0..*" Batch : covers
    MasterContract "1" --> "0..*" ValidationRule : defines
    MasterContract "1" --> "0..*" Claim : governs
    Batch "1" --> "0..*" Debtor : contains
    Batch "3" --> "1" Nota : aggregates to
    Nota "1" --> "0..*" Payment : receives
    Nota "1" --> "0..*" DebitCreditNote : adjusted by
    Debtor "1" --> "0..*" Claim : files
    Claim "1" --> "1" Nota : generates
    Claim "1" --> "0..*" Subrogation : triggers
    Subrogation "1" --> "1" Nota : generates
```

### 1.2 Information Architecture - Complete System

```mermaid
graph TB
    subgraph Core["Core Domain"]
        MC[Master Contract<br/>Policy Rules & Coverage]
        VR[Validation Rules<br/>Business Logic]
    end
    
    subgraph Premium["Premium Management"]
        BAT[Batch<br/>Monthly Collections]
        DEB[Debtor<br/>Individual Coverage]
        NOTA[Nota<br/>Invoice & Billing]
        PAY[Payment<br/>Reconciliation]
    end
    
    subgraph Claims["Claims Management"]
        CLM[Claim<br/>Loss Events]
        SUB[Subrogation<br/>Recovery]
        NCLAIM[Nota Claim<br/>Claim Invoice]
        NSUB[Nota Subrogation<br/>Recovery Invoice]
    end
    
    subgraph Adjustment["Financial Adjustment"]
        DN[Debit Note<br/>Additional Charges]
        CN[Credit Note<br/>Refunds]
    end
    
    MC -.defines.-> VR
    MC -->|governs| BAT
    MC -->|governs| CLM
    BAT -->|contains| DEB
    BAT -->|aggregates 3:1| NOTA
    DEB -->|files| CLM
    CLM -->|generates| NCLAIM
    CLM -->|triggers| SUB
    SUB -->|generates| NSUB
    NOTA -->|receives| PAY
    NCLAIM -->|receives| PAY
    NSUB -->|receives| PAY
    PAY -.generates.-> DN
    PAY -.generates.-> CN
    NOTA -.adjusted by.-> DN
    NOTA -.adjusted by.-> CN
    
    VR -.validates.-> BAT
    VR -.validates.-> DEB
    VR -.validates.-> CLM
```

### 1.3 Data Model - Key Entities Detail### 1.4 Information States and Lifecycles

erDiagram
    MASTER_CONTRACT ||--o{ VALIDATION_RULE : "defines"
    MASTER_CONTRACT ||--o{ BATCH : "governs"
    MASTER_CONTRACT ||--o{ CLAIM : "covers"
    
    BATCH ||--o{ DEBTOR : "contains"
    BATCH }o--|| NOTA_BATCH : "aggregates to (3:1)"
    
    DEBTOR ||--o{ CLAIM : "may file"
    
    CLAIM ||--|| NOTA_CLAIM : "generates"
    CLAIM ||--o{ SUBROGATION : "may trigger"
    
    SUBROGATION ||--|| NOTA_SUBROGATION : "generates"
    
    NOTA_BATCH ||--o{ PAYMENT : "receives"
    NOTA_CLAIM ||--o{ PAYMENT : "receives"
    NOTA_SUBROGATION ||--o{ PAYMENT : "receives"
    
    NOTA_BATCH ||--o{ DN_CN : "may have adjustments"
    PAYMENT ||--o{ DN_CN : "may generate"
    
    MASTER_CONTRACT {
        string contract_id PK "Unique identifier"
        string policy_no UK "Policy number"
        string program_id "Program identifier"
        string loan_type "Type of loan covered"
        date coverage_start_date "Coverage begins"
        date coverage_end_date "Coverage ends"
        decimal share_tugure_percentage "Tugure's share %"
        decimal premium_rate "Premium rate %"
        decimal ric_rate "RIC rate %"
        decimal bf_rate "BF rate %"
        string allowed_kolektabilitas "Valid collectibility values"
        string allowed_region "Allowed regions"
        string effective_status "Draft|Active|Inactive"
        int version "Version number for amendments"
        string parent_contract_id FK "For version tracking"
        datetime first_approved_date "First approval timestamp"
        datetime second_approved_date "Second approval timestamp"
    }
    
    VALIDATION_RULE {
        string rule_id PK "Unique identifier"
        string contract_id FK "Links to contract"
        string rule_name "Name of validation rule"
        string logic_rule "Business logic expression"
        string fail_action "REJECT|WARNING|CONDITIONAL"
        string severity "HIGH|MEDIUM|LOW"
        boolean is_active "Rule active status"
    }
    
    BATCH {
        string batch_id PK "Unique identifier"
        string contract_id FK "Links to contract"
        int batch_month "1-12"
        int batch_year "Year"
        int total_records "Count of debtors"
        decimal total_exposure "Sum of plafon (raw)"
        decimal total_premium "Sum of premium (raw)"
        decimal final_exposure_amount "Approved debtors only"
        decimal final_premium_amount "Approved debtors only"
        boolean debtor_review_completed "All debtors reviewed"
        boolean batch_ready_for_nota "Ready to generate nota"
        string status "Uploaded|Validated|Matched|Approved|Nota_Issued|Closed"
        boolean operational_locked "Locked when closed"
        datetime validated_date "Validation timestamp"
        datetime approved_date "Approval timestamp"
        datetime nota_issued_date "Nota generation timestamp"
        datetime closed_date "Closure timestamp"
    }
    
    DEBTOR {
        string debtor_id PK "Auto-generated ID"
        string batch_id FK "Links to batch"
        string contract_id FK "Links to contract"
        string nomor_peserta UK "Participant number"
        string nomor_rekening_pinjaman "Loan account number"
        string nama_peserta "Participant name"
        string loan_type "Loan type code"
        date tanggal_mulai_covering "Coverage start"
        date tanggal_akhir_covering "Coverage end"
        decimal plafon "Loan amount"
        decimal nominal_premi "Gross premium"
        decimal premi_percentage "Premium %"
        decimal ric_percentage "RIC %"
        decimal bf_percentage "BF %"
        decimal net_premi "Net premium after deductions"
        string unit_code "Unit code"
        string region_desc "Region"
        int kolektabilitas "1-5 collectibility"
        int flag_restruktur "0 or 1"
        string status "DRAFT|SUBMITTED|APPROVED|REJECTED|CONDITIONAL"
        boolean is_locked "Locked after batch closed"
        string rejection_reason "Reason if rejected"
        string validation_remarks "Validation notes"
        int version_no "Version for amendments"
    }
    
    NOTA_BATCH {
        string nota_number PK "Invoice number"
        string nota_type "BATCH"
        string reference_id FK "Batch reference (aggregated)"
        string contract_id FK "Links to contract"
        decimal amount "IMMUTABLE after issued"
        string currency "IDR"
        string status "Draft|Issued|Confirmed|Paid"
        boolean is_immutable "TRUE after issued"
        string reconciliation_status "PENDING|PARTIAL|MATCHED|OVERPAID|FINAL"
        datetime issued_date "Issuance timestamp"
        datetime confirmed_date "Confirmation timestamp"
        datetime paid_date "Payment timestamp"
        string payment_reference "Payment ref number"
        decimal total_actual_paid "Actual payment received"
    }
    
    CLAIM {
        string claim_no PK "Claim number"
        string debtor_id FK "Links to debtor"
        string contract_id FK "Links to contract"
        string policy_no "Policy reference"
        string nomor_sertifikat "Certificate number"
        string nama_tertanggung "Insured name"
        date tanggal_kejadian "Incident date"
        date tanggal_meninggal "Death date (if applicable)"
        decimal nilai_klaim "Claim amount"
        decimal share_tugure_amount "Tugure's share of claim"
        string status "Draft|Checked|Doc_Verified|Invoiced|Paid"
        boolean check_bdo_premi "Validate against premium BDO"
        string rejection_reason "Reason if rejected"
    }
    
    NOTA_CLAIM {
        string nota_number PK "Claim invoice number"
        string nota_type "CLAIM"
        string claim_id FK "Links to claim"
        decimal amount "Claim payout amount"
        string status "Draft|Issued|Paid"
        datetime issued_date "Issuance timestamp"
    }
    
    SUBROGATION {
        string subro_id PK "Subrogation ID"
        string claim_id FK "Links to claim"
        string debtor_id FK "Links to debtor"
        decimal recovery_amount "Amount recovered"
        string status "Draft|Invoiced|Paid_Closed"
        datetime recovery_date "Recovery timestamp"
    }
    
    NOTA_SUBROGATION {
        string nota_number PK "Subrogation invoice"
        string nota_type "SUBROGATION"
        string subro_id FK "Links to subrogation"
        decimal amount "Recovery amount"
        string status "Draft|Issued|Paid"
        datetime issued_date "Issuance timestamp"
    }
    
    PAYMENT {
        string payment_id PK "Payment ID"
        string nota_number FK "Links to nota"
        string payment_ref "Bank reference"
        decimal amount "Payment amount"
        date payment_date "Payment date"
        string match_status "PENDING|MATCHED|PARTIAL|OVERPAID|UNMATCHED"
        string exception_type "UNDERPAYMENT|OVERPAYMENT|TIMING"
        datetime reconciled_date "Reconciliation timestamp"
    }
    
    DN_CN {
        string note_number PK "DN/CN number"
        string nota_number FK "Links to nota"
        string note_type "DEBIT|CREDIT"
        decimal adjustment_amount "Adjustment value"
        string reason_code "Reason for adjustment"
        string status "Draft|Issued|Verified|Applied"
        datetime issued_date "Issuance timestamp"
    }
    
```mermaid
stateDiagram-v2
    [*] --> MasterContract
    
    state MasterContract {
        [*] --> Draft
        Draft --> PendingFirstApproval : Submit
        PendingFirstApproval --> Draft : Reject
        PendingFirstApproval --> PendingSecondApproval : First Approve
        PendingSecondApproval --> Draft : Reject
        PendingSecondApproval --> Active : Second Approve
        Active --> Inactive : Expire/Terminate
        Active --> Active : Amend (new version)
        Inactive --> [*]
    }
    
    MasterContract --> Batch : Create batches
    
    state Batch {
        [*] --> Uploaded
        Uploaded --> Validated : Auto-validate
        Validated --> Matched : Match rules
        Matched --> Approved : TUGURE approves
        Matched --> Rejected : TUGURE rejects
        Rejected --> Uploaded : Revise
        Approved --> NotaIssued : Generate nota (after 3 batches)
        NotaIssued --> BranchConfirmed : Finance confirms
        BranchConfirmed --> Paid : Payment received
        Paid --> Closed : Reconciliation complete
        Closed --> ReopenRequested : Request reopen
        ReopenRequested --> Reopened : Supervisor approves
        Reopened --> Uploaded : Back to revision
        Closed --> [*]
    }
    
    Batch --> Nota : Aggregate 3:1
    
    state Nota {
        [*] --> NotaDraft
        NotaDraft --> Issued : Issue (becomes immutable)
        Issued --> Confirmed : BRINS confirms
        Confirmed --> NotaPaid : Payment matched
        NotaPaid --> [*]
        
        note right of Issued
            Amount becomes IMMUTABLE
            Auto-updates if batch revised
        end note
    }
    
    Batch --> Debtor : Contains
    
    state Debtor {
        [*] --> DebtorDraft
        DebtorDraft --> Submitted : Submit for review
        Submitted --> Approved : Pass validation
        Submitted --> Rejected : Fail validation
        Submitted --> Conditional : Conditional approval
        Rejected --> DebtorDraft : Revise
        Conditional --> Approved : Condition met
        Approved --> Locked : Batch closed
        Locked --> [*]
    }
    
    Debtor --> Claim : May file claim
    
    state Claim {
        [*] --> ClaimDraft
        ClaimDraft --> Checked : Initial validation
        Checked --> DocVerified : Document verified
        DocVerified --> Invoiced : Generate nota claim
        Invoiced --> ClaimPaid : Payment made
        ClaimPaid --> [*]
        
        Checked --> ClaimRejected : Validation fails
        ClaimRejected --> ClaimDraft : Revise
    }
    
    Claim --> Subrogation : May trigger
    
    state Subrogation {
        [*] --> SubroDraft
        SubroDraft --> SubroInvoiced : Generate nota
        SubroInvoiced --> SubroPaidClosed : Payment received
        SubroPaidClosed --> [*]
    }
```

---

## 2. Interaction Modelling

### 2.1 Actor Interaction Overview

```mermaid
graph TB
    subgraph External["External Actors"]
        BSM[BSM<br/>Broker]
        BRINS_OPS[BRINS<br/>Operations]
        BRINS_FIN[BRINS<br/>Finance]
    end
    
    subgraph Internal["Internal Actors"]
        TUGURE_UW[TUGURE<br/>Underwriter]
        TUGURE_CLM[TUGURE<br/>Claims]
        TUGURE_FIN[TUGURE<br/>Finance]
        SYS_ADMIN[System<br/>Administrator]
    end
    
    subgraph System["A3M System"]
        CONTRACT[Contract<br/>Management]
        BATCH[Batch<br/>Processing]
        NOTA[Nota<br/>Generation]
        CLAIM[Claim<br/>Processing]
        PAYMENT[Payment<br/>Reconciliation]
        VALIDATION[Validation<br/>Engine]
    end
    
    BSM -->|Send batch data| BRINS_OPS
    BRINS_OPS -->|Submit contract| CONTRACT
    BRINS_OPS -->|Upload batches| BATCH
    BRINS_FIN -->|Submit payment| PAYMENT
    
    CONTRACT -->|Review & approve| TUGURE_UW
    BATCH -->|Review batches| TUGURE_UW
    CLAIM -->|Review claims| TUGURE_CLM
    PAYMENT -->|Reconcile| TUGURE_FIN
    
    TUGURE_UW -.->|Approve/Reject| CONTRACT
    TUGURE_UW -.->|Approve/Reject| BATCH
    TUGURE_CLM -.->|Approve/Reject| CLAIM
    TUGURE_FIN -.->|Confirm| PAYMENT
    
    BATCH -->|Validate| VALIDATION
    BATCH -->|Generate| NOTA
    CLAIM -->|Generate| NOTA
    
    SYS_ADMIN -.->|Configure| VALIDATION
    SYS_ADMIN -.->|Manage| CONTRACT
    
    NOTA -->|Notify| BRINS_FIN
    PAYMENT -.->|Exception| BRINS_FIN
```

### 2.2 Use Case Diagram - Complete System### 2.3 Sequence Diagram - Premium Processing (End-to-End)

```mermaid
sequenceDiagram
    autonumber
    actor BSM as BSM Broker
    actor BRINS_OPS as BRINS Operations
    actor BRINS_FIN as BRINS Finance
    participant SYS as A3M System
    participant VAL as Validation Engine
    actor TUG_UW as TUGURE Underwriter
    actor TUG_FIN as TUGURE Finance
    
    rect rgb(230, 240, 255)
    note over BSM,SYS: Phase 1: Batch Collection (Month)
    BSM->>BRINS_OPS: Send Batch 1 Data (Week 1)
    BRINS_OPS->>BRINS_OPS: Internal Review
    BSM->>BRINS_OPS: Send Batch 2 Data (Week 2)
    BRINS_OPS->>BRINS_OPS: Internal Review
    BSM->>BRINS_OPS: Send Batch 3 Data (Week 3)
    BRINS_OPS->>BRINS_OPS: Internal Review
    note over BRINS_OPS: Collect all 3 batches
    end
    
    rect rgb(240, 255, 240)
    note over BRINS_OPS,VAL: Phase 2: System Upload & Validation
    BRINS_OPS->>SYS: Upload Combined Batches (3 batches)
    SYS->>SYS: Create Batch Records
    loop For each batch
        SYS->>VAL: Validate Batch
        VAL->>VAL: Check Master Contract Rules
        VAL->>VAL: Validate Each Debtor
        VAL-->>SYS: Validation Results
    end
    SYS->>SYS: Update Batch Status: Validated
    end
    
    rect rgb(255, 240, 230)
    note over SYS,TUG_UW: Phase 3: TUGURE Review
    SYS->>TUG_UW: Send Batches for Review
    TUG_UW->>TUG_UW: Review Batch Details
    TUG_UW->>TUG_UW: Review Debtor List
    
    alt All Batches Approved
        TUG_UW->>SYS: Approve All Batches
        SYS->>SYS: Update Status: Approved
    else Need Revision
        TUG_UW->>SYS: Add Remarks & Request Revision
        SYS->>BRINS_OPS: Notification: Revision Required
        BRINS_OPS->>SYS: Upload Revised Batch
        SYS->>VAL: Re-validate
        VAL-->>SYS: New Validation Results
        SYS->>TUG_UW: Send for Re-review
        TUG_UW->>SYS: Approve Revised Batch
    end
    end
    
    rect rgb(255, 255, 230)
    note over SYS,TUG_FIN: Phase 4: Nota Generation
    SYS->>SYS: Check: 3 Batches Approved?
    SYS->>SYS: Calculate Total Premium
    SYS->>SYS: Generate Nota (Auto)
    SYS->>SYS: Nota Status: Draft
    SYS->>TUG_FIN: Send Nota for Review
    SYS->>BRINS_FIN: Notify: Nota Generated
    
    TUG_FIN->>TUG_FIN: Review Nota Amount
    TUG_FIN->>SYS: Issue Nota
    SYS->>SYS: Nota Status: Issued (IMMUTABLE)
    SYS->>BRINS_FIN: Notify: Nota Issued
    
    BRINS_FIN->>SYS: Confirm Nota
    SYS->>SYS: Nota Status: Confirmed
    end
    
    rect rgb(230, 255, 255)
    note over BRINS_FIN,TUG_FIN: Phase 5: Payment & Netting
    BRINS_FIN->>SYS: Check: Any Claims Last Month?
    SYS->>SYS: Query Claims (Previous Month)
    
    alt Has Claims
        SYS-->>BRINS_FIN: Claim Amount: Rp X
        BRINS_FIN->>BRINS_FIN: Calculate Net Premium<br/>(Nota Amount - Claim)
        BRINS_FIN->>SYS: Submit Net Payment
    else No Claims
        BRINS_FIN->>SYS: Submit Full Payment
    end
    
    SYS->>SYS: Record Payment
    SYS->>TUG_FIN: Notify: Payment Received
    end
    
    rect rgb(255, 230, 255)
    note over SYS,TUG_FIN: Phase 6: Reconciliation
    TUG_FIN->>SYS: Reconcile Payment
    SYS->>SYS: Match Payment vs Nota
    
    alt Payment Matched
        SYS->>SYS: Nota Status: Paid
        SYS->>SYS: Reconciliation: MATCHED
        SYS->>BRINS_FIN: Confirmation: Payment Complete
    else Payment Mismatch
        SYS->>SYS: Reconciliation: PARTIAL/OVERPAID
        SYS->>BRINS_FIN: Exception Notification
        BRINS_FIN->>SYS: Confirm Exception
        TUG_FIN->>SYS: Generate DN/CN
        SYS->>BRINS_FIN: Send DN/CN for Verification
        BRINS_FIN->>SYS: Verify DN/CN
        SYS->>SYS: Apply Adjustment
        SYS->>SYS: Nota Status: Paid (Final)
    end
    
    SYS->>SYS: Batch Status: Paid → Closed
    SYS->>SYS: Lock Batch (Operational_Locked = TRUE)
    end
```

### 2.4 Sequence Diagram - Claim Processing

```mermaid
sequenceDiagram
    autonumber
    actor BRINS as BRINS Operations
    participant SYS as A3M System
    participant VAL as Validation Engine
    actor TUG_CLM as TUGURE Claims
    actor TUG_FIN as TUGURE Finance
    actor BRINS_FIN as BRINS Finance
    
    rect rgb(255, 240, 240)
    note over BRINS,VAL: Phase 1: Claim Submission
    BRINS->>SYS: Submit Claim (nomor polis reference)
    SYS->>VAL: Validate Claim
    VAL->>VAL: Check Policy Number exists
    VAL->>VAL: Check Debtor exists
    VAL->>VAL: Check Coverage Period
    VAL->>VAL: Validate against Master Contract
    
    alt Validation Pass
        VAL-->>SYS: Validation OK
        SYS->>SYS: Claim Status: Checked
    else Validation Fail
        VAL-->>SYS: Validation Errors
        SYS->>BRINS: Rejection with Errors
        BRINS->>SYS: Revise & Resubmit
        SYS->>VAL: Re-validate
    end
    end
    
    rect rgb(240, 255, 240)
    note over SYS,TUG_CLM: Phase 2: Document Review
    SYS->>TUG_CLM: Send Claim for Review
    TUG_CLM->>TUG_CLM: Review Documents
    TUG_CLM->>TUG_CLM: Verify Claim Details
    TUG_CLM->>SYS: Check BDO Premi (if flag set)
    
    alt Documents Complete & Valid
        TUG_CLM->>SYS: Approve Claim
        SYS->>SYS: Claim Status: Doc_Verified
    else Documents Incomplete
        TUG_CLM->>SYS: Request Additional Documents
        SYS->>BRINS: Document Request
        BRINS->>SYS: Upload Additional Docs
        SYS->>TUG_CLM: Notify: Docs Uploaded
    end
    end
    
    rect rgb(240, 240, 255)
    note over SYS,TUG_FIN: Phase 3: Claim Nota Generation
    TUG_CLM->>SYS: Final Approval
    SYS->>SYS: Calculate Share TUGURE Amount
    SYS->>SYS: Generate Nota Claim
    SYS->>SYS: Claim Status: Invoiced
    SYS->>TUG_FIN: Send Nota for Payment
    SYS->>BRINS_FIN: Notify: Claim Approved
    end
    
    rect rgb(255, 255, 230)
    note over TUG_FIN,BRINS_FIN: Phase 4: Payment Processing
    TUG_FIN->>TUG_FIN: Process Payment
    TUG_FIN->>SYS: Submit Payment
    SYS->>SYS: Record Payment
    SYS->>SYS: Claim Status: Paid
    SYS->>BRINS_FIN: Payment Notification
    
    note over BRINS_FIN: Claim will be deducted<br/>from next month's premium
    end
    
    rect rgb(230, 255, 255)
    note over SYS,BRINS: Phase 5: Subrogation (Optional)
    alt Recovery Possible
        BRINS->>SYS: Submit Subrogation (ref to claim)
        SYS->>VAL: Validate Subrogation
        VAL->>VAL: Check Claim exists
        VAL->>VAL: Validate Recovery Amount
        VAL-->>SYS: Validation OK
        
        SYS->>TUG_CLM: Send for Review
        TUG_CLM->>SYS: Approve Subrogation
        SYS->>SYS: Generate Nota Subrogation
        SYS->>BRINS_FIN: Send Nota for Payment
        
        BRINS_FIN->>SYS: Submit Recovery Payment
        SYS->>SYS: Subrogation Status: Paid_Closed
    end
    end
```

### 2.5 Collaboration Diagram - Batch to Nota Flow

```mermaid
graph TB
    subgraph "Actor Collaboration"
        A1[BSM Broker]
        A2[BRINS Operations]
        A3[TUGURE Underwriter]
        A4[BRINS Finance]
        A5[TUGURE Finance]
    end
    
    subgraph "System Components"
        C1[Batch Upload<br/>Module]
        C2[Validation<br/>Engine]
        C3[Batch Review<br/>Module]
        C4[Nota Generation<br/>Engine]
        C5[Payment<br/>Reconciliation]
    end
    
    subgraph "Data Flow"
        D1[(Batch Data)]
        D2[(Validated Batch)]
        D3[(Approved Batch)]
        D4[(Nota)]
        D5[(Payment)]
    end
    
    A1 -->|1: Send batch data| A2
    A2 -->|2: Upload to system| C1
    C1 -->|3: Store| D1
    C1 -->|4: Trigger validation| C2
    C2 -->|5: Validate| D1
    C2 -->|6: Store results| D2
    C2 -->|7: Send for review| C3
    
    A3 -->|8: Review & approve| C3
    C3 -->|9: Update status| D3
    C3 -->|10: Trigger nota| C4
    
    C4 -->|11: Check batches| D3
    C4 -->|12: Generate nota| D4
    C4 -->|13: Notify finance| A4
    C4 -->|14: Notify finance| A5
    
    A5 -->|15: Issue nota| C4
    C4 -->|16: Update immutable| D4
    
    A4 -->|17: Confirm & pay| C5
    C5 -->|18: Match payment| D4
    C5 -->|19: Record payment| D5
    
    A5 -->|20: Reconcile| C5
    C5 -->|21: Update status| D4
```

---

## 3. Process Modelling

### 3.1 BPMN - Premium Collection Process (Workflow Baru)### 3.2 BPMN - Claim Processing### 3.3 Activity Diagram - Contract Amendment

```mermaid
stateDiagram-v2
    [*] --> CheckAmendmentNeed: Amendment Required
    
    CheckAmendmentNeed --> PrepareAmendment: BRINS identifies changes
    PrepareAmendment --> CreateNewVersion: System creates v2
    CreateNewVersion --> CopyBaseData: Copy from v1
    
    CopyBaseData --> ModifyFields: BRINS modifies fields
    ModifyFields --> UpdateValidationRules: Update validation matrix
    UpdateValidationRules --> SubmitForApproval: Submit v2
    
    SubmitForApproval --> FirstApproval: TUGURE reviews
    
    state FirstApproval {
        [*] --> ReviewChanges
        ReviewChanges --> CompareVersions: Compare v1 vs v2
        CompareVersions --> ValidateImpact: Assess impact
        ValidateImpact --> DecisionFirst
        
        DecisionFirst --> ApprovedFirst: Changes acceptable
        DecisionFirst --> RejectedFirst: Changes unacceptable
        
        RejectedFirst --> [*]: Reject
        ApprovedFirst --> [*]: First Approve
    }
    
    FirstApproval --> ModifyFields: Rejected - revise
    FirstApproval --> SecondApproval: First Approved
    
    state SecondApproval {
        [*] --> FinalReview
        FinalReview --> CheckCompliance: Compliance check
        CheckCompliance --> DecisionSecond
        
        DecisionSecond --> ApprovedSecond: Compliant
        DecisionSecond --> RejectedSecond: Non-compliant
        
        RejectedSecond --> [*]: Reject
        ApprovedSecond --> [*]: Final Approve
    }
    
    SecondApproval --> ModifyFields: Rejected - revise
    SecondApproval --> ActivateNewVersion: Second Approved
    
    ActivateNewVersion --> DeactivateOldVersion: Set v1 = Inactive
    DeactivateOldVersion --> SetNewActive: Set v2 = Active
    SetNewActive --> NotifyStakeholders: Send notifications
    NotifyStakeholders --> UpdateRelatedBatches: Link new batches to v2
    
    UpdateRelatedBatches --> [*]: Amendment Complete
```

### 3.4 Swimlane Diagram - Payment Reconciliation Process

```mermaid
graph TB
    subgraph "BRINS Finance"
        BF1[Receive Nota]
        BF2[Check Previous Claims]
        BF3{Has Claims?}
        BF4[Calculate Net Premium<br/>Nota - Claims]
        BF5[Prepare Full Payment]
        BF6[Submit Payment]
        BF7[Receive Exception Notice]
        BF8[Confirm Exception]
        BF9[Verify DN/CN]
        BF10[Submit Additional Payment]
    end
    
    subgraph "A3M System"
        SYS1[Generate Nota]
        SYS2[Send to BRINS Finance]
        SYS3[Query Previous Month Claims]
        SYS4[Provide Claim Data]
        SYS5[Receive Payment]
        SYS6[Match Payment vs Nota]
        SYS7{Match Status}
        SYS8[Update: Paid & MATCHED]
        SYS9[Update: PARTIAL/OVERPAID]
        SYS10[Generate Exception Report]
        SYS11[Receive DN/CN]
        SYS12[Apply Adjustment]
        SYS13[Update Final Status]
        SYS14[Close Batch]
    end
    
    subgraph "TUGURE Finance"
        TF1[Issue Nota]
        TF2[Receive Payment Notification]
        TF3[Reconcile Payment]
        TF4[Analyze Difference]
        TF5{Generate DN/CN?}
        TF6[Create DN/CN]
        TF7[Send to BRINS]
        TF8[Confirm Final]
    end
    
    SYS1 --> SYS2
    SYS2 --> BF1
    BF1 --> TF1
    TF1 --> BF1
    BF1 --> BF2
    BF2 --> SYS3
    SYS3 --> SYS4
    SYS4 --> BF3
    
    BF3 -->|Yes| BF4
    BF3 -->|No| BF5
    BF4 --> BF6
    BF5 --> BF6
    
    BF6 --> SYS5
    SYS5 --> SYS6
    SYS6 --> TF2
    TF2 --> TF3
    TF3 --> SYS7
    
    SYS7 -->|MATCHED| SYS8
    SYS7 -->|MISMATCH| SYS9
    
    SYS8 --> SYS14
    SYS14 --> TF8
    
    SYS9 --> SYS10
    SYS10 --> BF7
    BF7 --> BF8
    BF8 --> TF4
    TF4 --> TF5
    
    TF5 -->|Yes| TF6
    TF5 -->|No| BF10
    
    TF6 --> TF7
    TF7 --> SYS11
    SYS11 --> BF9
    BF9 --> SYS12
    SYS12 --> SYS13
    SYS13 --> SYS14
    
    BF10 --> SYS5
```

### 3.5 Data Flow Diagram - Level 0 (Context Diagram)

```mermaid
graph TB
    subgraph External["External Entities"]
        BSM[BSM Broker]
        BRINS[BRINS]
        TUGURE[TUGURE]
    end
    
    subgraph System["A3M Reinsurance System"]
        CORE[A3M Core<br/>Reinsurance Processing]
    end
    
    BSM -->|Batch Debitur Data| CORE
    BRINS -->|Master Contract| CORE
    BRINS -->|Batch Upload| CORE
    BRINS -->|Claim Submission| CORE
    BRINS -->|Subrogation Data| CORE
    BRINS -->|Payment| CORE
    
    CORE -->|Batch Status| BRINS
    CORE -->|Nota Invoice| BRINS
    CORE -->|Claim Status| BRINS
    CORE -->|DN/CN| BRINS
    
    CORE -->|Contract for Review| TUGURE
    CORE -->|Batch for Review| TUGURE
    CORE -->|Nota for Issuance| TUGURE
    CORE -->|Claim for Review| TUGURE
    
    TUGURE -->|Contract Approval| CORE
    TUGURE -->|Batch Approval| CORE
    TUGURE -->|Nota Issued| CORE
    TUGURE -->|Claim Approval| CORE
    TUGURE -->|Payment| CORE
    TUGURE -->|Reconciliation Result| CORE
```

### 3.6 Data Flow Diagram - Level 1 (Premium Process)

```mermaid
graph TB
    subgraph Actors["External Actors"]
        BSM[BSM Broker]
        BRINS[BRINS Ops]
        BRINS_FIN[BRINS Finance]
        TUGURE_UW[TUGURE UW]
        TUGURE_FIN[TUGURE Finance]
    end
    
    subgraph Process["Core Processes"]
        P1[1.0<br/>Batch<br/>Upload]
        P2[2.0<br/>Validation<br/>Engine]
        P3[3.0<br/>Batch<br/>Review]
        P4[4.0<br/>Nota<br/>Generation]
        P5[5.0<br/>Payment<br/>Processing]
        P6[6.0<br/>Reconciliation]
    end
    
    subgraph Data["Data Stores"]
        D1[(D1: Master<br/>Contract)]
        D2[(D2: Batch<br/>Data)]
        D3[(D3: Debtor<br/>Data)]
        D4[(D4: Nota<br/>Data)]
        D5[(D5: Payment<br/>Data)]
        D6[(D6: Claim<br/>Data)]
    end
    
    BSM -->|Raw Batch Data| BRINS
    BRINS -->|Combined Batches| P1
    P1 -->|Store Batch| D2
    P1 -->|Store Debtors| D3
    P1 -->|Trigger Validation| P2
    
    P2 -->|Read Rules| D1
    P2 -->|Read Batch| D2
    P2 -->|Validate Debtors| D3
    P2 -->|Validation Results| D2
    P2 -->|Send for Review| P3
    
    TUGURE_UW <-->|Review & Approve| P3
    P3 -->|Update Status| D2
    P3 -->|Update Debtors| D3
    P3 -->|Trigger Generation| P4
    
    P4 -->|Read Batches| D2
    P4 -->|Aggregate Amounts| D3
    P4 -->|Generate Nota| D4
    P4 -->|Notify| BRINS_FIN
    P4 -->|Send for Issuance| TUGURE_FIN
    
    TUGURE_FIN -->|Issue Nota| P4
    P4 -->|Update Immutable| D4
    
    BRINS_FIN -->|Check Claims| D6
    BRINS_FIN -->|Submit Payment| P5
    P5 -->|Store Payment| D5
    P5 -->|Trigger Reconciliation| P6
    
    TUGURE_FIN <-->|Reconcile| P6
    P6 -->|Read Nota| D4
    P6 -->|Read Payment| D5
    P6 -->|Match & Update| D4
    P6 -->|Update Status| D2
    P6 -->|Result| BRINS_FIN
```

### 3.7 Process Comparison - Lama vs Baru

```mermaid
graph LR
    subgraph Lama["WORKFLOW LAMA"]
        L1[1. Create Nota<br/>FIRST]
        L2[2. Upload<br/>Batch 1]
        L3[3. Review &<br/>Approve]
        L4[4. Add to<br/>Nota]
        L5[5. Upload<br/>Batch 2]
        L6[6. Upload<br/>Batch 3]
        L7[7. Finalize<br/>Nota]
        L8[8. Payment]
        
        L1 --> L2
        L2 --> L3
        L3 --> L4
        L4 --> L5
        L5 --> L3
        L3 --> L4
        L4 --> L6
        L6 --> L3
        L3 --> L7
        L7 --> L8
    end
    
    subgraph Baru["WORKFLOW BARU"]
        B1[1. Collect<br/>Batch 1]
        B2[2. Collect<br/>Batch 2]
        B3[3. Collect<br/>Batch 3]
        B4[4. Upload<br/>Combined]
        B5[5. Validate<br/>All]
        B6[6. Review &<br/>Approve]
        B7[7. AUTO Generate<br/>Nota]
        B8[8. Payment<br/>with Netting]
        
        B1 --> B2
        B2 --> B3
        B3 --> B4
        B4 --> B5
        B5 --> B6
        B6 --> B7
        B7 --> B8
    end
    
    style L1 fill:#ffcccc
    style L7 fill:#ffcccc
    style B7 fill:#ccffcc
    style B8 fill:#ccffcc
```

---

## Summary: Key Modelling Insights

### Information Model
- **Workflow Baru**: Nota is derived from Batch (3:1 aggregation), not created independently
- **Immutability**: Nota becomes immutable after issuance, ensuring data integrity
- **Versioning**: Master Contract supports versioning for amendments
- **Validation Matrix**: Embedded in Master Contract for automated validation

### Interaction Model
- **Simplified Actor Flow**: BSM → BRINS → System → TUGURE (linear flow)
- **Auto-Generation**: System autonomously generates Nota after 3 batches approved
- **Premium Netting**: System automatically deducts previous month's claims from premium payment
- **Exception Handling**: Structured DN/CN generation for payment mismatches

### Process Model
- **Batch-First Approach**: Collect all batches before nota generation
- **Validation-Driven**: Automated validation at multiple checkpoints
- **Status-Based Workflow**: Clear state transitions for each entity
- **Reconciliation Integration**: Built-in payment reconciliation with automatic exception handling
