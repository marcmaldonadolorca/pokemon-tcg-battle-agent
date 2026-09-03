# Search API de libcg.so: verificación empírica y veredicto MCTS

Fecha: 2026-08-06. Scripts: `research/search_wrapper.py` (binding ctypes, verificado),
`research/test_search_api.py` (T1-T7), `research/probe_search_perspectiva.py`.
Referencia de la doc oficial: `research/notas/search-api-doc.md`.

## Veredicto: MCTS VIABLE (determinized MCTS / ISMCTS con re-muestreo en la raíz)

El motor expone un modelo de transición completo, rápido, estable y utilizable DENTRO
de una partida real del interpreter. No hay bloqueo técnico: el `api.py` oficial (tras
el gate de reglas) solo aportaría el envoltorio Python que ya replicamos.

## Signaturas (C, x86-64; envueltas en search_wrapper.py)

```
void* AgentStart(void)                       # contexto propio, independiente del battle_ptr
char* SearchBegin(void* ctx, const char* sbi, int len,
                  const int* your_deck, const int* your_prize,
                  const int* opp_deck,  const int* opp_prize,
                  const int* opp_hand,  const int* opp_active, int manual_coin)
char* SearchStep(void* ctx, long long search_id, const int* select, int n)
void  SearchEnd(void* ctx)                   # libera TODOS los estados (memoria se reutiliza)
void  SearchRelease(void* ctx, long long id) # libera un estado
```
Retorno JSON: `{"state": {"select","logs","current","searchId"}, "error": N}`;
`sbi` = `obs["search_begin_input"]`. Los tamaños de las listas deben cuadrar EXACTOS
con los conteos reales (deckCount, nº premios boca abajo, handCount rival).

## Resultados de los tests

- **T1 legalidad**: `select` de la raíz de búsqueda == `select` real de la partida,
  idéntico JSON, en 3 obs distintas de mitad de partida. `current` difiere solo en que
  los premios aparecen boca ARRIBA (la muestra que pasamos). searchId raíz = 0.
- **T2/T3 semántica de la información oculta** (LA pregunta de diseño):
  - La determinización la aporta EL LLAMANTE como multiconjuntos: mazo propio, premios
    propios, mazo/premios/mano del rival. El motor la respeta exactamente (la mano
    rival observada en búsqueda = predicha + robos, multiset exacto).
  - **El ORDEN de las listas se ignora**: el motor rebaraja internamente en cada
    `search_begin` con semilla no determinista (rotar la lista no cambia nada
    predecible; dos begins idénticos divergen en el PRIMER evento de mazo — paso 12
    del walk de T2 —, idénticos hasta entonces).
  - **Dentro de una búsqueda todo es determinista**: re-step del MISMO searchId con el
    mismo select → observación idéntica (nuevo searchId). El azar queda fijado por
    nodo al crearse. El árbol persiste: cualquier searchId antiguo sigue siendo
    steppeable (raíz incluida) hasta `search_end`.
  - **El árbol es de información PERFECTA post-determinización y controlamos a los DOS
    jugadores**: tras mi END, `yourIndex` se voltea y la mano del actor de turno se
    hace visible (la rival = nuestra predicción). Hace falta política de oponente en
    la simulación (random/greedy/la misma heurística).
  - Re-determinizar = repetir `search_begin` con otra muestra (0,13 ms) → ISMCTS por
    muestreo en raíz confirmado (T4: dos manos rivales distintas, ambas reflejadas).
  - `manual_coin=True` acepta (error 0): monedas como nodos de decisión explícitos
    (pendiente menor: mapear el select de moneda concreto).
- **T5 velocidad (1 proceso, torre compartida)**: `search_begin+end` 7.882/s
  (0,127 ms); `search_step` **20.122 pasos/s** (100.629 pasos, walks de ~92 pasos
  hasta terminal desde mitad de partida, 0 errores). Presupuesto de evaluación:
  actTimeout 0 + overage 600 s/episodio → p. ej. 2 s/jugada ≈ 40.000 steps/jugada.
- **T6 fugas**: 3.000 ciclos begin+5 steps+end → RSS clavada en 351,4 MiB (0 fuga).
  La memoria de estados solo crece entre `search_end`s (se reutiliza, no se devuelve).
- **T7 en partida real**: agente que busca en cada MAIN dentro de `env.run` — 5/5
  partidas terminan DONE con rewards válidos, 137 búsquedas, 0 mismatch del select
  raíz vs el real, 0 errores. El contexto de `AgentStart` NO toca el battle_ptr del
  interpreter: **buscar en producción es seguro**.

## Terminales y errores

Terminal en búsqueda: `state.observation.current.result >= 0` (0/1 ganador, 2 empate)
o `select == null`. `error != 0` en el retorno = select inválido o contexto roto (30).

## Implicaciones de diseño para el agente

1. MCTS determinizado: K determinizaciones (begin) × N simulaciones; dentro de una
   determinización el azar por nodo está fijado → para no sesgar, repartir el
   presupuesto entre begins (baratos) más que profundizar una sola.
2. La estimación de la mano/mazo rival importa: podemos sesgar las muestras con
   conteo de cartas vistas (los multisets los construye `determinize()` en
   `test_search_api.py`, ya cuadra zonas con `deckCount/handCount/prize`).
3. PELIGRO heredado del motor: nada de hilos; un proceso = un contexto de agente.
   En evaluación (2 vCPU) iría todo en el proceso del agente, secuencial.
4. `search_end()` tras cada decisión para que la memoria se reutilice.

## Pendiente menor

- Mapear el select de moneda con `manual_coin=True` (¿SelectType YES_NO?).
- Setup (turno 0): `opp_active` con activo rival boca abajo, sin probar.
- Al aceptar las reglas de Simulation, comparar `search_wrapper.py` con el `api.py`
  oficial (orden de argumentos y errores).
