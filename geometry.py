"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Geometry helper module for Manta AirLab.
Handles NACA 4-digit profile generation, transforms, and 3D mesh helpers.
"""

from __future__ import annotations

import math

import numpy as np


def parse_naca4_code(code: str):
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA code must have 4 digits, for example 2412 or 0012.")
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:4]) / 100.0
    return {"code": code, "m": m, "p": p, "t": t, "is_symmetric": (code[:2] == "00")}


def naca4_points_components(code: str, n_side: int = 100, chord: float = 1.0):
    geom = parse_naca4_code(code)
    m = geom["m"]
    p = geom["p"]
    t = geom["t"]

    beta = np.linspace(0.0, math.pi, n_side + 1)
    x = 0.5 * (1.0 - np.cos(beta))
    a4 = -0.1036

    yt = 5.0 * t * (
        0.2969 * np.sqrt(np.maximum(x, 0.0))
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        + a4 * x**4
    )

    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if m > 0 and p > 0:
        mask1 = x < p
        mask2 = ~mask1

        yc[mask1] = (m / p**2) * (2 * p * x[mask1] - x[mask1] ** 2)
        dyc_dx[mask1] = (2 * m / p**2) * (p - x[mask1])

        yc[mask2] = (m / (1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x[mask2] - x[mask2] ** 2)
        dyc_dx[mask2] = (2 * m / (1 - p) ** 2) * (p - x[mask2])

    theta = np.arctan(dyc_dx)
    return x * chord, yc * chord, theta, yt * chord


def close_profile(x, y):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(x) == 0:
        return x, y
    if not (np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1])):
        x = np.append(x, x[0])
        y = np.append(y, y[0])
    return x, y


def strip_duplicate_closing_point(x, y):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(x) == 0:
        return x, y
    if np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1]):
        return x[:-1], y[:-1]
    return x, y


def profile_xy_to_section_vertices(x, y, z):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    z_vals = np.full_like(x, float(z), dtype=float)
    return np.column_stack([x, y, z_vals])


def build_extruded_mesh(x, y, span):
    if span <= 0:
        raise ValueError("Span must be greater than zero.")

    x, y = strip_duplicate_closing_point(x, y)
    if len(x) < 3:
        raise ValueError("Profile must contain at least 3 unique points.")

    root = profile_xy_to_section_vertices(x, y, 0.0)
    tip = profile_xy_to_section_vertices(x, y, span)

    side_quads = []
    tol = 1e-12
    count = len(root)
    for i in range(count):
        j = (i + 1) % count
        edge_len = np.linalg.norm(root[j] - root[i])
        if edge_len <= tol:
            continue
        side_quads.append([root[i], root[j], tip[j], tip[i]])

    if not side_quads:
        raise ValueError("Unable to build 3D mesh from the current profile.")

    return {
        "root": root,
        "tip": tip,
        "side_quads": side_quads,
        "root_cap": root[::-1],
        "tip_cap": tip,
    }


def compute_display_limits_3d(points_xyz_mm, pad_ratio_xy=0.12, pad_ratio_z=0.08, min_pad_mm=3.0):
    pts = np.asarray(points_xyz_mm, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3 or len(pts) == 0:
        raise ValueError("3D display limits require Nx3 points.")

    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    spans = np.maximum(maxs - mins, 1e-9)

    pad_x = max(spans[0] * pad_ratio_xy, min_pad_mm)
    pad_y = max(spans[1] * pad_ratio_xy, min_pad_mm)
    pad_z = max(spans[2] * pad_ratio_z, min_pad_mm)

    xlim = (mins[0] - pad_x, maxs[0] + pad_x)
    ylim = (mins[1] - pad_y, maxs[1] + pad_y)
    zlim = (mins[2] - pad_z, maxs[2] + pad_z)
    aspect = (
        max(xlim[1] - xlim[0], 1.0),
        max(ylim[1] - ylim[0], 1.0),
        max(zlim[1] - zlim[0], 1.0),
    )
    return {"xlim": xlim, "ylim": ylim, "zlim": zlim, "aspect": aspect}


def build_base_airfoil_xy(code: str, n_side: int = 100, chord: float = 1.0):
    x, yc, theta, yt = naca4_points_components(code=code, n_side=n_side, chord=chord)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    upper_x = xu[::-1]
    upper_y = yu[::-1]
    lower_x = xl[1:]
    lower_y = yl[1:]

    x_all = np.concatenate([upper_x, lower_x])
    y_all = np.concatenate([upper_y, lower_y])
    return close_profile(x_all, y_all)


def build_curved_airfoil_xy(code: str, n_side: int, chord: float, radius: float, convex: bool = True, keep_developed_chord: bool = True):
    if radius <= 0:
        raise ValueError("Curvature radius must be greater than zero.")

    x, yc, theta_local, yt = naca4_points_components(code=code, n_side=n_side, chord=chord)

    if keep_developed_chord:
        phi = x / radius
    else:
        if np.max(x) > radius:
            raise ValueError(
                "With linear projected chord, radius must be >= chord. Increase radius or enable 'keep developed chord'."
            )
        ratio = np.clip(x / radius, -1.0, 1.0)
        phi = np.arcsin(ratio)

    sign = 1.0 if convex else -1.0
    x_base = radius * np.sin(phi)
    y_base = sign * radius * (1.0 - np.cos(phi))
    tx = np.cos(phi)
    ty = sign * np.sin(phi)
    nx = -ty
    ny = tx
    alpha = np.arctan2(ty, tx)
    x_cam = x_base + yc * nx
    y_cam = y_base + yc * ny
    total_angle = alpha + theta_local
    npx = -np.sin(total_angle)
    npy = np.cos(total_angle)

    xu = x_cam + yt * npx
    yu = y_cam + yt * npy
    xl = x_cam - yt * npx
    yl = y_cam - yt * npy

    upper_x = xu[::-1]
    upper_y = yu[::-1]
    lower_x = xl[1:]
    lower_y = yl[1:]

    x_all = np.concatenate([upper_x, lower_x])
    y_all = np.concatenate([upper_y, lower_y])
    return close_profile(x_all, y_all)


def transform_points(x, y, angle_deg=0.0, mirror_x=False, mirror_y=False):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if mirror_x:
        y = -y
    if mirror_y:
        x = -x

    if angle_deg:
        ang = math.radians(-angle_deg)
        c = math.cos(ang)
        s = math.sin(ang)
        x, y = x * c - y * s, x * s + y * c

    return close_profile(x, y)


def naca4_points_base(code: str, n_side: int = 100, chord: float = 1.0):
    x, y = build_base_airfoil_xy(code=code, n_side=n_side, chord=chord)
    z = np.zeros_like(x)
    return x, y, z


def generate_airfoil_xy(values):
    if values["mode"] == "flat":
        x, y = build_base_airfoil_xy(code=values["code"], n_side=values["n_side"], chord=values["chord"])
    else:
        x, y = build_curved_airfoil_xy(
            code=values["code"],
            n_side=values["n_side"],
            chord=values["chord"],
            radius=values["radius"],
            convex=values["curvature_dir"] == "convex",
            keep_developed_chord=values["keep_developed_chord"],
        )

    return transform_points(
        x,
        y,
        angle_deg=values["angle_deg"],
        mirror_x=values["mirror_x"],
        mirror_y=values["mirror_y"],
    )
