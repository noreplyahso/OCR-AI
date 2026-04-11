from drb_inspection.adapters.db.models import ProductRecord, UserRecord
from drb_inspection.app.container import build_container
from drb_inspection.application.contracts.context import LoginCommand


def test_supervisor_access_profile_disables_authentication_and_report_only() -> None:
    container = build_container()

    profile = container.get_access_profile.execute("Supervisor")

    assert profile.can_open_authentication is False
    assert profile.can_open_report is False
    assert profile.can_load_model is True
    assert profile.can_real_time is True
    assert profile.can_run_cycle is True


def test_load_main_screen_context_uses_session_user_and_role() -> None:
    container = build_container()
    container.repository.save_user(
        UserRecord(user_name="supervisor1", password_hash="pw", role="Supervisor")
    )
    container.repository.upsert_product(
        ProductRecord(product_name="PRODUCT-A", model_path="models/product_a.pt")
    )
    container.repository.update_session(product_name="PRODUCT-A")
    container.login_user.execute(LoginCommand(user_name="supervisor1", password="pw"))

    context = container.load_main_screen_context.execute()

    assert context.current_user_name == "supervisor1"
    assert context.current_role == "Supervisor"
    assert "PRODUCT-A" in context.available_products
    assert context.access_profile.can_open_authentication is False
    assert context.access_profile.can_load_model is True
