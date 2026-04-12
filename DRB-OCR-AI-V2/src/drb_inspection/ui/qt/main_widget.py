from __future__ import annotations

import traceback
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QDateTime, QProcess, QPropertyAnimation, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsScene,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from PyQt5.uic import loadUi

from drb_inspection.app.settings import resolve_app_storage_root_dir
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.qt.frame_preview import build_preview_pixmap
from drb_inspection.ui.shell import DesktopShell


BUTTON_STYLESHEET_OFF = """
QPushButton {
    background-color: #A6CAEE;
    border: 2px solid black;
    border-radius: 12px;
    padding: 10px 10px;
}
QPushButton:hover {
    background-color: qlineargradient(
        spread:pad,
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #738B95,
        stop:1 #BAE5F5
    );
}
QPushButton:pressed {
    background-color: qlineargradient(
        spread:pad,
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #BAE5F5,
        stop:1 #738B95
    );
    padding-top: 6px;
}
"""

BUTTON_STYLESHEET_ON = """
QPushButton {
    border: 2px solid black;
    border-radius: 12px;
    padding: 10px 10px;
    background-color: qlineargradient(
        spread:pad,
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #738B95,
        stop:1 #BAE5F5
    );
}
"""

RESULT_STYLE_OK = """
QLabel {
    background-color: rgb(74, 212, 90);
    color: rgb(14,114,190);
    border-radius: 7px;
}
"""

RESULT_STYLE_FAIL = """
QLabel {
    background-color: red;
    color: rgb(14,114,190);
    border-radius: 7px;
}
"""

RESULT_STYLE_CHECKING = """
QLabel {
    font: 45pt;
    background-color: yellow;
    color: rgb(14,114,190);
    border-radius: 7px;
}
"""

RESULT_STYLE_IDLE = """
QLabel {
    background-color: rgb(255, 193, 7);
    color: rgb(14,114,190);
    border-radius: 7px;
}
"""


class MainScreenWidget(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, shell: DesktopShell):
        super().__init__()
        self.shell = shell
        self._ui_window = QMainWindow()
        loadUi(str(self._asset_path("form_UI", "screenMain.ui")), self._ui_window)

        self._menu_bar = getattr(self._ui_window, "menuBar", None)
        if not isinstance(self._menu_bar, QMenuBar):
            self._menu_bar = self._ui_window.findChild(QMenuBar, "menuBar")
        self._status_bar = getattr(self._ui_window, "statusBar", None)
        if not isinstance(self._status_bar, QStatusBar):
            self._status_bar = self._ui_window.findChild(QStatusBar, "statusBar")
        self._central_widget = self._ui_window.centralWidget()
        if self._menu_bar is not None:
            self._menu_bar.setParent(self)
        if self._status_bar is not None:
            self._status_bar.setParent(self)
        self._central_widget.setParent(self)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        if self._menu_bar is not None:
            root_layout.addWidget(self._menu_bar)
        root_layout.addWidget(self._central_widget, 1)
        if self._status_bar is not None:
            root_layout.addWidget(self._status_bar)
        self.setLayout(root_layout)

        self._bind_ui_attrs(
            "graphics_view_reference",
            "checkbox_show_ROI",
            "spinbox_ROI_to_move",
            "combobox_zoom_factor",
            "combobox_acceptance_threshold",
            "combobox_mns_threshold",
            "comboBox_PLC_protocol",
            "action_logout",
            "action_load_model",
            "action_update_product_list",
            "action_open_training_screen",
            "action_select_path_save_image",
            "button_exit",
            "button_grab",
            "button_live_camera",
            "button_real_time",
            "button_auto",
            "button_manual",
            "button_record",
            "button_connect_camera",
            "button_disconnect_camera",
            "button_connect_PLC",
            "button_disconnect_PLC",
            "button_reset_counter",
            "button_toggle_setting",
            "button_on_save_default",
            "button_save_result_time",
            "button_save_sleep_time",
            "button_save_zoom",
            "button_save_PLCIP",
            "button_save_camera",
            "button_save_AI_config",
            "button_move_ROI_left",
            "button_move_ROI_right",
            "button_move_ROI_up",
            "button_move_ROI_down",
            "button_authentication",
            "button_report",
            "combobox_product",
            "label_current_user",
            "label_product",
            "current_model_path",
            "spinbox_default_value",
            "spinbox_exposure_time",
            "spinbox_result_time",
            "spinbox_sleep_time",
            "spinbox_offset_x",
            "spinbox_offset_y",
            "spinbox_image_width",
            "spinbox_image_height",
            "line_edit_PLCIP",
            "lineEdit_PLC_port",
            "label_result",
            "label_quantity",
            "label_count",
            "label_batch",
            "label_cycle_time",
            "label_dimention_image",
            "label_fps",
            "widget_AI_configure",
            "widget_hardware_setting",
            "widget_panel_setting",
            "label_30",
            "label_116",
            "label_clock",
            "checkbox_move_all_ROI",
        )

        self.preview_scene = QGraphicsScene(self)
        self.graphics_view_reference.setScene(self.preview_scene)

        self.live_timer = QTimer(self)
        self.live_timer.setInterval(1000)
        self.plc_poll_timer = QTimer(self)
        self.plc_poll_timer.setInterval(250)
        self.result_hold_timer = QTimer(self)
        self.result_hold_timer.setSingleShot(True)
        self.idle_shutdown_timer = QTimer(self)
        self.idle_shutdown_timer.setSingleShot(True)
        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self._update_clock)

        self._live_resume_after_hold = False
        self._setting_panel_min_height = 281
        self._setting_panel_max_height = 871
        self._training_process: QProcess | None = None

        self._configure_static_inputs()
        self._connect_events()
        self._apply_runtime_assets()
        self._update_clock()
        self.clock_timer.start()

    def render(self) -> None:
        state = self.shell.main_state or self.shell.refresh_main()
        live_active = self.live_timer.isActive()
        hold_active = self.result_hold_timer.isActive()
        control_states = self._control_enabled_map(
            state=state,
            live_active=live_active,
            hold_active=hold_active,
        )
        self._render_identity_state(state)
        self._render_session_state(state)
        self._render_cycle_state(state, hold_active=hold_active)
        self._render_preview(state)
        self._apply_runtime_button_states(
            state=state,
            control_states=control_states,
            live_active=live_active,
            hold_active=hold_active,
        )
        self._apply_access_profile_state(state)
        if self._status_bar is not None:
            self._status_bar.showMessage(state.message or "")

    def _render_identity_state(self, state) -> None:
        self.label_current_user.setText(f"User: {state.current_user_name or '<none>'}")
        self.label_product.setText(state.selected_product_name or "<none>")
        self.current_model_path.setText(state.model_path or "<none>")

    def _render_session_state(self, state) -> None:
        self._set_combo_text(self.combobox_product, state.available_products, state.selected_product_name)
        self._set_combo_text(
            self.comboBox_PLC_protocol,
            self._plc_protocol_display_values(),
            self._display_plc_protocol(state.plc_protocol),
        )
        self._set_combo_text(self.combobox_zoom_factor, self._zoom_values(), f"{float(state.zoom_factor or 0.4):g}")
        self._set_combo_text(
            self.combobox_acceptance_threshold,
            self._threshold_values(),
            f"{float(state.threshold_accept or 0.5):g}",
        )
        self._set_combo_text(
            self.combobox_mns_threshold,
            self._threshold_values(),
            f"{float(state.threshold_mns or 0.5):g}",
        )

        self.spinbox_default_value.setValue(int(state.default_number or 0))
        self.spinbox_exposure_time.setValue(int(state.exposure or 0))
        self.spinbox_result_time.setValue(int(state.result_time or 0))
        self.spinbox_sleep_time.setValue(int(state.sleep_time or 0))
        self.spinbox_offset_x.setValue(int(state.offset_x or 0))
        self.spinbox_offset_y.setValue(int(state.offset_y or 0))
        self.spinbox_image_width.setValue(int(state.image_width or 0))
        self.spinbox_image_height.setValue(int(state.image_height or 0))
        self.spinbox_ROI_to_move.setMaximum(max(1, len(state.roi_points) or 5))
        self.line_edit_PLCIP.setText(state.plc_ip)
        self.lineEdit_PLC_port.setText(str(state.plc_port))

    def _render_cycle_state(self, state, *, hold_active: bool) -> None:
        cycle_text, cycle_variant = self._cycle_status_visual_state(
            last_result_label=state.last_result_label,
            last_cycle_status=state.last_cycle_status,
            hold_active=hold_active,
        )
        self._apply_result_visual(cycle_text, cycle_variant)
        self.label_quantity.setText(str(state.last_quantity))
        self.label_count.setText(str(state.inspection_counter_value))
        self.label_batch.setText(str(state.inspection_batch_value))
        self.label_cycle_time.setText(f"{state.last_cycle_duration_ms:.1f} ms")
        self.label_dimention_image.setText(self._build_dimension_text(state))
        self.label_fps.setText(self._build_fps_text(state))

    def _apply_runtime_button_states(
        self,
        *,
        state,
        control_states: dict[str, bool],
        live_active: bool,
        hold_active: bool,
    ) -> None:
        self._apply_camera_button_state(
            connected=state.camera_connected,
            live_active=live_active or hold_active,
            can_connect=control_states["connect_camera"],
            can_disconnect=control_states["disconnect_camera"],
        )
        self._apply_plc_button_state(
            connected=state.plc_connected,
            can_connect=control_states["connect_plc"],
            can_disconnect=control_states["disconnect_plc"],
        )
        self._apply_mode_button_state(
            manual_active=not state.auto_mode_enabled,
            auto_active=state.auto_mode_enabled,
            can_manual=control_states["manual_mode"],
            can_auto=control_states["auto_mode"],
        )
        self._apply_toggle_button_state(
            self.button_real_time,
            inactive_text="Real-time",
            active_text="AI Checking",
            active=state.inspection_enabled,
            enabled=state.access_profile.can_real_time or state.access_profile.can_run_cycle,
        )
        self._apply_toggle_button_state(
            self.button_record,
            inactive_text="Record",
            active_text="Recording",
            active=state.recording_enabled,
            enabled=state.access_profile.can_run_cycle,
        )

        live_text, _ = self._live_preview_visual_state(
            live_active=live_active,
            hold_active=hold_active,
        )
        self.button_live_camera.setText(live_text)
        self.button_live_camera.setEnabled(control_states["live_preview"])
        self.button_grab.setEnabled(control_states["run_cycle"] or control_states["grab_preview"])
        self.button_auto.setEnabled(control_states["auto_mode"])
        self.button_manual.setEnabled(control_states["manual_mode"])
        self.button_reset_counter.setEnabled(state.access_profile.can_run_cycle)
        self.button_toggle_setting.setEnabled(
            state.access_profile.can_configure_hardware
            or state.access_profile.can_configure_ai
            or state.access_profile.can_update_product_list
        )

    def _apply_access_profile_state(self, state) -> None:
        self.widget_AI_configure.setEnabled(state.access_profile.can_configure_ai)
        self.widget_hardware_setting.setEnabled(state.access_profile.can_configure_hardware)
        self.button_authentication.setEnabled(state.current_role == "Administrator")
        self.button_report.setEnabled(state.current_role == "Administrator")

    def _configure_static_inputs(self) -> None:
        self.checkbox_show_ROI.setChecked(True)
        self.spinbox_ROI_to_move.setRange(1, 5)
        self._set_combo_text(self.combobox_zoom_factor, self._zoom_values(), "0.4")
        self._set_combo_text(self.combobox_acceptance_threshold, self._threshold_values(), "0.5")
        self._set_combo_text(self.combobox_mns_threshold, self._threshold_values(), "0.5")
        self._set_combo_text(
            self.comboBox_PLC_protocol,
            self._plc_protocol_display_values(),
            self._display_plc_protocol("slmp"),
        )

    def _connect_events(self) -> None:
        self.action_logout.triggered.connect(self._on_logout)
        self.action_load_model.triggered.connect(self._on_browse_model)
        self.action_update_product_list.triggered.connect(self._on_import_catalog)
        self.action_open_training_screen.triggered.connect(self._on_open_training_screen)
        self.action_select_path_save_image.triggered.connect(self._on_open_artifact_path)
        self.button_exit.clicked.connect(self._on_exit)
        self.button_grab.clicked.connect(self._on_run_cycle)
        self.button_live_camera.clicked.connect(self._on_toggle_live_preview)
        self.button_real_time.clicked.connect(self._on_toggle_ai_checking)
        self.button_auto.clicked.connect(self._on_auto_mode)
        self.button_manual.clicked.connect(self._on_manual_mode)
        self.button_record.clicked.connect(self._on_toggle_recording)
        self.button_connect_camera.clicked.connect(self._on_connect_camera)
        self.button_disconnect_camera.clicked.connect(self._on_disconnect_camera)
        self.button_connect_PLC.clicked.connect(self._on_connect_plc)
        self.button_disconnect_PLC.clicked.connect(self._on_disconnect_plc)
        self.button_reset_counter.clicked.connect(self._on_reset_counters)
        self.button_toggle_setting.clicked.connect(self._on_toggle_setting_panel)
        self.button_on_save_default.clicked.connect(self._on_save_default)
        self.button_save_result_time.clicked.connect(self._on_save_result_time)
        self.button_save_sleep_time.clicked.connect(self._on_save_sleep_time)
        self.button_save_zoom.clicked.connect(self._on_save_zoom)
        self.button_save_PLCIP.clicked.connect(self._on_save_plc)
        self.button_save_camera.clicked.connect(self._on_save_camera)
        self.button_save_AI_config.clicked.connect(self._on_save_ai_config)
        self.button_move_ROI_left.clicked.connect(lambda: self._on_move_roi("left"))
        self.button_move_ROI_right.clicked.connect(lambda: self._on_move_roi("right"))
        self.button_move_ROI_up.clicked.connect(lambda: self._on_move_roi("up"))
        self.button_move_ROI_down.clicked.connect(lambda: self._on_move_roi("down"))
        self.button_authentication.clicked.connect(
            lambda: self._show_not_migrated_message("Authentication management screen is not migrated to V2 yet.")
        )
        self.button_report.clicked.connect(
            lambda: self._show_not_migrated_message("Report screen is not migrated to V2 yet.")
        )
        self.combobox_product.currentTextChanged.connect(self._on_product_changed)
        self.live_timer.timeout.connect(self._on_live_tick)
        self.plc_poll_timer.timeout.connect(self._on_plc_poll_tick)
        self.result_hold_timer.timeout.connect(self._on_result_hold_timeout)
        self.idle_shutdown_timer.timeout.connect(self._on_idle_shutdown_timeout)

    def _on_product_changed(self, product_name: str) -> None:
        if not product_name:
            return
        self.shell.main_state = self.shell.main_presenter.select_current_product(product_name)
        self.render()

    def _on_save_default(self) -> None:
        def action() -> None:
            self.shell.main_state = self._save_current_product_settings()
            self.render()

        self._run_safe_ui_action("Save Default", action)

    def _on_save_result_time(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.update_session_settings(
                result_time=self.spinbox_result_time.value()
            )
            self.render()

        self._run_safe_ui_action("Save Result Time", action)

    def _on_save_sleep_time(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.update_session_settings(
                sleep_time=self.spinbox_sleep_time.value()
            )
            self.render()

        self._run_safe_ui_action("Save Sleep Time", action)

    def _on_save_zoom(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.update_session_settings(
                zoom_factor=self._current_combo_float(self.combobox_zoom_factor)
            )
            self.render()

        self._run_safe_ui_action("Save Zoom", action)

    def _on_save_plc(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.update_session_settings(
                **self._current_plc_session_updates()
            )
            self.render()

        self._run_safe_ui_action("Save PLC", action)

    def _on_save_camera(self) -> None:
        def action() -> None:
            self.shell.main_presenter.update_session_settings(**self._current_camera_session_updates())
            self.shell.main_presenter.update_product_settings(**self._current_product_updates())
            self.shell.main_state = self.shell.main_presenter.grab_preview_frame()
            self.render()

        self._run_safe_ui_action("Save Camera", action)

    def _on_save_ai_config(self) -> None:
        def action() -> None:
            self.shell.main_state = self._save_current_product_settings()
            self.render()

        self._run_safe_ui_action("Save AI Config", action)

    def _on_browse_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select model",
            str(Path.cwd()),
            "Model files (*.pt *.onnx *.engine);;All Files (*)",
        )
        if not path:
            return

        def action() -> None:
            self.current_model_path.setText(path)
            self.shell.main_state = self._save_current_product_settings(model_path=path)
            self.render()

        self._run_safe_ui_action("Load Model", action)

    def _on_import_catalog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select product catalog",
            str(Path.cwd()),
            "Catalog files (*.xlsx *.xlsm *.csv *.json *.yaml *.yml);;All Files (*)",
        )
        if not path:
            return

        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.import_product_catalog_from_file(path)
            self.render()

        self._run_safe_ui_action("Import Catalog", action)

    def _on_open_training_screen(self) -> None:
        def action() -> None:
            if self._training_process is not None and self._training_process.state() != QProcess.NotRunning:
                current_state = self.shell.main_state or self.shell.refresh_main()
                self.shell.main_state = replace(current_state, message="Training tool is already running.")
                self.render()
                return

            executable = self._resolve_training_executable()
            if executable is None:
                message = (
                    "Training tool executable was not found. "
                    "Expected OCR_DeepLearning_Software\\OCR_DeepLearning_Software.exe."
                )
                current_state = self.shell.main_state or self.shell.refresh_main()
                self.shell.main_state = replace(current_state, message=message)
                self.render()
                QMessageBox.information(self, "Training Tool", message)
                return

            self._stop_live_preview()
            self.shell.main_state = self.shell.main_presenter.set_manual_mode()
            self.render()
            self._start_training_process(executable)

        self._run_safe_ui_action("Open Training Screen", action, stop_live_on_error=True)

    def _on_open_artifact_path(self) -> None:
        def action() -> None:
            target_path = self.shell.resolve_artifact_browser_path()
            success, message = self.shell.open_external_path(target_path)
            current_state = self.shell.main_state or self.shell.refresh_main()
            self.shell.main_state = replace(current_state, message=message)
            self.render()
            if not success:
                QMessageBox.information(self, "Artifact Path", message)

        self._run_safe_ui_action("Open Artifact Path", action)

    def _on_toggle_setting_panel(self) -> None:
        current_height = self.widget_panel_setting.height()
        start_geometry = self.widget_panel_setting.geometry()
        if current_height <= self._setting_panel_min_height + 2:
            target_height = self._setting_panel_max_height
            self.button_toggle_setting.setText("Collapse")
        else:
            target_height = self._setting_panel_min_height
            self.button_toggle_setting.setText("Expand")

        target_geometry = start_geometry.adjusted(0, 0, 0, target_height - current_height)
        self._setting_panel_anim = QPropertyAnimation(self.widget_panel_setting, b"geometry", self)
        self._setting_panel_anim.setDuration(250)
        self._setting_panel_anim.setStartValue(start_geometry)
        self._setting_panel_anim.setEndValue(target_geometry)
        self._setting_panel_anim.start()

    def _on_logout(self) -> None:
        self.result_hold_timer.stop()
        self.idle_shutdown_timer.stop()
        self.plc_poll_timer.stop()
        self._stop_live_preview()
        self.shell.logout()
        self.navigate.emit(ScreenId.LOGIN.value)

    def _on_exit(self) -> None:
        self._stop_live_preview()
        self.shell.main_presenter.shutdown_runtime_hardware()
        QApplication.quit()

    def _on_run_cycle(self) -> None:
        def action() -> None:
            self._begin_result_hold_if_needed()
            self.shell.main_state = self.shell.main_presenter.run_cycle()
            self._arm_result_hold_resume()
            self.render()

        self._run_safe_ui_action("Grab", action, stop_live_on_error=True)

    def _on_reset_counters(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.reset_cycle_counters()
            self.render()
            QMessageBox.information(self, "Success", "Reset Counter and Batch successfully!")

        self._run_safe_ui_action("Reset Counter", action)

    def _on_toggle_live_preview(self) -> None:
        def action() -> None:
            if self.live_timer.isActive() or self.result_hold_timer.isActive():
                self._stop_live_preview()
                self.render()
                return
            current_state = self.shell.main_state or self.shell.refresh_main()
            if not current_state.camera_connected:
                self.shell.main_state = self.shell.main_presenter.connect_camera_hardware()
                if not self.shell.main_state.camera_connected:
                    self.render()
                    return
            self.idle_shutdown_timer.stop()
            self.live_timer.start()
            self._on_live_tick()

        self._run_safe_ui_action("Live Camera", action, stop_live_on_error=True)

    def _on_live_tick(self) -> None:
        def action() -> None:
            self.idle_shutdown_timer.stop()
            if self.shell.main_presenter.runtime_controls.inspection_enabled:
                self.shell.main_state = self.shell.main_presenter.inspect_preview_frame()
            else:
                self.shell.main_state = self.shell.main_presenter.grab_preview_frame()
            self.render()

        self._run_safe_ui_action("Live Camera Tick", action, stop_live_on_error=True)

    def _on_move_roi(self, direction: str) -> None:
        def action() -> None:
            previous_state = self.shell.main_state or self.shell.refresh_main()
            updated_state = self.shell.main_presenter.move_roi(
                direction=direction,
                roi_index=self.spinbox_ROI_to_move.value(),
                move_all=self.checkbox_move_all_ROI.isChecked(),
            )
            if previous_state.preview_frame is not None and updated_state.preview_frame is None:
                updated_state = replace(
                    updated_state,
                    preview_frame=previous_state.preview_frame,
                    preview_annotations=previous_state.preview_annotations,
                    preview_summary=previous_state.preview_summary,
                    last_cycle_status=previous_state.last_cycle_status,
                    plc_last_result=previous_state.plc_last_result,
                    task_summaries=previous_state.task_summaries,
                    ocr_diagnostics=previous_state.ocr_diagnostics,
                )
            self.shell.main_state = updated_state
            self.render()

        self._run_safe_ui_action(f"Move ROI {direction}", action)

    def _on_manual_mode(self) -> None:
        def action() -> None:
            self.plc_poll_timer.stop()
            self.idle_shutdown_timer.stop()
            self.shell.main_state = self.shell.main_presenter.set_manual_mode()
            self.render()

        self._run_safe_ui_action("Manual Mode", action)

    def _on_auto_mode(self) -> None:
        def action() -> None:
            self.idle_shutdown_timer.stop()
            self.plc_poll_timer.start()
            self.shell.main_state = self.shell.main_presenter.set_auto_mode()
            self.render()

        self._run_safe_ui_action("Auto Mode", action)

    def _on_toggle_ai_checking(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.toggle_inspection_enabled()
            self.render()

        self._run_safe_ui_action("Real-time AI", action)

    def _on_toggle_recording(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.toggle_recording_enabled()
            self.render()

        self._run_safe_ui_action("Record Result", action)

    def _on_poll_plc_once(self) -> None:
        def action() -> None:
            self._begin_result_hold_if_needed(for_plc=True)
            self.shell.main_state = self.shell.main_presenter.poll_plc_once()
            if self.shell.main_state.plc_poll_action == "stop":
                self._stop_live_preview()
                self._arm_idle_shutdown()
            elif self.shell.main_state.plc_poll_action == "start":
                self.idle_shutdown_timer.stop()
                if not self.live_timer.isActive():
                    self.live_timer.start()
                    self._on_live_tick()
            elif self.shell.main_state.plc_poll_action == "grab":
                self.idle_shutdown_timer.stop()
            if self.shell.main_state.plc_cycle_triggered:
                self._arm_result_hold_resume()
            self.render()

        self._run_safe_ui_action("Poll PLC", action, stop_live_on_error=True)

    def _on_plc_poll_tick(self) -> None:
        self._on_poll_plc_once()

    def _on_connect_camera(self) -> None:
        def action() -> None:
            self.shell.main_state = self.shell.main_presenter.connect_camera_hardware()
            self.render()

        self._run_safe_ui_action("Connect Camera", action)

    def _on_disconnect_camera(self) -> None:
        def action() -> None:
            self._stop_live_preview()
            self.shell.main_state = self.shell.main_presenter.disconnect_camera_hardware()
            self.render()

        self._run_safe_ui_action("Disconnect Camera", action, stop_live_on_error=True)

    def _on_connect_plc(self) -> None:
        def action() -> None:
            connected_state = self.shell.main_presenter.connect_plc_hardware()
            if connected_state.plc_connected:
                self.plc_poll_timer.start()
                auto_state = self.shell.main_presenter.set_auto_mode()
                self.shell.main_state = self._merge_plc_connect_workflow_state(
                    connected_state=connected_state,
                    auto_state=auto_state,
                )
            else:
                self.shell.main_state = connected_state
            self.render()

        self._run_safe_ui_action("Connect PLC", action)

    def _on_disconnect_plc(self) -> None:
        def action() -> None:
            self.idle_shutdown_timer.stop()
            self.plc_poll_timer.stop()
            disconnected_state = self.shell.main_presenter.disconnect_plc_hardware()
            manual_state = self.shell.main_presenter.set_manual_mode()
            self.shell.main_state = self._merge_plc_disconnect_workflow_state(
                disconnected_state=disconnected_state,
                manual_state=manual_state,
            )
            self.render()

        self._run_safe_ui_action("Disconnect PLC", action)

    def _on_shutdown_runtime(self) -> None:
        def action() -> None:
            self.idle_shutdown_timer.stop()
            self.plc_poll_timer.stop()
            self._stop_live_preview()
            self.shell.main_state = self.shell.main_presenter.shutdown_runtime_hardware()
            self.render()

        self._run_safe_ui_action("Shutdown Runtime", action, stop_live_on_error=True)

    def _on_idle_shutdown_timeout(self) -> None:
        self._on_shutdown_runtime()

    def _on_result_hold_timeout(self) -> None:
        def action() -> None:
            if not self._live_resume_after_hold:
                return
            self._live_resume_after_hold = False
            self.live_timer.start()
            self._on_live_tick()

        self._run_safe_ui_action("Result Hold Resume", action, stop_live_on_error=True)

    def _stop_live_preview(self) -> None:
        self.result_hold_timer.stop()
        self._live_resume_after_hold = False
        self.live_timer.stop()

    def _begin_result_hold_if_needed(self, *, for_plc: bool = False) -> None:
        current_state = self.shell.main_state or self.shell.refresh_main()
        if for_plc and not current_state.inspection_enabled:
            self._live_resume_after_hold = False
            return
        if not self.live_timer.isActive():
            self._live_resume_after_hold = False
            return
        self._live_resume_after_hold = True
        self.live_timer.stop()

    def _arm_result_hold_resume(self) -> None:
        if not self._live_resume_after_hold:
            return
        current_state = self.shell.main_state or self.shell.refresh_main()
        result_seconds = max(0, int(current_state.result_time or 0))
        if result_seconds <= 0:
            self._on_result_hold_timeout()
            return
        self.result_hold_timer.start(result_seconds * 1000)

    def _arm_idle_shutdown(self) -> None:
        current_state = self.shell.main_state or self.shell.refresh_main()
        sleep_minutes = max(0, int(current_state.sleep_time or 0))
        if sleep_minutes <= 0:
            return
        self.idle_shutdown_timer.start(sleep_minutes * 60000)

    def _build_dimension_text(self, state) -> str:
        if state.preview_frame is not None:
            frame = state.preview_frame.frame
            shape = getattr(frame, "shape", None)
            if shape is not None and len(shape) >= 2:
                return f"{int(shape[1])} x {int(shape[0])}"
        return f"{int(state.image_width or 0)} x {int(state.image_height or 0)}"

    def _build_fps_text(self, state) -> str:
        if state.preview_frame is None or state.preview_frame.capture_seconds <= 0:
            return "-"
        fps = 1.0 / state.preview_frame.capture_seconds
        return f"{fps:.1f}"

    def _render_preview(self, state) -> None:
        width = max(420, self.graphics_view_reference.viewport().width() - 24)
        height = max(260, self.graphics_view_reference.viewport().height() - 24)
        pixmap = build_preview_pixmap(
            state.preview_frame.frame if state.preview_frame is not None else None,
            state.preview_summary or "No preview captured.",
            width=width,
            height=height,
            roi_rects=state.roi_rects if self.checkbox_show_ROI.isChecked() else [],
            annotations=state.preview_annotations if self.checkbox_show_ROI.isChecked() else [],
        )
        self.preview_scene.clear()
        self.preview_scene.addPixmap(pixmap)
        rect = pixmap.rect()
        self.preview_scene.setSceneRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()))
        self.scale_zoom_factor()

    def _apply_camera_button_state(
        self,
        *,
        connected: bool,
        live_active: bool,
        can_connect: bool,
        can_disconnect: bool,
    ) -> None:
        if connected:
            self.button_connect_camera.setText("Connected")
            self.button_connect_camera.setStyleSheet(BUTTON_STYLESHEET_ON)
            self.button_disconnect_camera.setText("Disconnect")
            self.button_disconnect_camera.setStyleSheet(BUTTON_STYLESHEET_OFF)
        else:
            self.button_connect_camera.setText("Connect")
            self.button_connect_camera.setStyleSheet(BUTTON_STYLESHEET_OFF)
            self.button_disconnect_camera.setText("Disconnected")
            self.button_disconnect_camera.setStyleSheet(BUTTON_STYLESHEET_ON)
        self.button_connect_camera.setEnabled(can_connect)
        self.button_disconnect_camera.setEnabled(can_disconnect and not live_active)

    def _apply_plc_button_state(
        self,
        *,
        connected: bool,
        can_connect: bool,
        can_disconnect: bool,
    ) -> None:
        if connected:
            self.button_connect_PLC.setText("Connected")
            self.button_connect_PLC.setStyleSheet(BUTTON_STYLESHEET_ON)
            self.button_disconnect_PLC.setText("Disconnect")
            self.button_disconnect_PLC.setStyleSheet(BUTTON_STYLESHEET_OFF)
        else:
            self.button_connect_PLC.setText("Connect")
            self.button_connect_PLC.setStyleSheet(BUTTON_STYLESHEET_OFF)
            self.button_disconnect_PLC.setText("Disconnected")
            self.button_disconnect_PLC.setStyleSheet(BUTTON_STYLESHEET_ON)
        self.button_connect_PLC.setEnabled(can_connect)
        self.button_disconnect_PLC.setEnabled(can_disconnect)

    def _apply_mode_button_state(
        self,
        *,
        manual_active: bool,
        auto_active: bool,
        can_manual: bool,
        can_auto: bool,
    ) -> None:
        del auto_active
        if manual_active:
            self.button_manual.setText("Manual ON")
            self.button_manual.setStyleSheet(BUTTON_STYLESHEET_ON)
            self.button_auto.setText("Auto")
            self.button_auto.setStyleSheet(BUTTON_STYLESHEET_OFF)
        else:
            self.button_manual.setText("Manual")
            self.button_manual.setStyleSheet(BUTTON_STYLESHEET_OFF)
            self.button_auto.setText("Auto ON")
            self.button_auto.setStyleSheet(BUTTON_STYLESHEET_ON)
        self.button_manual.setEnabled(can_manual)
        self.button_auto.setEnabled(can_auto)

    def _apply_toggle_button_state(
        self,
        button,
        *,
        inactive_text: str,
        active_text: str,
        active: bool,
        enabled: bool,
    ) -> None:
        button.setText(active_text if active else inactive_text)
        button.setStyleSheet(BUTTON_STYLESHEET_ON if active else BUTTON_STYLESHEET_OFF)
        button.setEnabled(enabled)

    def _apply_result_visual(self, cycle_text: str, cycle_variant: str) -> None:
        display_text = cycle_text
        if cycle_text == "CHECKING":
            display_text = "Checking"
        self.label_result.setText(display_text)
        if cycle_variant == "ok":
            self.label_result.setStyleSheet(RESULT_STYLE_OK)
        elif cycle_variant == "fail":
            self.label_result.setStyleSheet(RESULT_STYLE_FAIL)
        elif cycle_variant in {"checking", "hold"}:
            self.label_result.setStyleSheet(RESULT_STYLE_CHECKING)
        else:
            self.label_result.setStyleSheet(RESULT_STYLE_IDLE)

    @staticmethod
    def _cycle_status_visual_state(
        *,
        last_result_label: str,
        last_cycle_status: str,
        hold_active: bool,
    ) -> tuple[str, str]:
        if hold_active:
            return "RESULT HOLD", "hold"
        normalized_result = (last_result_label or "").strip().lower()
        normalized_cycle = (last_cycle_status or "").strip().lower()
        if normalized_result == "ok":
            return "OK", "ok"
        if normalized_result in {"fail", "ng"} or normalized_cycle == "fail":
            return "FAIL", "fail"
        if normalized_result == "checking":
            return "CHECKING", "checking"
        if normalized_cycle == "pass":
            return "OK", "ok"
        return "NO CYCLE", "idle"

    @staticmethod
    def _live_preview_visual_state(*, live_active: bool, hold_active: bool) -> tuple[str, str]:
        if hold_active:
            return "Result Hold", "warning"
        if live_active:
            return "Live ON", "active"
        return "Live Camera", "inactive"

    def _run_safe_ui_action(self, action_name: str, action, *, stop_live_on_error: bool = False) -> None:
        try:
            action()
        except Exception as exc:
            self._log_ui_action_exception(action_name, exc)
            if stop_live_on_error:
                try:
                    self._stop_live_preview()
                except Exception:
                    pass
            current_state = self.shell.main_state or self.shell.refresh_main()
            self.shell.main_state = replace(
                current_state,
                message=self._build_ui_error_message(action_name, exc),
            )
            self.render()

    @staticmethod
    def _build_ui_error_message(action_name: str, exc: Exception) -> str:
        return f"{action_name} failed. Check ui-error.log. {exc}"

    def _log_ui_action_exception(self, action_name: str, exc: Exception) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = (
            f"[{timestamp}] action={action_name}\n"
            f"{type(exc).__name__}: {exc}\n"
            f"{traceback.format_exc()}\n"
            f"{'-' * 80}\n"
        )
        try:
            log_dir = self._ui_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "ui-error.log"
            existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            log_path.write_text(existing + payload, encoding="utf-8")
        except Exception:
            return

    @staticmethod
    def _ui_log_dir() -> Path:
        return resolve_app_storage_root_dir() / "logs"

    def _apply_runtime_assets(self) -> None:
        self.setWindowTitle("DRB OCR AI V2")
        self._set_label_pixmap(
            self.label_30,
            self._asset_path("form_UI", "logo", "dong_400x400_398160146-removebg-preview.png"),
            max_height=30,
        )
        self._set_label_pixmap(
            self.label_116,
            self._asset_path("form_UI", "all-icons", "clock-6-24.png"),
            max_height=22,
        )

    def _update_clock(self) -> None:
        self.label_clock.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy  HH:mm:ss"))

    def _set_label_pixmap(self, label, path: Path, *, max_height: int) -> None:
        if not path.exists():
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return
        label.setPixmap(pixmap.scaledToHeight(max_height))

    def _asset_path(self, *parts: str) -> Path:
        return Path(__file__).resolve().parents[5].joinpath(*parts)

    def _bind_ui_attrs(self, *names: str) -> None:
        for name in names:
            setattr(self, name, getattr(self._ui_window, name))

    @staticmethod
    def _control_enabled_map(*, state, live_active: bool, hold_active: bool) -> dict[str, bool]:
        profile = state.access_profile
        can_control_hardware = profile.can_configure_hardware
        return {
            "connect_camera": can_control_hardware and not state.camera_connected and not live_active and not hold_active,
            "disconnect_camera": can_control_hardware and state.camera_connected and not live_active and not hold_active,
            "connect_plc": can_control_hardware and not state.plc_connected,
            "disconnect_plc": can_control_hardware and state.plc_connected,
            "shutdown_runtime": can_control_hardware,
            "manual_mode": profile.can_manual_mode and state.auto_mode_enabled,
            "auto_mode": profile.can_auto_mode and not state.auto_mode_enabled,
            "poll_plc": state.plc_connected and (profile.can_auto_mode or profile.can_manual_mode or profile.can_run_cycle),
            "grab_preview": profile.can_grab or profile.can_live_camera or profile.can_run_cycle,
            "live_preview": profile.can_live_camera or profile.can_run_cycle,
            "run_cycle": bool(state.selected_product_name) and profile.can_run_cycle and not state.auto_mode_enabled and not hold_active,
        }

    @staticmethod
    def _merge_plc_connect_workflow_state(*, connected_state, auto_state):
        return replace(
            auto_state,
            message=f"{connected_state.message} Auto mode enabled.",
        )

    @staticmethod
    def _merge_plc_disconnect_workflow_state(*, disconnected_state, manual_state):
        return replace(
            manual_state,
            camera_connected=disconnected_state.camera_connected,
            plc_connected=disconnected_state.plc_connected,
            plc_last_result=disconnected_state.plc_last_result,
            message=f"{disconnected_state.message} Manual mode enabled.",
        )

    def scale_zoom_factor(self) -> None:
        try:
            zoom_factor = self._current_combo_float(self.combobox_zoom_factor)
        except ValueError:
            zoom_factor = 0.4
        transform = QTransform()
        transform.scale(zoom_factor, zoom_factor)
        self.graphics_view_reference.setTransform(transform)

    def _show_not_migrated_message(self, message: str) -> None:
        QMessageBox.information(self, "V2 UI", message)

    def _resolve_training_executable(self) -> Path | None:
        for candidate in self._training_executable_candidates():
            if candidate.exists():
                return candidate
        return None

    def _training_executable_candidates(self) -> list[Path]:
        repo_root = self._asset_path()
        return [
            repo_root / "OCR_DeepLearning_Software" / "OCR_DeepLearning_Software.exe",
            Path.cwd() / "OCR_DeepLearning_Software" / "OCR_DeepLearning_Software.exe",
        ]

    def _start_training_process(self, executable: Path) -> None:
        host_window = self.window()
        process = QProcess(self)
        process.setProgram(str(executable))
        process.setWorkingDirectory(str(executable.parent))
        process.finished.connect(self._on_training_process_finished)
        process.errorOccurred.connect(self._on_training_process_error)
        self._training_process = process

        if host_window is not None:
            host_window.hide()

        process.start()
        if process.waitForStarted(1500):
            current_state = self.shell.main_state or self.shell.refresh_main()
            self.shell.main_state = replace(current_state, message="Training tool started.")
            self.render()
            return

        error_message = process.errorString() or "Unknown process start error."
        self._training_process = None
        self._restore_after_training_process()
        current_state = self.shell.main_state or self.shell.refresh_main()
        self.shell.main_state = replace(
            current_state,
            message=f"Training tool failed to start: {error_message}",
        )
        self.render()
        QMessageBox.warning(self, "Training Tool", self.shell.main_state.message)

    def _on_training_process_finished(self, *_args) -> None:
        self._training_process = None
        self._restore_after_training_process()
        current_state = self.shell.main_state or self.shell.refresh_main()
        self.shell.main_state = replace(current_state, message="Training tool closed.")
        self.render()

    def _on_training_process_error(self, _error) -> None:
        process = self._training_process
        self._training_process = None
        self._restore_after_training_process()
        error_message = process.errorString() if process is not None else "Unknown training process error."
        current_state = self.shell.main_state or self.shell.refresh_main()
        self.shell.main_state = replace(
            current_state,
            message=f"Training tool error: {error_message}",
        )
        self.render()

    def _restore_after_training_process(self) -> None:
        host_window = self.window()
        if host_window is None:
            return
        host_window.show()
        host_window.raise_()
        host_window.activateWindow()

    @staticmethod
    def _threshold_values() -> list[str]:
        return [
            "0.1", "0.15", "0.2", "0.25", "0.3", "0.35", "0.4", "0.45", "0.5",
            "0.55", "0.6", "0.65", "0.7", "0.75", "0.8", "0.85", "0.9", "0.95", "1.0",
        ]

    @staticmethod
    def _zoom_values() -> list[str]:
        return [
            "0.1", "0.15", "0.2", "0.25", "0.3", "0.35", "0.4", "0.45", "0.5",
            "0.55", "0.6", "0.65", "0.7", "0.75", "0.8", "0.85", "0.9", "0.95", "1.0",
        ]

    def _current_product_updates(self, *, model_path: str | None = None) -> dict[str, object]:
        return {
            "product_name": self.combobox_product.currentText().strip(),
            "model_path": (model_path if model_path is not None else self.current_model_path.text()).strip(),
            "default_number": self.spinbox_default_value.value(),
            "exposure": self.spinbox_exposure_time.value(),
            "threshold_accept": self._current_combo_float(self.combobox_acceptance_threshold),
            "threshold_mns": self._current_combo_float(self.combobox_mns_threshold),
        }

    def _current_camera_session_updates(self) -> dict[str, object]:
        return {
            "offset_x": self.spinbox_offset_x.value(),
            "offset_y": self.spinbox_offset_y.value(),
            "image_width": self.spinbox_image_width.value(),
            "image_height": self.spinbox_image_height.value(),
            "zoom_factor": self._current_combo_float(self.combobox_zoom_factor),
        }

    def _current_plc_session_updates(self) -> dict[str, object]:
        return {
            "plc_ip": self.line_edit_PLCIP.text().strip(),
            "plc_port": self.lineEdit_PLC_port.text().strip(),
            "plc_protocol": self._internal_plc_protocol(self.comboBox_PLC_protocol.currentText().strip()),
        }

    def _save_current_product_settings(self, *, model_path: str | None = None):
        return self.shell.main_presenter.update_product_settings(
            **self._current_product_updates(model_path=model_path)
        )

    @staticmethod
    def _plc_protocol_display_values() -> list[str]:
        return ["TCP", "RTU", "SLMP"]

    @staticmethod
    def _display_plc_protocol(protocol: str) -> str:
        normalized = str(protocol or "").strip().lower()
        if normalized in {"tcp", "modbus_tcp", "modbustcp"}:
            return "TCP"
        if normalized in {"rtu", "modbus_rtu", "modbusrtu"}:
            return "RTU"
        if normalized in {"slmp", "mc", "mcprotocol", "mc_protocol"}:
            return "SLMP"
        return str(protocol or "SLMP")

    @staticmethod
    def _internal_plc_protocol(protocol: str) -> str:
        normalized = str(protocol or "").strip().lower()
        if normalized in {"tcp", "modbus_tcp", "modbustcp"}:
            return "modbus_tcp"
        if normalized in {"rtu", "modbus_rtu", "modbusrtu"}:
            return "modbus_rtu"
        if normalized in {"slmp", "mc", "mcprotocol", "mc_protocol"}:
            return "slmp"
        return str(protocol or "").strip()

    @staticmethod
    def _set_combo_text(combo, values: list[str], current_text: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        if current_text:
            index = combo.findText(current_text)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                combo.addItem(current_text)
                combo.setCurrentText(current_text)
        combo.blockSignals(False)

    @staticmethod
    def _current_combo_float(combo) -> float:
        return float(str(combo.currentText()).strip())
