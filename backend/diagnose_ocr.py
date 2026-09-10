#!/usr/bin/env python3
"""
Diagnostic script: Run PaddleOCR on a passport image and dump raw output
with bounding boxes. Analyze label/value detection.
"""
import sys
import re
import os

sys.path.insert(0, os.path.dirname(__file__))

import cv2

def center(box):
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    return (sum(xs)/len(xs), sum(ys)/len(ys))

def main():
    if len(sys.argv) < 2:
        image_path = "/Volumes/BE Huxtler/Projects/bg/storage/uploads/d0f71ec4f86f/original.png"
    else:
        image_path = sys.argv[1]

    print(f"=== Diagnosing: {image_path} ===\n")
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        print(f"ERROR: Could not read image from {image_path}")
        sys.exit(1)
    print(f"Image shape: {image_bgr.shape}")

    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("ERROR: PaddleOCR not installed")
        sys.exit(1)

    print("Initializing PaddleOCR...")
    try:
        engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    except Exception as e:
        print(f"WARNING: {e}, trying minimal...")
        engine = PaddleOCR(lang='en')

    print("Running OCR...")
    rgb = image_bgr[:, :, ::-1]
    try:
        result = engine.ocr(rgb, cls=True)
    except TypeError:
        result = engine.ocr(rgb)

    lines = []
    if result:
        page = result[0] if len(result) == 1 and isinstance(result[0], list) else result
        for entry in page or []:
            try:
                box = entry[0]
                text, conf = entry[1][0], float(entry[1][1])
                poly = [[float(p[0]), float(p[1])] for p in box]
                cx, cy = center(poly)
                lines.append({"text": text, "conf": round(conf, 4), "box": poly, "cx": round(cx, 1), "cy": round(cy, 1)})
            except Exception as e:
                print(f"  Skipping entry: {e}")

    lines_sorted = sorted(lines, key=lambda l: (l["cy"], l["cx"]))
    print(f"\n=== RAW OCR OUTPUT ({len(lines)} lines) ===")
    for i, ln in enumerate(lines_sorted):
        print(f"  [{i:2d}] cy={ln['cy']:6.1f} cx={ln['cx']:6.1f} conf={ln['conf']:.3f}  text={repr(ln['text'])}")

    # Label vocab including missing fields
    LABELS = {
        "surname": ["surname", "nom", "apellido", "familyname", "cognome", "nachname", "prijmeni"],
        "given_names": ["givenname", "givennames", "prenom", "forename", "nombre", "vorname", "jmena", "jmeno", "given"],
        "document_number": ["passportno", "passportnumber", "documentno", "docno", "passno", "passnr", "cislopasu", "passeportno", "numero"],
        "nationality": ["nationality", "nationalite", "nacionalidad", "staatsang", "angeh", "statniprisl", "statni", "nationalit"],
        "date_of_birth": ["dateofbirth", "birth", "naissance", "nacimiento", "geburt", "datumnaroz", "narozeni", "dob"],
        "sex": ["sex", "sexe", "sexo", "gender", "geschlecht", "pohlavi"],
        "expiry_date": ["dateofexpiry", "expiry", "expiration", "expr", "gultig", "gueltig", "gutig", "ablauf", "validuntil", "platnost", "dateexpir"],
        "date_of_issue": ["dateofissue", "issue", "issuy", "delivrance", "vydani", "dateissue"],
        "place_of_birth": ["placeofbirth", "lieudenaissance", "geburtsort", "mistenarozeni"],
        "authority": ["authority", "autorite", "behorde", "uradvydani", "urad"],
        "issued_at": ["issuedat", "faita", "fait", "issueplace"],
    }

    def _norm(text):
        return re.sub(r"[^a-z]", "", text.lower())

    def _label_field(text):
        n = _norm(text)
        if len(n) < 3:
            return None
        best_field, best_len = None, 0
        for field_key, keywords in LABELS.items():
            for kw in keywords:
                if kw in n and len(kw) > best_len:
                    best_field, best_len = field_key, len(kw)
        return best_field

    print("\n=== LABEL DETECTION ===")
    label_lines = {}
    for ln in lines_sorted:
        fk = _label_field(ln["text"])
        if fk:
            print(f"  LABEL '{ln['text']}' -> {fk}  (cy={ln['cy']:.1f})")
            if fk not in label_lines:
                label_lines[fk] = ln
    print(f"\nDetected labels: {list(label_lines.keys())}")
    missing = [k for k in LABELS if k not in label_lines]
    print(f"MISSING labels:  {missing}")

    DATE_RE = re.compile(r"\b(\d{1,2})[\s./\-]{0,2}([A-Z]{3}|\d{1,2})[\s./\-]{0,2}(\d{2,4})\b", re.IGNORECASE)
    MONTHS = {"JAN":"01","FEB":"02","MAR":"03","APR":"04","MAY":"05","JUN":"06",
               "JUL":"07","AUG":"08","SEP":"09","OCT":"10","NOV":"11","DEC":"12"}

    def _is_dateish(text):
        return DATE_RE.search(text.upper()) is not None

    print("\n=== ALL DATES DETECTED ===")
    for ln in lines_sorted:
        m = DATE_RE.search(ln["text"].upper())
        if m:
            day, mon, year = m.groups()
            mon_n = MONTHS.get(mon.upper(), mon)
            print(f"  cy={ln['cy']:.1f} text='{ln['text']}' -> day={day} mon={mon_n} year={year}")

    # MRZ band
    print("\n=== MRZ BAND DIAGNOSTIC ===")
    h, w = image_bgr.shape[:2]
    y0 = int(h * 0.72)
    print(f"MRZ band: y={y0} to y={h} (image h={h})")
    band = image_bgr[y0:h, 0:w]
    scale = 4
    import cv2 as _cv2
    band_scaled = _cv2.resize(band, (w*scale, band.shape[0]*scale), interpolation=_cv2.INTER_CUBIC)
    try:
        result_band = engine.ocr(band_scaled[:, :, ::-1], cls=True)
        band_lines = []
        if result_band:
            page = result_band[0] if len(result_band)==1 and isinstance(result_band[0], list) else result_band
            for entry in page or []:
                try:
                    text, conf = entry[1][0], float(entry[1][1])
                    band_lines.append({"text": text, "conf": round(conf, 4)})
                except: pass
        for bl in sorted(band_lines, key=lambda x: x["cy"] if "cy" in x else 0):
            print(f"  conf={bl['conf']:.3f} text='{bl['text']}'")
    except Exception as e:
        print(f"MRZ band OCR failed: {e}")

    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
