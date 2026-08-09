# Synthetic claims data dictionary

| Field | Type | Purpose |
|---|---|---|
| `claim_id` | string | Synthetic claim-line identifier |
| `beneficiary_id` | string | Synthetic beneficiary identifier |
| `provider_id` | string | Synthetic provider identifier |
| `provider_specialty` | string | Demonstration specialty grouping |
| `state` | string | Synthetic two-letter state |
| `date_of_service` | date | Used for policy effective-date logic |
| `procedure_code` | string | Demonstration HCPCS/CPT-format code |
| `modifier` | string | Demonstration claim modifier field |
| `therapy_category` | string | `PT`, `OT`, `SLP`, or `NONE` |
| `cumulative_therapy_spend_ytd` | float | Synthetic cumulative amount used for the KX example |
| `allowed_amount` | float | Synthetic allowed amount used for fee-variance simulation |
| `billed_amount` | float | Synthetic billed amount |
| `paid_amount` | float | Synthetic paid amount summarized as “in scope,” never treated as recoverable savings |
| `policy_mapping_status` | string | Synthetic configuration status for new-code mapping |
| `line_of_business` | string | Synthetic Medicare line-of-business label |
| `place_of_service` | string | Synthetic place-of-service code |
| `diagnosis_group` | string | Broad synthetic diagnostic grouping |
| `documentation_score` | float | Synthetic queue-prioritization feature; not a clinical score |
| `source_system` | string | Synthetic upstream system label |

All values are generated. No row represents a real healthcare transaction.
