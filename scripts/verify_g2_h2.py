#!/usr/bin/env python
"""Run G2 Verification 1 and calibration-only H2 measurements."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from prama_protokol import KernelConfig
from prama_protokol.compliance import (
    check_density,
    check_inductive_ratio,
    check_memory_ratio,
)

from aptadynamic_eg import automatic_only, load_bpa
from aptadynamic_eg.g2 import (
    G2InterfaceConfig,
    build_hourly_domain,
    context_codes,
    find_verification_cut,
    normalize_and_project,
)


def git_sha(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def git_dirty(root: Path) -> bool:
    return bool(
        subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"], text=True
        ).strip()
    )


def iso(value: pd.Timestamp) -> str:
    return value.isoformat().replace("+00:00", "Z")


def occupancy_summary(
    index: pd.DatetimeIndex,
    valid: np.ndarray,
    day_type: bool,
) -> dict:
    codes = context_codes(index, day_type=day_type)
    if day_type:
        universe = [month * 1000 + hour * 10 + kind for month in range(1, 13)
                    for hour in range(24) for kind in range(2)]
    else:
        universe = [month * 100 + hour for month in range(1, 13)
                    for hour in range(24)]
    counts = pd.Series(codes[np.asarray(valid, dtype=bool)]).value_counts()
    occupied = np.array([int(counts.get(code, 0)) for code in universe], dtype=int)
    return {
        "n_cells": len(universe),
        "minimum": int(occupied.min()),
        "median": float(np.median(occupied)),
        "cells_below_10": int((occupied < 10).sum()),
        "histogram": {str(int(k)): int(v) for k, v in zip(
            *np.unique(occupied, return_counts=True)
        )},
    }


def write_markdown(
    path: Path,
    verification: dict,
    measurements: dict,
) -> None:
    rows = []
    for channel, record in measurements["channels"].items():
        rows.append(
            f"| {channel} | {record['RHO_I'].get('rho_I')} | "
            f"{record['C4'].get('C4_D')} | {record['MEM'].get('ratio')} |"
        )
    text = f"""# G2 Verification 1 and H2 calibration measurements

**Status:** mechanical, calibration-only H2 record. Not confirmatory and not
eligible for confirmatory use. No cascade, severity or evaluation outcome was
constructed or read.

## Verification 1

- Effective start: `{verification['t_start_utc']}`
- Warm-up end (exclusive): `{verification['warmup_end_exclusive_utc']}`
- Complete annual cycles: {', '.join(verification['complete_annual_cycles'])}
- Calibration end (exclusive): `{verification['calibration_end_exclusive_utc']}`
- Calibration ID: `{verification['calibration_id']}`
- Domain end (exclusive): `{verification['domain_end_exclusive_utc']}`

The cut follows the closed rule in `G2_OD_CONTRACTS_H2.md`; it was not chosen
from an outcome. Counts and complete occupancy histograms are in
`G2_VERIFICATION_1.json`.

## Calibration-only measurements

| Channel | rho_I | C4_D | L_cal/tau |
|---|---:|---:|---:|
{chr(10).join(rows)}

`rho_I` and C4 are informational: H2 declares no admissibility band or f-star.
MEM uses the already-closed minimum of 20. The C4 null is stratified by the
channel's own induction context, with n_null={measurements['n_null']} and
provisional seed {measurements['null_seed']}.

## Remaining H3 decisions

Only the items expressly reserved by H2 remain open: per-channel rho_I bands,
C4 f-star, bootstrap and tie-break seeds, and transcription of these verified
dates into the frozen preregistration. No confirmatory run is authorized by
this record.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outages", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--start", default="2008-11")
    parser.add_argument("--end", default="2020-12")
    parser.add_argument("--n-null", type=int, default=1000)
    parser.add_argument("--null-seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    cfg = G2InterfaceConfig()
    outages = automatic_only(load_bpa(args.outages))
    domain = build_hourly_domain(
        args.cache, outages, start=args.start, end=args.end
    )
    cut = find_verification_cut(domain, warmup_valid_hours=cfg.min_hist)
    calibration_end = cut["calibration_end_exclusive_utc"]
    cal = domain.index < calibration_end
    evaluation = ~cal

    channel_validity = {
        "CH-L": domain["ch-l_valid"].to_numpy(dtype=bool)
                & (domain["nyca_load_hourly"].to_numpy(dtype=float) > 0),
        "CH-P": domain["ch-p_valid"].to_numpy(dtype=bool),
        "CH-F": domain["ch-f_valid"].to_numpy(dtype=bool),
    }
    bins = {}
    occupancy = {}
    for channel, valid in channel_validity.items():
        bins[channel] = {
            "calibration_total": int(cal.sum()),
            "calibration_valid": int((cal & valid).sum()),
            "evaluation_total": int(evaluation.sum()),
            "evaluation_valid": int((evaluation & valid).sum()),
        }
        occupancy[channel] = {
            "verification_context_month_utc_x_hour_utc_x_day_type":
                occupancy_summary(domain.index[cal], valid[cal], day_type=True),
            "induction_context": occupancy_summary(
                domain.index[cal], valid[cal], day_type=channel != "CH-F"
            ),
        }

    verification = {
        "schema": "AptadynamiK-G2-verification-1/1",
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "outcomes_accessed": False,
        "outcome_columns_constructed": [],
        "implementation_commit": git_sha(root),
        "working_tree_dirty": git_dirty(root),
        "source_months": [args.start, args.end],
        "source_archive_count": 292,
        "t_start_utc": iso(cut["start_utc"]),
        "warmup_rule": "first 720 valid CH-L hours from t_start",
        "warmup_end_exclusive_utc": iso(cut["warmup_end_exclusive_utc"]),
        "complete_annual_cycles": [
            f"{start.year}" for start, _ in cut["cycles"]
        ],
        "calibration_id": "nyiso_calib_G2_v1",
        "calibration_end_exclusive_utc": iso(calibration_end),
        "domain_end_exclusive_utc": iso(cut["end_exclusive_utc"]),
        "full_hour_containment_rule": (
            "include [t,t+1h) only when fully contained in source/outage "
            "coverage; source-invalid hours remain rows with sigma_valid=0"
        ),
        "bins": bins,
        "context_occupancy": occupancy,
    }

    channels = {}
    kernel_cfg = KernelConfig()
    for channel in ("CH-L", "CH-P", "CH-F"):
        gamma, metadata = normalize_and_project(
            domain, channel, calibration_end=calibration_end, cfg=cfg
        )
        gamma_cal = gamma.loc[cal].reset_index(drop=True)
        context_cal = np.asarray(metadata.pop("context"))[cal]
        channels[channel] = {
            "schema_version": 2,
            "kernel_config": asdict(kernel_cfg),
            "interface_config": {
                "driver": metadata["driver"],
                "normalization": metadata["normalization"],
                "reference": format(metadata["reference"], ".17g"),
                "q_floor": format(metadata["q_floor"], ".17g"),
                "min_context_count": cfg.min_context_count,
                "min_hist": cfg.min_hist,
                "align_utc": True,
                "sigma_op_semantics": "valid_CH-L_and_load_above_calibration_q_floor",
                "trailing_days": cfg.trailing_days if channel != "CH-F" else None,
                "trailing_volatility_window": 1 if channel == "CH-P" else None,
            },
            "induction": {
                "epoch_id": metadata["epoch_id"],
                "estimator": metadata["estimator"],
                "regime": metadata["regime"],
                "estimator_hash": metadata["estimator_hash"],
            },
            "n_calibration_bins": int(cal.sum()),
            "n_valid_calibration_bins": int(gamma_cal["valid"].sum()),
            "RHO_I": check_inductive_ratio(
                gamma_cal["omega"].to_numpy(),
                gamma_cal["expected"].to_numpy(), band=None,
            ),
            "C4": check_density(
                gamma_cal,
                kernel_cfg,
                context=context_cal,
                n_null=args.n_null,
                seed=args.null_seed,
                f_star=None,
            ),
            "MEM": check_memory_ratio(
                kernel_cfg,
                n_cal=int(cal.sum()), min_ratio=20,
            ),
        }

    measurements = {
        "schema": "AptadynamiK-G2-H2-calibration-measurements/1",
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_mode": "calibration_only_interface_measurement",
        "confirmatory_eligible": False,
        "outcomes_accessed": False,
        "implementation_commit": git_sha(root),
        "working_tree_dirty": git_dirty(root),
        "calibration_id": verification["calibration_id"],
        "calibration_end_exclusive_utc": verification[
            "calibration_end_exclusive_utc"
        ],
        "n_null": args.n_null,
        "null_seed": args.null_seed,
        "threshold_status": {
            "rho_I": "informational_no_band_H3_decision",
            "C4": "informational_no_f_star_H3_decision",
            "MEM": "minimum_20_closed_in_H2",
        },
        "channels": channels,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "G2_VERIFICATION_1.json").write_text(
        json.dumps(verification, indent=2, allow_nan=False), encoding="utf-8"
    )
    (args.output_dir / "G2_H2_MEASUREMENTS.json").write_text(
        json.dumps(measurements, indent=2, allow_nan=False), encoding="utf-8"
    )
    write_markdown(
        args.output_dir / "G2_VERIFICATION_1.md", verification, measurements
    )
    print(json.dumps({
        "verification": {
            "t_start": verification["t_start_utc"],
            "warmup_end": verification["warmup_end_exclusive_utc"],
            "cycles": verification["complete_annual_cycles"],
            "cut": verification["calibration_end_exclusive_utc"],
        },
        "measurements": {
            channel: {
                "rho_I": record["RHO_I"].get("rho_I"),
                "C4_D": record["C4"].get("C4_D"),
                "MEM": record["MEM"].get("ratio"),
            }
            for channel, record in channels.items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
