# Arquetipos del campo: cómo los pilota un humano bueno

Fecha: 2026-08-10. **Pase 2: 2026-08-11** (§7 al final: listas de papel con conteos reales,
mapa de premios, cartas del pool que el pase 1 no vio y **cuatro correcciones de aritmética
que cambian decisiones**). Tema: conocimiento de juego por arquetipo (plan, línea de turnos
1-3, punto débil, cómo se juega CONTRA), contrastado carta a carta con
`research/cards_clean.csv` y con la matriz de emparejamientos **medida en nuestra propia
ladder**.

Fuentes de papel citadas con URL en cada sección. **Todo texto de carta que aparece aquí está
copiado de `cards_clean.csv`** (el simulador), no de la web: cuando el papel y el pool no
coinciden se dice explícitamente.

---

## 0. AVISO: el censo del encargo está desactualizado

El encargo parte de «Mega Lucario ~42%, Alakazam ~17%, aggro tipo-ejemplo ~17%, Garchomp ~8%».
Eso era el censo de 12 replays. `research/notas/baraja-vs-campo.md` (18.674 barajas, 9.337
partidas de los días 0808/0809) lo corrige y aquí se confirma recalculándolo:

| # | arquetipo | share | WR real |
|---|---|---|---|
| 1 | Marnie's Grimmsnarl ex + Munkidori + Froslass | **31,2%** | 46,6% |
| 2 | Alakazam (+Dudunsparce/Fezandipiti) | **18,2%** | 49,7% |
| 3 | Mega Lopunny ex + Mega Froslass ex | **12,8%** | 51,0% |
| 4 | Dragapult ex | 8,2% | **58,7%** |
| 5 | Mega Kangaskhan ex + Crustle | 6,9% | 44,5% |
| 6 | Teal Mask Ogerpon ex | 5,0% | 46,3% |
| 7 | **Mega Lucario ex + Hariyama** | **4,0%** | 54,6% |
| 8 | Dipplin/Seaking + Grookey (Festival Lead) | 3,5% | 55,1% |
| 9 | Hydrapple ex + Ogerpon | 2,5% | 56,1% |
| 10 | Slowking + Mega Kangaskhan ex + Latias ex | 1,8% | **63,3%** |
| 11 | Cynthia's Garchomp ex | 1,6% | 50,3% |

La baraja de ejemplo del motor (Mega Abomasnow/Kyogre) aparece **0 veces en 18.674**. Sigo
cubriendo los cuatro que pedía el encargo, pero añado los que de verdad mandan.

---

## 1. Matriz de emparejamientos MEDIDA (nuestra ladder, no el papel)

Reagrupado desde `data/replays/idx/idx_08{08,09}.json` con el criterio del censo
(solape de multiconjunto ≥ 0,62). Celda = % que gana la FILA a la COLUMNA / n. `-` = n < 15.
Script: `scratchpad/matriz_fina.py`.

|  fila gana a → | Grimmsn. | Alakazam | Lopunny | Dragapult | Kanga/Crustle | Ogerpon | **Lucario** | Dipplin | Hydrapple | Slowking | Garchomp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Grimmsnarl | 50/1834 | **57**/1058 | 45/768 | 36/477 | 50/421 | **20**/281 | 50/212 | 39/224 | 31/131 | 23/83 | 53/98 |
| Alakazam | 43/1058 | 50/652 | **57**/425 | 37/268 | **67**/243 | **63**/170 | 52/120 | 43/124 | **67**/85 | 38/45 | 50/44 |
| Lopunny+Froslass | 55/768 | 43/425 | 50/280 | 43/182 | **73**/172 | **85**/131 | **14**/91 | 54/84 | 35/68 | 33/39 | **10**/42 |
| Dragapult | **64**/477 | **63**/268 | 57/182 | 50/128 | 47/116 | **75**/85 | 47/58 | **76**/38 | 52/46 | 33/21 | 52/25 |
| Kanga+Crustle | 50/421 | **33**/243 | **27**/172 | 53/116 | 50/56 | **69**/54 | **29**/42 | 54/54 | 56/25 | 55/20 | 48/25 |
| Ogerpon | **80**/281 | 37/170 | **15**/131 | **25**/85 | 31/54 | 50/54 | 24/34 | 35/34 | 17/23 | – | – |
| **Lucario** | 50/212 | 48/120 | **86**/91 | 53/58 | **71**/42 | **76**/34 | 50/18 | 45/22 | 59/22 | **23**/56 | – |
| Dipplin | **61**/224 | 57/124 | 46/84 | 24/38 | 46/54 | **65**/34 | 55/22 | 50/20 | – | – | – |
| Hydrapple | **69**/131 | 33/85 | **65**/68 | 48/46 | 44/25 | **83**/23 | 41/22 | – | – | **68**/19 | – |
| Slowking | **77**/83 | **62**/45 | **67**/39 | **67**/21 | 45/20 | – | **77**/56 | – | 32/19 | – | – |
| Garchomp | 47/98 | 50/44 | **90**/42 | 48/25 | 52/25 | – | – | – | – | – | – |

Lecturas que importan, con el PORQUÉ:

- **Lucario aplasta a Lopunny/Froslass (86%, n=91)**: Mega Lopunny ex 849 es {C} con
  **debilidad {F}**. Aura Jab 130 ×2 = 260; con Premium Power Pro 1141 (+30 antes de
  debilidad) = 320. Mega Brave 270 → 600. Nuestro tipo es el contador natural del 12,8% del
  campo. **CORRECCIÓN pase 2:** Mega Lopunny ex tiene **330 PS**, así que 320 **no** mata;
  hace falta sumar Black Belt's Training 1211 (+40) → (130+30+40)×2 = 400, o Maximum Belt
  1158 (+50) → (130+50)×2 = 360. Ver §7.3.
- **Lucario aplasta a Kanga/Crustle (71%) y a Ogerpon (76%)**: Mega Kangaskhan ex 756 es {C}
  débil a {F}; Ogerpon 96 tiene 210 PS y se muere de un Mega Brave.
- **Lucario pierde a Slowking/Kangaskhan/Latias (23%, n=56)** — su peor emparejamiento de
  largo. Motivo mecánico, ver §3.8: **Annihilape 224, `Destined Fight [{F}●]: Both Active
  Pokémon are Knocked Out`**, lanzado desde Slowking 163 (`Seek Inspiration`) con el mazo
  apilado por Ciphermaniac's Codebreaking 1188. Cambian un single-prize de 120 PS por
  nuestros 3 premios.
- **Grimmsnarl pierde a Ogerpon 20/281**: Marnie's Grimmsnarl ex 648 es {D} con debilidad
  **{G}**. Es el hueco del mazo más jugado del campo (31,2%).
- **Dragapult es el mejor mazo del campo (58,7%)** y gana a los dos primeros (64% y 63%).
- **Alakazam se hunde contra Grimmsnarl (43%) y Dragapult (37%)** y gana a todo lo lento
  (Crustle 67%, Ogerpon 63%, Hydrapple 67%).

Contraste con el papel (mismos vectores, distinto campo): en Limitless el Mega Lucario va
0-14 (0%) contra Gardevoir y 4-9 (31%) contra Alakazam-Dudunsparce, y Alakazam gana a
«Lucario Hariyama» 42-19 (68%) —
[Limitless matchups Mega Lucario](https://play.limitlesstcg.com/decks/mega-lucario-ex/matchups?format=standard&rotation=2025&set=PFL),
[Limitless matchups Alakazam Dudunsparce](https://play.limitlesstcg.com/decks/alakazam-dudunsparce/matchups?format=standard&rotation=2025&set=MEG).
En nuestra ladder Alakazam solo gana a Lucario 52/120: nuestro campo NO tiene Gardevoir, y
Alakazam de aquí no lleva las piezas que rompen a Lucario en el papel.

---

## 2. Primero o segundo: el dato duro

El jugador 0 del env **siempre** elige (select `(9,41)`, `motor-mecanica.md §1`). Medido sobre
9.331 partidas decididas: **el jugador que elige gana el 54,5%** (5.087–4.244). Desglose por
arquetipo (WR siendo el que elige vs. siendo el otro):

| arquetipo | WR como p0 (elige) | WR como p1 | delta |
|---|---|---|---|
| Mega Lucario | 60,9% (n=348) | 49,0% (n=390) | **+11,9** |
| Grimmsnarl | 51,8% (n=2905) | 41,4% (n=2915) | +10,4 |
| Dragapult | 63,7% (n=782) | 53,4% (n=741) | +10,2 |
| Garchomp | 54,5% (n=154) | 45,7% (n=140) | +8,8 |
| Alakazam | 54,2% (n=1667) | 45,5% (n=1735) | +8,7 |
| Kanga/Crustle | 47,2% (n=678) | 40,9% (n=663) | +6,3 |

**Ninguna mejora algorítmica que hemos probado vale +11,9 puntos.** El select (9,41) es la
decisión más barata y más rentable del agente y hoy la resolvemos sin criterio por arquetipo.

Regla del papel (pendiente de un test de una línea en el motor): **el que va primero no puede
atacar en su primer turno**. El pool lo refleja: Rare Candy 1079 dice «You can't use this card
during your first turn» y Carmine 1192 «If you go first, you may use this card during your
first turn». Consecuencia estándar: mazos de evolución de fase 2 (Alakazam, Grimmsnarl,
Garchomp, Dragapult) quieren **ir primero** (un turno extra de montaje sin recibir daño);
mazos de básicos/fase 1 que atacan ya (Lucario, Lopunny, Kangaskhan, Ogerpon) quieren
**ir segundo** para pegar el primer golpe. La guía de Dark Fox lo dice explícito para Lucario
contra Dragapult: «if you go second, get a good board setup, evolve into your Mega
Lucarios… you have a great roadmap to winning» —
[Dark Fox TCG](https://www.darkfoxtcg.com/blogs/news/mega-lucario-deck-matchup-guide).

---

## 3. Arquetipo por arquetipo

### 3.1 Mega Lucario ex — 4,0% del campo, WR 54,6% (nuestro arquetipo)

**Piezas (todas existen en el pool):** Riolu **677** (80 PS, `Accelerating Stab [{F}] 30`,
no repetible), Mega Lucario ex **678** (Stage 1 desde Riolu, **340 PS**, debilidad {P},
`Aura Jab [{F}] 130 :: Attach up to 3 Basic {F} Energy cards from your discard pile to your
Benched Pokémon`, `Mega Brave [{F}{F}] 270`, no repetible), Makuhita **673** / Hariyama **674**
(`[Ability] Heave-Ho Catcher`: al evolucionar, **gust gratis** de un banquillo rival;
`Wild Press [{F}{F}{F}] 210` con 70 de retroceso), Lunatone **675** (`Lunar Cycle`: descarta
un {F} básico de la mano → roba 3, requiere Solrock en juego) / Solrock **676**
(`Cosmic Beam [{F}] 70`, no aplica debilidad ni resistencia, requiere Lunatone en banca),
Fighting Gong **1142**, Premium Power Pro **1141** (+30 de {F} al activo, **Item**),
Poké Pad **1152**, Judge **1213**, Boss's Orders **1182**, Hero's Cape **1159** (ACE SPEC,
+100 PS → Lucario de 440), Wally's Compassion **1229** (cura TODO a un Mega ex y **te devuelve
sus energías a la mano**), Gravity Mountain **1252** (−30 PS a cada Stage 2 en juego).

**El concepto real del mazo no es «pegar 270».** Pokémon.com lo llama *single-Prize
manipulation*: «attack with single-Prize Pokémon throughout the game, preventing opponents
from winning by knocking out two Mega Lucario ex» —
[Pokemon.com, Building a Mega Lucario ex Deck](https://www.pokemon.com/uk/strategy/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck).
Dark Fox va más lejos y solo juega **2** Mega Lucario ex: «giving up 3 Prizes when knocked out
SUCKS» — [Dark Fox TCG](https://www.darkfoxtcg.com/blogs/news/mega-lucario-deck-matchup-guide).
El motor implementa la regla: `prize_count()` = **3 megaEx / 2 ex / 1**
(`research/notas/kernels-referencia.md` §kernels).

**Motor:** Aura Jab. Es a la vez ataque barato y aceleración — pero **a la BANCA, nunca a sí
mismo**. La rutina correcta es «Aura Jab con el Lucario activo → las 3 energías del descarte
van al Lucario de banca», de modo que cuando cae el activo entra otro ya cargado.
Flipside lo llama *Aura Farm*: «staying in the active spot, soaking up hits, and replenishing
your board» —
[Flipside Gaming](https://flipsidegaming.com/blogs/pokemon-blog/searching-standard-mega-lucario-ex).
El segundo motor es el par Lunatone/Solrock (robo + atacante de 1 premio).

**Línea ideal T1-T3 (yendo segundo):**
- T1: Riolu al activo; Poké Pad/Fighting Gong para asegurar Riolu 2 + {F}; Solrock y Lunatone
  a banca; 1 {F} a Riolu; `Accelerating Stab` 30 si no hay nada mejor.
- T2: evolucionar a Mega Lucario ex; **Aura Jab 130** y colocar las 3 energías del descarte en
  el Lucario/Riolu de banca. Con Premium Power Pro (Item) sube a 160.
- T3: `Mega Brave` 270. **Combo de OHKO universal**: Mega Brave + Premium Power Pro **1141**
  (Item, +30) + Black Belt's Training **1211** (Supporter, +40 al activo **ex**) = **340**.
  Ítem y partidario en el mismo turno, sin conflicto. 340 mata de un golpe a Grimmsnarl ex
  (320), Dragapult ex (320), Garchomp ex (330), Lopunny ex (330) y Kangaskhan ex (300).
  Al turno siguiente Mega Brave está bloqueado → toca Aura Jab (que además recarga).
- Cuando el rival juega single-prizes de ≤110 PS, **atacar con Solrock** (70, ignora debilidad
  y resistencia) en vez de exponer al Lucario: así el intercambio de premios es 1 por 1.

**Puntos débiles conocidos:**
1. **3 premios por KO.** Dos Lucarios muertos = partida perdida. Es la razón de las listas de
   2 copias y del paquete de single-prizes.
2. **Debilidad {P}** — en el papel es la muerte (0-14 contra Gardevoir). En nuestra ladder no
   hay Gardevoir; el único {P} relevante es Alakazam, y su `Powerful Hand` **coloca contadores
   de daño**, que no aplican debilidad. Por eso aquí el 48% y no el 0%.
3. **Mega Brave no se puede repetir** → un turno de cada dos pegas 130-160, no 270. Un rival
   que cura o que retira gana ese turno.
4. Contadores de daño y efectos de ataque (Phantom Dive, Powerful Hand, Adrena-Brain) esquivan
   PS y muros.

**Cómo se juega CONTRA Mega Lucario:**
- **Matar primero al Lucario de banca cargado**, no al activo: Aura Jab pone las energías
  ahí. Boss's Orders 1182 sobre el Lucario de banca deshace dos turnos de aceleración.
- **Negar Premium Power Pro/Fighting Gong** no se puede (no hay descarte de mano dirigido);
  lo que sí se niega es el gusting: si su Hariyama te saca la banca, tu pieza clave no debe
  estar en banca sin retirada.
- **Ir primero** contra él si tu mazo es de Fase 2 (necesitas el turno de montaje y él tarda
  hasta T2-T3 en llegar a 270). **Ir segundo** si eres agresivo y le puedes pegar a Riolu
  (80 PS) antes de que evolucione: matar el Riolu es matar el mazo.
- Single-prizes que peguen ≥170: le obligas a gastar 3 premios por cada 1 tuyo.

---

### 3.2 Alakazam — 18,2% del campo, WR 49,7%

**Piezas:** Abra **741** (50 PS) → Kadabra **742** (80 PS, `[Ability] Psychic Draw`: al
evolucionar, **roba 2**) → Alakazam **743** (140 PS, Stage 2, **single-prize**,
`[Ability] Psychic Draw`: al evolucionar, **roba 3**; `Powerful Hand [{P}]:: Place 2 damage
counters on your opponent's Active Pokémon for each card in your hand`). Motor de mano:
Dudunsparce **66** (`Run Away Draw`: roba 3 y se baraja a sí mismo de vuelta), Dunsparce **305**,
Hilda **1225** (busca 1 evolución + 1 energía), Dawn **1231** (busca **básico + Stage 1 +
Stage 2** de golpe), Rare Candy **1079**, Buddy-Buddy Poffin **1086**, Poké Pad **1152**,
Telepath Psychic Energy **19** (al pegarla, busca 2 básicos {P} a banca),
Enriching Energy **13** (ACE SPEC: al pegarla, **roba 4**), Xerosic's Machinations **1197**
(el rival descarta hasta quedarse en 3), Enhanced Hammer **1081**, Night Stretcher **1097**,
Lana's Aid **1184**, Sacred Ash **1129**, Nighttime Mine **1266**.

**El concepto:** 20 de daño por carta en la mano, por **una** energía, desde un Pokémon de
**1 premio**. 10 cartas = 200. 16 cartas = 320 (lo que hace falta para matar un Dragapult ex) —
[Cardsrealm](https://pokemon.cardsrealm.com/en-us/articles/pokemon-tcg-standard-deck-tech-alakazam-dudunsparce).
Ganó regional en manos de Cerys Jones (Indianápolis) —
[Deltia's Gaming](https://deltiasgaming.com/pokemon-tcg-best-alakazam-deck-guide-mega-evolution/).

**Línea ideal T1-T3 (yendo primero):**
- T1: Abra al activo, más Abras y Dunsparce a banca con Buddy-Buddy Poffin; Dawn 1231 para
  tener la línea entera en la mano. **Guardar cartas, no gastarlas.**
- T2: Kadabra (roba 2) → Alakazam (roba 3), o Rare Candy directo a Alakazam (roba 3) si el
  Abra ya estaba en juego el turno anterior. Pegar Telepath Psychic Energy 19 (busca 2 básicos
  a banca **y** engorda la mano por el efecto). `Powerful Hand` con 8-10 cartas = 160-200.
- T3: Dudunsparce `Run Away Draw` + Enriching Energy 13 (+4) para subir a 12-14 cartas =
  240-280, y `Powerful Hand` otra vez. El daño no se «gasta»: es todo el turno lo mismo.

**Puntos débiles:**
1. **Vive de la mano.** Judge **1213** (ambos barajan y roban **4**) lo baja a 80 de daño.
   Hand Trimmer **1087** (ambos descartan hasta 5, es **Item** → se juega junto a un
   partidario) lo baja a 100. Xerosic's Machinations **1197** (rival a 3) lo baja a 60.
   Es la carta técnica que decide el emparejamiento.
2. **La línea es de cristal:** Abra 50 PS, Kadabra 80 PS. Cualquier daño de banca los mata.
   Por eso Grimmsnarl+Froslass le gana 57/1058: Froslass **104** (`Freezing Shroud`: 1
   contador a **cada** Pokémon con habilidad en el chequeo, ambos lados) más Munkidori **112**
   (`Adrena-Brain`: mueve hasta 3 contadores propios al rival) barren los Abras de banca sin
   atacar. Y Grimmsnarl 648 `Shadow Bullet` mete 30 a un banquillo cada turno.
3. **Se ahoga contra 320 PS.** Contra Dragapult ex necesita 16 cartas en mano: 37% en nuestra
   ladder, 28% en el papel.
4. Gravity Mountain **1252** (−30 PS a cada Stage 2) lo deja en **110 PS**: entra en rango de
   casi cualquier ataque medio.

**Cómo se juega CONTRA Alakazam:**
- **Matar la banca, no el activo** — pero **arrastrándola al activo**, no disparándole.
  **CORRECCIÓN pase 2:** la lista de campo `c2-alakazam.csv` lleva **Shaymin 343**
  (`[Ability] Flower Curtain :: Prevent all damage done to your Benched Pokémon that don't
  have a Rule Box by attacks from your opponent's Pokémon`). Con Shaymin en mesa, **todo
  daño de ataque a sus Abra/Kadabra/Dunsparce de banca es 0**: el plan «snipe de banca» no
  funciona. Flower Curtain **no** protege el Activo → Boss's Orders 1182 sigue siendo la
  respuesta, y el propio Shaymin (80 PS, sin Rule Box) es un objetivo de Boss's Orders de
  primer orden. Si le quitas la segunda línea, no hay Alakazam de repuesto.
- **La carta a negar es su propia mano**: Judge 1213 el turno ANTES de que ataque. Nuestro
  pool NO tiene Iono ni Marnie; los sustitutos son Judge 1213, Hand Trimmer 1087 (Item) y
  Xerosic's Machinations 1197.
- **La carta que lo blanquea es Rock Fighting Energy 20**: `provides {F} Energy. Prevent all
  effects of attacks used by your opponent's Pokémon done to the {F} Pokémon this card is
  attached to. (Damage is not an effect.)` — `Powerful Hand` **coloca contadores**, es decir
  es un *efecto*, no daño. Pokemon.com lo dice con todas las letras al listar las debilidades
  del mazo de Lucario: «Alakazam decks using Powerful Hand (mitigated by Rocky Fighting
  Energy)» —
  [Pokemon.com](https://www.pokemon.com/uk/strategy/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck).
  Está en nuestro pool (**card_id 20**) y da {F}, o sea que en un mazo mono-{F} no es carta
  muerta. **Ojo:** es energía especial, así que `Aura Jab` (que solo mueve *Basic {F}*) no la
  recicla; se pega a mano.
- **Ir primero** contra él tiene sentido si tu mazo es más rápido: su daño real no llega hasta
  T2-T3 y sus básicos mueren a un soplo.

---

### 3.3 Cynthia's Garchomp ex — 1,6% del campo, WR 50,3%

**Piezas:** Cynthia's Gible **379** → Gabite **380** (`[Ability] Champion's Call`: 1/turno
busca **cualquier Cynthia's Pokémon**) → Cynthia's Garchomp ex **381** (Stage 2, **330 PS**,
**retirada 0**, debilidad {G}; `Corkscrew Dive [{F}] 100 :: You may draw cards until you have
6 cards in your hand`; `Draconic Buster [{F}{F}] 260 :: Discard all Energy from this Pokémon`),
Cynthia's Roselia **341** → Roserade **342** (`[Ability] Cheer On to Glory`: **+30** a los
ataques de Cynthia's al activo, **acumulable**), Cynthia's Spiritomb **387** (`Raging Curse`
10× por contador en la banca Cynthia's, ignora debilidad), Cynthia's Power Weight **1173**
(tool, **+70 PS** → Garchomp de **400**), Rock Fighting Energy **20**, Fighting Gong **1142**,
Unfair Stamp **1080** (ACE SPEC), Buddy-Buddy Poffin **1086**, Poké Pad **1152**.

**El concepto:** un Stage 2 de 330-400 PS con **retirada 0** que pega 100 barato (y roba) o
260 caro, y que se busca a sí mismo con Gabite. Roserade lo sube: `Draconic Buster` 260+30 =
**290**, y con dos Roserade **320** —
[Deltia's Gaming](https://deltiasgaming.com/pokemon-tcg-best-cynthias-garchomp-ex-deck-guide-destined-rivals/).

**Línea ideal T1-T3 (yendo primero):**
- T1: Gible al activo, Roselia y más Gibles a banca (Buddy-Buddy Poffin coge los de ≤70 PS);
  1 {F} al Gible; `Rock Hurl` 20 si toca.
- T2: Gabite → `Champion's Call` busca Garchomp ex (o Roserade). Evolucionar Roselia a
  Roserade. Segunda energía.
- T3: Garchomp ex + Cynthia's Power Weight (400 PS) + `Draconic Buster` 260+30 = **290**.
  Como descarta todas sus energías, el turno siguiente usa `Corkscrew Dive` (100+30=130, y
  **roba hasta 6**) mientras recarga. **Retirada 0** significa que puede rotar a un Garchomp
  fresco gratis cada turno: ese es el truco que un humano usa y una heurística no ve.

**Puntos débiles:**
1. `Draconic Buster` **se autodesarma**: tras cada 290 hay un turno flojo. Es el turno para
   matarlo.
2. **Debilidad {G}** con 330 PS: Ogerpon/Hydrapple/Dipplin lo parten. Contra Lopunny gana
   90/42 porque Lopunny es débil a {F}.
3. Es Stage 2 → **Gravity Mountain 1252** le quita 30 (330→300) y mata sus Gabite/Roserade.
4. Depende de Gabite para encontrar todo: matar el Gabite de banca lo deja ciego.

**Cómo se jugaría CONTRA (con nuestro Lucario):** no tenemos datos de ese emparejamiento en la
ladder (n<15) y el papel da 62,5% a Lucario (5-3,
[Limitless MEG](https://play.limitlesstcg.com/decks/mega-lucario-ex/matchups?format=standard&rotation=2025&set=MEG)).
Objetivo prioritario: **Gabite/Roserade de banca** con Boss's Orders, no el Garchomp de 400 PS.
Si hay que matar al Garchomp, hace falta la línea de 340 (Mega Brave + PPP + Black Belt's
Training) porque con Power Weight tiene 400. Ir **segundo**: es un mazo de montaje lento.

---

### 3.4 Aggro de agua tipo-ejemplo (Mega Abomasnow ex + Kyogre) — 0% del campo

**Piezas:** Kyogre **721** (150 PS, `Riptide [{W}] 20×` por cada {W} básica en el descarte, y
luego **las baraja de vuelta**), Snover **722** (90 PS) → Mega Abomasnow ex **723**
(**350 PS**, debilidad **{M}**, retirada **4**; `Hammer-lanche [{W}{W}] 100× :: Discard the top
6 cards of your deck, and this attack does 100 damage for each Basic {W} Energy card that you
discarded`; `Frost Barrier [{W}{W}{W}] 200`, −30 recibido el turno siguiente),
Powerglass **1163**, Surfing Beach **1262**, Secret Box **1092**, Mega Signal **1145**.

**El concepto:** tragaperras. La lista de papel corre **29 energías de agua** «to mitigate some
of that randomness» — [Flipside Gaming](https://flipsidegaming.com/blogs/pokemon-blog/searching-standard-mega-abomasnow-ex);
la del motor corre 33. Con 33/60, E[daño] ≈ 330 pero la varianza es enorme (0 a 600).

**Línea T1-T3:** Snover activo → energía → Mega Abomasnow ex T2 → `Hammer-lanche` desde T2.
No hay más plan; Kyogre recicla las {W} del descarte al mazo para que Hammer-lanche vuelva a
tener con qué pegar.

**Puntos débiles:** (a) es **0/18.674** en nuestra ladder, o sea que **no es un rival, es un
sparring**, y medir contra él no dice nada (el ranking de 15 listas contra esta baraja medía
un rival inexistente); (b) retirada 4 y sin Switch suficientes = se queda atrapado;
(c) debilidad {M}; (d) 3 premios; (e) el propio Hammer-lanche **se descarta el mazo**: es una
condición de deck-out autoinfligida (`reason 2` del motor); (f) la baraja de ejemplo tuvo
**375 mulligans en 50 partidas** (`motor-mecanica.md §3`) — cada mulligan **revela su mano
entera** y regala robo al rival.

**Cómo se juega CONTRA:** no hay que hacer nada especial. Si aparece, mata a Snover (90 PS)
antes de la evolución y cuenta sus turnos: se deck-outea solo.

**Piezas del papel que NO están en nuestro pool** y cambian el plan copiado: `Artazon`,
`Nest Ball`, `Technical Machine: Turbo Energize`, `Professor's Research`, `Super Rod`,
`Earthen Vessel` — ninguna existe (verificado por nombre en `cards_clean.csv`). Las listas de
papel que las usen hay que reconstruirlas con Poké Pad 1152 / Buddy-Buddy Poffin 1086 /
Night Stretcher 1097 / Cheren 1224 / Urbain 1236.

---

### 3.5 Marnie's Grimmsnarl ex — **31,2% del campo** (el rival de verdad)

**Piezas:** Marnie's Impidimp **646** → Morgrem **647** → **Marnie's Grimmsnarl ex 648**
(Stage 2, 320 PS, {D}, debilidad **{G}**; `[Ability] Punk Up`: al evolucionar desde la mano,
**busca hasta 5 energías {D} básicas del mazo y las reparte entre tus Marnie's**;
`Shadow Bullet [{D}{D}] 180 :: This attack also does 30 damage to 1 of your opponent's Benched
Pokémon`), Munkidori **112** (`Adrena-Brain`: mueve hasta 3 contadores de un Pokémon tuyo a uno
del rival), Snorunt **860** → Froslass **104** (`Freezing Shroud`: 1 contador a **cada** Pokémon
con habilidad de ambos lados en el chequeo), Spikemuth Gym **1259** (busca un Marnie's cada
turno, **×4** en la lista líder), Rare Candy **1079**, TR Petrel **1219** (×4),
Lillie's Determination **1227** (×4), Unfair Stamp **1080**.

**El concepto:** `Punk Up` resuelve toda la energía del mazo de golpe (5 de una vez), así que
las adjunciones manuales van a Munkidori; luego Froslass siembra contadores en toda la mesa y
Munkidori los reubica para rematar. «Use Munkidori to move damage counters from your side of
the board to your opponent's, while Marnie's Grimmsnarl ex deals consistent damage to the
Active Pokémon while also dropping 30 damage on a Benched Pokémon, setting you up to take
multiple Prize cards each turn» —
[Pokemon.com](https://www.pokemon.com/us/strategy/pokemon-tcg-strategy-energize-your-deck-with-marnies-grimmsnarl-ex).

**Línea T1-T3 (yendo primero):** T1 Impidimp activo + Spikemuth Gym (busca Marnie's) + banca
de Impidimps y Munkidori; T2 Morgrem o Rare Candy; T3 **Grimmsnarl ex + Punk Up (5 energías)
+ Shadow Bullet 180 + 30 a banca**. Desde T3 pega 180/30 todos los turnos sin volver a pegar
energía a mano.

**Puntos débiles:** debilidad **{G}** (pierde 20/281 contra Ogerpon); Froslass y Munkidori son
de banca y de 90-110 PS (Boss's Orders los mata y desmonta el motor de contadores); es Stage 2
→ **Gravity Mountain 1252** lo baja a 290 y mata a Froslass/Morgrem.

**Cómo se juega CONTRA (siendo Lucario, 50/212 hoy):** matar **Froslass** primero — sin ella
no hay contadores que mover; después Munkidori. Grimmsnarl 320 PS entra exactamente en la
línea de **340** (Mega Brave + Premium Power Pro + Black Belt's Training). Ir **segundo**: él
necesita hasta T3 para arrancar; si pegas primero le obligas a evolucionar bajo presión.
Ojo: `Shadow Bullet` hace **daño** (no contadores) a la banca → Rock Fighting Energy **no**
lo bloquea.

---

### 3.6 Mega Lopunny ex + Mega Froslass ex — 12,8% del campo

Mega Lopunny ex **849** (Stage 1, 330 PS, {C}, **debilidad {F}**; `Gale Thrust [●] 60`, **+170
si se movió de banca a activo este turno** = 230 por UNA energía incolora;
`Spiky Hopper [●●] 160`, ignora efectos del activo rival) y Mega Froslass ex **861**
(310 PS, `Resentful Refrain [{W}] 50×` **por carta en la mano del RIVAL**). Apoyo: Dunsparce
**305** / Dudunsparce **66**, Air Balloon **1174**, Mist Energy **11**, Battle Cage **1264**
(bloquea contadores a la banca), Hand Trimmer **1087**, Wally's Compassion **1229**.

Plan: rotar desde banca cada turno para que `Gale Thrust` valga 230, y castigar manos grandes
con Froslass. **Es nuestro mejor emparejamiento (86%)** porque Lopunny es débil a {F}: Aura Jab
+ Premium Power Pro = (130+30)×2 = **320**, que se queda a **10 PS** de sus 330 — **hay que
añadir Black Belt's Training 1211**, (130+30+40)×2 = **400**, o Maximum Belt 1158,
(130+50)×2 = **360**, para que el OHKO con el ataque barato exista de verdad.
Ojo también con Mega Froslass ex 861: `Resentful Refrain [{W}] 50×` es **50 por cada carta de
NUESTRA mano** (mano de 7 = 350, mata al Lucario de 340). Contra ese mazo hay que **vaciar la
mano antes de pasar turno**, no robar de más. Contra ellos: ir **segundo** y matar el Lopunny activo antes de
que rote. Nota táctica: Mega Froslass ex castiga tener la mano llena; contra ella **no** hay
que robar de más.

### 3.7 Dragapult ex — 8,2%, **WR 58,7% (el mejor del campo)**

Dreepy **119** → Drakloak **120** (`Recon Directive`: mira 2, coge 1) → **Dragapult ex 121**
(Stage 2, **320 PS**, tipo dragón **sin debilidad**; `Phantom Dive [{R}{P}] 200 :: Put 6 damage
counters on your opponent's Benched Pokémon in any way you like`). Apoyo: Munkidori **112**,
Budew **235** (`Itchy Pollen`: el rival **no puede jugar Items** el turno siguiente — sin coste
de energía), Crushing Hammer **1120** ×4, Jamming Tower **1246** (anula todas las tools),
Judge **1213**, Unfair Stamp **1080**, Crispin **1198**.

Plan: 200 al activo **más 60 repartidos por la banca** cada turno; con Munkidori reubica esos
contadores. Sin debilidad y con 320 PS es dificilísimo de matar de un golpe. Punto débil:
línea de Fase 2 frágil (Dreepy 70 PS) y necesita dos tipos de energía.

**Contra Dragapult:** Budew le apaga los Items al rival — nuestro plan de daño depende de
**Premium Power Pro, que es un Item**; con Budew activo perdemos los +30 y bajamos de 340 a
300, que **no** mata sus 320. Es exactamente la clase de detalle que decide el emparejamiento.
Jamming Tower anula Hero's Cape. `Phantom Dive` pone **contadores** → Rock Fighting Energy 20
**sí** los bloquea en el {F} que la lleve.

### 3.8 Slowking + Mega Kangaskhan ex + Latias ex — 1,8%, **WR 63,3%; nos gana 77/56**

El mazo con mejor winrate del campo y **nuestro peor emparejamiento (ganamos 23%)**. Piezas:
Slowpoke **162** → Slowking **163** (`Seek Inspiration [{P}●] :: Discard the top card of your
deck, and if that card is a Pokémon that doesn't have a Rule Box, choose 1 of its attacks and
use it as this attack`), **Ciphermaniac's Codebreaking 1188** ×4 (`Search your deck for 2
cards… then put those cards on top of it in any order` → **apila la cima del mazo**),
**Annihilape 224** (`Destined Fight [{F}●] :: Both Active Pokémon are Knocked Out`),
Conkeldurr **115** (`Gutsy Swing [{F}●●●] 250`, ignora el coste si está bajo condición
especial), Mega Kangaskhan ex **756** (300 PS, `Run Errand`: roba 2/turno en activo),
Latias ex **184** (`Skyliner`: **todos tus básicos con retirada 0**), Kyurem **144**,
Academy at Night **1248** ×4, Wondrous Patch **1146**, Prime Catcher **1088**.

**Por qué nos destroza:** Codebreaking pone Annihilape en la cima; Slowking (120 PS,
**1 premio**) lo descarta y usa `Destined Fight` → **muere nuestro Mega Lucario ex de 340 PS
(3 premios) a cambio de un single-prize suyo**. Dos ciclos y perdemos. Ni los PS ni el daño
importan. Es la refutación práctica de «un solo atacante enorme».

**Cómo se juega contra ellos:** matar **Slowpoke/Slowking** (80/120 PS) antes de que llegue el
ciclo, y **no dejar al Mega Lucario en el activo** cuando puedan usar Destined Fight: rotar a
Solrock/Riolu para que el intercambio sea 1 por 1. Latias ex 184 de banca es un objetivo de
Boss's Orders excelente (le quita la retirada 0 a toda su mesa).

### 3.9 Dipplin / Festival Lead — 3,5%, WR 55,1%

Dipplin **93** (`[Ability] Festival Lead`: **con Festival Grounds 1245 en juego, ataca dos
veces**, y si el primer ataque hace KO ataca otra vez tras la nueva elección de activo;
`Do the Wave [{G}] 20×` por cada Pokémon en tu banca = 100 con banca llena), Thwackey **90**
(`Boom Boom Groove`: busca cualquier carta si el activo tiene Festival Lead),
Festival Grounds **1245** ×4, Brave Bangle **1175** (+30 contra ex si el portador no tiene
Rule Box), Black Belt's Training **1211**.

Todo son single-prizes de ≤100 PS que pegan 2×100+ contra nuestros 3 premios. Punto débil:
**depende por completo de Festival Grounds** — un estadio propio cualquiera lo apaga.
**Nuestra lista no lleva ningún estadio, así que no podemos apagarlo.**

---

## 4. Nuestra lista contra las del campo

`research/decks/propios/mega-lucario.csv` vs `research/decks/campo/c7-lucario-campo.csv`
(la lista líder real del arquetipo, 738 partidas, WR 54,6%). **Solape de multiconjunto: 0,60**
— por debajo del umbral 0,62 del censo, es decir, **nuestra lista no agruparía con las del
campo: es otro mazo.**

| id | carta | NUESTRA | campo c7 | sample |
|---|---|---|---|---|
| 447 | **Regirock ex** | **4** | 0 | 0 |
| 673/674 | **Makuhita / Hariyama** | **0/0** | 2/2 | 2/2 |
| 675/676 | **Lunatone / Solrock** | **0/0** | 2/3 | 2/3 |
| 677 | Riolu | 4 | 3 | 3 |
| 1152 | **Poké Pad** | **0** | 4 | 4 |
| 1213 | **Judge** | **0** | 4 | 0 |
| 1141 | Premium Power Pro | 2 | **4** | **4** |
| 1227 | Lillie's Determination | 2 | 4 | 4 |
| 1224/1236 | Cheren / Urbain | 4/4 | 0/0 | 0/0 |
| 1238 | Tarragon | 2 | 0 | 0 |
| 1097 | Night Stretcher | 2 | 0 | 0 |
| 1125 | Master Ball (ACE SPEC) | 1 | 0 | 0 |
| 1159 | Hero's Cape (ACE SPEC) | 0 | 1 | 1 |
| 1229 | Wally's Compassion | 0 | 2 | 0 |
| 1252 | Gravity Mountain | 0 | 0 | 2 |
| 1102 / 1192 | Dusk Ball / Carmine | 0/0 | 0/0 | 4/4 |
| 6 | Basic {F} Energy | **19** | 13 | 13 |

Diferencias que importan, por orden de impacto:

1. **Regalamos premios en todas las cartas.** 4 Mega Lucario ex (3 premios) + 4 Regirock ex
   (2 premios) = **el rival gana con 2 KOs**. El campo y las dos guías de papel construyen
   exactamente al revés: 2-3 Mega Lucario y un paquete de single-prizes (Solrock 676 pega 70
   por 1 energía; Hariyama 674 pega 210 por 3). Es el punto 1 del concepto de baraja que
   puntúa el 20% de Deck Score, y hoy no lo tenemos articulado.
2. **No llevamos gusting gratis.** Hariyama 674 (`Heave-Ho Catcher`) saca un banquillo rival
   **al evolucionar**, sin gastar el partidario del turno. Nosotros gastamos Boss's Orders
   (2 copias) y con eso perdemos el robo de ese turno.
3. **Nos falta la mitad del daño.** 2 Premium Power Pro en vez de 4, y **cero** Black Belt's
   Training 1211. Sin ellos no existe la línea de 340 y no matamos de un golpe a Grimmsnarl
   (320), Dragapult (320) ni Garchomp (330) — el 43% del campo.
4. **Cero disrupción.** El campo lleva **4 Judge 1213**; nosotros ninguno. Judge es la carta
   que convierte el 48% contra Alakazam (18,2% del campo) en un emparejamiento ganado, y de
   paso frena a Mega Froslass ex.
5. **Cero estadios.** 13 de las 14 listas de campo llevan estadio (2-4 copias). Sin estadio
   propio **no podemos retirar el suyo**: Spikemuth Gym (Grimmsnarl), Festival Grounds
   (Dipplin), Jamming Tower (Dragapult), Battle Cage y Academy at Night se quedan puestos toda
   la partida. Gravity Mountain 1252 sería además ofensivo: −30 PS a **todo Stage 2**
   (Grimmsnarl 320→290, Dragapult 320→290, Garchomp 330→300, Alakazam 140→110) y **Mega
   Lucario ex es Stage 1: inmune**.
6. **Motor de robo caro.** 4 Cheren + 4 Urbain (8 partidarios de robo simple) donde el campo
   lleva 4 Poké Pad 1152 (**Item**: busca cualquier Pokémon sin Rule Box → Riolu, Solrock,
   Makuhita) + 4 Lillie's Determination. Poké Pad es búsqueda gratis que no gasta el
   partidario del turno. **No existe Iono ni Professor's Research en el pool**, así que el
   robo de la casa es Cheren/Urbain/Lillie's — pero la *búsqueda* debe ser por Item.
7. **19 energías es demasiado** para un mazo cuyo ataque barato recicla 3 del descarte cada
   turno. El campo juega 13. Esas 6 cartas son el hueco para Judge/estadio/Power Pro.
8. **ACE SPEC.** Master Ball 1125 (buscar un Pokémon) contra Hero's Cape 1159 (+100 PS →
   Lucario de 440, fuera del rango de casi todo) o **Legacy Energy 12**, que da cualquier tipo
   y hace que **el rival tome 1 premio menos** al matar al portador (una vez por partida):
   ataca directamente al problema estructural de los 3 premios, y el motor **ya lo implementa**
   (`prize_count()` con descuentos por Legacy Energy 12 y Lillie's Pearl 1172,
   `kernels-referencia.md`).

---

## 5. Cartas del pool que cambian el plan (todas verificadas en `cards_clean.csv`)

| id | carta | por qué |
|---|---|---|
| **20** | Rock Fighting Energy | da {F} y **bloquea todos los EFECTOS de ataques** sobre el {F} que la lleve: anula `Powerful Hand` (contadores), `Phantom Dive` (contadores), `Adrena-Brain`. Avalado por Pokemon.com como el arreglo del emparejamiento Alakazam. No la recicla Aura Jab (es especial). |
| **1211** | Black Belt's Training | +40 al activo **ex**; con Premium Power Pro (Item) da la línea de **340** = OHKO a todo el campo ex. |
| **1213** | Judge | única «ambos barajan y roban 4» del pool. Rompe Alakazam y Mega Froslass ex. |
| **1087** | Hand Trimmer | **Item** que deja a ambos en 5 cartas → Alakazam a 100 de daño **sin gastar el partidario**. |
| **1252** | Gravity Mountain | −30 PS a todo Stage 2; Mega Lucario es Stage 1 (inmune). Además es *un* estadio, que es lo que nos falta para tirar los suyos. |
| **674** | Hariyama | gust gratis al evolucionar + 210 de daño desde un single-prize. |
| **676/675** | Solrock / Lunatone | atacante de 1 premio (70, ignora debilidad) + robo de 3. Es el paquete que arregla el intercambio de premios. |
| **12** | Legacy Energy (ACE SPEC) | 1 premio menos al morir el portador; **implementado en el motor**. |
| **117** | Cornerstone Mask Ogerpon ex | `Prevent all damage from attacks done to this Pokémon by your opponent's Pokémon that have an Ability`. Grimmsnarl ex (Punk Up) y Alakazam (Psychic Draw) **tienen** habilidad → no le hacen daño. Dragapult ex y Mega Lopunny ex **no** tienen habilidad → sí se lo hacen. Es {F}: encaja con nuestra energía. Contra: es ex (2 premios). Dark Fox lo mete de tech y dice que le da 80/20 contra Gholdengo. |
| **602** | Sawk | `Rising Chop [{F}] 90`, **solo funciona contra ex**; single-prize de 110 PS y retirada 1. Con Power Pro + Black Belt's = 160 por UNA energía desde un cuerpo de 1 premio. Candidato a probar, nadie lo juega. |
| **1080** | Unfair Stamp (ACE SPEC) | tras recibir un KO: ambos barajan la mano, tú robas 5 y él 2. Lo llevan 6 de las 14 listas del campo. |

**No existen en el pool** (verificado por nombre): Iono, Marnie, Professor's Research, Artazon,
Nest Ball, Super Rod, Earthen Vessel, Counter Catcher, Bravery Charm, Defiance Band,
Technical Machine (ninguna). Cualquier lista de papel que se copie hay que traducirla.

---

## 6. Qué hay que comprobar en el motor antes de creerse esto

Son tests baratos (una partida o una lectura de logs), no experimentos:

1. **Multiplicador de debilidad**: ¿es ×2? De ello depende el 86% contra Lopunny y toda la
   valoración del tipo {F}.
2. **¿Bloquea Rock Fighting Energy 20 la colocación de contadores?** Es la diferencia entre
   ganar y perder el 18,2% del campo. Test: Alakazam ataca a un {F} con la energía puesta.
3. **¿El que va primero puede atacar en su primer turno?** Determina toda la política del
   select (9,41), que vale +6 a +12 puntos de winrate.
4. **¿Aura Jab acepta 0 objetivos de banca?** (`option == []`, select `(0,7)`) — el agente
   debe devolver `[0]`, ya cubierto en `motor-mecanica.md §1`.
5. **¿`Destined Fight` (Annihilape 224) está implementado?** Explica el 23% contra el mazo de
   mayor winrate del campo.
6. **¿Cuenta `Heave-Ho Catcher` (Hariyama 674) como habilidad al evolucionar?** El motor tiene
   habilidades «al jugar para evolucionar» (Kadabra/Alakazam las usan y el campo las juega).

---
---

# §7 — PASE 2 (2026-08-11): listas de papel con conteos, mapa de premios y correcciones

Este pase busca lo que el pase 1 no tenía: **conteos exactos de listas reales de torneo**,
la **secuencia de premios** con la que un humano gana con Mega Lucario, y una relectura del
pool buscando específicamente las cartas que las guías de papel dan por obvias. Cuatro
afirmaciones del pase 1 estaban mal y se corrigen abajo.

## 7.0 Correcciones al pase 1 (verificadas en `cards_clean.csv`)

1. **Mega Lopunny ex 849 tiene 330 PS, no 320.** Aura Jab + Premium Power Pro = (130+30)×2 =
   **320**: se queda a 10. El OHKO barato contra el 12,8% del campo **sólo existe** si sumas
   Black Belt's Training 1211 (+40 a ex) → 400, o Maximum Belt 1158 (+50 a ex) → 360. Sin una
   de esas dos cartas el mejor emparejamiento del mazo es mucho peor de lo que parecía.
2. **Alakazam tiene blindaje de banca.** `decks/campo/c2-alakazam.csv` lleva **Shaymin 343**:
   `Flower Curtain :: Prevent all damage done to your Benched Pokémon that don't have a Rule
   Box by attacks from your opponent's Pokémon`. El plan «matar Abras de banca» hace **0
   daño** mientras Shaymin viva. Hay que **arrastrar al activo** (Boss's Orders 1182 /
   Prime Catcher 1088 / `Heave-Ho Catcher` de Hariyama 674) o matar al propio Shaymin (80 PS).
3. **Rock Fighting Energy 20 no es un blindaje permanente contra Alakazam.** Es *Special
   Energy* y la lista de campo de Alakazam lleva **4 Enhanced Hammer 1081**
   (`Discard a Special Energy from 1 of your opponent's Pokémon`, Item, gratis). Sigue siendo
   la carta correcta —mientras esté puesta, `Powerful Hand` (que **coloca contadores**, o sea
   un *efecto*) hace literalmente 0—, pero hay que contar con que se la quitan: 2 copias
   contra 4 hammers pierde la carrera; y `Aura Jab` **no la recicla** (sólo mueve *Basic {F}*).
4. **En nuestro pool Riolu sólo evoluciona a Mega Lucario ex.** Consulta:
   `prev_stage == 'Riolu'` → `[('678','Mega Lucario ex')]`, único resultado. El «baby Lucario»
   (Lucario SVI 114) que las guías de papel usan como atacante de 1 premio **no existe aquí**,
   y con él se cae el truco de Dark Fox de dejar Riolus sin evolucionar para evolucionarlos
   luego a un cuerpo barato. Nuestros únicos atacantes de 1 premio {F} tienen que ser
   **Solrock 676 / Hariyama 674** (u otros básicos, §7.4).
   Del mismo modo, la frase de Dark Fox «Aura Jabbing removes their energies» **no aplica**:
   el texto del pool es `Aura Jab [{F}] 130 :: Attach up to 3 Basic {F} Energy cards from your
   discard pile to your Benched Pokémon in any way you like` — sólo acelera lo nuestro, no
   descarta lo suyo.

## 7.1 Mega Lucario ex: cinco listas reales frente a la nuestra

Todos los conteos son de la fuente citada, no interpretados. `—` = la carta no está en esa
lista; `∅` = **la carta no existe en nuestro pool** (verificado por nombre en `cards_clean.csv`).

| carta (id pool) | Pokemon.com | Limitless (media) | Dark Fox | J.W.Anderson | UltimaSupply | campo `c7` | **NUESTRA** |
|---|---|---|---|---|---|---|---|
| Riolu **677** | 3 | 4 | 4 | 3 | 3 | 3 | **4** |
| Mega Lucario ex **678** | 3 | **3 (100% listas)** | **2** | 3 | 3 | 4 | **4** |
| Lucario básico (∅ SVI 114) | — | 2 | 1 | — | — | — | — |
| Makuhita/Hariyama **673/674** | 2/2 | splash | 1/1 | 2/2 | 2/2 | 2/2 | **0/0** |
| Lunatone/Solrock **675/676** | 2/2 | 2/2 | 2/2 | 2/2 | 2/3 | 2/3 | **0/0** |
| Regirock ex **447** | — | — | — | — | — | — | **4** |
| Fighting Gong **1142** | 4 | 4 | 4 | 4 | — | 4 | 4 |
| Premium Power Pro **1141** | 4 | 4 (95%) | 4 | 4 | — | 4 | **2** |
| Poké Pad **1152** | 4 | 3 | — | — | — | 4 | **0** |
| Ultra Ball **1121** | 4 | 2 | 4 | 4 | 4 | 4 | 4 |
| Lillie's Determination **1227** | 4 | 4 | 3 | 4 | 3 | 4 | **2** |
| Judge **1213** | **2** | — | — | — | — | **4** | **0** |
| Boss's Orders **1182** | 2 | — | 3 | 2 | 3 | 2 | 2 |
| Black Belt's Training **1211** | **1** | — | — | — | — | — | **0** |
| Gravity Mountain **1252** | **1** | **1 (100% listas)** | — | 2 | — | — | **0** |
| Air Balloon **1174** | 1 | — | 2 | 2 | — | — | **0** |
| Night Stretcher **1097** | 2 | — | 2 | 2 | — | — | 2 |
| Switch **1123** | 1 | — | 1 | — | 2 | 2 | 2 |
| ACE SPEC | Secret Box **1092** | — | Maximum Belt **1158** | Maximum Belt **1158** | Maximum Belt **1158** | Hero's Cape **1159** | Master Ball **1125** |
| Rock Fighting Energy **20** | **3** | — | — | — | (4 «Stone» ∅) | — | **0** |
| Energía {F} básica **6** | 10 | **7** | 9 | 9 | 10 | 13 | **19** |
| **total energías** | **13** | **7** | **9** | **9** | **14** | **13** | **19** |

Fuentes:
[Pokemon.com — Building a Mega Lucario ex Deck](https://www.pokemon.com/us/features/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck),
[Limitless — Mega Lucario deck overview (core cards e inclusión %)](https://limitlesstcg.com/decks/345),
[Dark Fox TCG — Mega Lucario Deck & Matchup Guide](https://www.darkfoxtcg.com/blogs/news/mega-lucario-deck-matchup-guide),
[Joseph Writer Anderson — Mega Lucario ex Deck List and Guide](https://www.josephwriteranderson.com/blog/mega-lucario-ex-deck-list-and-guide),
[Ultima Supply — Mega Lucario ex Deck Guide: Post-Rotation](https://ultimasupply.com/blogs/news/mega-lucario-ex-deck-guide-post-rotation-strategy-and-list).

**Los cinco consensos del papel que nuestra lista rompe:**

1. **Nadie juega 4 Mega Lucario ex.** Limitless: **3 copias en el 100% de las listas**; Dark
   Fox baja a 2 («giving up 3 Prizes when knocked out SUCKS»). Nosotros llevamos 4 **y encima
   4 Regirock ex** (2 premios cada uno): **8 Pokémon multi-premio y cero atacantes de 1
   premio**. Contra cualquier mazo, dos KOs y estamos muertos.
2. **Todas llevan paquete de 1 premio (Solrock/Lunatone y/o Hariyama). Nosotros, ninguno.**
3. **Todas llevan 4 Premium Power Pro.** Nosotros 2.
4. **7-14 energías, nunca 19.** La mediana del papel es 9. Con `Aura Jab` reciclando 3 del
   descarte cada turno y 4 Fighting Gong buscando, 19 son ~7 cartas muertas.
5. **Estadio: Gravity Mountain aparece en el 100% de las listas de Limitless** (1 copia).
   Nosotros no llevamos ninguno, así que además de perder el efecto **no podemos tirar el
   estadio del rival** (Spikemuth Gym, Festival Grounds, Jamming Tower, Academy at Night).

**Matiz honesto sobre Regirock ex 447**: no es una carta absurda —
`Giant Rock [{F}●●●] 140 :: If your opponent's Active Pokémon is a Stage 2 Pokémon, this
attack does 140 more damage` = **280 contra Stage 2**, y Stage 2 es Grimmsnarl + Alakazam +
Garchomp + Dragapult ≈ **59% del campo**; y `Regi Charge [●]` se autoacelera 2 {F} del
descarte. El problema no es la carta, es **la cantidad**: 4 copias de un cuerpo de 2 premios y
230 PS que necesita 4 energías. Si se conserva, 1 copia como atacante de castigo, no 4.

## 7.2 El mapa de premios: el concepto de baraja que hay que escribir en el writeup

Esto es lo que puntúa el 20% de Deck Score y hoy no lo tenemos articulado. El papel lo formula
como una **secuencia de 6 premios**, no como «pegar fuerte»:

> «attack with single-Prize Pokémon throughout the game, preventing your opponent from just
> winning the game by Knocking Out two Mega Lucario ex»
> — [Pokemon.com](https://www.pokemon.com/us/features/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck)

> «using Aura Jab to take an initial KO on a low-HP two-Prize Pokémon, then using Hariyama to
> take another two Prize cards before finishing with a Mega Brave»
> — [Dark Fox TCG](https://www.darkfoxtcg.com/blogs/news/mega-lucario-deck-matchup-guide)

**El plan canónico = 2 + 2 + 2:**
- **premios 1-2**: `Aura Jab` (130, barato, y **acelera 3 {F} del descarte a la banca**) mata
  un ex de apoyo de PS bajo. En nuestro campo esos objetivos existen: **Fezandipiti ex 140**
  (210 PS, {D}, **debilidad {F}**, lo lleva la lista de Alakazam del campo) y **Meowth ex
  1071** (170 PS, {C}, **debilidad {F}**) mueren a `Aura Jab` pelado, 130×2 = **260**.
  Cuidado con los otros dos candidatos: **Latias ex 184** (210 PS, débil {D}) y **Teal Mask
  Ogerpon ex 96** (210 PS, débil {R}) **no son débiles a {F}** → 130 no basta, hacen falta
  `Aura Jab`+PPP+Black Belt's (200) todavía corto, o directamente `Mega Brave`.
- **premios 3-4**: **Hariyama 674**. Y aquí está el detalle que nadie deduce solo: las 3
  energías que `Aura Jab` saca del descarte se pueden poner **todas en un Hariyama de banca**,
  que es exactamente su coste `Wild Press [{F}{F}{F}] 210`. Pokemon.com lo dice literal: «you
  can power up its {F}{F}{F} cost with one Aura Jab». Además Hariyama, **al evolucionar desde
  la mano**, hace `Heave-Ho Catcher` = **gust gratis sin gastar el partidario del turno**:
  evoluciona, arrastra el objetivo y pega 210, todo en el mismo turno.
- **premios 5-6**: `Mega Brave` 270 (+30 PPP, +40 Black Belt's, +50 Maximum Belt) sobre el
  atacante gordo del rival.

**Regla de apertura del papel** (Pokemon.com): *«typically you want to open with Solrock
against single-Prize decks and with Mega Lucario ex against the decks where you need to set up
for Mega Brave and attack with Hariyama»*. Es una regla de decisión de una línea que hoy no
tenemos: **contra mazos de 1 premio (Alakazam 18,2%, Dipplin 3,5%, Slowking 1,8% ≈ 24% del
campo) el activo de salida es Solrock, no Lucario.**

Y la regla de montaje de Dark Fox: *«Typically you want to have 2 Riolu down to start, evolve
one into Mega Lucario ex, then leave the other as a Riolu»* — **nunca dos Mega Lucario ex en
mesa a la vez**; el segundo Riolu se queda de Riolu (1 premio) hasta que evolucionarlo sea
seguro.

## 7.3 Aritmética de daño: qué mata a qué (todos los PS del pool)

Modificadores del pool, todos **antes de debilidad**: Premium Power Pro **1141** (Item, +30
este turno, {F}), Black Belt's Training **1211** (Supporter, +40, **sólo contra ex**),
Maximum Belt **1158** (ACE SPEC Tool, **+50 permanente, sólo contra ex**). Item + Supporter +
Tool son compatibles el mismo turno: **270+30+40+50 = 390 contra un ex**, 300 contra un
no-ex. Gravity Mountain **1252** resta 30 PS a **todo Stage 2** (Mega Lucario es Stage 1:
inmune).

| objetivo | PS | Stage 2 | con Gravity Mountain | ¿Mega Brave 270 solo? | ¿qué hace falta? |
|---|---|---|---|---|---|
| Marnie's Grimmsnarl ex **648** | 320 | sí | **290** | no | GM+PPP (300) **o** Maximum Belt (320 exacto) |
| Dragapult ex **121** | 320 | sí | **290** | no | igual que arriba. **Ojo Budew 235**: apaga nuestros Items → sin PPP nos quedamos en 270 |
| Cynthia's Garchomp ex **381** | 330 (**400** con Power Weight 1173) | sí | 300 / 370 | no | GM+PPP=300 contra el desnudo; contra 400 **no llegamos** ni con 390 → hay que matar al Gabite |
| Mega Lopunny ex **849** | 330, **débil {F}** | no | 330 | (Aura Jab) | Aura Jab+PPP=320 **falla**; +BBT → 400 ✓ o +Belt → 360 ✓ |
| Mega Kangaskhan ex **756** | 300, **débil {F}** | no | 300 | (Aura Jab) | Aura Jab+PPP = (130+30)×2 = **320** ✓ |
| Mega Froslass ex **861** | 310 | no | 310 | no | 270+50 = 320 ✓ (Maximum Belt) |
| Mega Abomasnow ex **723** | 350 | no | 350 | no | 270+30+40+50 = **390** ✓ |
| Alakazam **743** | 140 | sí | **110** | — | **con GM, `Aura Jab` 130 lo mata solo**; sin GM hace falta PPP (160) |
| Hariyama/Dudunsparce/Slowking | 150/140/120 | no | — | — | Aura Jab 130 + PPP = 160 mata a los tres |
| Froslass **104** / Munkidori **112** | 90 / 110 | no | — | — | Solrock `Cosmic Beam` 70 + PPP = 100 mata Froslass; Munkidori necesita Aura Jab |

Dos conclusiones operativas: **(a)** Gravity Mountain 1252 no es «una carta más», es lo que
convierte `Mega Brave + PPP` (300) en OHKO contra el **59% del campo** que juega Stage 2, y lo
que hace que `Aura Jab` mate a Alakazam de un golpe. **(b)** Maximum Belt 1158 es el ACE SPEC
que juegan **tres de las cinco listas de papel** y es mejor que nuestro Master Ball 1125:
+50 permanente contra ex, sin gastar carta cada turno.

## 7.4 Cartas del pool que el pase 1 no vio (todas verificadas)

| id | carta | por qué importa |
|---|---|---|
| **1158** | **Maximum Belt** (ACE SPEC Tool) | `+50 more damage to your opponent's Active Pokémon {ex}`. **Permanente**, no un turno. El ACE SPEC de Dark Fox, J.W.Anderson y Ultima Supply. Da OHKO exacto a Grimmsnarl ex (320) y a Dragapult ex (320) con `Mega Brave` pelado. |
| **1174** | **Air Balloon** (Tool) | `Retreat Cost {C}{C} less`. **Mega Lucario ex tiene retirada 2 → 0.** Todo el plan de rotar Solrock↔Lucario↔Hariyama depende de poder retirar gratis; hoy lo pagamos con 2 Switch de un solo uso. Lo llevan 3 de las 5 listas. |
| **41** | **Ting-Lu** (Basic {F}, 140 PS, **1 premio**) | `Ground Crasher [{F}] 30 :: If a Stadium is in play, this attack also does 30 damage to each of your opponent's Benched Pokémon, and **discard that Stadium**`. Por **una** energía: tira el estadio rival (Spikemuth Gym / Festival Grounds / Jamming Tower / Academy at Night) **y** siembra 30 en toda su banca. Es la respuesta a Dipplin (que muere sin Festival Grounds) desde un cuerpo de 1 premio. |
| **607** | **Terrakion** (Basic {F}, 140 PS, **1 premio**) | `Retaliate [{F}●] 50 :: +80 si alguno de tus Pokémon fue noqueado el turno pasado` = **130 por 2 energías** justo el turno después de perder un Lucario, y `Aura Jab` deja esas 2 energías puestas. Atacante de venganza de 1 premio. |
| **884** | **Medicham** (Stage 1 {F}, 120 PS, 1 premio) | `Seventh Kick [{F}] 150` si tienes **exactamente 7** cartas en la mano. 150 por una energía. Condición dura para una heurística, trivial para un agente que cuenta la mano. |
| **1210** | **Brock's Scouting** (Supporter) | `busca hasta 2 Básicos **o** 1 de Evolución`. Lo lleva la lista oficial de Pokemon.com (×2). Es el buscador de Pokémon que el pool sí tiene (no hay Nest Ball ni Artazon). |
| **1071** | **Meowth ex** (170 PS, {C}, **debilidad {F}**) | `Last-Ditch Catch`: al bajarlo a banca **busca un Supporter cualquiera**. Lo lleva Ultima Supply como seguro anti-disrupción. Contra nosotros es un objetivo de Aura Jab (260 por debilidad). |
| **1251** | **Lively Stadium** | +30 PS a **cada Básico**: Riolu 80→110 (sale del rango de los ataques de 100), Solrock/Lunatone 110→140. Estadio defensivo alternativo a Gravity Mountain. |
| **1260** | **Risky Ruins** | 2 contadores a cada Básico **no-{D}** que se baje a banca. Castiga a Alakazam (4 Buddy-Buddy Poffin bajando Abras de **50 PS** → quedan en 30) y a Garchomp (Gibles de 70). Nosotros bajamos pocos Básicos y los nuestros aguantan. Estadio agresivo anti-Fase-2. |
| **534** | **Landorus** (BLK, Basic {F}, 130 PS, 1 premio) | `Abundant Harvest [●] :: Attach a Basic {F} Energy card from your discard pile to this Pokémon` — se autoacelera; `Earthquake [{F}●●] 110`. |
| **1088** | **Prime Catcher** (ACE SPEC Item) | gust **+ cambio propio** en la misma carta. Alternativa a Maximum Belt si el problema es alcanzar la banca. |

## 7.5 Trampa detectada: **Neutralization Zone 1247** NO es para nosotros

Texto completo: `Prevent all damage done to Pokémon that don't have a Rule Box (both yours
and your opponent's) by attacks from the opponent's Pokémon {ex} and Pokémon {V}`. A primera
vista blinda nuestro paquete de 1 premio. En realidad es **simétrica y nos perjudica**: con
ella en mesa, **nuestro Mega Lucario ex no puede hacer daño a Alakazam 743, Dipplin 93,
Froslass 104, Munkidori 112 ni Slowking 163** — es decir, se apaga contra el 24% del campo que
es exactamente el que ya nos cuesta. Y no ayuda contra `Powerful Hand`, porque eso **coloca
contadores** (efecto), no «daño». La lleva `meta/alakazam-v10.csv` (×1) precisamente porque
ellos son el mazo de 1 premio: **es una carta contra nosotros, no nuestra**.

## 7.6 Emparejamientos del papel (Limitless, formato Standard 2025, set MEG)

Sirven para el **porqué**, no para predecir nuestra ladder (el campo de papel es otro: allí
existen Gardevoir y Charizard, aquí no).

**Mega Lucario ex** — [matchups](https://play.limitlesstcg.com/decks/mega-lucario-ex/matchups?format=standard&rotation=2025&set=MEG):
Dragapult Charizard 80% (4-1) · Pidgeot Control 66,7% · Mega Venusaur 62,5% (5-3) ·
**Cynthia's Garchomp 62,5% (5-3)** · Joltik Box 60% · Dragapult Dusknoir 53,1% (17-14) ·
N's Zoroark 50% · Mega Absol Box 47,1% · **Grimmsnarl Froslass 42,9% (6-8)** ·
Gholdengo Lunatone 37,5% · Lucario Hariyama 37,5% · Ceruledge 35% · Slowking 33,3% ·
Charizard Pidgeot 32% · Raging Bolt Ogerpon 30% · Gholdengo 28,6% · **Gardevoir 14,3% (3-18)** ·
**Tera Box 0% (0-7)**.

**Alakazam Dudunsparce** — [matchups](https://play.limitlesstcg.com/decks/alakazam-dudunsparce/matchups?format=standard&rotation=2025&set=MEG),
récord global 48,35% (1714-1775-56):
Gholdengo 77,1% · **Lucario Hariyama 67,7% (42-19)** · Ceruledge 69,4% · Mega Venusaur 63,5% ·
Raging Bolt 63,1% · **Cynthia's Garchomp 60,4% (32-21)** · Crustle 60,8% ·
Gholdengo Lunatone 59,5% · Tera Box 53,5% · Mega Absol 51,2% · Charizard Pidgeot 46,7% ·
N's Zoroark 40,6% · Gardevoir Jellicent 34,3% · Gardevoir 32,9% ·
**Dragapult Dusknoir 28,3% (78-197)** · **Grimmsnarl Froslass 22,7% (55-185)**.

**Lucario Hariyama** (la variante de 1 premio, deck distinto) —
[matchups](https://play.limitlesstcg.com/decks/lucario-hariyama/matchups?format=standard&rotation=2025&set=MEG),
récord global 46,0%: Mega Absol 61,1% · **Dragapult Dusknoir 54,1%** · Raging Bolt 50% ·
Mega Venusaur 47,1% · Grimmsnarl Froslass 45,3% · Ceruledge 43,9% · Charizard Pidgeot 41,3% ·
Gholdengo Lunatone 39,7% · **Gardevoir 25,2%** · **Gardevoir Jellicent 20,8%**.

**Lectura cruzada, que es lo que importa:**
- **Alakazam gana a Lucario 67,7% en el papel y sólo 52% en nuestra ladder.** La diferencia es
  que en el papel Lucario juega con debilidad {P} real (Gardevoir 14%, Gardevoir Jellicent
  20,8%) y aquí el único {P} grande es Alakazam, cuyo daño son **contadores** que **no aplican
  debilidad**. Conclusión: **nuestra debilidad {P} casi no cuesta en esta ladder** — el
  argumento «Lucario es malo porque es débil a {P}» no aplica aquí y no debe ir al writeup.
- **Grimmsnarl gana a Alakazam en los dos campos** (papel 77,3%, ladder 57%) por el mismo
  motivo mecánico: Froslass 104 + Munkidori 112 barren la línea Abra(50)/Kadabra(80) sin
  atacar. Es la misma física, y por eso la matriz de la ladder es creíble.
- **Cynthia's Garchomp pierde con Alakazam (39,6%) y pierde con Lucario (37,5%)** en el papel:
  es un mazo de montaje lento que los dos castigan.

## 7.7 Tabla de decisión CONTRA cada arquetipo (lo que hay que codificar)

| rival | ¿primero o segundo? | objetivo #1 a matar | carta clave a negar | error típico de una heurística greedy |
|---|---|---|---|---|
| **Mega Lucario ex** | **primero** si eres Fase 2 (te da el turno de montaje y él no pega 270 hasta T3); **segundo** si puedes matar Riolu (80 PS) antes de que evolucione | el **Riolu / Lucario de banca cargado** por `Aura Jab`, no el activo | Hariyama 674 en banca (gust gratis) | pegar al activo de 340 PS en vez de al banquillo cargado |
| **Alakazam** | **primero** (su daño real no llega hasta T2-T3 y sus básicos mueren de un soplo) | **Shaymin 343 arrastrado al activo**, después Kadabra/Abra de repuesto | su **mano**: Judge 1213 el turno ANTES de que ataque; Hand Trimmer 1087 es **Item** (no gasta partidario) | disparar a la banca (Flower Curtain lo anula) y robar cartas de más justo antes de su turno |
| **Cynthia's Garchomp ex** | **segundo** (montaje lento: Gible→Gabite→Garchomp) | **Cynthia's Gabite 380** de banca (`Champion's Call` es su único buscador) y **Roserade 342** (+30 acumulable) | Cynthia's Power Weight 1173: con él son 400 PS y **no hay OHKO posible** | intentar matar al Garchomp de 400 PS en vez de al Gabite de 100 |
| **Aggro de agua (Abomasnow/Kyogre)** | **segundo** e ir a por Snover | **Snover 722 (90 PS)** antes de la evolución | ninguna: se autodestruye (`Hammer-lanche` descarta 6 de su propio mazo cada turno) | tratarlo como amenaza real; **es 0/18.674 en la ladder** |
| Marnie's Grimmsnarl ex (31,2%) | **segundo** | **Froslass 104** (sin ella no hay contadores que mover), después Munkidori 112 | Spikemuth Gym 1259 → **Ting-Lu 41** lo descarta por 1 energía | dejar que Froslass viva porque «no ataca» |
| Dragapult ex (8,2%) | **segundo** con montaje hecho (Dark Fox lo da 50/50) | Dreepy/Drakloak de banca | **Budew 235**: nos apaga los **Items** un turno → sin Premium Power Pro no llegamos a 320 | contar con el +30 de PPP el turno en que Budew está activo |
| Slowking/Kanga/Latias (nos gana 77%) | **segundo** | **Slowpoke 162 / Slowking 163** antes del ciclo | Ciphermaniac's Codebreaking 1188 (apila la cima) → `Destined Fight` de Annihilape 224 | **dejar el Mega Lucario en el activo**: cambian un cuerpo de 1 premio por nuestros 3 |
| Dipplin / Festival Lead (3,5%) | **segundo** | Dipplin 93 (80 PS) | **Festival Grounds 1245** → Ting-Lu 41 o cualquier estadio propio | no llevar estadio y regalarle ataque doble toda la partida |

## 7.8 Lista propuesta (60) — **propuesta, sin medir; decide el propietario**

No he lanzado partidas (regla de la tarea). Esto es la traducción del consenso de papel a
nuestro pool, con los huecos tapados por las cartas de §7.4. Cada línea justificada arriba.

**Pokémon (16)**: 4× Riolu **677** · 3× Mega Lucario ex **678** · 3× Solrock **676** ·
2× Lunatone **675** · 2× Makuhita **673** · 2× Hariyama **674**
**Entrenador (33)**: 4× Fighting Gong **1142** · 4× Poké Pad **1152** ·
4× Premium Power Pro **1141** · 3× Ultra Ball **1121** · 4× Lillie's Determination **1227** ·
3× Judge **1213** · 2× Boss's Orders **1182** · 2× Black Belt's Training **1211** ·
2× Air Balloon **1174** · 1× Switch **1123** · 1× Night Stretcher **1097** ·
1× **Maximum Belt 1158** (ACE SPEC) · 2× Gravity Mountain **1252**
**Energía (11)**: 9× Basic {F} **6** · 2× Rock Fighting Energy **20**

Cambios respecto a la nuestra, por impacto esperado: fuera **4 Regirock ex** (−8 premios
regalados) y **10 energías**; dentro el **paquete de 1 premio** (Solrock/Lunatone/Hariyama =
el mapa 2+2+2 de §7.2), **+2 Premium Power Pro y +2 Black Belt's Training** (sin ellos no
existe el OHKO contra el 59% del campo), **Judge** (el 18,2% del campo es Alakazam),
**estadio** (efecto propio + poder tirar el suyo), **Air Balloon** (el mazo es de rotar) y el
cambio de ACE SPEC a **Maximum Belt**. Variantes a probar si sobra hueco: 1× Ting-Lu **41**
por 1 Judge si Dipplin/Grimmsnarl suben; 1× Terrakion **607** como atacante de venganza.

**Antes de creerse nada de esto hay que medir**, y hay dos comprobaciones de motor que valen
más que la lista entera: (1) ¿el multiplicador de debilidad es ×2? (de ahí sale todo el valor
del tipo {F}); (2) ¿`Aura Jab` deja realmente elegir a qué Pokémon de banca van las 3
energías? Si el motor las reparte solo, el mapa 2+2+2 de §7.2 no se puede ejecutar.
