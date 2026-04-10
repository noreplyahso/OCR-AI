from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.context import AccessProfile


@dataclass
class GetAccessProfileUseCase:
    def execute(self, role: str) -> AccessProfile:
        normalized_role = (role or "Operator").strip() or "Operator"
        admin_profile = AccessProfile(
            can_open_authentication=True,
            can_open_report=True,
            can_configure_image=True,
            can_configure_hardware=True,
            can_configure_ai=True,
            can_load_model=True,
            can_select_image_path=True,
            can_open_training_screen=True,
            can_update_product_list=True,
            can_grab=True,
            can_live_camera=True,
            can_real_time=True,
            can_manual_mode=True,
            can_auto_mode=True,
            can_change_result_time=True,
            can_change_sleep_time=True,
            can_toggle_setting=True,
            can_run_cycle=True,
        )
        if normalized_role == "Supervisor":
            return AccessProfile(
                **{
                    **admin_profile.__dict__,
                    "can_open_authentication": False,
                    "can_open_report": False,
                }
            )
        if normalized_role == "Operator":
            return AccessProfile(
                can_open_authentication=False,
                can_open_report=False,
                can_configure_image=False,
                can_configure_hardware=False,
                can_configure_ai=False,
                can_load_model=False,
                can_select_image_path=False,
                can_open_training_screen=False,
                can_update_product_list=False,
                can_grab=False,
                can_live_camera=False,
                can_real_time=False,
                can_manual_mode=False,
                can_auto_mode=False,
                can_change_result_time=False,
                can_change_sleep_time=False,
                can_toggle_setting=False,
                can_run_cycle=False,
            )
        return admin_profile
