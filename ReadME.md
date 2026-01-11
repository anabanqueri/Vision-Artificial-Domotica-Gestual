Este proyecto implementa un sistema de **Interacción Hombre-Máquina (HMI)** basado en visión por ordenador clásica. El objetivo es simular un entorno de control domótico (luces y persianas) que puede ser operado mediante gestos manuales sin contacto, utilizando la cámara del ordenador.

## Descripción del Sistema

El sistema procesa el flujo de vídeo en tiempo real para detectar la mano del usuario, interpretar su intención y ejecutar acciones en una interfaz virtual.

### Funcionalidades:
1.  **Control de Iluminación:** Encender/Apagar una luz virtual mediante gestos de mano abierta o puño.
2.  **Control de Persianas:** Modulación analógica de la altura de una persiana mediante seguimiento (tracking) de la mano.
3.  **Robustez:** Sistema de calibración de color dinámica y estabilización temporal para evitar falsos positivos.

## Requisitos e Instalación

El proyecto requiere **voi-lab** y las siguientes librerías:

* OpenCV (`opencv-python`)
* NumPy (`numpy`)

Para instalar las dependencias:
pip install opencv-python numpy

***Guía de Uso (Paso a Paso)***
Para ejecutar el programa, corre el script principal:
python main.py

1. Fase de Calibración (Inicialización)
Al iniciar, el sistema necesita aprender el entorno:

Color de Piel: Coloca tu mano frente a la cámara y haz CLICK IZQUIERDO con el ratón sobre ella. Esto ajusta los filtros de color a tu tono de piel y luz actual.

Fondo Estático: Aparta la mano de la cámara (deja el fondo despejado) y pulsa la tecla 'B'.

2. Interacción (Gestos)
Una vez calibrado, puedes realizar las siguientes acciones:

- Encender Luz: Muestra la mano abierta (palma extendida). El indicador de luz se volverá amarillo.

- Apagar Luz: Cierra la mano formando un puño. La luz se apagará.

- Modo Persiana: Coloca la mano de perfil (vertical) o levanta el dedo índice.

Una vez dentro del modo persiana:

Subir mano: Sube la persiana.

Bajar mano: Baja la persiana.

Para salir: Cierra el puño o retira la mano.

Nota sobre Estabilidad: El sistema incorpora un retardo de seguridad de 0.2 segundos para cambiar entre modos (Luz/Persiana) y evitar parpadeos erróneos. Mantén el gesto firme 0.2 segundos hasta que el sistema responda.

Tecnologías y Técnicas Aplicadas
Este proyecto integra conocimientos adquiridos en los laboratorios de la asignatura:

Calibración de Cámara (Lab 2): Uso de matriz intrínseca y coeficientes de distorsión para corregir la imagen.

Segmentación Híbrida (Lab 1 & 4): Combinación de Sustracción de Fondo (para detectar movimiento) y Espacio de Color HSV (para validar piel).

Análisis Morfológico (Lab 3): Operaciones de erosión y dilatación para limpiar la máscara binaria.

Extracción de Características (Lab 3): Uso de Momentos de Hu (Centroides), Área del contorno y Relación de Aspecto (Bounding Rect) para clasificar gestos.

Tracking y Máquina de Estados: Lógica de seguimiento vertical para la persiana y filtrado temporal para la estabilidad de la interfaz.

Estructura del Proyecto
main.py: Código fuente principal de la aplicación.

camera_matrix.npy: Archivo de calibración (matriz intrínseca).

dist_coeffs.npy: Archivo de calibración (coeficientes de distorsión).

README.md: Este archivo de documentación.

Autores
Ana Banqueri Camy
Carolina Garicano Vidal

