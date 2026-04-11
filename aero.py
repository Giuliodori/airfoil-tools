"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Aerodynamic helper module for Manta AirLab.
Provides Reynolds computation, quick lift/drag coefficient estimation, and
force calculations used by both the GUI and CLI.
"""

from __future__ import annotations

import math


def compute_reynolds(velocity: float, chord: float, density: float, viscosity: float):
    if viscosity <= 0:
        raise ValueError("Dynamic viscosity must be greater than zero.")
    if chord <= 0:
        raise ValueError("Chord must be greater than zero.")
    return density * velocity * chord / viscosity


def compute_cl_cd(alpha_deg: float, params):
    cl_alpha = float(params["cl_alpha_per_deg"])
    cl_alpha_neg_scale = max(float(params.get("cl_alpha_neg_scale", 1.0)), 0.0)
    cl_alpha_pos_scale = max(float(params.get("cl_alpha_pos_scale", 1.0)), 0.0)
    alpha_zero = float(params["alpha_zero_lift_deg"])
    cl_max = max(float(params["cl_max"]), 0.05)
    cd0 = max(float(params["cd0_base"]), 0.0001)
    k_drag = max(float(params["k_drag"]), 0.0001)
    cl_cd_min = float(params.get("cl_cd_min", 0.0))
    drag_bucket_half_width = max(float(params.get("drag_bucket_half_width", 0.0)), 0.0)
    drag_rise_linear = max(float(params.get("drag_rise_linear", 0.0)), 0.0)
    k_drag_neg = max(float(params.get("k_drag_neg", k_drag)), 0.0)
    k_drag_pos = max(float(params.get("k_drag_pos", k_drag)), 0.0)
    drag_rise_linear_neg = max(float(params.get("drag_rise_linear_neg", drag_rise_linear)), 0.0)
    drag_rise_linear_pos = max(float(params.get("drag_rise_linear_pos", drag_rise_linear)), 0.0)
    pre_stall_curve_start = min(max(float(params.get("pre_stall_curve_start", 1.0)), 0.0), 1.0)
    pre_stall_curve_strength = min(max(float(params.get("pre_stall_curve_strength", 0.0)), 0.0), 1.0)
    post_stall_decay_rate = max(float(params.get("post_stall_decay_rate", 0.12)), 0.0)
    post_stall_min_cl_ratio = min(max(float(params.get("post_stall_min_cl_ratio", 0.18)), 0.0), 1.0)
    stall_drag_factor = max(float(params.get("stall_drag_factor", 0.015)), 0.0)
    stall_drag_exponent = max(float(params.get("stall_drag_exponent", 1.25)), 0.0)
    alpha_stall = max(float(params["alpha_stall_deg"]), 1.0)

    alpha_eff = alpha_deg - alpha_zero
    cl_alpha_local = cl_alpha * (cl_alpha_neg_scale if alpha_eff < 0 else cl_alpha_pos_scale)
    cl_linear = cl_alpha_local * alpha_eff
    sign = 1.0 if cl_linear >= 0 else -1.0

    if abs(alpha_eff) <= alpha_stall:
        cl = max(-cl_max, min(cl_max, cl_linear))
        ratio = abs(alpha_eff) / alpha_stall if alpha_stall > 1e-12 else 0.0
        if pre_stall_curve_strength > 0.0 and ratio > pre_stall_curve_start:
            span = max(1.0 - pre_stall_curve_start, 1e-9)
            t = min(max((ratio - pre_stall_curve_start) / span, 0.0), 1.0)
            smooth = t * t * (3.0 - 2.0 * t)
            cl_soft = sign * cl_max * math.tanh(abs(cl_linear) / max(cl_max, 1e-9))
            blend = pre_stall_curve_strength * smooth
            cl = (1.0 - blend) * cl + blend * cl_soft
        stall_drag = 0.0
    else:
        cl_stall = cl_alpha * alpha_stall
        excess = abs(alpha_eff) - alpha_stall
        degraded = abs(cl_stall) * math.exp(-post_stall_decay_rate * excess)
        min_post_stall = post_stall_min_cl_ratio * cl_max
        cl = sign * max(min_post_stall, min(cl_max, degraded))
        stall_drag = stall_drag_factor * excess ** stall_drag_exponent

    drag_delta = max(0.0, abs(cl - cl_cd_min) - drag_bucket_half_width)
    if cl < cl_cd_min:
        drag_linear = drag_rise_linear_neg
        drag_quad = k_drag_neg
    else:
        drag_linear = drag_rise_linear_pos
        drag_quad = k_drag_pos
    cd = cd0 + drag_linear * drag_delta + drag_quad * drag_delta**2 + stall_drag
    return cl, cd


def compute_lift_drag(density: float, velocity: float, area: float, cl: float, cd: float):
    if area <= 0:
        raise ValueError("Wing area must be greater than zero.")
    q = 0.5 * density * velocity**2
    lift = q * area * cl
    drag = q * area * cd
    ld_ratio = lift / drag if abs(drag) > 1e-12 else float("inf")
    return lift, drag, ld_ratio


def compute_flow_arrow_length(span_ref_mm: float, velocity_kmh: float):
    base_len = max(span_ref_mm * 0.44, 48.0)
    speed = max(float(velocity_kmh), 0.0)
    speed_scale = 0.65 + min(speed, 300.0) / 300.0 * 1.1
    return base_len * speed_scale
