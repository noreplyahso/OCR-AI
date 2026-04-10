from drb_inspection.application.contracts.inspection import InspectionTaskRequest, InspectionTaskType


def test_inspection_task_request_fields() -> None:
    request = InspectionTaskRequest(
        task_id="ocr_1",
        task_type=InspectionTaskType.OCR,
        image_ref="frame://1",
        roi_name="label_roi",
    )
    assert request.task_id == "ocr_1"
    assert request.task_type == InspectionTaskType.OCR
    assert request.roi_name == "label_roi"
