# Laboratorio de barajas — arquetipos medidos contra el motor real

Fecha: 2026-08-07. Script reproducible: `research/lab_barajas.py`
(subcomandos `validar | mulligan | medir | chequeo`; resultados JSON en el scratchpad).
Barajas propias en `research/decks/propios/*.csv` (una por arquetipo de
`notas/cartas-pool.md`, completadas a 60 con el shell de consistencia); mazos del meta en
`research/decks/meta/*.csv`. Piloto de todas las medidas: `research/agentes/heuristico.py`.

## 1. Las 9 listas propias (todas legales en `battle_start`: errorPlayer −1)

| Baraja | Núcleo | Básicos | Energía | Notas de construcción |
|---|---|---|---|---|
| mega-lucario (A1) | 4-4 Riolu/Mega Lucario 678 + 4 Regirock ex 447 | 8 | 19 {F} | 4 Fighting Gong, 2 Tarragon, shell completo |
| ethans-hooh (A2) | 4 Ho-Oh ex 357 + 3-3-2 línea Typhlosion 354 | 7 | 16 {R} | 4 Ethan's Adventure, 3 Firebreather |
| iono-bellibolt (A3) | 4 Tadbulb, 3 Bellibolt 269, 3-2 Wattrel/Kilowattrel, 2 Voltorb 265 | 9 | 16 {L} | 3 Levincia, 2 Canari, 3 Poffin |
| tr-mewtwo (A4) | 3 TR Mewtwo ex 431, 4 Murkrow 463, 2-2 Tarountula/Spidops | 9 | 4 TR + 12 {P} | 4 Ariana, 2+2+2 Petrel/Transceiver/Great Ball, 2 Factory |
| okidogi (A5) | 4 Okidogi ex 138 + 4 TR Murkrow 463 | 8 | 15 {D} | 4 Janine, 4 Mochi, 4 Pokégear, 4 Night Stretcher (arreglada 2026-08-10, ver §4bis) |
| hops-snorlax (A6) | 4 Snorlax 304, 3-3 Wooloo/Dubwool, 2 Cramorant | 9 | 16 (cualquiera) | 4 Choice Band, 4 Hop's Bag, 3 Postwick |
| ns-zekrom (A7) | 4 N's Zekrom 906, 2 Reshiram, 2-2 Zorua/Zoroark ex | 8 | 9 {R} + 9 {L} | 4 PP Up, 2 Castle, 2 Plan |
| mega-kangaskhan (A8) | 4 Mega Kangaskhan ex 756 + 3-3 Dunsparce/Dudunsparce | 7 | 16 (cualquiera) | 4 Mega Signal, Hero's Cape (ACE SPEC), 3 Poffin |
| abomasnow-plus (A9) | 4-4 Snover/Mega Abomasnow + 3 Kyogre | 7 | 28 {W} | La del ejemplo con Trolley + 4 Ultra Ball + robo moderno |

Reglas verificadas al construir: 60 exactas, ≤4 copias por ID (energía básica exenta),
≥1 básico, ≤1 ACE SPEC por baraja (1080/1092/1125/1126/1129/1159 son ACE SPEC — el
shell lleva Master Ball 1125 de serie, así que Hero's Cape solo cabe sin Master Ball).

## 2. Mulligan: la hipergeométrica ES el motor (verificado)

P(mano de 7 sin básico) = C(60−B,7)/C(60,7). Empírico: cada re-robo tras mulligan es una
muestra iid del mismo experimento (mano completa vuelve, shuffle, 7 nuevas), así que se
cuentan TODOS los checks `{"type":1, hasBasicPokemon}` de los logs. 200 setups espejo por
baraja; los 15 casos COINCIDEN dentro de 3σ:

| Básicos | Exacta | Barajas (empírica) |
|---|---|---|
| 7 | 0,399 | ethans-hooh 0,384 · mega-kangaskhan 0,405 · abomasnow-plus 0,419 · alakazam-v10 0,375 |
| 8 | 0,346 | mega-lucario 0,359 · ns-zekrom 0,346 · okidogi 0,351 |
| 9 | 0,300 | iono-bellibolt 0,286 · tr-mewtwo 0,274 · hops-snorlax 0,303 · garchomp 0,320 · great-tusk 0,329 · iono-sample 0,327 |
| 10 | 0,259 | grimmsnarl-dtc 0,245 · lucario-sample 0,251 |

Regla de diseño: cada básico de menos cuesta ~4-5 puntos de mulligan. El mulligan aquí no
pierde la partida (se re-roba), pero revela la mano y regala robo extra al rival.

## 3. Hallazgo de mecánica: option type 10 = USAR HABILIDAD

Corrige la duda de `motor-mecanica.md` («10 (area 7, ¿estadio?)»). En (0,0), option
type 10 es activar una habilidad o efecto de carta en juego:

- Pokémon propio: referencia por `inPlayArea`/`area` 4 (activo) o 5 (banca) — visto con
  Ho-Oh 357 (Golden Flame), Bellibolt 269 (Electric Streamer, repetible), Kilowattrel 271,
  Kangaskhan 756 (Run Errand), Dudunsparce 66, Zoroark 293 (Trade).
- Estadio en juego: `{"area": 7, "index": 0, "type": 10}` — visto con Levincia 1254.

El heurístico actual IGNORA el type 10 (recorte deliberado del baseline) → toda baraja
cuyo motor es una habilidad (A2, A3, A8, y el robo de Zoroark en A7) juega
sin su motor en las medidas del §5. Es el mayor upside de pilotaje pendiente.

## 4. Chequeo de implementación (partidas sondeo instrumentadas)

Método: espejo por baraja, política = heurístico salvo cuando aparece una opción de la
carta clave (se clica y se mide el diff de estado al volver a (0,0), o el log 16 de daño).
`lab_barajas.py chequeo` + sondas dirigidas para los 4 dudosos.

**FUNCIONAN (efecto observable exacto):**

- 678 Aura Jab: descarte −3 / energías +3 además del daño 130. 447 Regi Charge: +1-2 del descarte.
- 1142 Fighting Gong, 1215 Ethan's Adventure (+3), 1232 Firebreather (+7), 1233 Canari,
  1216 Ariana (roba hasta 5), 1134 Transceiver, 1219/1132 (búsqueda): todos mueven las cartas dichas.
- 357 Golden Flame (type 10): energía de mano a banca Ethan's. 269 Electric Streamer:
  +1 {L} por activación, repetible. 271 Flashing Draw: descarta {L} propia y roba hasta 6.
- 354 Buddy Blast: escala +60/Adventure en descarte (−160 observado con 2). El «damage=0»
  del catálogo es solo cosmético: el motor SÍ calcula el daño variable.
- 756 Run Errand (+2), 66 Run Away Draw (+3 y se rebaraja él mismo: banca −1, mazo +1),
  1159 Hero's Cape (+100 maxHp), 1145 Mega Signal.
- 138 Poisonous Musculature: busca y pega 2 {D} y se envenena; 1195 Janine: +1 {D}/objetivo
  con veneno al activo; 1162 Binding Mochi adjunta.
- 1115 Hop's Bag (banca +2), 1171 Choice Band: **coste −{C} verificado** (Dynamic Press
  ofrecido con 2 energías solo con Band) y daños EXACTOS: 140 base +30 Band +30 Extra
  Helpings (304) +30 Postwick → −200/−230 en log 16. Los tres modificadores apilan bien.
- 1113 PP Up (+1 del descarte), 1221 N's Plan (mueve 2: activo +2 / banca −2),
  1254 Levincia (uso type 10 area 7: hasta 2 {L} del descarte a mano),
  293 Trade (descarta 1, roba 2).
- 723 Hammer-lanche (−300 con 3 {W} en el top-6), 1126 Precious Trolley (banca +3..+5),
  1163 Powerglass, 431 Erasure Ball (−160 base).

**INUTILIZABLE:**

- **1230 Grimsley's Move: ROTA.** 48 clics con hueco en banca (0-3 ocupados), turnos 3-11,
  8 Pokémon {D} en mazo → banca +0 en 48/48 (P(fallo natural)≈0,3⁴⁸≈10⁻²⁰). La carta se
  juega y va al descarte sin efecto. Herida: okidogi pierde su setup secundario (el núcleo
  Musculature+Janine sí funciona). Sustituir por Pokégear/robo en la lista final.

Sin más rotas entre las 36 cartas sondeadas. Contexto nuevo visto en los sondeos:
ningún option type fuera de {7,8,9,10,12,13,14} en (0,0).

## 4bis. Arreglo de okidogi (2026-08-10) y dos hallazgos de motor

Fuera las 4× Grimsley's Move 1230 (rota). Entran **+2 Pokégear 3.0 1122 (→4) y
+2 Night Stretcher 1097 (→4)**. Razonamiento: quitando Grimsley la lista queda con
16 Supporters (4 Janine, 4 Cheren, 4 Urbain, 2 Lillie, 2 Boss) — la ranura de Supporter
(1/turno) está saturada, así que el robo/búsqueda de reemplazo debe ser Item. Poffin 1086
descartado: sus objetivos son básicos ≤70 HP y Murkrow tiene 80 (cero objetivos).

Hallazgos de las sondas del arreglo (`scratchpad/probe_okidogi_items.py`, `probe_1132_fetch.py`):

- **1132 TR Great Ball: el motor NO implementa el texto del CSV** («Search your deck for a
  Trainer card»). Implementa la carta real: busca **Pokémon Team Rocket's**. En okidogi solo
  encontraba Murkrow 463 (8/20 clics) o nada (12/20) → descartada aquí. En tr-mewtwo sigue
  siendo funcional (la lista está llena de Pokémon TR); el «búsqueda OK» del §4 era eso.
- **1122 Pokégear funciona** (15/20 trae Cheren/Boss/Janine/Lillie/Urbain respondiendo al
  máximo su select intermedio `(type 1, context 7, min 0, max 1, opts type 3 area 12)`),
  **pero el heurístico v2 lo declina**: ese select cae al fallback genérico (min 0 → `[]`),
  así que bajo este piloto Pokégear se juega sin coger nada. Gap de PILOTO, no de carta —
  mejora pendiente del heurístico: en (1,7) con min 0 tras jugar un buscador, coger 1.
- 1097 Night Stretcher bajo el piloto: 25/25 con efecto neto `{}` = éxito (el propio item
  al descarte +1 se compensa con la carta recuperada −1; su select intermedio es min 1 y el
  fallback ya elige). Lista final validada: `battle_start` errorPlayer −1; mulligan sin
  cambio (siguen 8 básicos).

## 5. Medidas (heurístico pilotando ambos lados, 300+300 partidas por baraja)

(pendiente de la corrida — se rellena abajo)

## 6. Ranking y top-3

(pendiente de la corrida)
