# Rules in ruleset 1.0

| Rule | Severity | Evidence |
|---|---|---|
| BL-UNIT-001 | info | Multiple samples share a declared unit; shows unit/sample relationships |
| BL-UNIT-002 | warning | Target level has fewer than two distinct units; not a power calculation |
| BL-COVER-001 | warning | An empty target-by-batch combination; not automatically non-estimable |
| BL-COVER-002 | warning | Optional observation export omits samples |
| BL-DESIGN-001 | warning | Design rank below column count; inspect each contrast individually |
| BL-CONTRAST-001 | critical | Contrast lies outside numerical row space of the declared matrix |
| BL-SUPPORT-001 | warning | Sampling structure or sample-to-batch relation outside supported model |
| BL-NUMERIC-001 | warning | Condition number on retained subspace exceeds numerical review threshold |

Schema/metadata errors (the planning category BL-META-001) are input validation failures with exit 2, not successful audit findings. They never produce a scientific pass. Each finding carries rule version, message, scope, JSON evidence pointers, limitations and a suggested next step. Severity reflects review/automation policy, not quantified biological harm.
