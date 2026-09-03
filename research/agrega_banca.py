#!/usr/bin/env python3
"""Agrupa las corridas (muestras independientes: el RNG del motor no es sembrable)
y hace el analisis CONDICIONAL del asiento.

Clave del analisis condicional: el select (9,41) SOLO lo recibe el jugador 0 del env.
La variante `segundo` cambia su decision unicamente cuando le toca ser jugador 0; en la
mitad de las partidas (jugador 1) es el v2 exacto. Por tanto la tasa global de arena
DILUYE el efecto a la mitad, y el numero honesto de "cuanto cuesta la decision" es el
condicionado al asiento 0. La rama de asiento 1 sirve de PLACEBO: si la variante solo
cambio lo que creemos, ahi tiene que medir lo mismo que el v2.
"""
import json
import math
import os

RAIZ = "/home/ftpx100/work/active/kaggle-pokemon-tcg"
D = os.path.join(RAIZ, "data/banca")


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - r, c + r


def dif(k1, n1, k2, n2):
    """Diferencia de dos proporciones con IC95 normal y z."""
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return d, d - 1.96 * se, d + 1.96 * se, (d / se if se else 0.0)


def carga(nombre):
    with open(os.path.join(D, nombre)) as f:
        return json.load(f)


def linea(et, k, n):
    p, lo, hi = wilson(k, n)
    print("   %-34s %5d/%-5d  %.4f  IC95 [%.4f, %.4f]" % (et, k, n, p, lo, hi))


print("=" * 78)
print("1) BANCA — `crit`: la politica LITERAL del enunciado (plan > no-ex > ex desnudo)")
print("=" * 78)
crit600 = (281, 600)                      # rejilla de descubrimiento
c = carga("crit_n1500.json")
crit1500 = (c["victorias"], c["n"])       # confirmacion en muestra nueva (esta sesion)
linea("descubrimiento n=600", *crit600)
linea("confirmacion n=1500 (nueva)", *crit1500)
linea("POOL", crit600[0] + crit1500[0], crit600[1] + crit1500[1])
print("   ilegales en la confirmacion: A=%d B=%d  estados=%s/%s"
      % (c["ilegales_a"], c["ilegales_b"], c["estados_a"], c["estados_b"]))
print("   usos de la palanca:", c["usos"])

print()
print("=" * 78)
print("2) BANCA — `orden` (misma cantidad que el v2, solo cambia CUAL se baja)")
print("=" * 78)
o1 = carga("orden_n1500.json")
o2 = carga("orden_n3000.json")
o3 = carga("orden_n1500_c.json")
linea("n=1500 (descubrimiento)", o1["victorias"], o1["n"])
linea("n=3000 (confirmacion previa)", o2["victorias"], o2["n"])
linea("n=1500 (confirmacion nueva)", o3["victorias"], o3["n"])
K = o1["victorias"] + o2["victorias"] + o3["victorias"]
N = o1["n"] + o2["n"] + o3["n"]
linea("POOL", K, N)
print("   ilegales (las tres corridas): %d" % sum(x["ilegales_a"] + x["ilegales_b"]
                                                  for x in (o1, o2, o3)))

print()
print("=" * 78)
print("3) ASIENTO — coste de elegir SEGUNDO, global y CONDICIONADO al asiento")
print("=" * 78)
s1 = dict(n=1000, v=403, as0=0.388, as1=0.418)   # rejilla (bat_banca.py)
s2 = carga("segundo_n1000.json")
s3 = carga("segundo_n1000_b.json")
e1 = carga("espejo_n1500.json")
e2 = carga("espejo_n1000_b.json")
e600 = dict(n=600, v=305, as0=0.5767, as1=0.44)  # espejo de la rejilla

print("\n   -- GLOBAL (lo que imprime arena; diluido: en la mitad de las partidas")
print("      la variante es jugador 1 y NUNCA recibe el select) --")
ks = [s1["v"], s2["victorias"], s3["victorias"]]
ns = [s1["n"], s2["n"], s3["n"]]
for et, k, n in zip(("segundo n=1000 (rejilla)", "segundo n=1000 (duelo)",
                     "segundo n=1000 (nueva)"), ks, ns):
    linea(et, k, n)
linea("POOL segundo", sum(ks), sum(ns))

print("\n   -- CONDICIONADO: solo las partidas en que la variante ES el jugador 0")
print("      (las unicas en que llega a elegir) --")
kv = sum(round(x["as0"] * (x["n"] // 2)) for x in
         ({"as0": s1["as0"], "n": s1["n"]}, {"as0": s2["as0"], "n": s2["n"]},
          {"as0": s3["as0"], "n": s3["n"]}))
nv = sum(x["n"] // 2 for x in (s1, s2, s3))
kb = sum(round(x["as0"] * (x["n"] // 2)) for x in
         ({"as0": e600["as0"], "n": e600["n"]}, {"as0": e1["as0"], "n": e1["n"]},
          {"as0": e2["as0"], "n": e2["n"]}))
nb = sum(x["n"] // 2 for x in (e600, e1, e2))
linea("elige SEGUNDO (jugador 0)", kv, nv)
linea("elige PRIMERO = v2 (jugador 0)", kb, nb)
d, lo, hi, z = dif(kv, nv, kb, nb)
print("   >> COSTE REAL de la decision: %+.4f  IC95 [%+.4f, %+.4f]  z = %.2f"
      % (d, lo, hi, z))

print("\n   -- PLACEBO: la variante como jugador 1 (nunca recibe el select;")
print("      es el v2 exacto). Si midiera distinto, el wrapper tocaria algo mas --")
kv1 = sum(round(x["as1"] * (x["n"] // 2)) for x in
          ({"as1": s1["as1"], "n": s1["n"]}, {"as1": s2["as1"], "n": s2["n"]},
           {"as1": s3["as1"], "n": s3["n"]}))
kb1 = sum(round(x["as1"] * (x["n"] // 2)) for x in
          ({"as1": e600["as1"], "n": e600["n"]}, {"as1": e1["as1"], "n": e1["n"]},
           {"as1": e2["as1"], "n": e2["n"]}))
linea("variante como jugador 1", kv1, nv)
linea("v2 como jugador 1 (espejo)", kb1, nb)
d, lo, hi, z = dif(kv1, nv, kb1, nb)
print("   >> diferencia placebo: %+.4f  IC95 [%+.4f, %+.4f]  z = %.2f" % (d, lo, hi, z))

print("\n   -- VALOR DEL ASIENTO con nuestro piloto (espejo v2-v2, mega-lucario) --")
kp = kb + (nb - kb1)   # gana el que va primero = (p0 gana en as0) + (p0 gana en as1)
linea("gana el que va PRIMERO", kp, nb + nb)
