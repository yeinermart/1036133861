import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from skimage.filters import threshold_otsu
import tkinter as tk
from tkinter import filedialog
import os

# === 1. Selector de imagen ===
root = tk.Tk()
root.withdraw()
ruta_imagen = filedialog.askopenfilename(
    title="Selecciona una imagen de hortensias",
    filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]
)
if not ruta_imagen:
    raise SystemExit("❌ No se seleccionó ninguna imagen.")

# Crear carpeta para resultados
os.makedirs("resultados", exist_ok=True)

# === 2. Cargar imagen ===
img = cv2.imread(ruta_imagen)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

plt.figure(figsize=(7,7))
plt.title("Imagen original")
plt.imshow(img_rgb)
plt.axis('off')
plt.savefig("resultados/1_original.png")
plt.show()

# === 3. Convertir a HSV y filtrar colores no florales ===
hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

# Filtrar verdes (hojas) y marrones (tierra)
lower_green = np.array([25, 30, 30])
upper_green = np.array([90, 255, 255])

lower_brown = np.array([10, 60, 20])
upper_brown = np.array([30, 255, 200])

mask_green = cv2.inRange(hsv, lower_green, upper_green) #genera mascaras binarias
mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

mask_non_flower = cv2.bitwise_or(mask_green, mask_brown) #combina las mascaras 
mask_flower = cv2.bitwise_not(mask_non_flower)  # Invierte para obtener las flores

masked_img = cv2.bitwise_and(img_rgb, img_rgb, mask=mask_flower)   #aplica la mascara

plt.figure(figsize=(7,7))
plt.title("Filtrado HSV: eliminación de fondo vegetal y suelo ")
plt.imshow(masked_img)
plt.axis('off')
plt.savefig("resultados/2_filtrada.png")
plt.show()

# === 4. Convertir a Lab y aplicar K-means ===
lab = cv2.cvtColor(masked_img, cv2.COLOR_RGB2LAB)
pixel_values = lab.reshape((-1, 3))
pixel_values = np.float32(pixel_values)

kmeans = KMeans(n_clusters=2, random_state=42) #dos grupos flores y No flores
labels = kmeans.fit_predict(pixel_values) # asigna cada pixel a su cluster mas cercano
segmented_img = labels.reshape(lab.shape[:2])

cluster_mean = [np.mean(lab[segmented_img == i, 0]) for i in range(2)]  #- Se asume que el cluster con mayor luminancia (L) corresponde a las flores
flower_cluster = np.argmax(cluster_mean)
mask = (segmented_img == flower_cluster).astype(np.uint8) * 255

plt.figure(figsize=(7,7))
plt.title("Agrupamiento Lab: extracción de regiones florales por luminancia")
plt.imshow(mask, cmap='gray')
plt.axis('off')
plt.savefig("resultados/3_segmentacion.png")
plt.show()

# === 5. Umbralización + limpieza morfológica ===
thresh_val = threshold_otsu(mask)
binary = (mask > thresh_val).astype(np.uint8) * 255

kernel = np.ones((7,7), np.uint8)
binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel) # elimina huecos internos y suaviza bordes
binary = cv2.medianBlur(binary, 5)               #reduce ruido 

plt.figure(figsize=(7,7))
plt.title("Binarización Otsu + limpieza morfológica de pétalos")
plt.imshow(binary, cmap='gray')
plt.axis('off')
plt.savefig("resultados/4_binaria.png")
plt.show()

# === 6. Detección de círculos (flores) con Hough optimizado ===

# Aplicar un suavizado más fuerte para reducir bordes internos de los pétalos
gray = cv2.GaussianBlur(binary, (11,11), 3)

height, width = gray.shape

# Rango dinámico de radios basado en resolución
minR = int(min(height, width) * 0.04)   # tamaño mínimo de flor pequeña
maxR = int(min(height, width) * 0.23)   # tamaño máximo de flor grande

# Ajustar sensibilidad
circles = cv2.HoughCircles(   #detecta circulos en la imangen
    gray, cv2.HOUGH_GRADIENT, dp=1.1, minDist=60,
    param1=45, param2=17, minRadius=minR, maxRadius=maxR
)

output = img_rgb.copy()
count = 0

# Filtro de área para evitar círculos superpuestos o muy pequeños
if circles is not None:
    circles = np.uint16(np.around(circles))
    for (x, y, r) in circles[0, :]:
        if r > minR * 0.8 and r < maxR * 1.1:  # descarta falsos pequeños o grandes
            cv2.circle(output, (x, y), r, (255, 0, 0), 3)
            count += 1

plt.figure(figsize=(8,8))
plt.title(f"Detección de hortensias por Hough: {count} hortensias detectadas")
plt.imshow(output)
plt.axis('off')
plt.savefig("resultados/5_conteo.png")
plt.show()

print(f"✅ Total de hortensias detectadas: {count}")
