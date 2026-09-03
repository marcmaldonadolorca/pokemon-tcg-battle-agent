# Presupuesto de búsqueda: gastar el banco de 600 s

Fecha: 2026-08-13. Código: `research/agentes/clon_busq2.py` (nuevo; `clon_busq.py`
NO se ha tocado, está en la ladder con μ 675,3 / 709,0). Instrumentación:
`scratchpad/reloj/barre.py` (arena + reloj en una pasada), `scratchpad/reloj/mk2.py`
(envoltorios con parámetros fijados **después** del `exec_module`),
`scratchpad/reloj/test_reloj.py` (aritmética del controlador),
`scratchpad/reloj/test_banco.py` (partidas con el banco reducido).

## 1. Qué hace hoy `clon_busq.py` (el de la ladder)

| parámetro | entorno | valor | qué es |
|---|---|---|---|
| `K_DETS` | `CB_K` | **8** | determinizaciones por decisión buscada |
| `N_CAND` | `CB_C` | **3** | candidatas evaluadas (las 3 mejores acciones DISTINTAS de la red) |
| `R_PASOS` | `CB_R` | **16** | selects de rollout truncado |
| `MARGEN` | `CB_MARGEN` | **1,5** | «están cerca» (unidades de la puntuación de la red) |
| `RESERVA` | — | 40 s | banco intocable |
| `TOPE` | `CB_TOPE` | 1,0 | **declarado y NUNCA usado**: `clon_busq.py` no tiene controlador de reloj |

Cuándo busca: `remainingOverageTime > 100 s` **y** tracker sano **y** `trk._cur is not None`
**y** `rival_bocabajo_n == 0` (el motor rechaza esa determinización con error 2) **y** la red
da ≥2 opciones **y** `pts[0] − min(pts[1:]) ≤ MARGEN`.

La última condición es un **hueco total**: exige que TODAS las candidatas estén cerca, así
que una candidata lejana veta la decisión entera y **subir C reduce la frecuencia de
búsqueda**. Por eso `clon_busq2.py` añade la regla por **banda** (entran solo las opciones a
menos de `MARGEN` de la mejor, hasta `N_CAND`), que hace C y MARGEN ortogonales y es
condición previa para poder barrerlos.

Cómo evalúa: cada candidata se juega en la raíz de cada determinización y se sigue con un
rollout donde **la propia red pilota los dos lados**; la hoja se evalúa con `mcts._evalua`,
que usa la **red de valor aprendida** (`_VALOR_OK = True`, 72,7% de acierto), no la
heurística de material.

Guardas: `search_end()` en `finally`, toda acción validada con `heuristico._es_legal` y
caída a `heuristico._politica` → `_fallback`.

### Coste medido del agente de la ladder

(n=32 partidas, c2-alakazam en los dos lados, con la torre cargada)

| magnitud | valor |
|---|---|
| decisiones propias por partida | 78,4 |
| fracción buscada | 38,3% |
| determinizaciones por decisión buscada | 8,0 |
| ms por decisión: media / p95 / máx | 77,6 / 310 / 597 |
| s de agente por partida: media / máx | 6,08 / 9,23 |
| **fracción del banco de 600 s usada** | **~1,0 %** |

Es decir: sobra un factor ~60 de reloj. Ese es el hueco que mide esta nota.

## 2. Resultados del barrido

Fase 1 lanzada el 2026-08-13 20:09, cerrada el 2026-08-14 00:06
(`scratchpad/reloj/fase1.sh`, logs en `fase1.log`, un JSON por punto en
`r_<TAG>.json`). Cada punto es `clon_busq2.py` con un parámetro movido contra
`clon_busq.py` tal cual está en la ladder, **misma red d7h384 y misma baraja
c2-alakazam en los dos lados**, asientos intercambiados por `barre.py`.

| tag | qué mueve | n | tasa | IC95 | veredicto |
|---|---|---|---|---|---|
| **RC** | **R=32 y C=5 a la vez** | 1600 | **0,6350** | [0,6111, 0,6582] | **gana** |
| R32 | rollout 16 → 32 | 1600 | 0,5850 | [0,5607, 0,6089] | **gana** |
| C5 | candidatas 3 → 5 | 1600 | 0,5656 | [0,5412, 0,5897] | **gana** |
| K16 | determinizaciones 8 → 16 | 1600 | 0,5212 | [0,4968, 0,5456] | empate |
| P1_banda | regla `hueco` → `banda` | 2000 | 0,4920 | [0,4701, 0,5139] | empate |
| M075 | margen 1,5 → 0,75 | 1600 | 0,4775 | [0,4531, 0,5020] | empate/peor |
| P0_hueco | regla `hueco` con TOPE activo | 2000 | 0,4620 | [0,4402, 0,4839] | **pierde** |
| MINF | margen infinito (buscar siempre) | 1600 | 0,4387 | [0,4146, 0,4632] | **pierde** |

Tres lecturas, y ninguna era la esperada al abrir la nota:

- **La profundidad del rollout es el eje que más compra**, no el número de
  determinizaciones. R32 gana solo; K16 empata pese a costar el doble.
- **Buscar más no es jugar mejor.** MINF —buscar en todas las decisiones— es el
  peor punto de los ocho, por debajo de no tocar nada. La condición de disparo no
  es una limitación que haya que quitar: es parte de lo que hace que la búsqueda
  ayude, porque concentra el presupuesto donde la red duda de verdad.
- **R32 y C5 se suman**: 0,585 y 0,566 por separado, 0,635 juntas. Es el tercer
  caso del proyecto en que dos ejes ortogonales se acumulan (red + búsqueda fue el
  primero, datos + búsqueda el segundo).

## 3. Controlador de reloj

`clon_busq2.py` reparte el banco con `TOPE` (tope duro por decisión), `DIV`
(decisiones propias que supone por delante), `RESERVA` (40 s de planificación) y
`RESERVA_DURA` (15 s que no se tocan jamás). El barrido corrió con `TOPE=10,0` y
`DIV=60`, es decir, con la correa muy larga a propósito para ver dónde topa.

Y topa. Con la configuración RC, sobre 312.187 decisiones:

| magnitud | RC | K16 | BASE (ladder) |
|---|---|---|---|
| decisiones buscadas | 97.596 | 85.312 | ~38% |
| **cortes de reloj** | **976** | 624 | 0 |
| **decisiones sin presupuesto** | **80.236** | 61.785 | 0 |
| decisión más lenta | 3,32 s | 2,28 s | 0,19 s |
| s de agente por partida (media) | 13,5 | 13,7 | 6,1 |
| **partidas perdidas por reloj** | **0** | 0 | 0 |

El controlador **degrada, no rompe**: 3.200 asientos jugados, todos `DONE`, cero
excepciones, cero acciones ilegales, cero determinizaciones fallidas. Cuando el
banco aprieta deja de buscar y devuelve el argmax de la red, que es exactamente el
comportamiento que se quería.

Aviso honesto sobre estas cifras de tiempo: se midieron con 8 y 15 procesos
compitiendo en una torre de 16 hilos, así que están infladas por contención. En
producción hay ~1,6 vCPU pero un solo agente. La medida limpia es la prueba de
banco reducido de la fase 3, todavía sin correr.

## 4. Veredicto

**Configuración RC** — `R_PASOS=32`, `N_CAND=5`, `K_MAX=8`, `MARGEN=1,5`,
`REGLA=banda`, `TOPE=10,0`, `DIV=60` — es la mejor medida: **0,6350 [0,6111,
0,6582]** contra el agente que está en la ladder, con la misma red y la misma
baraja.

Dos cosas que faltan antes de que pueda enviarse, y que están anotadas como tales:

1. La validación de la fase 3 (`fase3.sh`): campo de 12 arquetipos, auditoría de
   500 partidas y prueba de banco reducido a 120 y 30 s.
2. La comprobación en `c1-grimmsnarl`. Todo el barrido se hizo sobre
   `c2-alakazam`; que un parámetro de búsqueda transfiera entre barajas es
   plausible pero **no está medido**, y este proyecto ya se llevó un susto con una
   báscula que se invertía al cambiar de piloto (`PKM-012`).
