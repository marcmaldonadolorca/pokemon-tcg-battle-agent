#!/usr/bin/env python3
"""Auditoría del clon: legalidad, uso de la red vs fallback y tiempo por decisión.

Una acción ilegal cuesta la partida entera, así que esto se mide ANTES de creerse
ningún winrate. Juega N partidas EN ESTE PROCESO (los contadores del agente son
globales de módulo y se pierden en el Pool de arena.py).
"""
import argparse
import importlib.util
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def carga(ruta):
    s = importlib.util.spec_from_file_location("ag", ruta)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=os.path.join(RAIZ, "research/agentes/clon.py"))
    ap.add_argument("--b", default=os.path.join(RAIZ, "research/agentes/variantes/v2_mega_lucario.py"))
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()
    from kaggle_environments import make
    A, B = carga(a.a), carga(a.b)
    t_dec = [0.0, 0]

    def envuelto(obs):
        t0 = time.perf_counter()
        r = A.agent(obs)
        t_dec[0] += time.perf_counter() - t0
        t_dec[1] += 1
        return r

    ganadas = estados = 0
    t0 = time.time()
    for i in range(a.n):
        env = make("cabt", configuration={"decks": [list(A.DECK), list(B.DECK)]},
                   debug=False)
        par = [envuelto, B.agent] if i % 2 == 0 else [B.agent, envuelto]
        env.run(par)
        r0 = env.state[0].reward
        ganadas += int((r0 == 1) if i % 2 == 0 else (r0 == -1))
        estados += sum(1 for s in env.state if s.status == "DONE")
    dt = time.time() - t0
    c = A.CONTADORES
    print("partidas %d  ganadas %d  DONE %d/%d" % (a.n, ganadas, estados, 2 * a.n))
    print("decisiones %d   red %d (%.2f%%)  heuristico %d  excepciones %d  ilegales %d"
          % (t_dec[1], c["red"], 100.0 * c["red"] / max(t_dec[1], 1),
             c["heuristico"], c["excepcion"], c["ilegal"]))
    print("tiempo/decision %.3f ms   partida %.2f s   (limite produccion: 600 s/partida)"
          % (1000 * t_dec[0] / max(t_dec[1], 1), dt / a.n))
    print("margen sobre el reloj de pared: x%.0f"
          % (600.0 / max(t_dec[0] / a.n, 1e-9)))


if __name__ == "__main__":
    sys.exit(main())
