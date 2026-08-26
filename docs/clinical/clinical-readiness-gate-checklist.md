# Проект На Clinical Readiness Gate Checklist

Статус: Draft за clinical-readiness planning. Не е одобрен gate record и не разрешава clinical pilot или donor-situation use.

Този документ дефинира начална gate checklist структура за решение дали HLA Transplantation Simulation проектът може да продължи към clinical-intended pilot/deployment planning. Всички gate items са draft и текущият статус е blocked/not complete.

## Цел

Целта е да се съберат основните blockers в една decision checklist, така че проектът да не премине към клинична употреба само защото има работещ backend или frontend prototype.

Gate checklist-ът трябва да бъде използван след controlled baseline, но преди:

- real donor/recipient/patient data processing;
- clinical workflow pilot;
- production-like clinical deployment;
- clinical claims;
- regulatory submission or market placement;
- use in an actual donor situation.

## Изходни Документи

- [Document Control Index Draft](document-control-index.md)
- [Approval Matrix Draft](approval-matrix.md)
- [Claims Control Matrix Draft](claims-control-matrix.md)
- [Change Impact Checklist Draft](change-impact-checklist.md)
- [Quality System Draft](quality-system.md)
- [Risk Management And Initial Risk Register](risk-register.md)
- [Software Lifecycle Draft](software-lifecycle.md)
- [Software Requirements Specification Draft](software-requirements.md)
- [Traceability Matrix Draft](traceability-matrix.md)
- [Software Architecture Draft](software-architecture.md)
- [Verification Plan Draft](verification-plan.md)
- [Usability Engineering File Draft](usability-engineering.md)
- [Validation Plan Draft](validation-plan.md)
- [Cybersecurity Plan Draft](cybersecurity-plan.md)
- [Data Governance Plan Draft](data-governance.md)
- [SOUP And Dependency Register Draft](soup-dependency-register.md)
- [Release And Deployment Plan Draft](release-deployment-plan.md)
- [Maintenance Plan Draft](maintenance-plan.md)
- [Problem Resolution And CAPA Plan Draft](problem-resolution-capa.md)

Официални външни references, проверени на 2026-08-26:

- ISO 13485:2016, Medical devices - quality management systems:
  https://www.iso.org/standard/59752.html
- IEC 62304:2006+AMD1:2015, Medical device software - software life cycle processes:
  https://webstore.iec.ch/en/publication/22794
- ISO 14971:2019, Medical devices - application of risk management:
  https://www.iso.org/standard/72704.html
- FDA Quality Management System Regulation (QMSR):
  https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr
- FDA Clinical Decision Support Software Guidance, January 2026:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- MDCG guidance index, including software, PMS/vigilance and PRRC guidance:
  https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents-and-other-guidance_en

## Gate Decision Rule

The default decision is `Blocked`. A gate may move to `Ready for formal review` only when every applicable item has:

- owner;
- evidence reference;
- reviewer;
- approval state;
- deviation decision if incomplete;
- linked risks and requirements.

No automatic pass is allowed. Missing evidence means blocked.

## Gate Checklist

| ID | Gate item | Required evidence | Current status |
| --- | --- | --- | --- |
| GATE-001 | Intended use frozen and approved. | Approved intended-use baseline | Blocked |
| GATE-002 | Claims matrix approved and user-facing wording reviewed. | Claims-control approval | Blocked |
| GATE-003 | Regulatory route and classification assessed. | Regulatory decision record | Blocked |
| GATE-004 | Manufacturer/legal responsible entity identified. | Legal/regulatory record | Blocked |
| GATE-005 | QMS/document-control process approved. | QMS/document-control record | Blocked |
| GATE-006 | Owners and approvers assigned. | Approval matrix with named accountable people | Blocked |
| GATE-007 | Requirements and traceability baselined. | Requirements baseline and traceability matrix | Blocked |
| GATE-008 | Risk management file reviewed and residual risks assessed. | Risk report and acceptability decision | Blocked |
| GATE-009 | Architecture/design records approved. | Architecture/design approval | Blocked |
| GATE-010 | Verification plan executed and report approved. | Verification report | Blocked |
| GATE-011 | Validation plan executed with representative cases and report approved. | Validation report and dataset record | Blocked |
| GATE-012 | Usability engineering validation complete for clinical UI. | Usability report and use-error review | Blocked |
| GATE-013 | Cybersecurity threat model, controls and security tests complete. | Cybersecurity report | Blocked |
| GATE-014 | Data governance/privacy approvals complete. | DPIA/privacy/data-governance record where applicable | Blocked |
| GATE-015 | SOUP register, SBOM and vulnerability review complete. | SBOM and dependency review | Blocked |
| GATE-016 | Release/deployment package complete. | Release checklist and deployment runbook | Blocked |
| GATE-017 | Maintenance, problem-resolution and CAPA workflows approved. | Maintenance/CAPA procedure records | Blocked |
| GATE-018 | Training, user documentation and competency expectations defined. | Training plan and records | Blocked |
| GATE-019 | Integration contracts preserve human oversight and provenance. | Downstream integration contract | Blocked |
| GATE-020 | Clinical pilot protocol, if any, approved by required institutional process. | Pilot protocol/ethics/institutional approval | Blocked |

## Gate Evidence Summary

| Evidence area | Current repository state | Gate result |
| --- | --- | --- |
| Intended use | Draft exists | Blocked until approved |
| Regulatory classification | Draft exists | Blocked until formal decision |
| Requirements/traceability | Drafts exist | Blocked until baseline and review |
| Architecture | Draft exists | Blocked until approved design baseline |
| Verification | Plan draft exists; automated tests exist | Blocked until executed verification report |
| Validation | Plan draft exists | Blocked until validation execution/report |
| Usability | Usability file draft exists | Blocked until formative/summative evidence |
| Cybersecurity | Plan draft exists | Blocked until threat model/security tests |
| Data governance | Plan draft exists | Blocked until data approvals and retention/access controls |
| SOUP/dependencies | Register draft exists | Blocked until SBOM and vulnerability review |
| Release/deployment | Plan draft exists | Blocked until release/deployment rehearsal |
| Maintenance/CAPA | Drafts exist | Blocked until approved workflow and records |
| Training | Not started | Blocked |
| Clinical pilot | Not started | Blocked |

## Gate Decision Values

| Decision | Meaning |
| --- | --- |
| Blocked | Required evidence missing or not approved. |
| Ready for formal review | Evidence appears complete enough for assigned reviewers. |
| Approved for non-clinical use | Approved only for development/demo/validation-planning scope. |
| Approved for controlled validation | Approved only for defined validation activity, not clinical care. |
| Approved for clinical pilot | Approved only under defined protocol/environment/user group. |
| Rejected | Gate failed and cannot proceed without corrective action. |

## Clinical-Use Blockers

Current gate result: `Blocked`.

Reasons:

- all key records are drafts, not approved baselines;
- no formal regulatory classification decision;
- no executed validation report;
- no completed usability validation;
- no implemented RBAC/TLS/SBOM/retention production controls;
- no named owners/approvers;
- no release/deployment rehearsal;
- no maintenance/CAPA controlled workflow;
- no clinical pilot protocol or institutional approval.

## Step 12 Conclusion

This checklist makes the current blocked status explicit. It does not approve clinical pilot, clinical deployment or donor-situation use.
