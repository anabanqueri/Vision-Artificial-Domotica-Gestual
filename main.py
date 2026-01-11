import cv2
import numpy as np
import time

# 1. CONFIGURACIÓN
estado_luz = False      
altura_persiana_px = 0  
modo_persiana_bloqueado = False 

# VARIABLES DE ESTADO
accion_oficial = "PARADA"      
accion_candidata = "PARADA"    
timer_cambio_estado = 0        

modo_candidato = "NADA"
timer_modo = 0

background = None

# VARIABLES DE COLOR
lower_skin = np.array([0, 10, 60], dtype=np.uint8)
upper_skin = np.array([20, 255, 255], dtype=np.uint8)
calibracion_color_hecha = False
frame_hsv_global = None

def calibrar_color(event, x, y, flags, param):
    global lower_skin, upper_skin, calibracion_color_hecha, frame_hsv_global
    if event == cv2.EVENT_LBUTTONDOWN:
        if frame_hsv_global is not None:
            pixel_hsv = frame_hsv_global[y, x]
            lower_skin = np.array([max(0, pixel_hsv[0] - 15), max(30, pixel_hsv[1] - 50), max(30, pixel_hsv[2] - 80)], dtype=np.uint8)
            upper_skin = np.array([min(180, pixel_hsv[0] + 15), 255, 255], dtype=np.uint8)
            calibracion_color_hecha = True
            print(f"COLOR CALIBRADO: {pixel_hsv}")

try:
    K = np.load("camera_matrix.npy")
    dist = np.load("dist_coeffs.npy")
    calib_ok = True
except:
    calib_ok = False

def dibujar_interfaz(frame, luz, altura_tela, modo, bloqueado, bg_capturado, accion_txt, color_ok):
    h, w = frame.shape[:2]
    
    # BOMBILLA
    color_luz = (0, 255, 255) if luz else (50, 50, 50)
    cv2.circle(frame, (w-80, 80), 40, color_luz, -1)
    cv2.putText(frame, "LUZ", (w-110, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

    # PERSIANA
    cv2.rectangle(frame, (50, 100), (150, 300), (200, 200, 200), 2) 
    cv2.rectangle(frame, (52, 102), (148, 298), (230, 216, 173), -1) 
    if altura_tela > 0:
        cv2.rectangle(frame, (52, 102), (148, 100 + altura_tela), (50, 50, 50), -1)
    
    pct = int((altura_tela / 200) * 100)
    cv2.putText(frame, f"{pct}%", (70, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # AVISOS
    y_aviso = h//2 - 60
    if not color_ok:
        cv2.putText(frame, "1. CLICK EN TU MANO", (w//2 - 200, y_aviso), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 3)
        y_aviso += 50
    if not bg_capturado:
        cv2.putText(frame, "2. APARTATE Y PULSA 'B'", (w//2 - 200, y_aviso), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
    else:
        color_texto = (0, 255, 0) if not bloqueado else (0, 165, 255)
        texto_estado = f"MODO: {modo}" 
        if bloqueado: texto_estado = f"PERSIANA: {accion_txt}"
        cv2.putText(frame, texto_estado, (w//2 - 150, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
    return frame

# 2. BUCLE PRINCIPAL
cap = cv2.VideoCapture(0)
cv2.namedWindow('Domotica')
cv2.setMouseCallback('Domotica', calibrar_color)

print("INSTRUCCIONES:")
print("1. Click para color. 2. 'B' para fondo.")
print("INFO DEBUG EN PANTALLA: A=Area, R=Ratio")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    if calib_ok:
        h, w = frame.shape[:2]
        new_K, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
        frame = cv2.undistort(frame, K, dist, None, new_K)

    clean_frame = frame.copy()
    frame_hsv_global = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_final = np.zeros(frame.shape[:2], dtype=np.uint8)

    if background is not None:
        diff = cv2.absdiff(background, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        _, mask_diff = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        mask_color = cv2.inRange(frame_hsv_global, lower_skin, upper_skin)
        mask_final = cv2.bitwise_and(mask_diff, mask_color)
        mask_final = cv2.erode(mask_final, None, iterations=1)
        mask_final = cv2.dilate(mask_final, None, iterations=3)

    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    modo_txt = "ESPERANDO..."

    if len(contours) > 0 and background is not None:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 3000: 
            color_c = (0, 0, 255) if modo_persiana_bloqueado else (0, 255, 0)
            cv2.drawContours(frame, [c], -1, color_c, 2)

            x, y, w_box, h_box = cv2.boundingRect(c)
            aspect_ratio = float(h_box) / w_box 
            
            # VISUAL 
            # Te muestra el Ratio (R) en pantalla
            cv2.putText(frame, f"R:{aspect_ratio:.2f}", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(frame, (cx, cy), 10, (255, 0, 0), -1)

            #  DETECCIÓN DE INTENCIÓN (UMBRALES AJUSTADOS) 
            intencion_actual = "NADA"

            
            if modo_persiana_bloqueado:
                # Salida más fácil
                if aspect_ratio < 1.4:
                    intencion_actual = "SALIR_PERSIANA"
                else:
                    intencion_actual = "MANTENER_PERSIANA"
            else:
                # 2. PERSIANA: Exige ser vertical (R > 1.9)
                if aspect_ratio > 1.9:
                    intencion_actual = "ENTRAR_PERSIANA"
                

                elif aspect_ratio < 1.5:
                    intencion_actual = "LUZ_ON"

                elif aspect_ratio < 1.9:
                    intencion_actual = "LUZ_OFF"

            
            #  FILTRO 0.2s 
            if intencion_actual != modo_candidato:
                modo_candidato = intencion_actual
                timer_modo = time.time()
            
            gesto_confirmado = "NADA"
            if (time.time() - timer_modo) > 0.2:
                gesto_confirmado = modo_candidato
            
            #  LÓGICA DE CONTROL 
            if gesto_confirmado == "LUZ_ON": 
                modo_txt = "LUZ ON"
                estado_luz = True
                modo_persiana_bloqueado = False
            
            elif (modo_persiana_bloqueado and gesto_confirmado != "SALIR_PERSIANA") or gesto_confirmado == "ENTRAR_PERSIANA":
                if not modo_persiana_bloqueado:
                    modo_persiana_bloqueado = True
                    accion_oficial = "PARADA"

                modo_txt = "CONTROLANDO..."
                target_altura = np.interp(cy, [50, 400], [0, 200])
                diferencia = target_altura - altura_persiana_px
                
                accion_raw = "PARADA"
                if abs(diferencia) > 10: 
                    if diferencia > 0: accion_raw = "BAJANDO..."
                    else: accion_raw = "SUBIENDO..."
                
                if accion_oficial == "PARADA" and accion_raw != "PARADA":
                    accion_oficial = accion_raw
                    accion_candidata = accion_raw 
                    timer_cambio_estado = time.time()
                else:
                    if accion_raw != accion_candidata:
                        accion_candidata = accion_raw
                        timer_cambio_estado = time.time() 
                    if (time.time() - timer_cambio_estado) > 0.5:
                        accion_oficial = accion_candidata
                altura_persiana_px = int(target_altura)
                
            elif gesto_confirmado == "LUZ_OFF":
                modo_txt = "LUZ OFF"
                estado_luz = False
            
            if gesto_confirmado == "SALIR_PERSIANA":
                modo_persiana_bloqueado = False

    else:
        modo_persiana_bloqueado = False

    frame = dibujar_interfaz(frame, estado_luz, altura_persiana_px, modo_txt, 
                             modo_persiana_bloqueado, background is not None, 
                             accion_oficial, calibracion_color_hecha)
    
    mask_bgr = cv2.cvtColor(cv2.resize(mask_final, (150, 150)), cv2.COLOR_GRAY2BGR)
    frame[0:150, 0:150] = mask_bgr 

    cv2.imshow('Domotica', frame)
    
    key = cv2.waitKey(1)
    if key == 27: break
    elif key == ord('b') or key == ord('B'):
        gray_bg = cv2.cvtColor(clean_frame, cv2.COLOR_BGR2GRAY)
        background = cv2.GaussianBlur(gray_bg, (21, 21), 0)
        print("FONDO CAPTURADO.")

cap.release()
cv2.destroyAllWindows()