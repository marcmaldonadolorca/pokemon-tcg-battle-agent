#!/usr/bin/env python3
"""Rasgos de ESTADO y de OPCIÓN para la red de política (clonado por imitación).

Este módulo es la ÚNICA fuente del esquema: lo usan el extractor de replays
(`extraer.py`), el entrenador (`entrenar.py`) y el agente de producción
(`research/agentes/clon.py`). Si diverge, los pesos dejan de significar nada.

Diseño (por qué así):
  La salida no es un escalar sino elegir entre un nº VARIABLE de opciones. Así que
  se puntúa cada opción por separado con el mismo puntuador
      score_j = f(estado, opcion_j) + b_carta[j]
  y se hace softmax SOBRE EL BLOQUE de opciones del mismo select. Eso es
  exactamente clasificación con la jugada del experto como positiva.

  Los rasgos de opción son DECK-AGNÓSTICOS salvo el sesgo por carta (que es un
  escalar aparte, ablacionable): describen lo que la opción HACE (daño efectivo,
  premios que concede, si mata, coste, etapa evolutiva), no qué carta es. Una
  baraja no vista se describe con los mismos números.

Contrato del motor verificado en research/notas/motor-mecanica.md (incluidas las
dos correcciones del 2026-08-11: (1,3)/(1,4) van al revés de lo que decía la
tabla original, y (1,8) es descarte de coste con N variable).

Tipos de option observados (research/notas/motor-mecanica.md §1 + censo propio):
  0 número · 1/2 sí-no o primero/segundo · 3 elegir carta en `area`
  4 objetivo de tool · 6 descartar energía adjunta · 7 jugar carta de la mano
  8 básico de la mano a activo/banca · 9 evolucionar/tool sobre un Pokémon en juego
  10 activar habilidad · 12 retirada · 13 atacar (`attackId`) · 14 fin de turno
  15 carta revelada (`cardId`)
Áreas: 1 mazo (lista `select.deck`) · 2 mano · 3 descarte · 4 activo · 5 banca.
"""
import os
import sys

import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_D, "..", "valor"), _D):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import features_v2 as fv2  # noqa: E402

# ---------------------------------------------------------------- dimensiones
N_TIPO_SEL = 10
N_TIPO_OPC = 16
N_AREA = 13
N_CARDTYPE = 7
N_ENERGYTYPE = 10

DIM_S = fv2.DIM + N_TIPO_SEL + 13 + N_AREA + N_TIPO_OPC          # 62+10+13+13+16 = 114
DIM_O = 39 + 33 + 13 + 10 + 1                                    # 96 (la última = «no elegir nada»)

_ZONA_JUEGO = {4: "active", 5: "bench"}
_ZONA_CARTA = {2: "hand", 3: "discard"}


# ------------------------------------------------------------------ catálogo
def _cardinfo(cid):
    """Ficha cruda del catálogo del motor (dict de AllCard) o None."""
    cards, _ = fv2._catalogo()
    return cards.get(cid)


def _atk(aid):
    _, atks = fv2._catalogo()
    return atks.get(aid)


def _act(p):
    a = (p.get("active") or [None])[0]
    return a if isinstance(a, dict) else None


# --------------------------------------------------------------- rasgos estado
def rasgos_estado(sel, cur) -> np.ndarray:
    """62 rasgos de features_v2 + 52 de la FORMA del select.

    Los rasgos del select son constantes dentro del bloque (no rompen el
    softmax por sí solos), pero interaccionan con los de opción en la capa
    oculta: es como el modelo aprende «en un (1,4) prefiero HP alto» sin que
    haya que enumerar contexts (que son huecos de carta, no mecánicas).
    """
    v = np.zeros(DIM_S, dtype=np.float32)
    base = fv2.extrae(cur)
    v[: fv2.DIM] = base
    b = fv2.DIM
    if not sel:
        return v

    t = sel.get("type")
    if isinstance(t, int) and 0 <= t < N_TIPO_SEL:
        v[b + t] = 1.0
    b += N_TIPO_SEL

    opt = sel.get("option") or []
    n = len(opt)
    mn = float(sel.get("minCount") or 0)
    mx = float(sel.get("maxCount") or 0)
    dk = sel.get("deck") or []
    ef = sel.get("effect")
    yo = (cur or {}).get("yourIndex", 0)
    jug = (cur or {}).get("players") or []
    activo_vacio = 1.0
    if 0 <= yo < len(jug):
        activo_vacio = 0.0 if _act(jug[yo]) else 1.0
    lados = [o.get("playerIndex") for o in opt if isinstance(o, dict)]
    mios = [x for x in lados if x is not None and x == yo]
    suyos = [x for x in lados if x is not None and x != yo]

    v[b + 0] = 1.0 if mn == mx else 0.0
    v[b + 1] = min(mn, 6.0) / 6.0
    v[b + 2] = min(mx, 6.0) / 6.0
    v[b + 3] = min(n, 20.0) / 20.0
    v[b + 4] = np.log1p(n) / 3.5
    v[b + 5] = 1.0 if dk else 0.0
    v[b + 6] = min(len(dk), 60.0) / 60.0
    v[b + 7] = 1.0 if ef else 0.0
    v[b + 8] = 1.0 if (isinstance(ef, dict) and ef.get("playerIndex") == yo) else 0.0
    v[b + 9] = activo_vacio                       # (1,4): promoción tras KO
    v[b + 10] = 1.0 if (mios and not suyos) else 0.0
    v[b + 11] = 1.0 if (suyos and not mios) else 0.0
    v[b + 12] = min(float((cur or {}).get("turnActionCount") or 0), 20.0) / 20.0
    b += 13

    a0 = opt[0].get("area") if (opt and isinstance(opt[0], dict)) else None
    if isinstance(a0, int) and 0 <= a0 < N_AREA:
        v[b + a0] = 1.0
    b += N_AREA

    for o in opt:                                  # multi-hot de tipos presentes
        if isinstance(o, dict):
            ot = o.get("type")
            if isinstance(ot, int) and 0 <= ot < N_TIPO_OPC:
                v[b + ot] = 1.0
    return v


# -------------------------------------------------------------- resolución
def _carta_de_opcion(o, sel, cur, yo):
    """(cardId, dict de la carta/pokemon en juego o None) que toca la opción."""
    if not isinstance(o, dict):
        return -1, None
    t = o.get("type")
    if t == 15:                                    # carta revelada: id explícito
        return int(o.get("cardId") or -1), None
    if t == 13:                                    # atacar: la carta es mi activo
        jug = (cur or {}).get("players") or []
        a = _act(jug[yo]) if 0 <= yo < len(jug) else None
        return (int(a["id"]), a) if a and a.get("id") is not None else (-1, None)
    if t == 12:                                    # retirada: ídem
        jug = (cur or {}).get("players") or []
        a = _act(jug[yo]) if 0 <= yo < len(jug) else None
        return (int(a["id"]), a) if a and a.get("id") is not None else (-1, None)

    idx = o.get("index")
    area = o.get("area")
    if t == 7 and area is None:                    # jugar carta de la mano (sin area)
        area = 2
    pi = o.get("playerIndex")
    j = pi if isinstance(pi, int) else yo
    jug = (cur or {}).get("players") or []

    c = None
    if area == 1:                                  # mazo: la lista va en select.deck
        dk = sel.get("deck") or []
        if isinstance(idx, int) and 0 <= idx < len(dk):
            c = dk[idx]
    elif area in _ZONA_CARTA:
        if 0 <= j < len(jug):
            lst = jug[j].get(_ZONA_CARTA[area])
            if isinstance(lst, list) and isinstance(idx, int) and 0 <= idx < len(lst):
                c = lst[idx]
    elif area in _ZONA_JUEGO:
        if 0 <= j < len(jug):
            lst = jug[j].get(_ZONA_JUEGO[area])
            if isinstance(lst, list) and isinstance(idx, int) and 0 <= idx < len(lst):
                c = lst[idx]
    if isinstance(c, dict) and c.get("id") is not None:
        return int(c["id"]), c
    return -1, None


def _objetivo_en_juego(o, cur, yo):
    """Pokémon EN JUEGO al que apunta la opción (destino o sujeto), o None.

    Cubre tres formas distintas: `inPlayArea/inPlayIndex` (tipos 8, 9),
    `area 4/5 + index` (tipos 3, 4, 6, 10) y el activo propio (12, 13).
    """
    if not isinstance(o, dict):
        return None, None
    jug = (cur or {}).get("players") or []
    t = o.get("type")
    if t in (12, 13):
        return (_act(jug[yo]) if 0 <= yo < len(jug) else None), yo
    ipa, ipi = o.get("inPlayArea"), o.get("inPlayIndex")
    if isinstance(ipa, int) and ipa in _ZONA_JUEGO:
        j = yo
        if 0 <= j < len(jug):
            lst = jug[j].get(_ZONA_JUEGO[ipa])
            if isinstance(lst, list) and isinstance(ipi, int) and 0 <= ipi < len(lst):
                x = lst[ipi]
                return (x if isinstance(x, dict) else None), j
        return None, j
    area = o.get("area")
    if isinstance(area, int) and area in _ZONA_JUEGO:
        pi = o.get("playerIndex")
        j = pi if isinstance(pi, int) else yo
        idx = o.get("index")
        if 0 <= j < len(jug):
            lst = jug[j].get(_ZONA_JUEGO[area])
            if isinstance(lst, list) and isinstance(idx, int) and 0 <= idx < len(lst):
                x = lst[idx]
                return (x if isinstance(x, dict) else None), j
    return None, None


# ------------------------------------------------------------- rasgos opción
def rasgos_opciones(sel, cur):
    """(O float32 (k[+1], DIM_O), C int32) para las opciones del select.

    Si `minCount == 0` se añade UNA fila extra al final: la opción «no elegir
    nada», que es una jugada real y frecuente (pasar una búsqueda `(1,7)`, no
    poner banca inicial `(1,2)`). Sin ella el modelo no puede representar el
    `[]` del experto y hay que tirarlo del dataset.
    """
    opt = sel.get("option") or []
    k = len(opt)
    pasa = 1 if (sel.get("minCount") or 0) == 0 else 0
    O = np.zeros((k + pasa, DIM_O), dtype=np.float32)
    C = np.full(k + pasa, -1, dtype=np.int32)
    if pasa:
        O[k, DIM_O - 1] = 1.0
    if k == 0:
        return O, C

    cur = cur or {}
    yo = cur.get("yourIndex", 0)
    jug = cur.get("players") or []
    mi = jug[yo] if 0 <= yo < len(jug) else {}
    ri = jug[1 - yo] if 0 <= 1 - yo < len(jug) else {}
    mi_act, su_act = _act(mi), _act(ri)
    i_su = fv2._info(su_act.get("id")) if su_act else fv2._VACIA
    i_mi = fv2._info(mi_act.get("id")) if mi_act else fv2._VACIA
    hp_su = float(su_act.get("hp") or 0.0) if su_act else 0.0
    hp_mi = float(mi_act.get("hp") or 0.0) if mi_act else 0.0
    # daño pagable del rival contra mi activo: sirve para «este objetivo muere ya»
    dmg_riv, _, _, _, _ = fv2._ofensiva(su_act, mi_act) if (su_act and mi_act) else (0.0, 0, 0, 0, 0)

    for r, o in enumerate(opt):
        v = O[r]
        if not isinstance(o, dict):
            continue
        # ---- A: campos crudos (0..38)
        t = o.get("type")
        if isinstance(t, int) and 0 <= t < N_TIPO_OPC:
            v[t] = 1.0
        area = o.get("area")
        if isinstance(area, int) and 0 <= area < N_AREA:
            v[N_TIPO_OPC + area] = 1.0
        b = N_TIPO_OPC + N_AREA                                    # 29
        pi = o.get("playerIndex")
        v[b + 0] = 1.0 if pi is not None else 0.0
        v[b + 1] = 1.0 if (pi is not None and pi == yo) else 0.0
        v[b + 2] = min(float(o.get("index") or 0), 20.0) / 20.0
        v[b + 3] = 1.0 if "attackId" in o else 0.0
        v[b + 4] = 1.0 if o.get("inPlayArea") == 4 else 0.0
        v[b + 5] = 1.0 if o.get("inPlayArea") == 5 else 0.0
        v[b + 6] = min(float(o.get("inPlayIndex") or 0), 5.0) / 5.0
        v[b + 7] = min(float(o.get("count") or 0), 5.0) / 5.0
        v[b + 8] = 1.0 if "toolIndex" in o else 0.0
        v[b + 9] = min(float(o.get("number") or 0), 5.0) / 5.0

        # ---- B: la carta implicada (39..71)
        b = 39
        cid, cdict = _carta_de_opcion(o, sel, cur, yo)
        C[r] = cid
        if cid >= 0:
            ci = _cardinfo(cid)
            if ci is not None:
                v[b + 0] = 1.0
                ct = ci.get("cardType")
                if isinstance(ct, int) and 0 <= ct < N_CARDTYPE:
                    v[b + 1 + ct] = 1.0
                c2 = b + 1 + N_CARDTYPE                            # 47
                v[c2 + 0] = 1.0 if ci.get("basic") else 0.0
                v[c2 + 1] = 1.0 if ci.get("stage1") else 0.0
                v[c2 + 2] = 1.0 if ci.get("stage2") else 0.0
                v[c2 + 3] = 1.0 if ci.get("ex") else 0.0
                v[c2 + 4] = 1.0 if ci.get("megaEx") else 0.0
                v[c2 + 5] = 1.0 if ci.get("tera") else 0.0
                v[c2 + 6] = 1.0 if ci.get("aceSpec") else 0.0
                inf = fv2._info(cid)
                v[c2 + 7] = min(float(ci.get("hp") or 0), 400.0) / 400.0
                v[c2 + 8] = min(inf["rc"], 4.0) / 4.0
                v[c2 + 9] = inf["prz"] / 3.0
                v[c2 + 10] = min(inf["dmax"], 300.0) / 300.0
                cmin = min((len(cc) for _, cc in inf["atk"]), default=0)
                v[c2 + 11] = min(float(cmin), 5.0) / 5.0
                et = inf["et"]
                if isinstance(et, int) and 0 <= et < N_ENERGYTYPE:
                    v[c2 + 12 + et] = 1.0
                c3 = c2 + 12 + N_ENERGYTYPE                        # 69
                # cuánto pegaría ESTA carta al activo rival (potencial, sin energía)
                pot = 0.0
                for d, _cc in inf["atk"]:
                    e = fv2._efectivo(d, inf["et"], i_su["wk"], i_su["rs"])
                    if e > pot:
                        pot = e
                v[c3 + 0] = min(pot, 300.0) / 300.0
                v[c3 + 1] = 1.0 if (hp_su > 0.0 and pot >= hp_su) else 0.0
                v[c3 + 2] = 1.0 if ct == 5 else 0.0                 # energía básica

        # ---- C: el Pokémon EN JUEGO al que apunta (72..84)
        b = 72
        obj, j_obj = _objetivo_en_juego(o, cur, yo)
        if obj is not None:
            io = fv2._info(obj.get("id"))
            hpo = float(obj.get("hp") or 0.0)
            mx = float(obj.get("maxHp") or 0.0)
            v[b + 0] = 1.0
            v[b + 1] = 1.0 if j_obj == yo else 0.0
            es_act = obj is _act(jug[j_obj]) if (j_obj is not None and 0 <= j_obj < len(jug)) else False
            v[b + 2] = 1.0 if es_act else 0.0
            v[b + 3] = min(hpo, 400.0) / 400.0
            v[b + 4] = (hpo / mx) if mx > 0 else 0.0
            v[b + 5] = min(len(obj.get("energies") or ()), 5.0) / 5.0
            v[b + 6] = io["prz"] / 3.0
            rival_obj = su_act if j_obj == yo else mi_act
            pag, potp, _, mata, _ = fv2._ofensiva(obj, rival_obj)
            v[b + 7] = min(pag, 300.0) / 300.0
            v[b + 8] = mata
            v[b + 9] = 1.0 if (j_obj == yo and hpo > 0.0 and dmg_riv >= hpo) else 0.0
            v[b + 10] = min(io["rc"], 4.0) / 4.0
            v[b + 11] = min(len(obj.get("tools") or ()), 3.0) / 3.0
            v[b + 12] = 1.0 if obj.get("appearThisTurn") else 0.0

        # ---- D: el ataque concreto (85..94)
        b = 85
        aid = o.get("attackId")
        if aid is not None:
            a = _atk(int(aid))
            if a is not None:
                d = float(fv2._dmg(a))
                efd = fv2._efectivo(d, i_mi["et"], i_su["wk"], i_su["rs"])
                txt = (a.get("text") or "").lower()
                v[b + 0] = 1.0
                v[b + 1] = min(d, 300.0) / 300.0
                v[b + 2] = min(efd, 300.0) / 300.0
                v[b + 3] = 1.0 if (hp_su > 0.0 and efd >= hp_su) else 0.0
                v[b + 4] = min(efd / hp_su, 2.0) / 2.0 if hp_su > 0 else 0.0
                v[b + 5] = min(len(a.get("energies") or ()), 5.0) / 5.0
                v[b + 6] = 1.0 if ("coin" in txt or "flip" in txt) else 0.0
                v[b + 7] = 1.0 if "discard" in txt else 0.0
                v[b + 8] = 1.0 if ("heal" in txt or "damage counter" in txt) else 0.0
                v[b + 9] = i_su["prz"] / 3.0 if (hp_su > 0.0 and efd >= hp_su) else 0.0
    return O, C


if __name__ == "__main__":
    print("DIM_S =", DIM_S, " DIM_O =", DIM_O)
