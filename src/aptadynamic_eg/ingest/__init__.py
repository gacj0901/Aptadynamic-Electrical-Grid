"""Ingest BPA/NYISO outage CSV exports into canonical event rows."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

COLMAP = {
    "OutAbstime": "t_out",
    "InAbstime": "t_in",
    "Voltage": "voltage_kv",
    "Length": "length_mi",
    "Reactance": "reactance",
    "OutageType": "outage_type",
    "OutageID": "outage_id",
    "Duration": "duration_min",
}


def _anon(name: str) -> str:
    return hashlib.sha1(name.strip().lower().encode("utf-8")).hexdigest()[:10]


def _epoch_seconds(values: pd.Series, numeric_epoch: str = "unix") -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().mean() > 0.95:
        if numeric_epoch == "mathematica_1900":
            # Mathematica AbsoluteTime: seconds since 1900-01-01T00:00:00Z.
            numeric = numeric - 2_208_988_800
        elif numeric_epoch != "unix":
            raise ValueError(f"unsupported numeric epoch: {numeric_epoch}")
        return numeric.astype("Int64")
    parsed = pd.to_datetime(values, errors="coerce", utc=True)
    return (
        (parsed - pd.Timestamp(0, tz="utc"))
        // pd.Timedelta("1s")
    ).astype("Int64")


def load_bpa(path: str) -> pd.DataFrame:
    """Load a cleaned BPA/NYISO outage CSV into canonical event columns.

    Required output columns are ``t_out``, ``t_in`` and ``duration_s``. Bus names,
    when present, are replaced by stable hashes before returning the frame.
    """

    df = pd.read_csv(path)
    absolute_time_source = "OutAbstime" in df.columns
    df = df.rename(columns={k: v for k, v in COLMAP.items() if k in df.columns})

    if "t_out" in df.columns:
        df["t_out"] = _epoch_seconds(
            df["t_out"], "mathematica_1900" if absolute_time_source else "unix"
        )
    elif "OutDatetime" in df.columns:
        df["t_out"] = _epoch_seconds(df["OutDatetime"])
    else:
        raise ValueError(f"missing outage start time; columns present: {list(df.columns)}")

    if "t_in" in df.columns:
        df["t_in"] = _epoch_seconds(
            df["t_in"], "mathematica_1900" if absolute_time_source else "unix"
        )
    elif "InDatetime" in df.columns:
        df["t_in"] = _epoch_seconds(df["InDatetime"])
    elif "duration_min" in df.columns:
        duration = pd.to_numeric(df["duration_min"], errors="coerce").fillna(0.0)
        df["t_in"] = (df["t_out"].astype(float) + duration * 60.0).round().astype("Int64")
    else:
        df["t_in"] = df["t_out"]

    df = df.dropna(subset=["t_out"]).copy()
    df["t_in"] = df["t_in"].fillna(df["t_out"])
    df["t_out"] = df["t_out"].astype("int64")
    df["t_in"] = df["t_in"].astype("int64")
    df["duration_s"] = (df["t_in"] - df["t_out"]).clip(lower=0)

    for col in ("BusNames", "bus_names"):
        if col in df.columns:
            buses = df[col].astype(str).str.strip("{}").str.split(",", n=1, expand=True)
            df["bus_a"] = buses[0].fillna("").map(_anon)
            df["bus_b"] = buses[1].fillna("").map(_anon) if buses.shape[1] > 1 else ""
            df = df.drop(columns=[col])
            break

    drop = [c for c in ("Name", "NameClean", "LineName") if c in df.columns]
    if drop:
        df = df.drop(columns=drop)

    numeric_cols = ["voltage_kv", "length_mi", "reactance", "duration_min"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("t_out").reset_index(drop=True)


def automatic_only(df: pd.DataFrame) -> pd.DataFrame:
    """Keep automatic/forced outages when an outage-type column exists."""

    if "outage_type" not in df.columns:
        return df.reset_index(drop=True)
    mask = df["outage_type"].astype(str).str.strip().str.lower().isin(["auto", "forced"])
    return df[mask].reset_index(drop=True)
