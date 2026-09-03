# La baraja contra el campo REAL (2026-08-10)

Sustituye al censo de 12 replays y a la báscula «vs baraja de ejemplo del motor».
Scripts: `research/replays/censo_campo.py` (censo), `research/gauntlet.py` (medida),
`research/ver_baraja.py` (leer/diff de listas). Rivales en `research/decks/campo/`.
Resultados crudos: `scratchpad/gauntlet.json`, `data/replays/censo_campo.json`.

---

## 1. Censo real del campo: 18.674 barajas, 203 listas únicas

Fuente: `data/replays/idx/idx_0808.json` + `idx_0809.json` (los dos días descargados,
9.337 episodios, las DOS barajas de cada partida leídas del paso 1 con el desfase
corregido; recuperación 100%). Agrupación propia por solapamiento de multiconjunto
(`sum(min(a,b))/60 ≥ 0,62`, líder = lista más jugada del grupo), no por las firmas de
Sumi: esas dejaban un 26-31% del campo en el cubo «otro».

**Solo hay 203 listas distintas en 18.674 barajas** y las 50 más jugadas cubren el 90%.
El campo es un puñado de listas copiadas, no una distribución larga.

| # | arquetipo (Pokémon núcleo) | n | share | WR real | listas | equipos |
|---|---|---|---|---|---|---|
| 1 | Marnie's Grimmsnarl ex (+Munkidori, Froslass) | 5.821 | **31,2%** | 46,6% | 21 | 205 |
| 2 | Alakazam (Abra/Kadabra + Dudunsparce) | 3.408 | **18,2%** | 49,7% | 23 | 120 |
| 3 | Mega Lopunny ex + Mega Froslass ex | 2.386 | **12,8%** | 51,0% | 7 | 61 |
| 4 | Dragapult ex (Dreepy/Drakloak) | 1.523 | 8,2% | **58,7%** | 21 | 30 |
| 5 | Mega Kangaskhan ex + Crustle | 1.281 | 6,9% | 44,5% | 20 | 55 |
| 6 | Teal Mask Ogerpon ex (mono {G}) | 925 | 5,0% | 46,3% | 16 | 30 |
| 7 | Mega Lucario ex (Makuhita/Hariyama) | 738 | 4,0% | 54,6% | 12 | 28 |
| 8 | Dipplin + Grookey/Thwackey | 651 | 3,5% | 55,1% | 20 | 17 |
| 9 | Hydrapple ex + Meganium (Applin/Bayleef) | 474 | 2,5% | 56,1% | 12 | 12 |
| 10 | Slowking + Mega Kangaskhan ex | 327 | 1,8% | **63,3%** | 1 | 5 |
| 11 | Cynthia's Garchomp | 294 | 1,6% | 50,3% | 6 | 19 |
| 12 | N's Zoroark ex + N's Zekrom | 156 | 0,8% | 57,7% | 1 | 4 |

WR real = winrate en la ladder, sin espejos, con los pilotos de sus dueños.

**Qué corrige respecto al censo de 12 replays** (Mega Lucario 42% / Alakazam 17% /
tipo-ejemplo 17% / Garchomp 8%): aquel censo era ruido de muestra pequeña sesgado por
nuestros propios emparejamientos. Mega Lucario es el 4,0% del campo, no el 42%; y la
baraja de ejemplo del motor **no aparece: 0 de 18.674**. Confirma el diagnóstico: el
ranking de 15 listas contra la baraja de ejemplo medía contra un rival que no existe.

Lo que sí se mantiene: Grimmsnarl domina el share y está en regresión (46,6%), y hay
tres listas minoritarias con WR alto (Dragapult 58,7%, Slowking 63,3%, Hydrapple 56,1%).

---

## 2. El gauntlet

`research/decks/campo/c1..c8` = los 8 arquetipos más jugados, **89,8% del campo real**,
cada uno la lista líder exacta de su grupo (copiada literal de los replays, validada en
`battle_start` con `errorPlayer −1`). Pesos = su share.

| fichero | arquetipo | peso |
|---|---|---|
| `c1-grimmsnarl.csv` | Marnie's Grimmsnarl ex | 0,312 |
| `c2-alakazam.csv` | Alakazam | 0,182 |
| `c3-lopunny-froslass.csv` | Mega Lopunny + Mega Froslass | 0,128 |
| `c4-dragapult.csv` | Dragapult ex | 0,082 |
| `c5-kangaskhan-crustle.csv` | Mega Kangaskhan + Crustle | 0,069 |
| `c6-ogerpon.csv` | Teal Mask Ogerpon ex | 0,050 |
| `c7-lucario-campo.csv` | Mega Lucario ex (versión del campo) | 0,040 |
| `c8-dipplin-grookey.csv` | Dipplin + Grookey | 0,035 |

Además `x1..x7` son listas del campo guardadas como CANDIDATAS (no rivales): slowking,
hydrapple, cynthia-garchomp, ns-zoroark, dragapult, dipplin-grookey, lucario-campo.

(sigue en §3)
