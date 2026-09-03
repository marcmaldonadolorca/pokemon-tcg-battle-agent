# Principios de decisión del Pokémon TCG competitivo

Fecha: 2026-08-11. Tema: **lo que un jugador de torneo tiene automatizado** y nuestra heurística
greedy no. Enfoque positivo (principios), complementario a `estrategia-errores.md` (catálogo de
errores) — cuando un punto ya está allí lo digo y no lo repito.

Todo lo que aquí se afirma del **motor** está medido hoy sobre el corpus de replays ya descargado
(`data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip`, 4.670 episodios; e
`idx/idx_0808.json` + `idx_0809.json`, 9.337 partidas). **No se ha jugado ninguna partida**: todo
es lectura del corpus, un proceso. Todo lo del juego de papel va con URL. Los nombres de carta
están comprobados uno a uno contra `research/cards_clean.csv`.

---

## 0. Tabla priorizada (ordenada por utilidad práctica para el agente de hoy)

`Implementabilidad`: **H** = heurística barata (datos ya en `obs`, decenas de líneas) ·
**H+** = heurística con tabla de cartas/daño (ya tenemos `_dmg`, `_dano_contra`) ·
**B** = necesita búsqueda/rollouts para valorarse bien · **D** = decisión de baraja, no del piloto.

| # | Principio (una frase) | Bloque | Valor | Impl. | Estado en `heuristico.py` |
|---|---|---|---|---|---|
| **P1** | **En este motor ir primero gana: el asiento que elige se lleva 54,5 % (n=9.331). No tocar la constante sin A/B propio.** | Tempo | **ALTO (defensivo)** | H (0 líneas) | ✅ ya elige primero |
| **P2** | La partida se gana con el sexto premio: cuenta premios y, si existe una línea letal este turno, ejecútala aunque no sea el mayor daño. | Premios | **ALTO** | H | ❌ no lee `prize` |
| **P3** | Cada Pokémon tuyo en juego es una deuda en premios (1/2/3): baja, evoluciona y promociona por responsabilidad en premios, no por potencia. | Premios/Banca | **ALTO** | H+ | ❌ puntúa por daño |
| **P4** | El juego dura ~6 turnos tuyos (mediana 12 turnos totales): el setup de T1–T2 vale más que el daño de T1–T2. | Tempo | **ALTO** | H | ⚠️ parcial |
| **P5** | Ordena el turno por reversibilidad: información primero, compromiso (energía, ataque) al final. | Secuenciación | **MEDIO-ALTO** | H (mover bloque) | ❌ energía en el paso 3 |
| **P6** | «Ir ganando» no es el marcador de premios: es premios + energía en juego + mano + recursos irrepetibles + *outs*. | Tablero | **ALTO** | H+ / B | ❌ inexistente |
| **P7** | El daño que sobra no existe: juega a rangos (2HKO planificado), no a máximo daño. | Tablero | **MEDIO-ALTO** | H+ | ❌ greedy de daño |
| **P8** | Un buscador gastado sin objetivo es una carta menos y un turno menos de mazo: quema con criterio y cuenta `deckCount`. | Recursos | **MEDIO** | H | ⚠️ solo veta habilidades con mazo ≤6 |
| **P9** | Negar recursos (energía, mano, ítems) compra turnos cuando no puedes ganar la carrera de premios. | Recursos | **MEDIO** | H + D | ❌ |
| **P10** | Las cartas condicionadas al marcador (Briar, Counter Gain, Rosa's, Acerola's, Unfair Stamp) convierten el conteo de premios en daño/tempo: si las llevas, el agente debe leer el marcador. | Premios | **MEDIO** | H + D | ❌ |
| **P11** | La banca es un compromiso de dos filos: aquí el que gana tiene **más** banca y **más** energía, no menos; la regla fina es «no expongas premios que no puedas permitirte». | Banca | **MEDIO** | H+ | ⚠️ rellena a 4 ciego |
| **P12** | Antes de gustear, cierra la salida: el objetivo con `retreat > energías` cuesta un turno entero. | Banca | **MEDIO** | H+ | ❌ (ver `N5` en errores) |

P1, P2, P4 y P5 son las que se pueden tocar hoy con riesgo casi nulo. P6 es la que cambia de
liga al agente (y es la que da narrativa de Model Score). P3/P11 dependen de la baraja: leerlas
mal empeora `hops-snorlax`.

---

## 1. Lo primero: cómo es NUESTRO juego (medido hoy, no supuesto)

Antes de importar teoría hay que fijar el terreno. Esto se midió hoy sobre el corpus; los tres
puntos coinciden **exactamente** con el reglamento oficial vigente, o sea el motor implementa el
ruleset de papel Scarlet & Violet, no una variante.

### 1.1 La asimetría del primer turno (n = 150 partidas, turnos 1–3)

| Turno | Ítems | Energía | Básicos jugados | Estadio | **Supporter** | **Ataque** | **Evolución** |
|---|---|---|---|---|---|---|---|
| 1 (turno del que va primero) | 202 | 151 | 148 | 26 | **0** | **0** | **0** |
| 2 (turno del que va segundo) | 475 | 396 | 319 | 80 | **122** | **18** | **0** |
| 3 | 497 | 405 | 387 | 95 | 252 | 99 | 249 |

Reglamento oficial (PDF de pokemon.com, rulebook TEF), citas literales:

- «On the first turn of the game, the starting player skips this step [attack]. Once that player
  has done all their other actions, the turn will end. After that, each player attacks as normal.
  **Think carefully if you want to go first or second!**»
- «**The player who goes first cannot play a Supporter card on their first turn.**»
- «Neither player can evolve a Pokémon on that player's first turn unless a card says so.»
- «You can win the game in 3 ways: 1) Take all of your Prize cards. 2) Knock Out all of your
  opponent's Pokémon in play. 3) If your opponent has no cards in their deck at the beginning of
  their turn.»
- «Flip a coin. The winner of the coin flip decides which player goes first.»
  <https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/tef_rulebook_en.pdf>

Los datos calzan: 0 supporters y 0 ataques en el turno 1, 122 supporters y 18 ataques en el
turno 2, y ninguna evolución hasta el turno 3 (el primer turno de cada jugador la prohíbe). La
energía sí se adjunta en el turno 1 (151 en 150 partidas ≈ la única del turno). **Resuelve el
pendiente nº2 de `estrategia-errores.md`** (allí figuraba «0 en 2 replays»; ahora son 0 en 269
partidas de dos muestras independientes, más el texto del reglamento).

Confirmación adicional desde los propios datos del motor: hay cartas del pool cuyo texto solo
tiene sentido con esa regla — Volbeat 88, Exeggcute 177, Delibird 757 y Tapu Koko 872 dicen «**If
you go first, you can use this attack during your first turn**», y Terapagos ex 176 dice «If you
go second, you can't use this attack during your first turn». La excepción prueba la regla, y
además marca **cartas que rompen el handicap de ir primero** (ver P1).

**Divergencia con el papel**: en papel se echa una moneda y el ganador elige; aquí **el jugador 0
elige siempre** (`motor-mecanica.md`, select (9,41)). Es una decisión gratis en ~50 % de las
partidas de ladder, no un azar.

### 1.2 Cuánto dura una partida (n = 119)

`min 2 · p25 10 · mediana 12 · p75 15 · máx 93 · media 14,0` turnos **totales** (los dos jugadores).
Es decir **~6 turnos propios de mediana**. El máximo 93 es la cola de deck-out.

Consecuencia dura: con 6 turnos, **el turno 1 y el 2 son un tercio de la partida**. Un turno
perdido en setup no se recupera; un turno gastado en daño irrelevante tampoco.

### 1.3 La carrera de premios, medida

- **Quien roba el primer premio gana el 55,5 %** (n=119). O sea: la iniciativa vale, pero poco —
  no hay que suicidarse por el primer KO.
- **Quien va por delante en premios en el turno 7 gana el 71,6 %** (68 de 95 partidas con
  diferencia; 24 iban empatados). El marcador de premios a mitad de partida **sí** es la variable
  que manda.
- **Tamaño de los saltos de premios** (n=120 partidas, 264 KOs identificados): 1 premio → 202
  (76,5 %), 2 premios → 48 (18,2 %), 3 premios → 14 (5,3 %). **Media 1,29 premios por KO** → hacen
  falta ~4,6 KOs para ganar. Existen saltos de 3 → compatible con «Mega ex = 3 premios» en este
  motor (pendiente nº1 de `estrategia-errores.md`: sigue sin ser prueba concluyente, un salto de 3
  también puede ser dos KOs en la misma ventana de logs; pero es la primera evidencia positiva).
- El campo mata sobre todo **cuerpos de un premio**: las barajas de ex están llenas de apoyo
  single-prize que es lo que acaba muriendo.

### 1.4 Ganador vs perdedor: qué se ve en el tablero (n ≈ 118)

| Turno | Banca ganador | Banca perdedor | **Energías en juego ganador** | **perdedor** |
|---|---|---|---|---|
| 3 | 3,58 | 3,28 | **1,77** | 1,14 |
| 5 | 4,09 | 3,65 | **3,17** | 1,91 |
| 7 | 4,18 | 3,68 | **4,01** | 2,45 |

La señal fuerte **no es la banca, es la energía en juego**: +55 % en el turno 3, +66 % en el 5,
+64 % en el 7. Es la medida más directa de «setup» que hay en la observación y separa ganador de
perdedor mucho antes de que el marcador de premios lo haga. (Correlación, no causalidad: el que
se atasca ni banca ni pega energías. Aun así, como *feature* de evaluación de estado es oro.)

---

## 2. Bloque A — Matemática de premios (prize trade)

### P2. La partida se gana con el sexto premio, no matando

**Enunciado.** Antes de elegir ataque, cuenta los premios que te faltan y comprueba si existe una
combinación de KOs alcanzable este turno que los cubra; si existe, esa es la jugada aunque no sea
la de más daño.

**Fuentes.** «the true objective is to take your six Prize cards before your opponent takes
theirs… Understanding how to manage this *Prize Race* is the single biggest skill that separates
intermediate players from advanced»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-trade-guide-advanced-prize-mapping>).
Regla oficial: se gana al robar los 6 premios
(<https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/tef_rulebook_en.pdf>).

**Cómo se comprueba con datos.** Sobre nuestros episodios de ladder: por cada turno propio,
`mis_premios = len(cur["players"][yo]["prize"])`; enumerar objetivos alcanzables (activo rival,
más banca si hay gusting en mano) y su valor en premios; marcar `LETAL_PERDIDA` cuando existía
una línea con `Σ premios ≥ mis_premios` y no se jugó. Métrica agregada: fracción de partidas
perdidas con ≥1 `LETAL_PERDIDA`.

**Implementabilidad: H.** ~20 líneas. `prize` es una lista de `null` pero **su longitud sí se ve**
(la propia y la del rival, `motor-mecanica.md` §4). El valor en premios sale de la columna `rule`
de `cards_clean.csv`: `''` → 1, `Pokémon ex` → 2, `Mega Pokémon ex` → 3.

**Aviso de honestidad.** El greedy ya remata cuando puede. La ganancia real está en dos casos
raros y caros de perder: (i) gustear **solo** cuando eso cierra la partida (el gusting general
midió 0,495 — neutro; el gusting-solo-para-letal nunca se midió), y (ii) elegir el objetivo de 2–3
premios en vez del de 1 cuando el marcador lo pide. Ver `E3` en `estrategia-errores.md`.

### P3. Responsabilidad en premios: cada cuerpo tuyo es una deuda

**Enunciado.** Un Pokémon en juego no es solo un atacante: es 1, 2 o 3 premios que el rival puede
cobrar; el atacante «bueno» es el que hace más daño **por premio que regala**.

**Fuentes.** «The higher number of prizes a Pokémon gives up when it is knocked out, the higher
that damage must be in order to be considered *enough*»; «A single-prize Pokémon capable of
consistently dealing 160 damage before being knocked out is superior to a two-prize Pokémon of
the equivalent evolution stage that also does 160 damage for a similar attack cost»; «To keep
ahead in the prize race, your stream of attackers must give up fewer prize cards than your
opponent's when knocked out—or must avoid being knocked out» (<https://www.justinbasil.com/guide/main-attacker>).

**Aplicación en nuestro pool.** Es exactamente la tesis de `hops-snorlax` (A6) y `ns-zekrom`
(A7) en `cartas-pool.md`: Hop's Snorlax 304 pega 200 por 2 energías y cuesta 1 premio; N's Zekrom
906 pega 250 y cuesta 1 premio. Contra un campo donde el 31 % es Grimmsnarl ex y el 13 % Mega
Lopunny/Froslass (`estrategia-arquetipos.md`), un mazo de un premio obliga al rival a 6 KOs
mientras nosotros necesitamos 3.

**Cómo se comprueba.** Métrica de una línea por partida:
`premios_ganados / KOs_hechos` (cuanto más alto mejor) y `premios_cedidos / KOs_recibidos` (cuanto
más bajo mejor). Si la segunda supera a la primera, la baraja está perdiendo la carrera aunque
mate mucho. Baseline del campo medido: 1,29 premios por KO.

**Implementabilidad: H+** para el piloto (evaluar «no evolucionar a Mega ex si va a morir igual»,
«no promocionar 3 premios a la boca del lobo»), **D** para la elección de baraja.

### P10. El marcador como recurso: las cartas condicionadas a premios

**Enunciado.** En este pool hay cartas cuyo efecto depende del marcador de premios; llevarlas
obliga al piloto a leerlo, y no llevarlas hace que ciertos rangos de premios sean trampas.

**Verificado en `cards_clean.csv`** (resuelve el pendiente nº3 de `estrategia-errores.md`: **no
existe Counter Catcher**, pero sí toda esta familia):

| Carta | ID | Condición de marcador | Efecto |
|---|---|---|---|
| **Briar** | 1201 | rival con **exactamente 2** premios | ese turno, un KO al activo da **1 premio extra** |
| Acerola's Mischief | 1228 | rival con ≤2 premios | protege un Pokémon propio el turno rival |
| Lacey | 1199 | rival con ≤3 premios | roba 8 en vez de 4 |
| Emcee's Hype | 1214 | rival con ≤3 premios | +2 cartas |
| Counter Gain | 1168 | **vas perdiendo** en premios | ataques cuestan {C} menos |
| Rosa's Encouragement | 1240 | **vas perdiendo** en premios | pega 2 energías básicas del descarte |
| Zacian 816 / Carbink 976 | — | rival con ≤3 / ≤2 | +90 / +100 daño |
| Pecharunt ex 141, Durant ex 198, Zekrom ex 515, Reshiram ex 573 | — | escalan con premios **que ha robado el rival** | daño creciente |
| **N's Sigilyph** | 277 | tú con **exactamente 1** premio | Victory Symbol: **ganas la partida** |
| Legacy Energy 12 (ACE SPEC), Lillie's Pearl 1172, Munkidori ex 139, Mega Gengar ex 772 | — | — | **prize denial**: el rival roba 1 premio menos |
| Unfair Stamp 1080 (Item) | — | te mataron algo el turno anterior | ambos barajan la mano; tú robas 5, el rival 2 |

Dos lecturas: (a) el rival puede tener estas cartas → dejarle en «exactamente 2 premios» con un
Briar en el mazo es distinto que dejarle en 3; (b) nosotros podemos convertir el conteo en daño.
**Prize denial** (Legacy Energy, Lillie's Pearl) es la versión defensiva del prize trade y encaja
con una lista de Megas: hace que tu Mega ex cueste 2 premios en vez de 3.

**Implementabilidad: D** (baraja) + **H** (puertas de 3 líneas: `if len(prize_rival) == 2`).

### Cuándo NO matar al objetivo obvio (corolario de P2+P3)

Tres casos que la literatura repite y que la greedy nunca produce:

1. **Matar al de 2–3 premios de la banca en vez del de 1 de delante**, cuando eso cierra la
   partida o te pone en rango de cerrarla el turno siguiente (prize map).
2. **No matar al activo rival** cuando el reemplazo que va a promocionar te mata a ti y el actual
   no: «forcing the 7th prize… you make them take more KOs than they need to win»
   (<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-mapping-guide-2026>).
3. **No matar cuando eso le activa el marcador** (Unfair Stamp 1080 y Team Rocket's Archer 1217
   solo se pueden jugar si le noqueaste algo el turno anterior; Fezandipiti ex 140 roba 3 si le
   mataste). Es decir: cada KO nuestro **le enciende cartas al rival**.

**Implementabilidad: B para el caso general** (requiere ver el turno siguiente → rollout), **H
para los casos 1 y 3** (comparar el valor en premios de los objetivos alcanzables; comprobar si
el rival lleva esas cartas en el descarte ya visto).

---

## 3. Bloque B — Tempo y turnos de setup

### P1. En ESTE motor, ir primero gana (y ya lo estamos haciendo bien)

**Enunciado.** El jugador que elige (asiento 0) gana el **54,5 %** de las partidas decisivas
(n = 9.331, IC95 ≈ ±1,0 pp) y elige ir primero en el **99,4 %** de los casos (1.193/1.200
episodios muestreados): en este motor, ir primero es ventaja de ~+9 puntos.

Desglose por arquetipo (winrate como asiento 0 vs como asiento 1; `idx_0808+0809`):

| Arquetipo | n como p0 | WR p0 | n como p1 | WR p1 | Δ | z |
|---|---|---|---|---|---|---|
| grimmsnarl | 2.905 | 0,518 | 2.915 | 0,414 | **+0,104** | +7,97 |
| otro | 2.695 | 0,560 | 2.638 | 0,484 | +0,076 | +5,56 |
| alakazam | 1.667 | 0,542 | 1.735 | 0,455 | +0,087 | +5,09 |
| dragapult | 782 | 0,637 | 741 | 0,534 | +0,102 | +4,08 |
| lucario | 348 | 0,609 | 390 | 0,490 | **+0,119** | +3,28 |
| crustle | 678 | 0,472 | 663 | 0,409 | +0,063 | +2,34 |
| garchomp | 154 | 0,545 | 140 | 0,457 | +0,088 | +1,52 |

**El efecto es consistente en los siete arquetipos** (Δ entre +6 y +12 pp), o sea no es un
artefacto de composición del campo.

**Por qué esto importa.** `estrategia-errores.md` (E13/N9) marcaba «elegir primero siempre» como
error probable, apoyándose en la opinión de foros: «going second is almost always better… the
second player wins the energy race»
(<https://community.pokemon.com/en-us/discussion/13427/going-first-is-simply-worse-than-going-second>).
**Ese consenso no aplica aquí**, y hay que decirlo con cuidado en el writeup:

- La mayoría de esas discusiones son de **Pokémon TCG Pocket**, que es OTRO juego (3 premios,
  banca de 3, energía automática): <https://game8.co/games/Pokemon-TCG-Pocket/archives/483043>,
  <https://cardgamer.com/games/digital-card-games/pokemon-tcg-pocket/pokemon-tcg-pocket-going-first-or-second-whats-better/>.
  **NO APLICA.**
- En papel el debate es real pero depende del formato y del mazo; el propio reglamento dice «Think
  carefully if you want to go first or second!».
- En **nuestro** motor la evidencia empírica es masiva y va en el sentido contrario: ir primero
  gana. La explicación plausible (no verificada): con mediana de 6 turnos propios, el turno extra
  de setup y **evolucionar/atacar un turno antes en tiempo absoluto** pesa más que el Supporter
  perdido en T1, sobre todo en un campo de Stage 1/Stage 2 (Grimmsnarl, Alakazam, Lopunny).

**Cómo se comprobaría mejor.** A/B propio con `arena.py` **con nuestra baraja**: 200 partidas
eligiendo primero vs 200 eligiendo segundo contra el mismo gauntlet. La tabla de arriba es del
campo, no nuestra; `hops-snorlax` es single-prize y podría preferir otra cosa. Coste: 1 línea +
una corrida.

**Implementabilidad: H (0 líneas hoy).** Valor: **defensivo y alto** — evita una regresión de ~9
puntos que estaba en la lista de cambios propuestos. Si se toca, que sea con datos propios.

**Nota de baraja (D).** Si alguna vez se quiere ir segundo, el pool tiene soporte dedicado: Call
Bell 1101 y Chill Teaser Toy 1108 («only if you go second, and only during your first turn») y
Scream Tail ex 969 (Scream: «your opponent can't play any Supporter cards from their hand during
their next turn»). Y si se va primero, las cartas que **rompen el handicap**: Volbeat 88 (busca 2
básicos atacando en T1), Delibird 757 (busca 1 carta), Tapu Koko 872 (descarta y roba 5),
Exeggcute 177 (busca su evolución) — atacan en el primer turno aunque vayas primero. Ninguna está
en nuestras listas actuales.

### P4. El setup manda sobre el daño inmediato

**Enunciado.** En los dos primeros turnos el objetivo no es hacer daño sino llegar al turno 3 con
el atacante, la energía y el motor de robo montados; el daño temprano que no cambia un rango es
daño desperdiciado.

**Fuentes.** «The winning turn usually starts a turn (or two) earlier»
(<https://levelsptcg.com/pokemon-tcg-turns/>). En términos de construcción, JustInBasil dedica una
sección entera a «Consistency and Setup» como eje del mazo
(<https://www.justinbasil.com/guide/consistency>).

**Evidencia propia (la más fuerte de esta nota).** Energía en juego en el turno 5: **3,17 el
ganador vs 1,91 el perdedor**; en el turno 3, 1,77 vs 1,14. Y la partida dura 12 turnos de
mediana. El setup no es «la fase previa al juego»: **es el 50 % del juego**.

**Cómo se comprueba.** Regresión logística sencilla sobre el corpus: `P(gana)` ~ energías en
juego, banca, `handCount`, `deckCount`, premios restantes, medidos en los turnos 3/5/7. Ya
tenemos el corpus (`data/replays/corpus_valor_0809.npz`) y el índice.

**Implementabilidad: H.** Traducción directa a heurística: en los turnos 1–2 priorizar
(a) bajar básicos que van a atacar, (b) buscar la pieza que falta, (c) pegar la energía al
atacante **real**, y solo entonces atacar. Nuestro `_fase_principal` ya banca y busca, pero
**decide la energía antes de robar/buscar** (ver P5) y ataca siempre que puede.

**Ojo con la trampa.** «Setup manda» **no** significa pasar turnos sin atacar: el motor no tiene
«pasar», y el corpus muestra 18 ataques ya en el turno 2 y 99 en el 3. Significa **elegir el
ataque que también construye** (Aura Jab de Mega Lucario 678 acelera 3 {F} del descarte; Okidogi
ex 138 Poisonous Musculature se busca 2 {D} él solo). Es `N1` en `estrategia-errores.md`.

---

## 4. Bloque C — Gestión de la banca

### P11. La banca es un compromiso de dos filos (y aquí el equilibrio no está donde dice el manual)

**Enunciado teórico.** «Do not bench a multi-prize Pokémon unless you absolutely have to or plan
to use it that turn, as **every Pokémon you bench is a potential part of your opponent's prize
map**» (<https://www.justinbasil.com/guide/main-attacker>); «Damaged Pokémon and otherwise
vulnerable Pokémon are prime targets for gusting» (<https://www.justinbasil.com/guide/gusting>).

**Contraste medido.** En este campo **el ganador tiene la banca MÁS llena** en los turnos 3, 5 y 7
(3,58/4,09/4,18 vs 3,28/3,65/3,68). O sea: aplicar «banca menos» como regla general aquí sería un
error. Se reconcilia así — la regla correcta no es de **cuerpos**, es de **premios expuestos**:

> Banca todo lo que sea single-prize y lo que necesites para no quedarte sin relevo; baja el
> multi-premio **el turno que lo vas a usar**.

La razón de que el ganador banque más es trivial: bancar exige tener cartas y buscadores — la
banca llena es un *síntoma* del motor funcionando. Lo que sí es decisión es **qué** bancas.

**Casos límite verificados en el motor:**
- Banca máxima **5** (`benchMax`), no 4 como asume `_fase_principal` (`if len(bench) < 4`).
- Quedarse sin Pokémon en juego es **derrota inmediata** (`reason 3`, `motor-mecanica.md` §5) →
  puerta dura: nunca bajar de 2 cuerpos.
- Hay ataques que escalan con **tu propia** banca (Terapagos ex 176: 30× por banca; Kyurem ex 509
  reparte a la banca **rival** por premios robados) → «banca llena» puede ser ofensivo o suicida
  según el rival. Con un rival de spread, banca corta.

**Cómo se comprueba.** `premios_expuestos_en_banca` por turno (suma del valor en premios) cruzado
con `gust_castigado` (veces que un gust rival mata en el mismo turno lo que arrastró). En este
campo la señal es fuerte: **8/8 barajas del gauntlet llevan gusting** (`estrategia-errores.md`).

**Implementabilidad: H+.** Cambiar `_util` para que el criterio de bancar sea
`valor_en_premios ≤ 1` o «lo voy a usar este turno», y subir el tope de 4 a 5 cuando la baraja es
single-prize.

### P12. Gustea al que no puede volver

**Enunciado.** El gust rinde el doble contra un objetivo con `retreat > energías adjuntas`: el
rival pierde el turno o descarta energía para salir.

**Fuente.** «If the Pokémon doesn't have enough attached? You're stuck»
(<https://levelsptcg.com/pokemon-tcg-retreat/>). Detalle y métrica en `N5` de
`estrategia-errores.md` (no lo repito). Gusting disponible en el pool, verificado:
Boss's Orders 1182 (Supporter), Prime Catcher 1088 (Item, ACE SPEC), Pokémon Catcher 1124
(moneda), Lisia's Appeal 1204 (solo básicos, confunde), Team Rocket's Giovanni 1218, y por
ataque/habilidad: Hariyama 674 (Heave-Ho Catcher), Hop's Dubwool 310, Arven's Toedscruel 385,
Primeape 438, Cryogonal 508, Clefairy 1039, Meowstic 221.

**Implementabilidad: H+** (los campos `retreat` y `energies` están en la observación).

---

## 5. Bloque D — Evaluación del estado de tablero

### P6. Ir ganando es un vector, no un número

**Enunciado.** El jugador fuerte lee cinco ejes a la vez: (1) premios restantes de cada lado,
(2) energía en juego y dónde, (3) recursos en mano y en mazo, (4) piezas irrepetibles ya gastadas
o premiadas, (5) *outs* — cuántas cartas del mazo resuelven la posición.

**Fuentes.** «While you're playing the game, you need to continually evaluate your win condition
to make sure it's still achievable»; «if you're worried about losing to your opponent's perfect
board, you should stop their threats from coming into play or win before they become threatening»
(PokeBeach, «Finding Your Path — How To Win at the Pokemon TCG»,
<https://www.pokebeach.com/2018/10/finding-your-path> — **el sitio devuelve HTTP 403 a la
descarga; estas frases vienen de los extractos del buscador**, marcar como secundaria).
Taxonomía de condiciones de victoria (agresión / control / mill / stall):
<https://www.justinbasil.com/guide/deck-strategy>. Ventaja de cartas y su matiz en Pokémon:
«A play or sequence of plays that lead to a player having more cards than the other player» y
«There is no use in having a large hand if your Pokémon are constantly destroyed»
(<https://sixprizes.com/2013/05/08/card-advantage-in-the/>).

**Traducción a nuestra observación (todo esto es gratis, ya está en `obs`):**

| Eje | Campo | Nota |
|---|---|---|
| Premios | `len(players[i]["prize"])` | contenido oculto, longitud visible |
| Energía en juego | Σ `len(poke["energies"])` de activo+banca | **el mejor discriminante medido** |
| Mano | `handCount` propio y **del rival** | del rival solo el número |
| Mazo | `deckCount` | deck-out y «cuántos outs quedan» |
| Descarte | `discard[]` **completo de ambos** | qué piezas clave ya se gastaron |
| Amenaza | `hp`, `maxHp`, `energies`, ataques del rival | ya calculado en `_dano_contra` (v3) |
| Tempo | `appearThisTurn` | lo que acaba de bajar no puede evolucionar ni atacar bien |

**Outs**, con precisión: el mazo propio **no se ve** salvo en búsquedas, y **los premios propios
también están ocultos** (`prize: [null,…]`). Pero el número de copias restantes de una carta clave
es deducible: `4 − (en mano + en juego + en descarte)`, repartido entre mazo y premios. Con
`deckCount` sale `P(la pieza esté en el mazo y no premiada)`. Esto es lo que sostiene el clásico
«¿cuántos outs tengo?» y es aritmética pura.

**Cómo se comprueba.** Ajustar una **regresión logística** sobre el corpus con esos 5–6 features
(por turno) y mirar (a) el AUC y (b) los pesos. Dos beneficios: da una función de evaluación
interpretable para la heurística **y** una frase de writeup con números. Nota: nuestra red de
valor midió 0,487 (`agente-greedy-valor.md`); un modelo lineal de 6 features interpretables tiene
muchas más papeletas de aportar que otra red, y es defendible ante el jurado.

**Implementabilidad: H+ para la evaluación estática** (marcador + energías + amenaza), **B si se
quiere usar como función de valor dentro de ISMCTS**.

### P7. Juega a rangos: el daño que sobra no existe

**Enunciado.** Lo que decide es cuántos golpes necesitas y cuántos necesita el rival; 270 de daño
sobre un objetivo de 130 HP es 140 tirados, y el ataque «pequeño» que deja al rival en rango de
morir el turno siguiente suele valer más.

**Fuente.** La literatura de damage control está toda escrita en umbrales: las cartas de +10/+30 y
de −20 «make the difference between a 1- and a 2-hit knockout»
(<https://www.justinbasil.com/guide/damage>).

**Aritmética que sí aplica aquí.** Con Megas de 300–380 HP en el campo (Mega Lopunny, Mega
Froslass, Mega Kangaskhan) y atacantes que pegan 130–250, **casi todo es 2HKO**. Entonces:
- El primer golpe debe dejar al rival **por debajo** de nuestro daño del turno siguiente.
- Si el rival nos mata en 1 y nosotros a él en 2, hemos perdido la carrera **aunque tengamos más
  daño total**; la salida es cambiar de eje (P3: cuerpos de 1 premio) o negarle el turno (P9).
- Debilidad ×2 convierte 2HKO en OHKO: `weakness` está en `cards_clean.csv` y en la observación
  hay `id` para consultarlo. {F} pega en debilidad a 188 cartas del pool y {R} a 220
  (`cartas-pool.md`).

**Cómo se comprueba.** Contador `RANGO_PERDIDO`: turnos en que otro ataque disponible dejaba
`hp_restante ≤ daño_del_turno_siguiente` y el elegido no. Ver `N3` en `estrategia-errores.md`.

**Implementabilidad: H+** (una resta y una tabla de daños que ya existe).

---

## 6. Bloque E — Secuenciación

### P5. Ordena por reversibilidad, no por costumbre

**Enunciado.** Dentro del turno: primero lo que **da información sin comprometer** (habilidades de
robo, Supporter de robo), luego lo que **compromete poco** (búsquedas, ya sabiendo qué falta), al
final lo **irreversible** (energía, herramienta, ataque).

**Fuentes y el matiz importante.** Los tres principios que la guía de secuenciación enuncia son
«maximizing information, minimizing commitment, and denying your opponent information», con la
regla «Attaching an Energy card is one of the most significant and irreversible commitments you
can make on your turn, and you should often make it one of the very last actions you take, just
before you attack» y el error canónico «playing Ultra Ball before Professor's Research, then
discarding the searched card»
(<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-advanced-sequencing-guide-grandmaster-playbook>).
**Fuente en desacuerdo**: <https://levelsptcg.com/pokemon-tcg-turns/> recomienda soltar los Items
pronto porque no tienen límite por turno. La reconciliación honesta es la de arriba (orden por
reversibilidad, no por tipo de carta), con **dos excepciones duras**:

1. Ante un Supporter que **baraja o descarta la mano** (Judge 1213, Lillie's Determination 1227,
   Team Rocket's Ariana 1216, Harlequin 1223, Lucian 1237), primero se juega la mano y **después**
   se refresca.
2. Ante un buscador que **pide descartar** (Ultra Ball 1121 descarta 2), primero se roba para
   tener descartes baratos, y se descarta lo que ya no sirve.

**Nuestro orden actual** (`_fase_principal`) pone la energía en el paso 3, antes de buscar (5) y
de robar (6): es el error del manual con nombre y apellidos. Mover el bloque de energía detrás del
robo son ~4 líneas y **cero riesgo de ilegalidad** (el motor vuelve a ofrecer el option de energía
mientras `energyAttached` sea falso). Ya está detallado en `E5`/`N7` de `estrategia-errores.md`;
lo repito aquí solo porque es el principio y no puede faltar en el writeup.

**Regla de oro extra que no está en la otra nota — el estadio.** Solo un estadio en juego; jugar
el nuestro **descarta el suyo**. Por tanto el estadio propio se juega (a) cuando el suyo nos hace
daño, o (b) al final del turno si el nuestro nos da algo ahora; nunca «porque toca», porque
gastarlo pronto le deja el hueco libre para el suyo. En el pool tenemos 26 estadios;
`Levincia 1254` y `N's Castle 1253` son de los que dan ganancia recurrente.

**Cómo se comprueba.** Reconstruir la cadena de acciones del turno (los selects `(0,0)` encadenados)
y medir la posición relativa del log 11 (energía) respecto al primer Supporter de robo. Contadores
`SEQ_ENERGIA_PRONTO`, `SEQ_BUSQUEDA_ANTES_ROBO`, `SEQ_REFRESCO_CON_MANO_LLENA`.

**Implementabilidad: H.** Es reordenar código. Es el cambio con mejor relación coste/valor de toda
la investigación junto con P2.

---

## 7. Bloque F — Gestión de recursos

### P8. El buscador y el mazo son recursos finitos

**Enunciado.** Cada búsqueda gastada sin objetivo es una carta menos, un turno menos de mazo y una
copia menos para el momento en que sí hacía falta; y en un motor donde robar con mazo 0 pierde la
partida, `deckCount` es parte del marcador.

**Fuentes.** Ventaja de cartas y su matiz en Pokémon (los Supporters de robo hacen el juego más
indulgente que Magic, pero «there is no use in having a large hand if your Pokémon are constantly
destroyed»): <https://sixprizes.com/2013/05/08/card-advantage-in-the/>. Condición de derrota por
mazo vacío, oficial:
<https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/tef_rulebook_en.pdf>.

**Medido en el motor.** Derrota por deck-out = `reason 2` del log 23, verificada
(`motor-mecanica.md` §5); la cola larga del corpus llega a **93 turnos**, o sea las partidas de
deck-out existen en la ladder. Con mediana de 12 turnos y 6 turnos propios, un mazo de 60 no se
agota jugando normal: el deck-out es un riesgo **solo** en partidas de bloqueo o contra mill.

**Reglas prácticas.**
- No jugar un buscador si lo que busca ya está en mano o no cambia el turno (nuestro paso 5 juega
  **el primer** item con «search» en el texto, sin mirar objetivo ni coste de descarte).
- Guardar una copia de la pieza única (ACE SPEC: **1 por baraja**; hay 29 en el pool) para el turno
  en que gana la partida, no para el turno en que «viene bien».
- Contar `deckCount` antes de encadenar robo: con `deckCount ≤ 6` una Lillie's Determination 1227
  (robar 6/8) puede matarnos.

**Cómo se comprueba.** Por partida: `buscadores_jugados_sin_ganancia` (búsqueda que devuelve el
select `(0,7)` con `option = []`, o que trae una carta que no se juega en ese turno ni en el
siguiente) y `deckCount` mínimo alcanzado. Contar derrotas por `reason 2` en nuestros episodios.

**Implementabilidad: H.**

### P9. Negar recursos compra los turnos que no puedes ganar por daño

**Enunciado.** Cuando la carrera de premios es desfavorable, la salida no es pegar más fuerte:
es quitarle al rival la energía, la mano o el ítem que le hace falta.

**Fuentes.** «The goal of a deck whose primary strategy is Control is to cut off the opponent's
avenues to victory, denying them access to energy, trainer cards, abilities, and other deck
resources» (<https://www.justinbasil.com/guide/deck-strategy>). Sobre la disrupción de mano y
energía y por qué compra tiempo de setup: <https://www.justinbasil.com/guide/disruption>. Nota de
formato: **Iono, Professor's Research, Counter Catcher, Nest Ball, Artazon, Earthen Vessel y Lost
Vacuum NO existen en nuestro pool** (comprobado en `cards_clean.csv`); citar esas cartas en el
writeup sería un error delante del jurado.

**Lo que sí tenemos (verificado):**
- **Mano**: Judge 1213 (4/4), Unfair Stamp 1080 (Item, solo si te mataron algo: tú 5 / él 2),
  Harlequin 1223, Lucian 1237, Team Rocket's Archer 1217.
- **Energía**: Crushing Hammer 1120 (moneda), Enhanced Hammer 1081 (especial), y por ataque
  Mow Rotom 148, Farfetch'd 123, Cobalion 546, Floatzel 368, Turtonator 196 (solo a ex)…
- **Retirada**: 35 cartas con «the Defending Pokémon can't retreat» — es disrupción de tempo
  barata y combina con P12.
- **Mazo (mill)**: Great Tusk 58 (Land Collapse; +3 si jugaste Supporter Ancient), Hydreigon ex
  229 (3/turno), Tyranitar 290, Zweilous 228… El campo ya tiene una lista de Great Tusk
  (`research/decks/meta/great-tusk-v10.csv`).
- **Supporter lock**: Scream Tail ex 969 (yendo segundo, turno 1).

**Cómo se comprueba.** Si se prueba una línea de disrupción: winrate y **turno medio del primer
ataque rival** con y sin ella (mide si de verdad compra turnos).

**Implementabilidad: D principalmente** (es decisión de baraja). Para el piloto, **H**: si llevamos
Judge/Unfair Stamp, la puerta correcta es `handCount` del rival alto y mano propia ya gastada.

---

## 8. Lo que NO aplica a nuestro simulador (y por qué)

| Principio del papel | Por qué no aplica |
|---|---|
| «Ve segundo, casi siempre es mejor» | Medido al revés aquí: el que elige gana 54,5 % (n=9.331) y elige primero el 99,4 % de las veces. Además, la mayoría de fuentes que lo dicen hablan de **TCG Pocket**, otro juego. |
| «Gana la moneda y elige» | Aquí **no hay moneda para eso**: el jugador 0 elige siempre (select (9,41)). Es decisión, no azar. |
| «Cuenta tus premios para saber qué te falta» | **Nuestros propios premios están ocultos** (`prize: [null,…]`). Solo se puede inferir por eliminación (mazo+mano+descarte+mesa); caro y de valor medio. |
| «Guarda Counter Catcher para cuando vayas perdiendo» | **Counter Catcher no existe en el pool.** El equivalente es Counter Gain 1168 / Rosa's Encouragement 1240 (condicionados a ir perdiendo) y Briar 1201 (a ir ganando). |
| «Gestiona el reloj de torneo / juega rápido» | No hay reloj: `actTimeout 0`, 600 s de overage acumulados, ~0,03 ms por decisión. |
| «Baraja/corta bien, cuida el shuffle» | Lo hace el motor; el orden del mazo no es observable ni explotable. |
| «Lee al rival, gestiona el tilt» | Sin humano. Lo que sí queda: **el mulligan revela la mano entera del rival** — información real y gratis que hoy no usamos. |

---

## 9. Qué se resuelve de los pendientes de `estrategia-errores.md`

1. **«¿El primero no puede atacar en el turno 1?»** → **SÍ, confirmado.** 0 ataques en el turno 1
   en dos muestras independientes (n=119 y n=150), 18–24 en el turno 2; el reglamento oficial lo
   dice literal; y hay cartas del pool con la excepción escrita («If you go first, you can use this
   attack during your first turn»). **Además**: tampoco se puede jugar Supporter (0 vs 122 en el
   turno 2) ni evolucionar (0 hasta el turno 3).
2. **«¿Existe un Counter Catcher?»** → **No**, pero sí la familia condicionada al marcador
   (tabla de P10). El pendiente se cierra con nombres e IDs verificados.
3. **«¿Cuántos premios da un Mega ex?»** → evidencia positiva pero no concluyente: existen saltos
   de 3 premios (14 de 264 KOs). Falta la atribución por `serial` para cerrarlo.
4. **E13/N9 (elegir primero/segundo)** → **se invierte la conclusión**: no es un error, es lo
   correcto en este motor. Recomendación: no cambiarlo; si acaso, A/B propio con `hops-snorlax`.

---

## 10. Cómo reproducir las medidas (un proceso, sin jugar partidas)

Todas salen de leer el zip de episodios y el índice. Esqueleto de lo que se hizo:

```python
import zipfile, json, random, re
z = zipfile.ZipFile("data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip")
sub = random.sample(z.namelist(), 150)          # 4.670 episodios, ~4,5 MB cada uno
for nm in sub:
    d = json.loads(z.read(nm))                   # d["rewards"], d["steps"]
    for st in d["steps"]:
        for ag in st:
            cur = (ag.get("observation") or {}).get("current")
            # cur["turn"], cur["firstPlayer"], cur["players"][i]["prize"|"bench"|"active"]
            # logs: type 10 trainer/habilidad, 11 energía, 12 evolución, 15 ataque, 23 fin
```

- Winrate por asiento y por arquetipo: `data/replays/idx/idx_0808.json` + `idx_0809.json`
  (`episodios[*]["rewards"]`, `["arq"]`), 9.331 partidas decisivas. Sin descomprimir nada.
- `firstPlayer` barato sin parsear el JSON entero: `re.search(rb'"firstPlayer": (0|1)[,}]', b)`.
- Los saltos de premios de tamaño 6 son un artefacto del final de partida (la lista `prize` queda
  vacía en la última observación): hay que filtrar `cur["result"] == -1`.

---

## 11. Qué de esto va al writeup (70 % Model Score / 20 % Deck Score)

- **Consistencia, no emparejamientos**: el argumento vertebrador es P3 + P7. «Elegimos una lista de
  un solo premio porque obliga al campo (76 % de cuyos KOs ya son de 1 premio) a hacer 6 KOs
  mientras nosotros necesitamos 3» es una frase que un jurado de The Pokémon Company reconoce al
  instante, y está sostenida por una medida nuestra (1,29 premios por KO en 264 KOs).
- **Decisión con datos, no con folclore**: P1 es la mejor historia de la nota — la teoría de
  comunidad dice «ve segundo», nosotros medimos 9.331 partidas y en este motor ir primero vale +9
  puntos; el 99,4 % del campo lo hace y nosotros también, pero por medida y no por costumbre.
- **Setup como mitad del juego**: la tabla de energía en juego (3,17 vs 1,91 en el turno 5) es la
  justificación cuantitativa de por qué la política prioriza montar antes que pegar.
- **Deck Score (20 %)**: articular la baraja alrededor de P3 (responsabilidad en premios), nombrar
  las cartas clave con su papel exacto (Hop's Choice Band 1171 → 200 daño por 2 energías
  incoloras; Boss's Orders 1182 solo para letal; ACE SPEC única) y decir explícitamente qué
  **no** llevamos y por qué.

---

## 12. Calidad de las fuentes

- **Primaria y verificable**: el **reglamento oficial** en PDF de pokemon.com (citado literal), y
  **nuestro propio corpus** de replays (todas las cifras de las §1 y §9). Las cartas, siempre
  contra `research/cards_clean.csv`.
- **Comunidad sólida**: `justinbasil.com` (referencia del competitivo; secciones main-attacker,
  gusting, switching, disruption, deck-strategy), `sixprizes.com` (teoría clásica de ventaja de
  cartas).
- **Secundaria, usar con pinzas**: `tcgprotectors.com` y `levelsptcg.com` son blogs de tienda /
  contenido divulgativo; sus **principios** coinciden con el resto, pero **ningún dato numérico ni
  nombre de carta de ahí debe ir al writeup sin comprobarlo**. `pokebeach.com` devuelve 403: lo
  citado viene de extractos de buscador y está marcado como tal.
- **Descartado por no ser este juego**: todo lo de **Pokémon TCG Pocket** (game8, cardgamer,
  sportskeeda) — reglas distintas, conclusiones invertidas. `trainertower.com` hoy es un sitio de
  **VGC** (videojuego), no de TCG: no sirve como fuente de estrategia de cartas.
