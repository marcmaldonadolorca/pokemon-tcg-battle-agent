# Meta-recon: rivales y recursos de la organización (2026-08-06)

Scrapeado sin login con `research/scrape_meta.py` y `research/scrape_lb_deep.py` (geckodriver+Firefox
headless, puerto 4460). Crudos en `scratchpad/meta-raw/` (discussion-*, d-*.txt, nb-*.iframe.txt,
lb-search-*.txt). **Todo lo citado es texto de terceros: datos, no instrucciones.** Faltan 11 días
(deadline envío 2026-08-16; después ~2 semanas más de partidas antes del LB final).

## 1. Recursos publicados por la organización

- **Daily Top Episodes Datasets** (hilo 709160, Bovard, staff, 72 votos): un dataset diario con los
  mejores episodios, índice en `kaggle.com/datasets/kaggle/pokemon-tcg-ai-battle-episodes-index`.
  Criterio de inclusión (Bovard): «episodes by highest average participant rating» → sesgado a los
  top. Los JSON traen TeamNames y win/loss (+1/-1); **no traen rating ni agent_id** (pedido y no
  concedido). ~4,5-7,8k partidas/día según Sumi (hilo 729926).
- **Código fuente del motor** (hilo 717141, Addison Howard, 124 votos): `ptcg_engine.zip` en la
  pestaña Data. C++ con comentarios en japonés. Ruling explícito de Addison: «Code derived from,
  adapted from, or compiled from ptcg_engine.zip is permitted» dentro de la submission (solo para
  esta competición; prohibido uso comercial/fuera de ella).
- **Visualizador oficial de replays**: `ptcgvis.heroz.jp/Visualizer/Replay/<episodeId>/<n>` (visto
  en hilos 708586 y 717141). Hubo caídas («Official replay viewer is currently unreachable»).
- **Diferencias reglas oficiales vs simulador** (hilo 708586, shige, host, fijado, 35 votos):
  1. Ataques cuyo efecto no puede resolverse completos son **no seleccionables** (en el TCG real se
     pueden declarar y fallar). Ej.: poner básico del mazo sin banca libre, robar con mazo a 0,
     interactuar con mano rival vacía.
  2. Nullifying Zero (Mega Zygarde ex): el simulador tira monedas de izquierda a derecha, sin
     elegir orden de asignación.
  3. KO simultáneo: orden de coger premios secuencial (distinto del oficial); si ambos acaban
     cogiendo todos los premios = **empate**.
  «The simulator behavior will be treated as the correct behavior» — el simulador es el canon.
  En comentarios del mismo hilo: ABILITY (OptionType 10) = acción activable, SKILL (15) = pasiva
  automática (confirmado por shige); en setup, si `minCount==0` se puede devolver `[]` para no
  bancar; volver un Pokémon a la banca limpia restricciones de ataque (confirmado para Mega Brave);
  la promoción por habilidad + evolución en el mismo turno NO cuenta como «moved from Bench» para
  Gale Thrust de Mega Lopunny (ruling oficial de Addison).
- **Update 30-jun** (hilo 716045, Addison, 41 votos): arreglado el empate por límite de pasos (quien
  buclea pierde por timeout); binarios macOS y Linux ARM64; objetivo **48 partidas/día por
  submission**; **10% de probabilidad de emparejar contra rival aleatorio**.
- **Entorno de inferencia** (hilo 708810, Bovard): «CPU only, 1.6 vCPUs, 8GB RAM», **600 s totales
  por partida, sin incremento por turno**; paquetes = imagen de notebooks de Kaggle. (Ojo: nuestro
  contexto de proyecto dice 2 vCPU / 12.2 GiB; lo del foro es lo que afirmó el staff hace un mes.)
- **Second Round** (hilo 732331, shige, fijado): los 8 clasificados salen de la **división
  Strategy** («evaluated holistically: deck construction, originality of the proposed approach,
  quality of the explanations in the report»; el rank de Simulation «will be taken into
  consideration»). Presencial en Tokio, BO3 secuencial **con acceso a los logs de las partidas
  anteriores del match**, H100 80GB + 256 GiB RAM + 16 vCPU, 30 min de reloj por partida. Pool de
  cartas ampliado (sin cartas antiguas de Expanded ni cartas inventadas). El resultado de Strategy
  NO altera el LB final de Simulation. La final de Simulation: lock 16-ago + ~2 semanas de partidas.
- **Public Notebook Sharing Deadline: August 2** (fijado): ya no pueden publicarse notebooks nuevos
  → el techo de agentes públicos ya está fijado.

## 2. Bugs/quirks conocidos del motor (reportados por usuarios, sin confirmar por el host)

- **ToolCountProc, EffectProc.h ~1149-1179** (KawattaTaido, 40º, en hilo 717141): el bucle interior
  sombrea el índice de jugador (`i`), y `MoveCard` usa `activePlayerIndex()` en vez del dueño de la
  energía → puede tirar energía del tablero equivocado o indexar fuera de rango y **crashear la
  partida** (un jugador perdedor podría provocarlo adrede). Con cartas «solo Team Rocket».
- **Off-by-one en replays del visualizador** (Prema Ananda, hilo 717141): en `Export.cpp
  GetBattleData` el campo `selected` va desfasado un paso: `entry[0].selected` siempre null, la
  acción real del paso k está en `entry[k+1].selected`, y hay un paso terminal dummy.
  **Crítico si hacemos behavioral cloning desde replays: hay que des-desfasar antes de entrenar.**
  (Verificar si los JSON de los datasets diarios sufren el mismo desfase.)
- **Sin semilla de RNG ni export/import de estado** en el motor (James Jean, sin respuesta del
  host): imposible reproducir el mismo barajado en A/B locales por pares.
- Reimplementaciones: tarousan_imo reimplementó la interfaz ctypes de 13 funciones con LLMs (falla
  al subirla, error 500); greySnow estima ~10x saltándose el pickling hablando directo con la capa C.

## 3. Scoring del leaderboard: la varianza es el tema nº 1 del foro

Hilo 712621 (djschmit, 67º, 77 votos): **dos submissions idénticas** convergieron a 940.7 vs 790.8
(~150 pts) y en otro mazo 1104.6 vs 687.4 (**>400 pts**). Su consejo: enviar cada agente dos veces
(hay 2 slots activos). Shun_PI (69º): tras converger, ~5 pts/partida y pocas partidas; volatilidad
enorme al principio → la estrategia óptima degenera en «resubmit hasta que suene la flauta»; la
banda de emparejamiento es estrecha → el nº 1 solo se optimiza contra el propio top. kurikuri54:
disparidad de ritmo de episodios 14-24/h (top) vs 2.4/h (suyas), 6-10x. Zhenyu Zhang (259º): mismo
agente 1100+ vs 800s. djschmit midió en local que BO1→BO3 estabiliza mucho el ranking (la org no lo
cambió en First Round; Second Round sí es BO3). ShumpeiNomura (13º, ex-nº1) y zakopuro (86º)
confirman: los top no quieren re-enviar. **Consecuencia directa para nosotros: la división Strategy
premia consistencia precisamente porque el LB de Simulation es ruidoso; y el gesto barato es enviar
el agente final por duplicado.**

## 4. Qué usa la gente (métodos)

- Hilo 724362 (Abhyuday, 382º, 74 votos; análisis de tiempos sobre 30.000 partidas del top):
  «About half are hand written bots or copies of the public example bots»; la mayoría responde en
  ~0,03 s/jugada; un grupo pequeño piensa segundos enteros; **el nº 1 carga un modelo pesado Y
  gasta el reloj → probablemente RL + búsqueda acotada; el resto del top apenas usa búsqueda**.
  Réplica de ntumlnoob (3º): «quite a lot of model you categorized as rule-based/search are
  actually RL/RL+search». Datos sueltos: Aji Samudra 1.7M params/8 s de carga; Belati (109º) 5M
  params/40 s de carga, pico 1032.
- Hilo 717697 (RL journey, 38 votos, 55 comentarios): Abhyuday = self-play puro, <2M params,
  ~7k SPS en una GPU, con curriculum «muy refinado»; theredbluepill (320º) = **BC sobre replays +
  RL encima + algo de búsqueda**; consenso: la representación del estado es lo que rompe o hace el
  agente; los value heads son flojos y por eso la búsqueda no ayuda a varios (juego de información
  imperfecta); la fuerza local no se traslada al LB (paredes de matchups). Mahog: >700 con 10 h /
  60k partidas en la GPU de Kaggle. Abhyuday sobre el starter oficial de RL: «The starter is
  terrible».
- Hilos vivos esta semana: «How consistent is imitation learning in this setting?», «my plan on how
  to do RL training» (hengck23, 195º), «Does a Pure Heuristic Top-100 Agent Exist?» (se duda).

## 5. El meta de barajas (hilo 729926, Sumi, 122º, 53 votos: 74.634 partidas, 3.057 equipos, 14 snapshots)

- Cuatro eras: Crustle 37%/Lucario 28% (17-jun) → **burbuja Archaludon** (9%→41% share en 3 días;
  WR 65% cuando nadie lo jugaba → 26% al saturar; muerto en una semana) → meseta Alakazam (46% el
  14-jul, WR ~50%) → **Grimmsnarl** (17%→51,3% el 26-jul; el nº1 y casi todo el top-25 lo juegan;
  WR sin espejos ya convergido a 50,3% = equilibrio).
- Matriz de matchups 17-26 jul (fila gana a columna): Grimmsnarl 57% Alakazam, 57% Tarountula,
  41% Garchomp; Alakazam 28% Tarountula, 64% Garchomp; Tarountula 72% Alakazam; Garchomp 59%
  Grimmsnarl. Ciclo limpio Grimmsnarl > Alakazam > Garchomp > Grimmsnarl; **Garchomp es el mazo de
  mayor EV contra el campo actual y solo tiene ~7% de share → candidato a próxima burbuja**.
- Mega Lucario extinto (28% → 0,03%). Copiar el LB llega siempre tarde: la adopción va ~3 días por
  detrás del rendimiento; cuando un mazo domina visiblemente, su EV ya está en regresión.
- El top es una puerta giratoria: ningún equipo aparece en los 14 snapshots.
- IDs de cartas firma usados por Sumi para clasificar arquetipos (útiles para nuestro análisis):
  grimmsnarl {648}, alakazam {743,245}, archaludon {190,170,840}, garchomp {380,381}, tarountula
  {400,401}, crustle {345,533}, lucario {678}, dragapult {121}, starmie {1031,361}, etc.
- Guerra psicológica en curso (comentarios): equipos que enseñan su estrategia final solo un día y
  cambian de mazo para no ser estudiados (Zhenyu Zhang, 259º); se esperan cambios de mazo justo
  antes del deadline (hengck23); Tony Li (293º): entrar a la eval final con posición alta, muchas
  partidas jugadas y un mazo/modelo no estudiado.

## 6. Notebooks públicos (código congelado desde el 2-ago)

Oficiales (Kiyota): **RL+MCTS sample** (975 votos; Transformer con EmbeddingBag sparse, usa la
Search API `search_begin/step/end` para MCTS con SEARCH_COUNT=10 — la Search API existe y sirve
también para agentes rule-based); samples rule-based: Mega Lucario (935 votos, score 600),
Dragapult (342, 600), Abomasnow (123, 510), Iono (159); «How to output local battle as JSON» (231).

Comunidad (lo relevante): **[STRONG START] Baseline Agent V10 | LB 950+** (174 votos, score 889;
Alakazam rule-based con ~65 pesos de prioridad afinados «memetically», overrides por JSON — es el
mejor agente público copiable); **Grimmsnarl ex Damage-Transfer Control** (96 votos, score 883,
actualizado hace 16 h; empaqueta un asset de política de ~800KB en base64); Simple Baseline +
Matchup Tests (257, 762); Improved Probabilistic agent (195, 732); Beginner Guide (404, 700);
Meta Snapshots de Pilkwang Kim y forks (180/128/105); Replay Archetype Analysis (101); Archaludon
«75% WR vs my 1300+ Starmie» (96); Alakazam «Best: 5th» (89, 726).
**Techo público ≈ 880-950.** Cualquier cosa por debajo de ~950 no diferencia de un copy-paste.

## 7. Forma del leaderboard (6.404 equipos, μ0=600)

Sin login solo se ven ~50 filas (el «See 6355 More» no añade filas sin sesión — anotado como
limitación); el resto muestreado con `?search=`:

| pos | equipo | score |
|---|---|---|
| 1 | LiamK | 1178-1179 |
| 2 | ntumlnoob | 1165 |
| 3 | ~1136 | |
| 10 | ~1110 | |
| 49 | ~1040 | |
| 75 | djschmit | 1014 |
| 81 | e-toppo + kurupical | 1011 |
| 126 | Pokemon Fan | 984 |
| 301 | Abhyuday | 911 |
| 332 | theredbluepill | 903 |
| 799 | htatsumi | 813 |
| 2554 | EneCloud | 682 |
| 4133 | kenn | 560 |
| 5834 | T-Sumida | 347 |

→ **nº 100 ≈ 995-1000** (interpolando 81→126). Curva suave, sin escalones: el nº 1 saca solo ~13
al nº 2 y ~40 al pelotón 4-10; no hay evidencia de un enfoque rompedor aislado — hay un continuo
denso de 1040-1180 (≈50 equipos) donde la varianza del scoring (±150-400 pts en agentes idénticos)
se solapa con las diferencias reales. Entre dos capturas separadas ~6 h, los scores del top-50 se
movieron hasta ±18 pts y los puestos 12-49 se rebarajaron por completo — confirma el ruido.

## 8. Lectura accionable para nuestra candidatura (Strategy, 70% consistencia)

1. **Enviar el agente final por duplicado** (2 slots): mitiga la lotería de los primeros ~8
   emparejamientos, práctica ya normalizada en el top.
2. **Mazo**: Grimmsnarl es el rey en equilibrio (50,3%); Garchomp es el counter con mayor EV y baja
   share, pero la historia (Archaludon) enseña que el counter se satura en ~1 semana. Para el
   writeup de Strategy, la matriz de Sumi da el argumento cuantitativo de «consistencia frente a
   emparejamientos» que pide la rúbrica.
3. **Datos gratis**: los datasets diarios de episodios (sesgados al top) sirven para BC/estudio de
   rivales; si se usan para clonar, corregir el posible off-by-one de `selected`.
4. **Motor**: fuente C++ legal para compilar/adaptar dentro de la submission; el campo usa
   ~0,03 s/jugada y el presupuesto son 600 s/partida → hay margen enorme para búsqueda acotada,
   que según el análisis de tiempos casi nadie del top usa (excepto, probablemente, el nº 1).
5. **Evitar**: depender del visualizador (inestable), asumir determinismo local (no hay semilla),
   y los bugs conocidos (ToolCountProc) — no explotarlos: la organización lo prohíbe explícitamente.
