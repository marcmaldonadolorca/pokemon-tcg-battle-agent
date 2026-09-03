#!/usr/bin/env python3
"""Política GREEDY de 1 ply sobre la función de valor v2 (sin MCTS).

Hipótesis (research/notas/agente-greedy-valor.md): la red v2 predice el ganador
al 75,4% desde un estado, pero como evaluación de hojas del ISMCTS no aportó
nada. Si el problema es el ÁRBOL (rollouts largos con política mediocre, ruido de
las determinizaciones, profundidad efectiva mínima) y no la EVALUACIÓN, usar la
red directamente como política debería batir al heurístico.

Arquitectura:
- Por decisión no trivial: K determinizaciones del InfoTracker; por cada una un
  `search_begin` (~0,13 ms) y, desde ESE searchId raíz, un `search_step` por
  acción candidata (el re-step desde un mismo sid es determinista, igual que la
  expansión de hijos de mcts.py). El estado hijo se evalúa con
  `features_v2.extrae` + la red 62→32→16→1 (`valor_v2.npz`), en LOTE.
- Perspectiva: los rasgos van siempre desde el punto de vista de `yourIndex`.
  Tras aplicar la acción puede tocarle al rival, así que se evalúa con una copia
  superficial de `current` con `yourIndex = me` (lo mismo que `mcts._evalua`).
- Agregación: media del valor por acción sobre las determinizaciones; argmax.
  `GREEDY_MARGEN` exige superar a la acción heurística (candidata 0) por ese
  margen para desviarse de ella (0 = argmax puro).
- Triviales sin evaluar; fallback al heurístico ante cualquier excepción;
  controlador de reloj idéntico en forma al de mcts.py; `search_end()` en
  `finally`; TODA acción devuelta pasa `heuristico._es_legal`.

Contrato: agent(obs) -> list[int]; DECK = 60 IDs.
Config por entorno: GREEDY_K (dets, def. 4), GREEDY_TOPE (s/decisión, def. 1.0),
GREEDY_CAP (candidatas raíz, def. 24), GREEDY_MARGEN (def. 0.0),
GREEDY_PESOS (ruta del .npz, def. research/valor/valor_v2.npz),
GREEDY_RASGOS ("v2" | "v1", def. v2).
"""
import os
import sys
import random
import time as _time

_T_IMPORT = _time.perf_counter()

_DIR = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_DIR)                      # research/
for _p in (_DIR, _RAIZ, os.path.join(_RAIZ, "valor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import heuristico                     # política de referencia, fallback y legalidad
import search_wrapper as sw           # binding ctypes verificado (importa libcg)
from tracker import InfoTracker, MirrorModel

_RASGOS_NOMBRE = os.environ.get("GREEDY_RASGOS", "v2")
if _RASGOS_NOMBRE == "v1":
    import features as _feats
    _PESOS_DEF = os.path.join(_RAIZ, "valor", "valor.npz")
else:
    import features_v2 as _feats
    _PESOS_DEF = os.path.join(_RAIZ, "valor", "valor_v2.npz")

CARGA_S = _time.perf_counter() - _T_IMPORT

DECK = list(heuristico.DECK)

# ----------------------------------------------------------------- parámetros
K_DETS = int(os.environ.get("GREEDY_K", "4"))
TOPE = float(os.environ.get("GREEDY_TOPE", "1.0"))
CAP_RAIZ = int(os.environ.get("GREEDY_CAP", "24"))
MARGEN = float(os.environ.get("GREEDY_MARGEN", "0.0"))
SIGNO = float(os.environ.get("GREEDY_SIGNO", "1.0"))   # -1 = argmin (test de orientación)
# Dónde se aplica la red y sobre qué estado se evalúa (ver la nota, §diagnóstico):
#   "todo"  1 ply puro sobre TODAS las candidatas (la hipótesis original)
#   "fase"  1 ply, pero en la fase principal solo se comparan candidatas de la misma
#           clase que la heurística (finales de turno {13,14} vs desarrollo): un
#           estado «mi turno sigue» y otro «turno del rival» no son comparables
#   "turno" 1 ply + COMPLETADO del turno con la heurística: cada candidata se evalúa
#           en la MISMA frontera de fase (cuando el turno pasa al rival)
#   "cartas" como "turno" pero SOLO en los selects de elegir cartas (type 1), donde
#           la heurística es más pobre; el resto lo decide ella
MODO = os.environ.get("GREEDY_MODO", "todo")
PASOS_TURNO = int(os.environ.get("GREEDY_PASOS", "40"))   # tope del completado
FINALES = (13, 14)      # option types que cierran el turno: 13 atacar, 14 terminar
RESERVA = 40.0            # s de banco que nunca se tocan
UMBRAL_DEGRADA = 0.02     # presupuesto menor => heurístico puro (greedy es barato)

# ------------------------------------------------------------------ la red v2
_W = None
_W_ERR = None


def _pesos():
    """Carga los pesos una vez. Si no están, la red no está disponible."""
    global _W, _W_ERR
    if _W is not None or _W_ERR is not None:
        return _W
    rutas = [os.environ.get("GREEDY_PESOS") or _PESOS_DEF,
             "/kaggle_simulations/agent/valor_v2.npz"]
    for r in rutas:
        try:
            if r and os.path.exists(r):
                d = np.load(r)
                _W = {k: d[k].astype(np.float32)
                      for k in ("W1", "b1", "W2", "b2", "W3", "b3")}
                return _W
        except Exception as e:
            _W_ERR = e
    _W_ERR = _W_ERR or FileNotFoundError("pesos de valor no encontrados")
    return None


def _red(X):
    """X: (n, DIM) float32 -> (n,) probabilidad de ganar en [0,1]."""
    p = _pesos()
    if p is None:
        return np.full(len(X), 0.5, dtype=np.float32)
    h = np.maximum(X @ p["W1"] + p["b1"], 0.0)
    h = np.maximum(h @ p["W2"] + p["b2"], 0.0)
    z = (h @ p["W3"] + p["b3"]).ravel()
    return 1.0 / (1.0 + np.exp(-z))


# ------------------------------------------------------- estado y estadística
_TRACKER = None
_MODELO = None
_TRACKER_ROTO = False
_RNG = random.Random((os.getpid() << 16) ^ int(_time.time_ns() & 0xFFFF))

TIEMPOS = []
ESTAD = {
    "decisiones": 0, "triviales": 0, "greedy": 0, "heuristicas": 0,
    "degradadas_presupuesto": 0, "fallback_busqueda": 0, "accion_ilegal": 0,
    "det_fallida": 0, "dets": 0, "steps": 0, "errores_step": 0,
    "evaluaciones": 0, "terminales": 0, "cands_tot": 0,
    "coincide_heuristico": 0, "desvia": 0, "empate_plano": 0,
    "tracker_roto": 0, "sin_red": 0,
    "delta_mejor_heur": 0.0,      # suma de (v_mejor − v_heurística) en las desviaciones
    "primera_llamada_s": 0.0, "carga_s": CARGA_S,
}


# ------------------------------------------------------------------ utilidades
def _plano(st):
    """{'searchId', 'observation': {...}} -> {'searchId', 'select', 'current'}."""
    ob = st.get("observation")
    if ob is not None:
        return {"searchId": st["searchId"], "select": ob.get("select"),
                "current": ob.get("current")}
    return st


def _terminal(st, me):
    """Valor terminal [0,1] desde mi perspectiva, o None si no es terminal."""
    cur = st.get("current")
    r = (cur or {}).get("result", -1)
    if st.get("select") is None or (r is not None and r >= 0):
        if r == me:
            return 1.0
        if r == 1 - me:
            return 0.0
        return 0.5
    return None


def _rasgos(cur, me):
    """Rasgos del estado SIEMPRE desde la perspectiva de `me`."""
    if cur.get("yourIndex") != me:
        c = dict(cur)              # copia superficial: solo cambia la perspectiva
        c["yourIndex"] = me
        cur = c
    return _feats.extrae(cur)


def _accion_heuristica(sel, cur):
    acc = None
    try:
        acc = heuristico._politica(sel, cur)
    except Exception:
        acc = None
    if not heuristico._es_legal(acc, sel):
        acc = heuristico._fallback(sel)
    return acc


def _candidatas(sel, cur, rng, cap):
    """Acciones legales candidatas; la heurística SIEMPRE primera (índice 0).
    Copiada de mcts._candidatas (fontanería ya depurada; mcts.py no se toca)."""
    ops = sel["option"]
    mn, mx, n = sel["minCount"], sel["maxCount"], len(ops)
    if n == 0:
        return [[0]] if mn >= 1 else [[]]
    out, vistos = [], set()

    def anhade(a):
        k = tuple(sorted(a))
        if k not in vistos and heuristico._es_legal(a, sel):
            vistos.add(k)
            out.append(a)

    if mx <= 1:
        if mn == 0:
            anhade([])
        for i in range(n):
            anhade([i])
    elif mn == n:
        anhade(list(range(n)))
    else:
        anhade(heuristico._fallback(sel))
        if mn == 0:
            anhade([])
        idx = list(range(n))
        for k in {mn, min(mx, n)}:
            if mn <= k <= min(mx, n) and k > 0:
                for _ in range(8):
                    anhade(sorted(rng.sample(idx, k)))
    heur = None
    try:
        h = heuristico._politica(sel, cur)
        if heuristico._es_legal(h, sel):
            heur = h
    except Exception:
        pass
    if heur is not None:
        kh = tuple(sorted(heur))
        out = [a for a in out if tuple(sorted(a)) != kh]
        out.insert(0, heur)
    out = out[:cap]
    return out or [heuristico._fallback(sel)]


def _clase_final(sel, acc):
    """True si la acción cierra el turno (atacar o terminar) en la fase principal."""
    if sel["type"] != 0 or len(acc) != 1:
        return False
    return sel["option"][acc[0]].get("type") in FINALES


def _filtra_fase(sel, cands):
    """Deja solo las candidatas de la misma clase que la heurística (cands[0])."""
    if sel["type"] != 0 or len(cands) < 2:
        return cands
    obj = _clase_final(sel, cands[0])
    out = [a for a in cands if _clase_final(sel, a) == obj]
    return out or cands


def _completa_turno(st, me):
    """Juega con la heurística hasta que el turno pase al rival (o terminal).
    Devuelve (estado, valor_terminal|None). Hace comparables las candidatas:
    todas se evalúan en la misma frontera de fase."""
    getattr(heuristico, "_T10", {}).clear()   # presupuesto fresco de type 10
    for _ in range(PASOS_TURNO):
        v = _terminal(st, me)
        if v is not None:
            return st, v
        if st["current"].get("yourIndex") != me:
            return st, None                   # frontera: ya juega el rival
        acc = _accion_heuristica(st["select"], st["current"])
        r = sw.search_step(st["searchId"], acc)
        st2 = r.get("state")
        ESTAD["steps_turno"] = ESTAD.get("steps_turno", 0) + 1
        if r.get("error") or not st2:
            ESTAD["errores_step"] += 1
            return st, None
        st = _plano(st2)
    return st, None


def _greedy(obs, sel, presupuesto, t0):
    """1 ply: aplica cada candidata en K determinizaciones y evalúa con la red.
    Devuelve la acción, o None (el llamante degrada a heurístico)."""
    me = obs["current"]["yourIndex"]
    rng = _RNG
    cands = _candidatas(sel, obs["current"], rng, CAP_RAIZ)
    if MODO == "fase":
        cands = _filtra_fase(sel, cands)
    if len(cands) == 1:
        return cands[0]
    ESTAD["cands_tot"] += len(cands)
    if _pesos() is None:
        ESTAD["sin_red"] += 1
        return None

    sumas = [0.0] * len(cands)
    cuentas = [0] * len(cands)
    margen = 0.05 * presupuesto + 0.005
    for k in range(K_DETS):
        if (_time.perf_counter() - t0) > presupuesto - margen:
            break
        det = _TRACKER.sample(rng, _MODELO)
        res = sw.search_begin(obs, **det)
        st = res.get("state")
        if res.get("error") or not st:
            ESTAD["det_fallida"] += 1
            c = f"det_err_{res.get('error')}"
            ESTAD[c] = ESTAD.get(c, 0) + 1
            continue
        raiz = _plano(st)
        sid = raiz["searchId"]
        if _terminal(raiz, me) is not None:
            continue
        ESTAD["dets"] += 1
        filas, idx = [], []
        for i, acc in enumerate(cands):
            r = sw.search_step(sid, acc)
            st2 = r.get("state")
            ESTAD["steps"] += 1
            if r.get("error") or not st2:
                ESTAD["errores_step"] += 1
                sumas[i] += 0.0          # una acción que rompe el motor es lo peor
                cuentas[i] += 1
                continue
            st2 = _plano(st2)
            v = _terminal(st2, me)
            if v is None and MODO in ("turno", "cartas"):
                st2, v = _completa_turno(st2, me)
            if v is not None:
                ESTAD["terminales"] += 1
                sumas[i] += v
                cuentas[i] += 1
            else:
                filas.append(_rasgos(st2["current"], me))
                idx.append(i)
        if filas:
            vs = _red(np.stack(filas))
            ESTAD["evaluaciones"] += len(vs)
            for j, i in enumerate(idx):
                sumas[i] += float(vs[j])
                cuentas[i] += 1

    if not any(cuentas):
        return None
    val = [SIGNO * (sumas[i] / cuentas[i]) if cuentas[i] else -1e9
           for i in range(len(cands))]
    mejor = max(range(len(cands)), key=lambda i: val[i])
    v_h = val[0]
    if mejor != 0 and val[mejor] - v_h <= MARGEN:
        mejor = 0                       # sin ventaja clara, manda la heurística
    if mejor == 0:
        ESTAD["coincide_heuristico"] += 1
    else:
        ESTAD["desvia"] += 1
        ESTAD["delta_mejor_heur"] += val[mejor] - v_h
    vivos = [val[i] for i in range(len(cands)) if cuentas[i]]
    if max(vivos) - min(vivos) < 1e-6:
        ESTAD["empate_plano"] += 1
    return cands[mejor]


def _jugadas_restantes(cur):
    try:
        prem = max(sum(1 for c in (p.get("prize") or []) if c is None)
                   for p in cur["players"])
        return 8 + 12 * prem
    except Exception:
        return 60


# ------------------------------------------------------------------ el agente
def agent(obs) -> list:
    global _TRACKER, _MODELO, _TRACKER_ROTO
    t0 = _time.perf_counter()
    primera = not TIEMPOS
    try:
        sel = obs["select"]
        if not _TRACKER_ROTO:
            try:
                if _TRACKER is None:
                    _TRACKER = InfoTracker(DECK)
                    _MODELO = MirrorModel(DECK)
                _TRACKER.update(obs)
            except Exception:
                _TRACKER_ROTO = True
                ESTAD["tracker_roto"] += 1

        if sel is None:
            return list(DECK)

        ESTAD["decisiones"] += 1
        n, mn, mx = len(sel["option"]), sel["minCount"], sel["maxCount"]
        if n == 0:                             # confirmación (type 0, context 7)
            ESTAD["triviales"] += 1
            return [0] if mn >= 1 else []
        if n == 1 and mn >= 1:
            ESTAD["triviales"] += 1
            return [0]
        if mn == n and mx >= n:
            ESTAD["triviales"] += 1
            return list(range(n))

        rot = obs.get("remainingOverageTime", 600) or 600
        rest = max(_jugadas_restantes(obs.get("current")), 20)
        presupuesto = min(TOPE, (rot - RESERVA) / rest)

        acc = None
        # Con cualquier carta rival boca abajo el motor rechaza la determinización
        # (error 2, medido en mcts.py): buscar ahí es tiempo tirado.
        buscable = (presupuesto >= UMBRAL_DEGRADA and not _TRACKER_ROTO
                    and (MODO != "cartas" or sel["type"] == 1)
                    and _TRACKER is not None and _TRACKER._cur is not None
                    and getattr(_TRACKER, "rival_bocabajo_n", 0) == 0)
        if buscable:
            _t10 = getattr(heuristico, "_T10", {})
            _t10_bak = {k: list(v) for k, v in _t10.items()}
            try:
                acc = _greedy(obs, sel, presupuesto, t0)
                if acc is None:
                    ESTAD["fallback_busqueda"] += 1
            except Exception:
                ESTAD["fallback_busqueda"] += 1
                acc = None
            finally:
                _t10.clear()
                _t10.update(_t10_bak)
                try:
                    sw.search_end()
                except Exception:
                    pass
            if acc is not None:
                ESTAD["greedy"] += 1
        else:
            ESTAD["degradadas_presupuesto"] += 1

        if acc is None:
            ESTAD["heuristicas"] += 1
            acc = _accion_heuristica(sel, obs["current"])
        if not heuristico._es_legal(acc, sel):
            ESTAD["accion_ilegal"] += 1
            acc = heuristico._fallback(sel)
        return acc
    finally:
        dt = _time.perf_counter() - t0
        TIEMPOS.append(dt)
        if primera:
            ESTAD["primera_llamada_s"] = dt + CARGA_S
