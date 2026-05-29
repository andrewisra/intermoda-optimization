from __future__ import annotations


def recommend_dwell_extension(required_hold_minutes: float, max_extension_minutes: float = 3.0) -> dict:
    required_hold_minutes = float(required_hold_minutes)
    if required_hold_minutes <= 0:
        return {"extension_minutes":0.0,"feasible":True,"reason":"Tidak perlu tambahan dwell time."}
    if required_hold_minutes <= max_extension_minutes:
        return {"extension_minutes":round(required_hold_minutes,2),"feasible":True,"reason":"Tambahan dwell time masih dalam batas operasional."}
    return {"extension_minutes":0.0,"feasible":False,"reason":"Tambahan dwell time melebihi batas. Gunakan moda berikutnya."}
