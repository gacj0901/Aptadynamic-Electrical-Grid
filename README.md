# Aptadynamic-VPA (Viability Power Administration)

**G.A.C.J.** | ORCID: 0009-0009-5649-1359
Copyright © 2026 G.A.C.J.
Released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**

---

## Overview
**Aptadynamic-VPA** is the reference implementation of the **PRAMA Protokol (Projection Protocol)** for evaluating the structural viability of electric transmission systems.
Rather than modeling the physical mechanisms responsible for outages, PRAMA projects observable operational data into an abstract viability space where the historical evolution of structural degradation can be quantified independently of the underlying domain.
This repository contains the first empirical validation of the Aptadynamic framework on real transmission outage datasets using **Bonneville Power Administration (BPA)** and **New York Independent System Operator (NYISO)** records.

---

# Aptadynamic
Aptadynamic is a theoretical framework for studying the **viability and structural persistence of complex systems under perturbation**.
Its primary object is **the trajectory of viability**, not the instantaneous state of the system.
Instead of asking

> *What is the current state of the system?*

Aptadynamic asks

> *How is the system's capacity to remain structurally viable evolving through time?*

The framework models historical accumulation, endogenous deformation of viability thresholds, structural margins, and latent degradation preceding observable collapse.

---

# PRAMA Protokol (Projection Protocol)

PRAMA Protokol is the operational protocol derived from Aptadynamic.
It is intentionally **domain-independent**.
PRAMA never models the internal physics, logic, semantics, or causal mechanisms of the observed system.
It operates exclusively on observable data streams.
Every application follows the same sequence:

```
Domain
↓
Observables Ω
↓
History H
↓
Projection
↓
Γ
↓
Regime Stratification
↓
Viability Assessment
```

The only domain-specific component is the observable extraction stage.
Everything downstream belongs to the protocol itself.

---

# Core Aptadynamic Coordinates
The protocol projects the observed trajectory into the aptadynamic space

```
Γ = (Δ, Ξ, λ, Θ, M, G)
```

where

### Δ(t)
**Structural decoupling.**
The normalized deviation between the current observation and its causal historical expectation.

```
Δ(t)=|O(t)-E[O│history]|/(E[O│history]+1)
```

The expectation is computed exclusively from past observations.

Δ therefore measures structural deviation rather than raw event intensity.

---

### Ξ(t)
**Historical structural tension.**

```
Ξ(t)=∫K(t-τ)Δ(τ)dτ
```

A genuinely non-Markovian accumulation of historical decoupling.

---

### λ(t)
**Historical permissivity.**
Represents the remaining operational capacity of the system.
Historical tension erodes λ, while recovery is bounded and never erases accumulated history.

---

### Θ(λ)
**Endogenous viability threshold.**
The admissible structural tension contracts as historical permissivity decreases.
The threshold therefore evolves with the trajectory rather than remaining externally fixed.

---

### M(t)
**Viability margin.**

```
M(t)=Θ(λ)-Ξ
```

Positive values indicate remaining structural viability.
Negative values indicate structural exhaustion.

---

### G(t)
**Structural generation power.**

```
G(t)=D⁺M
```
The forward derivative of the viability margin.
It measures whether structural viability is being generated or consumed.

---

# Latent Collapse
PRAMA distinguishes observable functionality from structural viability.
A system may continue operating while its viability margin is still positive but continuously deteriorating.
This condition is defined as **latent collapse**.

```
M ≥ 0
G < 0
```
Observable functionality persists despite ongoing structural degradation.
This allows PRAMA to identify deteriorating trajectories before conventional failure indicators appear.

---

# Regime Stratification
The protocol partitions the aptadynamic space into four operational regimes.

```
S₁  Stable
S₂  Stress
S₃  Critical
S₄  Collapse
```

Regimes are defined over the geometry of the viability space rather than over domain-specific variables.
Consequently, the same stratification framework applies across heterogeneous domains.

---

# Pipeline

```
ingest
↓
omega
↓
history
↓
projection
↓
stratification
↓
validation
```

### ingest
Raw outage records are transformed into canonical events.
All bus names are anonymized by irreversible hashing.

### omega
Canonical events are converted into observable streams Ω.
Current adapters include

* intensity
* load
* severity

No assumptions are made regarding outage mechanisms.

### history
Observations are accumulated into a causal historical representation.
Only past observations contribute to the current historical state.

### projection
The historical state is projected into the aptadynamic coordinates

```
Γ=(Δ,Ξ,λ,Θ,M,G)
```

### stratification
The projected trajectory is classified into structural viability regimes.

### validation
Predicted viability trajectories are compared against observed cascade behavior.
Zipf exponents and Hurst coefficients are treated exclusively as properties of the data, never as calibration targets.

---

# Empirical Results
## Bonneville Power Administration (1999–2017)
* Zipf exponent of cascade sizes:

```
α = 2.99
```

(reference: Dobson ≈ 2.87)
* Large-cascade enrichment (12-hour horizon)

```
×1.90
```

* Circular permutation test preserving autocorrelation

```
p < 0.005
```

* Latent-collapse condition substantially increases the conditional probability of large cascades.
* Combined causal structural decoupling achieves conditional enrichment ratios exceeding sixteen under the validated projection.

---

## Independent Replication

The protocol was independently evaluated on NYISO transmission outage data.
An initial negative result was traced to a degenerate definition of structural decoupling based on raw intensity.
After redefining Δ as **causal structural decoupling**, independent replication was obtained without modifying the aptadynamic kernel.
This demonstrates that protocol performance depends primarily on the quality of the observable projection rather than on the electrical infrastructure itself.

---

# Domain Independence

PRAMA Protokol is not a power-system model.
Power transmission constitutes only the first empirical domain.
The protocol requires only

```
Domain
↓
Observable extraction
↓
History
↓
Projection

---

# Usage

```bash
pip install -e .

python scripts/run_pipeline.py <path-to-outages.csv>

python scripts/sweep.py

python scripts/permtest.py

python scripts/latent_test.py

python scripts/baseline_test.py
```

---

# Data
Cleaned BPA outage data were kindly provided by **Dr. Ian Dobson**, Sandbulte Professor of Electrical and Computer Engineering, Iowa State University.
Dataset files are **not distributed** with this repository.
Bus names are anonymized in every generated output.
The analysis and conclusions presented here are solely those of the authors and do not represent the views of Bonneville Power Administration.

---

# Current Status
Implemented

* Domain-independent PRAMA Protokol
* Historical causal projection
* Structural viability coordinates
* Regime stratification
* Latent-collapse detection
* BPA empirical validation
* NYISO independent replication

Ongoing development

* Universal protocol specification
* Generalized embedding formulation
* Cross-domain adapters
* LLM viability experiments
* Formal protocol standardization

---

# License

This project is released under the **GNU Affero General Public License v3.0 (AGPL-3.0).**
Commercial licensing, industrial collaborations and academic research partnerships may be available separately.

