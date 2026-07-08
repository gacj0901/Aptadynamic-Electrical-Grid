"""Validation helpers for conditional cascade severity."""

from __future__ import annotations

import numpy as np
import pandas as pd


def zipf_alpha(sizes: pd.Series, min_size: int = 2) -> float:
    x = np.sort(sizes[sizes >= min_size].to_numpy())[::-1]
    if len(x) < 10:
        return float("nan")
    rank = np.arange(1, len(x) + 1)
    slope, _ = np.polyfit(np.log(rank), np.log(x), 1)
    b = -slope
    return 1.0 + 1.0 / b if b > 0 else float("nan")


def precursor_enrichment(
    proj: pd.DataFrame,
    events: pd.DataFrame,
    large_q: float = 0.95,
    horizon_bins: int = 24,
    bin_s: int = 3600,
) -> dict:
    """Estimate conditional-severity enrichment for large cascades.

    The denominator is the unconditional large-cascade rate among cascades, so
    ``enrichment`` answers P(large | stressed precursor) / P(large).
    """

    sizes = events.groupby("cascade_id").size()
    if sizes.empty:
        return {
            "n_large": 0,
            "size_threshold": float("nan"),
            "p_large_given_precursor": float("nan"),
            "p_large_baseline": float("nan"),
            "p_precursor_given_large": float("nan"),
            "p_stressed_baseline": float(proj["stratum"].isin([2, 4]).mean()) if len(proj) else 0.0,
            "enrichment": float("nan"),
            "zipf_alpha_data": float("nan"),
        }

    t_start = events.groupby("cascade_id")["t_out"].min()
    threshold = sizes.quantile(large_q)
    is_large = sizes >= threshold

    t0 = proj["t"].iloc[0]
    idx = np.clip(((t_start.to_numpy() - t0) // bin_s).astype(int), 0, len(proj) - 1)
    stressed = proj["stratum"].isin([2, 4]).to_numpy()

    preceded = []
    for i in idx:
        lo = max(0, i - horizon_bins)
        preceded.append(bool(i > lo and stressed[lo:i].mean() > 0.5))
    preceded = np.asarray(preceded, dtype=bool)
    large = is_large.to_numpy(dtype=bool)

    p_large_base = float(large.mean())
    p_stressed_base = float(stressed.mean())
    p_large_given_precursor = float(large[preceded].mean()) if preceded.any() else 0.0
    p_precursor_given_large = float(preceded[large].mean()) if large.any() else 0.0

    return {
        "n_large": int(large.sum()),
        "size_threshold": float(threshold),
        "p_large_given_precursor": p_large_given_precursor,
        "p_large_baseline": p_large_base,
        "p_precursor_given_large": p_precursor_given_large,
        "p_stressed_baseline": p_stressed_base,
        "enrichment": p_large_given_precursor / max(p_large_base, 1e-12),
        "zipf_alpha_data": zipf_alpha(sizes),
    }
