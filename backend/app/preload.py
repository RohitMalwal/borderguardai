"""Preload local models for an OFFLINE demo.

PaddleOCR downloads its detection/recognition models on first use and caches
them locally (default: ``~/.paddleocr`` on macOS/Linux, ``%USERPROFILE%\\.paddleocr``
on Windows). Run this once WHILE ONLINE so the demo works with no network:

    cd backend
    python -m app.preload

It also verifies the vendored Haar face cascade loads. Exits 0 even if a
capability is unavailable — it reports status honestly rather than failing.
"""
from __future__ import annotations


def main() -> int:
    print("BorderGuard AI — preloading local models...\n")

    # --- OCR ---------------------------------------------------------------
    try:
        from app.services.ocr.paddle_service import preload as ocr_preload

        status = ocr_preload()
        if status.get("ocr"):
            print("  [OK]   PaddleOCR ready (models cached locally).")
            if status.get("warmup_warning"):
                print(f"         warmup note: {status['warmup_warning']}")
        else:
            print(f"  [SKIP] PaddleOCR unavailable: {status.get('error')}")
            print("         OCR-dependent stages will report 'engine_unavailable'.")
    except Exception as exc:  # noqa: BLE001
        print(f"  [SKIP] PaddleOCR preload failed: {exc}")

    # --- Face cascade ------------------------------------------------------
    try:
        from app.services.face.detector import _get_cascade

        print(
            "  [OK]   Haar face cascade loaded."
            if _get_cascade() is not None
            else "  [SKIP] Haar face cascade unavailable in this OpenCV build."
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [SKIP] Face cascade check failed: {exc}")

    print("\nDone. You can now run the demo offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
