# Pool de cartas y arquetipos viables (cabt / Pokémon TCG AI Battle Challenge)

Fuente: `data/raw/EN_Card_Data.csv` (variante con guion bajo). Script reproducible:
`research/analisis_cartas.py` → genera `research/cards_clean.csv` (derivado, gitignoreado).
Fecha: 2026-08-06.

## 1. Estructura del CSV (verificada)

- 2.022 filas, 1.267 `Card ID` únicos. Filas por carta: 1×544, 2×691, 3×32.
- **Una fila por movimiento**, no solo por ataque: la fila puede ser ataque, `[Ability]` o
  marcador `[Tera]` (columna `Move Name`). Recuento de filas: 1.559 ataques, 223 habilidades,
  29 `[Tera]`, 211 sin movimiento (trainers/energías).
- Las columnas estáticas (nombre, HP, tipo, etapa…) son **consistentes en todas las filas de
  una carta** (0 inconsistencias) → agrupar por `Card ID` es seguro.
- Ojo prompt inicial: «270 Pokémon ex / 54 Mega ex» eran FILAS; cartas únicas son 121 ex y 30 Mega ex.

## 2. Censo (cartas únicas)

| Clase | n |
|---|---|
| Basic Pokémon | 595 |
| Stage 1 | 345 |
| Stage 2 | 116 |
| **Pokémon total** | **1.056** (905 single-prize, 121 ex, 30 Mega ex) |
| Item | 77 |
| Supporter | 61 |
| Stadium | 26 |
| Pokémon Tool | 27 |
| Basic Energy | 8 ({G}{R}{W}{L}{P}{F}{D}{M} — no hay Fairy; el tipo dragón 竜 no tiene energía propia) |
| Special Energy | 12 |
| ACE SPEC | 29 (máx. 1 por baraja) |

- HP Pokémon: mediana 100 (Basic med. 70/máx. 310, St1 med. 120/máx. 350, St2 med. 170/máx. 380).
  Basic ex ≈ 190–280 HP; Mega ex ≈ 250–380 HP.
- Premios al caer (regla TCG real, **pendiente de confirmar contra el motor**): normal 1,
  ex 2, Mega ex 3. La columna `Rule` solo trae la etiqueta, no el texto.
- Líneas evolutivas completas en el pool: Basic→St1→St2 **99**; Basic→St1 **290/295**.
  Los 5 St2 «sin línea» (Archeops, Aurorus, Carracosta, Cradily, Tyrantrum) evolucionan de
  Items «Antique … Fossil» (1099/1136/1138/1150/1151) que se juegan como Basic de 60 HP.
- Debilidades (a qué tipo le pega más gente): {R} 220, {F} 188, {L} 155, {G} 141, {W} 99,
  {D} 91, {M} 86, {P} 41, sin debilidad 35 (dragones). → Atacantes {R} y {F} explotan más
  debilidades; los dragones no regalan debilidad.
- Categorías: 52 cartas «Team Rocket's», y paquetes de dueño (Hop 12, N 15, Ethan 9, Iono 6…)
  con trainers dedicados que solo funcionan dentro del paquete. 29 Tera (protección banca del
  propio Koraidon ex etc.), 14 Ancient, 10 Future.

## 3. Columna vertebral de consistencia (motores)

**Robo (Supporters)**: Cheren 1224 y Urbain 1236 (Draw 3 incondicional — los más simples de
pilotar), Lillie's Determination 1227 (barajar y robar 6/8), Judge 1213 (reset 4/4),
Emcee's Hype 1214, Iris's Fighting Spirit 1208 (robar hasta 6 con descarte), Amarys 1207,
Team Rocket's Ariana 1216 (robar hasta 5, hasta 8 si todo es TR), Lacey 1199, Surfer 1203.

**Búsqueda (Items)**: Ultra Ball 1121 (cualquier Pokémon, descarta 2 — alimenta descarte),
Buddy-Buddy Poffin 1086 (bancar 2 basics ≤70 HP), Poké Pad 1152 (Pokémon sin Rule Box),
Tera Orb 1127, Mega Signal 1145 (Mega ex), Fighting Gong 1142, Pokégear 3.0 1122 (Supporter),
Energy Search 1119; ACE SPEC: Master Ball 1125, Precious Trolley 1126, Secret Box 1092.
Gusting: **Boss's Orders 1182**. Recuperación: Night Stretcher 1097, Energy Retrieval 1118,
Sacred Ash 1129, Energy Recycler 1139.

**Aceleración de energía**: casi toda vive en habilidades de Pokémon concretos (define
arquetipo): Iono's Bellibolt ex 269 (ilimitada desde mano a Iono's), Ethan's Ho-Oh ex 357
(2 {R}/turno a banca Ethan's), Emboar 569 (ilimitada {R}), Eelektrik 512 (1 {L}/turno desde
descarte), Blaziken ex 326, Magneton 211, Archaludon ex 190, Regis 447/944/988 (Regi Charge
a sí mismos), Okidogi ex 138 (busca 2 {D} del mazo al atacar). Trainers de aceleración:
Janine's Secret Art 1195 ({D}), Crispin 1198, Waitress 1235, Wondrous Patch 1146 ({P}),
N's PP Up 1113, Powerglass 1163 (tool, del descarte al activo al final del turno),
Levincia 1254 (stadium {L}), Glass Trumpet 1098 (Tera).

**Robo por habilidad (motor en banca)**: Mega Kangaskhan ex 756 (roba 2/turno), Iono's
Kilowattrel 271 (descarta {L} → roba hasta 6), N's Zoroark ex 293 (Trade), Fezandipiti ex 140
(3 si te mataron algo), Dudunsparce 66, Rapidash 351.

## 4. Baraja de ejemplo de `cabt.py` (decodificada)

2× Kyogre 721 · 4× Snover 722 · 4× Mega Abomasnow ex 723 · 1× Secret Box 1092 (ACE SPEC) ·
2× Ultra Ball 1121 · 2× Mega Signal 1145 · 2× Powerglass 1163 · 4× TR Petrel 1219 ·
4× Lillie's Determination 1227 · 2× Surfing Beach 1262 · 33× Basic {W} Energy (3).

**Arquetipo**: aggro mono-agua Mega Abomasnow. Hammer-lanche ({W}{W}, descarta el top-6 del
mazo y hace 100× por cada {W} descartada — de ahí las 33 energías, E[daño] ≈ 300) con Kyogre
(Riptide 20× por {W} en descarte, luego las recicla) de secundario. Petrel busca cualquier
trainer; Lillie es el robo. Es una máquina tragaperras: daño esperado alto, varianza altísima
→ mala referencia para un Model Score que premia consistencia, pero buen sparring.

## 5. Arquetipos candidatos (núcleos concretos)

Criterios: daño/energía, aceleración propia, premios que regala, y cuántas decisiones
ramificadas exige al agente (menos = mejor). Shell genérico de consistencia común a casi
todos: 4 Cheren 1224 + 3-4 Urbain 1236 + 2 Boss's Orders 1182 + 4 Ultra Ball 1121 +
1 Master Ball 1125 + 2 Switch 1123 + Night Stretcher 1097.

### A1. Mega Lucario ex (Fighting, 3 premios) — el más redondo
Núcleo: 4 Riolu 677, 4 **Mega Lucario ex 678** (St1, 340 HP; Aura Jab {F} 130 **y acelera
3 {F} del descarte a la banca**; Mega Brave {F}{F} 270), 2 Regirock ex 447 (Regi Charge),
4 Fighting Gong 1142, 2 Tarragon 1238, 1 Premium Power Pro 1141, ~12 {F} + shell.
Autoalimentado (el ataque barato ES la aceleración), decisiones lineales, y {F} pega en
debilidad a 188 Pokémon. Contra: 3 premios al caer; debilidad {P}.

### A2. Ethan's Ho-Oh ex turbo (Fire, 2 premios) — el más simple
Núcleo: 3-4 **Ethan's Ho-Oh ex 357** (230 HP; hab.: 2 {R}/turno de mano a banca Ethan's;
Shining Feathers {R}×4 160 + cura 50 a todo), 2-2-2 línea Ethan's Cyndaquil 352 / Quilava 353
(busca Ethan's Adventure) / Typhlosion 354 (single-prize: 40 + 60× por Ethan's Adventure en
descarte), 4 Ethan's Adventure 1215, 2 Firebreather 1232 (busca 7 {R}), ~14 {R} + shell.
Bucle trivial: roba energías → 2 al banquillo → rota Ho-Oh curados. 160 se queda corto contra
Megas; Typhlosion cierra. Débil a {W}.

### A3. Iono's Bellibolt ex (Lightning, 2 premios) — motor integrado
Núcleo: 4 Iono's Tadbulb 268, 3-4 **Iono's Bellibolt ex 269** (280 HP; hab.: energía {L}
ILIMITADA de mano a Iono's; Thunderous Bolt 230), 2-2 Iono's Wattrel 270 / Kilowattrel 271
(robo: descarta {L} → roba hasta 6), 3 Levincia 1254 (recupera 2 {L}/turno), 2 Canari 1233,
~15 {L} + shell. Robo y aceleración dentro del propio arquetipo; dos Bellibolt alternan para
esquivar el «no puede atacar el próximo turno». Débil a {F} (Lucario).

### A4. Caja Team Rocket / TR Mewtwo ex (Psychic/Dark, 2 premios) — el motor de búsqueda más profundo
Núcleo: 3 **TR Mewtwo ex 431** (280 HP; Erasure Ball 160+60 por energía descartada de banca,
hasta 280; exige 4 TR Pokémon en juego), 4 TR Ariana 1216 (roba hasta 8), 2 TR Petrel 1219,
2 TR Transceiver 1134, 2 TR Great Ball 1132, 2 TR Proton 1220, 2 TR Murkrow 463 (ataque =
busca Supporter), 2 TR Spidops 401 (acelera del descarte), 4 TR Energy 15 (2 tipos a TR),
2 TR Factory 1257, resto basics TR baratos + {P}. Consistencia brutal, pero más decisiones
(gestión de banca y de qué descartar) → más difícil de pilotar bien para un agente.

### A5. Okidogi ex veneno (Darkness, 2 premios) — autosuficiente
Núcleo: 4 **Okidogi ex 138** (250 HP; Poisonous Musculature {C}: busca y pega 2 {D} del mazo
a sí mismo y se envenena; Chain-Crazed {D}{D}{C} 130+130 si envenenado), 3 Binding Mochi 1162
(+40 si envenenado → 300), 4 Janine's Secret Art 1195 (acelera {D} del mazo y envenena),
2 Grimsley's Move 1230, ~12 {D} + shell. Turno 1: Musculature (acelera solo); turno 2+: 260-300.
Decisiones mínimas. Débil a {F}.

### A6. Hop's Snorlax (Colorless, **single-prize**) — muro que pega
Núcleo: 4 **Hop's Snorlax 304** (150 HP, single-prize; hab. pasiva: +30 a ataques de Hop's;
Dynamic Press {C}{C}{C} 140 (+30) con 80 de retroceso), 4 Hop's Choice Band 1171 (coste −{C}
y +30 → **200 por 2 energías de cualquier tipo**), 4 Hop's Bag 1115 (banca 2 Hop's), 2-3
Postwick 1255 (+30 a Hop's), 2 Hop's Dubwool 310 (gust al evolucionar), opcional 1-2 Hop's
Zacian ex 299 de cierre, ~10 energía cualquiera + shell. El rival necesita 6 KOs; nosotros
matamos ex de ≤200 al ritmo de 1 por turno. Coste colorless = cualquier energía = cero
decisiones de color. Débil a {F}.

### A7. N's Zekrom dragones (R+L, **single-prize**) — trade de premios premium
Núcleo: 4 **N's Zekrom 906** (130 HP, single-prize, SIN debilidad; Rampaging Thunder
{R}{L}{L}{C} **250**, no ataca el turno siguiente), 2 N's Reshiram 303, 2 N's Zoroark ex 293
(Trade, robo; opcional para mantenerlo full single-prize usar más robo genérico), 4 N's PP Up
1113 (acelera del descarte a banca N's), 2-3 N's Castle 1253 (retirada gratis N's → rotar
Zekroms cargados), 2 N's Plan 1221 (mueve 2 energías al activo), ~8 {R} + ~8 {L} + shell.
Un single-prize de 130 HP que mata Megas de 330+ en dos golpes y ex de ≤250 de uno; el rival
gana 1 premio por KO. Contra: dos colores de energía y rotación = complejidad media.

### A8. Mega Kangaskhan ex (Colorless, 3 premios) — el Mega más simple
Núcleo: 3-4 **Mega Kangaskhan ex 756** (BASIC 300 HP, sin evolución; hab.: roba 2/turno en
activo; Rapid-Fire Combo {C}{C}{C} 200 + 50× por cara), 2 Mega Signal 1145, energía cualquiera
~12 + shell + tools defensivos (Hero's Cape 1159 ACE SPEC → 400 HP). Basic + colorless +
robo integrado = mínimo árbol de decisión. Contra: 3 premios y daño con moneda (varianza).

### A9. Mega Abomasnow/Kyogre (Water) — la del ejemplo, mejorable
La del motor (sección 4) con shell moderno (Poffin no aplica: Snover 90 HP; sí Precious
Trolley 1126 o más robo). Referencia/sparring: varianza intrínseca del top-deck la hace mala
candidata para Model Score, aunque su techo de daño (300-600) gana partidas sueltas.

## 6. Observaciones para la selección final

- El Model Score premia consistencia → preferir A1/A2/A3/A5 (aceleración determinista, sin
  monedas) sobre A8/A9 (moneda/tragaperras). A6/A7 cubren la exigencia single-prize y además
  castigan el trade de premios de los Mega (3 premios por KO nuestro vs 1 por el suyo).
- Falta verificar QUÉ efectos implementa realmente `libcg.so` (tema motor): si una habilidad
  clave no está implementada, el arquetipo se cae. Probar con partidas reales antes de fijar.
- Sin rotación de tipos dominante: {F} y {R} explotan más debilidades; {P} y dragón casi no
  regalan debilidad propia.
- ACE SPEC: 1 por baraja — candidatos por defecto Master Ball 1125 (búsqueda sin coste) o
  Precious Trolley 1126 (setup de basics).
