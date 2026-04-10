from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.application.contracts.runtime import PreviewFrameResult


@dataclass
class GrabPreviewUseCase:
    camera: CameraAdapter

    def execute(self) -> PreviewFrameResult:
        try:
            camera_connected = self.camera.is_connected()
            if not camera_connected:
                camera_connected = bool(self.camera.connect())
        except Exception as exc:
            return PreviewFrameResult(
                image_frame=None,
                camera_connected=False,
                message=f"Camera connect failed: {exc}",
            )

        if not camera_connected:
            return PreviewFrameResult(
                image_frame=None,
                camera_connected=False,
                message="Camera is not connected.",
            )

        try:
            image_frame = self.camera.grab()
        except Exception as exc:
            return PreviewFrameResult(
                image_frame=None,
                camera_connected=camera_connected,
                message=f"Camera grab failed: {exc}",
            )
        if image_frame is None:
            return PreviewFrameResult(
                image_frame=None,
                camera_connected=camera_connected,
                message="Camera frame unavailable.",
            )
        return PreviewFrameResult(
            image_frame=image_frame,
            camera_connected=camera_connected,
            message="Preview frame captured.",
        )
