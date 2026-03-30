"""Manta AirLab by Duilio.cc — Fabio Giuliodori."""

import math


AIRFOIL_DB = {
    "0008": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.095, "alpha_zero_lift_deg": 0.0, "cl_max": 0.95, "cd0_base": 0.0170, "k_drag": 0.0150, "alpha_stall_deg": 9.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.098, "alpha_zero_lift_deg": 0.0, "cl_max": 1.08, "cd0_base": 0.0140, "k_drag": 0.0130, "alpha_stall_deg": 11.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.100, "alpha_zero_lift_deg": 0.0, "cl_max": 1.16, "cd0_base": 0.0120, "k_drag": 0.0120, "alpha_stall_deg": 12.0},
        ]
    },
    "0012": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.097, "alpha_zero_lift_deg": 0.0, "cl_max": 1.00, "cd0_base": 0.0200, "k_drag": 0.0160, "alpha_stall_deg": 10.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.101, "alpha_zero_lift_deg": 0.0, "cl_max": 1.25, "cd0_base": 0.0150, "k_drag": 0.0140, "alpha_stall_deg": 13.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.104, "alpha_zero_lift_deg": 0.0, "cl_max": 1.38, "cd0_base": 0.0125, "k_drag": 0.0130, "alpha_stall_deg": 15.0},
        ]
    },
    "0015": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.095, "alpha_zero_lift_deg": 0.0, "cl_max": 1.00, "cd0_base": 0.0210, "k_drag": 0.0175, "alpha_stall_deg": 10.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.100, "alpha_zero_lift_deg": 0.0, "cl_max": 1.25, "cd0_base": 0.0165, "k_drag": 0.0150, "alpha_stall_deg": 13.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.103, "alpha_zero_lift_deg": 0.0, "cl_max": 1.38, "cd0_base": 0.0140, "k_drag": 0.0140, "alpha_stall_deg": 15.0},
        ]
    },
    "0020": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.093, "alpha_zero_lift_deg": 0.0, "cl_max": 0.95, "cd0_base": 0.0240, "k_drag": 0.0190, "alpha_stall_deg": 9.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.098, "alpha_zero_lift_deg": 0.0, "cl_max": 1.18, "cd0_base": 0.0190, "k_drag": 0.0170, "alpha_stall_deg": 12.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.101, "alpha_zero_lift_deg": 0.0, "cl_max": 1.30, "cd0_base": 0.0160, "k_drag": 0.0160, "alpha_stall_deg": 14.0},
        ]
    },
    "2412": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.095, "alpha_zero_lift_deg": -1.8, "cl_max": 1.10, "cd0_base": 0.0170, "k_drag": 0.0160, "alpha_stall_deg": 11.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.100, "alpha_zero_lift_deg": -2.0, "cl_max": 1.35, "cd0_base": 0.0135, "k_drag": 0.0140, "alpha_stall_deg": 14.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.103, "alpha_zero_lift_deg": -2.2, "cl_max": 1.50, "cd0_base": 0.0115, "k_drag": 0.0130, "alpha_stall_deg": 16.0},
        ]
    },
    "4412": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.094, "alpha_zero_lift_deg": -3.0, "cl_max": 1.15, "cd0_base": 0.0185, "k_drag": 0.0170, "alpha_stall_deg": 10.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.099, "alpha_zero_lift_deg": -3.2, "cl_max": 1.45, "cd0_base": 0.0145, "k_drag": 0.0150, "alpha_stall_deg": 13.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.102, "alpha_zero_lift_deg": -3.4, "cl_max": 1.60, "cd0_base": 0.0125, "k_drag": 0.0140, "alpha_stall_deg": 15.0},
        ]
    },
    "4415": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.093, "alpha_zero_lift_deg": -3.0, "cl_max": 1.10, "cd0_base": 0.0200, "k_drag": 0.0180, "alpha_stall_deg": 10.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.098, "alpha_zero_lift_deg": -3.2, "cl_max": 1.40, "cd0_base": 0.0160, "k_drag": 0.0160, "alpha_stall_deg": 13.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.101, "alpha_zero_lift_deg": -3.4, "cl_max": 1.55, "cd0_base": 0.0135, "k_drag": 0.0150, "alpha_stall_deg": 15.0},
        ]
    },
}


AIRFOIL_FAMILY_ANCHORS = {
    "00": ["0008", "0012", "0015", "0020"],
    "24": ["2412"],
    "44": ["4412", "4415"],
}


def parse_naca4_code(code: str):
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA code must have 4 digits, for example 2412 or 0012.")
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:4]) / 100.0
    return {"code": code, "m": m, "p": p, "t": t, "is_symmetric": (code[:2] == "00")}


def _interpolate_bucket_pair(low_bucket, high_bucket, blend: float):
    result = {
        "re_min": low_bucket["re_min"],
        "re_max": low_bucket["re_max"],
    }
    for key in ("cl_alpha_per_deg", "alpha_zero_lift_deg", "cl_max", "cd0_base", "k_drag", "alpha_stall_deg"):
        lv = float(low_bucket[key])
        hv = float(high_bucket[key])
        result[key] = lv + (hv - lv) * blend
    return result


def _build_scaled_family_buckets(base_code: str, target_code: str):
    base_geom = parse_naca4_code(base_code)
    target_geom = parse_naca4_code(target_code)
    t_base = max(base_geom["t"], 1e-6)
    t_target = target_geom["t"]

    thickness_ratio = t_target / t_base
    thickness_delta = t_target - t_base
    camber_delta = target_geom["m"] - base_geom["m"]
    camber_pos_delta = target_geom["p"] - base_geom["p"]

    scaled = []
    for bucket in AIRFOIL_DB[base_code]["re_buckets"]:
        entry = dict(bucket)
        entry["cl_alpha_per_deg"] = max(0.088, min(0.108, entry["cl_alpha_per_deg"] - 0.010 * thickness_delta))
        entry["alpha_zero_lift_deg"] = entry["alpha_zero_lift_deg"] - 85.0 * camber_delta + 0.8 * (0.4 - target_geom["p"]) - 0.8 * (0.4 - base_geom["p"])
        entry["cl_max"] = max(0.9, min(1.9, entry["cl_max"] + 10.0 * camber_delta - 1.5 * abs(thickness_delta)))
        entry["cd0_base"] = max(0.008, min(0.032, entry["cd0_base"] + 0.010 * abs(thickness_delta) + 0.006 * thickness_delta ** 2))
        entry["k_drag"] = max(0.010, min(0.028, entry["k_drag"] * (0.85 + 0.15 * thickness_ratio)))
        entry["alpha_stall_deg"] = max(8.0, min(18.0, entry["alpha_stall_deg"] + 70.0 * thickness_delta + 45.0 * camber_delta - 4.0 * camber_pos_delta))
        scaled.append(entry)
    return scaled


def build_interpolated_airfoil_entry(code: str):
    family = code[:2]
    anchors = AIRFOIL_FAMILY_ANCHORS.get(family)
    if not anchors:
        return None

    if code in AIRFOIL_DB:
        return AIRFOIL_DB[code]

    target_thickness = int(code[2:4])
    anchor_thicknesses = sorted(int(anchor[2:4]) for anchor in anchors)

    if target_thickness <= anchor_thicknesses[0]:
        base_code = f"{family}{anchor_thicknesses[0]:02d}"
        return {"re_buckets": _build_scaled_family_buckets(base_code, code)}

    if target_thickness >= anchor_thicknesses[-1]:
        base_code = f"{family}{anchor_thicknesses[-1]:02d}"
        return {"re_buckets": _build_scaled_family_buckets(base_code, code)}

    low_t = None
    high_t = None
    for idx in range(len(anchor_thicknesses) - 1):
        left = anchor_thicknesses[idx]
        right = anchor_thicknesses[idx + 1]
        if left <= target_thickness <= right:
            low_t = left
            high_t = right
            break

    if low_t is None or high_t is None:
        return None

    low_code = f"{family}{low_t:02d}"
    high_code = f"{family}{high_t:02d}"
    low_scaled = _build_scaled_family_buckets(low_code, code)
    high_scaled = _build_scaled_family_buckets(high_code, code)
    blend = (target_thickness - low_t) / max(high_t - low_t, 1)

    buckets = [
        _interpolate_bucket_pair(low_bucket, high_bucket, blend)
        for low_bucket, high_bucket in zip(low_scaled, high_scaled)
    ]
    return {"re_buckets": buckets}


def estimate_fallback_airfoil_parameters(code: str, reynolds: float):
    geom = parse_naca4_code(code)
    m = geom["m"]
    p = geom["p"]
    t = geom["t"]

    re_factor = min(max((math.log10(max(reynolds, 5.0e4)) - 5.0) / 2.0, 0.0), 1.0)

    cl_alpha = 0.094 + 0.010 * (1.0 - abs(t - 0.12) / 0.12)
    cl_alpha = max(0.088, min(0.106, cl_alpha))
    cl_alpha += 0.004 * re_factor

    if geom["is_symmetric"]:
        alpha_zero = 0.0
    else:
        camber_pos_term = (0.4 - p) * 0.8 if p > 0 else 0.0
        alpha_zero = -(85.0 * m) + camber_pos_term

    cl_max = 1.0 + 10.0 * m + 0.25 * re_factor - 2.0 * abs(t - 0.12)
    cl_max = max(0.9, min(1.8, cl_max))

    cd0_base = 0.012 + 0.040 * (t - 0.10) ** 2 + 0.006 * (1.0 - re_factor) + 0.005 * m
    cd0_base = max(0.008, min(0.032, cd0_base))

    k_drag = 0.011 + 0.020 * max(t - 0.08, 0.0) + 0.004 * (1.0 - re_factor)
    k_drag = max(0.010, min(0.028, k_drag))

    alpha_stall = 10.0 + 80.0 * max(t - 0.10, 0.0) + 45.0 * m + 3.0 * re_factor
    alpha_stall = max(8.0, min(18.0, alpha_stall))

    return {
        "cl_alpha_per_deg": cl_alpha,
        "alpha_zero_lift_deg": alpha_zero,
        "cl_max": cl_max,
        "cd0_base": cd0_base,
        "k_drag": k_drag,
        "alpha_stall_deg": alpha_stall,
        "source": "fallback",
    }


def get_airfoil_parameters(code: str, reynolds: float, use_internal_library: bool = True, overrides=None):
    overrides = overrides or {}
    base = None
    library_entry = None

    if use_internal_library:
        library_entry = AIRFOIL_DB.get(code)
        if library_entry is None:
            library_entry = build_interpolated_airfoil_entry(code)

    if library_entry is not None:
        for bucket in library_entry["re_buckets"]:
            if bucket["re_min"] <= reynolds < bucket["re_max"]:
                base = dict(bucket)
                base["source"] = "library"
                break
        if base is None:
            base = dict(library_entry["re_buckets"][-1])
            base["source"] = "library"
    else:
        base = estimate_fallback_airfoil_parameters(code, reynolds)

    if overrides.get("cd0") is not None:
        base["cd0_base"] = max(0.0001, float(overrides["cd0"]))
    if overrides.get("k_drag") is not None:
        base["k_drag"] = max(0.0001, float(overrides["k_drag"]))
    if overrides.get("cl_max") is not None:
        base["cl_max"] = max(0.1, float(overrides["cl_max"]))
    if overrides.get("alpha_zero_lift_deg") is not None:
        base["alpha_zero_lift_deg"] = float(overrides["alpha_zero_lift_deg"])

    return base
