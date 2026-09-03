# Referencia condensada de la Search API de cabt (doc oficial Sphinx)

Fuente: https://matsuoinstitute.github.io/cabt/api.html (+ sim.html, game.html, utils.html),
descargada 2026-08-06. Esto es el resumen operativo; las signaturas C reales del binding
están en `research/search_wrapper.py`.

## Funciones de búsqueda (nivel Python documentado, api.py — bloqueado tras el gate)

```
search_begin(agent_observation, your_deck, your_prize, opponent_deck, opponent_prize,
             opponent_hand, opponent_active, manual_coin=False) -> SearchState (raíz)
search_step(search_id: int, select: list[int]) -> SearchState   # avanza UN estado
search_end() -> None          # termina la búsqueda; la memoria se REUTILIZA en la siguiente
search_release(search_id) -> None  # libera un estado concreto por id
```

Puntos clave literales de la doc:

- `agent_observation`: "You must input the observation argument passed to your agent
  function exactly as is" (usa internamente `Observation.search_begin_input`).
- `your_deck`: **Predicted** Card IDs de TU mazo. Mismo nº de cartas que tu mazo real.
  "If Observation.select.deck != None, ignored this" (cuando un efecto te enseña el mazo,
  el motor ya lo conoce).
- `your_prize`: Predicted Card IDs de tus premios (mismo nº).
- `opponent_deck` / `opponent_prize` / `opponent_hand`: Predicted Card IDs de mazo /
  premios / mano del rival (mismos tamaños que los reales). En setup el deck rival debe
  contener al menos 1 Pokémon Básico.
- `opponent_active`: solo si hay un Pokémon boca abajo en el activo rival (setup);
  debe ser ID de carta Pokémon.
- `manual_coin=True`: "the coin's heads or tails can be chosen" → las monedas se vuelven
  nodos de decisión (chance nodes explícitos elegibles).
- **La información oculta la determiniza EL LLAMANTE**: el motor no muestrea nada por ti;
  tú le pasas una muestra completa y coherente del estado oculto.

## Tipos

- `SearchState(observation: Observation, searchId: int)` — `observation.search_begin_input`
  es None dentro de la búsqueda.
- `ApiResult(state: SearchState|None, error: int)` — error != 0 → fallo (30 = contexto roto).
- `Observation(select, logs, current, search_begin_input)`; `current: State` con
  `turn, turnActionCount, yourIndex, firstPlayer, supporterPlayed, stadiumPlayed,
  energyAttached, retreated, result (-1 en curso / 0 gana P0 / 1 gana P1 / 2 empate),
  stadium, looking, players[2]`.
- `PlayerState`: `active, bench, benchMax, deckCount, discard, prize (null = boca abajo),
  handCount, hand (null si no visible), poisoned/burned/asleep/paralyzed/confused`.
- `SelectData(type, context, minCount, maxCount, remainDamageCounter, remainEnergyCost,
  option, deck, contextCard, effect)`.

## Enums (los que usa el agente)

- `SelectType`: 0 MAIN, 1 CARD, 2 ATTACHED_CARD, 3 CARD_OR_ATTACHED_CARD, 4 ENERGY,
  5 SKILL, 6 ATTACK, 7 EVOLVE, 8 COUNT, 9 YES_NO, 10 SPECIAL_CONDITION.
- `OptionType`: 0 NUMBER, 1 YES, 2 NO, 3 CARD, 4 TOOL_CARD, 5 ENERGY_CARD, 6 ENERGY,
  7 PLAY, 8 ATTACH, 9 EVOLVE, 10 ABILITY, 11 DISCARD, 12 RETREAT, 13 ATTACK, 14 END,
  15 SKILL.
- `AreaType`: 1 DECK, 2 HAND, 3 DISCARD, 4 ACTIVE, 5 BENCH, 6 PRIZE, 7 STADIUM,
  8 ENERGY, 9 TOOL, 10 PRE_EVOLUTION, 11 PLAYER, 12 LOOKING.
- `SelectContext`: 0 MAIN, 1 SETUP_ACTIVE_POKEMON, 2 SETUP_BENCH_POKEMON, 3 SWITCH,
  4 TO_ACTIVE, 5 TO_BENCH, 6 TO_FIELD, 7 TO_HAND, 8 DISCARD, 9 TO_DECK,
  10 TO_DECK_BOTTOM, 11 TO_PRIZE, 12 NOT_MOVE, 13 DAMAGE_COUNTER, 14 DAMAGE_COUNTER_ANY,
  15 DAMAGE, 16 REMOVE_DAMAGE_COUNTER, 17 HEAL, 18 EVOLVES_FROM, … (más contextos de
  efectos concretos hasta ~41).

## Otras funciones del motor (sim/game)

- `battle_start/battle_select/battle_finish/get_battle_data/visualize_data` (game.py,
  ya envueltas en el paquete instalado).
- libcg.so exporta además `AllCard` y `AllAttack` (catálogo de cartas/ataques) —
  útiles para construir la CardData local sin scraping.

## Bloqueo del api.py oficial

El `api.py` de la competición (envoltorio Python oficial de estas funciones) está tras el
gate de aceptar las reglas de la división Simulation. NO bloquea nada técnico: todas las
funciones C están exportadas en la libcg.so instalada y nuestro binding
(`research/search_wrapper.py`) las cubre. Al aceptar las reglas convendrá comparar
nuestro wrapper con el oficial (orden exacto de argumentos y manejo de errores).
