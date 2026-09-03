# Kernels de referencia de Kaggle — destilado (terceros, NO ejecutados)

Fecha: 2026-08-07. Bajados con `kaggle kernels pull -m` a `research/terceros/<slug>/`
(re-pull 2026-08-07, sin cambios vs 2026-08-06). **Código de terceros no confiable: leído,
no ejecutado.** El asset base64 de Grimmsnarl se decodificó en memoria (tarfile) solo para
leer `deck.csv` y `main.py`; nada importado. Extractos legibles en scratchpad
`kernels-txt/`. La entrega final debe ser código propio: esto es referencia de diseño.

## 0. Qué se bajó y licencias

| Carpeta | Kernel (slug) | Autor | Licencia |
|---|---|---|---|
| rl-mcts-sample | kiyotah/reinforcement-learning-and-mcts-sample-code | HEROZ (motor) — canónico | sin declarar → Apache-2.0 (default Kaggle) |
| lucario-sample | kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck | HEROZ | sin declarar → Apache-2.0 |
| iono-sample | kiyotah/a-sample-rule-based-agent-iono-s-deck | HEROZ | sin declarar → Apache-2.0 |
| strong-start-v10 | romanrozen/strong-start-baseline-agent-v10-lb-950 | comunidad (~174 votos, LB ~889) | sin declarar → Apache-2.0 |
| grimmsnarl-dtc | tetsutani/grimmsnarl-ex-damage-transfer-control | comunidad (~96 votos, LB ~883) | sin declarar → Apache-2.0 |
| garchomp-sample | masamikobayashi/a-sample-cynthia-garchomp-ex-deck | comunidad | sin declarar → Apache-2.0 |

Ninguno lleva cabecera de licencia propia (los hits de grep eran «submit»/«limitless»).
`cg-lib`/`libcg.so` es de HEROZ bajo las reglas de la competición: uso permitido SOLO dentro
de ella (ruling de Addison, hilo 717141).

## 1. RL+MCTS oficial (kiyotah) — la referencia canónica de la Search API

Es un notebook de ENTRENAMIENTO (self-play con `battle_start/battle_select/battle_finish`
de `cg.game`, no el kaggle env); **no trae main.py de submission** — el empaquetado canónico
está en los samples rule-based (§2).

- **Determinización de zonas ocultas** (lo que pasa a `search_begin`, kwargs idénticos a
  nuestro `search_wrapper.py`): `your_deck = random.sample(decklist, deckCount)` y
  `your_prize = random.sample(decklist, nPremios)` — muestrea del decklist COMPLETO sin
  descontar lo ya visto (naive, puede duplicar copias ya jugadas);
  `opponent_deck = [1072 (Snorlax)] * deckCount`, `opponent_prize = opponent_hand = [1
  (energía básica)] * n`, `opponent_active=[1072]` si boca abajo. **No hay mirror ni
  muestreo realista: el rival determinizado es un maniquí con mano de energías que no puede
  jugar nada.** El árbol solo captura la línea propia; la «respuesta rival» simulada es ruido.
- **SEARCH_COUNT=10** = nº de iteraciones MCTS por decisión (solo 10 expansiones). PUCT
  con `c = 0.4*sqrt(visit)`, prior `softmax(policy*10)`, valor negado cuando el nodo es del
  rival, elección final por visitas. UNA sola determinización por decisión (`search_begin`
  1 vez, `search_end` al final).
- **Enumeración de acciones**: todas las combinaciones de tamaño EXACTO `maxCount` sobre
  `range(len(option))`, cap 64. No enumera longitudes entre min y max.
- **Representación de estado (Transformer)**: encoder-decoder d_model=128, 2 heads,
  ff=256, 1+1 capas, entrada sparse por `EmbeddingBag(mode=sum)`. Encoder = 24 «palabras»:
  8 slots de banca ×2 jugadores (padding con «pokémon null»), activo ×2, player-state ×2
  (contadores normalizados + premios one-hot + estados), mano propia (peso 0.25), decklist
  propio (0.25), estadio, global (turn/10, first). Pokémon = [es-null, hp/400, id one-hot,
  tools 1.0, energyCards 0.5]. Decoder = 1 palabra por acción candidata: tipo de opción
  (END/YES/NO/NUMBER…), `attackId` one-hot, o `cardId` one-hot indexado por (feature-slot |
  SelectContext) — la misma carta significa cosas distintas según el contexto del select.
  Salidas: value tanh escalar + policy tanh por acción.
- **Entrenamiento**: labels de value hacia atrás con λ=0.9 (`label=(value+v)/2`,
  `value = value*λ + v*(1-λ)`); policy target = ventaja de visitas vs raíz clipped ±1 (los
  hijos no visitados: `min_value - v - 0.03`); HuberLoss; eval vs agente random.
- Su `random_agent` usa `random.sample(range(len(option)), maxCount)` → **casca en (0,7)**
  (option=[], maxCount=1); confirma nuestro gotcha 3.

## 2. Samples rule-based (Lucario, Iono oficiales; Garchomp comunidad)

Patrón común (el «esqueleto sample»): una pasada que puntúa CADA opción con una heurística
por `OptionType` × `SelectContext`, ordena descendente y devuelve `desc[:maxCount]`.
Genérico: cubre todos los selects sin enumerar contexts (salvo option=[], ver riesgos).
Estado global mínimo reseteado por turno (plan de ataque, flags de habilidad usada).

- **Lucario** (2 fases): primero construye un `AttackPlan` (mejor atacante×ataque×objetivo,
  con gating: solo considera banca si `can_switch`, solo banca rival si tiene Boss/gust;
  daño con debilidad ×2 / resistencia −30; letal → score 50000; si
  `premios_rival ≤ prize(target)` → 50000 = jugada de victoria). Después puntúa opciones
  con bonus si coinciden con el plan. Jerarquía de tiers: ABILITY 30000 > PLAY pokémon
  20000 > PLAY trainer 10000 > EVOLVE 9000 > attach energía ~8000 > Switch 6000 > …
  > RETREAT 2000 > ATTACK 1000 (+100 el planificado) — **se juega todo lo jugable antes de
  atacar; atacar/terminar cierran el turno**. `prize_count()` = 3 megaEx / 2 ex / 1, con
  descuentos por Legacy Energy (12) y Lillie's Pearl (1172).
- **Iono**: mismos huesos; extra: `hand_scores` calculados una vez se REUTILIZAN para
  descartes (`DISCARD` → score = −hand_score: lo peor de la mano se descarta primero);
  anti-atasco de duplicados en búsquedas (`id_counts` penaliza coger 2ª/3ª copia);
  anti-deck-out (`no_draw = deckCount<=5` desactiva robo); ATTACK score = `attackId` (proxy
  burdo de «el ataque más nuevo/grande»).
- **Garchomp** (el mejor factorizado, ~700 líneas, clases View/Scorer):
  - **Detección de matchup por IDs visibles del rival** (tabla `MATCHUPS` de líneas firma +
    `OPP_MAX_DAMAGE` por arquetipo) → pesos condicionales por matchup (a quién dar la tool,
    cuándo NO evolucionar a Garchomp vs crustle, umbral de retirada = daño máximo esperado
    del rival).
  - **Lee `obs.logs` para contar PP jugados este turno** (LogType.PLAY + TURN_START) —
    único sample que usa los logs como memoria.
  - Selección multi-pick greedy con actualización incremental de conteos entre picks (para
    Poffin 2×: equilibra línea G/R en el MISMO select).
  - Win-plan explícito (front KO / Boss KO, con o sin PP extra) calculado una vez por View.
  - Métricas locales que reporta vs samples oficiales (N=500): 81% Iono, 66% Lucario,
    57% Dragapult, 50% Abomasnow.
- **Empaquetado canónico** (celda final de los samples): `submission.tar.gz` con
  `main.py` + `cg/` (del dataset kiyotah/cg-lib o del sample_submission de la competición)
  + `deck.csv`. `main.py` carga `deck.csv` desde `./` y si no
  `/kaggle_simulations/agent/deck.csv`; `agent(obs)` con `select None` → devuelve lista de
  60 IDs.
- **Riesgos copiables detectados** (nuestro gotcha 3 confirmado como agujero real de los
  públicos): Lucario/Iono con option=[] devuelven `desc[:max]` = `[]` (ilegal con
  minCount=1); Garchomp devuelve `[]` explícito; su fallback de excepción
  (`random.sample(range(n), maxCount)`) casca si maxCount>n. El select (0,7) verificado:
  minCount=1, maxCount=1, option=[] → **solo `[0]` es legal**.

## 3. STRONG START V10 (Alakazam «Codex Sol Eclipse», el mejor público copiable)

main.py monolítico embebido como string en el notebook; capas apiladas por redefinición de
`agent` (v19 plantillas → v22 guard → entrypoint final).

- **~65 pesos con nombre** en dict `WEIGHTS` (tiers idénticos al esqueleto sample) +
  override por JSON buscado en rutas conocidas (`alak_w.json`,
  `/kaggle_simulations/agent/…`) → pipeline de tuning «memetic» sin tocar código; los
  valores afinados van baked en un `WEIGHTS.update({...})`.
- **Capa de búsqueda** (2-ply minimax determinizado sobre la Search API, inlined):
  `N_DET=3` determinizaciones × candidatos top-8 de la heurística (no terminales, score≥0)
  × `K_OPP=3` respuestas rivales; rollouts greedy con LA MISMA heurística para completar
  turnos (`MAX_SUBSTEPS=40`); `TIME_BUDGET_S=0.80` por decisión con `time.monotonic()`
  chequeado en cada paso; solo en MAIN con `3 ≤ n_opciones ≤ 24` y `turn ≥ 2`.
  **Override de la heurística SOLO si el margen medio ≥ 500 = medio premio** en su eval —
  amortigua el ruido de pocas determinaciones. Leaf eval: `1000*Δpremios + ΔHP +
  5*Δenergías − 4000*sin_activo`; terminal ±1e7.
- **Belief model — la determinización seria** (contraste con §1): lado propio = multiset
  `decklist − visto` EXACTO (mano+descarte+premios boca arriba+en juego+tools+energías+
  preEvolution+estadio propio); premios propios rellenados del mismo resto. Lado rival =
  matching de arquetipo por overlap de IDs de Pokémon visibles vs plantillas
  (`top20_decks/*.csv` si existen; embebidas `_GRIMM_IDS`/`_TUSK_IDS`), plantilla activada
  SOLO cuando la línea rival ya es visible (v19); fallback: carta-más-vista×30 + energía
  básica del tipo dominante×30 + 8 básicos dummy. Pad con energía oscura si falta.
- **Robustez**: si `search_begin_input` es None o `search_begin` lanza → búsqueda
  deshabilitada el resto de la partida (`_search_ok`), rehabilitada al primer step de la
  siguiente (select None); `search_end()` en `finally`; cadena de fallbacks del agente:
  `_agent_impl` → except → primeros k legales (`k=min(max(1,minCount),n)` si n else 0) →
  `[0]`.
- **`get_last_callable`**: Kaggle ejecuta main.py con exec y llama a la ÚLTIMA callable
  definida → definen una función única de 1 argumento físicamente al final
  (`codex_sol_eclipse_alakazam_v22`). Peligro real si defines helpers después de `agent`.
- **Guard v22 post-decisión**: intercepta la acción YA elegida y la reescribe (si RETREAT
  con Abra cargado y sin Alakazam listo en banca → sustituye por el ataque Teleportation,
  que cambia de activo sin pagar coste). Patrón «guard que veta/reescribe al final».
- Detalles de juego: elige ir SEGUNDO (IS_FIRST: NO=5 > YES=−1; Garchomp en cambio va
  primero con YES=100); `safe_draws = deckCount − mis_premios − 1` desactiva robo
  (anti-deck-out fino: reserva para el robo obligatorio de cada turno); counter-tech
  dinámico (Enhanced Hammer +20000 si ve Team Rocket Energy en el rival); empaqueta
  `cg/` del sample_submission oficial con chequeo de ABI (`SetTestSeed` en sim.py ↔
  libcg.so) y `group.txt` con el nombre del equipo.

## 4. Grimmsnarl ex Damage-Transfer Control (tetsutani)

El notebook NO contiene la política: embebe un `tar.gz` base64 (~637KB, sha256 verificado)
con TODO (main.py, 5 guards, router, 3 expertos, generaciones v22/v26/v28/v32 de políticas
de reglas, modelos, EN_Card_Data.csv) y solo decodifica, añade `cg/` oficial
(`find_official_cg()` con scoring de rutas), valida el contenido con un set `required`,
importa main para asegurar `deck == agent({})`, y re-empaqueta con `compresslevel=9`.
Ofusca la estrategia y congela dependencias.

- **Modelo: ensemble GBDT en formato binario PROPIO** «PTC2»: por modelo, árboles de nodos
  `struct <hBBBee>` = (feature int16, flags u8, left u8, right u8, threshold float16,
  leaf float16); 180KB gz; **inferencia = bucle Python puro** (sin sklearn/lightgbm/numpy)
  con manejo de NaN por flag de dirección → cero dependencias y carga instantánea.
- **Routing por contexto del select**: modelos separados `main` (ctx 0), `c7` (ctx 7 =
  búsquedas de mazo), `low` (3,5,8), `mid` (13,15,16,21,22,40,43), `easy`
  (1,2,4,27,30,34,37,38,41); contexto no mapeado → política de reglas. Entrenan un modelo
  específico para las búsquedas de mazo — donde las reglas pierden más valor.
- **Features por opción**: semántica normalizada (type, source_id, target_id, attack_id,
  area, inplay_area) + rank de duplicados + `intent_text→id` (vocabulario congelado en
  final_schema.json) + última acción propia + `len(historial)`; historial = últimas 8
  acciones elegidas (semánticas), actualizado con lo que de verdad se devolvió.
- **Arbitraje en cadena** (main.py): modelo → `strategic_agent` (reglas, fallback base) →
  `matchup_router` (expertos mirror/tempo) → `human_controller` → guards advisor →
  residual → tactical → development → robustness; **CADA propuesta pasa `_legal()`
  (min ≤ len ≤ max, índices únicos, int en rango) antes de aceptarse**; fallback final
  `list(range(min(n, maxCount)))`. Todo envuelto en try/except por capa.
- **Perfilado del rival en vivo**: `human_memory.update(obs)` → (profile, confidence);
  activa un `coalition_expert` solo si `profile=='grass_fast'` y confianza ≥0.45.
- Reset de TODO el estado global al primer step (select None) — el proceso se reutiliza
  entre partidas.
- Riesgo heredado: con option=[] su modelo y su fallback final devuelven `[]`; dependen de
  `strategic_agent` para el (0,7) (no verificable sin ejecutar).
- Sin gestión explícita de reloj (la inferencia GBDT es ~despreciable); V10 sí presupuesta.

## 5. Mazos escritos (research/decks/meta/, un ID por línea, validados 60/≤4 copias)

| CSV | Fuente exacta |
|---|---|
| `lucario-sample.csv` | conteos comentados en main.py del sample oficial (deck.csv vivía en dataset kiyotah/mega-lucario-ex-deck, no en el notebook); 673×2 674×2 675×2 676×3 677×3 678×4, trainers, 6×13 |
| `iono-sample.csv` | ídem sample oficial Iono (dataset kiyotah/iono-deck); 265/268/269/270/271×3, 4×22 |
| `alakazam-v10.csv` | `DECK_SOURCE` literal del notebook V10 (4-4-4 línea Abra + Dudunsparce, SOLO 6 energías: 5×2+19×4; 1225×4, 1231×4) |
| `grimmsnarl-dtc.csv` | `deck.csv` del asset embebido decodificado; **idéntico a `_GRIMM_IDS` de V10** (doble confirmación del mazo Grimmsnarl público): 7×10, 112×4 Munkidori, 646×4/647×3/648×3, 1219×4, 1227×4, 1259×4 |
| `garchomp-sample.csv` | celda deck.csv literal; lista humana de Neddy Kosek (3º Regional Praga 2026-04-25, limitlesstcg 0062/0243); 379×4 380×4 381×3 + línea Roserade + 387 Spiritomb, 6×5+20×4 |
| `great-tusk-v10.csv` | `_TUSK_IDS` literal embebido en V10 (plantilla pública «great_tusk»: 58×4, 344×4, 345×4, 20×4, 11×4, 607×1) |

Grimmsnarl meta (Sumi {648}) y Alakazam meta ({743,245}) quedan cubiertos; Garchomp meta
de LB ({380,381}) es esta misma línea Cynthia.

## 6. Trucos de ingeniería adoptables (priorizados)

1. **`_legal()` universal como última línea SIEMPRE** (de DTC) + `[0]` para option=[] —
   ningún público cubre bien el (0,7); nosotros sí debemos.
2. **Esqueleto sample**: puntuar cada opción por OptionType×SelectContext y devolver
   `desc[:maxCount]` — cubre TODOS los selects genéricamente; la búsqueda solo en MAIN.
3. **Determinización estilo V10** (propio = decklist−visto exacto; rival = plantilla de
   arquetipo activada al ver la línea, con fallback sintético) ≫ la naive del sample
   oficial (rival maniquí). Nuestras plantillas: los CSV de §5.
4. **Override de búsqueda solo con margen** (V10: ≥ medio premio) — clave para
   consistencia: la heurística manda salvo evidencia clara.
5. **Presupuesto por decisión con `time.monotonic()` chequeado dentro del rollout** (V10,
   0.8s fijo) — nosotros: controlador dinámico banco/jugadas (presupuesto-tiempo.md).
6. **Pesos con nombre + override JSON** (V10) — tuning/evolución sin tocar código.
7. **`get_last_callable`**: la última función definida en main.py es la que llama Kaggle —
   `agent` debe ser lo último definido (o un alias único al final).
8. Empaquetado: tar.gz plano {main.py, deck.csv, cg/ oficial(+libcg.so), group.txt};
   deck.csv resuelto en `__file__`-dir → cwd → `/kaggle_simulations/agent/`; validar el
   tar re-abriéndolo (miembros y deck) antes de subir.
9. **Guards post-decisión** que reescriben la acción final (patrón v22 de V10 / cadena DTC):
   vetos quirúrgicos sin tocar la política base.
10. **Anti-deck-out**: `safe_draws = deckCount − mis_premios − 1` antes de cualquier robo
    voluntario (V10, más fino que el `deckCount<=5` de Iono).
11. Estado global reseteado al step de mazo (select None) — el proceso se reutiliza.
12. Matchup por IDs visibles + tabla `OPP_MAX_DAMAGE` (Garchomp): barato y efectivo para
    umbrales de retirada/tools; los logs (`obs.logs`) sirven de memoria de turno.
13. Si algún día empaquetamos modelo: GBDT binario propio float16 sin deps (DTC) o pesos
    JSON; el asset base64-en-notebook con sha256 es el mecanismo de embebido probado.
