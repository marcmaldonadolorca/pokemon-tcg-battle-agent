#!/usr/bin/env python3
"""Entrenador del clon, versión CORPUS GRANDE (memmap) — sucesor de entrenar2.py.

Mismo modelo, mismo corte por episodio (semilla 0) y mismos flags que entrenar2.py.
Añade tres cosas y nada más:

  * el corpus puede ser un DIRECTORIO de .npy (salida de research/clon/fusiona.py)
    que se abre con mmap_mode="r": 30 días son ~13 GB y no caben cómodos en los
    30 GB de RAM de la torre si se cargan de golpe;
  * --train-dias K  entrena solo con los K días MÁS RECIENTES (deriva de meta);
  * --test-dias K   mide el test solo en los K días más recientes (para poder
    comparar con la tanda de 7 días sin cambiar de vara).

(original)

Es `research/clon/entrenar.py` con cuatro añadidos y la misma arquitectura, el
mismo corte por episodio y la misma semilla de corte (0), para que los números
sean comparables celda a celda con la tanda original:

  --checkpoints 2,5,10,20   guarda pesos Y mide TEST en esas épocas (la curva de
                            épocas sale de UNA sola corrida, no de cuatro)
  --frac-ep 0.25            usa solo esa fracción de los EPISODIOS de train
                            (curva de aprendizaje; val y test intactos)
  --solo-ganador            entrena solo con las decisiones del jugador que GANÓ
                            (requiere meta con >= 10 columnas: extraer2.py)
  --capas 3                 mete una tercera capa oculta H3 = H2 // 2

Uso:
  .venv/bin/python research/clon/entrenar2.py data/clon/pol_1030.npz \
      --h1 192 --h2 96 --epocas 20 --checkpoints 2,5,10,20 \
      --prefijo research/clon/cap_h192
"""
import argparse
import json
import os
import sys
import time

import numpy as np


def softmax_bloques(z, loc, nb):
    mx = np.full(nb, -1e30, np.float32)
    np.maximum.at(mx, loc, z)
    e = np.exp(z - mx[loc])
    s = np.zeros(nb, np.float32)
    np.add.at(s, loc, e)
    return (e / s[loc]).astype(np.float32)


class Red:
    def __init__(self, ds, do, h1, h2, ncart, semilla=1, capas=2):
        g = np.random.default_rng(semilla)
        self.capas = capas
        self.W1s = (g.standard_normal((ds, h1)) / np.sqrt(ds)).astype(np.float32)
        self.W1o = (g.standard_normal((do, h1)) / np.sqrt(do)).astype(np.float32)
        self.b1 = np.zeros(h1, np.float32)
        self.W2 = (g.standard_normal((h1, h2)) / np.sqrt(h1)).astype(np.float32)
        self.b2 = np.zeros(h2, np.float32)
        h3 = max(h2 // 2, 8)
        if capas >= 3:
            self.W3 = (g.standard_normal((h2, h3)) / np.sqrt(h2)).astype(np.float32)
            self.b3h = np.zeros(h3, np.float32)
            ult = h3
        else:
            self.W3 = np.zeros((1, 1), np.float32)
            self.b3h = np.zeros(1, np.float32)
            ult = h2
        self.w3 = (g.standard_normal((ult, 1)) / np.sqrt(ult)).astype(np.float32)
        self.b3 = np.zeros(1, np.float32)
        self.bc = np.zeros(ncart, np.float32)

    @property
    def par(self):
        p = [self.W1s, self.W1o, self.b1, self.W2, self.b2, self.w3, self.b3, self.bc]
        if self.capas >= 3:
            p += [self.W3, self.b3h]
        return p

    def adelante(self, Sb, Ob, Cb, loc, nb, usa_cartas):
        Ps = Sb @ self.W1s
        a1 = Ps[loc] + (Ob @ self.W1o) + self.b1
        h1 = np.maximum(a1, 0.0)
        h2 = np.maximum(h1 @ self.W2 + self.b2, 0.0)
        if self.capas >= 3:
            h3 = np.maximum(h2 @ self.W3 + self.b3h, 0.0)
        else:
            h3 = h2
        z = (h3 @ self.w3).ravel() + self.b3[0]
        if usa_cartas:
            z = z + self.bc[Cb]
        return h1, h2, h3, z


def evalua(red, S, O, C, ptr, T, dec, usa_cartas, lote=8192):
    aciertos = 0.0
    ll = 0.0
    pred = np.zeros(len(dec), np.int64)
    for i0 in range(0, len(dec), lote):
        d = dec[i0:i0 + lote]
        filas = np.concatenate([np.arange(ptr[i], ptr[i + 1]) for i in d])
        tam = (ptr[d + 1] - ptr[d]).astype(np.int64)
        loc = np.repeat(np.arange(len(d)), tam)
        _, _, _, z = red.adelante(S[d], O[filas].astype(np.float32),
                                  C[filas], loc, len(d), usa_cartas)
        p = softmax_bloques(z, loc, len(d))
        despl = np.concatenate([[0], np.cumsum(tam)[:-1]])
        for j in range(len(d)):
            sl = slice(despl[j], despl[j] + tam[j])
            pp = p[sl]
            k = int(np.argmax(pp))
            pred[i0 + j] = k
            tt = T[filas[sl]]
            aciertos += 1.0 if tt[k] > 0 else 0.0
            ll -= float(np.sum(tt * np.log(np.maximum(pp, 1e-9))))
    return aciertos / len(dec), ll / len(dec), pred


def guarda(ruta, red, dim_s, dim_o, usa_cartas, acc):
    d = dict(W1s=red.W1s, W1o=red.W1o, b1=red.b1, W2=red.W2, b2=red.b2,
             w3=red.w3, b3=red.b3, bc=(red.bc if usa_cartas else np.zeros_like(red.bc)),
             dim_s=np.int32(dim_s), dim_o=np.int32(dim_o),
             test_top1=np.float32(acc), capas=np.int32(red.capas))
    if red.capas >= 3:
        d["W3"] = red.W3
        d["b3h"] = red.b3h
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    np.savez_compressed(ruta, **d)
    return os.path.getsize(ruta) / 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--prefijo", default="research/clon/cap")
    ap.add_argument("--epocas", type=int, default=20)
    ap.add_argument("--checkpoints", default="")
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--h1", type=int, default=96)
    ap.add_argument("--h2", type=int, default=0, help="0 = h1//2")
    ap.add_argument("--capas", type=int, default=2)
    ap.add_argument("--lote", type=int, default=2048)
    ap.add_argument("--l2", type=float, default=1e-6)
    ap.add_argument("--sin-cartas", action="store_true")
    ap.add_argument("--min-rating", type=float, default=0.0)
    ap.add_argument("--frac-ep", type=float, default=1.0)
    ap.add_argument("--solo-ganador", action="store_true")
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--train-dias", type=int, default=0, help="0 = todos")
    ap.add_argument("--test-dias", type=int, default=0, help="0 = todos")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    h2 = a.h2 or max(a.h1 // 2, 8)
    ck = sorted({int(x) for x in a.checkpoints.split(",") if x.strip()} | {a.epocas})

    if os.path.isdir(a.npz):
        L = lambda k: np.load(os.path.join(a.npz, k + ".npy"), mmap_mode="r")
        S, O, C, ptr, T, ep, meta = (L("S"), L("O"), L("C"), np.asarray(L("ptr")),
                                     L("T"), np.asarray(L("ep")), np.asarray(L("meta")))
        dia = np.asarray(L("dia"))
        ndias = int(dia.max()) + 1
    else:
        d = np.load(a.npz)
        S, O, C, ptr, T, ep, meta = (d["S"], d["O"], d["C"], d["ptr"], d["T"],
                                     d["ep"], d["meta"])
        dia = np.zeros(len(ptr) - 1, np.int16)
        ndias = 1
    n = len(ptr) - 1
    tam = np.diff(ptr).astype(np.int64)
    ncart = 1300
    Ci = np.where((np.asarray(C) >= 0) & (np.asarray(C) < ncart - 1),
                  C, ncart - 1).astype(np.int32)   # int32: 52 M opciones = 208 MB, no 416
    usa_cartas = not a.sin_cartas

    # ---- corte POR EPISODIO 70/15/15 (semilla 0: idéntico a entrenar.py)
    eps = np.unique(ep)
    rng = np.random.default_rng(0)
    rng.shuffle(eps)
    n1, n2 = int(0.70 * len(eps)), int(0.85 * len(eps))
    grupo = np.zeros(eps.max() + 1, np.int8)
    grupo[eps[n1:n2]] = 1
    grupo[eps[n2:]] = 2
    gd = grupo[ep]
    if a.frac_ep < 1.0:                       # curva de aprendizaje: poda EPISODIOS
        tr_eps = eps[:n1]
        k = max(int(round(a.frac_ep * len(tr_eps))), 1)
        rng2 = np.random.default_rng(11)
        keep = set(rng2.permutation(tr_eps)[:k].tolist())
        fuera = ~np.isin(ep, list(keep))
        gd = np.where((gd == 0) & fuera, 3, gd)
    if a.min_rating > 0:
        gd = np.where((gd == 0) & (meta[:, 3] < a.min_rating), 3, gd)
    if a.solo_ganador:
        if meta.shape[1] < 10:
            print("ERROR: este dataset no trae la columna de ganador (usa extraer2.py)")
            return 2
        gd = np.where((gd == 0) & (meta[:, 9] < 0.5), 3, gd)
    if a.train_dias:                          # solo los K dias mas recientes
        gd = np.where((gd == 0) & (dia < ndias - a.train_dias), 3, gd)
    tr = np.flatnonzero(gd == 0)
    va = np.flatnonzero(gd == 1)
    te = np.flatnonzero(gd == 2)
    if a.test_dias:
        te = te[dia[te] >= ndias - a.test_dias]
    eps_tr = len(np.unique(ep[tr]))
    s_azar = float((1.0 / tam[te]).mean())
    s_heur = float(meta[te, 7].mean())
    print("H1=%d H2=%d capas=%d dias=%d(tr%d/te%d) | train %d dec / %d eps | val %d | test %d "
          "| suelos: azar %.4f heur %.4f"
          % (a.h1, h2, a.capas, ndias, a.train_dias or ndias, a.test_dias or ndias,
             len(tr), eps_tr, len(va), len(te), s_azar, s_heur),
          flush=True)

    red = Red(S.shape[1], O.shape[1], a.h1, h2, ncart, a.semilla, a.capas)
    par = red.par
    m = [np.zeros_like(p) for p in par]
    v = [np.zeros_like(p) for p in par]
    t = 0
    mejor = (-1.0, None, 0)
    filas_por_dec = [None]
    g = np.random.default_rng(a.semilla + 7)
    hist = []
    for e in range(1, a.epocas + 1):
        t0 = time.time()
        orden = tr.copy()
        g.shuffle(orden)
        for i0 in range(0, len(orden), a.lote):
            dec = orden[i0:i0 + a.lote]
            nb = len(dec)
            filas = np.concatenate([np.arange(ptr[i], ptr[i + 1]) for i in dec])
            tb = tam[dec]
            loc = np.repeat(np.arange(nb), tb)
            Sb = S[dec]
            Ob = O[filas].astype(np.float32)
            Cb = Ci[filas]
            h1, h2v, h3, z = red.adelante(Sb, Ob, Cb, loc, nb, usa_cartas)
            p = softmax_bloques(z, loc, nb)
            dz = ((p - T[filas]) / nb).astype(np.float32)
            gw3 = h3.T @ dz[:, None]
            gb3 = np.array([dz.sum()], np.float32)
            dh = dz[:, None] @ red.w3.T
            if red.capas >= 3:
                dh[h3 <= 0] = 0.0
                gW3 = h2v.T @ dh
                gb3h = dh.sum(0)
                dh = dh @ red.W3.T
            dh[h2v <= 0] = 0.0
            gW2 = h1.T @ dh
            gb2 = dh.sum(0)
            dh1 = dh @ red.W2.T
            dh1[h1 <= 0] = 0.0
            gW1o = Ob.T @ dh1
            gb1 = dh1.sum(0)
            dPs = np.zeros((nb, dh1.shape[1]), np.float32)
            np.add.at(dPs, loc, dh1)
            gW1s = Sb.T @ dPs
            gbc = np.zeros_like(red.bc)
            if usa_cartas:
                np.add.at(gbc, Cb, dz)
            grads = [gW1s, gW1o, gb1, gW2, gb2, gw3, gb3, gbc]
            if red.capas >= 3:
                grads += [gW3, gb3h]
            t += 1
            for pp, gg, mm, vv in zip(par, grads, m, v):
                if a.l2 and pp.ndim == 2:
                    gg = gg + a.l2 * pp
                mm *= 0.9
                mm += 0.1 * gg
                vv *= 0.999
                vv += 0.001 * gg * gg
                pp -= a.lr * (mm / (1 - 0.9 ** t)) / (np.sqrt(vv / (1 - 0.999 ** t)) + 1e-8)
        acc_v, ll_v, _ = evalua(red, S, O, Ci, ptr, T, va, usa_cartas)
        if acc_v > mejor[0]:
            mejor = (acc_v, [p.copy() for p in par], e)
        linea = {"epoca": e, "val": round(acc_v, 4), "ll_val": round(ll_v, 4),
                 "seg": round(time.time() - t0)}
        if e in ck:
            acc_t, ll_t, _ = evalua(red, S, O, Ci, ptr, T, te, usa_cartas)
            ruta = "%s_e%d.npz" % (a.prefijo, e)
            mb = guarda(ruta, red, S.shape[1], O.shape[1], usa_cartas, acc_t)
            linea.update({"test": round(acc_t, 4), "ll_test": round(ll_t, 4),
                          "pesos": ruta, "MB": round(mb, 3)})
        print("  e%-3d val %.4f  %s" % (e, acc_v, json.dumps(
            {k: x for k, x in linea.items() if k not in ("epoca", "val")})), flush=True)
        hist.append(linea)

    for p, q in zip(par, mejor[1]):
        p[...] = q
    acc_t, ll_t, _ = evalua(red, S, O, Ci, ptr, T, te, usa_cartas)
    ruta = "%s_mejorval.npz" % a.prefijo
    mb = guarda(ruta, red, S.shape[1], O.shape[1], usa_cartas, acc_t)
    print("MEJOR-VAL epoca %d  val %.4f  TEST %.4f  -> %s (%.3f MB)"
          % (mejor[2], mejor[0], acc_t, ruta, mb), flush=True)
    res = {"h1": a.h1, "h2": h2, "capas": a.capas, "frac_ep": a.frac_ep,
           "ndias": ndias, "train_dias": a.train_dias, "test_dias": a.test_dias,
           "solo_ganador": a.solo_ganador, "min_rating": a.min_rating,
           "npz": a.npz, "n_train": len(tr), "eps_train": eps_tr,
           "n_test": len(te), "suelo_heur": round(s_heur, 4),
           "suelo_azar": round(s_azar, 4), "hist": hist,
           "mejor_val_epoca": mejor[2], "mejor_val": round(mejor[0], 4),
           "test_mejorval": round(acc_t, 4)}
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
