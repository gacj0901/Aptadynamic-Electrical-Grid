"""Proyección aptadinámica sobre Ω (Corpus §4).

    Δ(t)  = desacoplamiento observable (severity normalizada sobre baseline)
    Ξ(t)  = ∫ K(t-τ) Δ(τ) dτ, kernel exponencial con memoria genuina
    λ(t)  = permisividad histórica: erosión por Ξ, recuperación acotada
            (sin reincarnación markoviana: recuperación nunca borra Ξ)
    Θ(λ)  = umbral endógeno, contractivo con la historia
    M(t)  = Θ(λ) - Ξ         margen de viabilidad
    G(t)  = D⁺M              potencia de generación estructural
Colapso latente: O(t) > 0 ∧ M ≥ 0 ∧ G < 0.

Estratificación S₁–S₄ sobre (M, G): geometría en el plano margen-potencia,
no cortes rectangulares — frontera por curvas de nivel de M·sign(G) y ‖(M,G)‖.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ProjectionConfig:
    tau_memory: float = 24 * 14        # bins (h): memoria de Ξ, ~2 semanas
    lambda_eq: float = 1.0
    lambda_erosion: float = 0.02
    lambda_recovery: float = 0.005
    lambda_min: float = 0.1
    theta_scale: float = 2.0
    #baseline_win: int = 24 * 90        # bins: baseline móvil de Δ, ~90 días
    g_smooth: int = 24  
    kappa: float = 0.05               # suavizado de D⁺M
    #driver: str = "load"
    #driver: str = "intensity"
    #driver: str = "severity"

def project(omega: pd.DataFrame, cfg: ProjectionConfig = ProjectionConfig()) -> pd.DataFrame:
    from .omega import expected_profile

    obs = omega["intensity"].to_numpy(dtype=float)
    exp_ = expected_profile(omega)
    valid = ~np.isnan(exp_)
    delta = np.zeros(len(obs))
    delta[valid] = np.abs(obs[valid] - exp_[valid]) / (exp_[valid] + 1.0)

    n = len(delta)
    a = np.exp(-1.0 / cfg.tau_memory)
    xi = np.zeros(n)
    lam = np.full(n, cfg.lambda_eq)
    A = np.zeros(n)
    theta = np.zeros(n)
    theta[0] = cfg.theta_scale * cfg.lambda_eq

    for i in range(1, n):
        xi[i] = a * xi[i - 1] + (1 - a) * delta[i]
        excess = max(xi[i] - theta[i - 1], 0.0)
        A[i] = A[i - 1] + excess
        d_lam = -cfg.kappa * excess + cfg.lambda_recovery * (cfg.lambda_eq - lam[i - 1])
        lam[i] = np.clip(lam[i - 1] + d_lam, cfg.lambda_min, cfg.lambda_eq)
        theta[i] = cfg.theta_scale * lam[i]

    m = theta - xi
    g = np.gradient(pd.Series(m).rolling(cfg.g_smooth, min_periods=1).mean().to_numpy())

    out = omega.copy()
    out["delta"] = delta
    out["xi"] = xi
    out["lambda"] = lam
    out["theta"] = theta
    out["M"] = m
    out["G"] = g
    out["latent_collapse"] = (obs > 0) & (m >= 0) & (g < 0) & valid
    out["stratum"] = np.where(valid, stratify(m, g), 1)
    return out


def stratify(m: np.ndarray, g: np.ndarray) -> np.ndarray:
    s = np.ones(len(m), dtype=int)
    s[(m > 0) & (g < 0)] = 2
    s[(m <= 0) & (g >= 0)] = 3
    s[(m <= 0) & (g < 0)] = 4
    return s
