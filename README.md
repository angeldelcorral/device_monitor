# Device Monitor

**Device Monitor** es una aplicación de escritorio desarrollada en Python que permite detectar, listar y monitorear eventos de diversos dispositivos conectados al sistema, incluyendo dispositivos HID, puertos serie (COM) y dispositivos USB genéricos. Además, cuenta con una funcionalidad para capturar eventos globales de teclado y ratón.

La interfaz gráfica está construida con `tkinter` y estilizada con `ttkbootstrap`, ofreciendo una experiencia de usuario moderna y funcional.

## Funcionalidades Principales

### 1. Detección de Dispositivos
El sistema es capaz de escanear y listar los siguientes tipos de dispositivos:
*   **HID (Human Interface Devices):** Teclados, ratones, gamepads, etc. Utiliza la librería `hidapi`.
*   **Puertos COM (Serial):** Dispositivos conectados vía puerto serie. Utiliza `pyserial`.
*   **USB (Genérico):** Listado de dispositivos USB conectados utilizando `pyusb`.

### 2. Monitoreo en Tiempo Real
Permite seleccionar un dispositivo de la lista y comenzar a monitorear sus eventos.
*   **Visualización de Logs:** Los eventos capturados se muestran en tiempo real en un panel de texto con marca de tiempo y nivel de severidad.
*   **Gráficos en Vivo:** Utiliza `matplotlib` para graficar datos de los eventos en tiempo real, facilitando el análisis visual de la actividad del dispositivo.

### 3. Captura Global de Teclado y Ratón
Incluye un módulo (`km_listener.py`) que permite capturar eventos de teclado y ratón a nivel global del sistema, independientemente de la ventana que tenga el foco.
*   **Nota:** Esta funcionalidad requiere permisos de administrador/root para funcionar correctamente.
*   **Advertencia:** Úsese con responsabilidad.

### 4. Gestión de Logs y Exportación
*   **Guardar Log:** Permite guardar el contenido actual del panel de logs en un archivo de texto (`.txt`).
*   **Exportar CSV:** Permite exportar el historial de eventos capturados a un archivo CSV para su posterior análisis.
*   **Directorio de Logs:** Los logs se organizan automáticamente en una carpeta `logs/`.

### 5. Filtrado y Búsqueda
Barra de búsqueda integrada para filtrar la lista de dispositivos detectados por nombre o ID.

## Requisitos del Sistema

El proyecto requiere **Python 3.x** y las siguientes librerías externas con sus versiones específicas:

| Módulo            | Versión    | Descripción                                                  |
| :---------------- | :--------- | :----------------------------------------------------------- |
| `ttkbootstrap`    | `1.19.0`   | Estilos modernos para Tkinter.                               |
| `hidapi`          | `0.14.0`   | Comunicación con dispositivos HID.                           |
| `pyusb`           | `1.2.1`    | Acceso a dispositivos USB (requiere backend libusb).         |
| `pyserial`        | `3.5`      | Comunicación con puertos serie.                              |
| `keyboard`        | `0.13.5`   | Captura global de teclado.                                   |
| `mouse`           | `0.7.1`    | Captura global de ratón.                                     |
| `matplotlib`      | `3.8.1`    | Generación de gráficos.                                      |
| `Pillow`          | `10.3.0`   | Procesamiento de imágenes (dep. de matplotlib/ttkbootstrap). |
| `python-dotenv`   | `1.0.1`    | Gestión de variables de entorno.                             |
| `requests`        | `2.32.3`   | Peticiones HTTP (si aplica).                                 |

### Instalación de Dependencias

Puedes instalar todas las dependencias necesarias ejecutando el siguiente comando en tu terminal:

```bash
pip install -r requirements.txt
```

> **Nota:** Para el uso de `pyusb` en Windows, es posible que necesites instalar un controlador `libusb` para el dispositivo específico (puedes usar herramientas como Zadig).

## Uso

1.  Ejecuta el archivo principal de la aplicación:
    ```bash
    python main.py
    ```
2.  La aplicación se abrirá mostrando la lista de dispositivos detectados.
3.  Selecciona un dispositivo de la lista.
4.  Haz clic en **"Start Monitor"** para comenzar a capturar eventos.
5.  (Opcional) Activa la casilla **"Enable global keyboard/mouse capture"** para monitorear entradas globales.
6.  Utiliza los botones de **"Save Log..."** o **"Export CSV"** para guardar los datos.

## Estructura del Proyecto

*   `main.py`: Punto de entrada de la aplicación y lógica de la interfaz gráfica.
*   `hid_reader.py`: Módulo para lectura de dispositivos HID.
*   `serial_reader.py`: Módulo para lectura de puertos serie.
*   `usb_reader.py`: Módulo para lectura de dispositivos USB.
*   `km_listener.py`: Módulo para la captura global de teclado y ratón.
*   `plotter.py`: Módulo encargado de la visualización gráfica de eventos.
*   `utils.py`: Funciones de utilidad (ej. creación de directorios).
*   `requirements.txt`: Lista de dependencias del proyecto.
