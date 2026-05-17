# Wrapstation Task 2 — IoT Camera Control

A real-time desktop camera control application built with Python, PyQt5, and OpenCV. Supports live preview with viewfinder overlay, adjustable camera parameters (exposure, brightness, contrast), single-frame capture, and high-speed burst mode — all from a dark-themed GUI.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.13-5C3EE8?logo=opencv&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.0-013243?logo=numpy&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Tech Stack

| Technology | |
|-----------|--|
| ![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white) | **Python 3.9+** |
| ![OpenCV](https://img.shields.io/badge/OpenCV-4.13-5C3EE8?logo=opencv&logoColor=white) | **OpenCV 4.13** |
| ![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white) | **PyQt5 5.15** |
| ![NumPy](https://img.shields.io/badge/NumPy-2.0-013243?logo=numpy&logoColor=white) | **NumPy 2.0** |

---

## Prerequisites

- **Python** `>= 3.9`
- **pip** (included with Python)
- **Webcam / USB camera** (built-in or external)
- **Supported OS:** macOS, Windows, Linux

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/wrapstation-task2-iot-camera.git
cd wrapstation-task2-iot-camera
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python camera_app.py
```

> **macOS note:** If the camera permission dialog does not appear, go to  
> **System Settings → Privacy & Security → Camera** and enable access for Terminal.

---

## Features

- **Live Preview** — real-time camera feed with viewfinder overlay (FPS counter, resolution, timestamp, crosshair, LIVE/REC indicator)
- **Multi-camera support** — auto-detects all connected cameras (indices 0–9) via background scan; switch cameras without restarting
- **Resolution control** — choose from 320×240, 640×480, 1280×720, 1920×1080
- **Parameter control** — Exposure (shutter speed simulation via gamma LUT), Brightness (ISO offset), Contrast — all adjustable via sliders
- **Mirror mode** — flip horizontal toggle for selfie-style view
- **Single Capture** — saves the current clean frame (no overlay) as a timestamped JPEG
- **Burst Mode** — continuous capture at 10 fps (configurable in `config.py`)
- **Auto-timestamp filenames** — `capture_YYYY-MM-DD_HH-MM-SS.jpg` / `_burst_001.jpg`
- **Keyboard shortcuts** — `SPACE`, `B`, `Q` for capture, burst toggle, and quit
- **Clean shutdown** — camera thread and scan thread are stopped gracefully on exit

---

## Demo Sistem


https://drive.google.com/file/d/1kIfSUwRdak5n45xyY9q24M0BVU10dIZC/view?usp=sharing

> **Cara menambah screenshot/recording:**
> 1. Jalankan aplikasi: `python camera_app.py`
> 2. Screenshot UI: `Cmd+Shift+4` (macOS) → simpan ke `screenshots/main_interface.png`
> 3. Screen recording: `Cmd+Shift+5` (macOS) → export sebagai GIF menggunakan [Gifski](https://gif.ski) atau [GIPHY Capture](https://giphy.com/apps/giphycapture) → simpan ke `screenshots/demo.gif`

---

## Folder Structure

```
wrapstation-task2-iot-camera/
├── camera_app.py     # Main application (UI + camera threads + capture logic)
├── config.py         # All configurable parameters (camera, paths, shortcuts, sliders)
├── requirements.txt  # Python dependencies
├── screenshots/      # UI screenshots and demo GIF for README
├── captures/         # Saved images (auto-created, gitignored)
└── README.md
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `SPACE` | Capture single frame |
| `B` | Toggle burst mode on/off |
| `Q` | Quit application |

---

## Configuration

Edit `config.py` to change default behavior:

```python
CONFIG = {
    'camera_index': 0,          # Default camera (0 = built-in, 1 = first external, etc.)
    'default_width': 640,
    'default_height': 480,
    'capture_directory': '...',  # Auto-resolved to ./captures/ relative to script
    'image_format': 'jpg',
    'target_fps': 30,
    'burst_interval_ms': 100,   # 100ms = 10 fps burst

    'capture_key': ' ',         # Space
    'burst_key':   'b',
    'exit_key':    'q',

    'exposure_min': -13,  'exposure_max': -1,  'exposure_default': -6,
    'brightness_min': 0,  'brightness_max': 100, 'brightness_default': 50,
    'contrast_min': 0,    'contrast_max': 100,   'contrast_default': 50,
}
```

---

## Development Environment

Spesifikasi perangkat yang digunakan selama pengerjaan tugas:

| Komponen | Spesifikasi |
|----------|-------------|
| **OS** | macOS 26.2 (Build 25C56) |
| **Chip** | Apple M1 |
| **RAM** | 8 GB |
| **Display** | 2560 × 1600 Retina |
| **Python** | 3.9.6 |
| **OpenCV** | 4.13.0 |
| **PyQt5** | 5.15.11 |
| **NumPy** | 2.0.2 |

---

## License

**MIT**.
