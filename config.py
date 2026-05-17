import os

CONFIG = {
    # Camera
    'camera_index': 0,
    'default_width': 640,
    'default_height': 480,

    # Capture
    'capture_directory': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captures'),
    'image_format': 'jpg',

    # Keyboard shortcuts
    'capture_key': ' ',   # Space = single capture
    'burst_key':   'b',   # B = burst mode toggle
    'exit_key':    'q',   # Q = quit

    # Display
    'window_title': 'Camera Control Application',

    # Performance
    'target_fps': 30,
    'burst_interval_ms': 100,   # 10 fps burst

    # Parameter ranges
    'exposure_min': -13,
    'exposure_max': -1,
    'exposure_default': -6,
    'brightness_min': 0,
    'brightness_max': 100,
    'brightness_default': 50,
    'contrast_min': 0,
    'contrast_max': 100,
    'contrast_default': 50,
}
