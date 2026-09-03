#!/usr/bin/env python3
"""AUTO-JUEGO: el clon genera su PROPIO corpus jugando, para pasar de imitar a mejorar.

Por qué existe: `extraer.py` saca pares (estado, opciones, acción) de los replays
ajenos, así que el techo del clon es parecerse a los equipos de la ladder. Aquí los
pares los produce el clon jugando: contra sí mismo (espejo) y contra los arquetipos
del campo, con exploración, y luego se filtra por RESULTADO.

Cómo explora: Gumbel sobre las puntuaciones de la red. `z + tau*Gumbel(0,1)` es
exactamente muestrear de `softmax(z/tau)` (truco de Gumbel-max), y aplicado a la
ORDENACIÓN es Gumbel-top-k, es decir muestreo sin reemplazo — que es lo que hacen
falta en los selects con `maxCount > 1`. `tau=0` reproduce el argmax de clon.py.

Salida .npz: el MISMO esquema que `research/clon/extraer.py` (S, O, C, ptr, T, y,
ep, meta) más tres columnas propias:
    gan  (n,) float32  1.0 si la decisión la tomó el bando que GANÓ la partida
    exp  (n,) float32  1.0 si el ruido cambió la acción respecto al argmax
    dk   (n,) int32    índice de la baraja que pilotaba ese bando
`meta` conserva el layout de extraer.py — [type, context, turno, 0, 0, npos, nsel, 0]
— para que el entrenador pueda concatenar los dos corpus sin casos especiales.

Blindaje idéntico al de producción: toda la ruta va en try, la acción se valida con
`heuristico._es_legal` y, si falla, se juega la heurística y la decisión NO se graba
(no queremos enseñarle a la red jugadas que no salieron de ella).

Uso:
  .venv/bin/python research/clon/autojuego.py --n 4000 --procs 3 --tau 0.5 \
      --pesos research/clon/politica.npz --salida data/clon/sp_r1.npz
"""
import argparse
import csv
import importlib.util
import multiprocessing as mp
import os
import sys
import time

import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(_D))
sys.path.insert(0, _D)
sys.path.insert(0, RAIZ)
import rasgos  # noqa: E402

# Share real del campo (research/gauntlet.py, censo sobre 18.674 barajas).
CAMPO = {
    "c1-grimmsnarl": 0.3117, "c2-alakazam": 0.1825, "c3-lopunny-froslass": 0.1278,
    "c4-dragapult": 0.0816, "c5-kangaskhan-crustle": 0.0686, "c6-ogerpon": 0.0495,
    "c7-lucario-campo": 0.0395, "c8-dipplin-grookey": 0.0349, "x2-hydrapple": 0.0254,
    "x1-slowking": 0.0175, "x3-cynthia-garchomp": 0.0157, "x4-ns-zoroark": 0.0084,
}
# Las dos listas que se van a enviar/medir pesan la mitad del corpus; la otra mitad
# es el campo con su share real. Así el corpus cubre el estado que de verdad
# visitaremos sin dejar de ver barajas raras.
PROPIAS = {"c2-alakazam": 0.25, "mega-lucario": 0.25}


def _ruta_deck(nombre):
    for sub in ("campo", "propios", "meta"):
        fp = os.path.join(RAIZ, "research", "decks", sub, nombre + ".csv")
        if os.path.exists(fp):
            return fp
    raise SystemExit("baraja no encontrada: " + nombre)


def lee_deck(nombre):
    with open(_ruta_deck(nombre)) as f:
        return [int(r[0]) for r in csv.reader(f) if r and r[0].strip().isdigit()]


def catalogo_barajas():
    pesos = {}
    for k, w in CAMPO.items():
        pesos[k] = pesos.get(k, 0.0) + 0.5 * w
    for k, w in PROPIAS.items():
        pesos[k] = pesos.get(k, 0.0) + w
    nombres = sorted(pesos)
    p = np.array([pesos[k] for k in nombres], float)
    return nombres, p / p.sum()


# --------------------------------------------------------------- worker global
_heur = None
_P = None
_DECKS = None


def _init(ruta_pesos, decks):
    global _heur, _P, _DECKS
    s = importlib.util.spec_from_file_location(
        "heur_sp", os.path.join(RAIZ, "research", "agentes", "heuristico.py"))
    _heur = importlib.util.module_from_spec(s)
    s.loader.exec_module(_heur)
    z = np.load(ruta_pesos)
    _P = {k: z[k] for k in ("W1s", "W1o", "b1", "W2", "b2", "w3", "b3", "bc")}
    _P["ncart"] = len(_P["bc"])
    _DECKS = decks


def _puntua(s, O, C):
    P = _P
    h1 = np.maximum(s @ P["W1s"] + O @ P["W1o"] + P["b1"], 0.0)
    h2 = np.maximum(h1 @ P["W2"] + P["b2"], 0.0)
    z = (h2 @ P["w3"]).ravel() + P["b3"][0]
    nc = P["ncart"]
    ci = np.where((C >= 0) & (C < nc - 1), C, nc - 1)
    return z + P["bc"][ci]


def _elige(z, k, mn, mx):
    """La MISMA regla de research/agentes/clon.py, sobre las puntuaciones dadas."""
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


def _decide(sel, cur, rng, tau):
    """(accion, datos_para_grabar). datos=None si la decisión no enseña nada."""
    opt = sel.get("option") or []
    k = len(opt)
    if k == 0:
        return [0], None                       # confirmación (0,7)
    s = rasgos.rasgos_estado(sel, cur)
    O, C = rasgos.rasgos_opciones(sel, cur)
    if len(O) == 0:
        return None, None
    z = _puntua(s, O, C)
    mn = int(sel.get("minCount") or 0)
    mx = int(sel.get("maxCount") or 1)
    npos = len(z)
    if tau > 0.0:
        g = -np.log(-np.log(rng.random(npos) + 1e-12) + 1e-12)
        acc = _elige(z + tau * g.astype(np.float32), k, mn, mx)
        base = _elige(z, k, mn, mx)
        explor = 1.0 if sorted(acc) != sorted(base) else 0.0
    else:
        acc = _elige(z, k, mn, mx)
        explor = 0.0
    if npos < 2:
        return acc, None
    hay_pasa = npos == k + 1
    if len(acc) == 0:
        if not hay_pasa:
            return acc, None
        elegidas = [k]
    else:
        elegidas = sorted(set(acc))
    T = np.zeros(npos, np.float32)
    T[elegidas] = 1.0 / len(elegidas)
    meta = (float(sel.get("type", -1)), float(sel.get("context", -1)),
            float((cur or {}).get("turn") or 0), 0.0, 0.0,
            float(npos), float(len(elegidas)), 0.0)
    return acc, (s, O.astype(np.float16), C, npos, T, int(np.argmax(T)), meta, explor)


def _heuristica(sel, cur):
    try:
        acc = _heur._politica(sel, cur)
    except Exception:
        acc = None
    if not _heur._es_legal(acc, sel):
        acc = _heur._fallback(sel)
    return acc


def _tanda(t):
    """Juega un lote de partidas en este proceso y devuelve los pares grabados."""
    semilla, tau, pares = t
    from kaggle_environments import make
    rng = np.random.default_rng(semilla)
    S, O, C, tam, T, Y, M, G, E, DK, EP = [], [], [], [], [], [], [], [], [], [], []
    cnt = {"partidas": 0, "validas": 0, "fb": 0, "dec": 0}
    ep_id = 0
    for ia, ib in pares:
        deck = [_DECKS[ia], _DECKS[ib]]
        reg = [[], []]

        def hace(p):
            def ag(obs):
                sel = obs["select"]
                if sel is None:
                    return list(deck[p])
                cur = obs["current"]
                acc = dat = None
                try:
                    acc, dat = _decide(sel, cur, rng, tau)
                except Exception:
                    acc = dat = None
                if acc is None or not _heur._es_legal(acc, sel):
                    cnt["fb"] += 1
                    return _heuristica(sel, cur)
                if dat is not None:
                    reg[p].append(dat)
                return acc
            return ag

        env = make("cabt", configuration={"decks": deck}, debug=False)
        env.run([hace(0), hace(1)])
        cnt["partidas"] += 1
        r0 = env.state[0].reward
        if r0 not in (1, -1):
            continue                            # sin ganador: no hay señal
        cnt["validas"] += 1
        for p in (0, 1):
            if not reg[p]:
                continue
            gana = 1.0 if ((r0 == 1) == (p == 0)) else 0.0
            for (s, o, c, npos, tt, y, m, ex) in reg[p]:
                S.append(s)
                O.append(o)
                C.append(c)
                tam.append(npos)
                T.append(tt)
                Y.append(y)
                M.append(m)
                G.append(gana)
                E.append(ex)
                DK.append(ia if p == 0 else ib)
                EP.append(ep_id)
            cnt["dec"] += len(reg[p])
            ep_id += 1
    if not S:
        return None
    return (np.asarray(S, np.float32), np.concatenate(O), np.concatenate(C),
            np.asarray(tam, np.int32), np.concatenate(T), np.asarray(Y, np.int32),
            np.asarray(M, np.float32), np.asarray(G, np.float32),
            np.asarray(E, np.float32), np.asarray(DK, np.int32),
            np.asarray(EP, np.int32), cnt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000, help="partidas")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--tau", type=float, default=0.5, help="0 = argmax puro")
    ap.add_argument("--pesos", default=os.path.join(RAIZ, "research/clon/politica.npz"))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--lote", type=int, default=25, help="partidas por tarea")
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--barajas", default="", help="lista,separada por comas (por defecto: campo+propias)")
    a = ap.parse_args()

    if a.barajas:
        nombres = [x for x in a.barajas.split(",") if x]
        prob = np.full(len(nombres), 1.0 / len(nombres))
    else:
        nombres, prob = catalogo_barajas()
    decks = [lee_deck(n) for n in nombres]
    for n, d in zip(nombres, decks):
        if len(d) != 60:
            raise SystemExit("baraja %s tiene %d cartas" % (n, len(d)))
    rng = np.random.default_rng(a.semilla)
    ia = rng.choice(len(nombres), a.n, p=prob)
    ib = rng.choice(len(nombres), a.n, p=prob)
    pares = list(zip(ia.tolist(), ib.tolist()))
    tareas = [(a.semilla * 1000 + i, a.tau, pares[i:i + a.lote])
              for i in range(0, len(pares), a.lote)]

    print("barajas %d  partidas %d  tau %.2f  procs %d  tareas %d"
          % (len(nombres), a.n, a.tau, a.procs, len(tareas)), flush=True)
    t0 = time.time()
    res = []
    tot = {"partidas": 0, "validas": 0, "fb": 0, "dec": 0}
    with mp.Pool(a.procs, initializer=_init, initargs=(a.pesos, decks)) as pool:
        for j, r in enumerate(pool.imap_unordered(_tanda, tareas)):
            if r is None:
                continue
            res.append(r)
            for k in tot:
                tot[k] += r[-1][k]
            if (j + 1) % 10 == 0:
                dt = time.time() - t0
                print("  %d/%d tareas  %d partidas  %d decisiones  %.1f part/s"
                      % (j + 1, len(tareas), tot["partidas"], tot["dec"],
                         tot["partidas"] / dt), flush=True)
    if not res:
        raise SystemExit("sin datos")

    off = 0
    EPs = []
    for r in res:
        EPs.append(r[10] + off)
        off += int(r[10].max()) + 1
    S = np.concatenate([r[0] for r in res])
    O = np.concatenate([r[1] for r in res])
    C = np.concatenate([r[2] for r in res])
    tam = np.concatenate([r[3] for r in res])
    T = np.concatenate([r[4] for r in res])
    Y = np.concatenate([r[5] for r in res])
    M = np.concatenate([r[6] for r in res])
    G = np.concatenate([r[7] for r in res])
    E = np.concatenate([r[8] for r in res])
    DK = np.concatenate([r[9] for r in res])
    ep = np.concatenate(EPs).astype(np.int32)
    ptr = np.zeros(len(tam) + 1, np.int32)
    np.cumsum(tam, out=ptr[1:])
    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    np.savez(a.salida, S=S, O=O, C=C, ptr=ptr, T=T, y=Y, ep=ep, meta=M,
             gan=G, exp=E, dk=DK, barajas=np.array(nombres))
    dt = time.time() - t0
    print("\npartidas %d (con ganador %d)  decisiones %d  opciones %d (%.2f/dec)"
          % (tot["partidas"], tot["validas"], len(Y), len(O), len(O) / len(Y)))
    print("ganadoras %.1f%%   exploradas %.1f%%   fallbacks heuristicos %d"
          % (100.0 * G.mean(), 100.0 * E.mean(), tot["fb"]))
    print("%.2f partidas/s  %.0f s  fichero %.0f MB"
          % (tot["partidas"] / dt, dt, os.path.getsize(a.salida) / 1e6))


if __name__ == "__main__":
    main()
