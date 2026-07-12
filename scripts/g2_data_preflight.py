#!/usr/bin/env python
"""Inventory NYISO G2 candidate channels without reading evaluation outcomes."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from aptadynamic_eg import automatic_only, load_bpa


BASE = "https://mis.nyiso.com/public/csv"
CHANNELS = {
    "CH-L": {
        "directory": "pal",
        "archive": "{date}pal_csv.zip",
        "member_suffix": "pal.csv",
        "value": "Load",
    },
    "CH-P": {
        "directory": "realtime",
        "archive": "{date}realtime_zone_csv.zip",
        "member_suffix": "realtime_zone.csv",
        "value": "LBMP ($/MWHr)",
    },
}
NYISO_ZONES = {
    "CAPITL", "CENTRL", "DUNWOD", "GENESE", "HUD VL", "LONGIL",
    "MHK VL", "MILLWD", "N.Y.C.", "NORTH", "WEST",
}


def month_range(start: str, end: str) -> list[pd.Timestamp]:
    return [period.to_timestamp() for period in pd.period_range(start, end, freq="M")]


def archive_target(cache: Path, channel: str, month: pd.Timestamp) -> tuple[str, Path]:
    spec = CHANNELS[channel]
    name = spec["archive"].format(date=month.strftime("%Y%m01"))
    return f"{BASE}/{spec['directory']}/{name}", cache / channel / name


def download_one(url: str, target: Path) -> dict:
    if target.exists() and target.stat().st_size > 0:
        return {"url": url, "path": str(target), "bytes": target.stat().st_size, "cached": True}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "AptadynamiK-G2-preflight/1"})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
    temporary.replace(target)
    return {"url": url, "path": str(target), "bytes": target.stat().st_size, "cached": False}


def local_to_utc(frame: pd.DataFrame, channel: str) -> pd.Series:
    naive = pd.to_datetime(frame["Time Stamp"], errors="coerce")
    if channel == "CH-L":
        offsets = frame["Time Zone"].map({"EDT": 4, "EST": 5})
        return (naive + pd.to_timedelta(offsets, unit="h")).dt.tz_localize("UTC")

    result = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
    for _, indices in frame.groupby("Name", sort=False).groups.items():
        values = naive.loc[indices]
        localized = values.dt.tz_localize(
            "America/New_York", ambiguous="infer", nonexistent="shift_forward"
        ).dt.tz_convert("UTC")
        result.loc[indices] = localized
    return result


def inspect_channel(channel: str, archives: list[Path], overlap_start: pd.Timestamp, overlap_end: pd.Timestamp) -> dict:
    spec = CHANNELS[channel]
    complete_parts: list[np.ndarray] = []
    missing_values = invalid_timestamps = duplicate_rows = rows = 0
    observed_names: set[str] = set()
    member_count = 0

    for archive in sorted(archives):
        with zipfile.ZipFile(archive) as zipped:
            members = [name for name in zipped.namelist() if name.endswith(spec["member_suffix"])]
            member_count += len(members)
            for member in members:
                with zipped.open(member) as handle:
                    frame = pd.read_csv(handle)
                rows += len(frame)
                observed_names.update(str(value) for value in frame["Name"].dropna().unique())
                frame["utc"] = local_to_utc(frame, channel)
                invalid_timestamps += int(frame["utc"].isna().sum())
                missing_values += int(frame[spec["value"]].isna().sum())
                internal = frame[frame["Name"].isin(NYISO_ZONES)].copy()
                duplicate_rows += int(internal.duplicated(["Name", "utc"]).sum())
                table = internal.pivot_table(
                    index="utc", columns="Name", values=spec["value"], aggfunc="mean"
                )
                complete = table.reindex(columns=sorted(NYISO_ZONES)).notna().all(axis=1)
                # Pandas may preserve source-dependent datetime resolutions
                # (for example us from CSV parsing and ns from date_range).
                # Compare explicit epoch seconds so equality is resolution-safe.
                complete_parts.append(table.index[complete].as_unit("s").asi8)

    observed = np.unique(np.concatenate(complete_parts)) if complete_parts else np.array([], dtype=np.int64)
    start = overlap_start.ceil("5min")
    end = overlap_end.floor("5min")
    expected = pd.date_range(start, end, freq="5min", tz="UTC").as_unit("s").asi8
    within = observed[(observed >= expected[0]) & (observed <= expected[-1])] if len(expected) else observed
    present = int(np.intersect1d(expected, within, assume_unique=True).size)
    missing = int(len(expected) - present)
    return {
        "archives": len(archives),
        "csv_members": member_count,
        "rows": rows,
        "observed_names": sorted(observed_names),
        "nyiso_internal_zones": sorted(NYISO_ZONES),
        "missing_value_rows": missing_values,
        "invalid_timestamp_rows": invalid_timestamps,
        "duplicate_internal_zone_timestamp_rows": duplicate_rows,
        "overlap_start_utc": start.isoformat(),
        "overlap_end_utc": end.isoformat(),
        "expected_5min_slots": int(len(expected)),
        "complete_all_zone_5min_slots": present,
        "missing_all_zone_5min_slots": missing,
        "missing_all_zone_fraction": float(missing / len(expected)) if len(expected) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2008-11")
    parser.add_argument("--end", default="2020-12")
    parser.add_argument("--outages", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(os.environ.get("TEMP", ".")) / "nyiso_g2_preflight")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    months = month_range(args.start, args.end)
    jobs = [(channel, month, *archive_target(args.cache, channel, month)) for channel in CHANNELS for month in months]
    downloads: list[dict] = []
    failures: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, url, target): (channel, month, url) for channel, month, url, target in jobs}
        for future in as_completed(futures):
            channel, month, url = futures[future]
            try:
                downloads.append({"channel": channel, "month": month.strftime("%Y-%m"), **future.result()})
            except Exception as exc:  # recorded, never silently imputed
                failures.append({"channel": channel, "month": month.strftime("%Y-%m"), "url": url, "error": str(exc)})

    outages = automatic_only(load_bpa(args.outages))
    overlap_start = pd.to_datetime(outages["t_out"].min(), unit="s", utc=True)
    overlap_end = pd.to_datetime(outages["t_in"].max(), unit="s", utc=True)
    channels = {}
    for channel in CHANNELS:
        paths = [Path(row["path"]) for row in downloads if row["channel"] == channel]
        channels[channel] = inspect_channel(channel, paths, overlap_start, overlap_end)

    payload = {
        "schema": "AptadynamiK-G2-data-preflight/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "outcomes_accessed": False,
        "outage_inventory": {
            "automatic_events": len(outages),
            "start_utc": overlap_start.isoformat(),
            "end_utc": overlap_end.isoformat(),
        },
        "requested_months": [args.start, args.end],
        "archive_downloads": {
            "requested": len(jobs),
            "succeeded": len(downloads),
            "failed": len(failures),
            "compressed_bytes": sum(row["bytes"] for row in downloads),
            "failures": sorted(failures, key=lambda row: (row["channel"], row["month"])),
        },
        "channels": channels,
        "sources": {
            "CH-L": f"{BASE}/pal/YYYYMM01pal_csv.zip",
            "CH-P": f"{BASE}/realtime/YYYYMM01realtime_zone_csv.zip",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
