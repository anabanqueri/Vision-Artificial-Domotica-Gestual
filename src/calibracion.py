import cv2

import numpy as np

import glob

import os
 
CHECKERBOARD = (7, 9)

square_size = 20
 
def calibrar_camara():

    # Ruta absoluta de este archivo

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
    # Ruta real a la carpeta ../data

    DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))
 
    print("Usando carpeta de imágenes:", DATA_DIR)
 
    # Comprobación

    if not os.path.exists(DATA_DIR):

        print("❌ ERROR: La carpeta data NO existe:", DATA_DIR)

        return
 
    # Cargar las rutas de las imágenes

    imgs_path = sorted([

        os.path.join(DATA_DIR, item)

        for item in os.listdir(DATA_DIR)

        if item.endswith(".jpg")

    ])
 
    print(f"Encontradas {len(imgs_path)} imágenes para calibrar.")
 
    if len(imgs_path) == 0:

        print("❌ No hay imágenes en la carpeta.")

        return
 
    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)

    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

    objp = objp * square_size
 
    objpoints = []

    imgpoints = []
 
    gray = None
 
    for fname in imgs_path:

        img = cv2.imread(fname)

        if img is None:

            print("❌ No se pudo leer:", fname)

            continue
 
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
 
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
 
        if ret:

            print(f"✔ Esquinas detectadas en {fname}")

            objpoints.append(objp)
 
            corners2 = cv2.cornerSubPix(

                gray, corners, (11, 11), (-1, -1),

                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

            )
 
            imgpoints.append(corners2)

        else:

            print(f"✘ No se detectaron esquinas en {fname}")
 
    if len(imgpoints) == 0:

        print("❌ No se detectaron patrones en ninguna imagen.")

        return
 
    h, w = gray.shape[:2]
 
    rms, K, dist, rvecs, tvecs = cv2.calibrateCamera(

        objpoints, imgpoints, (w, h), None, None

    )
 
    print("\n=== RESULTADOS DE CALIBRACIÓN ===")

    print("RMS:", rms)

    print("K:\n", K)

    print("dist:\n", dist)
 
    np.save("camera_matrix.npy", K)

    np.save("dist_coeffs.npy", dist)
 
    with open("calibration_params.txt", "w") as f:

        f.write("=== Parámetros de calibración ===\n\n")

        f.write(f"RMS: {rms}\n\n")

        f.write("K:\n")

        f.write(np.array2string(K) + "\n\n")

        f.write("Distorsión:\n")

        f.write(np.array2string(dist))
 
    print("\nParámetros guardados en camera_matrix.npy y dist_coeffs.npy.")
 
    return rms, K, dist, rvecs, tvecs
 
 
if __name__ == "__main__":

    calibrar_camara()
 