from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.qt.frame_preview import build_preview_pixmap
from drb_inspection.ui.shell import DesktopShell


class MainScreenWidget(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, shell: DesktopShell):
        super().__init__()
        self.shell = shell
        self.header_card = QFrame()
        self.header_card.setObjectName("card")
        self.runtime_card = QFrame()
        self.runtime_card.setObjectName("card")
        self.settings_card = QFrame()
        self.settings_card.setObjectName("card")
        self.user_label = QLabel("")
        self.user_label.setObjectName("mutedLabel")
        self.role_label = QLabel("")
        self.role_label.setObjectName("mutedLabel")
        self.message_label = QLabel("")
        self.message_label.setObjectName("successMessageLabel")
        self.cycle_status_label = QLabel("")
        self.cycle_status_label.setObjectName("statusPill")
        self.camera_status_label = QLabel("")
        self.camera_status_label.setObjectName("mutedLabel")
        self.plc_status_label = QLabel("")
        self.plc_status_label.setObjectName("mutedLabel")
        self.preview_label = QLabel("")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_summary_label = QLabel("")
        self.preview_summary_label.setObjectName("mutedLabel")
        self.preview_summary_label.setWordWrap(True)
        self.task_results_view = QTextEdit()
        self.task_results_view.setReadOnly(True)
        self.product_combo = QComboBox()
        self.model_path_label = QLabel("")
        self.model_path_label.setObjectName("mutedLabel")
        self.plc_ip_edit = QLineEdit()
        self.plc_port_edit = QLineEdit()
        self.plc_protocol_combo = QComboBox()
        self.result_time_spin = QSpinBox()
        self.sleep_time_spin = QSpinBox()
        self.zoom_factor_spin = QDoubleSpinBox()
        self.offset_x_spin = QSpinBox()
        self.offset_y_spin = QSpinBox()
        self.image_width_spin = QSpinBox()
        self.image_height_spin = QSpinBox()
        self.grab_preview_button = QPushButton("Grab Preview")
        self.live_preview_button = QPushButton("Start Live Preview")
        self.live_preview_button.setCheckable(True)
        self.save_button = QPushButton("Save Settings")
        self.refresh_button = QPushButton("Refresh")
        self.run_cycle_button = QPushButton("Run Inspection Cycle")
        self.logout_button = QPushButton("Logout")
        self.grab_preview_button.setObjectName("primaryButton")
        self.save_button.setObjectName("primaryButton")
        self.run_cycle_button.setObjectName("successButton")
        self.logout_button.setObjectName("dangerButton")
        self.live_timer = QTimer(self)
        self.live_timer.setInterval(1000)
        self._build_ui()
        self._connect_events()

    def render(self) -> None:
        state = self.shell.main_state or self.shell.refresh_main()
        self.user_label.setText(f"User: {state.current_user_name or '<none>'}")
        self.role_label.setText(f"Role: {state.current_role}")
        self.message_label.setText(state.message)
        self.cycle_status_label.setText((state.last_cycle_status or "<no cycle>").upper())
        self.camera_status_label.setText(
            f"Camera: {'Connected' if state.camera_connected else 'Disconnected'}"
            f" | vendor: {state.camera_vendor or 'demo'}"
        )
        plc_result = state.plc_last_result or "<none>"
        self.plc_status_label.setText(
            f"PLC: {'Connected' if state.plc_connected else 'Disconnected'}"
            f" | vendor: {state.plc_vendor or 'demo'}"
            f" | protocol: {state.plc_protocol or 'demo'}"
            f" | last result: {plc_result}"
        )
        self.model_path_label.setText(state.model_path or "<no model>")
        self.preview_summary_label.setText(state.preview_summary or "No preview captured.")
        self.task_results_view.setPlainText(
            "\n".join(state.task_summaries) if state.task_summaries else "No inspection cycle executed yet."
        )
        self.preview_label.setPixmap(build_preview_pixmap(
            state.preview_frame.frame if state.preview_frame is not None else None,
            state.preview_summary or "No preview captured.",
        ))

        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        self.product_combo.addItems(state.available_products)
        if state.selected_product_name:
            index = self.product_combo.findText(state.selected_product_name)
            if index >= 0:
                self.product_combo.setCurrentIndex(index)
        self.product_combo.blockSignals(False)

        self.plc_ip_edit.setText(state.plc_ip)
        self.plc_port_edit.setText(state.plc_port)
        self.plc_protocol_combo.setCurrentText(state.plc_protocol or "modbus_tcp")
        self.result_time_spin.setValue(int(state.result_time or 0))
        self.sleep_time_spin.setValue(int(state.sleep_time or 0))
        self.zoom_factor_spin.setValue(float(state.zoom_factor or 0.0))
        self.offset_x_spin.setValue(state.offset_x)
        self.offset_y_spin.setValue(state.offset_y)
        self.image_width_spin.setValue(state.image_width)
        self.image_height_spin.setValue(state.image_height)

        profile = state.access_profile
        self.product_combo.setEnabled(profile.can_update_product_list or profile.can_configure_ai or profile.can_run_cycle)
        self.save_button.setEnabled(
            profile.can_change_result_time
            or profile.can_change_sleep_time
            or profile.can_configure_hardware
        )
        self.grab_preview_button.setEnabled(profile.can_grab or profile.can_live_camera or profile.can_run_cycle)
        self.live_preview_button.setEnabled(profile.can_live_camera or profile.can_run_cycle)
        self.run_cycle_button.setEnabled(bool(state.selected_product_name) and profile.can_run_cycle)

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)
        title = QLabel("Inspection Main Screen")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Runtime shell for product, PLC and inspection-cycle orchestration.")
        subtitle.setObjectName("screenSubtitle")

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(8)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(self.user_label)
        header_layout.addWidget(self.role_label)
        self.header_card.setLayout(header_layout)
        root.addWidget(self.header_card)

        body = QHBoxLayout()
        body.setSpacing(18)

        runtime_layout = QVBoxLayout()
        runtime_layout.setContentsMargins(24, 20, 24, 20)
        runtime_layout.setSpacing(12)
        runtime_title = QLabel("Runtime")
        runtime_title.setObjectName("sectionTitle")
        runtime_layout.addWidget(runtime_title)
        runtime_layout.addWidget(self.camera_status_label)
        runtime_layout.addWidget(self.plc_status_label)
        runtime_layout.addWidget(self.cycle_status_label)
        runtime_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        runtime_layout.addWidget(self.preview_summary_label)

        preview_actions = QHBoxLayout()
        preview_actions.setSpacing(10)
        preview_actions.addWidget(self.grab_preview_button)
        preview_actions.addWidget(self.live_preview_button)
        runtime_layout.addLayout(preview_actions)

        task_title = QLabel("Inspection Task Results")
        task_title.setObjectName("sectionTitle")
        runtime_layout.addWidget(task_title)
        runtime_layout.addWidget(self.task_results_view)
        self.runtime_card.setLayout(runtime_layout)
        body.addWidget(self.runtime_card, 3)

        form = QFormLayout()
        form.setSpacing(14)
        form.addRow("Product", self.product_combo)
        form.addRow("Model", self.model_path_label)
        form.addRow("PLC IP", self.plc_ip_edit)
        form.addRow("PLC Port", self.plc_port_edit)
        form.addRow("PLC Protocol", self.plc_protocol_combo)
        form.addRow("Result Time", self.result_time_spin)
        form.addRow("Sleep Time", self.sleep_time_spin)
        form.addRow("Zoom", self.zoom_factor_spin)
        form.addRow("Offset X", self.offset_x_spin)
        form.addRow("Offset Y", self.offset_y_spin)
        form.addRow("Image Width", self.image_width_spin)
        form.addRow("Image Height", self.image_height_spin)
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(24, 20, 24, 20)
        settings_layout.setSpacing(12)
        settings_title = QLabel("Session Settings")
        settings_title.setObjectName("sectionTitle")
        settings_layout.addWidget(settings_title)
        settings_layout.addLayout(form)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.run_cycle_button)
        actions.addWidget(self.logout_button)
        settings_layout.addLayout(actions)
        self.settings_card.setLayout(settings_layout)
        body.addWidget(self.settings_card, 2)

        root.addLayout(body)
        root.addWidget(self.message_label)
        root.addStretch(1)
        self.setLayout(root)

        self.result_time_spin.setMaximum(100000)
        self.sleep_time_spin.setMaximum(100000)
        self.zoom_factor_spin.setMaximum(10.0)
        self.zoom_factor_spin.setSingleStep(0.1)
        self.offset_x_spin.setMaximum(100000)
        self.offset_y_spin.setMaximum(100000)
        self.image_width_spin.setMaximum(100000)
        self.image_height_spin.setMaximum(100000)
        self.plc_protocol_combo.addItems(["modbus_tcp", "modbus_rtu", "slmp"])
        self.preview_label.setMinimumSize(520, 300)
        self.task_results_view.setMinimumHeight(180)

    def _connect_events(self) -> None:
        self.product_combo.currentTextChanged.connect(self._on_product_changed)
        self.grab_preview_button.clicked.connect(self._on_grab_preview)
        self.live_preview_button.toggled.connect(self._on_toggle_live_preview)
        self.save_button.clicked.connect(self._on_save)
        self.refresh_button.clicked.connect(self._on_refresh)
        self.run_cycle_button.clicked.connect(self._on_run_cycle)
        self.logout_button.clicked.connect(self._on_logout)
        self.live_timer.timeout.connect(self._on_live_tick)

    def _on_product_changed(self, product_name: str) -> None:
        if not product_name:
            return
        self.shell.main_state = self.shell.main_presenter.select_current_product(product_name)
        self.render()

    def _on_save(self) -> None:
        self.shell.main_state = self.shell.main_presenter.update_session_settings(
            plc_ip=self.plc_ip_edit.text().strip(),
            plc_port=self.plc_port_edit.text().strip(),
            plc_protocol=self.plc_protocol_combo.currentText().strip(),
            result_time=self.result_time_spin.value(),
            sleep_time=self.sleep_time_spin.value(),
            zoom_factor=self.zoom_factor_spin.value(),
            offset_x=self.offset_x_spin.value(),
            offset_y=self.offset_y_spin.value(),
            image_width=self.image_width_spin.value(),
            image_height=self.image_height_spin.value(),
        )
        self.render()

    def _on_refresh(self) -> None:
        self.shell.refresh_main()
        self.render()

    def _on_logout(self) -> None:
        self._stop_live_preview()
        self.shell.logout()
        self.navigate.emit(ScreenId.LOGIN.value)

    def _on_run_cycle(self) -> None:
        self.shell.main_state = self.shell.main_presenter.run_cycle()
        self.render()

    def _on_grab_preview(self) -> None:
        self.shell.main_state = self.shell.main_presenter.grab_preview_frame()
        self.render()

    def _on_toggle_live_preview(self, checked: bool) -> None:
        if checked:
            self.live_preview_button.setText("Stop Live Preview")
            self.live_timer.start()
            self._on_grab_preview()
            return
        self._stop_live_preview()

    def _on_live_tick(self) -> None:
        self._on_grab_preview()

    def _stop_live_preview(self) -> None:
        self.live_timer.stop()
        self.live_preview_button.blockSignals(True)
        self.live_preview_button.setChecked(False)
        self.live_preview_button.setText("Start Live Preview")
        self.live_preview_button.blockSignals(False)
