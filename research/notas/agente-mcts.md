# Agente ISMCTS anytime sobre la Search API (mcts.py)

Fecha: 2026-08-07. Código: `research/agentes/mcts.py`. Verificación: harness de
scratchpad (réplica del contrato de arena.py con recogida de estadísticas del
módulo por partida; intercambio de asientos + IC de Wilson, idéntico a arena).

## Arquitectura

- **ISMCTS de raíz (determinized MCTS)**: en cada decisión no trivial, K=8
  determinizaciones muestreadas del `InfoTracker` (`sample()` + `search_begin`,
  ~0,13 ms); por cada una, un árbol UCT (C=0,9) apoyado en la persistencia de
  `searchId` (re-step determinista, verificada en search-api.md). Rollouts con la
  **política heurística para LOS DOS jugadores** (dentro de la búsqueda el árbol
  es de información perfecta y controlamos ambos lados), truncados a 50 selects,
  y evaluación terminal o heurística. Agregación final: suma de visitas por
  acción-raíz sobre las K determinizaciones (voto ponderado por visitas;
  desempate por valor medio).
- **Evaluación** `_evalua` ∈ [0,1]: `0,5 + 0,5·tanh(0,5·s)` con
  `s = Δpremios_restantes(rival−yo) + 0,003·Δdaño_en_mesa + 0,05·Δenergías +
  0,05·Δpokémon_en_mesa` — el premio manda (≈1,0 por KO), el resto desempata.
- **Candidatas por nodo** (`_candidatas`): heurística SIEMPRE primera (se expande
  la primera); con `maxCount≤1` todas las opciones sueltas (+`[]` si min 0); con
  multi-selección heurística + fallback + muestras aleatorias de tamaño min y
  max. Cap 24 en raíz, 12 en nodos internos. Toda candidata pasa `_es_legal`.
- **Triviales sin búsqueda**: `option=[]` → `[0]`/`[]`; 1 opción forzada → `[0]`;
  todo forzado (min==len(option)) → `list(range(n))`.
- **Controlador de reloj**: `presupuesto = min(TOPE,
  (remainingOverageTime − 40) / max(8 + 12·premios_restantes_max, 20))`,
  automedido con `perf_counter`; el bucle reparte lo que queda entre las
  determinizaciones pendientes y respeta un margen del 5%+10 ms. Presupuesto
  < 0,15 s → heurístico puro (`degradadas_presupuesto`). TOPE y K por entorno:
  `MCTS_TOPE` (def. 1,0 s), `MCTS_K` (def. 8). La primera llamada paga los
  imports: `CARGA_S` los mide a nivel módulo y `primera_llamada_s` la primera
  decisión completa.
- **Blindaje**: tracker en try/except (si rompe → `_TRACKER_ROTO`, heurístico
  para el resto de la partida); búsqueda entera en try/except con fallback al
  heurístico; TODA acción devuelta pasa `heuristico._es_legal` y si no,
  `heuristico._fallback`. `search_end()` en `finally` tras cada decisión (la
  memoria de estados se reutiliza, T6 de search-api.md).
- No se busca si `rival_bocabajo_n > 1` (setup con banca sin voltear:
  la determinización no es representable en `SearchBegin`).

## Hallazgo nuevo sobre la Search API (corrige search-api.md)

El JSON de `SearchBegin/SearchStep` NO devuelve `{select, logs, current,
searchId}` planos: devuelve `{"searchId": N, "observation": {select, logs,
current, ...}}`. `_plano()` lo normaliza (tolera ambas formas). Sin esto, todo
estado parecía terminal (`select` ausente) y el árbol no arrancaba.

## Resultados (torre, procs 4, 2026-08-07)

(se rellenan al terminar la batería — ver JSONs `res_*.json` del scratchpad)

## Diagnóstico

(pendiente de números)

## Decisiones de diseño pendientes para la siguiente ronda

- Modelo rival: `MirrorModel(DECK)` (exacto en el espejo de la arena). Con mazo
  propio real habrá que pasar a `MetaModel` + elección de arquetipo por
  verosimilitud (stub ya en tracker.py).
- `manual_coin=False`: las monedas quedan fijadas por nodo al crearse (azar del
  motor); explicitarlas como nodos de azar es mejora posible.
- Ataques «N por cada X» siguen estimados N×3 SOLO en la política de rollout;
  la búsqueda ya los valora bien (el motor aplica el daño real en los steps).
