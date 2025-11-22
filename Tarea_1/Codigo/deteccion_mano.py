# ------------------------------------------------------------------------------
# ------- PLANTILLA DE CÓDIGO --------------------------------------------------
# ------- Conceptos básicos de PDI (Procesamiento Digital de Imágenes) ----------
# ------- por: Leyder Marcillo y Yeiner Martínez ----------------------------------------
# ------- Curso de Procesamiento de Imágenes y Visión Artificial ----------------
# ------- V2 - Octubre de 2025 --------------------------------------------------
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# -- 1. Inicialización del sistema ---------------------------------------------
# ------------------------------------------------------------------------------

import cv2  # Importa la librería OpenCV para procesamiento de imágenes
import numpy as np # Importa NumPy para operaciones matemáticas y manejo de matrices

# Inicializa la cámara
cap = cv2.VideoCapture(0) # Abre la cámara predeterminada (índice 0)
cap.set(3, 640) # Establece el ancho del frame en 640 píxeles
cap.set(4, 480) # Establece el alto del frame en 480 píxeles

# ------------------------------------------------------------------------------
# -- 2. Definición de parámetros del sistema ------------------------------------
# ------------------------------------------------------------------------------

# Rango de color en HSV para detectar el guante amarillo
LOWER_YELLOW = np.array([18, 90, 90], dtype=np.uint8) # Límite inferior del color amarillo en HSV
UPPER_YELLOW = np.array([38, 255, 255], dtype=np.uint8) # Límite superior del color amarillo en HSV

# Límites de área para considerar detección
MIN_AREA = 1200          # Área mínima para considerar que hay una mano (evita ruido)
OPEN_AREA = 9000         # Si el área > OPEN_AREA → mano "abierta"

# Variable para imprimir información de depuración
DEBUG = False # Si es True, imprime valores intermedios en la consola

# ------------------------------------------------------------------------------
# -- 3. Función principal de detección de mano ---------------------------------
# ------------------------------------------------------------------------------

def get_hand_position(show_camera=True):
    """
    Retorna (norm_x, estado)
      norm_x: posición horizontal del centroide normalizada 0..1
      estado: 'abierta' o 'cerrada' o None si no detecta
    Si show_camera=True, muestra ventana con cámara + máscara
    """
     # Captura un frame desde la cámara
    ret, frame = cap.read()  # Lee un cuadro (imagen) de la cámara
    if not ret:              # Si no se pudo capturar, retorna vacío
        return None, None

     # Reflejo horizontal (efecto espejo para que coincida con los movimientos)
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]   # Obtiene altura (h) y ancho (w) de la imagen

    # Conversión del espacio de color BGR a HSV (más adecuado para detección por color)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Crea una máscara binaria para aislar el color amarillo del guante
    mask = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)

    # Operaciones morfológicas para eliminar ruido y mejorar la forma
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5)) # Crea un kernel elíptico 5x5
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1) # Elimina puntos pequeños
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1) # Cierra huecos pequeños
    mask = cv2.GaussianBlur(mask, (5,5), 0) # Suaviza los bordes de la máscara

    # Busca los contornos en la máscara (zonas donde se detectó el color)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Variables iniciales para almacenar resultados
    norm_x = None
    estado = None

    # Si hay contornos encontrados (posibles manos detectadas)
    if contours:
        # Selecciona el contorno más grande (la mano principal)
        c = max(contours, key=cv2.contourArea)
        area = int(cv2.contourArea(c))  # Calcula el área del contorno

        if DEBUG:   # Si está activado el modo depuración, muestra el área
            print("Area:", area)

        if area >= MIN_AREA:    # Si el área es suficientemente grande
            # Calcula el centroide (cx, cy)(punto central del contorno)
            M = cv2.moments(c)
            if M["m00"] != 0:     # Evita división por cero
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:                                # Si no se puede calcular, usa el centro del frame
                cx, cy = w // 2, h // 2

            # Normaliza la posición X entre 0 y 1
            norm_x = cx / w

            # Determina si la mano está abierta o cerrada según el área detectada
            estado = "abierta" if area >= OPEN_AREA else "cerrada"

            # Dibuja contorno y centroide sobre la imagen
            cv2.drawContours(frame, [c], -1, (0,255,0), 2) # Dibuja el contorno verde
            cv2.circle(frame, (cx, cy), 6, (0,0,255), -1)  # Dibuja un punto rojo en el centro
            cv2.putText(frame, f"{estado} A:{area}", (cx-60, cy-20),  # Muestra texto con estado y área
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

    # ------------------------------------------------------------------------------
    # -- 4. Visualización de resultados -------------------------------------------
    # ------------------------------------------------------------------------------

    if show_camera:
        # Convierte la máscara (blanco y negro) a formato BGR para mostrarla junto al frame
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        try:
            combined = cv2.hconcat([frame, mask_bgr])  # Une ambas imágenes horizontalmente
        except Exception:
            # Si falla la concatenación (por tamaños diferentes), las ajusta
            mask_bgr = cv2.resize(mask_bgr, (w, h))
            frame = cv2.resize(frame, (w, h))
            combined = cv2.hconcat([frame, mask_bgr])

        #Escalar tamaño de la ventana 70%
        scale = 0.7  
        small = cv2.resize(combined, (0, 0), fx=scale, fy=scale)

        # Muestra la ventana con la cámara (izquierda) y la máscara (derecha)
        cv2.imshow("Camara (izq) - Mascara (der)", small)

    # Devuelve la posición normalizada y el estado de la mano
    return norm_x, estado

# ------------------------------------------------------------------------------
# -- 5. Liberación de recursos --------------------------------------------------
# ------------------------------------------------------------------------------

def release_camera():
    #Libera la cámara y destruye las ventanas abiertas
    cap.release()  # Libera la cámara para que pueda usarse en otro programa
    cv2.destroyAllWindows() # Cierra todas las ventanas abiertas por OpenCV

# ------------------------------------------------------------------------------
# -------------------------- FIN DEL LA DETECCION CON CAMARA ----------------------------------
# ------------------------------------------------------------------------------