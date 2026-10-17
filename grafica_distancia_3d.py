# -*- coding: utf-8 -*-
"""Grafica 3D de lineas "Calibracion distancia" (OTDR) - script de referencia.

Recrea la grafica 3D con:
  - Eje X (PATRONES)    : "Valor inicial" de la tabla (1.004, 5.012, 10.023, 20.002)
  - Eje Y (MUESTRAS)    : 5 series compactas (MUESTRA 1..5) muy juntas en el plano Y
  - Eje Z (DISTANCIA KM): valores de 0 a 25 exactos
  - Vista frontal, lateral y baja: elev=18, azim=-72

Las muestras quedan agrupadas (y_positions = 0.1..0.5) formando un abanico/rampa
compacta. Se aplica un desplazamiento vertical SOLO visual (FAN_STRENGTH) y no se
usan marcadores: solo lineas continuas, lisas y delgadas.

Uso:    python grafica_distancia_3d.py
Genera: grafica_distancia_3d.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- Eje X: "Valor inicial" de cada patron (se dibuja como categoria) ---
patrones = [1.004, 5.012, 10.023, 20.002]
patrones_etiqueta = ["1,004", "5,012", "10,023", "20,002"]

# --- 5 muestras (cada fila = MUESTRA n, columnas = patrones) ---
muestras = [
    [1.004, 5.011, 10.023, 20.002],
    [1.004, 5.012, 10.022, 20.002],
    [1.005, 5.012, 10.022, 20.002],
    [1.004, 5.012, 10.023, 20.002],
    [1.006, 5.012, 10.022, 20.002],
]

# Desplazamiento SOLO visual para formar el abanico (no altera la tabla).
FAN_STRENGTH = 1.2
# Posiciones compactas en Y (MUESTRAS muy juntas).
Y_POSITIONS = [0.1, 0.2, 0.3, 0.4, 0.5]

colores = ["#0a8fb0", "#e52421", "#2f8f5b", "#b8962f", "#7a4fd0"]

# Eje X categorico: posiciones secuenciales 0, 1, 2 ... en orden de la tabla.
x_index = list(range(len(patrones)))

fig = plt.figure(figsize=(9.8, 5.4))
ax = fig.add_axes([0.02, 0.04, 0.62, 0.86], projection="3d")

centro = (len(muestras) - 1) / 2.0
handles = []

for indice, fila in enumerate(muestras):
    ys = [Y_POSITIONS[indice]] * len(x_index)
    gx = [x / (len(x_index) - 1) for x in x_index] if len(x_index) > 1 else [0.0]
    zs = [z + (indice - centro) * FAN_STRENGTH * g for z, g in zip(fila, gx)]
    ax.plot(
        x_index, ys, zs,
        color=colores[indice], linewidth=1.6, markersize=0,
        solid_capstyle="round",
    )
    handles.append(Patch(facecolor=colores[indice], edgecolor="none",
                         label="MUESTRA %d" % (indice + 1)))

ax.set_xlabel("PATRONES", labelpad=12)
ax.set_ylabel("MUESTRAS", labelpad=12)
ax.set_zlabel("DISTANCIA (KM)", labelpad=8)

ax.set_xticks(x_index)
ax.set_xticklabels(patrones_etiqueta, fontsize=7)
ax.set_xlim(-0.4, len(x_index) - 0.6)
ax.set_yticks(Y_POSITIONS)
ax.set_yticklabels(["MUESTRA %d" % (i + 1) for i in range(len(muestras))])
ax.set_ylim(min(Y_POSITIONS) - 0.05, max(Y_POSITIONS) + 0.05)
ax.set_zlim(0, 25)

for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
    axis.pane.set_edgecolor("#e3e9f2")
ax.grid(True)

ax.set_box_aspect((1.7, 1.1, 1.0))
ax.view_init(elev=18, azim=-72)

ax.set_title("CALIBRACIÓN DISTANCIA", fontsize=12, fontweight="bold", pad=12)
fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.70, 0.5),
           fontsize=9, frameon=False, handlelength=1.1, handleheight=1.1,
           borderpad=0.4, labelspacing=0.6)

fig.savefig("grafica_distancia_3d.png", dpi=150, bbox_inches="tight",
            pad_inches=0.25, facecolor="white")
print("Generado: grafica_distancia_3d.png")
