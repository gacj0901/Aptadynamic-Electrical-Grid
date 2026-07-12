# G2 — CONTRATOS O_D POR CANAL Y VERIFICACIÓN 1 (H2)

**Estatus:** texto normativo de H2, cerrado para implementación. Incorpora
las decisiones de dirección del 2026-07-12. Queda para H3, y solo para H3:
banda de ρ_I por canal (tras medición en calibración), f\* de C4, semillas
nuevas de bootstrap y desempate, y las fechas que Verificación 1 produzca.
Ninguna otra casilla queda abierta.

**Jerarquía normativa:** PREREGISTRATION_G2 (al congelar H3) > este
documento > Despliegue O_D v0.2 > contrato desplegado C1–C7 > AS-1/Corpus.
Los invariantes del programa (kernel intocable, evidencia intocable, G1 solo
anexable) rigen sin excepción.

**Decisiones de dirección incorporadas (2026-07-12):** bins horarios UTC
(reloj v2); CH-L = media horaria de la carga NYCA total (suma de las 11
zonas internas) como **canal primario**; CH-P = desviación estándar
intra-hora del LBMP promedio zonal, ventana de volatilidad como parámetro
del contrato congelado en 1; frecuencia/ACE = 𝓑ₒ residual nombrada; corte
temporal por regla (Verificación 1); régimen del estimador = ventana
trailing de 3 años por celda; σ_op sobre carga con q_floor = 5% de la
mediana de calibración; umbrales de admisibilidad en H3 tras medición.

---

## 1. Definiciones comunes del dominio (época v2)

### 1.1 Reloj y grilla

Bins horarios UTC alineados: bordes en múltiplos exactos de 3600 s
(`align_utc=True`). Grilla nativa de fuentes: 5 minutos. Regla de
remuestreo, idéntica para todo canal:

- un **slot** de 5 min es válido ⟺ las 11 zonas internas NYISO presentes
  con valor no nulo y timestamp UTC válido (zonas proxy externas excluidas:
  H Q, NPX, O H, PJM);
- una **hora** es válida ⟺ sus 12 slots son válidos (caso-completo; sin
  interpolación, sin forward-fill, sin imputación de ninguna clase);
- una hora inválida en un canal invalida la fila de ese canal
  (σ_valid = 0), no la de los demás.

### 1.2 Intersección triple y dominio temporal

El dominio temporal de G2 es la intersección de cobertura de CH-L, CH-P y
el registro de outages automáticos (2008-11 → 2020-12 según preflight H1),
sobre la grilla horaria v2. Verificación 1 (§6) computa sus bordes exactos
y el corte de calibración.

### 1.3 σ_op del dominio (cierra la derogación §9.7)

Un único indicador de operación para todo el dominio, derivado de CH-L:

    σ_op(t) = 1 ⟺ hora t válida en CH-L ∧ Load_NYCA(t) > q_floor,
    q_floor = 0.05 · mediana{Load_NYCA(s) : s ∈ calibración, s válida}

congelado por época. Codifica continuidad observable de operación del
sistema; no está definido sobre el ancla de cascada y no es tautológico en
los puntos de evaluación. La semántica G1 (`sigma_semantics_v1_activity`)
queda derogada para toda corrida de época v2; se reporta una sola vez como
sensibilidad histórica etiquetada, si se reporta.

### 1.4 Época, esquema y registro de drivers

- Épocas C7 de esta especificación: `nyiso_chl_induction_v1`,
  `nyiso_chp_induction_v1` (canales nuevos, primera época) y
  `nyiso_chf_induction_v2` (canal legado sobre reloj v2). Los pases de
  compuerta no se heredan de G1.
- Todo reporte: `schema_version: 2`, bloques `kernel_config` /
  `interface_config` (por canal) / `induction` con `epoch_id`, `estimator`,
  `regime`, `estimator_hash` (SHA-256 del fuente UTF-8 del estimador vía
  `inspect.getsource`).
- `DRIVER_SPECS` se extiende: `nyca_load_hourly` y `lbmp_intrahour_std`
  con `causal: True` y nota del contrato de disponibilidad — ambos feeds
  son publicaciones en tiempo real de NYISO; los archivos históricos usados
  son el archivo de esas publicaciones, luego el contenido era conocible en
  t. `severity` permanece bloqueado.

### 1.5 Kernel

Universal, invariante, sin ajuste por dominio ni outcome:
`prama-protokol==0.2.1` (identidad bit-certificada), configuración idéntica
a G1 — τ=336 (bins horarios), λ_eq=1.0, r=0.005, λ_min=0.1, θ_s=2.0,
g_smooth=24, κ=0.05. Una proyección Γ **por canal** (P0: sin observable
compuesto, sin síntesis de canales en ninguna capa).

---

## 2. Contrato CH-L — carga NYCA (CANAL PRIMARIO)

**C1 — Observable atómico.** Para cada slot válido, Load_NYCA = suma del
campo Load de las 11 zonas internas. Para cada hora válida,
L(t) = media de los 12 valores Load_NYCA del intervalo [t, t+1h). Unidad
fuente: MW. Justificación de la suma: el outcome es de sistema; el
observable de estado debe serlo.

**𝔑_D — Normalización (contrato N1).**

    ω(t) = L(t) / L_ref,
    L_ref = mediana{L(s) : s ∈ calibración, s válida}

L_ref se congela por época y se registra en `interface_config` con 17
dígitos significativos. ω es adimensional; la forma Δ = |ω−ω̂|/(ω̂+1)
opera lejos del régimen ω̂≈0 (ω̂ ≈ 1 por construcción). Ceros: una carga
horaria de 0 MW con hora válida es físicamente inadmisible y se trata como
hora inválida, registrada. Saturación: sin recorte; los valores extremos
son señal, no defecto.

**C2 — Expectativa causal propia (capa de inducción).**

- Estimador: media condicional causal por celda de contexto.
- Contexto: mes_UTC × hora_UTC × tipo_de_día, con tipo_de_día ∈
  {laborable, no-laborable} definido sobre el calendario local
  America/New_York (no-laborable = sábado y domingo locales). Los feriados
  federales cuentan como su día de semana: aproximación declarada, aceptada
  para evitar dispersión de celdas. La mezcla hora-UTC/día-local es
  deliberada y declarada; el emborronamiento DST de ±1 h es aceptado y es
  estrictamente menor que el desfase arbitrario de G1.
- **Régimen: ventana trailing de 1096 días (3 años) por celda** (§6.2
  v0.2, regla congelada; su cambio abre época). Una fila tiene ω̂ definido
  ⟺ su celda acumula ≥ min_context_count = 10 observaciones válidas dentro
  de la ventana; si no, σ_valid = 0. min_hist = 720 h de warm-up global.
- Causalidad: ω̂(t) usa exclusivamente observaciones estrictamente
  anteriores a t (verificable por truncamiento, compuerta C2).

**C3 — Anti-degeneración.** Dos ramas, bi-particional, s_min = 0.01,
r\* = 0.5, rama decisoria en el registro (idéntico al contrato desplegado).

**C4 / ρ_I / MEM.** Computados por época sobre calibración en H2
(medición sin outcome); umbrales congelados en H3. Nulo de C4: permutación
estratificada por el mismo contexto del estimador, n_null = 1000, semilla
declarada en H3. MEM: mínimo ya congelado, L_cal/τ ≥ 20.

**C5 — Outcomes.** Ocurrencia y severidad son outcomes distintos evaluados
por separado; ninguna superioridad es garantía contractual.

**C6/C7.** Instrumento de evaluación congelado tras calibración; época
`nyiso_chl_induction_v1` con `estimator_hash` en todo reporte.

---

## 3. Contrato CH-P — volatilidad intra-hora del LBMP (secundario)

**C1 — Observable atómico.** Para cada slot válido,
P(slot) = media no ponderada del LBMP en tiempo real de las 11 zonas
internas ($/MWh). Para cada hora válida,
s(t) = desviación estándar muestral (ddof=1) de los 12 valores P(slot) del
intervalo [t, t+1h). Es volatilidad realizada intra-hora: el primitivo sin
memoria propia.

**Parámetro del contrato:** `trailing_volatility_window = 1` hora,
**congelado**. Toda la integración temporal pertenece al kernel (Ξ, τ=336);
apilar memoria en el instrumento repartiría la persistencia entre dos
integradores y emborronaría la atribución. Cambiar este parámetro abre
época nueva de CH-P.

**𝔑_D — Normalización.**

    ω(t) = log1p( s(t) / P_ref ),
    P_ref = mediana{s(u) : u ∈ calibración, u válida}

P_ref congelado por época, registrado con 17 dígitos. El log1p es parte
declarada del contrato: las colas del LBMP son pesadas (spikes de órdenes
de magnitud) y sin compresión declarada la varianza de Δ quedaría dominada
por un puñado de eventos extremos; log1p preserva el orden de severidad
(monótona) y el cero (s=0 → ω=0). Ceros: s(t)=0 con hora válida es
admisible (precio plano) y entra como ω=0. Saturación: sin recorte.

**C2.** Misma familia, contexto y régimen que CH-L (media condicional
causal, mes_UTC × hora_UTC × tipo_de_día local, trailing 1096 días,
min_context_count=10, min_hist=720). **C3–C7:** como CH-L, con época
`nyiso_chp_induction_v1`.

---

## 4. Contrato CH-F — intensidad de outages (continuidad comparativa)

**C1.** Conteo de inicios de outage automáticos por bin horario del reloj
v2 (mismo filtro y misma definición de cascada que G1; gap > 3600 s).
ω = conteo, adimensional por naturaleza.

**C2.** Familia y contexto de G1 (media condicional causal expansiva,
mes_UTC × hora_UTC, min_context_count=10, min_hist=720) **sobre el reloj
v2**: el cambio de reloj abre la época `nyiso_chf_induction_v2`. Se
conserva el régimen expansivo de G1 deliberadamente: el rol del canal es
continuidad comparativa — aislar el efecto del reloj y de las compuertas
nuevas sobre el instrumento viejo —, no competir. Sus fallos de compuerta
(esperables: ρ_I de G1 fue −0.022) se reportan y no afectan nada más.

**C3–C7:** como los demás; canal secundario a todos los efectos de §5 del
skeleton.

---

## 5. Evaluación (sin cambios de fondo respecto al skeleton)

Outcomes idénticos a G1 en definición; severidad = ceil(P95) de cascadas
completas de calibración G2, entero congelado; evaluación estricta en
idx−1 sobre filas válidas post-calibración del canal correspondiente;
unidad = cascada; contraste pareado por bootstrap de cascadas
(n = 10,000), nulo de alineación por desplazamiento circular (n = 10,000,
mínimo 24 bins); presupuesto de alerta igualado por el mecanismo G1
(order-statistic + desempate sembrado). Comparador primario: la línea base
de mayor enriquecimiento **en calibración** entre B-TRIV, B-VAR, B-AC1 y
B-COMP (rango promedio de varianza y AC1), todas causales, B-VAR/B-AC1 con
ventana = 336 h sobre el residual ω−ω̂ del canal primario. Los contrastes
no primarios se reportan con corrección de Holm. Reclamación primaria:
**CH-L**, éxito ⟺ contraste > 0 y p unilateral < 0.01 condicionado a
compuertas. Clasificación y cláusula de falsación: §0 y §7 del skeleton,
sin modificación.

---

## 6. VERIFICACIÓN 1 — cómputo mecánico del corte de calibración

Entrada: la grilla horaria v2 de la intersección triple (§1.2), con las
máscaras de validez por canal ya aplicadas. Sin acceso a outcomes: la
verificación usa exclusivamente timestamps y validez.

Definiciones cerradas:
- **Inicio efectivo** t_start: primera hora de la intersección triple.
- **Warm-up**: las primeras 720 horas válidas del canal primario desde
  t_start.
- **Ciclo anual completo**: intervalo [1 de enero 00:00 UTC, 31 de
  diciembre 23:00 UTC] de un año calendario íntegramente contenido en la
  intersección triple y posterior al fin del warm-up.
- **Regla del corte**: fin de calibración (exclusivo) = 1 de enero 00:00
  UTC del año siguiente al segundo ciclo anual completo. Todo lo anterior
  es calibración; todo lo posterior, evaluación.

Salida comprometida (`G2_VERIFICATION_1.md` + JSON): t_start, fin de
warm-up, ciclos identificados, fecha de corte, `calibration_id =
nyiso_calib_G2_v1` con la fecha en el registro, n_bins de calibración y
evaluación por canal, e histograma de ocupación de celdas de contexto en
calibración (mes × hora × tipo_de_día: 576 celdas; reporte de mínimo,
mediana y celdas < 10) por canal. El histograma es diagnóstico: la
exclusión de filas sin cobertura la aplica el runtime (σ_valid), no un
juicio manual.

Nota de expectativa, no de regla: con el preflight en mano, la regla
produce previsiblemente corte = 2011-01-01T00:00:00Z (warm-up nov–dic
2008; ciclos 2009 y 2010). Vale lo que compute la verificación, no esta
nota.

---

## 7. Mediciones H2 (sin outcome) y congelamiento H3

Tras Verificación 1, se computan y comprometen **sobre calibración
únicamente**: ρ_I, C4_D (nulo estratificado, n_null=1000, semilla
provisional 0 — la semilla definitiva de H3 no altera una medición
informativa) y MEM, por canal. H3 congela entonces: banda de ρ_I por canal
y f\* de C4 — registrando en el mismo documento los valores medidos junto
a los umbrales elegidos, con justificación escrita de una línea por umbral
(auditabilidad: el mecanismo es seguro porque armar compuertas arma la
cláusula de falsación, pero debe además verse) —, semilla de bootstrap,
semilla de desempate, y las fechas de Verificación 1 transcritas. Con H3
congelado y hasheado, la corrida confirmatoria queda autorizada; ninguna
edición posterior salvo error demostrado registrado en ANOMALIES.
