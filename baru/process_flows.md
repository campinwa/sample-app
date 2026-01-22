# Detailed Process Flow Diagrams

## 1. System Architecture Overview

```mermaid
C4Context
    title System Context - Reinsurance Management System

    Person(brins, "BRINS User", "Cedant/Insurance Company")
    Person(tugure, "TUGURE User", "Reinsurer")
    Person(admin, "System Admin", "Administrator")
    
    System(system, "Reinsurance System", "Manages credit reinsurance between BRINS and TUGURE")
    
    System_Ext(bank, "Banking System", "Payment gateway")
    System_Ext(email, "Email Service", "Notifications")
    System_Ext(whatsapp, "WhatsApp API", "Alerts")
    
    Rel(brins, system, "Submits batches, confirms payments")
    Rel(tugure, system, "Reviews debtors, processes claims")
    Rel(admin, system, "Manages configuration")
    
    Rel(system, bank, "Fetches payment data")
    Rel(system, email, "Sends notifications")
    Rel(system, whatsapp, "Sends alerts")
```

---

## 2. Batch Processing - Detailed State Machine

```mermaid
stateDiagram-v2
    [*] --> Uploaded: User uploads Excel
    
    state Uploaded {
        [*] --> ParseFile
        ParseFile --> ValidateFormat
        ValidateFormat --> CreateRecords
        CreateRecords --> [*]
    }
    
    Uploaded --> Validated: Auto-validation
    
    state Validated {
        [*] --> CheckDuplicates
        CheckDuplicates --> ValidateFields
        ValidateFields --> CheckMandatory
        CheckMandatory --> [*]
    }
    
    Validated --> Matched: Contract matching
    
    state Matched {
        [*] --> FindContract
        FindContract --> CheckEligibility
        CheckEligibility --> MatchDebtors
        MatchDebtors --> [*]
    }
    
    Matched --> Approved: TUGURE approves
    
    state "Debtor Review" as DebtorReview {
        [*] --> ReviewEachDebtor
        ReviewEachDebtor --> CheckKolektabilitas
        CheckKolektabilitas --> CheckRegion
        CheckRegion --> CheckPlafond
        CheckPlafond --> UpdateRecordStatus
        UpdateRecordStatus --> [*]
    }
    
    Matched --> DebtorReview: Start review
    DebtorReview --> Matched: Review ongoing
    DebtorReview --> Approved: All debtors reviewed
    
    state Approved {
        [*] --> CalculateFinalAmounts
        CalculateFinalAmounts --> SetReviewCompleted
        SetReviewCompleted --> SetReadyForNota
        SetReadyForNota --> [*]
    }
    
    Approved --> NotaIssued: Issue Nota
    
    state NotaIssued {
        [*] --> CreateNota
        CreateNota --> SetNotaAmount
        SetNotaAmount --> MarkImmutable
        MarkImmutable --> [*]
    }
    
    NotaIssued --> BranchConfirmed: BRINS confirms
    BranchConfirmed --> Paid: Payment matched
    Paid --> Closed: Close batch
    
    state Closed {
        [*] --> LockOperations
        LockOperations --> LockDebtors
        LockDebtors --> FinalizeReconciliation
        FinalizeReconciliation --> [*]
    }
    
    Closed --> ReopenRequested: Request reopen
    
    state ReopenRequested {
        [*] --> CaptureReason
        CaptureReason --> AssessImpact
        AssessImpact --> RequestApproval
        RequestApproval --> [*]
    }
    
    ReopenRequested --> Reopened: Supervisor approves
    ReopenRequested --> Closed: Request denied
    
    state Reopened {
        [*] --> UnlockBatch
        UnlockBatch --> UnlockDebtors
        UnlockDebtors --> EnableEditing
        EnableEditing --> [*]
    }
    
    Reopened --> Validated: Resume from validation
    
    Validated --> Rejected: Validation errors
    Matched --> Rejected: Matching errors
    Approved --> Rejected: Approval denied
    
    state Rejected {
        [*] --> CaptureRejectionReason
        CaptureRejectionReason --> NotifyUsers
        NotifyUsers --> [*]
    }
    
    Rejected --> [*]
```

---

## 3. Debtor Lifecycle - Complete Flow

```mermaid
graph TD
    A[Create Debtor Record] --> B[Status: DRAFT]
    B --> C{Auto Validation}
    C -->|Pass| D[Status: SUBMITTED]
    C -->|Fail| E[Set validation_remarks]
    E --> F[Status: REJECTED]
    
    D --> G[TUGURE Review]
    G --> H{Eligibility Check}
    
    H --> I{Kolektabilitas?}
    I -->|In allowed list| J{Region?}
    I -->|Not allowed| F
    
    J -->|In allowed list| K{Plafond?}
    J -->|Not allowed| F
    
    K -->|Within limit| L{Complete Data?}
    K -->|Exceeds limit| F
    
    L -->|Yes| M[Status: APPROVED]
    L -->|Minor issues| N[Status: CONDITIONAL]
    L -->|Major issues| F
    
    N --> O[Request Revision]
    O --> P[Update version_no]
    P --> Q[Modify data]
    Q --> D
    
    M --> R[Update Record: Accepted]
    R --> S[Include in final_premium_amount]
    
    F --> T[Update Record: Rejected]
    T --> U[Exclude from calculations]
    
    S --> V{All debtors reviewed?}
    U --> V
    
    V -->|Yes| W[batch.debtor_review_completed = TRUE]
    V -->|No| G
    
    W --> X{Any approved debtors?}
    X -->|Yes| Y[batch.batch_ready_for_nota = TRUE]
    X -->|No| Z[Cannot issue Nota]
    
    Y --> AA[Lock Debtors: is_locked = TRUE]
    AA --> AB[Batch proceeds to Nota]
```

---

## 4. Payment Matching Algorithm

```mermaid
flowchart TD
    Start[Payment Received from Bank] --> A[Create Payment Record]
    A --> B[Extract: amount, bank_reference, payment_date]
    B --> C{Manual match<br/>or Auto?}
    
    C -->|Auto| D[Search Pending Notas/Invoices]
    C -->|Manual| E[User selects Invoice/Nota]
    
    D --> F{Found match<br/>by reference?}
    F -->|Yes| G[Link to Invoice/Nota]
    F -->|No| H[mark: match_status = UNMATCHED]
    
    E --> G
    
    G --> I{Compare Amounts}
    
    I -->|Exact Match| J[Update Nota.total_actual_paid]
    J --> K[Nota.status = MATCHED]
    K --> L[Payment.match_status = MATCHED]
    L --> M[Payment.exception_type = NONE]
    
    I -->|Payment < Nota.amount| N[Partial Payment]
    N --> O[Update Nota.total_actual_paid]
    O --> P[Nota.reconciliation_status = PARTIAL]
    P --> Q[Payment.match_status = PARTIALLY_MATCHED]
    Q --> R[Payment.exception_type = UNDER]
    R --> S{Remaining > threshold?}
    S -->|Yes| T[Keep Nota open]
    S -->|No| U[Consider DN for difference]
    
    I -->|Payment > Nota.amount| V[Overpayment]
    V --> W[Update Nota.total_actual_paid]
    W --> X[Nota.reconciliation_status = OVERPAID]
    X --> Y[Payment.match_status = MATCHED]
    Y --> Z[Payment.exception_type = OVER]
    Z --> AA[Auto-create Credit Note]
    AA --> AB[CN.adjustment_amount = excess]
    
    H --> AC[Queue for Manual Review]
    M --> AD[Update Reconciliation]
    T --> AD
    U --> AD
    AB --> AD
    AC --> AD
    
    AD --> AE{Reconciliation Check}
    AE --> AF[total_invoiced vs total_paid]
    AF --> AG{Difference?}
    AG -->|Zero| AH[Reconciliation.status = MATCHED]
    AG -->|Non-zero| AI[Reconciliation.status = EXCEPTION]
    
    AH --> AJ[Close Period]
    AI --> AK[Investigate & Resolve]
    
    AJ --> End[Complete]
    AK --> End
```

---

## 5. Nota Generation Logic

```mermaid
flowchart TD
    Start[Trigger: Batch Approved] --> A{Check Source}
    A -->|Batch| B[Type: Batch Nota]
    A -->|Claim| C[Type: Claim Nota]
    A -->|Subrogation| D[Type: Subrogation Nota]
    
    B --> E[Source: Batch.final_premium_amount]
    C --> F[Source: Claim.share_tugure_amount]
    D --> G[Source: Subrogation.recovery_amount]
    
    E --> H[Generate nota_number]
    F --> H
    G --> H
    
    H --> I[Set reference_id]
    I --> J[Set contract_id]
    J --> K[Set amount from source]
    K --> L[Set currency]
    L --> M[Status = Draft]
    
    M --> N{Ready to Issue?}
    N -->|No| O[Save as Draft]
    N -->|Yes| P[Validate Data]
    
    P --> Q{Validation OK?}
    Q -->|No| R[Show Errors]
    Q -->|Yes| S[Issue Nota]
    
    S --> T[Status = Issued]
    T --> U[Set issued_by]
    U --> V[Set issued_date]
    V --> W[is_immutable = TRUE]
    W --> X[Lock amount field]
    
    X --> Y[Create Notification]
    Y --> Z{nota_type?}
    Z -->|Batch| AA[Notify BRINS to pay]
    Z -->|Claim| AB[Notify BRINS of payment due]
    Z -->|Subrogation| AC[Notify BRINS to receive]
    
    AA --> AD[Send Email via EmailTemplate]
    AB --> AD
    AC --> AD
    
    AD --> AE[Create System Notification]
    AE --> AF[Update AuditLog]
    AF --> End[Nota Issued]
    
    O --> End2[Saved as Draft]
    R --> End3[Fix & Retry]
```

---

## 6. Claim Processing - End to End

```mermaid
graph LR
    subgraph "1. Claim Creation"
        A1[Loss Event Occurs] --> A2[Create Claim Record]
        A2 --> A3[Status: Draft]
        A3 --> A4[Link to Debtor]
        A4 --> A5[Link to Contract]
    end
    
    subgraph "2. Initial Check"
        B1[Assign to Checker] --> B2[Verify Basic Info]
        B2 --> B3[Check Policy No]
        B3 --> B4[Verify Debtor]
        B4 --> B5[Status: Checked]
    end
    
    subgraph "3. Document Verification"
        C1[Upload Documents] --> C2[Verify Completeness]
        C2 --> C3{check_bdo_premi?}
        C3 -->|Pass| C4[Verify Coverage Period]
        C3 -->|Fail| C5[Reject: Wrong Period]
        C4 --> C6[Verify KOL Status]
        C6 --> C7{Valid KOL?}
        C7 -->|Yes| C8[Status: Doc Verified]
        C7 -->|No| C9[Reject: Invalid KOL]
    end
    
    subgraph "4. Amount Calculation"
        D1[Get max_coverage] --> D2[Get share_tugure_%]
        D2 --> D3[Calculate: nilai_klaim * share_%]
        D3 --> D4[Set share_tugure_amount]
    end
    
    subgraph "5. Invoicing"
        E1[Create Claim Nota] --> E2[Amount = share_tugure_amount]
        E2 --> E3[Issue to BRINS]
        E3 --> E4[Status: Invoiced]
    end
    
    subgraph "6. Payment"
        F1[TUGURE Processes Payment] --> F2[Payment Record Created]
        F2 --> F3[Match to Claim Nota]
        F3 --> F4[Claim Status: Paid]
    end
    
    subgraph "7. Subrogation (Optional)"
        G1{Recovery Possible?} -->|Yes| G2[Create Subrogation]
        G2 --> G3[Recovery Process]
        G3 --> G4[Amount Recovered]
        G4 --> G5[Create Subrogation Nota]
        G5 --> G6[BRINS Pays Back]
    end
    
    A5 --> B1
    B5 --> C1
    C8 --> D1
    D4 --> E1
    E4 --> F1
    F4 --> G1
```

---

## 7. Reconciliation Process Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant ReconciliationEngine
    participant Database
    participant NotaTable
    participant PaymentTable
    participant DN_CN_Table
    participant NotificationService
    
    Scheduler->>ReconciliationEngine: Trigger Monthly Reconciliation
    ReconciliationEngine->>Database: Get Contract List
    
    loop For Each Contract
        ReconciliationEngine->>NotaTable: Get All Notas for Period
        NotaTable-->>ReconciliationEngine: List of Notas
        
        ReconciliationEngine->>ReconciliationEngine: SUM(Nota.amount) = total_invoiced
        
        ReconciliationEngine->>PaymentTable: Get All Payments for Period
        PaymentTable-->>ReconciliationEngine: List of Payments
        
        ReconciliationEngine->>ReconciliationEngine: SUM(Payment.amount) = total_paid
        
        ReconciliationEngine->>DN_CN_Table: Get All DN/CN for Period
        DN_CN_Table-->>ReconciliationEngine: List of Adjustments
        
        ReconciliationEngine->>ReconciliationEngine: Calculate Net Adjustments
        
        ReconciliationEngine->>ReconciliationEngine: difference = (total_invoiced + adjustments) - total_paid
        
        alt Difference = 0
            ReconciliationEngine->>Database: Update Status = MATCHED
            ReconciliationEngine->>NotificationService: Send Success Notification
        else Difference > 0 (Underpaid)
            ReconciliationEngine->>Database: Update Status = EXCEPTION
            ReconciliationEngine->>ReconciliationEngine: Flag as Underpayment
            ReconciliationEngine->>NotificationService: Alert Finance Team
        else Difference < 0 (Overpaid)
            ReconciliationEngine->>Database: Update Status = EXCEPTION
            ReconciliationEngine->>ReconciliationEngine: Flag as Overpayment
            ReconciliationEngine->>NotificationService: Alert Finance Team
        end
        
        ReconciliationEngine->>Database: Create Reconciliation Record
    end
    
    ReconciliationEngine->>NotificationService: Send Summary Report
    ReconciliationEngine-->>Scheduler: Reconciliation Complete
```

---

## 8. Debit/Credit Note Flow

```mermaid
flowchart TD
    Start[Identify Adjustment Need] --> A{Adjustment Type?}
    
    A -->|Increase Amount| B[Create Debit Note]
    A -->|Decrease Amount| C[Create Credit Note]
    
    B --> D[DN: adjustment_amount > 0]
    C --> E[CN: adjustment_amount < 0]
    
    D --> F[Select Reason Code]
    E --> F
    
    F --> G{Reason?}
    G -->|Payment Difference| H[Document variance]
    G -->|FX Adjustment| I[Calculate FX impact]
    G -->|Premium Correction| J[Recalculate premium]
    G -->|Coverage Adjustment| K[Adjust coverage]
    G -->|Other| L[Provide description]
    
    H --> M[Status: Draft]
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[drafted_by, drafted_date]
    N --> O[Submit for Review]
    O --> P[Status: Under Review]
    
    P --> Q[Reviewer Checks]
    Q --> R{Approve?}
    
    R -->|No| S[Status: Rejected]
    S --> T[Set rejection_reason]
    T --> End1[Notify Drafter]
    
    R -->|Yes| U[Status: Approved]
    U --> V[approved_by, approved_date]
    V --> W[Send to BRINS]
    
    W --> X[BRINS Reviews]
    X --> Y{Acknowledge?}
    
    Y -->|Yes| Z[Status: Acknowledged]
    Z --> AA[acknowledged_by, acknowledged_date]
    AA --> AB[Update Nota.amount]
    AB --> AC[Update total_actual_paid if needed]
    AC --> AD[Update Reconciliation]
    
    Y -->|Dispute| AE[Initiate Dispute Resolution]
    AE --> AF[Document reasons]
    AF --> AG[Management Review]
    
    AD --> End2[Complete]
    AG --> End3[Resolve & Retry]
```

---

## 9. SLA Monitoring System

```mermaid
stateDiagram-v2
    [*] --> Active: SLA Rule Created
    
    state Active {
        [*] --> Monitoring
        
        state Monitoring {
            [*] --> CheckConditions
            CheckConditions --> EvaluateTrigger
            EvaluateTrigger --> [*]
        }
        
        Monitoring --> Triggered: Condition Met
        
        state Triggered {
            [*] --> CreateNotification
            CreateNotification --> DetermineRecipients
            DetermineRecipients --> SendNotifications
            SendNotifications --> [*]
        }
        
        Triggered --> Monitoring: Notification Sent
        
        state "Check Recurrence" as CheckRecur {
            [*] --> IsRecurring
            IsRecurring --> ScheduleNext: Yes
            IsRecurring --> StopMonitoring: No
        }
        
        Monitoring --> CheckRecur: After Trigger
        CheckRecur --> Monitoring: Continue
        CheckRecur --> Paused: Stop
    }
    
    Active --> Inactive: Disable Rule
    Inactive --> Active: Enable Rule
    Active --> [*]: Delete Rule
    
    note right of Triggered
        Trigger Conditions:
        - STATUS_DURATION
        - CREATED_DURATION
        - UPDATED_DURATION
        - DUE_DATE_APPROACHING
        - DUE_DATE_PASSED
    end note
```

---

## 10. User Role Permissions Matrix

```mermaid
graph TD
    subgraph "BRINS User Permissions"
        B1[Upload Batch] --> B2[View Own Batches]
        B2 --> B3[Confirm Branch Receipt]
        B3 --> B4[Submit Payment Intent]
        B4 --> B5[View Notas]
        B5 --> B6[Acknowledge DN/CN]
        B6 --> B7[Create Claims]
        B7 --> B8[View Reports]
    end
    
    subgraph "TUGURE User Permissions"
        T1[View All Batches] --> T2[Review Debtors]
        T2 --> T3[Approve/Reject Batches]
        T3 --> T4[Issue Notas]
        T4 --> T5[Process Claims]
        T5 --> T6[Create DN/CN]
        T6 --> T7[Match Payments]
        T7 --> T8[Reconciliation]
    end
    
    subgraph "Admin Permissions"
        A1[Manage MasterContracts] --> A2[Manage Contracts]
        A2 --> A3[Configure System]
        A3 --> A4[Manage Users]
        A4 --> A5[View Audit Logs]
        A5 --> A6[Approve Reopens]
        A6 --> A7[Override Actions]
        A7 --> A8[Full System Access]
    end
```

---

## 11. Integration Points

```mermaid
graph LR
    subgraph "External Systems"
        Bank[Banking System]
        Email[Email Service]
        WhatsApp[WhatsApp API]
        Storage[File Storage]
        Analytics[Analytics Platform]
    end
    
    subgraph "Core System"
        API[REST API Layer]
        PaymentService[Payment Service]
        NotificationService[Notification Service]
        FileService[File Service]
        ReportService[Report Service]
    end
    
    subgraph "Database Layer"
        DB[(PostgreSQL)]
        Cache[(Redis Cache)]
        Queue[(Message Queue)]
    end
    
    Bank -->|Payment Data| PaymentService
    PaymentService --> DB
    
    API --> NotificationService
    NotificationService --> Email
    NotificationService --> WhatsApp
    NotificationService --> Queue
    
    FileService --> Storage
    FileService --> DB
    
    ReportService --> Analytics
    ReportService --> DB
    
    API --> Cache
    DB --> Cache
```

---

## 12. Data Archival Strategy

```mermaid
flowchart TD
    Start[Daily Archive Job] --> A{Check Date}
    A --> B[Identify Closed Batches > 2 years]
    A --> C[Identify Paid Notas > 2 years]
    A --> D[Identify Settled Claims > 2 years]
    
    B --> E[Extract Batch Data]
    C --> F[Extract Nota Data]
    D --> G[Extract Claim Data]
    
    E --> H[Include Related Records]
    F --> H
    G --> H
    
    H --> I[Include Related Debtors]
    I --> J[Include Related Payments]
    J --> K[Include Audit Logs]
    
    K --> L[Create Archive Package]
    L --> M[Compress Data]
    M --> N[Store in Archive DB]
    
    N --> O{Verification}
    O -->|Success| P[Delete from Active DB]
    O -->|Fail| Q[Rollback & Alert]
    
    P --> R[Update Archive Index]
    R --> S[Generate Archive Report]
    
    Q --> End1[Manual Review Required]
    S --> End2[Archive Complete]
```

---

## Document Information

**Version**: 1.0  
**Created**: 2025-01-22  
**Purpose**: Detailed process flows and state machines for reinsurance system  
**Status**: Final
