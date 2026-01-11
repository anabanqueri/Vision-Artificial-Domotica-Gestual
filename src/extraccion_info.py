import cv2
import numpy as np
import os
import time


try:
    K = np.load("camera_matrix.npy")
    dist = np.load("dist_coeffs.npy")
    CALIBRATION_OK = True
    print("Sistema: Calibración cargada correctamente.")
except:
    print("AVISO: No se encontraron archivos .npy. Usando cámara sin calibrar.")
    CALIBRATION_OK = False

def undistort_frame(frame, K, dist):
    if not CALIBRATION_OK: return frame
    h, w = frame.shape[:2]
    new_K, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
    return cv2.undistort(frame, K, dist, None, new_K)

# 2. CARGA DE TEMPLATES 
TEMPLATES_DIR = "./patterns" 
templates = {}

print("\n--- CARGANDO PATRONES ---")
if os.path.exists(TEMPLATES_DIR):
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            # A. LIMPIEZA DE NOMBRE (LETRAC -> C)
            raw_name = filename.split(".")[0].upper()
            clean_name = raw_name.replace("LETRA", "").replace("PATTERN", "").strip()
            
            path = os.path.join(TEMPLATES_DIR, filename)
            img = cv2.imread(path, 0) # Cargar en gris
            
            if img is not None:
                # B. REDIMENSIONADO AUTOMÁTICO (El arreglo clave)
                # Si la plantilla es mayor de 300px, la reducimos.
                # Esto evita que 'matchTemplate' falle o ignore la letra.
                h, w = img.shape[:2]
                if h > 300 or w > 300:
                    scale = 300 / max(h, w)
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    print(f" > {clean_name}: Reducido de {w}x{h} a {new_w}x{new_h}")
                
                templates[clean_name] = img
                print(f" > {clean_name}: LISTA PARA DETECTAR")
            
    print(f"Total letras en memoria: {list(templates.keys())}\n")
else:
    print(f"ERROR ROJO: No existe la carpeta {TEMPLATES_DIR}")

# [cite_start]3. SISTEMA DE SEGURIDAD (Decodificador [cite: 58])
class SecuritySystem:
    def __init__(self, password):
        self.password = password       
        self.input_sequence = []       # Memoria actual
        self.last_detection_time = 0
        self.cooldown = 1.5            # Segundos entre letras
        self.is_unlocked = False
        self.error_timer = 0           # Para mostrar mensaje de error

    def update(self, detected_char):
        current_time = time.time()
        
        # Bloqueo temporal si hubo error o detección reciente
        if current_time < self.error_timer: return
        if (current_time - self.last_detection_time) < self.cooldown: return

        # Guardar letra
        self.input_sequence.append(detected_char)
        self.last_detection_time = current_time
        print(f"Secuencia: {self.input_sequence}")

        # Comprobar contraseña
        if len(self.input_sequence) == len(self.password):
            if self.input_sequence == self.password:
                self.is_unlocked = True
                print("¡DESBLOQUEADO!")
            else:
                print("Error en contraseña. Esperando...")
                self.error_timer = time.time() + 2.0 # Mostrar error 2 seg
                self.input_sequence = [] # Se borrará visualmente tras el error

    def get_display_info(self):
        # Devuelve el texto y el color para pintar en pantalla
        if self.is_unlocked:
            return "ACCESO CONCEDIDO - FASE 2", (0, 255, 0)
        
        if time.time() < self.error_timer:
            return "ERROR: SECUENCIA INCORRECTA", (0, 0, 255)
            
        seq_str = '-'.join(self.input_sequence) if self.input_sequence else "ESPERANDO..."
        return f"Pass: {seq_str}", (255, 255, 0)

def detectar_letra_visual(gray_frame, debug_frame):
    best_letter = None
    best_score = 0
    
    y_debug = 100 # Altura para empezar a escribir en pantalla
    
    # Probamos TODAS las plantillas cargadas
    for letter, tmpl in templates.items():
        # Comprobación de seguridad de tamaño
        if tmpl.shape[0] > gray_frame.shape[0] or tmpl.shape[1] > gray_frame.shape[1]:
            continue 

        res = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        #  DIBUJAR PUNTUACIONES 
        color = (0, 255, 0) if max_val > 0.50 else (0, 0, 255)
        text = f"{letter}: {max_val:.2f}"
        cv2.putText(debug_frame, text, (10, y_debug), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        y_debug += 25

        if max_val > best_score:
            best_score = max_val
            best_letter = letter

    # UMBRAL DE DETECCIÓN
    if best_score > 0.50: # Si supera el 50% de coincidencia
        return best_letter, best_score
    return None, 0

# 5. BUCLE PRINCIPAL
PASSWORD = ['A', 'C', 'C', 'A'] 
sistema = SecuritySystem(PASSWORD)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = undistort_frame(frame, K, dist)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. Detección
    # Le pasamos 'frame' para que pueda pintar los numeritos de debug sobre el color
    letra, score = detectar_letra_visual(gray, frame)
    
    # 3. Lógica
    if not sistema.is_unlocked:
        # Modo Candado
        if letra and time.time() > sistema.error_timer:
            # Dibujar caja alrededor de la detección (Feedback visual)
            cv2.putText(frame, f"VEO: {letra}", (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            sistema.update(letra)
    else:
        cv2.putText(frame, "TRACKER ACTIVADO", (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        # tracker.update(frame)...

    # 4. Mostrar Estado
    texto_estado, color_estado = sistema.get_display_info()
    cv2.putText(frame, texto_estado, (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color_estado, 2)
    
    cv2.imshow('Proyecto Vision - Diva Final', frame)
    
    # Salir con ESC
    if cv2.waitKey(1) == 27: 
        break

cap.release()

cv2.destroyAllWindows()
