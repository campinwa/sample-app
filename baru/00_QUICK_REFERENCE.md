# Quick Reference Guide - Reinsurance System Data Model

## 📋 Executive Summary

Sistem ini mengelola proses reasuransi kredit antara **BRINS** (Cedant/Perusahaan Asuransi) dan **TUGURE** (Reinsurer). Sistem mencakup:

- **Premium Collection**: Upload debitur → Review → Invoicing → Payment
- **Claim Management**: Klaim → Verifikasi → Pembayaran → Subrogasi
- **Payment Reconciliation**: Matching pembayaran dengan invoice
- **Reporting & Compliance**: Bordero, audit trail, SLA monitoring

---

## 📊 Entity Overview

### Core Entities (20 total)

| Category | Entities | Purpose |
|----------|----------|---------|
| **Contract Management** | MasterContract, Contract | Template & active contracts |
| **Batch Processing** | Batch, Debtor, Record | Submission & review workflow |
| **Claims** | Claim, Subrogation | Loss events & recovery |
| **Billing** | Nota, DebitCreditNote | Invoicing & adjustments |
| **Reporting** | Bordero, Invoice | Periodic reports & billing |
| **Payment** | PaymentIntent, Payment, Reconciliation | Payment planning & matching |
| **Supporting** | AuditLog, Notification, NotificationSetting, SlaRule, EmailTemplate, SystemConfig | Audit, alerts, configuration |

---

## 🔄 Main Workflows

### 1. Premium Collection Flow
```
Upload Batch → Validate → Match Contract → Review Debtors → 
Approve Batch → Issue Nota → Confirm → Payment → Close
```

**Key Statuses**: Uploaded → Validated → Matched → Approved → Nota Issued → Branch Confirmed → Paid → Closed

### 2. Claim Processing Flow
```
Create Claim → Check → Doc Verify → Invoice → Payment → (Optional: Subrogation)
```

**Key Statuses**: Draft → Checked → Doc Verified → Invoiced → Paid

### 3. Payment Matching Flow
```
Payment Received → Match to Nota/Invoice → 
Handle Exceptions (DN/CN if needed) → Update Reconciliation
```

**Match Types**: Exact → MATCHED | Partial → PARTIAL | Over → OVERPAID + Credit Note

---

## 🗺️ Entity Relationship Map

```
MasterContract (Template)
    ↓
Contract (Active)
    ↓
├── Batch (Monthly submission)
│   ├── Debtor (Individual credit)
│   │   └── Record (Review tracking)
│   └── Nota (Premium invoice)
│       ├── Payment
│       └── DebitCreditNote (Adjustments)
│
├── Claim (Loss event)
│   ├── Subrogation (Recovery)
│   └── Nota (Claim payment)
│
├── Bordero (Summary report)
│   └── Invoice
│       ├── PaymentIntent (Planning)
│       └── Payment
│
└── Reconciliation (Period close)
```

---

## 🔑 Critical Fields

### Batch
- `final_premium_amount`: Final amount after debtor review (source for Nota)
- `debtor_review_completed`: TRUE when all debtors reviewed
- `batch_ready_for_nota`: TRUE when ready to invoice
- `operational_locked`: TRUE after Closed (prevents edits)

### Debtor
- `status`: DRAFT → SUBMITTED → APPROVED/REJECTED/CONDITIONAL
- `is_locked`: TRUE when batch closed
- `version_no`: Revision tracking
- `kolektabilitas`: Credit quality (1-5)

### Nota
- `amount`: **IMMUTABLE** after status = Issued
- `is_immutable`: Flag to prevent amount changes
- `total_actual_paid`: Accumulation of payments
- `reconciliation_status`: PENDING/PARTIAL/MATCHED/OVERPAID/FINAL

### Payment
- `match_status`: RECEIVED → MATCHED/PARTIALLY_MATCHED/UNMATCHED
- `exception_type`: NONE/PARTIAL/OVER/UNDER/LATE/FX
- `is_actual_payment`: TRUE for real payments (vs planning)

---

## ⚠️ Important Business Rules

### 1. Immutability Rules
- ✅ **Nota.amount** cannot change after Issued
- ✅ **Batch.final_premium_amount** cannot change after Closed
- ✅ **AuditLog** is append-only
- ✅ Use **DebitCreditNote** for adjustments

### 2. Workflow Rules
- ✅ Cannot skip statuses (strict progression)
- ✅ All debtors must be reviewed before Nota issuance
- ✅ Only APPROVED debtors count in final_premium_amount
- ✅ Batch reopen requires supervisor approval

### 3. Lock Mechanism
- ✅ `is_locked = TRUE` on debtors when batch closed
- ✅ `operational_locked = TRUE` prevents batch modifications
- ✅ Reopen process can unlock (with approval)

### 4. Payment Matching
- ✅ Exact match → Close Nota
- ✅ Partial payment → Keep Nota open
- ✅ Overpayment → Auto-create Credit Note
- ✅ Underpayment → May need Debit Note

---

## 📁 Document Reference

### 1. data_modelling.md
- Complete ERD with Mermaid diagrams
- Detailed entity descriptions
- Business rules and relationships
- Glossary and indexing strategy

### 2. process_flows.md
- Detailed state machines
- Sequence diagrams
- Payment matching algorithm
- Integration architecture

### 3. database_schema.md
- Complete SQL DDL statements
- Table definitions with constraints
- Indexes and performance tuning
- Views, triggers, and maintenance scripts

---

## 🎯 Quick Implementation Checklist

### Phase 1: Core Setup
- [ ] Create MasterContract table
- [ ] Create Contract table
- [ ] Create Batch table
- [ ] Create Debtor table
- [ ] Create Record table
- [ ] Set up audit logging

### Phase 2: Billing
- [ ] Create Nota table
- [ ] Create DebitCreditNote table
- [ ] Create Payment table
- [ ] Create Reconciliation table
- [ ] Implement matching logic

### Phase 3: Claims
- [ ] Create Claim table
- [ ] Create Subrogation table
- [ ] Link to Nota system
- [ ] Set up claim workflow

### Phase 4: Reporting
- [ ] Create Bordero table
- [ ] Create Invoice table
- [ ] Build summary views
- [ ] Set up periodic jobs

### Phase 5: Supporting Systems
- [ ] Notification system
- [ ] SLA monitoring
- [ ] Email templates
- [ ] System configuration

---

## 🔍 Common Queries Examples

### Get Batch Summary
```sql
SELECT 
    b.batch_id,
    b.status,
    b.total_records,
    b.final_premium_amount,
    n.nota_number,
    n.status as nota_status
FROM batch b
LEFT JOIN nota n ON b.batch_id = n.reference_id
WHERE b.contract_id = 'CONTRACT_ID';
```

### Check Payment Status
```sql
SELECT 
    n.nota_number,
    n.amount,
    n.total_actual_paid,
    n.amount - n.total_actual_paid as outstanding,
    n.reconciliation_status
FROM nota n
WHERE n.nota_number = 'NOTA_NUMBER';
```

### Debtor Review Status
```sql
SELECT 
    d.status,
    COUNT(*) as count
FROM debtor d
WHERE d.batch_id = 'BATCH_ID'
GROUP BY d.status;
```

### Reconciliation Check
```sql
SELECT 
    r.period,
    r.total_invoiced,
    r.total_paid,
    r.difference,
    r.status
FROM reconciliation r
WHERE r.contract_id = 'CONTRACT_ID'
AND r.period = 'YYYY-MM';
```

---

## 📊 Status Reference

### Batch Statuses
```
Uploaded → Validated → Matched → Approved → 
Nota Issued → Branch Confirmed → Paid → Closed
(+ Rejected, Reopen Requested, Reopened)
```

### Debtor Statuses
```
DRAFT → SUBMITTED → APPROVED/REJECTED/CONDITIONAL
```

### Nota Statuses
```
Draft → Issued → Confirmed → Paid
```

### Claim Statuses
```
Draft → Checked → Doc Verified → Invoiced → Paid
```

### Payment Match Statuses
```
RECEIVED → MATCHED/PARTIALLY_MATCHED/UNMATCHED
```

### Reconciliation Statuses
```
IN_PROGRESS → EXCEPTION/READY_TO_CLOSE → CLOSED
```

---

## 🔐 User Roles & Permissions

### BRINS User
- Upload batches
- View own batches
- Confirm branch receipt
- Submit payment intent
- Create claims
- Acknowledge DN/CN

### TUGURE User
- Review debtors
- Approve/reject batches
- Issue Notas
- Process claims
- Create DN/CN
- Match payments
- Reconciliation

### Admin
- Manage contracts
- Configure system
- Approve reopens
- Override actions
- Full access

---

## 📞 Key Contacts

| Module | Responsible | Contact |
|--------|-------------|---------|
| Contract Management | Contract Admin | - |
| Batch Processing | Operations Team | - |
| Claims | Claims Department | - |
| Finance/Payment | Finance Team | - |
| System Admin | IT Department | - |

---

## 🚀 Next Steps

1. **Review** all three detailed documents
2. **Validate** business rules with stakeholders
3. **Implement** database schema (start with Phase 1)
4. **Test** workflows in development environment
5. **Deploy** to staging for UAT
6. **Train** users on the system
7. **Go Live** with monitoring

---

## 📚 Document Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **Quick Reference** (this file) | Overview & quick lookup | All stakeholders |
| **data_modelling.md** | Complete data model & ERD | Architects, Developers |
| **process_flows.md** | Detailed workflows | Business Analysts, Developers |
| **database_schema.md** | SQL implementation | Database Admins, Developers |

---

## 📝 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-22 | Initial documentation |

---

**Status**: ✅ Final  
**Maintained By**: System Architecture Team  
**Last Review**: 2025-01-22
