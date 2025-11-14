from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox, QPushButton,
    QColorDialog, QMessageBox
)

from config import Config, ColorHex # type:ignore
from .tracker_thread import TrackerThread # type:ignore


class MainWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()

        self.setWindowTitle("Aimbot Control Panel")
        self.config = config

        self.tracker_thread = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Engine")
        self.btn_sync = QPushButton("Sync Engine")
        self.btn_save = QPushButton("Save Config")
        self.btn_stop = QPushButton("Stop Engine")
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_sync)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        # Create UI tabs
        self.init_general_tab()
        self.init_aimbot_tab()
        self.init_offset_tab()
        self.init_sensitivity_tab()

        # Bind actions
        self.btn_start.clicked.connect(self.start_engine)
        self.btn_stop.clicked.connect(self.stop_engine)
        self.btn_save.clicked.connect(self.save_config)
        self.btn_sync.clicked.connect(self.sync_engine)

    # --------------------------------------------------------------
    # TAB INITIALIZATION
    # --------------------------------------------------------------

    def init_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Target window
        layout.addWidget(QLabel("Target window title"))
        self.input_target = QLineEdit(self.config.general.target_win)
        layout.addWidget(self.input_target)

        # FOV (unsafe)
        layout.addWidget(QLabel("FOV (requires sync)"))
        self.spin_fov = QSpinBox()
        self.spin_fov.setRange(10, 2000)
        self.spin_fov.setValue(self.config.general.fov)
        layout.addWidget(self.spin_fov)

        # Debug mode
        self.chk_debug = QCheckBox("Enable debug")
        self.chk_debug.setChecked(self.config.general.debug_mode)
        layout.addWidget(self.chk_debug)

        # Color
        self.btn_color = QPushButton(f"Color: {self.config.general.color}")
        self.btn_color.clicked.connect(self.pick_color)
        layout.addWidget(self.btn_color)

        self.tabs.addTab(tab, "General")

        # Live updates
        self.chk_debug.stateChanged.connect(self.update_general_live)

    def init_aimbot_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Enabled
        self.chk_enabled = QCheckBox("Enable Aimbot")
        self.chk_enabled.setChecked(self.config.aimbot.enabled)
        layout.addWidget(self.chk_enabled)

        # Tolerance (unsafe)
        layout.addWidget(QLabel("Tolerance (requires sync)"))
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setRange(0, 255)
        self.spin_tolerance.setValue(self.config.aimbot.tolerance)
        layout.addWidget(self.spin_tolerance)

        # Lead factor
        layout.addWidget(QLabel("Lead factor"))
        self.spin_lead = QDoubleSpinBox()
        self.spin_lead.setRange(0.0, 10.0)
        self.spin_lead.setValue(self.config.aimbot.lead_factor)
        layout.addWidget(self.spin_lead)

        # Min area
        layout.addWidget(QLabel("Min area"))
        self.spin_minarea = QSpinBox()
        self.spin_minarea.setRange(0, 100000)
        self.spin_minarea.setValue(self.config.aimbot.min_area)
        layout.addWidget(self.spin_minarea)

        # Max area
        layout.addWidget(QLabel("Max area"))
        self.spin_maxarea = QSpinBox()
        self.spin_maxarea.setRange(0, 100000)
        self.spin_maxarea.setValue(self.config.aimbot.max_area)
        layout.addWidget(self.spin_maxarea)

        self.tabs.addTab(tab, "Aimbot")

        # Live updates
        self.chk_enabled.stateChanged.connect(self.update_aimbot_live)
        self.spin_lead.valueChanged.connect(self.update_aimbot_live)
        self.spin_minarea.valueChanged.connect(self.update_aimbot_live)
        self.spin_maxarea.valueChanged.connect(self.update_aimbot_live)

    def init_offset_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # X
        layout.addWidget(QLabel("Offset X"))
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-2000, 2000)
        self.spin_x.setValue(self.config.offset.x)
        layout.addWidget(self.spin_x)

        # Y
        layout.addWidget(QLabel("Offset Y"))
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-2000, 2000)
        self.spin_y.setValue(self.config.offset.y)
        layout.addWidget(self.spin_y)

        self.tabs.addTab(tab, "Offset")

        self.spin_x.valueChanged.connect(self.update_offset_live)
        self.spin_y.valueChanged.connect(self.update_offset_live)

    def init_sensitivity_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Smoothness"))
        self.spin_smooth = QDoubleSpinBox()
        self.spin_smooth.setRange(0.0, 1.0)
        self.spin_smooth.setSingleStep(0.01)
        self.spin_smooth.setValue(self.config.sensitivity.smoothness)
        layout.addWidget(self.spin_smooth)

        layout.addWidget(QLabel("Min sensitivity"))
        self.spin_minsens = QDoubleSpinBox()
        self.spin_minsens.setRange(0.0, 5.0)
        self.spin_minsens.setValue(self.config.sensitivity.min_sensitivity)
        layout.addWidget(self.spin_minsens)

        layout.addWidget(QLabel("Max sensitivity"))
        self.spin_maxsens = QDoubleSpinBox()
        self.spin_maxsens.setRange(0.0, 15.0)
        self.spin_maxsens.setValue(self.config.sensitivity.max_sensitivity)
        layout.addWidget(self.spin_maxsens)

        self.tabs.addTab(tab, "Sensitivity")

        self.spin_smooth.valueChanged.connect(self.update_sensitivity_live)
        self.spin_minsens.valueChanged.connect(self.update_sensitivity_live)
        self.spin_maxsens.valueChanged.connect(self.update_sensitivity_live)

    # --------------------------------------------------------------
    #     COLOR PICKER
    # --------------------------------------------------------------
    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_str = f"0x{color.red():02x}{color.green():02x}{color.blue():02x}"
            self.config.general.color = ColorHex(int(hex_str))
            self.btn_color.setText(f"Color: {hex_str}")

    # --------------------------------------------------------------
    #   LIVE UPDATE HANDLERS
    # --------------------------------------------------------------
    def update_general_live(self):
        self.config.general.debug_mode = self.chk_debug.isChecked()

    def update_aimbot_live(self):
        self.config.aimbot.enabled = self.chk_enabled.isChecked()
        self.config.aimbot.lead_factor = self.spin_lead.value()
        self.config.aimbot.min_area = self.spin_minarea.value()
        self.config.aimbot.max_area = self.spin_maxarea.value()

    def update_offset_live(self):
        self.config.offset.x = self.spin_x.value()
        self.config.offset.y = self.spin_y.value()

    def update_sensitivity_live(self):
        self.config.sensitivity.smoothness = self.spin_smooth.value()
        self.config.sensitivity.min_sensitivity = self.spin_minsens.value()
        self.config.sensitivity.max_sensitivity = self.spin_maxsens.value()

    # --------------------------------------------------------------
    #   ENGINE CONTROL
    # --------------------------------------------------------------
    def start_engine(self):
        if self.tracker_thread:
            return

        # Update config before starting
        self.config.general.target_win = self.input_target.text()
        self.config.general.fov = self.spin_fov.value()
        self.config.aimbot.tolerance = self.spin_tolerance.value()

        self.tracker_thread = TrackerThread(self.config)
        self.tracker_thread.started_successfully.connect(self.on_engine_started)
        self.tracker_thread.stopped.connect(self.on_engine_stopped)
        self.tracker_thread.start()

    def stop_engine(self):
        if self.tracker_thread:
            self.tracker_thread.stop()

    def on_engine_started(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def on_engine_stopped(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.tracker_thread = None

    # --------------------------------------------------------------
    #   CONFIG SYNC
    # --------------------------------------------------------------
    def sync_engine(self):
        if not self.tracker_thread:
            QMessageBox.warning(self, "Engine not running", "Start the engine first.")
            return

        # Apply unsafe values to config
        self.config.general.fov = self.spin_fov.value()
        self.config.aimbot.tolerance = self.spin_tolerance.value()
        self.config.general.target_win = self.input_target.text()

        ok = self.tracker_thread.sync_config()
        if ok:
            QMessageBox.information(self, "Synced", "Tracker updated successfully.")
        else:
            QMessageBox.critical(self, "Failed", "Tracker update failed.")

    # --------------------------------------------------------------
    #   SAVE CONFIG
    # --------------------------------------------------------------
    def save_config(self):
        self.config.save("config.yml")
        QMessageBox.information(self, "Saved", "Configuration saved.")
