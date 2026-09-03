# Teoría de construcción de mazos — ratios de torneo vs. nuestras listas

Fecha: 2026-08-10. **Revisión y ampliación 2026-08-11** (§0, §3bis, §5bis, §5ter, §8.0,
§8.5, §9bis). Alimenta el **20% Deck Score** del writeup («concepto de baraja claramente
articulado, cartas clave bien elegidas y utilizadas») y parte del 70% Model Score
(consistencia).

Scripts de apoyo (scratchpad, no versionados): `analiza_ratios.py`, `ratios2.py`,
`ratios3.py`, `metricas.py`; pase de verificación 2026-08-11 en `verif.py`…`verif4.py`.
Datos: `research/cards_clean.csv`, `research/decks/{propios,meta,campo}/`.

---

## 0. Qué cambió en la revisión del 2026-08-11

Se recalcularon **todas** las cifras agregadas desde cero sobre las 30 listas
(9 propias + 6 meta + 15 campo). Resultado del cotejo:

**Reproduce exacto** (la nota original es fiable en esto): medias de propios
11,1 Pk / 8,0 básicos / 0,348 mulligan / 31,1 Trainers / 17,8 energía / 2,08 energías por
mano; campo 16,3 / 9,6 / 0,288 / 33,0 / 10,7 / 1,25. Las 48 copias de Poké Pad en 13 de
15 listas del campo: confirmadas una a una. Las 29 ACE SPEC del pool y la corrección de
que **Sacred Ash 1129 no es ACE SPEC**: confirmadas contra la columna `rule`.

**Se corrige** (§5bis): el objetivo «P(básico) × P(motor) ≥ 0,90 conjunta» del §5 era
matemáticamente inalcanzable y medía lo que no era. La métrica correcta es
**condicionada a no hacer mulligan** — y con ella **no tenemos un problema de
consistencia**: 0,928 nosotros vs 0,901 el campo.

**Se añade lo que faltaba**, y que resultó ser el diagnóstico de verdad:

| Hallazgo nuevo | nosotros | campo | dónde |
|---|---|---|---|
| Pokémon que regalan 2 premios | **32,8%** | 27,9% (12,9% en `meta/`) | §8.0 |
| Estadios por lista | **1,33** (4 listas con 0) | 2,53 | §5ter |
| Supporters de robo | **9,56** | 4,87 | §5bis |
| Objetivos de Poké Pad (Pokémon sin Rule Box) | **7,6** | 12,5 | §8.5 |
| Motor total (robo+búsqueda) | 19,7 | 17,2 | §5bis |

Es decir: **no nos falta consistencia, nos sobra energía, regalamos premios, no
disputamos el estadio y el motor está en el tipo de carta equivocado.**

⚠️ **Aviso de meta**: el encargo de esta investigación citaba «Mega Lucario 42% /
Alakazam 17% / aggro 17% / Garchomp 8%». Ese censo está **derogado** por
`notas/baraja-vs-campo.md` (18.674 barajas, 2026-08-10): Grimmsnarl 31,2% ·
Alakazam 18,2% · Lopunny/Froslass 12,8% · Dragapult 8,2% · Kangaskhan 6,9% ·
Ogerpon 5,0% · **Mega Lucario 4,0%** · Dipplin 3,5%. Todo el §7 usa el censo bueno.

---

## 1. El esqueleto canónico y qué dice cada fuente

| Fuente | Pokémon | Trainers | Energía | Desglose |
|---|---|---|---|---|
| JustInBasil, *Deck Structure* | 20 | 30 | 10 | Supporters 6-12 (de los que **robo 4-9**, **Boss's Orders 2-4**); Items 15-20 (de los que **búsqueda de Pokémon 8-10**); Stadium 2-3 |
| TCG Protectors (2025) | 20 | 25 | 15 (principiante) | competitivo baja a 8-12 energías |
| Guías 2026 (agregado) | 12-20 | 30-35 | 8-15 | «lo más efectivo: 15 / 33 / 12» |

- JustInBasil: «not every deck will follow it exactly — many of the best decks in the
  Standard Format deviate from the card counts of each main category by **plus or minus
  three cards**». <https://www.justinbasil.com/guide/deck-structure>
- Regla de forma de la misma fuente: **si un Item y un Supporter hacen lo mismo, va el
  Item**, «you can only play one Supporter card each turn, but you can play as many Item
  cards as you like». Es el principio que más peso tiene en nuestro caso (ver §8.3).
- <https://tcgprotectors.com/blogs/pokemon-deck-guides/how-to-build-pokemon-tcg-deck-guide>

**Listas reales de torneo con NUESTRO pool** (set Mega Evolution / MEG, mismo formato
que el simulador). Esto vale más que cualquier guía porque son las mismas cartas:

| Lista | Torneo | Pk | Tr | En |
|---|---|---|---|---|
| Mega Lucario — Victor Zhao | Special Event Turin, 43º | **18** | **32** | **10** (9 {F} + 1 Rocky) |
| Lucario Hariyama — Brian Du | NAIC 2026, 86º | **16** | **32** | **12** {F} |
| Grimmsnarl Froslass — Andrew Choi | NAIC 2026, 128º | **19** | **32** | **9** {D} |
| Dragapult ×6 lists | NAIC 2026, 3º/8º/9º/13º/22º/49º | 18-20 | **31-35** | **8-9** |

<https://limitlesstcg.com/decks/list/27959> · <https://limitlesstcg.com/decks/list/28314> ·
<https://limitlesstcg.com/decks/list/28345> · <https://limitlesstcg.com/tournaments/518/decklists>

**Convergencia**: humano competente con este pool = **16-20 Pokémon / 31-35 Trainers /
8-13 Energía**. Nuestra media es **11,1 / 31,1 / 17,8**. Los Trainers están bien; el
error está en el reparto Pokémon↔Energía (≈ 6 cartas mal colocadas por lista).

### 1bis. La lista de Zhao, entera (verificada 2026-08-11)

Es nuestro mejor documento: **mismo arquetipo que `propios/mega-lucario`, mismo pool,
jugada por un humano en un torneo real**. Copiada literal de
<https://limitlesstcg.com/decks/list/27959> (Victor Zhao, Special Event Turin, 43º):

```
Pokémon (18)                    Trainer (32)                  Energy (10)
3 Riolu            (2 PRE+1 SCR) 4 Lillie's Determination      9 Fighting Energy
3 Mega Lucario ex  (MEG)         3 Hilda                       1 Rocky Fighting Energy
3 Solrock          (MEG)         2 Boss's Orders
2 Lunatone         (MEG)         1 Team Rocket's Petrel
2 Dunsparce        (JTG)         4 Fighting Gong
2 Dudunsparce      (TEF)         4 Poké Pad
1 Makuhita         (MEG)         4 Premium Power Pro
1 Hariyama         (MEG)         2 Buddy-Buddy Poffin
1 Chien-Pao        (SSP)         2 Ultra Ball
                                 1 Switch · 1 Special Red Card
                                 1 Air Balloon
                                 1 Maximum Belt   ← ACE SPEC
                                 2 Gravity Mountain
```

Cinco lecturas que se contradicen con lo que hacemos nosotros, y todas son medibles:

1. **12 básicos** (3 Riolu + 3 Solrock + 2 Lunatone + 2 Dunsparce + 1 Makuhita +
   1 Chien-Pao) → mulligan **0,191**. Nosotros 8 → **0,346**.
2. **Solo 3 Pokémon de 2 premios** de 18 (**17%**). Nosotros 8 de 12 (**67%**). Ver §8.0.
3. **2 Ultra Ball, 4 Poké Pad**: el buscador caro (descartar 2) baja a 2 copias porque el
   buscador gratis hace el trabajo. Nosotros: 4 Ultra Ball y **0 Poké Pad**.
4. **Su ACE SPEC es Maximum Belt 1158**, no un buscador. Nosotros llevamos Master Ball.
5. **3 copias del atacante principal**, no 4 — porque lo busca, no lo roba.

---

## 2. Líneas evolutivas: los ratios y su lógica

| Línea | Ratio canónico | Cuándo |
|---|---|---|
| Stage 1 (atacante principal) | **4-3** (a veces 4-4 o 3-4) | El básico es el que hay que abrir; el St1 se busca luego |
| Stage 1 secundario / utilidad | **2-2** o **3-2** | Dudunsparce, Hariyama, Froslass |
| Stage 2 sin Rare Candy | **4-3-3** o **3-2-3** («la más común para el atacante principal») | |
| Stage 2 **con Rare Candy** | **4-1-3 / 4-2-4**, incluso 4-0-3 | Rare Candy «negates the need for most Stage 2 decks to include copies of the Stage 1»; Rare Candy va a **3-4 copias** |

<https://tcgprotectors.com/blogs/pokemon-deck-guides/how-to-build-pokemon-tcg-deck-guide> ·
<https://www.justinbasil.com/guide/consistency>

**El porqué (con la hipergeométrica de nuestro motor)**: la pieza que necesitas en la
mano inicial va a 4; la que buscas o evolucionas después va a menos, porque tienes
7 + t cartas vistas al turno t más los buscadores. Ver tabla §4.

**Lo que hace el campo real de la ladder** (`decks/campo/`, copiado literal de replays):
`c1` 4-3-3 Impidimp/Morgrem/Grimmsnarl ex + 2-2 Snorunt/Froslass ·
`c2` 4-4-4 Abra/Kadabra/Alakazam + 3-2 Dunsparce/Dudunsparce ·
`c4` 4-4-3 Dreepy/Drakloak/Dragapult ex · `c7` **3-4** Riolu/Mega Lucario ex + 2-2
Makuhita/Hariyama. Es exactamente el libro.

Nota fina de `c7`: **más St1 que básicos (3-4)** porque el St1 es el atacante y lo
buscas con Ultra Ball, mientras el básico se busca con Poké Pad; el paper hace lo mismo
(Zhao: 3 Riolu / 3 Mega Lucario ex, Du: 3/3).

---

## 3. Energía: la regla real, derivada para nuestro motor

Regla empírica publicada: **8-13 energías** en competitivo; 10-14 si el atacante pide
2+; hasta 6-8 con aceleración fuerte; el número sube solo si el coste de ataque es alto
y no hay ni búsqueda ni aceleración.
<https://www.delightfultcg.com/blogs/articles/how-many-energy-cards-should-be-in-a-pokemon-deck> ·
<https://www.justinbasil.com/guide/crafting-your-deck> («for many decks, the average of
11 Energy cards is a good number to start with»).

**Cota dura calculada sobre nuestro motor** (60 cartas, mano 7, 1 robo/turno, 1 adjunto
por turno, sin búsqueda ni aceleración): para poder adjuntar C energías en C turnos hace
falta `E ≥ 60·C/(7+C)`.

| Coste del ataque | E mínima sin ayuda |
|---|---|
| 1 | 7,5 |
| 2 | 13,3 |
| 3 | 18,0 |
| 4 | 21,8 |
| 5 | 25,0 |

**Y la corrección que hace el humano**: cada buscador de energía vale ~2 energías y cada
acelerador vale ~3, así que

> `E_efectiva ≈ E_mazo + 2·(buscadores de energía) + 3·(aceleradores)`

Ejemplo con las listas reales de Lucario: coste real = 1 ({F} Aura Jab) porque *el
ataque barato ES la aceleración* (adjunta 3 {F} del descarte a la banca). Cota = 7,5.
Suman 4 Fighting Gong (busca {F} básica o Pokémon {F}) y 3 Hilda (busca evolución +
energía) → llevan **10-13**. Nuestra `mega-lucario` lleva **19**: entre 6 y 9 cartas de
más.

Tabla operativa (probabilidad de tener energía cuando toca):

| E en mazo | P(≥1 al turno 1, 8 cartas) | P(≥2 al T2, 9) | P(≥3 al T3, 10) | E[energías en la mano de 7] |
|---|---|---|---|---|
| 8 | 0,706 | 0,344 | 0,120 | 0,93 |
| 10 | 0,790 | 0,467 | 0,211 | 1,17 |
| 13 | 0,877 | 0,631 | 0,371 | 1,52 |
| 16 | 0,931 | 0,760 | 0,535 | 1,87 |
| 19 | 0,963 | 0,853 | 0,680 | 2,22 |
| 28 | 0,996 | 0,978 | 0,936 | 3,27 |

Lo que enseña la última columna es el coste: con 19 energías abres con **2,22** de media
y solo puedes adjuntar **1 por turno**. La energía sobrante en mano es carta muerta,
salvo que la descartes con Ultra Ball. Con 10, abres con 1,17 y casi ninguna es muerta.

**Excepción legítima**: aceleradores que sacan la energía **del mazo** (Okidogi ex 138
Poisonous Musculature, Janine's Secret Art 1195, Fighting Gong 1142) quieren energía EN
EL MAZO, no en la mano. Ahí conviene contar `E` alta, pero la parte que llega a la mano
sigue siendo muerta: la solución humana no es subir a 15, es subir a ~12 y meter
recuperación (Night Stretcher 1097, Energy Retrieval 1118) para reciclar.

### 3bis. Recuperación: los counts canónicos

Es la categoría que cierra el argumento anterior — **la energía baja se sostiene
reciclando, no acumulando**. JustInBasil da counts por carta, y el patrón es
consistentemente **1-2 copias para recuperar Pokémon y 2-4 para recuperar energía**:

| Efecto | Count canónico | Equivalente en nuestro pool |
|---|---|---|
| Recuperar Pokémon del descarte (tipo Super Rod) | **1-2** | Night Stretcher 1097 (Pokémon **o** energía básica) |
| Recuperar energía básica (tipo Energy Retrieval) | **2-4** | Energy Retrieval 1118, Tarragon 1238 (hasta 4 {F}) |
| Recuperar Supporters (tipo Pal Pad) | **1** | Miracle Headset 1109 (ACE SPEC) |
| Recuperación masiva de un uso | 1 | Max Rod 1110 (ACE SPEC, hasta 5) |

Citas literales: «Decks that run Super Rod tend to run **1-2** copies» · «Decks that run
Energy Retrieval tend to run **2-4** copies» · «for decks that do include Pal Pad, it's
usually just a **single copy**». <https://www.justinbasil.com/guide/recovery>

**Criterio de cuándo subirlo**: el mazo prioriza recuperación cuando descarta sus propios
recursos como coste. Aplicado a nosotros: llevamos **4 Ultra Ball** (descarta 2 cartas de
la mano) en varias listas, lo que convierte Night Stretcher en estructural, no opcional.
Nuestro `mega-lucario` lleva 2 Night Stretcher + 2 Tarragon: **este ratio sí está bien**
y es de lo poco que no hay que tocar.

Regla derivada que une §3 y §3bis: **una copia de recuperación de energía sustituye a
~2-3 energías de mazo** sin ocupar sitio en la mano inicial, porque solo la coges cuando
la necesitas. Es el mecanismo exacto por el que Zhao juega 10 energías y nosotros 19.

---

## 4. Hipergeométrica aplicada: qué pregunta responde y qué número es aceptable

Todo lo de abajo está calculado exacto sobre 60 cartas, mano de 7, 6 premios (nuestro
motor). El mulligan ya está validado contra el motor en `lab-barajas.md` §2 (15 casos,
todos dentro de 3σ): **la hipergeométrica ES el motor**.

### 4.1 «¿Tendré la pieza X?»

P(≥1 copia entre las primeras n cartas vistas):

| copias K | mano 7 | T1 (8) | T2 (9) | T3 (10) | T5 (12) | T8 (15) |
|---|---|---|---|---|---|---|
| 1 | 0,117 | 0,133 | 0,150 | 0,167 | 0,200 | 0,250 |
| 2 | 0,221 | 0,251 | 0,280 | 0,308 | 0,363 | 0,441 |
| 3 | 0,315 | 0,354 | 0,391 | 0,427 | 0,495 | 0,585 |
| 4 | **0,399** | 0,445 | 0,488 | 0,528 | 0,601 | 0,694 |
| 6 | 0,541 | 0,593 | 0,640 | 0,683 | 0,755 | 0,837 |
| 8 | 0,654 | 0,706 | 0,751 | 0,790 | 0,853 | 0,916 |

**Rendimientos decrecientes** (mano de 7): la 2ª copia añade +10,5 pts, la 4ª +8,4, la
8ª +5,3. Es la misma observación que hacen los jugadores: «going from 5 to 6 supporters
leads to an increase of 6.72%; the jump from 14 to 15 supporters is a meager 2.07%».
<https://forums.sixprizes.com/t/stats-on-starts-hypergeometric-distribution-and-the-pokemon-tcg/3465>
(citado vía búsqueda; el foro no resuelve DNS desde aquí).

**Umbral de torneo citado**: «for a key combo piece, anything above **50%** for the
opening hand is considered *consistent enough*, given the existence of search cards».
<https://cal3.calculator.city/pokemon-tcg-calculator/>
→ Ninguna carta a 4 copias llega sola al 50% (0,399). Por eso la pieza clave NO se busca
con copias, se busca con **buscadores**: 4 copias + 4 buscadores ≈ 8 outs ≈ 0,654.

### 4.2 «¿Y si me la premian?»

P(que TODAS las copias caigan en los 6 premios):

| copias | P(todas premiadas) |
|---|---|
| 1 | **0,100** |
| 2 | 0,0085 |
| 3 | 0,00058 |
| 4 | 0,00003 |

**Este es el número que justifica los ratios de 2 en vez de 1**: una carta a 1 copia es
inaccesible el **10% de las partidas** solo por premios, antes incluso de robarla. Es la
razón real por la que las listas de torneo llevan «2 Boss's Orders» y no 1, y por la que
el ACE SPEC (obligatoriamente 1 copia) se elige entre cartas que **no son el plan A**.

### 4.3 Mulligan

P(mano de 7 sin básico) = C(60−B,7)/C(60,7):

| B básicos | 4 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 15 |
|---|---|---|---|---|---|---|---|---|---|
| P(mulligan) | 0,601 | 0,459 | 0,399 | 0,346 | 0,300 | **0,259** | 0,222 | 0,191 | 0,118 |

Cada básico añadido cuesta ~4-5 puntos de mulligan. En nuestro motor el mulligan no
pierde la partida (se re-roba), pero **revela la mano entera al rival y le regala 1 robo
por cada mulligan** (`motor-mecanica.md` §3) — o sea, información + tempo.

**Objetivo del campo real: 9-11 básicos → 22-30% de mulligan.** Media del campo 9,6
básicos (28,8%); media nuestra 8,0 (34,8%). Estamos 6 puntos peor de media y regalamos
información en 1 de cada 3 partidas.

Extremos instructivos del propio campo: `x1-slowking` lleva **15 básicos** (11,8% de
mulligan) y `c6-ogerpon` lleva **4** (60,1%): esa lista acepta un mulligan de dos de cada
tres partidas a cambio de 20 energías y un único atacante básico autoacelerado. Es una
apuesta consciente, no un descuido — pero es exactamente el tipo de lista que un Model
Score que premia consistencia debe evitar.

---

## 5. Consistencia frente a potencia: cómo se mide

Definición operativa de SixPrizes: **consistencia** = «the ability of a deck to set up
and to do what you want it to do»; **robustez** = «withstand various stresses during the
game and continue to function» (KOs, descarte de energía, disrupción de mano).
<https://sixprizes.com/2013/01/20/robustness-a-topic-of/>

Métricas que usa un jugador, con el número equivalente en nuestro motor:

| Métrica | Cómo se calcula | Objetivo |
|---|---|---|
| Mulligan rate | hipergeométrica §4.3 | ≤ 30% (9+ básicos) |
| «Puedo empezar»: básico + arranque en mano | ⚠️ **mal planteada, ver §5bis** — la buena es P(motor ≥1 \| hay básico) | ≥ 0,90 (publicado: 0,9036) |
| Setup al T2 | P(atacante + energía + buscador vistos en 9 cartas) | ≥ 0,70 |
| Dead draws | E[cartas no jugables en la mano de 7] | minimizar; energía sobrante es el mayor sumidero |
| Turnos sin Supporter que aguanta | «a real measure of a deck is the number of turns that it can survive without a Supporter» | ≥ 2 |

Tres advertencias de las fuentes que aplican directo a nuestro caso:

1. **Sobre-consistencia**: «running excessive consistency cards leaves insufficient deck
   space for powerful threats» (SixPrizes, ídem). Hay un punto donde la 15ª carta de robo
   ya solo aporta 2 puntos y esa ranura vale más como atacante.
2. **La probabilidad no garantiza**: «even with a 90% success rate, you will fail 1 out
   of 10 times, and in a 9-round tournament that means you might brick in one entire
   match solely due to variance».
   <https://cal3.calculator.city/pokemon-tcg-calculator/> — relevante para el writeup: la
   consistencia se demuestra con **muchas partidas**, no con una racha.
3. **Recursos en juego > recursos en mano**: lo que ya está en la mesa no lo puede
   quitar un Judge/Iono. Traducción a construcción: preferir motores que viven en el
   campo (habilidades) a motores que viven en la mano — **con la salvedad de nuestro
   piloto**, ver §8.4.

---

## 5bis. La métrica de consistencia, bien planteada (corrige el §5)

El §5 pedía «P(≥1 básico) × P(≥1 motor) ≥ 0,90 conjunta». **Ese objetivo está mal
puesto**: la conjunta cruda no llega a 0,90 en ninguna lista jugable (el campo entero va
de 0,35 a 0,82), porque está multiplicando por el mulligan. Y el mulligan **no es un
fracaso en nuestro motor: se re-roba**. Lo que hay que medir es lo que pasa *en la mano
con la que efectivamente juegas*:

> **P(motor ≥ 1 | hay al menos un básico)** = P(básico ∧ motor) / P(básico)

Ese es además el número que publica la literatura: SixPrizes calcula para un mazo de
Keldeo un **90,36%** de empezar con al menos un Supporter y lo trata como el estándar de
un mazo bien construido.
<https://sixprizes.com/2013/01/13/themathtcg-the-probabilities-behind/>

| Grupo | P(motor \| básico), media | rango |
|---|---|---|
| **propios (9)** | **0,928** | 0,859 (`abomasnow-plus`) – 0,966 (`tr-mewtwo`) |
| meta (6) | 0,896 | 0,863 – 0,929 |
| campo (15) | 0,901 | 0,780 (`c5`) – 0,960 (`c4`/`x5`) |

**Conclusión que cambia el diagnóstico: la consistencia de arranque NO es nuestro
problema.** Estamos por encima del campo y por encima del listón publicado. Todas las
listas propias salvo `abomasnow-plus` (0,859) y `ns-zekrom` (0,861) pasan el 90%.

### El motor está en el tipo de carta equivocado

Donde sí nos separamos del campo es en **con qué** conseguimos esa consistencia:

| | Supporters | de robo | Items | motor total (robo+búsqueda) |
|---|---|---|---|---|
| **propios (9)** | **14,1** | **9,6** | 14,4 | 19,7 |
| meta (6) | 12,0 | 3,5 | 17,3 | 16,5 |
| campo (15) | 11,7 | 4,9 | 17,4 | 17,2 |

Llevamos **el doble de supporters de robo que el campo** (9,6 vs 4,9) y ~3 Items menos.
El canon de JustInBasil para robo es **4-9**; el campo vive en 4-5; nosotros en 9,6, por
encima del techo. Y esto **no compra nada**, porque el motor total ya es mayor que el del
campo (19,7 vs 17,2): son cartas redundantes que compiten por la única ranura de
Supporter del turno.

Coste exacto: E[Supporters en la mano de 7] = 7·S/60 → **1,65 nuestros vs 1,37 el campo**,
y solo se juega **1 por turno**. La diferencia es carta muerta pura, y se acumula con la
energía sobrante del §3 (2,08 vs 1,25 energías por mano).

> **Cartas estructuralmente muertas en la mano inicial** (energía por encima de 1 +
> supporter por encima de 1): nosotros ≈ **1,73**; el campo ≈ **0,62**. De 7 cartas.

El campo consigue lo mismo con Items (Poké Pad, Buddy-Buddy Poffin, Bug Catching Set) y
con **habilidades**: `c2-alakazam` lleva **0 supporters de robo** — roba con Dudunsparce
(Run Away Draw) y Fezandipiti ex. Es el principio «recursos en juego > en mano» del §5.3
llevado al extremo. (Ojo al §8.4: ese camino hoy nos está vetado por el piloto.)

---

## 5ter. Estadios: la categoría que hemos ignorado entera

Regla publicada: **2-3 estadios** en un mazo competitivo; más de 3 es excesivo porque
solo puede haber uno en juego. JustInBasil da el mismo 2-3 en el esqueleto.
<https://www.finetoys.ca/blogs/news/competitive-pokemon-tcg-guide> ·
<https://www.justinbasil.com/guide/deck-structure>

El punto que hace de esto una regla y no un adorno: **un estadio nuevo destruye el que
haya en juego**. Si llevas 0 estadios, el estadio del rival se queda puesto toda la
partida y no tienes ninguna respuesta. Es una asimetría gratuita.

| | estadios/lista | listas con 0 |
|---|---|---|
| **propios (9)** | **1,33** | **4 de 9** (`ethans-hooh`, `mega-kangaskhan`, `mega-lucario`, `okidogi`) |
| meta (6) | 1,83 | 1 de 6 |
| campo (15) | **2,53** | 2 de 15 (las dos son la misma lista de Lucario) |

Cuatro de nuestras nueve listas **no pueden quitar nunca un estadio rival**. Y el campo
juega estadios de verdad: `c1`/`c8`/`x1`/`x2`/`x6` llevan **4**.

Esto se cruza con el §7(b): **Gravity Mountain 1252** (−30 HP a todo Stage 2) pega al
57,6% del campo, la lista de torneo de Zhao lleva **2**, y nosotros llevamos **0** —
y encima en la lista donde más barato nos sale, porque no tenemos Stage 2 propios.

---

## 6. Cartas técnicas, «silver bullets» y la elección del ACE SPEC

### 6.1 Criterio de una copia

- Un silver bullet «can drastically alter a specific matchup and can generally be played
  in small counts»; y la regla de oro: «**don't disrupt your main strategy** — make sure
  the main strategy of your deck is still consistent, so that your matchup specific techs
  don't weigh you down and make you lose to something else».
  <https://sixprizes.com/2011/06/29/silver-bullets-tricky-ways-kill-top-decks/>
- JustInBasil sobre one-ofs: solo merecen ranura si el Pokémon (a) busca su propia
  evolución, (b) tiene retirada 0 o retirada gratis por habilidad, (c) busca otros
  Pokémon, (d) provoca condiciones especiales, (e) roba cartas, o (f) reduce daño / tiene
  HP superior. <https://www.justinbasil.com/guide/crafting-your-deck>
- Proceso de recorte del mismo autor, en orden: comprobar el esqueleto → adelgazar líneas
  evolutivas → consolidar roles → reducir redundancia funcional → **eliminar one-ofs que
  hagan lo mismo** → bajar de 4 a 3 copias.

### 6.2 Regla numérica del tech (derivada, para el writeup)

Una carta técnica vale la ranura si

> `share(emparejamiento) × Δ(winrate en ese emparejamiento) > dilución`

con `dilución ≈ 0,5-1 punto` de winrate global por ranura quitada al motor. Anclaje
publicado del orden de magnitud: «one copy of a specific tech card can swing Magnezone
matchups from **42% to 52%** — that's three extra wins per twenty-game tournament».
<https://pokecardfinder.com/best-pokemon-tcg-deck-2026/>

Con nuestro censo (§7) el umbral sale así:

| Rival | share | Δ WR necesario para pagar 1 ranura |
|---|---|---|
| Grimmsnarl | 31,2% | **> 3,2 pts** |
| Alakazam | 18,2% | > 5,5 pts |
| Lopunny/Froslass | 12,8% | > 7,8 pts |
| Dragapult | 8,2% | > 12 pts |
| Mega Lucario | 4,0% | > 25 pts → **nunca** una ranura dedicada |

### 6.3 ACE SPEC: 29 en el pool, 1 por baraja

El criterio del jugador es simple y nuestro shell lo viola: **el ACE SPEC no puede ser
una carta que ya haces con 4 copias de otra cosa**, porque es 1 sola copia (10% de
premiada, 11,7% de verla en la mano inicial). Se reserva para un efecto que **ninguna
otra carta del pool da**.

Las 29 del pool, agrupadas por lo que aportan:

| Grupo | Cartas |
|---|---|
| Robo/reset explosivo | **Unfair Stamp 1080** (tras un KO: ambos rebarajan, tú robas), Enriching Energy 13 (energía {C} + robar 4) |
| Gusting / posicionamiento | **Prime Catcher 1088** (gust + cambio propio), Scramble Switch 1107, Scoop Up Cyclone 1093 |
| Búsqueda | Master Ball 1125, Precious Trolley 1126, Secret Box 1092, Hyper Aroma 1082, Energy Search Pro 1100, Treasure Tracker 1111, Grand Tree 1249 |
| Supervivencia | **Hero's Cape 1159** (+100 HP), Survival Brace 1155, Poké Vital A 1096, Amulet of Hope 1169 |
| Daño | **Maximum Belt 1158** (+50 contra ex), Deluxe Bomb 1167, Dangerous Laser 1095 |
| Odio / control | **Neutralization Zone 1247** (los ex no dañan a los sin Rule Box), Megaton Blower 1104, Brilliant Blender 1128, Jamming-adyacentes |
| Recuperación | Max Rod 1110, Miracle Headset 1109, Reboot Pod 1089 |
| Energía comodín | Neo Upper 10, Legacy 12 |
| Nicho | Awakening Drum 1085 (Ancient), Sparkling Crystal 1165 (Tera) |

**Uso real en papel** (rankings de torneo): Unfair Stamp 15,63% (1.701 mazos), Hero's
Cape 6,83%, Maximum Belt 3,62%; Prime Catcher descrito como «the best Ace Spec card
simply because of its ability to mess with your opponent's field».
<https://pokemoncard.io/category/best-ace-spec-cards> (403 al fetch; datos vía búsqueda) ·
<https://bulbapedia.bulbagarden.net/wiki/ACE_SPEC_card_(TCG)>

**Uso real en NUESTRO campo** — censo completo sobre las 30 listas, verificado
2026-08-11 contra la columna `rule` (las 21 que no son nuestras: `campo/` + `meta/`):

| ACE SPEC | listas rivales (de 21) | listas nuestras (de 9) |
|---|---|---|
| **Unfair Stamp 1080** | **10 (48%)** | 0 |
| Hero's Cape 1159 | 5 | 1 (`mega-kangaskhan`) |
| Enriching Energy 13 | 2 | 0 |
| Neutralization Zone 1247 | 2 | 0 |
| Prime Catcher 1088 | 1 | 0 |
| Max Rod 1110 | 1 | 0 |
| Precious Trolley 1126 | 0 | 1 (`abomasnow-plus`) |
| **Master Ball 1125** | **0** | **7** |
| las otras 21 del pool | 0 | 0 |

**Nosotros llevamos Master Ball en 7 de 9 listas y nadie más la juega en ninguna de las
21 restantes.** Es la peor elección posible del grupo: duplica lo que ya hacen 4 Ultra
Ball / 4 Poké Pad / 4 Mega Signal, con 1 sola copia (11,7% de verla, 10% de premiada).
Cero listas del campo y cero listas de torneo la juegan. **Y en el arquetipo que sí
tenemos documentado en torneo, Zhao juega Maximum Belt 1158** (verificado en la lista
completa, §1bis) — una carta que ninguna de las 30 listas de nuestro corpus lleva.

Nota de lectura para el writeup: que el 48% del campo converja en Unfair Stamp y nosotros
en una carta que juega el 0% es, por sí solo, la señal de «no conocemos el juego» más
visible de toda nuestra construcción — y es la más barata de arreglar (1 carta).

⚠️ **Corrección al catálogo interno**: `lab-barajas.md` §1 dice «1080/1092/1125/1126/**1129**/1159
son ACE SPEC». **Sacred Ash 1129 NO es ACE SPEC** en este pool (`rule` vacío) y faltan 23:
10, 12, 13, 1082, 1085, 1088, 1089, 1093, 1095, 1096, 1100, 1104, 1107, 1109, 1110, 1111,
1128, 1155, 1158, 1165, 1167, 1169, 1247, 1249. Por eso `c8-dipplin` puede llevar Unfair
Stamp **y** Sacred Ash sin ser ilegal.

⚠️ **Sin verificar**: `motor-mecanica.md` §2 solo documenta errorType 1 (ID desconocido),
2 (exceso de copias) y 3 (sin básico). **No hay evidencia de que el motor imponga el
límite de 1 ACE SPEC.** Sonda barata: `battle_start` con una baraja que lleve 1080 y 1125
a la vez. Aunque el motor lo permita, **respetarlo**: el jurado incluye 3 personas de The
Pokémon Company y una lista con 2 ACE SPEC lee como «no conoce el juego» → tira el 20% de
Deck Score.

---

## 7. Adaptación al meta con el censo real

Distribución (`baraja-vs-campo.md`, 18.674 barajas; los 8 arquetipos cubren 89,8%):

| Rival | share | Win condition | HP | Debilidad | Retirada |
|---|---|---|---|---|---|
| c1 Marnie's Grimmsnarl ex | **31,2%** | Grimmsnarl ex (**St2**) | 320 | **{G}** | 2 |
| c2 Alakazam | **18,2%** | Alakazam (**St2**) | **140** | **{D}** | 1 |
| c3 Lopunny/Froslass | 12,8% | Mega Lopunny ex / Mega Froslass ex | 330 / 310 | {F} / {M} | 1 |
| c4 Dragapult ex | 8,2% | Dragapult ex (**St2**) | 320 | **ninguna** | 1 |
| c5 Kangaskhan/Crustle | 6,9% | Mega Kangaskhan ex | 300 | {F} | 3 |
| c6 Teal Mask Ogerpon ex | 5,0% | Ogerpon ex | 210 | {R} | 1 |
| c7 Mega Lucario ex | 4,0% | Mega Lucario ex | 340 | {P} | 2 |
| c8 Dipplin/Grookey | 3,5% | Dipplin / Thwackey | 80 / 100 | {R} | 2 |

Tres lecturas que se convierten en decisiones de construcción:

**(a) Tipo de nuestro atacante.** Share del campo golpeado por debilidad:
{G} 31,2% · {F} 19,7% · {D} 18,2% · {R} 8,5% · {P} 4,0% · sin debilidad 8,2%.
El tipo que más rinde contra ESTE campo es **{G}**, no {F} — al revés de lo que sugiere
el conteo global del pool (`cartas-pool.md` §2 decía que {R} y {F} explotan más
debilidades, pero eso cuenta las 1.267 cartas, no el campo real).

**(b) El 57,6% del campo gana con un Stage 2** (Grimmsnarl 31,2 + Alakazam 18,2 +
Dragapult 8,2). **Gravity Mountain 1252** («Each Stage 2 Pokémon in play gets −30 HP»)
pega a los tres, y en Alakazam es brutal: 140 → **110 HP**. Ninguna de nuestras 9 listas
lleva Stage 2 salvo `ethans-hooh` (2 Typhlosion) → el estadio es casi **simétrico a
nuestro favor**. Umbral del §6.2 cubierto de sobra (57,6% × cualquier Δ > 1,7 pts).
Las listas de torneo de Lucario ya lo llevan (Zhao 2, Du 1) y `meta/lucario-sample` 2.
**Es el tech número 1 disponible y lo tenemos a 0 copias.**

**(c) El 42,9% del campo depende de energía especial**: c2 (4 Telepath + 1 Enriching),
c3 (4 Mist + 1 Enriching), c5 (**12 de 13 energías especiales**), c6 (2 Grow Grass).
**Enhanced Hammer 1081** (descarta 1 especial, sin moneda) es un 1-2 de que gana solo la
partida contra c5 y muerde a c2/c3. Umbral cubierto (42,9%).

**(d) Alakazam (18,2%) ataca con Powerful Hand: «2 damage counters por carta en TU
mano»**. Es decir, su daño escala con el tamaño de nuestra mano. Construir con mano
pequeña (menos supporters de robo masivo tipo Lillie 8, más Items que se vacían) y llevar
**Xerosic's Machinations 1197 / Hand Trimmer 1087 / Judge 1213** es a la vez consistencia
y odio. El campo ya lo sabe: c2 lleva 3 Xerosic, c5 lleva 4.

---

## 8. Crítica de nuestras 9 listas, con números

Comparativa agregada (medias):

| | Pokémon | básicos | mulligan | Trainers | Energía | E[energía en mano 7] | motor* | disrupción |
|---|---|---|---|---|---|---|---|---|
| **propios (9)** | **11,1** | **8,0** | **0,348** | 31,1 | **17,8** | **2,07** | 20,6 | **0,0** |
| meta (6) | 16,7 | 9,0 | 0,303 | 32,0 | 11,3 | 1,32 | 19,0 | 2,2 |
| campo (15) | 16,3 | 9,6 | 0,288 | 33,0 | 10,7 | 1,25 | 18,9 | 2,9 |
| torneo real (4 listas MEG) | 16-19 | — | — | 32 | 9-12 | — | — | sí |

\* motor = supporters de robo + supporters de búsqueda + items de búsqueda.

Ampliación 2026-08-11 (columnas que faltaban):

| | Supporters | de robo | Items | Estadios | Pk de 2 premios | objetivos Poké Pad | P(motor\|básico) |
|---|---|---|---|---|---|---|---|
| **propios (9)** | 14,1 | **9,6** | 14,4 | **1,33** | **32,8%** | **7,6** | 0,928 |
| meta (6) | 12,0 | 3,5 | 17,3 | 1,83 | 12,9% | 14,5 | 0,896 |
| campo (15) | 11,7 | 4,9 | 17,4 | 2,53 | 27,9% | 12,5 | 0,901 |

### 8.0 La desviación que faltaba: regalamos premios

Esta es, en números, la diferencia más grande entre nuestras listas y las de torneo, y la
nota original solo la mencionaba de pasada.

**El principio.** Un Pokémon ex da **2 premios** al ser noqueado; uno normal, **1**. Con
6 premios, un rival necesita **3 KOs** contra un tablero de ex y **6 KOs** contra un
tablero de un premio. JustInBasil lo enuncia así: los atacantes multi-premio «trade
additional attack power, utility, and/or hit points for the extra prizes they give up
when knocked out», y por eso «it is not uncommon for these decks to include one or more
**Single-Prize Attackers**».
<https://www.justinbasil.com/guide/secondary-attackers>

El mapa de premios estándar del formato es el **«2-2-2»**: el rival planea tres KOs sobre
tres Pokémon de dos premios. La contramedida de construcción es obligarle a un mapa de
seis casillas. Regla operativa citada: «Do not bench a multi-prize Pokémon unless you
absolutely have to or plan to use it that turn. Every Pokémon you bench is a potential
part of your opponent's prize map».
<https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-trade-guide-advanced-prize-mapping>

**Nuestro número.** Fracción de los Pokémon de la lista que dan 2 premios:

| Lista | Pk | de 2 premios | % |
|---|---|---|---|
| **`propios/mega-lucario`** | 12 | **8** | **67%** ← el máximo de las 30 listas |
| `propios/okidogi` | 8 | 4 | 50% |
| `propios/mega-kangaskhan` | 10 | 4 | 40% |
| `propios/abomasnow-plus` | 11 | 4 | 36% |
| `propios/ethans-hooh` | 12 | 4 | 33% |
| — media propios — | | | **32,8%** |
| — media campo — | | | 27,9% |
| — media `meta/` (kernels) — | | | **12,9%** |
| `campo/c7-lucario-campo` | 16 | 4 | 25% |
| **Zhao, Turin 43º** | 18 | **3** | **17%** |
| `campo/c1-grimmsnarl` | 18 | 3 | 17% |
| `campo/c2-alakazam` | 19 | 1 | **5%** |

`c6-ogerpon` sale al 100%, pero es la lista de 4 Pokémon con 60,1% de mulligan: es la
apuesta extrema, no el modelo.

**Por qué esto pesa en el Model Score y no solo en el Deck Score.** Contra `mega-lucario`
el rival gana con **3 KOs**. Nuestro atacante tiene 340 HP, pero la lista mete **4
Regirock ex** (230 HP, retirada 3) en la banca, y cada uno es una casilla de dos premios
del mapa del rival. La versión del campo y la de torneo ponen ahí Solrock, Lunatone,
Makuhita y Dunsparce: **un premio cada uno, retirada 1**. Con la misma carta ganadora, el
rival necesita el doble de KOs contra ellos que contra nosotros.

Es exactamente el patrón que explica «perdemos de forma consistente sin depender del
emparejamiento»: no es que perdamos los intercambios, es que **cada intercambio que
perdemos vale el doble**.

### 8.1 Las cuatro desviaciones gordas

**D1 — Sobran ~7 energías y faltan ~5 Pokémon.** 17,8 vs 10,7. Es la desviación número
uno y explica sola una parte del «juega mecánico»: abrimos con 2,07 energías de media
y solo podemos adjuntar 1 por turno. Peor caso `abomasnow-plus` con **28** (3,27 por
mano). Segunda peor `mega-lucario` con **19** cuando el ataque de referencia cuesta
**1 {F}** y él mismo acelera 3 del descarte; la lista de Turin lleva **10** y la de NAIC
**12**.

**D2 — Cero disrupción en 9 de 9.** El campo lleva de 1 a 8 cartas (Judge, Xerosic's
Machinations, Crushing/Enhanced Hammer, Hand Trimmer, Unfair Stamp). Nosotros 0. En un
formato donde el 18,2% del campo (Alakazam) escala su daño con el tamaño de *nuestra*
mano y el 42,9% depende de energía especial, esto es dejar puntos en la mesa. Un jurado
que conoce el juego lo lee como lista incompleta.

**D3 — Cartas del shell que el campo juega y nosotros no llevamos NUNCA.**

| Carta | copias en el campo (15 listas) | listas que la llevan | nuestras 9 listas |
|---|---|---|---|
| **Poké Pad 1152** (busca Pokémon sin Rule Box, sin coste) | **48** | **13/15** | **0** |
| Hilda 1225 (busca **evolución + energía**) | 15 | 5 | 0 |
| Judge 1213 (reset 4/4) | 14 | 5 | 0 |
| Bug Catching Set 1094 | 16 | 4 | 0 |
| Crushing Hammer 1120 | 12 | 3 | 0 |
| Xerosic's Machinations 1197 | 9 | 4 | 0 |
| Unfair Stamp 1080 (ACE) | 8 | 8 | 0 |
| Dawn 1231 (busca básico+St1+St2) | 8 | 5 | 0 |
| Rare Candy 1079 | 6 | 2 | 0 |
| Gravity Mountain 1252 | 0 (pero 2 en `meta/lucario-sample` y en las listas de torneo) | — | 0 |

**Poké Pad es el agujero más caro**: 4 copias gratis que buscan cualquier Pokémon sin
Rule Box, frente a Ultra Ball que cuesta **descartar 2 cartas de la mano**. Objetivos sin
Rule Box en nuestras listas: `hops-snorlax` 12, `iono-bellibolt` 11, `ethans-hooh` 8,
`ns-zekrom` 8, `tr-mewtwo` 8, `abomasnow-plus` 7, `mega-kangaskhan` 6, `mega-lucario` 4,
`okidogi` 4. En las 7 primeras Poké Pad es un 4-de obvio.

**D4 — El ACE SPEC mal elegido** (§6.3): Master Ball en 7/9. Cero listas del campo o de
torneo lo juegan.

### 8.2 Desviaciones por baraja

| Baraja | Pk | bás | Tr | En | Sup | Diagnóstico numérico |
|---|---|---|---|---|---|---|
| `abomasnow-plus` | 11 | 7 | 21 | **28** | 8 | 21 Trainers (mínimo del campo: 24). 28 energías = 3,27/mano. Es la tragaperras del motor con lápiz de labios; para Model Score es la peor. |
| `ethans-hooh` | 12 | 7 | 32 | 16 | **20** | **20 Supporters** con 1 por turno: el campo va de 8 a 15 y JustInBasil dice 6-12. Sobran ~6. Además Shining Feathers cuesta **{R}×4** → cota §3 = 21,8 sin ayuda; con 4 Adventure + 3 Firebreather está cubierto, pero entonces sobran energías EN MANO. |
| `hops-snorlax` | 12 | 9 | 32 | 16 | 12 | La más cercana al canon. Con Choice Band el coste real baja a 2 {C} → cota 13,3; 16 son 3 de más. 12 objetivos de Poké Pad y 0 copias. |
| `iono-bellibolt` | 14 | 9 | 30 | 16 | 13 | Aceleración ILIMITADA desde la mano (Electric Streamer) → aquí sí quiere energía alta; correcto. Pero **el heurístico ignora el type 10** (`lab-barajas.md` §3): sin habilidad, la lista queda con 16 energías y ningún motor. Elegirla exige arreglar el piloto primero. |
| `mega-kangaskhan` | 10 | 7 | 34 | 16 | 14 | 7 básicos = 39,9% de mulligan en una lista **cuyo único atacante es básico**. La versión del campo (`c5`) tiene el mismo problema (7) pero compensa con 12 energías especiales y 8 cartas de disrupción. |
| `mega-lucario` | 12 | 8 | 29 | **19** | 14 | La desviación más medible del lote: 19 energías vs **10-12** en las listas de torneo con la misma carta; 4 Pokémon sin Rule Box vs 12 en `c7`; 0 Poké Pad vs 4; 0 Hilda vs 3; 0 Judge vs 3-4; 0 Gravity Mountain vs 1-2. Y llevamos 4 Regirock ex (**2 premios cada uno**) donde el campo lleva 3 Solrock + 2 Lunatone + 2 Makuhita + 2 Hariyama (single-prize + gust al evolucionar). |
| `ns-zekrom` | 10 | 8 | 32 | 18 | 14 | Rampaging Thunder = {R}{L}{L}{C}: coste 4 **de dos colores**. Cota §3 = 21,8 y encima repartida. 18 se queda corto para el plan A y sobra para el plan B. O sube a 20-22 con 4 PP Up, o cambia de atacante. |
| `okidogi` | **8** | 8 | 37 | 15 | 16 | **8 Pokémon, la mitad del campo (16,3)**; 0 líneas evolutivas; 37 Trainers (máximo del campo 37). 16 Supporters con 1/turno. La lista es un shell con dos atacantes. |
| `tr-mewtwo` | 11 | 9 | 33 | 16 | 16 | Erasure Ball {P}{P}{C} = 3 → cota 18; llevan 16 (12 {P} + 4 TR) y el descarte de energía de banca es coste extra. Justificable, pero 16 Supporters otra vez. |

### 8.3 Las tres reglas que estamos rompiendo, enunciadas

1. **«Si un Item y un Supporter hacen lo mismo, va el Item»** (JustInBasil). Llevamos
   14-20 Supporters en 7 de 9 listas cuando solo se juega **1 por turno**. Con 16
   Supporters, E[en la mano de 7] = 1,87 → casi 1 carta muerta por mano, cada mano.
   El campo resuelve esto con **Poké Pad + Buddy-Buddy Poffin + Bug Catching Set**
   (Items) donde nosotros ponemos supporters de búsqueda.
2. **La energía no se cuenta «por si acaso», se cuenta contra el coste de ataque real
   corregido por búsqueda y aceleración** (§3). Nuestras listas cuentan por el coste
   nominal del ataque grande, no por el ataque que se usa el 80% de los turnos.
3. **El ACE SPEC no repite lo que ya haces a 4 copias** (§6.3).

### 8.4 La regla que sí estamos aplicando bien, y hay que decirla en el writeup

`cartas-pool.md` §6 eligió arquetipos con **aceleración determinista y sin monedas**, y
`lab-barajas.md` §3 documentó que el piloto ignora el option type 10 (habilidades). Eso
es **construir la baraja para el piloto que tienes**, que es un argumento de Deck Score
de primera: «elegimos A1/A5 porque su motor vive en el ataque y en Items, no en
habilidades que nuestro agente aún no activa». Hay que decirlo explícitamente y
cuantificado, no dejarlo implícito.

### 8.5 El experimento controlado: tres Mega Lucario, mismo pool

Mismo arquetipo, mismas cartas disponibles, tres constructores distintos. Esta tabla vale
por sí sola como figura del writeup: aísla «conocimiento de juego» de todo lo demás.

| | `propios/mega-lucario` | `campo/c7` (ladder) | **Zhao, Turin 43º** |
|---|---|---|---|
| Pokémon | 12 | 16 | **18** |
| Básicos | 8 | 10 | **12** |
| Mulligan | 0,346 | 0,259 | **0,191** |
| Trainers | 29 | 31 | **32** |
| Energía | **19** | 13 | **10** |
| E[energía en mano 7] | **2,22** | 1,52 | 1,17 |
| Supporters | 14 | 12 | 10 |
| — de robo | **10** | 8 | 4 |
| Pk de 2 premios | **8 (67%)** | 4 (25%) | 3 (17%) |
| Objetivos de Poké Pad | **4** | 12 | 13 |
| Poké Pad | **0** | 4 | 4 |
| Ultra Ball | 4 | 4 | **2** |
| Premium Power Pro | 2 | 4 | 4 |
| Estadios | **0** | 0 | 2 (Gravity Mountain) |
| Disrupción | **0** | 4 (Judge) | 1 (Special Red Card) |
| ACE SPEC | **Master Ball** | Hero's Cape | **Maximum Belt** |
| Copias del atacante | 4 | 4 | **3** |

**Lo que enseña, en una frase**: los tres juegan la misma carta ganadora; nosotros
gastamos **9 cartas de más en energía** y **4 ranuras en Regirock ex** para pagarlas, y
las sacamos de Pokémon de un premio, del estadio, de la disrupción y del buscador gratis.
Las 9 energías sobrantes y los 4 Regirock son, casi exactamente, **las 13 cartas** que
separan nuestra lista de la de Zhao.

**El bucle causal que explica el ACE SPEC**: llevamos Master Ball (buscador genérico)
porque solo tenemos 4 objetivos de Poké Pad; tenemos 4 objetivos porque llenamos la banca
de ex; llenamos la banca de ex porque Regirock ex es nuestro acelerador; necesitamos
acelerador porque llevamos 19 energías en vez de 10. **Se arregla tirando del primer
hilo: la energía.**

---

## 9. Cambios concretos propuestos (sin tocar nada todavía)

Shell común corregido, calcado del consenso campo+torneo (33 Trainers):

```
4 Poké Pad 1152            ← el hueco más caro (48 copias en 13/15 listas del campo)
4 Ultra Ball 1121          (bajar a 3 si la lista no quiere descartar)
2-3 Buddy-Buddy Poffin 1086 solo si hay ≥6 básicos de ≤70 HP
4 Lillie's Determination 1227
3-4 Cheren 1224 / Urbain 1236 (robo 3 incondicional)
2-3 Boss's Orders 1182     (canon 2-4)
2-3 Judge 1213 o Xerosic's Machinations 1197   ← disrupción, hoy a 0
2 Night Stretcher 1097
1-2 Switch 1123
1-2 Gravity Mountain 1252  ← pega al 57,6% del campo, casi gratis para nosotros
1 Enhanced Hammer 1081     ← muerde al 42,9% del campo
1 ACE SPEC = Unfair Stamp 1080 (por defecto) / Hero's Cape 1159 (si el atacante es un
  muro de HP) / Prime Catcher 1088 (si el plan es gustear)
```

Prioridad 1 — **`mega-lucario`** (nuestra lista mejor medida y el arquetipo con lista
de torneo real que copiar): bajar **19 → 12 {F}**; sacar 2 Regirock ex (2 premios);
meter **4 Poké Pad**, **3 Hilda 1225**, **2 Gravity Mountain**, subir a **9-10 básicos**
con Solrock/Lunatone (Lunar Cycle roba 3 descartando una {F} — convierte la energía
sobrante en robo, que es exactamente nuestro problema D1); ACE SPEC Master Ball →
**Maximum Belt 1158** (+50 contra ex: el 100% de las win conditions del campo son ex o
St2) o Unfair Stamp.

Prioridad 2 — **`okidogi`**: 8 → 12-14 Pokémon; 15 → 12 {D}; añadir 4 Poké Pad (hoy solo
4 objetivos sin Rule Box: subir Murkrow a 4 y meter un básico {D} más los hace vivos);
bajar de 16 a 12-13 Supporters.

Prioridad 3 — **`ethans-hooh`**: 20 → 13-14 Supporters, la diferencia a Items.

**No tocar sin medir**: `iono-bellibolt` (su energía alta es correcta, el problema es el
piloto) y `abomasnow-plus` (es sparring, no candidata).

### 9bis. ⚠️ Corrección al §9: media lista de Zhao no la puede pilotar nuestro agente

Al verificar carta por carta (2026-08-11) aparece un filtro que el §9 no aplicaba. El
paquete de apoyo que usan Zhao y el campo **vive en habilidades**, y `lab-barajas.md` §3
documenta que el heurístico **ignora el option type 10**. Texto exacto del CSV:

| Carta | Qué es | ¿La usa nuestro piloto? |
|---|---|---|
| **Lunatone 675** — *Lunar Cycle*: «Once during your turn, if you have Solrock in play, you may discard a Basic {F} Energy card from your hand… Draw 3 cards.» | **Habilidad (type 10)** | **NO** |
| **Hariyama 674** — *Heave-Ho Catcher*: gust al evolucionar | **Habilidad (type 10)** | **NO** |
| **Dudunsparce 66** — *Run Away Draw*: robar 3 | **Habilidad (type 10)** | **NO** |
| Solrock 676 — *Cosmic Beam* {F} 70, sin debilidad/resistencia, exige Lunatone en banca | **Ataque** | **SÍ** |
| Poké Pad 1152, Gravity Mountain 1252, Premium Power Pro 1141, Maximum Belt 1158 | Trainer/Estadio/Tool | **SÍ** (pendiente sonda) |

**El §9 se equivocaba al justificar Lunatone por Lunar Cycle**: bajo el piloto actual esa
habilidad no se activa nunca, así que Lunatone entra como un básico de 110 HP, un premio
y retirada 1 — **que sigue siendo mejor que Regirock ex para el §8.0**, pero por el motivo
contrario al que decía la nota. La conversión «energía sobrante → robo» **no ocurre**.

Reordenación que se deduce, en dos tramos:

**Tramo A — mejoras que funcionan con el piloto de hoy** (ninguna depende de type 10):

1. Energía **19 → 12** en `mega-lucario`. Aura Jab cuesta 1 {F} y *él mismo* recupera 3
   del descarte; 4 Fighting Gong buscan {F}. Es la palanca que libera las ranuras.
2. **4 Regirock ex → 3 Solrock + 2 Lunatone** (o + Makuhita). Baja los Pokémon de dos
   premios de 8 a 4 (**67% → 25%**) y sube los básicos de 8 a 10 (mulligan 0,346 → 0,259)
   y los objetivos de Poké Pad de 4 a 9.
3. **+4 Poké Pad 1152** — ya rentable con el paso 2.
4. **+2 Gravity Mountain 1252** — el 57,6% del campo gana con un Stage 2; nosotros no
   tenemos ninguno. Además rompe el estadio rival (§5ter).
5. **Robo 10 → 4-6 supporters**, la diferencia a Items (§5bis).
6. **ACE SPEC Master Ball → Maximum Belt 1158**, que es literalmente lo que juega Zhao.
7. **+2-4 Judge 1213** (Item-libre, sin habilidad) — disrupción, hoy a 0 en 9 de 9.

**Tramo B — bloqueado hasta que el piloto active el type 10**: Dudunsparce, Hariyama,
Lunar Cycle, y el arquetipo `iono-bellibolt` entero. **No meter estas cartas «porque las
lleva el campo»**: medirían peor que lo que tenemos. Y a la inversa: arreglar el type 10
es lo que desbloquea copiar el shell del campo tal cual, lo que lo convierte en la mejora
de piloto con más retorno (ya señalada en `lab-barajas.md` §3).

**Para el writeup, esto es un argumento, no una excusa**: «construimos para el piloto que
tenemos y lo cuantificamos» es Deck Score; presentar una lista copiada cuyo motor el
agente no sabe activar sería lo contrario.

---

## 10. Qué de todo esto NO aplica a nuestro simulador

- **Cartas que no existen en el pool.** Todas las guías citan Quick Ball, Professor's
  Research, Iono, Arven, Earthen Vessel, Dedenne-GX, Lumineon V, Forest Seal Stone,
  Battle VIP Pass… **Ninguna está en `cards_clean.csv`.** Cada carta que salga de una
  fuente hay que comprobarla contra el CSV antes de citarla. Los equivalentes reales de
  nuestro pool son: robo → Cheren 1224 / Urbain 1236 / Lillie's Determination 1227;
  búsqueda → Poké Pad 1152 / Ultra Ball 1121 / Buddy-Buddy Poffin 1086; gust →
  Boss's Orders 1182.
- **Todo lo de Pokémon TCG Pocket.** Varias fuentes de la búsqueda hablan de Pocket
  (mazos de 20 cartas, 3 premios, zona de energía automática, 1 punto por KO). **No es
  nuestro juego**: nosotros somos 60 cartas, 6 premios, banca de 5, energía desde la mano.
  Descartado explícitamente.
- **Listas de formatos rotados.** SixPrizes 2011/2013 y los ejemplos de JustInBasil
  (Welder, Marnie, Charizard-VMAX) son de eras antiguas: **los principios valen, los
  counts concretos de carta no**.
- **Regla de «1 Radiant por baraja»**: no hay Radiant en el pool.
- **Prize checking** (mirar los premios entre partidas de un match al 2-de-3): en Kaggle
  cada episodio es una partida suelta; no hay sideboard ni información entre partidas.
- **La moneda de inicio**: en papel se echa a suertes; en nuestro motor **el jugador 0
  SIEMPRE elige primero/segundo** (`motor-mecanica.md`, select (9,41)). Es una decisión,
  no azar, y la mitad de las partidas es nuestra.

---

## 11. Pendientes de verificación (baratos, alto valor)

1. **¿Impone el motor el límite de 1 ACE SPEC?** `battle_start` con 1080 + 1125 juntos.
   Aunque lo permita, respetarlo (§6.3).
2. **¿Implementa el motor la regla «el que va primero no juega Supporter en su primer
   turno»?** Esa regla existe en el juego real desde el 2020-02-21
   (<https://www.cardcaverntradingcards.com/blogs/news/new-turn-1-supporter-rule-change-what-you-need-to-know>)
   y el pool la presupone: **Carmine 1192** y **Team Rocket's Proton 1220** dicen
   literalmente «If you go first, you may use this card during your first turn». Sonda:
   ir primero y mirar si en el select (0,0) del turno 1 aparecen options de Supporter.
   Si la regla está implementada, cambia el cálculo de §4 (yendo primero solo se ven
   7+1 cartas sin poder usar el motor de robo) y hace de Carmine/Proton cartas
   estructurales, no técnicas.
3. **¿Implementa el motor Gravity Mountain 1252 y Enhanced Hammer 1081?** Son las dos
   recomendaciones de meta con más impacto (57,6% y 42,9% del campo) y aún no están en la
   lista de 36 cartas sondeadas de `lab-barajas.md` §4.
4. **¿Implementa Poké Pad 1152?** Es el cambio de shell más grande que propongo y no
   aparece en el chequeo de implementación. Ojo al precedente de **TR Great Ball 1132**,
   donde el motor implementa la carta real y no el texto del CSV (`lab-barajas.md` §4bis).
5. **Maximum Belt 1158** (el ACE SPEC de Zhao, §1bis) tampoco está sondeado. Es un Tool
   y el motor ya implementa bien Hero's Cape 1159 y Choice Band 1171 (`lab-barajas.md`
   §4), así que el prior es bueno, pero hay que verlo antes de meterlo en la lista final.
6. **Prioridad de sondeo**, por coste de equivocarse: 1152 Poké Pad → 1252 Gravity
   Mountain → 1158 Maximum Belt → 1213 Judge → 1081 Enhanced Hammer. Las cinco son
   Trainers sin habilidad, o sea **compatibles con el piloto actual** (§9bis), que es lo
   que las hace accionables ya.

**Cerrado en la revisión del 2026-08-11** (no repetir):

- ✅ Las **29 ACE SPEC** del pool y la lista exacta de IDs: verificadas contra la columna
  `rule`. **Sacred Ash 1129 NO es ACE SPEC**; la lista de 6 IDs de `lab-barajas.md` §1
  está incompleta y mal.
- ✅ **Ninguna de las 30 listas del corpus lleva 2 ACE SPEC**, así que la duda del punto 1
  no está bloqueando nada hoy: todas son legales bajo la regla de papel.
- ✅ La lista de **Victor Zhao (Turin, 43º)** existe, es de este pool y su contenido
  carta por carta está en §1bis. Su ACE SPEC es **Maximum Belt**.
- ✅ Todas las medias agregadas de §8 reproducen desde cero (§0).
- ✅ **Lunar Cycle (Lunatone), Heave-Ho Catcher (Hariyama) y Run Away Draw (Dudunsparce)
  son habilidades**, no ataques ni Trainers → fuera del alcance del piloto actual (§9bis).

---

## 12. Fuentes

- JustInBasil, *Deck Structure* — <https://www.justinbasil.com/guide/deck-structure>
- JustInBasil, *Crafting Your Deck* — <https://www.justinbasil.com/guide/crafting-your-deck>
- JustInBasil, *Consistency and Setup* — <https://www.justinbasil.com/guide/consistency>
- JustInBasil, *Energy and Acceleration* — <https://www.justinbasil.com/guide/energy>
- JustInBasil, *Recovery and Rebound* (counts 1-2 / 2-4 / 1 copia) — <https://www.justinbasil.com/guide/recovery>
- JustInBasil, *Draw Cards* (2-3 copias por supporter de robo) — <https://www.justinbasil.com/guide/draw>
- JustInBasil, *Secondary Attackers* (atacantes de un premio, prize trade) — <https://www.justinbasil.com/guide/secondary-attackers>
- JustInBasil, *Appendix IV: Some Deck Math* (tablas de mulligan y de robo) — <https://www.justinbasil.com/guide/appendix4>
- SixPrizes, *TheMathTCG: The Probabilities Behind the Opening Hand* (11,67% / 22,15% / 39,95%; rango 7-11 básicos; **90,36%** de arrancar con Supporter) — <https://sixprizes.com/2013/01/13/themathtcg-the-probabilities-behind/>
- TCG Protectors, *Prize Trade Guide: Advanced Prize Mapping* (mapa 2-2-2, regla de no bancar multi-premio) — <https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-trade-guide-advanced-prize-mapping>
- TCG Protectors, *Intermediate Strategy Guide* — <https://tcgprotectors.com/blogs/pokemon-deck-guides/pokemon-tcg-intermediate-strategy-guide>
- Fine Toys, *Competitive Pokémon TCG Guide* (2-3 estadios) — <https://www.finetoys.ca/blogs/news/competitive-pokemon-tcg-guide>
- SixPrizes, *Robustness: A Topic of Consistency in Deck Building* — <https://sixprizes.com/2013/01/20/robustness-a-topic-of/>
- SixPrizes, *Six Silver Bullets* — <https://sixprizes.com/2011/06/29/silver-bullets-tricky-ways-kill-top-decks/>
- SixPrizes forums, *Stats on Starts* — <https://forums.sixprizes.com/t/stats-on-starts-hypergeometric-distribution-and-the-pokemon-tcg/3465> (DNS caído desde aquí; citado vía búsqueda)
- TCG Protectors, *Deck Building Guide 2025* — <https://tcgprotectors.com/blogs/pokemon-deck-guides/how-to-build-pokemon-tcg-deck-guide>
- Delightful TCG, *How Many Energy Cards* — <https://www.delightfultcg.com/blogs/articles/how-many-energy-cards-should-be-in-a-pokemon-deck>
- Calculator City, *Pokémon TCG Calculator* (umbral del 50%) — <https://cal3.calculator.city/pokemon-tcg-calculator/>
- Limitless, Mega Lucario (Victor Zhao, Turin) — <https://limitlesstcg.com/decks/list/27959>
- Limitless, Lucario Hariyama (Brian Du, NAIC 2026) — <https://limitlesstcg.com/decks/list/28314>
- Limitless, Grimmsnarl Froslass (Andrew Choi, NAIC 2026) — <https://limitlesstcg.com/decks/list/28345>
- Limitless, NAIC 2026 decklists — <https://limitlesstcg.com/tournaments/518/decklists>
- Limitless Labs, metagame (tiers por share/WR) — <https://labs.limitlesstcg.com/decks>
- Bulbapedia, *ACE SPEC card (TCG)* — <https://bulbapedia.bulbagarden.net/wiki/ACE_SPEC_card_(TCG)>
- PokemonCard, *Best ACE SPEC Cards* (usage) — <https://pokemoncard.io/category/best-ace-spec-cards>
- PokeCardFinder, *Best Decks 2026* (umbral de tech, 42%→52%) — <https://pokecardfinder.com/best-pokemon-tcg-deck-2026/>
- Card Cavern, *New Turn 1 Supporter Rule Change* — <https://www.cardcaverntradingcards.com/blogs/news/new-turn-1-supporter-rule-change-what-you-need-to-know>
- PokeGuardian, *First Turn No Supporter Rule* — <https://www.pokeguardian.com/386462_first-turn-no-supporter-rule-regulation-marks-has-been-officially-announced-fairy-type-no-longer-supported>
