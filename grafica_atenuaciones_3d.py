# -*- coding: utf-8 -*-
"""Grafica 3D de lineas "Calibracion atenuaciones" (OTDR) - script de referencia.

Recrea en 3D la grafica de calibracion de atenuaciones usando los datos de la
tabla (columna "Valor patrón" y las 5 muestras):

  - Eje X (ATENUACIONES PATRON): CATEGORICO. Las posiciones son indices
    secuenciales (0, 1, 2, ...) en el ORDEN de la tabla (EVENTO 1, 2, 3...),
    de modo que el orden se mantiene estricto y no se reordena por magnitud.
    Las etiquetas de las marcas son los valores reales de "Valor patrón".
  - Eje Y (MUESTRAS)           : 5 series muy juntas [1.0, 1.15, 1.3, 1.45, 1.6]
  - Eje Z (Atenuacion)         : escala desde 0.000 hasta el maximo redondeado,
                                 con marcas cada 0.100 (ej. 0.000 .. 0.400).

Lineas continuas, sin marcadores. Leyenda vertical a la derecha con cuadrados.

Uso:    python grafica_atenuaciones_3d.py
Genera: grafica_atenuaciones_3d.png
"""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- Eje X: "Valor patrón" de cada evento (se dibuja como categoria) ---
patrones = [0.328, 0.228, 0.334]
patrones_etiqueta = ["0,328", "0,228", "0,334"]

# --- 5 muestras (cada fila = MUESTRA n, columnas = eventos / patrones) ---
muestras = [
    [0.323, 0.228, 0.333],
    [0.323, 0.228, 0.331],
    [0.328, 0.223, 0.331],
    [0.320, 0.223, 0.331],
    [0.318, 0.226, 0.331],
]

# Posiciones compactas en Y (incrementos de 0.15 -> bloque/rampa).
Y_POSITIONS = [1.0, 1.15, 1.3, 1.45, 1.6]
Z_STEP = 0.100

colores = ["#0a8fb0", "#e52421", "#2f8f5b", "#b8962f", "#7a4fd0"]

# Eje X categorico: posiciones secuenciales 0, 1, 2 ... en orden de la tabla.
x_index = list(range(len(patrones)))

# Escala Z: 0 hasta el maximo redondeado al siguiente multiplo de Z_STEP.
valores = [v for fila in muestras for v in fila]
zmax = math.ceil(max(valores) / Z_STEP) * Z_STEP
zticks = [round(i * Z_STEP, 10) for i in range(int(round(zmax / Z_STEP)) + 1)]

fig = plt.figure(figsize=(9.8, 5.4))
ax = fig.add_axes([0.02, 0.04, 0.62, 0.86], projection="3d")

handles = []
for indice, fila in enumerate(muestras):
    ys = [Y_POSITIONS[indice]] * len(x_index)
    ax.plot(
        x_index, ys, fila,
        color=colores[indice], linewidth=1.6, markersize=0,
        solid_capstyle="round",
    )
    handles.append(Patch(facecolor=colores[indice], edgecolor="none",
                         label="MUESTRA %d" % (indice + 1)))

ax.set_xlabel("ATENUACIONES PATRÓN", labelpad=12)
ax.set_ylabel("MUESTRAS", labelpad=12)
ax.set_zlabel("Atenuación (dB)", labelpad=8)

ax.set_xticks(x_index)
ax.set_xticklabels(patrones_etiqueta, fontsize=7)
ax.set_xlim(-0.4, len(x_index) - 0.6)

ax.set_yticks(Y_POSITIONS)
ax.set_yticklabels(["MUESTRA %d" % (i + 1) for i in range(len(muestras))])
ax.set_ylim(min(Y_POSITIONS) - 0.075, max(Y_POSITIONS) + 0.075)

ax.set_zlim(0, zmax)
ax.set_zticks(zticks)
ax.set_zticklabels(["%.3f" % t for t in zticks], fontsize=7)

for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
    axis.pane.set_edgecolor("#e3e9f2")
ax.grid(True)

ax.set_box_aspect((1.4, 0.45, 0.85))
ax.view_init(elev=18, azim=-72)

ax.set_title("CALIBRACIÓN ATENUACIONES 1310", fontsize=12, fontweight="bold",
             pad=12)
fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.70, 0.5),
           fontsize=9, frameon=False, handlelength=1.1, handleheight=1.1,
           borderpad=0.4, labelspacing=0.6)

fig.savefig("grafica_atenuaciones_3d.png", dpi=150, bbox_inches="tight",
            pad_inches=0.25, facecolor="white")
print("Generado: grafica_atenuaciones_3d.png  (Z: 0 a %.3f, paso %.3f)"
      % (zmax, Z_STEP))
