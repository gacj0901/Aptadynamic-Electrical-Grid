# O_D Observation Contract

**Faithfulness conditions for the observation operator**  
Extracted and generalized from BPA and NYISO empirical cases.

An observation operator \( O_D : D \rightarrow \Omega \) is considered **PRAMA-faithful** if and only if it satisfies the following conditions:

### C1. Atomic Observable Event
There exists a timestamped stream of observable events without access to the domain’s internal state.  
**Examples**: BPA/NYISO → outages; LLM → token generation.

### C2. Proper Causal Conditional Expectation
\[
\widehat{O}(t) = E[O(t) \mid \text{domain's own rhythm}],
\]
computed exclusively from past observations.  

In the electrical grid case: \( E[\text{intensity} \mid \text{hour, month}] \).  
The original NYISO implementation violated this by using a constant global median, causing degeneration.

### C3. Δ as Structural Decoupling (not raw intensity)
\[
\Delta_t = \frac{|O_t - \widehat{O}_t|}{\widehat{O}_t + 1}
\]
Violation of C2 can make Ξ track raw activity instead of structural deviation.
Historical numerical claims from kernel 0.1.0 require causal revalidation.

### C4. Informational Density
The variance of Ξ over the characteristic memory timescale \( \tau_m \) must substantially exceed baseline stochastic noise.  
- BPA and NYISO density diagnostics are exploratory and must be regenerated
  under kernel 0.2.1 before quantitative comparison.

### C5. Bipartite Outcome
The domain must distinguish **occurrence** (\( Y_o \)) from **severity** (\( Y_s \)) separately.  
PRAMA only guarantees improved discrimination of conditional severity \( P(Y_s \mid Y_o) \). Occurrence forecasting remains the responsibility of causal Markovian baselines.

### C6. Stationary Evaluation Instrument

Causality is necessary but not sufficient. Comparison thresholds MUST be fitted
once on a declared, versioned calibration partition that is temporally disjoint
from evaluation, then frozen for the entire aggregated evaluation period.
Boundary ties use a declared seeded random rule. Any recalibration starts a new
calibration epoch (`calib_v1`, `calib_v2`, ...) and every readout carries that ID.
PRAMA warm-up is consumed inside the same calibration partition.

---

### Key Empirical Lesson

BPA and NYISO use the same universal projection kernel \( \pi \). Whether either
record supports an empirical claim is determined only by the reproducible 0.2.1
outputs, not by historical figures.
