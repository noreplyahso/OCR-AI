from drb_inspection.adapters.db.models import ProductRecord, UserRecord
from drb_inspection.app.container import build_container
from drb_inspection.application.contracts.context import LoginCommand, ProductCatalogEntry


def test_login_user_success_sets_session_user_and_resets_attempt() -> None:
    container = build_container()
    container.repository.save_user(
        UserRecord(user_name="operator1", password_hash="secret", role="Operator", attempt=2)
    )

    result = container.login_user.execute(LoginCommand(user_name="operator1", password="secret"))

    assert result.success is True
    assert result.user is not None
    assert result.user.attempt == 0
    assert result.session is not None
    assert result.session.user_name == "operator1"


def test_login_user_locks_non_admin_after_third_failed_attempt() -> None:
    container = build_container()
    container.repository.save_user(
        UserRecord(user_name="operator2", password_hash="secret", role="Operator", attempt=2)
    )

    result = container.login_user.execute(LoginCommand(user_name="operator2", password="wrong"))

    assert result.success is False
    assert result.user is not None
    assert result.user.active == "Inactive"
    assert "locked" in result.message.lower()


def test_sync_products_upserts_catalog_entries() -> None:
    container = build_container()

    result = container.sync_products.execute(
        [
            ProductCatalogEntry(product_name="IS35R-100", model_path="models/is35r_100.pt"),
            ProductCatalogEntry(product_name="IS35R-200", model_path="models/is35r_200.pt", exposure=4200),
        ]
    )

    assert len(result.products) == 2
    assert container.repository.get_product("IS35R-100").model_path == "models/is35r_100.pt"
    assert container.repository.get_product("IS35R-200").exposure == 4200


def test_select_product_updates_session_and_returns_product_context() -> None:
    container = build_container()
    container.repository.upsert_product(
        ProductRecord(
            product_name="IS35R-300",
            model_path="models/is35r_300.pt",
            exposure=4100,
            default_number=180,
            threshold_accept=0.7,
            threshold_mns=0.3,
        )
    )

    result = container.select_product.execute("IS35R-300")

    assert result.product.product_name == "IS35R-300"
    assert result.product.model_path == "models/is35r_300.pt"
    assert result.session.product_name == "IS35R-300"


def test_save_and_load_session_settings_roundtrip() -> None:
    container = build_container()

    save_result = container.save_session_settings.execute(
        result_time=250,
        sleep_time=15,
        zoom_factor=1.5,
        plc_ip="192.168.0.10",
        plc_port="502",
        plc_protocol="modbus_tcp",
        offset_x=12,
        offset_y=34,
        image_width=1280,
        image_height=1024,
    )
    load_result = container.load_session_settings.execute()

    assert save_result.session.result_time == 250
    assert load_result.session.sleep_time == 15
    assert load_result.session.plc_ip == "192.168.0.10"
    assert load_result.session.image_width == 1280
    assert load_result.session.plc_protocol == "modbus_tcp"


def test_save_product_settings_updates_current_product_configuration() -> None:
    container = build_container()
    container.repository.upsert_product(
        ProductRecord(
            product_name="IS35R-500",
            model_path="models/old.pt",
            exposure=3200,
            default_number=120,
            threshold_accept=0.4,
            threshold_mns=0.4,
        )
    )
    container.repository.update_session(product_name="IS35R-500")

    result = container.save_product_settings.execute(
        model_path="models/new.pt",
        exposure=4100,
        default_number=200,
        threshold_accept=0.8,
        threshold_mns=0.2,
    )

    assert result.product.model_path == "models/new.pt"
    assert result.product.exposure == 4100
    assert result.product.default_number == 200
    assert result.product.threshold_accept == 0.8
    assert result.product.threshold_mns == 0.2
    assert container.repository.get_product("IS35R-500").model_path == "models/new.pt"


def test_save_and_load_session_settings_roundtrip_includes_roi_coordinates() -> None:
    container = build_container()

    save_result = container.save_session_settings.execute(
        roi_x1=801,
        roi_x2=1301,
        roi_x3=1801,
        roi_x4=2301,
        roi_x5=2801,
        roi_y1=1201,
        roi_y2=1202,
        roi_y3=1203,
        roi_y4=1204,
        roi_y5=1205,
    )
    load_result = container.load_session_settings.execute()

    assert save_result.session.roi_x1 == 801
    assert load_result.session.roi_x5 == 2801
    assert load_result.session.roi_y3 == 1203


def test_move_session_roi_updates_all_targets_when_requested() -> None:
    container = build_container()

    result = container.move_session_roi.execute(direction="down", move_all=True)

    assert result.session.roi_y1 == 1190
    assert result.session.roi_y5 == 1190


def test_move_session_roi_requires_valid_single_target() -> None:
    container = build_container()

    try:
        container.move_session_roi.execute(direction="left", roi_index=7, move_all=False)
    except ValueError as exc:
        assert "ROI index" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid ROI index")
