from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import cv2

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / "vendor_onnxocr"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from link_detector import contains_link  # noqa: E402
from onnxocr.onnx_paddleocr import ONNXPaddleOcr  # noqa: E402

_ocr_engine: ONNXPaddleOcr | None = None
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def get_ocr_engine() -> ONNXPaddleOcr:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)
    return _ocr_engine


def normalize_ocr_result(raw: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not raw:
        return rows
    page = raw[0] if isinstance(raw, list) and raw else []
    for item in page or []:
        if len(item) < 2:
            continue
        box, payload = item
        text = payload[0] if payload else ""
        score = payload[1] if payload and len(payload) > 1 else None
        rows.append(
            {
                "text": text,
                "score": round(float(score), 4) if score is not None else None,
                "box": box,
            }
        )
    return rows


def run_ocr_on_image_path(path: str | Path) -> tuple[list[dict[str, Any]], str]:
    image_path = Path(path)
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"不支持的图片格式：{image_path.suffix}")

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("图片读取失败，请确认文件存在且未损坏")

    ocr = get_ocr_engine()
    result = ocr.ocr(img)
    data = normalize_ocr_result(result)
    full_text = "\n".join(row["text"] for row in data if row["text"])
    return data, full_text


def detect_links_from_rows(rows: list[dict[str, Any]], full_text: str) -> tuple[bool, list[str]]:
    return contains_link([row.get("text", "") for row in rows] + [full_text])
