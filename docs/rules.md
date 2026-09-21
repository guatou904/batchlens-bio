# Rules in ruleset 1.1

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

| BL-CELL-001 | warning | Fewer units meet the configured minimum cells within a cell type/condition |
| BL-CELL-002 | warning | Largest unit contributes strictly more than the configured share within a cell type/condition |
| BL-CELL-003 | warning | No cells for an observed cell type in a declared condition; eligible units come from the sample manifest |

Cell rules run only with `cell_coverage`. Zero-cell groups receive BL-CELL-003 instead of a redundant BL-CELL-001; largest share is null. Defaults 3 units / 20 cells / share >0.6 are review settings, not inference or power guarantees. All three point to their actual `cell_support` row and leave contrast estimability unchanged.

Schema/metadata errors (the planning category BL-META-001) are input validation failures with exit 2, not successful audit findings. They never produce a scientific pass. Each finding carries rule version, message, scope, JSON evidence pointers, limitations and a suggested next step. Severity reflects review/automation policy, not quantified biological harm.
