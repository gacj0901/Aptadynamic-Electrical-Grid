# G2 data preflight — NYISO multichannel candidates

**Status:** H1 data inventory only; not a frozen preregistration.

**Run date:** 2026-07-12.

**Outcome access:** none. The script read only the count and temporal extent of
the already-ingested automatic-outage records. It did not construct cascades,
severity labels, calibration outcomes, or evaluation outcomes.

## Scope and reproducibility

The inventory covers every monthly archive from November 2008 through
December 2020, the full interval coextensive with the automatic NYISO outage
record. It was generated with:

```powershell
$env:PYTHONPATH='src;..\PRAMA-Protokol\PRAMA-Protokol-py\src'
.\venv\Scripts\python.exe scripts\g2_data_preflight.py `
  --start 2008-11 --end 2020-12 `
  --outages data\dobson_nyiso\outagesNYISO.csv `
  --cache "$env:TEMP\nyiso_g2_preflight" `
  --out results\g2_data_preflight_inventory.json --workers 4
```

The machine-readable local inventory has SHA-256
`09ab7568ccdbcb6263e69f5cbfaa1f3dfb82564cf7858c22bc347dd829a5079`.
It is regenerable and ignored by Git. The raw archives remain in the temporary
cache and are not redistributed.

## Sources and reuse boundary

| Candidate | Exact source | Native resolution and fields | Coverage inspected | Reuse status |
|---|---|---|---|---|
| CH-L | NYISO monthly Actual Load archives: `https://mis.nyiso.com/public/csv/pal/YYYYMM01pal_csv.zip` ([load-data index](https://www.nyiso.com/load-data)) | 5 min; timestamp, EST/EDT marker, zone, PTID, Load | 2008-11 through 2020-12 | Publicly downloadable; no explicit open-data licence was identified. Subject to the [NYISO Legal Notice](https://www.nyiso.com/legal-notice). |
| CH-P | NYISO monthly real-time zonal LBMP archives: `https://mis.nyiso.com/public/csv/realtime/YYYYMM01realtime_zone_csv.zip` ([custom-reports index](https://www.nyiso.com/custom-reports?report=ham_lbmp_zonal)) | nominally 5 min; timestamp, zone/proxy, PTID, LBMP and components | 2008-11 through 2020-12 | Same restriction as CH-L. |
| CH-F | Existing G1 outage-start intensity | 1 h in G1; unchanged legacy event record | Entire ingested outage record | Already governed by the repository's G1 provenance. |

NYISO's notice provides the material as-is and does not grant a licence or
ownership interest. Therefore this repository commits source URLs, code and
aggregate inventory statistics only. Raw NYISO files must not be committed or
redistributed without a separate rights review.

The EIA bulk balancing-authority archive is a documented fallback
([EIA Open Data](https://www.eia.gov/opendata/)), but it is not substituted in
this preflight: its temporal coverage and balancing-authority semantics would
change the candidate source instead of testing the primary NYISO archives.

## Coverage and gap inventory

The automatic-outage inventory contains 9,600 events from
`2008-11-02T12:27:00Z` through `2020-12-01T04:57:00Z`. After rounding inward
to the 5-minute grid, the coextensive interval contains 1,270,566 slots.
A slot is counted as complete only when all 11 internal NYISO zones are
present with a non-null channel value. External proxy zones (`H Q`, `NPX`,
`O H`, `PJM`) are excluded.

| Measure | CH-L | CH-P |
|---|---:|---:|
| Monthly ZIP archives | 146/146 | 146/146 |
| Daily CSV members | 4,420 | 4,442 |
| Source rows | 14,143,470 | 19,382,760 |
| Invalid timestamp rows | 0 | 0 |
| Duplicate internal-zone/timestamp rows | 0 | 0 |
| Null value rows | 338 | 0 |
| Complete 11-zone slots | 1,258,453 | 1,264,825 |
| Missing/incomplete 11-zone slots | 12,113 | 5,741 |
| Gap fraction | 0.9533546% | 0.4518459% |
| Complete fraction | 99.0466454% | 99.5481541% |

All 292 requested archives downloaded successfully (238,792,538 compressed
bytes); there was no silent imputation and no failed month was omitted.
EST/EDT timestamps were converted explicitly to UTC. The November 2008 DST
fallback pilot produced 8,136 complete CH-L slots and 8,137 complete CH-P
slots within the outage-overlap interval, with no invalid timestamps or
duplicate zone/timestamp rows.

The available pre-2011 interval contains more than two complete calendar
cycles plus the 720-hour warm-up required by the G2 skeleton. This establishes
feasibility of the temporal minimum; it does **not** select the G2 calibration
cut or certify the per-context minimum, which depend on the final channel
contract and remain decisions of program direction.

## Missing-data policy for this preflight

The inventory uses complete-case support at the native 5-minute grid:

1. no interpolation, forward fill or synthetic replacement;
2. a zonal slot is valid only when its source value and UTC timestamp are
   valid;
3. an all-zone candidate is valid only when all 11 internal zones are valid;
4. aggregation and resampling are not performed at preflight;
5. any future imputation, aggregation or hourly resampling rule must be fixed
   in the per-channel O_D contract before H3 and will open a new induction
   epoch if later changed.

## Evidence-supported conclusions; decisions remain open

- **CH-L is feasible:** it has dense, coextensive, real-system coverage and
  exposes exactly the 11 internal zones. Summing zones is technically
  possible, but `[DECISION: source and aggregation]` is not resolved here.
- **CH-P is feasible as a secondary candidate:** the zonal feed is denser
  than CH-L. The choice between a reference location and a zonal aggregate,
  and the exact trailing-volatility construction, remain open.
- **CH-F remains the unchanged G1 continuity channel.** No G1 outcomes were
  recomputed or inspected during this preflight.
- **Frequency/ACE remains a named observability gap:** no stable, public,
  historical official feed coextensive with 2008-11–2020-12 was verified in
  this preflight. Its `[DECISION]` remains open.
- **The rho_I band is not frozen by availability evidence.** The existing G1
  diagnostic values make the proposed band empirically consequential, but a
  G2 threshold must be chosen by program direction before evaluation and
  cannot be inferred from these coverage statistics.

No `[DECISION]` marker in `PREREGISTRATION_G2_SKELETON.md` is resolved by
this H1 record.

## Erratum — inventory SHA-256 (2026-07-12)

The inventory digest printed above was truncated to 63 characters by a
transcription error. The complete, reverified SHA-256 of
`results/g2_data_preflight_inventory.json` is
`09ab7568ccdcbcb6263e69f5cbfaa1f3dfb82564cf7858c22bc347dd829a5079`
(64 hexadecimal characters). This correction changes no source, coverage,
policy, statistic or decision in H1.
