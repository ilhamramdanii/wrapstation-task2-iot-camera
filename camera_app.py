import sys
import os
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QSlider, QComboBox, QVBoxLayout, QHBoxLayout,
    QStatusBar, QFrame, QCheckBox, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from config import CONFIG


RESOLUTIONS = {
    '320 × 240':   (320,  240),
    '640 × 480':   (640,  480),
    '1280 × 720':  (1280, 720),
    '1920 × 1080': (1920, 1080),
}

# ─── Stylesheet ───────────────────────────────────────────────────────────────

STYLESHEET = """
QMainWindow, QWidget { background: #0f1117; color: #e2e8f0; font-size: 13px; }

/* Side panel card */
QFrame#panel {
    background: #171923;
    border-radius: 16px;
}

/* Preview area */
QLabel#preview {
    background: #080a0f;
    border-radius: 14px;
    color: #334155;
    font-size: 14px;
}

/* ── Buttons ── */
QPushButton {
    background: #1e2030;
    border: 1px solid #252840;
    border-radius: 9px;
    padding: 9px 14px;
    color: #94a3b8;
    font-weight: 500;
}
QPushButton:hover   { background: #252840; border-color: #353860; color: #e2e8f0; }
QPushButton:pressed { background: #181a2a; }

QPushButton#captureBtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #D4A827, stop:1 #9A7818);
    border: none;
    border-radius: 11px;
    color: #0f0f0f;
    font-size: 15px;
    font-weight: 700;
    padding: 14px;
    letter-spacing: 0.5px;
}
QPushButton#captureBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #E8C050, stop:1 #C9A227);
}
QPushButton#captureBtn:pressed { background: #7A5E10; color: #fff; }

QPushButton#burstBtn {
    background: #1A1200;
    border: 1px solid #3A2800;
    color: #C9A227;
    font-weight: 600;
}
QPushButton#burstBtn:hover { background: #251800; border-color: #5A4010; }

QPushButton#exitBtn {
    background: transparent;
    border: 1px solid #2d1515;
    color: #f87171;
}
QPushButton#exitBtn:hover { background: #1a0a0a; border-color: #4d2020; }

QPushButton#resetBtn {
    background: transparent;
    border: 1px solid #1e2030;
    color: #64748b;
    font-size: 12px;
}
QPushButton#resetBtn:hover { background: #1a1c2a; color: #94a3b8; }

/* ── Sliders ── */
QSlider::groove:horizontal {
    background: #1e2038;
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #C9A227;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #fff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: 2px solid #C9A227;
}
QSlider::handle:horizontal:hover {
    background: #C9A227;
    border-color: #fff;
}

/* ── ComboBox ── */
QComboBox {
    background: #1e2030;
    border: 1px solid #252840;
    border-radius: 9px;
    padding: 8px 12px;
    color: #e2e8f0;
}
QComboBox:hover { border-color: #C9A227; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { width: 10px; height: 10px; }
QComboBox QAbstractItemView {
    background: #171923;
    border: 1px solid #252840;
    border-radius: 8px;
    selection-background-color: #1e2030;
    color: #e2e8f0;
    padding: 4px;
    outline: none;
}

/* ── Checkbox ── */
QCheckBox { color: #64748b; font-size: 12px; spacing: 8px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1.5px solid #2d3155;
    border-radius: 4px;
    background: #1e2030;
}
QCheckBox::indicator:checked { background: #C9A227; border-color: #C9A227; }
QCheckBox:hover { color: #94a3b8; }

/* ── Status bar ── */
QStatusBar {
    background: #0a0c11;
    color: #334155;
    font-size: 11px;
    border-top: 1px solid #171923;
}
"""


# ─── Camera Scan Thread ───────────────────────────────────────────────────────

class CameraScanThread(QThread):
    """Scan index kamera 0-9 di background agar UI tidak freeze."""
    scan_done = pyqtSignal(list)   # list of int (indices yang berhasil dibuka)

    def run(self):
        found = []
        for i in range(10):
            if self.isInterruptionRequested():
                return
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                found.append(i)
                cap.release()
        self.scan_done.emit(found)


# ─── Camera Thread ────────────────────────────────────────────────────────────

class CameraThread(QThread):
    frame_ready  = pyqtSignal(np.ndarray)
    fps_updated  = pyqtSignal(float)
    error_signal = pyqtSignal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running      = False
        self.cap          = None
        self._fps_counter = 0
        self._fps_timer   = datetime.now()

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.error_signal.emit("Kamera tidak ditemukan. Pastikan webcam terhubung.")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CONFIG['default_width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['default_height'])
        self.cap.set(cv2.CAP_PROP_FPS,          CONFIG['target_fps'])

        self.running  = True
        fail_count    = 0
        MAX_FAILS     = 30

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                fail_count += 1
                if fail_count >= MAX_FAILS:
                    self.error_signal.emit("Kamera terputus. Pastikan webcam masih terhubung.")
                    break
                continue

            fail_count = 0
            self.frame_ready.emit(frame)

            self._fps_counter += 1
            elapsed = (datetime.now() - self._fps_timer).total_seconds()
            if elapsed >= 1.0:
                self.fps_updated.emit(self._fps_counter / elapsed)
                self._fps_counter = 0
                self._fps_timer   = datetime.now()

        self.cap.release()

    def set_resolution(self, width, height):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def set_exposure(self, value):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, value)

    def set_brightness(self, value):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def set_contrast(self, value):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_CONTRAST, value)

    def stop(self):
        self.running = False
        self.wait()


# ─── Main Application ─────────────────────────────────────────────────────────

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_frame      = None
        self.capture_count      = 0
        self.burst_active       = False
        self.burst_count        = 0
        self.burst_start        = None
        self.current_fps        = 0.0
        self.current_width      = CONFIG['default_width']
        self.current_height     = CONFIG['default_height']
        self.target_width       = CONFIG['default_width']
        self.target_height      = CONFIG['default_height']
        self.flip_horizontal    = True
        self.active_camera_index = CONFIG['camera_index']

        os.makedirs(CONFIG['capture_directory'], exist_ok=True)

        self._init_ui()

        self.burst_timer = QTimer()
        self.burst_timer.timeout.connect(self._burst_capture)
        self.burst_timer.setInterval(CONFIG['burst_interval_ms'])

        # Scan kamera di background, lalu start kamera aktif
        QTimer.singleShot(200, self._scan_cameras)

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle(CONFIG['window_title'])
        self.setMinimumSize(960, 640)
        self.resize(1120, 720)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 12)

        # ── Preview (kiri) ────────────────────────────────────────────────
        self.preview_label = QLabel("Menghubungkan kamera…")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.preview_label, stretch=1)

        # ── Side panel (kanan) ────────────────────────────────────────────
        from PyQt5.QtWidgets import QScrollArea

        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(300)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(16, 18, 16, 16)
        pl.setSpacing(0)

        # ── Helpers ──────────────────────────────────────────────────────
        def divider():
            f = QFrame()
            f.setFrameShape(QFrame.HLine)
            f.setFixedHeight(1)
            f.setStyleSheet("background: #1e2138; margin: 0px;")
            return f

        def section_label(text):
            l = QLabel(text)
            l.setStyleSheet(
                "color: #334155; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;"
            )
            return l

        def make_slider(min_v, max_v, default_v, label_text):
            col = QVBoxLayout()
            col.setSpacing(5)
            header = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #64748b; font-size: 12px;")
            val_lbl = QLabel(str(default_v))
            val_lbl.setStyleSheet("color: #C9A227; font-size: 12px; font-weight: 700;")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            header.addWidget(lbl)
            header.addStretch()
            header.addWidget(val_lbl)
            col.addLayout(header)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(default_v)
            slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
            col.addWidget(slider)
            return col, slider

        def stat_row(key, value_widget):
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet("color: #334155; font-size: 12px;")
            row.addWidget(k)
            row.addStretch()
            row.addWidget(value_widget)
            return row

        # ── Header: title + FPS (selalu terlihat, di luar scroll) ────────
        hdr = QHBoxLayout()
        title = QLabel("Camera Control")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f1f5f9;")
        self.fps_label = QLabel("-- fps")
        self.fps_label.setStyleSheet(
            "background: #1A1200; color: #C9A227; font-size: 11px; font-weight: 700;"
            "padding: 3px 10px; border-radius: 10px; border: 1px solid #3A2800;"
        )
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.fps_label)
        pl.addLayout(hdr)
        pl.addSpacing(14)

        # ── Scroll area untuk semua kontrol ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { background: transparent; width: 4px; border-radius: 2px; }"
            "QScrollBar::handle:vertical { background: #2a2d45; border-radius: 2px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 0, 6, 0)
        bl.setSpacing(0)

        # ── Camera selector ──
        bl.addWidget(section_label("CAMERA"))
        bl.addSpacing(8)
        cam_row = QHBoxLayout()
        cam_row.setSpacing(6)
        self.cam_combo = QComboBox()
        self.cam_combo.addItem("Scanning cameras…")
        self.cam_combo.setEnabled(False)
        self.cam_combo.currentIndexChanged.connect(self._on_camera_change)
        self.scan_btn = QPushButton("↻")
        self.scan_btn.setFixedSize(36, 36)
        self.scan_btn.setToolTip("Scan ulang kamera")
        self.scan_btn.clicked.connect(self._scan_cameras)
        cam_row.addWidget(self.cam_combo)
        cam_row.addWidget(self.scan_btn)
        bl.addLayout(cam_row)
        bl.addSpacing(16)
        bl.addWidget(divider())
        bl.addSpacing(16)

        # ── Resolution ──
        bl.addWidget(section_label("RESOLUTION"))
        bl.addSpacing(8)
        self.res_combo = QComboBox()
        for name in RESOLUTIONS:
            self.res_combo.addItem(name)
        self.res_combo.setCurrentText("640 × 480")
        self.res_combo.currentTextChanged.connect(self._on_resolution_change)
        bl.addWidget(self.res_combo)
        bl.addSpacing(16)
        bl.addWidget(divider())
        bl.addSpacing(16)

        # ── Parameters ──
        bl.addWidget(section_label("PARAMETERS"))
        bl.addSpacing(12)

        exp_row, self.exposure_slider = make_slider(
            CONFIG['exposure_min'], CONFIG['exposure_max'],
            CONFIG['exposure_default'], "Exposure"
        )
        bl.addLayout(exp_row)
        bl.addSpacing(12)

        br_row, self.brightness_slider = make_slider(
            CONFIG['brightness_min'], CONFIG['brightness_max'],
            CONFIG['brightness_default'], "Brightness (ISO)"
        )
        bl.addLayout(br_row)
        bl.addSpacing(12)

        ct_row, self.contrast_slider = make_slider(
            CONFIG['contrast_min'], CONFIG['contrast_max'],
            CONFIG['contrast_default'], "Contrast"
        )
        bl.addLayout(ct_row)
        bl.addSpacing(10)

        self.flip_checkbox = QCheckBox("Mirror (Flip Horizontal)")
        self.flip_checkbox.setChecked(self.flip_horizontal)
        self.flip_checkbox.stateChanged.connect(
            lambda s: setattr(self, 'flip_horizontal', bool(s))
        )
        bl.addWidget(self.flip_checkbox)
        bl.addSpacing(16)
        bl.addWidget(divider())
        bl.addSpacing(16)

        # ── Session info ──
        bl.addWidget(section_label("SESSION"))
        bl.addSpacing(10)

        self.info_res = QLabel(f"{self.current_width} × {self.current_height}")
        self.info_res.setStyleSheet("color: #C9A227; font-size: 12px; font-weight: 600;")
        self.info_count = QLabel("0 foto")
        self.info_count.setStyleSheet("color: #C9A227; font-size: 12px; font-weight: 600;")
        self.info_elapsed = QLabel("--")
        self.info_elapsed.setStyleSheet("color: #C9A227; font-size: 12px; font-weight: 600;")

        bl.addLayout(stat_row("Resolusi", self.info_res))
        bl.addSpacing(7)
        bl.addLayout(stat_row("Captured", self.info_count))
        bl.addSpacing(7)
        bl.addLayout(stat_row("Burst elapsed", self.info_elapsed))
        bl.addSpacing(4)
        bl.addStretch()

        scroll.setWidget(body)
        pl.addWidget(scroll)
        pl.addSpacing(10)

        # ── Keyboard hint ─────────────────────────────────────────────────
        hint = QLabel("SPACE  ·  B  ·  Q")
        hint.setStyleSheet("color: #1e2540; font-size: 10px; letter-spacing: 2px;")
        hint.setAlignment(Qt.AlignCenter)
        pl.addWidget(hint)
        pl.addSpacing(10)

        # ── Action buttons (selalu terlihat, di luar scroll) ─────────────
        self.capture_btn = QPushButton("Capture")
        self.capture_btn.setObjectName("captureBtn")
        self.capture_btn.clicked.connect(self._single_capture)
        pl.addWidget(self.capture_btn)
        pl.addSpacing(6)

        self.burst_btn = QPushButton("Burst Mode")
        self.burst_btn.setObjectName("burstBtn")
        self.burst_btn.clicked.connect(self._toggle_burst)
        pl.addWidget(self.burst_btn)
        pl.addSpacing(6)

        bot = QHBoxLayout()
        bot.setSpacing(6)
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_params)
        exit_btn = QPushButton("Quit")
        exit_btn.setObjectName("exitBtn")
        exit_btn.clicked.connect(self.close)
        bot.addWidget(reset_btn)
        bot.addWidget(exit_btn)
        pl.addLayout(bot)

        root.addWidget(panel)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Siap")

    # ─── Camera ──────────────────────────────────────────────────────────────

    def _scan_cameras(self):
        """Jalankan scan kamera di background thread."""
        self.cam_combo.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.cam_combo.clear()
        self.cam_combo.addItem("Scanning cameras…")
        self.status_bar.showMessage("Mendeteksi kamera…")

        self._scan_thread = CameraScanThread()
        self._scan_thread.scan_done.connect(self._on_scan_done)
        self._scan_thread.start()

    def _on_scan_done(self, found):
        """Dipanggil setelah scan selesai — populate dropdown & start kamera."""
        self.cam_combo.blockSignals(True)
        self.cam_combo.clear()

        if not found:
            self.cam_combo.addItem("Tidak ada kamera")
            self.cam_combo.setEnabled(False)
            self.scan_btn.setEnabled(True)
            self.status_bar.showMessage("Tidak ada kamera yang terdeteksi.")
            return

        for idx in found:
            label = f"Camera {idx}  {'(Built-in)' if idx == 0 else '(External)'}"
            self.cam_combo.addItem(label, userData=idx)

        # Pilih kamera yang sedang aktif (atau index 0 kalau tidak ada)
        target = self.active_camera_index
        for i in range(self.cam_combo.count()):
            if self.cam_combo.itemData(i) == target:
                self.cam_combo.setCurrentIndex(i)
                break

        self.cam_combo.blockSignals(False)
        self.cam_combo.setEnabled(True)
        self.scan_btn.setEnabled(True)

        self.status_bar.showMessage(f"{len(found)} kamera ditemukan")
        self._start_camera(self.active_camera_index)

    def _on_camera_change(self, combo_index):
        """Dipanggil saat user memilih kamera lain dari dropdown."""
        new_index = self.cam_combo.itemData(combo_index)
        if new_index is None or new_index == self.active_camera_index:
            return

        self.active_camera_index = new_index
        self.fps_label.setText("-- fps")
        self.preview_label.setText("Menghubungkan kamera…")

        # Stop thread lama
        if hasattr(self, 'camera_thread') and self.camera_thread.isRunning():
            self.camera_thread.stop()

        self._start_camera(new_index)

    def _start_camera(self, index=None):
        if index is None:
            index = self.active_camera_index

        self.status_bar.showMessage(f"Meminta izin akses Camera {index}…")

        # Buka sekali di main thread agar macOS AVFoundation tampilkan dialog izin
        test   = cv2.VideoCapture(index)
        opened = test.isOpened()
        test.release()

        if not opened:
            self.preview_label.setText(
                "⚠  Akses kamera ditolak atau tidak tersedia.\n\n"
                "System Settings → Privacy & Security → Camera\n"
                "centang Terminal, lalu restart aplikasi."
            )
            self.status_bar.showMessage("Kamera tidak dapat diakses.")
            return

        self.camera_thread = CameraThread(index)
        self.camera_thread.frame_ready.connect(self._on_frame)
        self.camera_thread.fps_updated.connect(self._on_fps)
        self.camera_thread.error_signal.connect(self._on_camera_error)
        self.camera_thread.start()
        self.status_bar.showMessage(f"Camera {index} aktif")

    def _apply_frame_params(self, frame):
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)

        b_offset = int((self.brightness_slider.value() - 50) * 2.54)
        c_alpha  = self.contrast_slider.value() / 50.0
        frame    = cv2.convertScaleAbs(frame, alpha=c_alpha, beta=b_offset)

        ev = self.exposure_slider.value() - CONFIG['exposure_default']
        if ev != 0:
            inv_gamma = 1.0 / (2.0 ** (ev * 0.3))
            table = np.array(
                [min(255, int((i / 255.0) ** inv_gamma * 255)) for i in range(256)],
                dtype=np.uint8,
            )
            frame = cv2.LUT(frame, table)

        return frame

    def _draw_overlay(self, frame):
        """Viewfinder overlay — gambar di atas display frame, tidak masuk ke file capture."""
        h, w   = frame.shape[:2]
        now    = datetime.now()
        GOLD   = (39,  162, 201)   # BGR untuk #C9A227
        WHITE  = (220, 220, 220)
        RED    = (60,   60, 210)   # merah di BGR
        FONT   = cv2.FONT_HERSHEY_SIMPLEX
        AA     = cv2.LINE_AA
        pad    = 14

        # ── 1. Corner brackets ─────────────────────────────────────────────
        blen = max(16, w // 36)
        for (ox, oy), dx, dy in [
            ((pad,       pad),       +1, +1),   # top-left
            ((w - pad,   pad),       -1, +1),   # top-right
            ((pad,       h - pad),   +1, -1),   # bottom-left
            ((w - pad,   h - pad),   -1, -1),   # bottom-right
        ]:
            cv2.line(frame, (ox, oy), (ox + dx * blen, oy), WHITE, 2, AA)
            cv2.line(frame, (ox, oy), (ox, oy + dy * blen), WHITE, 2, AA)

        # ── 2. FPS + Res box (top-left, dalam bracket) ────────────────────
        bx, by, bw_box, bh_box = pad + 4, pad + 4, 152, 48
        bg = frame.copy()
        cv2.rectangle(bg, (bx, by), (bx + bw_box, by + bh_box), (8, 8, 8), -1)
        frame = cv2.addWeighted(bg, 0.55, frame, 0.45, 0)
        # Left accent strip
        cv2.rectangle(frame, (bx, by), (bx + 3, by + bh_box), GOLD, -1)
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}",
                    (bx + 10, by + 18), FONT, 0.46, GOLD, 1, AA)
        cv2.putText(frame, f"Res: {w}x{h}",
                    (bx + 10, by + 38), FONT, 0.46, GOLD, 1, AA)

        # ── 3. LIVE / REC indicator (top-right, dalam bracket) ─────────────
        if self.burst_active:
            elapsed   = (now - self.burst_start).total_seconds() if self.burst_start else 0
            rec_label = f"REC  {self.burst_count}  {elapsed:.1f}s"
            (tw, _), _ = cv2.getTextSize(rec_label, FONT, 0.46, 1)
            rx  = w - pad - 4 - tw - 20
            ry  = pad + 4
            bg2 = frame.copy()
            cv2.rectangle(bg2, (rx - 4, ry), (rx + tw + 20, ry + 24), (8, 8, 8), -1)
            frame = cv2.addWeighted(bg2, 0.55, frame, 0.45, 0)
            # Blinking dot
            if now.microsecond < 500_000:
                cv2.circle(frame, (rx + 7, ry + 12), 5, RED, -1, AA)
            cv2.putText(frame, rec_label, (rx + 17, ry + 17), FONT, 0.46, RED, 1, AA)
        else:
            # LIVE label
            (lw, _), _ = cv2.getTextSize("LIVE", FONT, 0.46, 1)
            lx  = w - pad - 4 - lw - 20
            ly  = pad + 4
            bg2 = frame.copy()
            cv2.rectangle(bg2, (lx - 4, ly), (lx + lw + 20, ly + 24), (8, 8, 8), -1)
            frame = cv2.addWeighted(bg2, 0.55, frame, 0.45, 0)
            if now.microsecond < 500_000:
                cv2.circle(frame, (lx + 7, ly + 12), 5, RED, -1, AA)
            cv2.putText(frame, "LIVE", (lx + 17, ly + 17), FONT, 0.46, RED, 1, AA)

        # ── 4. Timestamp (bottom-left, di atas bracket) ────────────────────
        ts = now.strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(frame, ts, (pad + 4, h - pad - 5), FONT, 0.38, (170, 170, 170), 1, AA)

        # ── 5. Center crosshair ────────────────────────────────────────────
        cx, cy = w // 2, h // 2
        clen   = max(10, w // 48)
        cv2.line(frame, (cx - clen, cy), (cx - 4,    cy), WHITE, 1, AA)
        cv2.line(frame, (cx + 4,    cy), (cx + clen, cy), WHITE, 1, AA)
        cv2.line(frame, (cx, cy - clen), (cx, cy - 4),    WHITE, 1, AA)
        cv2.line(frame, (cx, cy + 4),    (cx, cy + clen), WHITE, 1, AA)
        cv2.circle(frame, (cx, cy), clen + 8, WHITE, 1, AA)

        return frame

    def _on_frame(self, frame):
        if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
            interp = cv2.INTER_AREA if self.target_width < frame.shape[1] else cv2.INTER_LINEAR
            frame  = cv2.resize(frame, (self.target_width, self.target_height), interpolation=interp)

        frame = self._apply_frame_params(frame)
        self.current_frame = frame.copy()   # simpan bersih (tanpa overlay) untuk capture
        h, w, ch = frame.shape

        display = self._draw_overlay(frame.copy())

        rgb    = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        qimg   = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix    = QPixmap.fromImage(qimg)
        scaled = pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

        self.current_width  = w
        self.current_height = h

    def _on_fps(self, fps):
        self.current_fps = fps
        self.fps_label.setText(f"{fps:.0f} fps")
        self.info_res.setText(f"{self.current_width} × {self.current_height}")

    def _on_camera_error(self, msg):
        self.preview_label.setText(f"⚠  {msg}")
        self.status_bar.showMessage(msg)

    def _on_resolution_change(self, text):
        w, h = RESOLUTIONS[text]
        self.target_width  = w
        self.target_height = h
        if hasattr(self, 'camera_thread'):
            self.camera_thread.set_resolution(w, h)
        self.status_bar.showMessage(f"Resolusi → {w} × {h}")

    # ─── Capture ─────────────────────────────────────────────────────────────

    def _single_capture(self):
        if self.current_frame is None:
            return
        path = self._save_frame(self.current_frame)
        if path:
            self.capture_count += 1
            self.info_count.setText(f"{self.capture_count} foto")
            self.status_bar.showMessage(f"✓  {path}")

    def _toggle_burst(self):
        self.burst_active = not self.burst_active
        if self.burst_active:
            self.burst_count = 0
            self.burst_start = datetime.now()
            self.burst_timer.start()
            self.burst_btn.setText("⏹  Stop Burst")
            self.burst_btn.setStyleSheet(
                "background: #2A1A00; border: 1px solid #8A6010; "
                "color: #E8C050; font-weight: 700; border-radius: 9px; padding: 9px 14px;"
            )
            self.status_bar.showMessage("Burst mode aktif…")
        else:
            self.burst_timer.stop()
            elapsed = (datetime.now() - self.burst_start).total_seconds() if self.burst_start else 0
            self.burst_btn.setText("⚡  Burst Mode")
            self.burst_btn.setStyleSheet("")   # kembali ke stylesheet global
            self.info_elapsed.setText(f"{elapsed:.1f}s")
            self.status_bar.showMessage(f"Burst selesai — {self.burst_count} foto dalam {elapsed:.1f}s")

    def _burst_capture(self):
        if self.current_frame is None:
            return
        self.burst_count += 1
        path = self._save_frame(self.current_frame, burst_seq=self.burst_count)
        if path:
            self.capture_count += 1
            self.info_count.setText(f"{self.capture_count} foto")
        elapsed = (datetime.now() - self.burst_start).total_seconds() if self.burst_start else 0
        self.info_elapsed.setText(f"{elapsed:.1f}s")

    def _save_frame(self, frame, burst_seq=None):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = (
            f"capture_{ts}_burst_{burst_seq:03d}.{CONFIG['image_format']}"
            if burst_seq else
            f"capture_{ts}.{CONFIG['image_format']}"
        )
        path = os.path.join(CONFIG['capture_directory'], filename)
        ok = cv2.imwrite(path, frame)
        if not ok:
            self.status_bar.showMessage(f"Gagal menyimpan: {path}")
            return None
        return path

    def _reset_params(self):
        self.exposure_slider.setValue(CONFIG['exposure_default'])
        self.brightness_slider.setValue(CONFIG['brightness_default'])
        self.contrast_slider.setValue(CONFIG['contrast_default'])
        self.res_combo.setCurrentText("640 × 480")
        self.flip_checkbox.setChecked(True)
        self.status_bar.showMessage("Parameter direset ke default")

    # ─── Keyboard ────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.text().lower()
        if key == CONFIG['capture_key'] or event.key() == Qt.Key_Space:
            self._single_capture()
        elif key == CONFIG['burst_key']:
            self._toggle_burst()
        elif key == CONFIG['exit_key']:
            self.close()

    # ─── Cleanup ─────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self.burst_active:
            self.burst_timer.stop()
        if hasattr(self, '_scan_thread') and self._scan_thread.isRunning():
            self._scan_thread.requestInterruption()
            self._scan_thread.wait(3000)   # max 3s; thread cek isInterruptionRequested()
        if hasattr(self, 'camera_thread') and self.camera_thread.isRunning():
            self.camera_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
