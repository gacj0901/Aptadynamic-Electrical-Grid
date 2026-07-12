# G2 Verification 1 and H2 calibration measurements

**Status:** mechanical, calibration-only H2 record. Not confirmatory and not
eligible for confirmatory use. No cascade, severity or evaluation outcome was
constructed or read.

## Verification 1

- Effective start: `2008-11-02T13:00:00Z`
- Warm-up end (exclusive): `2008-12-04T09:00:00Z`
- Complete annual cycles: 2009, 2010
- Calibration end (exclusive): `2011-01-01T00:00:00Z`
- Calibration ID: `nyiso_calib_G2_v1`
- Domain end (exclusive): `2020-12-01T04:00:00Z`

The cut follows the closed rule in `G2_OD_CONTRACTS_H2.md`; it was not chosen
from an outcome. Counts and complete occupancy histograms are in
`G2_VERIFICATION_1.json`.

## Calibration-only measurements

| Channel | rho_I | C4_D | L_cal/tau |
|---|---:|---:|---:|
| CH-L | 0.7867936625757861 | 2.8521166462234575 | 56.38988095238095 |
| CH-P | 0.1745961112958041 | 14.30415530189674 | 56.38988095238095 |
| CH-F | 0.01008383734619267 | 1.351420271784084 | 56.38988095238095 |

`rho_I` and C4 are informational: H2 declares no admissibility band or f-star.
MEM uses the already-closed minimum of 20. The C4 null is stratified by the
channel's own induction context, with n_null=1000 and
provisional seed 0.

## Remaining H3 decisions

Only the items expressly reserved by H2 remain open: per-channel rho_I bands,
C4 f-star, bootstrap and tie-break seeds, and transcription of these verified
dates into the frozen preregistration. No confirmatory run is authorized by
this record.
