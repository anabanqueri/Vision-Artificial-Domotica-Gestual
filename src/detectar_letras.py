import cv2

import numpy as np

import os
 

#   CARGAR CALIBRACIÓN

 
K = np.load("camera_matrix.npy")

dist = np.load("dist_coeffs.npy")
 
def undistort_frame(frame, K, dist):

    h, w = frame.shape[:2]

    new_K, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))

    return cv2.undistort(frame, K, dist, None, new_K)
 
 

#   CARGAR TEMPLATES DE LETRAS

 
TEMPLATES_DIR = ".\patterns"
 
templates = {}

for filename in os.listdir(TEMPLATES_DIR):

    if filename.endswith(".png") or filename.endswith(".jpg"):

        letter = filename.split(".")[0].upper()

        path = os.path.join(TEMPLATES_DIR, filename)
 
        img = cv2.imread(path, 0)

        templates[letter] = img
 
print("Letras cargadas:", list(templates.keys()))
 
 

#   DETECTAR LETRAS

 
def detectar_letra(gray_frame):

    best_letter = None

    best_score = 0
 
    for letter, tmpl in templates.items():

        # Template matching

        res = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
 
        if max_val > best_score:

            best_score = max_val

            best_letter = letter
 
    # UMBRAL 

    if best_score > 0.55:   # ajustable

        return best_letter, best_score
 
    return None, best_score
 
 

#   LOOP DE VÍDEO

 
cap = cv2.VideoCapture(0)
 
while True:

    ret, frame = cap.read()

    if not ret:

        break
 
    # 1. Undistort

    frame = undistort_frame(frame, K, dist)
 
    # 2. A gris

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 
    # 3. Detectar letra

    letra, score = detectar_letra(gray)
 
    if letra is not None:

        cv2.putText(frame, f"Letra detectada: {letra}   Score: {score:.2f}",

                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX,

                    1, (0, 255, 0), 2)

    else:

        cv2.putText(frame, "No detecto letra",

                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX,

                    1, (0, 0, 255), 2)
 
    cv2.imshow("Deteccion de letras", frame)
 
    if cv2.waitKey(1) == 27:  # ESC para salir

        break
 
cap.release()

cv2.destroyAllWindows()
 