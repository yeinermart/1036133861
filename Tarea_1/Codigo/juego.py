# ------------------------------------------------------------------------------
# ------- PLANTILLA DE CÓDIGO --------------------------------------------------
# ------- Juego: "Aperitivo de Hamburguesas" -----------------------------------
# ------- por: Leyder Marcillo y Yeiner Martínez -------------------------------
# ------- Curso de Procesamiento de Imágenes y Visión Artificial ----------------
# ------- V2 - Octubre de 2025 --------------------------------------------------
# ------------------------------------------------------------------------------
# Este código implementa un juego interactivo controlado por visión artificial.
# El jugador abre o cierra la boca del personaje moviendo la mano con un guante
# amarillo frente a la cámara. Si la mano está "abierta", el personaje "come".
# El objetivo es atrapar hamburguesas buenas y evitar las malas.
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# -- 1. Importación de librerías y módulos -------------------------------------
# ------------------------------------------------------------------------------

import pygame  # Librería para gráficos, sonido y eventos
import random  # Para generar posiciones y velocidades aleatorias
import sys     # Para controlar la salida del programa
import time    # Para medir el tiempo transcurrido
from deteccion_mano import get_hand_position, release_camera # Se importan funciones de detección de mano desde otro archivo

# ------------------------------------------------------------------------------
# -- 2. Inicialización del entorno de juego ------------------------------------
# ------------------------------------------------------------------------------

pygame.init()   # Inicializa todos los módulos de Pygame
ANCHO, ALTO = 800, 600   # Dimensiones de la ventana
ventana = pygame.display.set_mode((ANCHO, ALTO)) # Crea la ventana de juego
pygame.display.set_caption("Aperitivo de Hamburguesas ") # Título de la ventana

# # Definición de colores RGB
BLANCO = (255,255,255)
NEGRO = (0,0,0)

# ------------------------------------------------------------------------------
# -- 3. Carga y preparación de imágenes ----------------------------------------
# ------------------------------------------------------------------------------

# Carga las imágenes necesarias para el juego
fondo = pygame.image.load("img/fondo.png").convert()
personaje_abierto = pygame.image.load("img/personaje_abierto.png").convert_alpha()
personaje_cerrado = pygame.image.load("img/personaje_cerrado.png").convert_alpha()
hamb_buena = pygame.image.load("img/hamburguesa_buena.png").convert_alpha()
hamb_mala = pygame.image.load("img/hamburguesa_mala.png").convert_alpha()

# Escala las imágenes al tamaño deseado
fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))
PERSON_W, PERSON_H = 100, 100
personaje_abierto = pygame.transform.scale(personaje_abierto, (PERSON_W, PERSON_H))
personaje_cerrado = pygame.transform.scale(personaje_cerrado, (PERSON_W, PERSON_H))
hamb_buena = pygame.transform.scale(hamb_buena, (50,50))
hamb_mala = pygame.transform.scale(hamb_mala, (50,50))

# ------------------------------------------------------------------------------
# -- 4. Clase Hamburguesa ------------------------------------------------------
# ------------------------------------------------------------------------------

# --- Clase hamburguesa con rect para colisiones precisas
class Hamburguesa:
    #Representa una hamburguesa (buena o mala) que cae desde la parte superior.
    def __init__(self, tipo="buena"):
        self.tipo = tipo       # Tipo de hamburguesa
        self.imagen = hamb_buena if tipo=="buena" else hamb_mala  # Imagen según tipo
        self.rect = self.imagen.get_rect()   # Rectángulo para colisiones
        self.reset()                         # Inicializa posición y velocidad

    def reset(self):
        # Reaparece en una posición aleatoria en la parte superior
        self.rect.x = random.randint(50, ANCHO - 50 - self.rect.width)
        self.rect.y = random.randint(-500, -40)
        self.vel = random.randint(3,7) # Velocidad de caída aleatoria

    def update(self):
        # Mueve la hamburguesa hacia abajo
        self.rect.y += self.vel
        # Si sale de la pantalla, reaparece arriba
        if self.rect.top > ALTO:
            self.reset()

    def draw(self, surf):
        # Dibuja la hamburguesa en la superficie indicada
        surf.blit(self.imagen, (self.rect.x, self.rect.y))


# ------------------------------------------------------------------------------
# -- 5. Clase Jugador ----------------------------------------------------------
# ------------------------------------------------------------------------------


class Jugador:
    #Representa al personaje controlado por la mano detectada por cámara.
    def __init__(self):
        self.image = personaje_cerrado  # Imagen inicial (boca cerrada)
        self.rect = self.image.get_rect()  # Rectángulo para colisiones
        self.rect.centerx = ANCHO // 2     # Posición inicial horizontal (centro)
        self.rect.bottom = ALTO - 10       # Posición vertical (parte inferior)
        self.estado = "cerrada"            # Estado inicial de la boca

    #Mueve al personaje según la posición normalizada detectada (0 o 1)
    def mover_por_normx(self, norm_x):
        # norm_x 0..1 -> colocar centrox, asegurar límites
        if norm_x is None:  # Si no hay detección, no hacer nada
            return
        cx = int(norm_x * ANCHO)   # Escala la posición normalizada al ancho de pantalla
        # limitar para que el sprite no salga
        half = self.rect.width // 2   # Mitad del ancho del sprite
        cx = max(half, min(ANCHO - half, cx)) # Evita que se salga de los bordes
        self.rect.centerx = cx                # Actualiza la posición X

    def abrir(self):  # Cambia a imagen de boca abierta
        self.image = personaje_abierto
        self.estado = "abierta"

    def cerrar(self):    # Cambia a imagen de boca cerrada
        self.image = personaje_cerrado
        self.estado = "cerrada"

    def draw(self, surf):   # Dibuja al personaje en pantalla
        surf.blit(self.image, (self.rect.x, self.rect.y))


# ------------------------------------------------------------------------------
# -- 6. Configuración inicial del juego ----------------------------------------
# ------------------------------------------------------------------------------

jugador = Jugador()  # Crea al jugador

# Crea una lista de hamburguesas (buenas y malas)
hamburguesas = [Hamburguesa(random.choice(["buena","mala"])) for _ in range(7)]
puntaje = 0  # Puntaje inicial

font = pygame.font.SysFont("Arial", 28) # Fuente para texto
clock = pygame.time.Clock()             # Control de FPS

# temporizador 5 minutos = 300 segundos
TIEMPO_TOTAL = 300  # segundos
t_inicio = time.time()   # Guarda el tiempo de inicio

# ------------------------------------------------------------------------------
# -- 7. Bucle principal del juego ----------------------------------------------
# ------------------------------------------------------------------------------

running = True
while running:
    dt = clock.tick(30) / 1000.0    # Control de velocidad del bucle (30 FPS)

    # --- Eventos de Pygame (por ejemplo, cerrar ventana)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    # --- detección de mano (mueve jugador y estado)
    norm_x, estado = get_hand_position(show_camera=True)
    # si detecta, mover
    if norm_x is not None:
        jugador.mover_por_normx(norm_x) # Mueve personaje según detección

    # Mapeo de estados: mano abierta -> boca abierta -> puede atrapar
    if estado == "abierta":
        jugador.abrir()
    elif estado == "cerrada":
        jugador.cerrar()

    # Actualiza movimiento de hamburguesas
    for h in hamburguesas:
        h.update()

    # colisiones: usar rect collide y verificar que jugador esté en modo "abierta" para atrapar
    for h in hamburguesas:
        # rect de colisión con algo de margen vertical
        if jugador.rect.colliderect(h.rect):    # Si colisionan
            if jugador.estado == "abierta":     # Solo si boca abierta
                if h.tipo == "buena":          # Hamburguesa buena → +1 punto
                    puntaje += 1
                else:                          # Hamburguesa mala → -1 punto
                    puntaje -= 1
                h.reset()                      # La hamburguesa reaparece
            else:
                pass   # Si la boca está cerrada, no ocurre nada

    # Dibuja los elementos del juego 
    ventana.blit(fondo, (0,0))   # Fondo
    for h in hamburguesas:
        h.draw(ventana)          # Dibuja cada hamburguesa
    jugador.draw(ventana)        # Dibuja el personaje

    # Actualiza y muestra tiempo restante 
    # Inicializa la fuente con estilo negrita y tamaño grande
    font = pygame.font.SysFont("Arial", 32, bold=True)

    # Colores personalizados
    COLOR_PUNTUACION = (255, 255, 0)  # Amarillo
    COLOR_TIEMPO     = (255, 0, 0)    # Rojo

    # Cálculo de tiempo
    t_elapsed = int(time.time() - t_inicio)
    t_rest = max(0, TIEMPO_TOTAL - t_elapsed)
    minutos = t_rest // 60
    segundos = t_rest % 60

    # Superficies de texto con colores y fuente gruesa
    texto_tiempo = font.render(f"Tiempo: {minutos:02d}:{segundos:02d}", True, COLOR_TIEMPO)
    texto_punt   = font.render(f"Puntuación: {puntaje}", True, COLOR_PUNTUACION)

    # Dibujo en pantalla
    ventana.blit(texto_punt, (20, 20))
    ventana.blit(texto_tiempo, (20, 56))

    pygame.display.flip()   # Actualiza pantalla

    # Condición de fin del juego
    if puntaje >= 25:         # puntaje para ganar
        resultado = "ganaste"
        running = False
    elif t_rest <= 0:         # Termina si el tiempo llega a 0
        resultado = "tiempo"
        running = False


# ------------------------------------------------------------------------------
# -- 8. Pantalla final ----------------------------------------------------------
# ------------------------------------------------------------------------------

ventana.fill((0,0,0))  # Fondo negro
if resultado == "ganaste":
    msg = "¡Ganaste!"
else:
    msg = "Se acabó el tiempo"

# Renderiza mensaje final    
texto = font.render(msg, True, (255,255,255))
ventana.blit(texto, (ANCHO//2 - texto.get_width()//2, ALTO//2 - 20))
pygame.display.flip()
pygame.time.delay(3000)   # Pausa para mostrar mensaje final

# ------------------------------------------------------------------------------
# -- 9. Liberación de recursos --------------------------------------------------
# ------------------------------------------------------------------------------

release_camera() # Libera la cámara del módulo de detección
pygame.quit()    # Cierra Pygame
sys.exit()       # Sale del programa

# ------------------------------- FIN DEL JUEGO ---------------------------------
