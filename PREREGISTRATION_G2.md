# PREREGISTRATION G2 — NYISO multicanal, confrontación de dominio (H3)

**Estatus:** preregistro confirmatorio. Al comprometerse este documento
(commit H3), su texto queda congelado y es append-only: ninguna edición
posterior salvo enmienda anexada al final, y ningún parámetro de §5–§8 es
enmendable tras exposición a outcomes de evaluación por ninguna razón
distinta de un error demostrado de implementación registrado en
ANOMALIES.md antes de re-correr.

**Documentos incorporados por referencia (partes normativas de este
preregistro):** `G2_OD_CONTRACTS_H2.md` (contratos O_D por canal, σ_op,
normalizaciones, régimen del estimador, Verificación 1),
`G2_DATA_PREFLIGHT.md` (fuentes y frontera de licencia),
`G2_VERIFICATION_1.md` y `G2_H2_MEASUREMENTS.json` (mediciones sin outcome).
Anclas: preflight H1 = `37857b5`; fe de erratas del inventario = `3c4e3db`;
inventario SHA-256 =
`09ab7568ccdcbcb6263e69f5cbfaa1f3dfb82564cf7858c22bc347dd829a5079`;
H2 = `688e26f`, `401e8e6`; conformidad N1 = `9a6abe7`; kernel
`prama-protokol==0.2.1`, tag `v0.2.1` =
`69a51de562910539a2b4c3755f167dd0789ad32d`, golden fixture
`d92de6a187b3bd8a634b286a4886a839746b04ea8300d6b480acde3e59766516`.

**Checklist previo al commit H3:** [x] SHA-256 del inventario revalidado
contra el archivo local: 64 caracteres hexadecimales exactos.

---

## 0. Tesis y cláusula de falsación a nivel de programa

**Tesis de dominio (dirección del programa, 2026-07-11):** la red eléctrica
es el dominio de confrontación indispensable. El programa no se reserva la
migración a dominios de observables más blandos como respuesta a un fallo
aquí.

**Cláusula de falsación (congelada):**

> Si, con un operador de observación multicanal que supera las compuertas
> operacionales de §5 sobre las particiones congeladas de §3, PRAMA no
> supera en el contraste pareado preinscrito (§7) ni a la línea base
> trivial ni a los indicadores estándar de critical slowing down, el
> resultado se registra como **falsación a nivel de programa de la
> hipótesis de valor incremental de PRAMA**, no como fallo local del
> dominio ni del dataset. Esta clasificación no admite reinterpretación
> posterior por ninguna vía distinta de un error demostrado de
> implementación registrado en ANOMALIES.md.

Simetría declarada: un contraste positivo bajo idénticas condiciones recibe
el peso simétrico — primer resultado confirmatorio del programa no
atribuible a fugas ni a diseño benevolente.

**Perfil de tarea (§16.1 v0.2):** T_D = {inducción, resolución,
interpretación}. La capa de predicción no se declara; la evaluación es
discriminación de severidad de estado final en `idx−1`. Prohibidos los
enunciados de alerta temprana en todo reporte derivado de G2.

---

## 1. Dominio y épocas

**G2 es mono-dominio: NYISO.** BPA no entra porque no existe un preflight
coextensivo comprometido para sus canales; su eventual incorporación
(BPA-O_D-v2, observable voltaje-ponderado causal) requerirá su propio
preflight, contratos y preregistro. Esta exclusión es una decisión de
dirección transcrita, no una omisión.

Épocas C7: `nyiso_chl_induction_v1` (CH-L, **canal primario**),
`nyiso_chp_induction_v1` (CH-P, secundario), `nyiso_chf_induction_v2`
(CH-F, continuidad comparativa). Ningún pase de compuerta se hereda de G1.
Brecha de observabilidad residual nombrada: frecuencia/ACE (sin feed
público histórico estable coextenso; 𝓑ₒ declarada, no computada).

Outcomes idénticos a G1 en definición (cascadas por gap > 3600 s, filtro
automático); G1 vs G2 difieren en S_t, no en Y.

## 2. Datos

Por referencia al preflight H1: fuentes NYISO oficiales (carga zonal 5 min;
LBMP tiempo real zonal 5 min), 2008-11 → 2020-12, política de
casos-completos sin imputación, crudos fuera de Git por frontera de
licencia. Reloj v2: bins horarios UTC alineados; hora válida ⟺ 12/12
slots válidos; slot válido ⟺ 11/11 zonas internas.

## 3. Particiones (origen mecánico — Verificación 1)

- `calibration_id = nyiso_calib_G2_v1`
- Corte (exclusivo): **2011-01-01T00:00:00Z** — producido por la regla
  congelada (≥2 ciclos anuales completos + warm-up de 720 h dentro de la
  intersección triple), no por elección. Ciclos completos: 2009 y 2010;
  warm-up: nov–dic 2008.
- Calibración: intersección triple estrictamente anterior al corte.
  Evaluación: del corte a 2020-12. Umbral de severidad: ceil(P95) de
  cascadas completas de calibración, entero congelado al primer cómputo.
- Política: calibración disyunta y congelada; ningún reajuste en
  evaluación; warm-up consumido dentro de calibración.

## 4. Operador de observación

Íntegramente por referencia a `G2_OD_CONTRACTS_H2.md`: CH-L = media horaria
de la carga NYCA (suma de 11 zonas), ω = L/L_ref con L_ref mediana de
calibración congelada; CH-P = desviación estándar intra-hora del LBMP
promedio zonal, `trailing_volatility_window = 1` congelado,
ω = log1p(s/P_ref); CH-F = intensidad de outages sobre reloj v2 con
estimador G1 (rol: continuidad). Inducción de CH-L/CH-P: media condicional
causal por mes_UTC × hora_UTC × tipo_de_día local, **ventana trailing de
1096 días**, min_context_count = 10, min_hist = 720. σ_op del dominio:
carga válida ∧ Load_NYCA > 5% de la mediana de calibración (cierra la
derogación §9.7). Kernel universal invariante, config G1 (τ=336 bins
horarios, λ_eq=1.0, r=0.005, λ_min=0.1, θ_s=2.0, g_smooth=24, κ=0.05).
P0: una proyección Γ por canal; ningún observable compuesto.

## 5. Compuertas de admisibilidad (congeladas, con mediciones adjuntas)

Aplicación **por canal y por partición** (calibración y evaluación,
independientes). En la corrida, las compuertas de la partición de
evaluación se computan antes de cualquier estadístico dependiente de
outcomes. Mediciones de calibración: `G2_H2_MEASUREMENTS.json` (H2, sin
outcomes).

| Compuerta | Umbral congelado | Medición calibración (CH-L / CH-P / CH-F) | Estado calibración |
|---|---|---|---|
| C2 causalidad | igualdad exacta bajo truncamiento | verificada en suite | ✓ / ✓ / ✓ |
| C3 anti-degeneración | rama relativa: separación > 0.01; rama absoluta: \|r\| < 0.5; bi-particional | por computar en corrida (ambas particiones) | — |
| ρ_I (banda bilateral) | CH-L **[0.10, 0.95]**; CH-P **[0.10, 0.90]**; CH-F **[0.10, 0.90]** | 0.7868 / 0.1746 / 0.0101 | ✓ / ✓ / **✗** |
| C4 densidad | **f\* = 1.5 por canal y por partición**; nulo = permutación estratificada por contexto | 2.8521 / 14.3042 / 1.3514 | ✓ / ✓ / **✗** |
| MEM | L_cal/τ ≥ 20 | 56.39 (tres canales) | ✓ |
| N1 escala | Γ invariante bajo reescalado admisible, atol 1e-9 | CH-L/CH-P verificadas en suite; CH-F es conteo adimensional de escala canónica | ✓ / ✓ / N/A |
| σ_op | conforme §9.7, sin derogación | por construcción (§4) | ✓ |

Justificaciones de una línea (§7 H2): cota superior 0.95 de CH-L — en un
observable altamente predecible el umbral de degeneración está cerca de 1;
0.95 guarda sin penalizar mejora sana del estimador trailing. Cota inferior
0.10 uniforme — la inducción debe explicar algo. f\* = 1.5 — propuesto en
el skeleton antes de medir; las mediciones no lo movieron.

**Nota anti-benevolente (formulación exacta):** Las bandas se fijaron
usando diagnósticos sin outcomes. Una banda más amplia no favorece el signo
positivo del contraste: convierte más corridas en decisorias y expone
simétricamente al programa a éxito o falsación.

**Estado ya adjudicado en calibración:** CH-F falla ρ_I (0.0101 < 0.10) y
C4 (1.3514 < 1.5) → **canal secundario inválido desde calibración**, sin
efecto sobre la reclamación primaria; sus registros se publican como
continuidad comparativa (confirma que las compuertas nuevas habrían
declarado inadmisible la interfaz de G1 de origen). CH-L y CH-P superan
todas las compuertas medibles en calibración; quedan pendientes de la
partición de evaluación y de C3 bi-particional en la corrida.

## 6. Líneas base y selección del comparador primario

Todas causales, presupuesto de alerta igualado al de PRAMA en calibración
(order-statistic + desempate sembrado): **B-TRIV** (intensidad trailing
12 h), **B-VAR** (varianza trailing, ventana 336 h, sobre el residual
ω−ω̂ de CH-L), **B-AC1** (autocorrelación lag-1 trailing, misma ventana,
mismo residual), **B-COMP** (rango promedio de B-VAR y B-AC1). Comparador
del contraste primario: la línea base de **mayor enriquecimiento en
calibración** (regla evaluable antes de tocar evaluación); las demás,
contrastes secundarios con corrección de Holm.

## 7. Reclamación primaria, réplicas, semillas y clasificación

- **Canal primario: CH-L.** Unidad: cascada. Punto: `idx−1`, filas válidas
  post-calibración.
- **Estadístico primario:** contraste pareado por bootstrap de cascadas,
  `risk_difference(PRAMA_CH-L) − risk_difference(comparador §6)`.
- **Réplicas y semillas (desambiguadas, sin conflación):**
  - bootstrap pareado: **n = 10,000**, semilla **20260714**;
  - desempate del presupuesto de alerta: semilla **20260715**;
  - nulo circular de alineación: **n = 10,000**, semilla **20260716**,
    desplazamiento mínimo 24 bins;
  - nulo estratificado de C4: **n_null = 1,000**, semilla **20260717**.
  La cifra 10,000 aplica a bootstrap y al nulo de alineación; **no** a C4,
  fijado en 1,000 por H2 y el skeleton.
- **Éxito confirmatorio:** contraste observado > 0 y p unilateral < 0.01,
  condicionado a todas las compuertas de §5 en CH-L (ambas particiones).
- **Clasificación exhaustiva:**
  1. `confirmatory_success`;
  2. `confirmatory_criterion_not_met` — **activa la cláusula de §0** si el
     criterio tampoco se cumple contra B-TRIV en los contrastes
     secundarios;
  3. `invalid_for_confirmatory_claim_<gate>_failed` — con identificación de
     capa (taxonomía interface_failure; disyunción 𝓑ₒ/𝓑_I de §15.4 v0.2
     cuando aplique).
- Una sola prueba primaria por dominio. Resultados negativos e inválidos se
  publican sin modificar este texto.

## 8. Secuencia de commits

H1 preflight = `37857b5` ✓; fe de erratas del digest = `3c4e3db` ✓. H2
contratos + Verificación 1 + mediciones = `688e26f`, `401e8e6` ✓;
conformidad N1 = `9a6abe7` ✓. **H3 = commit de este documento** (congela).
H4 = corrida confirmatoria desde árboles limpios, reporte esquema v2 con
`induction.epoch_id` por canal. H5 = registro del resultado y, si procede,
activación de la cláusula de §0 en el registro del programa.

## Enmiendas

(ninguna; sección append-only)

## Anexo — Clasificación de afirmaciones

[N]: §§0 (cláusula), 3–8. Decisión de dirección transcrita: §0 (tesis), §1
(mono-dominio, exclusión BPA), umbrales de §5, semillas de §7. [E/H]: la
hipótesis en juego — valor incremental de PRAMA sobre el comparador
primario en CH-L. Mediciones citadas: [E], sin outcomes, commit `401e8e6`.
