from ultralytics import YOLO
import cv2
from norfair import Detection, Tracker
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os
import numpy as np


# 1. Selecciono el video 

root = Tk()
root.withdraw()
root.attributes('-topmost', True)

video_path = askopenfilename(
    title="Selecciona el archivo de video",
    filetypes=(
        ("Archivos de Video", "*.mp4 *.avi *.mov *.mkv"),
        ("Todos los archivos", "*.*")
    )
)

if not video_path:
    print("No seleccionaste ningún video. Saliendo...")
    exit()

# 2. Preparo el nombre de salida del video

folder = os.path.dirname(video_path)
filename = os.path.basename(video_path)
name_no_ext, ext = os.path.splitext(filename)

output_path = os.path.join(folder, f"{name_no_ext}_PROCESADO.mp4")

# 3. Cargo modelo YOLO que es el encargado de detectar las hortensias en cada imagen

model = YOLO("best.pt")

# 4. Inicializo el tracker de Norfair para darle seguimiento a cada hortensia 

tracker = Tracker(
    distance_function="euclidean",
    distance_threshold=30     # distancia máxima en píxeles
)


# 5. Contadores de las hortensias blancas y cremosas

detected_ids_blanca = set()
detected_ids_cremosa = set()
clases = ["hortensia_blanca", "hortensia_cremosa"]


# 6. Abro el video

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"ERROR: No se pudo abrir el video: {video_path}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

print(f"Guardando video procesado en:\n{output_path}")


# 7. Procesamiento frame por frame

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)

    detections_norfair = []
    class_assignments = {}

    # Extraer cajas YOLO
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            if conf < 0.4: # nivel de confianza
                continue

            cx = float((x1 + x2) / 2)
            cy = float((y1 + y2) / 2)

            detections_norfair.append(
                Detection(points=np.array([cx, cy]))
            )
            class_assignments[(cx, cy)] = cls

    # Actualizar tracks
    tracked_objects = tracker.update(detections_norfair)

    # Dibujar
    for track in tracked_objects:
        cx, cy = track.estimate[0]

        # Solo asignar clase si hay detecciones
        if class_assignments:
            closest_point = min(
                class_assignments.keys(),
                key=lambda p: (p[0] - cx)**2 + (p[1] - cy)**2
            )
            cls = class_assignments[closest_point]

            track_id = track.id

            if cls == 0:
                detected_ids_blanca.add(track_id)
                color = (255, 255, 255)
            else:
                detected_ids_cremosa.add(track_id)
                color = (0, 255, 255)

            cv2.circle(frame, (int(cx), int(cy)), 6, color, -1)
            cv2.putText(frame, f"{clases[cls]} ID:{track_id}",
                        (int(cx) + 10, int(cy) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Contadores
    cv2.putText(frame, f"Blancas: {len(detected_ids_blanca)}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

    cv2.putText(frame, f"Cremosas: {len(detected_ids_cremosa)}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

    # Mostrar y guardar
    cv2.imshow("Detección Hortensias", frame)
    out.write(frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# 8. Resultado final

print("===========================================")
print("RESULTADO FINAL (OBJETOS ÚNICOS DETECTADOS)")
print(f"Hortensias BLANCAS:  {len(detected_ids_blanca)}")
print(f"Hortensias CREMOSAS: {len(detected_ids_cremosa)}")
print("===========================================")
print(f"Video procesado guardado en:\n{output_path}")

cap.release()
out.release()
cv2.destroyAllWindows()
