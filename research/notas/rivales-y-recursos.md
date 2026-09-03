# Rivales y recursos públicos (fuera de Kaggle) — 2026-08-06

Tema: código, agentes y conocimiento reutilizable para la competición PTCG AI Battle Challenge.
Método: WebSearch + WebFetch + API de GitHub + PyPI JSON + inspección read-only del venv local. NO se instaló ni ejecutó código de terceros.

## 1. Hallazgo principal: la API de búsqueda del motor (forward model oficial)

- Documentación oficial del motor: **https://matsuoinstitute.github.io/cabt/** («PTCGABC cabt Engine 0.1.0», Matsuo Institute).
  - Documenta un módulo `api` (api.py) con **`search_begin(agent_observation, your_deck, your_prize, opponent_deck, opponent_prize, opponent_hand, opponent_active, manual_coin=False)` → SearchState**, `search_step(search_id, select)`, `search_end()`, `search_release()`: es un **forward model determinizado** — le pasas IDs predichos para las zonas ocultas y el motor simula ramas del juego paso a paso. Base directa para MCTS determinizado / ISMCTS sin escribir un simulador propio.
  - También `all_card_data()`, `all_attack()`, `to_observation_class()`, y enums completos (AreaType, EnergyType, CardType, SelectType, SelectContext con 49 contextos, OptionType con 17 tipos) + dataclasses (State, Observation, SelectData, Option, Pokemon, PlayerState).
- **Verificado localmente**: `cg/libcg.so` de nuestro venv **exporta** `SearchBegin/SearchStep/SearchEnd/SearchRelease/AgentStart/AllCard/AllAttack` (comprobado con `nm -D`), pero nuestro `cg/sim.py` (idéntico al de GitHub master, 1497 bytes) solo enlaza BattleStart/BattleFinish/GetBattleData/Select/VisualizeData. **api.py NO viene en el paquete pip ni en el repo kaggle-environments** — viene en los assets descargables de la competición en Kaggle (o se puede re-enlazar por ctypes siguiendo las firmas de la doc).
  - Acción sugerida: descargar los data files de la competición (`kaggle competitions download`) para obtener api.py oficial, o enlazar los símbolos a mano.
- Veredicto: **ORO**. Desbloquea agentes de búsqueda con presupuesto (600 s de overage por episodio según cabt.json local; actTimeout 0).

## 2. Repos de agentes de esta competición

| Repo | Qué es | Veredicto |
|---|---|---|
| **https://github.com/wmh/ptcg-abc** (4★, push 2026-07-28) | 3 agentes rule-based completos con main.py+deck.csv (Bellibolt Elo 836, Typhlosion 532, Alakazam pendiente), `tools/cabt_eval.py` (evalúa vs decks meta N partidas), sandbox web humano-vs-agente con scores por opción, análisis de meta en chino tradicional. **Sin licencia** (todos los derechos reservados). | **Rival de entrenamiento + inteligencia de meta**. No copiar código (sin licencia); sí usar como sparring local y leer su análisis: «la elección de deck domina sobre la calidad del agente»; Crustle (inmune a ataques de ex) reconfigura ~la mitad del field. |
| **https://github.com/TomBombadyl/kaggle_pokemon** (push activo, reset 2026-06-22) | Workspace enorme: 21 submissions catalogadas (`eval/AGENT_CATALOG_FULL.md`), TrueSkill-gates locales, pipeline de episodios de Kaggle. Datos: Dragapult pilot oficial 880.9 μ; su mejor propio = **SearchScorer×Lucario 660.5 μ**; su RL+MCTS v5 = 580.6 μ (¡regresión!). Sin licencia. | **Inteligencia competitiva**: confirma que (a) usar el Search API («SearchScorer») bate a su RL+MCTS casero, (b) el pilot oficial Dragapult ~880 μ es el listón. Leer sus catálogos, no su código. |
| **https://github.com/Rami-Ismael/Pokemon_TCG_Kaggle_Competition_2026** (202 commits, activo 2026-08-06) | Behavior cloning: BERT-encoder 3.3M params entrenado sobre **~210k replays de episodios públicos** de la ladder (los episodios se bajan con la API de Kaggle). Maneja multi-select autoregresivo, DECLINE sintético. Sin licencia visible. | **Referencia de enfoque IL**: demuestra que los episodios públicos de la ladder son un dataset masivo gratuito. Su utilidad final no está probada (sin μ publicada). |
| **https://github.com/AmedeoBiolatti/kaggle_ptcg_engine** (1★, C++20, push 2026-07-26) | **Reimplementación C++ del motor** con pybind11, `PTCG_BACKEND=native` drop-in, VectorEnv para rollouts batched, tests de paridad/shadow-mode vs motor oficial. Licencia «competition terms». | **Prometedor para RL/rollouts masivos** si hiciera falta más velocidad que 31,5 p/s; riesgo de divergencia de reglas (él mismo recomienda validar). No adoptar sin paridad verificada. |
| https://github.com/sutesute0000/ptcg-ai-battle-lopunny (2026-08-05) | Agente Mega Lopunny ex. | Menor; señal de meta (Lopunny en juego). |
| https://github.com/knightynite/ptcg-ai-battle-agent (2026-07-27) | Rule-based + harness de medición. | Menor. |
| https://github.com/Arths17/ptcg-alakazam-hand-engine (2026-08-03) | Heurístico Alakazam. | Menor; otra señal pro-Alakazam. |
| Jun-Morita/kaggle-ptcg-ai-battle, 1992Taku0512/…, Beiciccc/…, sota1111/ptcg-agent-gpt | Workspaces personales activos (ago-2026). | Ruido; ilustran nivel del field. |

## 3. Muestras oficiales del organizador (usuario Kaggle `kiyotah` = Kiyota Hidekazu, HEROZ; mismo autor de los commits cabt en kaggle-environments)

- **https://www.kaggle.com/code/kiyotah/reinforcement-learning-and-mcts-sample-code** — sample oficial RL+MCTS (2026-06-16). Casi seguro usa api.py/Search*. Bajar con `kaggle kernels pull`.
- https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck (2026-06-19) — baseline rule-based oficial (el «official pilot» que TomBombadyl mide en ~880 μ es de esta familia).
- https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-iono-s-deck (2026-06-17).
- Comunidad fuerte: https://www.kaggle.com/code/pixiux/ptcg-mega-lucario-ex-v63 (v63 = muy iterado; contenido no legible sin JS, bajar con API).
- Veredicto: **descargar los 3 de kiyotah es prioridad 1** — son el baseline legal y la demo canónica del Search API.

## 4. Visores de replays

- **https://github.com/charlielockyer-rice/cabt-viewer** (54★, TypeScript/Svelte, act. 2026-07-28) — visor de estados/replays cabt; también humano-vs-agente. El más adoptado (lo usa la comunidad japonesa).
- https://github.com/Leundai/cabt-replay-viewer (3★, Svelte) — alternativa.
- Bug conocido del replay HTML del paquete pip: https://github.com/Kaggle/kaggle-environments/issues/1261 («window.kaggle.renderer = ;»).
- Veredicto: útil para análisis cualitativo de derrotas; no crítico.

## 5. Estado del motor / versiones

- PyPI: **última = 1.32.4 (2026-08-04)**; 1.32.3 (08-03) y 1.32.4 son fixes de *kaggriculture*, **no tocan cabt**. Último cambio real de cabt: **2026-07-23 «Cabt update library (#1356): fixed a crash caused by a specific combination of cards»** (entra en 1.32.2); antes 07-16 fix de bug al descartar energía (#1324) y 06-29 subida de step limit + ARM64 (#1280). Timeouts: #1264/#1268 fijan actTimeout=0 y overage=600 s.
- **Nuestro venv 1.32.4 = motor más nuevo disponible.** «1.14.10» citado en el entorno de evaluación **no existe en PyPI** (249 releases comprobadas) — será tag de imagen docker u otra cosa; conviene verificar qué corre de verdad el evaluador, porque un motor viejo allí + combo de cartas del crash #1356 podría ser relevante al elegir deck.

## 6. Literatura / código aplicable (2 vCPU, 10 días)

- ISMCTS canónico: Cowling, Powley, Whitehouse, «Information Set Monte Carlo Tree Search», IEEE TCIAIG 2012 — determinizar zonas ocultas y buscar; encaja 1:1 con `search_begin(...)` que ya pide predicciones de zonas ocultas.
- https://arxiv.org/pdf/1808.04794 — «Improving Hearthstone AI by Combining MCTS and Supervised Learning» (MCTS + heurísticas aprendidas; presupuesto por movimiento, aplicable).
- https://ieee-cog.org/2020/papers2019/paper_257.pdf — mejoras de MCTS en Hearthstone (poda/priors baratos).
- https://arxiv.org/pdf/2103.04931 — survey de modificaciones MCTS (consultar solo para trucos puntuales: progressive widening, priors).
- Repos Hearthstone (alphastone, chenjy0801/Hearthstone-AI, peter1591/hearthstone-ai) — inspiración, no reutilizables directamente.
- Simuladores PTCG ajenos a la competición: keeshii/ryuu-play (TCG completo, TypeScript), sethkarten/tcg (Pocket, C+gym+PPO), bcollazo/deckgym-core (Pocket, Rust), AngelFireLA/PokemonTCGP-BattleSimulator y apmnt/poke-pocket-sim (Pocket, Python). **Veredicto: irrelevantes** — otro juego (Pocket) u otro pool de cartas; el motor oficial ya nos da simulación exacta.
- Comunidad japonesa activa (note.com, X): p.ej. https://note.com/tanaka_now/n/n707a493e0d8a (prompt de submission mínima con Codex) — valor bajo.

## 7. Conclusiones operativas (ranking de valor)

1. **Obtener api.py oficial** (assets de la competición o `kaggle kernels pull kiyotah/reinforcement-learning-and-mcts-sample-code`) y montar búsqueda determinizada sobre `search_begin/search_step` → es la palanca que separa a SearchScorer (660 μ) de los rule-based simples, con el pilot oficial (~880 μ) como listón.
2. **Deck > agente** en la ladder (consenso de wmh/ptcg-abc y TomBombadyl): invertir en elección de deck contra el meta (Crustle anti-ex, Alakazam single-prize, Lucario/Dragapult tier alto).
3. Sparring local: agentes de wmh/ptcg-abc (sin licencia → solo como oponentes, no copiar).
4. Episodios públicos de la ladder = dataset gratuito (~210k replays) si se quiere IL/priors baratos.
5. No hay release nueva del motor esta semana; ya estamos en la última (1.32.4). Verificar versión real del evaluador («1.14.10» no existe en PyPI).
