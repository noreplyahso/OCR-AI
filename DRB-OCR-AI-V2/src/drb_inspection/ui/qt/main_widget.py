from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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
        self.runtime_mode_label = QLabel("Mode: MANUAL")
        self.runtime_mode_label.setObjectName("mutedLabel")
        self.inspection_mode_label = QLabel("AI checking: disabled")
        self.inspection_mode_label.setObjectName("mutedLabel")
        self.recording_mode_label = QLabel("Result recording: disabled")
        self.recording_mode_label.setObjectName("mutedLabel")
        self.plc_signal_label = QLabel("PLC signals: not polled")
        self.plc_signal_label.setObjectName("mutedLabel")
        self.idle_shutdown_label = QLabel("Idle shutdown: not armed")
        self.idle_shutdown_label.setObjectName("mutedLabel")
        self.counter_summary_label = QLabel("Counter: 0 | Batch: 0 | Quantity: 0")
        self.counter_summary_label.setObjectName("mutedLabel")
        self.result_summary_label = QLabel("Result: <none> | OK: 0 | NG: 0")
        self.result_summary_label.setObjectName("mutedLabel")
        self.cycle_meta_label = QLabel("Cycle: trigger=<none> | duration=0.0 ms")
        self.cycle_meta_label.setObjectName("mutedLabel")
        self.artifact_summary_label = QLabel("Artifacts: not saved")
        self.artifact_summary_label.setObjectName("mutedLabel")
        self.artifact_summary_label.setWordWrap(True)
        self.preview_label = QLabel("")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_summary_label = QLabel("")
        self.preview_summary_label.setObjectName("mutedLabel")
        self.preview_summary_label.setWordWrap(True)
        self.roi_summary_label = QLabel("")
        self.roi_summary_label.setObjectName("mutedLabel")
        self.roi_summary_label.setWordWrap(True)
        self.task_results_view = QTextEdit()
        self.task_results_view.setReadOnly(True)
        self.history_results_view = QTextEdit()
        self.history_results_view.setReadOnly(True)
        self.catalog_path_edit = QLineEdit()
        self.product_combo = QComboBox()
        self.model_path_edit = QLineEdit()
        self.browse_model_button = QPushButton("Browse Model")
        self.default_number_spin = QSpinBox()
        self.exposure_spin = QSpinBox()
        self.threshold_accept_spin = QDoubleSpinBox()
        self.threshold_mns_spin = QDoubleSpinBox()
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
        self.roi_to_move_spin = QSpinBox()
        self.move_all_roi_checkbox = QCheckBox("Move all")
        self.move_roi_left_button = QPushButton("ROI Left")
        self.move_roi_right_button = QPushButton("ROI Right")
        self.move_roi_up_button = QPushButton("ROI Up")
        self.move_roi_down_button = QPushButton("ROI Down")
        self.manual_mode_button = QPushButton("Manual Mode")
        self.auto_mode_button = QPushButton("Auto Mode")
        self.ai_checking_button = QPushButton("Enable AI Checking")
        self.recording_button = QPushButton("Enable Result Recording")
        self.poll_plc_button = QPushButton("Poll PLC Once")
        self.connect_camera_button = QPushButton("Connect Camera")
        self.disconnect_camera_button = QPushButton("Disconnect Camera")
        self.connect_plc_button = QPushButton("Connect PLC")
        self.disconnect_plc_button = QPushButton("Disconnect PLC")
        self.shutdown_runtime_button = QPushButton("Shutdown Runtime")
        self.grab_preview_button = QPushButton("Grab Preview")
        self.live_preview_button = QPushButton("Start Live Preview")
        self.live_preview_button.setCheckable(True)
        self.browse_catalog_button = QPushButton("Browse Catalog")
        self.import_catalog_button = QPushButton("Import Catalog")
        self.save_product_button = QPushButton("Save Product")
        self.save_button = QPushButton("Save Settings")
        self.refresh_button = QPushButton("Refresh")
        self.reset_counter_button = QPushButton("Reset Counters")
        self.run_cycle_button = QPushButton("Run Inspection Cycle")
        self.logout_button = QPushButton("Logout")
        self.grab_preview_button.setObjectName("primaryButton")
        self.import_catalog_button.setObjectName("primaryButton")
        self.save_product_button.setObjectName("primaryButton")
        self.save_button.setObjectName("primaryButton")
        self.run_cycle_button.setObjectName("successButton")
        self.logout_button.setObjectName("dangerButton")
        self.shutdown_runtime_button.setObjectName("dangerButton")
        self.live_timer = QTimer(self)
        self.live_timer.setInterval(1000)
        self.plc_poll_timer = QTimer(self)
        self.plc_poll_timer.setInterval(250)
        self.result_hold_timer = QTimer(self)
        self.result_hold_timer.setSingleShot(True)
        self._live_resume_after_hold = False
        self.idle_shutdown_timer = QTimer(self)
        self.idle_shutdown_timer.setSingleShot(True)
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
        self.runtime_mode_label.setText(
            f"Mode: {'AUTO' if state.auto_mode_enabled else 'MANUAL'}"
        )
        self.inspection_mode_label.setText(
            f"AI checking: {'enabled' if state.inspection_enabled else 'disabled'}"
        )
        self.recording_mode_label.setText(
            f"Result recording: {'enabled' if state.recording_enabled else 'disabled'}"
        )
        self.manual_mode_button.setText("Manual ON" if not state.auto_mode_enabled else "Manual Mode")
        self.auto_mode_button.setText("Auto ON" if state.auto_mode_enabled else "Auto Mode")
        self.ai_checking_button.setText(
            "Disable AI Checking" if state.inspection_enabled else "Enable AI Checking"
        )
        self.recording_button.setText(
            "Disable Result Recording" if state.recording_enabled else "Enable Result Recording"
        )
        self.plc_signal_label.setText(state.plc_signal_summary or "PLC signals: not polled")
        self.idle_shutdown_label.setText(self._build_idle_shutdown_label(state))
        self.counter_summary_label.setText(
            "Counter:"
            f" {state.inspection_counter_value}"
            f" | Batch: {state.inspection_batch_value}"
            f" | Quantity: {state.last_quantity}"
        )
        self.result_summary_label.setText(
            "Result:"
            f" {state.last_result_label or '<none>'}"
            f" | OK: {state.last_ok_count}"
            f" | NG: {state.last_ng_count}"
        )
        self.cycle_meta_label.setText(
            "Cycle:"
            f" trigger={state.last_trigger_source or '<none>'}"
            f" | duration={state.last_cycle_duration_ms:.1f} ms"
        )
        self.artifact_summary_label.setText(state.artifact_summary or "Artifacts: not saved")
        self.model_path_edit.setText(state.model_path)
        self.default_number_spin.setValue(int(state.default_number or 0))
        self.exposure_spin.setValue(int(state.exposure or 0))
        self.threshold_accept_spin.setValue(float(state.threshold_accept or 0.0))
        self.threshold_mns_spin.setValue(float(state.threshold_mns or 0.0))
        self.preview_summary_label.setText(state.preview_summary or "No preview captured.")
        self.roi_summary_label.setText(state.roi_summary or "ROIs: none")
        self.task_results_view.setPlainText(
            "\n".join(state.task_summaries) if state.task_summaries else "No inspection cycle executed yet."
        )
        self.history_results_view.setPlainText(
            "\n".join(state.recent_history_summaries)
            if state.recent_history_summaries
            else "No cycle history recorded yet."
        )
        self.preview_label.setPixmap(build_preview_pixmap(
            state.preview_frame.frame if state.preview_frame is not None else None,
            state.preview_summary or "No preview captured.",
            roi_rects=state.roi_rects,
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
        self.roi_to_move_spin.setMaximum(max(1, len(state.roi_points) or 5))

        profile = state.access_profile
        self.catalog_path_edit.setEnabled(profile.can_update_product_list)
        self.browse_catalog_button.setEnabled(profile.can_update_product_list)
        self.import_catalog_button.setEnabled(profile.can_update_product_list)
        self.product_combo.setEnabled(profile.can_update_product_list or profile.can_configure_ai or profile.can_run_cycle)
        self.save_product_button.setEnabled(profile.can_configure_ai or profile.can_update_product_list)
        self.browse_model_button.setEnabled(profile.can_configure_ai or profile.can_update_product_list)
        self.model_path_edit.setEnabled(profile.can_configure_ai or profile.can_update_product_list)
        self.default_number_spin.setEnabled(profile.can_configure_ai or profile.can_update_product_list)
        self.exposure_spin.setEnabled(profile.can_configure_hardware or profile.can_configure_ai)
        self.threshold_accept_spin.setEnabled(profile.can_configure_ai)
        self.threshold_mns_spin.setEnabled(profile.can_configure_ai)
        can_move_roi = profile.can_configure_hardware or profile.can_configure_ai
        self.roi_to_move_spin.setEnabled(can_move_roi)
        self.move_all_roi_checkbox.setEnabled(can_move_roi)
        self.move_roi_left_button.setEnabled(can_move_roi)
        self.move_roi_right_button.setEnabled(can_move_roi)
        self.move_roi_up_button.setEnabled(can_move_roi)
        self.move_roi_down_button.setEnabled(can_move_roi)
        can_control_hardware = profile.can_configure_hardware
        self.connect_camera_button.setEnabled(can_control_hardware and not state.camera_connected)
        self.disconnect_camera_button.setEnabled(can_control_hardware and state.camera_connected)
        self.connect_plc_button.setEnabled(can_control_hardware and not state.plc_connected)
        self.disconnect_plc_button.setEnabled(can_control_hardware and state.plc_connected)
        self.shutdown_runtime_button.setEnabled(can_control_hardware)
        self.manual_mode_button.setEnabled(profile.can_manual_mode)
        self.auto_mode_button.setEnabled(profile.can_auto_mode)
        self.ai_checking_button.setEnabled(profile.can_real_time or profile.can_run_cycle)
        self.recording_button.setEnabled(profile.can_run_cycle)
        self.poll_plc_button.setEnabled(profile.can_auto_mode or profile.can_manual_mode or profile.can_run_cycle)
        self.reset_counter_button.setEnabled(profile.can_run_cycle)
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
        runtime_layout.addWidget(self.runtime_mode_label)
        runtime_layout.addWidget(self.inspection_mode_label)
        runtime_layout.addWidget(self.recording_mode_label)
        runtime_layout.addWidget(self.plc_signal_label)
        runtime_layout.addWidget(self.idle_shutdown_label)
        runtime_layout.addWidget(self.counter_summary_label)
        runtime_layout.addWidget(self.result_summary_label)
        runtime_layout.addWidget(self.cycle_meta_label)
        runtime_layout.addWidget(self.artifact_summary_label)
        runtime_layout.addWidget(self.cycle_status_label)
        runtime_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        runtime_layout.addWidget(self.preview_summary_label)
        runtime_layout.addWidget(self.roi_summary_label)

        preview_actions = QHBoxLayout()
        preview_actions.setSpacing(10)
        preview_actions.addWidget(self.grab_preview_button)
        preview_actions.addWidget(self.live_preview_button)
        runtime_layout.addLayout(preview_actions)
        plc_actions = QHBoxLayout()
        plc_actions.setSpacing(10)
        plc_actions.addWidget(self.manual_mode_button)
        plc_actions.addWidget(self.auto_mode_button)
        plc_actions.addWidget(self.ai_checking_button)
        plc_actions.addWidget(self.recording_button)
        plc_actions.addWidget(self.poll_plc_button)
        runtime_layout.addLayout(plc_actions)
        hardware_actions = QHBoxLayout()
        hardware_actions.setSpacing(10)
        hardware_actions.addWidget(self.connect_camera_button)
        hardware_actions.addWidget(self.disconnect_camera_button)
        hardware_actions.addWidget(self.connect_plc_button)
        hardware_actions.addWidget(self.disconnect_plc_button)
        hardware_actions.addWidget(self.shutdown_runtime_button)
        runtime_layout.addLayout(hardware_actions)

        task_title = QLabel("Inspection Task Results")
        task_title.setObjectName("sectionTitle")
        runtime_layout.addWidget(task_title)
        runtime_layout.addWidget(self.task_results_view)
        history_title = QLabel("Recent Cycle History")
        history_title.setObjectName("sectionTitle")
        runtime_layout.addWidget(history_title)
        runtime_layout.addWidget(self.history_results_view)
        self.runtime_card.setLayout(runtime_layout)
        body.addWidget(self.runtime_card, 3)

        form = QFormLayout()
        form.setSpacing(14)
        catalog_row = QHBoxLayout()
        catalog_row.setSpacing(8)
        catalog_row.addWidget(self.catalog_path_edit)
        catalog_row.addWidget(self.browse_catalog_button)
        catalog_row.addWidget(self.import_catalog_button)
        form.addRow("Catalog", catalog_row)
        form.addRow("Product", self.product_combo)
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        model_row.addWidget(self.model_path_edit)
        model_row.addWidget(self.browse_model_button)
        form.addRow("Model", model_row)
        form.addRow("Default", self.default_number_spin)
        form.addRow("Exposure", self.exposure_spin)
        form.addRow("Accept Threshold", self.threshold_accept_spin)
        form.addRow("MNS Threshold", self.threshold_mns_spin)
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
        roi_target_row = QHBoxLayout()
        roi_target_row.setSpacing(8)
        roi_target_row.addWidget(self.roi_to_move_spin)
        roi_target_row.addWidget(self.move_all_roi_checkbox)
        form.addRow("ROI Target", roi_target_row)
        roi_move_row = QHBoxLayout()
        roi_move_row.setSpacing(8)
        roi_move_row.addWidget(self.move_roi_left_button)
        roi_move_row.addWidget(self.move_roi_right_button)
        roi_move_row.addWidget(self.move_roi_up_button)
        roi_move_row.addWidget(self.move_roi_down_button)
        form.addRow("ROI Move", roi_move_row)
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
        actions.addWidget(self.reset_counter_button)
        actions.addWidget(self.save_product_button)
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
        self.default_number_spin.setMaximum(100000)
        self.exposure_spin.setMaximum(1000000)
        self.threshold_accept_spin.setMaximum(1.0)
        self.threshold_accept_spin.setSingleStep(0.1)
        self.threshold_mns_spin.setMaximum(1.0)
        self.threshold_mns_spin.setSingleStep(0.1)
        self.zoom_factor_spin.setMaximum(10.0)
        self.zoom_factor_spin.setSingleStep(0.1)
        self.offset_x_spin.setMaximum(100000)
        self.offset_y_spin.setMaximum(100000)
        self.image_width_spin.setMaximum(100000)
        self.image_height_spin.setMaximum(100000)
        self.roi_to_move_spin.setRange(1, 5)
        self.plc_protocol_combo.addItems(["modbus_tcp", "modbus_rtu", "slmp"])
        self.preview_label.setMinimumSize(520, 300)
        self.task_results_view.setMinimumHeight(180)
        self.history_results_view.setMinimumHeight(140)

    def _connect_events(self) -> None:
        self.product_combo.currentTextChanged.connect(self._on_product_changed)
        self.grab_preview_button.clicked.connect(self._on_grab_preview)
        self.live_preview_button.toggled.connect(self._on_toggle_live_preview)
        self.browse_catalog_button.clicked.connect(self._on_browse_catalog)
        self.import_catalog_button.clicked.connect(self._on_import_catalog)
        self.browse_model_button.clicked.connect(self._on_browse_model)
        self.save_product_button.clicked.connect(self._on_save_product)
        self.save_button.clicked.connect(self._on_save)
        self.move_roi_left_button.clicked.connect(lambda: self._on_move_roi("left"))
        self.move_roi_right_button.clicked.connect(lambda: self._on_move_roi("right"))
        self.move_roi_up_button.clicked.connect(lambda: self._on_move_roi("up"))
        self.move_roi_down_button.clicked.connect(lambda: self._on_move_roi("down"))
        self.manual_mode_button.clicked.connect(self._on_manual_mode)
        self.auto_mode_button.clicked.connect(self._on_auto_mode)
        self.ai_checking_button.clicked.connect(self._on_toggle_ai_checking)
        self.recording_button.clicked.connect(self._on_toggle_recording)
        self.poll_plc_button.clicked.connect(self._on_poll_plc_once)
        self.connect_camera_button.clicked.connect(self._on_connect_camera)
        self.disconnect_camera_button.clicked.connect(self._on_disconnect_camera)
        self.connect_plc_button.clicked.connect(self._on_connect_plc)
        self.disconnect_plc_button.clicked.connect(self._on_disconnect_plc)
        self.shutdown_runtime_button.clicked.connect(self._on_shutdown_runtime)
        self.refresh_button.clicked.connect(self._on_refresh)
        self.reset_counter_button.clicked.connect(self._on_reset_counters)
        self.run_cycle_button.clicked.connect(self._on_run_cycle)
        self.logout_button.clicked.connect(self._on_logout)
        self.live_timer.timeout.connect(self._on_live_tick)
        self.plc_poll_timer.timeout.connect(self._on_plc_poll_tick)
        self.result_hold_timer.timeout.connect(self._on_result_hold_timeout)
        self.idle_shutdown_timer.timeout.connect(self._on_idle_shutdown_timeout)

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

    def _on_save_product(self) -> None:
        self.shell.main_state = self.shell.main_presenter.update_product_settings(
            product_name=self.product_combo.currentText().strip(),
            model_path=self.model_path_edit.text().strip(),
            default_number=self.default_number_spin.value(),
            exposure=self.exposure_spin.value(),
            threshold_accept=self.threshold_accept_spin.value(),
            threshold_mns=self.threshold_mns_spin.value(),
        )
        self.render()

    def _on_browse_catalog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select product catalog",
            str(Path.cwd()),
            "Catalog files (*.xlsx *.xlsm *.csv *.json *.yaml *.yml);;All Files (*)",
        )
        if path:
            self.catalog_path_edit.setText(path)

    def _on_import_catalog(self) -> None:
        self.shell.main_state = self.shell.main_presenter.import_product_catalog_from_file(
            self.catalog_path_edit.text().strip()
        )
        self.render()

    def _on_browse_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select model",
            str(Path.cwd()),
            "Model files (*.pt *.onnx *.engine);;All Files (*)",
        )
        if path:
            self.model_path_edit.setText(path)

    def _on_refresh(self) -> None:
        self.shell.refresh_main()
        self.render()

    def _on_logout(self) -> None:
        self.result_hold_timer.stop()
        self._live_resume_after_hold = False
        self.idle_shutdown_timer.stop()
        self.plc_poll_timer.stop()
        self._stop_live_preview()
        self.shell.logout()
        self.navigate.emit(ScreenId.LOGIN.value)

    def _on_run_cycle(self) -> None:
        self._begin_result_hold_if_needed()
        self.shell.main_state = self.shell.main_presenter.run_cycle()
        self._arm_result_hold_resume()
        self.render()

    def _on_reset_counters(self) -> None:
        self.shell.main_state = self.shell.main_presenter.reset_cycle_counters()
        self.render()

    def _on_grab_preview(self) -> None:
        self.idle_shutdown_timer.stop()
        self.shell.main_state = self.shell.main_presenter.grab_preview_frame()
        self.render()

    def _on_move_roi(self, direction: str) -> None:
        previous_state = self.shell.main_state or self.shell.refresh_main()
        updated_state = self.shell.main_presenter.move_roi(
            direction=direction,
            roi_index=self.roi_to_move_spin.value(),
            move_all=self.move_all_roi_checkbox.isChecked(),
        )
        if previous_state.preview_frame is not None and updated_state.preview_frame is None:
            updated_state = replace(
                updated_state,
                preview_frame=previous_state.preview_frame,
                preview_summary=previous_state.preview_summary,
                last_cycle_status=previous_state.last_cycle_status,
                plc_last_result=previous_state.plc_last_result,
                task_summaries=previous_state.task_summaries,
            )
        self.shell.main_state = updated_state
        self.render()

    def _on_manual_mode(self) -> None:
        self.plc_poll_timer.stop()
        self.idle_shutdown_timer.stop()
        self.shell.main_state = self.shell.main_presenter.set_manual_mode()
        self.render()

    def _on_auto_mode(self) -> None:
        self.idle_shutdown_timer.stop()
        self.plc_poll_timer.start()
        self.shell.main_state = self.shell.main_presenter.set_auto_mode()
        self.render()

    def _on_toggle_ai_checking(self) -> None:
        self.shell.main_state = self.shell.main_presenter.toggle_inspection_enabled()
        self.render()

    def _on_toggle_recording(self) -> None:
        self.shell.main_state = self.shell.main_presenter.toggle_recording_enabled()
        self.render()

    def _on_poll_plc_once(self) -> None:
        self._begin_result_hold_if_needed(for_plc=True)
        self.shell.main_state = self.shell.main_presenter.poll_plc_once()
        if self.shell.main_state.plc_poll_action == "stop":
            self._stop_live_preview()
            self._arm_idle_shutdown()
        elif self.shell.main_state.plc_poll_action == "start" and not self.live_preview_button.isChecked():
            self.idle_shutdown_timer.stop()
            self.live_preview_button.setChecked(True)
        elif self.shell.main_state.plc_poll_action == "grab":
            self.idle_shutdown_timer.stop()
        if self.shell.main_state.plc_cycle_triggered:
            self._arm_result_hold_resume()
        self.render()

    def _on_plc_poll_tick(self) -> None:
        self._on_poll_plc_once()

    def _on_connect_camera(self) -> None:
        self.shell.main_state = self.shell.main_presenter.connect_camera_hardware()
        self.render()

    def _on_disconnect_camera(self) -> None:
        self._stop_live_preview()
        self.shell.main_state = self.shell.main_presenter.disconnect_camera_hardware()
        self.render()

    def _on_connect_plc(self) -> None:
        self.shell.main_state = self.shell.main_presenter.connect_plc_hardware()
        self.render()

    def _on_disconnect_plc(self) -> None:
        self.idle_shutdown_timer.stop()
        self.plc_poll_timer.stop()
        self.shell.main_state = self.shell.main_presenter.disconnect_plc_hardware()
        self.render()

    def _on_shutdown_runtime(self) -> None:
        self.idle_shutdown_timer.stop()
        self.plc_poll_timer.stop()
        self._stop_live_preview()
        self.shell.main_state = self.shell.main_presenter.shutdown_runtime_hardware()
        self.render()

    def _on_idle_shutdown_timeout(self) -> None:
        self._on_shutdown_runtime()

    def _on_result_hold_timeout(self) -> None:
        if not self._live_resume_after_hold:
            return
        self._live_resume_after_hold = False
        if not self.live_preview_button.isChecked():
            return
        self.live_preview_button.setText("Stop Live Preview")
        self.live_timer.start()
        self._on_grab_preview()

    def _arm_idle_shutdown(self) -> None:
        current_state = self.shell.main_state or self.shell.refresh_main()
        sleep_minutes = max(0, int(current_state.sleep_time or 0))
        if sleep_minutes <= 0:
            return
        self.idle_shutdown_timer.start(sleep_minutes * 60000)

    def _begin_result_hold_if_needed(self, *, for_plc: bool = False) -> None:
        current_state = self.shell.main_state or self.shell.refresh_main()
        if for_plc and not current_state.inspection_enabled:
            self._live_resume_after_hold = False
            return
        if not self.live_preview_button.isChecked():
            self._live_resume_after_hold = False
            return
        self._live_resume_after_hold = True
        self.live_timer.stop()
        self.live_preview_button.setText("Result Hold")

    def _arm_result_hold_resume(self) -> None:
        if not self._live_resume_after_hold:
            return
        current_state = self.shell.main_state or self.shell.refresh_main()
        result_seconds = max(0, int(current_state.result_time or 0))
        if result_seconds <= 0:
            self._on_result_hold_timeout()
            return
        self.result_hold_timer.start(result_seconds * 1000)

    def _build_idle_shutdown_label(self, state) -> str:
        if not self.idle_shutdown_timer.isActive():
            return "Idle shutdown: not armed"
        minutes = max(0, int(state.sleep_time or 0))
        return f"Idle shutdown: armed ({minutes} min)"

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
        self.result_hold_timer.stop()
        self._live_resume_after_hold = False
        self.live_timer.stop()
        self.live_preview_button.blockSignals(True)
        self.live_preview_button.setChecked(False)
        self.live_preview_button.setText("Start Live Preview")
        self.live_preview_button.blockSignals(False)
