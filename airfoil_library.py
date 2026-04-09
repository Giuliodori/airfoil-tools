"""Manta AirLab | Fabio Giuliodori — Explore https://duilio.cc."""

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
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.107, "alpha_zero_lift_deg": 0.1, "cl_max": 1.58, "cd0_base": 0.0074, "k_drag": 0.0054, "k_drag_neg": 0.0054, "k_drag_pos": 0.0054, "cl_cd_min": 0.15, "drag_bucket_half_width": 0.0, "drag_rise_linear": 0.0, "drag_rise_linear_neg": 0.0, "drag_rise_linear_pos": 0.0, "alpha_stall_deg": 16.3},
        ]
    },
    "0015": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.095, "alpha_zero_lift_deg": 0.0, "cl_max": 1.00, "cd0_base": 0.0210, "k_drag": 0.0175, "alpha_stall_deg": 10.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.1004, "alpha_zero_lift_deg": -0.75, "cl_max": 1.00, "cd0_base": 0.0113, "k_drag": 0.0200, "k_drag_neg": 0.0200, "k_drag_pos": 0.0200, "cl_cd_min": 0.075, "drag_bucket_half_width": 0.0, "drag_rise_linear": 0.0030, "drag_rise_linear_neg": 0.0030, "drag_rise_linear_pos": 0.0030, "pre_stall_curve_start": 0.86, "pre_stall_curve_strength": 0.22, "post_stall_decay_rate": 0.02, "post_stall_min_cl_ratio": 0.90, "stall_drag_factor": 0.052, "stall_drag_exponent": 1.25, "alpha_stall_deg": 10.8},
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
    "2414": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.093, "cl_alpha_neg_scale": 0.87, "cl_alpha_pos_scale": 1.16, "alpha_zero_lift_deg": 0.75, "cl_max": 1.05, "cd0_base": 0.0235, "k_drag": 0.0080, "k_drag_neg": 0.0157, "k_drag_pos": 0.0001, "cl_cd_min": -0.30, "drag_bucket_half_width": 0.03, "drag_rise_linear": 0.0140, "drag_rise_linear_neg": 0.0173, "drag_rise_linear_pos": 0.0108, "pre_stall_curve_start": 0.84, "pre_stall_curve_strength": 0.15, "alpha_stall_deg": 11.8},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.103, "alpha_zero_lift_deg": -1.3, "cl_max": 1.33, "cd0_base": 0.0150, "k_drag": 0.0138, "alpha_stall_deg": 14.6},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.105, "alpha_zero_lift_deg": -1.5, "cl_max": 1.48, "cd0_base": 0.0126, "k_drag": 0.0128, "alpha_stall_deg": 16.2},
        ]
    },
    "2415": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.101, "alpha_zero_lift_deg": -0.93, "cl_max": 1.15, "cd0_base": 0.0290, "k_drag": 0.0110, "k_drag_neg": 0.0218, "k_drag_pos": 0.0002, "cl_cd_min": -0.45, "drag_bucket_half_width": 0.18, "drag_rise_linear": 0.0060, "drag_rise_linear_neg": 0.0022, "drag_rise_linear_pos": 0.0092, "alpha_stall_deg": 13.7},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.103, "alpha_zero_lift_deg": -1.2, "cl_max": 1.34, "cd0_base": 0.0155, "k_drag": 0.0138, "cl_cd_min": 0.45, "drag_bucket_half_width": 0.10, "drag_rise_linear": 0.0030, "alpha_stall_deg": 14.8},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.105, "alpha_zero_lift_deg": -1.4, "cl_max": 1.48, "cd0_base": 0.0128, "k_drag": 0.0130, "cl_cd_min": 0.35, "drag_bucket_half_width": 0.08, "drag_rise_linear": 0.0020, "alpha_stall_deg": 16.3},
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
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.096, "alpha_zero_lift_deg": -4.0, "cl_max": 1.12, "cd0_base": 0.0120, "k_drag": 0.0120, "k_drag_neg": 0.0080, "k_drag_pos": 0.0160, "cl_cd_min": 0.55, "drag_bucket_half_width": 0.08, "drag_rise_linear": 0.0060, "drag_rise_linear_neg": 0.0040, "drag_rise_linear_pos": 0.0090, "alpha_stall_deg": 10.8},
            {"re_min": 2.0e5, "re_max": 9.0e5, "cl_alpha_per_deg": 0.1008, "alpha_zero_lift_deg": -4.23, "cl_max": 1.32, "cd0_base": 0.0074, "k_drag": 0.0115, "k_drag_neg": 0.0047, "k_drag_pos": 0.0185, "cl_cd_min": 0.65, "drag_bucket_half_width": 0.09, "drag_rise_linear": 0.0065, "drag_rise_linear_neg": 0.0036, "drag_rise_linear_pos": 0.0093, "pre_stall_curve_start": 0.62, "pre_stall_curve_strength": 0.55, "alpha_stall_deg": 16.6},
            {"re_min": 9.0e5, "re_max": 1.15e6, "cl_alpha_per_deg": 0.0997, "alpha_zero_lift_deg": -4.26, "cl_max": 1.33, "cd0_base": 0.0063, "k_drag": 0.0110, "k_drag_neg": 0.0032, "k_drag_pos": 0.0183, "cl_cd_min": 0.55, "drag_bucket_half_width": 0.14, "drag_rise_linear": 0.0115, "drag_rise_linear_neg": 0.0051, "drag_rise_linear_pos": 0.0181, "pre_stall_curve_start": 0.58, "pre_stall_curve_strength": 0.72, "alpha_stall_deg": 16.6},
            {"re_min": 1.15e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.1015, "alpha_zero_lift_deg": -4.13, "cl_max": 1.32, "cd0_base": 0.0054, "k_drag": 0.0110, "k_drag_neg": 0.0034, "k_drag_pos": 0.0186, "cl_cd_min": 0.61, "drag_bucket_half_width": 0.05, "drag_rise_linear": 0.0105, "drag_rise_linear_neg": 0.0041, "drag_rise_linear_pos": 0.0170, "pre_stall_curve_start": 0.58, "pre_stall_curve_strength": 0.68, "alpha_stall_deg": 16.5},
        ]
    },
    "4418": {
        "re_buckets": [
            {"re_min": 0, "re_max": 2.0e5, "cl_alpha_per_deg": 0.090, "alpha_zero_lift_deg": -2.5, "cl_max": 1.00, "cd0_base": 0.0145, "k_drag": 0.0145, "k_drag_neg": 0.0100, "k_drag_pos": 0.0180, "cl_cd_min": 0.30, "drag_bucket_half_width": 0.06, "drag_rise_linear": 0.0070, "drag_rise_linear_neg": 0.0040, "drag_rise_linear_pos": 0.0100, "alpha_stall_deg": 11.0},
            {"re_min": 2.0e5, "re_max": 1.0e6, "cl_alpha_per_deg": 0.091, "alpha_zero_lift_deg": -2.6, "cl_max": 1.22, "cd0_base": 0.0105, "k_drag": 0.0132, "k_drag_neg": 0.0070, "k_drag_pos": 0.0180, "cl_cd_min": 0.20, "drag_bucket_half_width": 0.08, "drag_rise_linear": 0.0060, "drag_rise_linear_neg": 0.0030, "drag_rise_linear_pos": 0.0090, "pre_stall_curve_start": 0.70, "pre_stall_curve_strength": 0.45, "alpha_stall_deg": 13.0},
            {"re_min": 1.0e6, "re_max": float("inf"), "cl_alpha_per_deg": 0.092, "alpha_zero_lift_deg": -2.8, "cl_max": 1.48, "cd0_base": 0.0081, "k_drag": 0.0125, "k_drag_neg": 0.0055, "k_drag_pos": 0.0175, "cl_cd_min": 0.32, "drag_bucket_half_width": 0.17, "drag_rise_linear": 0.0060, "drag_rise_linear_neg": 0.0030, "drag_rise_linear_pos": 0.0044, "pre_stall_curve_start": 0.84, "pre_stall_curve_strength": 0.22, "alpha_stall_deg": 18.0},
        ]
    },
}


AIRFOIL_FAMILY_ANCHORS = {
    "00": ["0008", "0012", "0015", "0020"],
    "24": ["2412", "2414", "2415"],
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
    for key in (
        "cl_alpha_per_deg",
        "alpha_zero_lift_deg",
        "cl_max",
        "cd0_base",
        "k_drag",
        "k_drag_neg",
        "k_drag_pos",
        "cl_cd_min",
        "drag_bucket_half_width",
        "drag_rise_linear",
        "drag_rise_linear_neg",
        "drag_rise_linear_pos",
        "pre_stall_curve_start",
        "pre_stall_curve_strength",
        "post_stall_decay_rate",
        "post_stall_min_cl_ratio",
        "stall_drag_factor",
        "stall_drag_exponent",
        "alpha_stall_deg",
    ):
        lv = float(low_bucket.get(key, 0.0))
        hv = float(high_bucket.get(key, 0.0))
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
        entry["k_drag_neg"] = max(0.0, float(entry.get("k_drag_neg", entry["k_drag"])) * (0.85 + 0.15 * thickness_ratio))
        entry["k_drag_pos"] = max(0.0, float(entry.get("k_drag_pos", entry["k_drag"])) * (0.85 + 0.15 * thickness_ratio))
        entry["cl_cd_min"] = float(entry.get("cl_cd_min", 0.0)) + 10.0 * camber_delta - 0.8 * abs(thickness_delta)
        entry["drag_bucket_half_width"] = max(0.0, float(entry.get("drag_bucket_half_width", 0.0)) + 1.5 * camber_delta + 1.0 * max(thickness_delta, 0.0))
        entry["drag_rise_linear"] = max(0.0, float(entry.get("drag_rise_linear", 0.0)) + 0.020 * max(camber_delta, 0.0))
        entry["drag_rise_linear_neg"] = max(0.0, float(entry.get("drag_rise_linear_neg", entry.get("drag_rise_linear", 0.0))) + 0.010 * max(camber_delta, 0.0))
        entry["drag_rise_linear_pos"] = max(0.0, float(entry.get("drag_rise_linear_pos", entry.get("drag_rise_linear", 0.0))) + 0.020 * max(camber_delta, 0.0))
        entry["pre_stall_curve_start"] = min(max(float(entry.get("pre_stall_curve_start", 1.0)) - 0.5 * max(camber_delta, 0.0), 0.0), 1.0)
        entry["pre_stall_curve_strength"] = min(max(float(entry.get("pre_stall_curve_strength", 0.0)) + 0.6 * max(camber_delta, 0.0), 0.0), 1.0)
        entry["post_stall_decay_rate"] = max(0.0, float(entry.get("post_stall_decay_rate", 0.12)) - 0.2 * max(camber_delta, 0.0))
        entry["post_stall_min_cl_ratio"] = min(max(float(entry.get("post_stall_min_cl_ratio", 0.18)) + 0.8 * max(camber_delta, 0.0), 0.0), 1.0)
        entry["stall_drag_factor"] = max(0.0, float(entry.get("stall_drag_factor", 0.015)) + 0.020 * max(thickness_delta, 0.0))
        entry["stall_drag_exponent"] = max(0.0, float(entry.get("stall_drag_exponent", 1.25)))
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
    k_drag_neg = k_drag * (1.15 + 0.8 * m)
    k_drag_pos = k_drag * max(0.45, 0.9 - 1.5 * m)

    cl_cd_min = max(0.0, min(0.9, 0.18 * re_factor + 12.0 * m - 0.6 * abs(t - 0.12)))
    drag_bucket_half_width = max(0.0, min(0.35, 0.02 + 1.8 * m + 0.35 * max(t - 0.10, 0.0) + 0.04 * (1.0 - re_factor)))
    drag_rise_linear = max(0.0, min(0.020, 0.010 * (1.0 - re_factor) + 0.015 * m))
    drag_rise_linear_neg = drag_rise_linear * (0.8 + 0.8 * m)
    drag_rise_linear_pos = drag_rise_linear * (1.0 + 1.2 * m)
    pre_stall_curve_start = min(max(0.88 - 3.0 * m - 0.10 * re_factor, 0.45), 1.0)
    pre_stall_curve_strength = min(max(0.15 + 4.0 * m + 0.10 * re_factor, 0.0), 0.9)
    post_stall_decay_rate = max(0.02, 0.12 - 0.04 * re_factor)
    post_stall_min_cl_ratio = min(max(0.18 + 0.10 * max(t - 0.12, 0.0) + 0.08 * m, 0.18), 0.92)
    stall_drag_factor = 0.015 + 0.030 * max(t - 0.12, 0.0) + 0.010 * (1.0 - re_factor)
    stall_drag_exponent = 1.25

    alpha_stall = 10.0 + 80.0 * max(t - 0.10, 0.0) + 45.0 * m + 3.0 * re_factor
    alpha_stall = max(8.0, min(18.0, alpha_stall))

    return {
        "cl_alpha_per_deg": cl_alpha,
        "alpha_zero_lift_deg": alpha_zero,
        "cl_max": cl_max,
        "cd0_base": cd0_base,
        "k_drag": k_drag,
        "k_drag_neg": k_drag_neg,
        "k_drag_pos": k_drag_pos,
        "cl_cd_min": cl_cd_min,
        "drag_bucket_half_width": drag_bucket_half_width,
        "drag_rise_linear": drag_rise_linear,
        "drag_rise_linear_neg": drag_rise_linear_neg,
        "drag_rise_linear_pos": drag_rise_linear_pos,
        "pre_stall_curve_start": pre_stall_curve_start,
        "pre_stall_curve_strength": pre_stall_curve_strength,
        "post_stall_decay_rate": post_stall_decay_rate,
        "post_stall_min_cl_ratio": post_stall_min_cl_ratio,
        "stall_drag_factor": stall_drag_factor,
        "stall_drag_exponent": stall_drag_exponent,
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
    if overrides.get("k_drag_neg") is not None:
        base["k_drag_neg"] = max(0.0, float(overrides["k_drag_neg"]))
    if overrides.get("k_drag_pos") is not None:
        base["k_drag_pos"] = max(0.0, float(overrides["k_drag_pos"]))
    if overrides.get("cl_cd_min") is not None:
        base["cl_cd_min"] = float(overrides["cl_cd_min"])
    if overrides.get("drag_bucket_half_width") is not None:
        base["drag_bucket_half_width"] = max(0.0, float(overrides["drag_bucket_half_width"]))
    if overrides.get("drag_rise_linear") is not None:
        base["drag_rise_linear"] = max(0.0, float(overrides["drag_rise_linear"]))
    if overrides.get("drag_rise_linear_neg") is not None:
        base["drag_rise_linear_neg"] = max(0.0, float(overrides["drag_rise_linear_neg"]))
    if overrides.get("drag_rise_linear_pos") is not None:
        base["drag_rise_linear_pos"] = max(0.0, float(overrides["drag_rise_linear_pos"]))
    if overrides.get("pre_stall_curve_start") is not None:
        base["pre_stall_curve_start"] = min(max(float(overrides["pre_stall_curve_start"]), 0.0), 1.0)
    if overrides.get("pre_stall_curve_strength") is not None:
        base["pre_stall_curve_strength"] = min(max(float(overrides["pre_stall_curve_strength"]), 0.0), 1.0)
    if overrides.get("post_stall_decay_rate") is not None:
        base["post_stall_decay_rate"] = max(0.0, float(overrides["post_stall_decay_rate"]))
    if overrides.get("post_stall_min_cl_ratio") is not None:
        base["post_stall_min_cl_ratio"] = min(max(float(overrides["post_stall_min_cl_ratio"]), 0.0), 1.0)
    if overrides.get("stall_drag_factor") is not None:
        base["stall_drag_factor"] = max(0.0, float(overrides["stall_drag_factor"]))
    if overrides.get("stall_drag_exponent") is not None:
        base["stall_drag_exponent"] = max(0.0, float(overrides["stall_drag_exponent"]))
    if overrides.get("cl_max") is not None:
        base["cl_max"] = max(0.1, float(overrides["cl_max"]))
    if overrides.get("alpha_zero_lift_deg") is not None:
        base["alpha_zero_lift_deg"] = float(overrides["alpha_zero_lift_deg"])

    base.setdefault("cl_cd_min", 0.0)
    base.setdefault("drag_bucket_half_width", 0.0)
    base.setdefault("drag_rise_linear", 0.0)
    base.setdefault("k_drag_neg", base["k_drag"])
    base.setdefault("k_drag_pos", base["k_drag"])
    base.setdefault("drag_rise_linear_neg", base["drag_rise_linear"])
    base.setdefault("drag_rise_linear_pos", base["drag_rise_linear"])
    base.setdefault("pre_stall_curve_start", 1.0)
    base.setdefault("pre_stall_curve_strength", 0.0)
    base.setdefault("post_stall_decay_rate", 0.12)
    base.setdefault("post_stall_min_cl_ratio", 0.18)
    base.setdefault("stall_drag_factor", 0.015)
    base.setdefault("stall_drag_exponent", 1.25)
    return base
