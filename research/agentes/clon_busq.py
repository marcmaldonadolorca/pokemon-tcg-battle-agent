#!/usr/bin/env python3
"""CLON + DESEMPATE POR SIMULACIÓN (vía 3): la red propone, la búsqueda desempata.

Qué cambia respecto al ISMCTS que fracasó (`mcts.py`, 0,529 sin significación): allí
la búsqueda tenía que ENCONTRAR la jugada entre 24 candidatas con una política de
rollout heurística flojísima. Aquí la red ya juega bien y solo se le pide a la
simulación que rompa empates: las candidatas son las `C` mejores de la red, y solo
se busca cuando están CERCA en puntuación (`MARGEN`), que es donde la red es
indiferente — medido: jugar con ruido Gumbel tau=0,5, que cambia el 33% de las
decisiones, cuesta 0,502 [0,462, 0,542] contra el argmax, es decir NADA. Si esas
decisiones son de verdad indiferentes no hay nada que ganar; si no lo son, este es
el sitio donde mirar.

Cada candidata se evalúa con `K` determinizaciones × un rollout truncado a `R`
selects con la PROPIA RED pilotando los dos lados dentro de la búsqueda, y la
evaluación de material de `mcts._evalua` al final (varianza mucho menor que un
resultado binario con tan pocas muestras).

Blindaje: `search_end()` en `finally`, no se busca con cartas rivales boca abajo
(`rival_bocabajo_n > 0`: el motor rechaza esa determinización con error 2), toda
acción devuelta pasa `heuristico._es_legal` y cae al clon/heurístico si no.
Parámetros por entorno: `CB_K`, `CB_C`, `CB_R`, `CB_MARGEN`, `CB_PESOS`.
"""
import importlib.util
import os
import random
import sys
import time as _time

import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
for _p in (_D, os.path.join(_D, "..", "clon"), os.path.join(_D, "..")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

import rasgos                                   # noqa: E402
import search_wrapper as sw                     # noqa: E402
from tracker import InfoTracker, MirrorModel    # noqa: E402


def _carga(nombre, ruta):
    s = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


_heur = _carga("cb_heur", os.path.join(_D, "heuristico.py"))
_mcts = _carga("cb_mcts", os.path.join(_D, "mcts.py"))

DECK = list(_heur.DECK)


def _busca(nombre):
    """Tolerante a las DOS disposiciones: el repo (agentes/ + clon/ + valor/) y el
    paquete de envio, donde --extra deja todo junto en agentes/."""
    for _p in (_D, os.path.join(_D, "..", "clon"), os.path.join(_D, "..", "agentes")):
        r = os.path.join(_p, nombre)
        if os.path.exists(r):
            return r
    return os.path.join(_D, nombre)


_RUTA = os.environ.get("CB_PESOS") or _busca("politica.npz")

K_DETS = int(os.environ.get("CB_K", "8"))
N_CAND = int(os.environ.get("CB_C", "3"))
R_PASOS = int(os.environ.get("CB_R", "16"))
MARGEN = float(os.environ.get("CB_MARGEN", "1.5"))
RESERVA = 40.0
TOPE = float(os.environ.get("CB_TOPE", "1.0"))

_P = None
# Un tracker POR ASIENTO (yourIndex) y reinicio cuando el turno retrocede. El
# tracker es estado que se acumula partida a partida: con un unico global, un
# proceso que juega varias seguidas arrastra el de la anterior (medido: 138
# excepciones de 348 decisiones) y un modulo que pilota LOS DOS bandos mezcla las
# dos perspectivas en el mismo objeto. En produccion hay un proceso por agente,
# pero auditar.py y los espejos en un solo proceso si lo tocan.
_TRK = {}
_RNG = random.Random((os.getpid() << 16) ^ int(_time.time_ns() & 0xFFFF))

ESTAD = {"decisiones": 0, "buscadas": 0, "sin_margen": 0, "no_buscable": 0,
         "cambia": 0, "det_fallida": 0, "err_step": 0, "excepcion": 0,
         "ilegal": 0, "rollouts": 0, "s_busqueda": 0.0}


def _pesos():
    global _P
    if _P is None:
        z = np.load(_RUTA)
        _P = {k: z[k] for k in ("W1s", "W1o", "b1", "W2", "b2", "w3", "b3", "bc")}
        _P["ncart"] = len(_P["bc"])
    return _P


def _puntua(sel, cur):
    P = _pesos()
    s = rasgos.rasgos_estado(sel, cur)
    O, C = rasgos.rasgos_opciones(sel, cur)
    if len(O) == 0:
        return None
    h1 = np.maximum(s @ P["W1s"] + O @ P["W1o"] + P["b1"], 0.0)
    h2 = np.maximum(h1 @ P["W2"] + P["b2"], 0.0)
    z = (h2 @ P["w3"]).ravel() + P["b3"][0]
    nc = P["ncart"]
    ci = np.where((C >= 0) & (C < nc - 1), C, nc - 1)
    return z + P["bc"][ci]


def _elige(z, k, mn, mx):
    """La regla de research/agentes/clon.py, sobre las puntuaciones dadas."""
    hay_pasa = len(z) == k + 1
    zo = z[:k]
    orden = np.argsort(-zo)
    if mn == mx:
        return [int(i) for i in orden[:mn]]
    if hay_pasa:
        umbral = float(z[k])
        sel_i = [int(i) for i in orden[:mn]]
        for i in orden[mn:mx]:
            if float(zo[i]) > umbral:
                sel_i.append(int(i))
            else:
                break
        return sel_i
    return [int(i) for i in orden[:max(mn, 1)]]


def _accion_red(sel, cur):
    opt = sel.get("option") or []
    if not opt:
        return [0]
    z = _puntua(sel, cur)
    if z is None:
        return None
    return _elige(z, len(opt), int(sel.get("minCount") or 0),
                  int(sel.get("maxCount") or 1))


def _candidatas(sel, cur, z):
    """Las N_CAND mejores acciones DISTINTAS: se fuerza cada opción del top a ir
    primera y se deja que la regla de selección construya la acción entera (así
    vale igual para los selects de multi-selección)."""
    opt = sel.get("option") or []
    k = len(opt)
    mn = int(sel.get("minCount") or 0)
    mx = int(sel.get("maxCount") or 1)
    base = _elige(z, k, mn, mx)
    cands = [base]
    puntos = [float(np.max(z[:k])) if k else 0.0]
    orden = list(np.argsort(-z))
    for j in orden[:N_CAND + 2]:
        if len(cands) >= N_CAND:
            break
        z2 = z.copy()
        z2[j] = float(np.max(z)) + 10.0
        a = _elige(z2, k, mn, mx)
        if sorted(a) not in [sorted(c) for c in cands]:
            cands.append(a)
            puntos.append(float(z[j]))
    return cands, puntos


def _rollout(st, me):
    """Los DOS lados juegan la red dentro de la búsqueda; trunca y evalúa material."""
    for _ in range(R_PASOS):
        v = _mcts._terminal(st, me)
        if v is not None:
            return v
        acc = _accion_red(st["select"], st["current"])
        if acc is None or not _heur._es_legal(acc, st["select"]):
            acc = _heur._fallback(st["select"])
        res = sw.search_step(st["searchId"], acc)
        st2 = res.get("state")
        if res.get("error") or not st2:
            ESTAD["err_step"] += 1
            return _mcts._evalua(st["current"], me)
        st = _mcts._plano(st2)
    return _mcts._evalua(st["current"], me)


def _desempata(obs, cands, e):
    """Valor medio de cada candidata sobre K determinizaciones. None si no se pudo."""
    me = obs["current"]["yourIndex"]
    suma = [0.0] * len(cands)
    n = 0
    for _ in range(K_DETS):
        det = e["trk"].sample(_RNG, e["mod"])
        res = sw.search_begin(obs, **det)
        st = res.get("state")
        if res.get("error") or not st:
            ESTAD["det_fallida"] += 1
            continue
        raiz = _mcts._plano(st)
        for i, a in enumerate(cands):
            r = sw.search_step(raiz["searchId"], a)
            s2 = r.get("state")
            if r.get("error") or not s2:
                ESTAD["err_step"] += 1
                suma[i] += 0.5
                continue
            hijo = _mcts._plano(s2)
            v = _mcts._terminal(hijo, me)
            suma[i] += v if v is not None else _rollout(hijo, me)
            ESTAD["rollouts"] += 1
        n += 1
    if n == 0:
        return None
    return [s / n for s in suma]


def _estado(cur):
    """Tracker del asiento que decide; nuevo si el turno retrocede (partida nueva)."""
    yo = (cur or {}).get("yourIndex", 0)
    t = float((cur or {}).get("turn") or 0)
    e = _TRK.get(yo)
    if e is None or t < e["turno"]:
        e = {"trk": InfoTracker(DECK), "mod": MirrorModel(DECK),
             "turno": t, "roto": False}
        _TRK[yo] = e
    e["turno"] = t
    return e


def agent(obs) -> list:
    sel = obs["select"]
    if sel is None:
        return list(DECK)
    cur = obs["current"]
    e = _estado(cur)
    if not e["roto"]:
        try:
            e["trk"].update(obs)
        except Exception:
            e["roto"] = True
    ESTAD["decisiones"] += 1
    acc = None
    try:
        opt = sel.get("option") or []
        z = _puntua(sel, cur) if opt else None
        acc = _elige(z, len(opt), int(sel.get("minCount") or 0),
                     int(sel.get("maxCount") or 1)) if z is not None else [0]
        buscable = (not e["roto"] and e["trk"]._cur is not None
                    and getattr(e["trk"], "rival_bocabajo_n", 0) == 0
                    and z is not None and len(z) >= 2
                    and (obs.get("remainingOverageTime", 600) or 600) > RESERVA + 60)
        if not buscable:
            ESTAD["no_buscable"] += 1
        else:
            cands, pts = _candidatas(sel, cur, z)
            if len(cands) < 2 or (pts[0] - min(pts[1:])) > MARGEN:
                ESTAD["sin_margen"] += 1
            else:
                t0 = _time.perf_counter()
                try:
                    vals = _desempata(obs, cands, e)
                finally:
                    try:
                        sw.search_end()
                    except Exception:
                        pass
                ESTAD["s_busqueda"] += _time.perf_counter() - t0
                if vals is not None:
                    ESTAD["buscadas"] += 1
                    mej = cands[int(np.argmax(vals))]
                    if sorted(mej) != sorted(acc):
                        ESTAD["cambia"] += 1
                    acc = mej
    except Exception as e:
        ESTAD["excepcion"] += 1
        if os.environ.get("CB_DEBUG"):
            import traceback
            ESTAD.setdefault("trazas", []).append(traceback.format_exc()[-600:])
        acc = None
    if acc is not None and _heur._es_legal(acc, sel):
        return acc
    if acc is not None:
        ESTAD["ilegal"] += 1
    try:
        a2 = _heur._politica(sel, cur)
    except Exception:
        a2 = None
    return a2 if _heur._es_legal(a2, sel) else _heur._fallback(sel)
