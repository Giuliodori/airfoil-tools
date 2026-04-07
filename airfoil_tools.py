"""Manta AirLab | Fabio Giuliodori — Explore https://duilio.cc."""

# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-Duilio-Commercial
#
# This file is part of Airfoil Tools.
# See LICENSE and COMMERCIAL-LICENSE.md for details.

import importlib
import argparse
import math
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import numpy as np
except ImportError:
    np = None

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None
    Poly3DCollection = None

from airfoil_library import get_airfoil_parameters
from defaults import CLI_DEFAULTS, FLUID_PRESETS, GUI_DEFAULTS

THEME_PRESETS = {
    "dark": {
        "label": "Dark",
        "colors": {
            "bg": "#141414",
            "panel": "#1b1b1b",
            "panel_alt": "#232323",
            "border": "#303030",
            "fg": "#ececec",
            "muted": "#9a9a9a",
            "accent": "#c2c7cd",
            "accent_alt": "#a7adb5",
            "entry": "#101010",
            "text": "#ececec",
            "selection": "#2e3238",
            "plot_bg": "#161616",
            "grid": "#2f2f2f",
            "button": "#262626",
            "button_hover": "#2f2f2f",
            "button_pressed": "#3a3a3a",
            "button_text_active": "#ffffff",
            "hero": "#1a1a1a",
            "hero_accent": "#b7b7b7",
            "hero_text": "#f3f3f3",
            "subtle": "#8c8c8c",
            "lift": "#4ec9b0",
            "drag": "#f14c4c",
            "plot_fill": "#686d73",
            "plot_fill_alt": "#8a9097",
        },
    },
    "light": {
        "label": "Light",
        "colors": {
            "bg": "#f1f3f6",
            "panel": "#ffffff",
            "panel_alt": "#eef1f5",
            "border": "#d4dbe4",
            "fg": "#1f2933",
            "muted": "#69798b",
            "accent": "#2f7dd1",
            "accent_alt": "#1e68b9",
            "entry": "#f8f9fb",
            "text": "#1f2933",
            "selection": "#dce9f8",
            "plot_bg": "#ffffff",
            "grid": "#d9e1e8",
            "button": "#f5f7fa",
            "button_hover": "#ecf1f6",
            "button_pressed": "#dfe8f2",
            "button_text_active": "#1f1f1f",
            "hero": "#ffffff",
            "hero_accent": "#2f7dd1",
            "hero_text": "#17324d",
            "subtle": "#66778a",
            "lift": "#16825d",
            "drag": "#c72e0f",
            "plot_fill": "#acd4fb",
            "plot_fill_alt": "#6eaee8",
        },
    },
}
THEME_LABEL_TO_KEY = {
    preset["label"]: key for key, preset in THEME_PRESETS.items()
}
THEME_KEY_TO_LABEL = {
    key: preset["label"] for key, preset in THEME_PRESETS.items()
}
THEME_OPTION_LABELS = tuple(THEME_LABEL_TO_KEY.keys())


def _prompt_install(packages, context=""):
    pkg_list = ", ".join(packages)
    header = "Install dependencies"
    extra = f"\n\n{context}" if context else ""
    msg = f"Missing dependencies: {pkg_list}.\nInstall now?{extra}"
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno(header, msg)
        finally:
            root.destroy()
    except Exception:
        resp = input(f"{msg} [y/N]: ")
        return resp.strip().lower().startswith("y")


def _run_pip_install(packages):
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    try:
        completed = subprocess.run(cmd, check=False)
    except Exception:
        return False
    return completed.returncode == 0


def _load_plotting_deps():
    global np, FigureCanvasTkAgg, Figure, Poly3DCollection
    if np is None:
        np = importlib.import_module("numpy")
    if FigureCanvasTkAgg is None or Figure is None or Poly3DCollection is None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as _FigureCanvasTkAgg
        from matplotlib.figure import Figure as _Figure
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection as _Poly3DCollection

        FigureCanvasTkAgg = _FigureCanvasTkAgg
        Figure = _Figure
        Poly3DCollection = _Poly3DCollection


def ensure_required_deps():
    required = []
    if np is None:
        required.append("numpy")
    if FigureCanvasTkAgg is None or Figure is None or Poly3DCollection is None:
        required.append("matplotlib")

    if not required:
        return True

    if not _prompt_install(required, context="The app cannot start without these packages."):
        return False

    if not _run_pip_install(required):
        messagebox.showerror(
            "Install failed",
            "Unable to install required packages. Please install them manually "
            "and restart the app.",
        )
        return False

    try:
        _load_plotting_deps()
    except Exception:
        messagebox.showerror(
            "Install failed",
            "Packages were installed but could not be imported. Please restart the app.",
        )
        return False

    return True


def ensure_numpy():
    global np
    if np is None:
        np = importlib.import_module("numpy")




def parse_naca4_code(code: str):
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA code must have 4 digits, for example 2412 or 0012.")
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:4]) / 100.0
    return {"code": code, "m": m, "p": p, "t": t, "is_symmetric": (code[:2] == "00")}


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
    """Scales the 2D flow arrow length with the configured speed."""
    base_len = max(span_ref_mm * 0.44, 48.0)
    speed = max(float(velocity_kmh), 0.0)
    speed_scale = 0.65 + min(speed, 300.0) / 300.0 * 1.1
    return base_len * speed_scale


def naca4_points_components(code: str, n_side: int = 100, chord: float = 1.0):
    """
    Generates geometric components of a NACA 4-digit profile.

    Returns:
    - x: coordinate along chord [0..chord]
    - yc: camber line
    - theta: local camber-line angle
    - yt: half-thickness

    Note: uses closed trailing edge (coefficient -0.1036).
    """
    geom = parse_naca4_code(code)
    m = geom["m"]
    p = geom["p"]
    t = geom["t"]

    beta = np.linspace(0.0, math.pi, n_side + 1)
    x = 0.5 * (1.0 - np.cos(beta))  # 0 -> 1

    # trailing edge geometrico chiuso
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
    """Ensures first and last points coincide."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(x) == 0:
        return x, y
    if not (np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1])):
        x = np.append(x, x[0])
        y = np.append(y, y[0])
    return x, y


def strip_duplicate_closing_point(x, y):
    """Removes duplicated last point from a closed 2D contour."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(x) == 0:
        return x, y
    if np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1]):
        return x[:-1], y[:-1]
    return x, y


def profile_xy_to_section_vertices(x, y, z):
    """Converts a 2D profile into 3D section vertices at constant z."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    z_vals = np.full_like(x, float(z), dtype=float)
    return np.column_stack([x, y, z_vals])


def build_extruded_mesh(x, y, span):
    """Builds a lightweight side-surface extrusion mesh along +Z."""
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
    """Returns per-axis display limits with light dynamic padding."""
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
    return {
        "xlim": xlim,
        "ylim": ylim,
        "zlim": zlim,
        "aspect": aspect,
    }


def build_base_airfoil_xy(code: str, n_side: int = 100, chord: float = 1.0):
    """
    Flat NACA 4-digit profile.
    Point order: upper surface TE -> LE, then lower surface LE -> TE.
    """
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


def build_curved_airfoil_xy(
    code: str,
    n_side: int,
    chord: float,
    radius: float,
    convex: bool = True,
    keep_developed_chord: bool = True,
):
    """
    Generates a curved profile on an arc of radius R.

    Strategy:
    1) compute local NACA components (x, yc, theta, yt)
    2) map the camber line onto an arc
    3) apply local offset along the local arc normal

    keep_developed_chord=True:
      x is arc length (theta = x / R)
    keep_developed_chord=False:
      x is linear projection (theta = asin(x / R))
    """
    if radius <= 0:
        raise ValueError("Curvature radius must be greater than zero.")

    x, yc, theta_local, yt = naca4_points_components(code=code, n_side=n_side, chord=chord)

    if keep_developed_chord:
        phi = x / radius
    else:
        if np.max(x) > radius:
            raise ValueError(
                "With linear projected chord, radius must be >= chord. "
                "Increase radius or enable 'keep developed chord'."
            )
        ratio = np.clip(x / radius, -1.0, 1.0)
        phi = np.arcsin(ratio)

    # curvature direction: convex (+1), concave (-1)
    sign = 1.0 if convex else -1.0

    # base arc through origin: x_base=R*sin(phi), y_base=sign*R*(1-cos(phi))
    x_base = radius * np.sin(phi)
    y_base = sign * radius * (1.0 - np.cos(phi))

    # local arc tangent
    tx = np.cos(phi)
    ty = sign * np.sin(phi)

    # local arc normal (rotated +90 deg)
    nx = -ty
    ny = tx

    # angle between local x-axis and arc tangent
    alpha = np.arctan2(ty, tx)

    # camber line mapped to arc
    x_cam = x_base + yc * nx
    y_cam = y_base + yc * ny

    # complete local profile normal (arc + NACA camber)
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
    """Global final mirrors and rotation.

    UI convention: positive rotation is clockwise.
    """
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if mirror_x:
        y = -y

    if mirror_y:
        x = -x

    if angle_deg:
        # Convert UI clockwise-positive convention to math CCW-positive rotation.
        ang = math.radians(-angle_deg)
        c = math.cos(ang)
        s = math.sin(ang)
        xr = x * c - y * s
        yr = x * s + y * c
        x, y = xr, yr

    return close_profile(x, y)


def format_number(value: float, decimals: int = 6) -> str:
    if abs(value) < 0.5 * 10 ** (-decimals):
        return "0"
    if abs(value - round(value)) < 0.5 * 10 ** (-decimals):
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def write_pts_text(x, y, decimals: int = 6):
    """Compatible .pts writer: x TAB y TAB z with z=0."""
    x, y = close_profile(x, y)
    z = np.zeros_like(x)
    lines = []
    for xv, yv, zv in zip(x, y, z):
        lines.append(
            f"{format_number(float(xv), decimals)}\t"
            f"{format_number(float(yv), decimals)}\t"
            f"{format_number(float(zv), decimals)}"
        )
    return "\n".join(lines), x, y, z


def write_pts_xy_text(x, y, decimals: int = 6):
    """PTS-style writer: x TAB y with no header."""
    x, y = close_profile(x, y)
    lines = []
    for xv, yv in zip(x, y):
        lines.append(
            f"{format_number(float(xv), decimals)}\t"
            f"{format_number(float(yv), decimals)}"
        )
    return "\n".join(lines), x, y, None


def write_csv_xyz_text(x, y, decimals: int = 6):
    """CSV writer: x,y,z with z=0 and no header."""
    x, y = close_profile(x, y)
    z = np.zeros_like(x)
    lines = []
    for xv, yv, zv in zip(x, y, z):
        lines.append(
            f"{format_number(float(xv), decimals)},"
            f"{format_number(float(yv), decimals)},"
            f"{format_number(float(zv), decimals)}"
        )
    return "\n".join(lines), x, y, z


def write_csv_xy_text(x, y, decimals: int = 6):
    """CSV writer: x,y with no header."""
    x, y = close_profile(x, y)
    lines = []
    for xv, yv in zip(x, y):
        lines.append(
            f"{format_number(float(xv), decimals)},"
            f"{format_number(float(yv), decimals)}"
        )
    return "\n".join(lines), x, y, None


def _load_ezdxf(prompt_install: bool):
    try:
        import ezdxf
    except ImportError as exc:
        if not prompt_install:
            raise RuntimeError("DXF export requires 'ezdxf'. Install with: pip install ezdxf") from exc
        if _prompt_install(["ezdxf"], context="Needed to export DXF files."):
            if _run_pip_install(["ezdxf"]):
                try:
                    import ezdxf  # type: ignore
                except Exception as err:
                    raise RuntimeError(
                        "Library 'ezdxf' was installed but could not be imported."
                    ) from err
            else:
                raise RuntimeError(
                    "Unable to install 'ezdxf'. Please install it manually and retry."
                ) from exc
        else:
            raise RuntimeError(
                "Library 'ezdxf' is not installed. Install with: pip install ezdxf"
            ) from exc
    return ezdxf


def _add_dxf_entity(msp, points_2d, layer: str, mode: str):
    if mode == "polyline":
        msp.add_lwpolyline(points_2d, format="xy", dxfattribs={"layer": layer, "closed": True})
        return
    spline = msp.add_spline(fit_points=points_2d, dxfattribs={"layer": layer})
    try:
        spline.closed = True
    except Exception:
        pass


def write_dxf(path: str, x, y, layer: str = "AIRFOIL", mode: str = "spline"):
    """Export a closed contour as DXF spline (default) or polyline."""
    ezdxf = _load_ezdxf(prompt_install=True)
    x, y = close_profile(x, y)

    doc = ezdxf.new("R2010")
    if layer not in doc.layers:
        doc.layers.add(name=layer)

    msp = doc.modelspace()
    points_2d = [(float(xv), float(yv)) for xv, yv in zip(x, y)]
    _add_dxf_entity(msp, points_2d, layer, mode=mode)
    doc.saveas(path)


def write_dxf_cli(path: str, x, y, layer: str = "AIRFOIL", mode: str = "spline"):
    """CLI DXF export: does not prompt for dependency installation."""
    ezdxf = _load_ezdxf(prompt_install=False)
    x, y = close_profile(x, y)
    doc = ezdxf.new("R2010")
    if layer not in doc.layers:
        doc.layers.add(name=layer)
    msp = doc.modelspace()
    points_2d = [(float(xv), float(yv)) for xv, yv in zip(x, y)]
    _add_dxf_entity(msp, points_2d, layer, mode=mode)
    doc.saveas(path)


def write_dxf_polyline(path: str, x, y, layer: str = "AIRFOIL"):
    """Export as a 2D LWPOLYLINE on the XY plane."""
    write_dxf(path, x, y, layer=layer, mode="polyline")


def write_dxf_polyline_cli(path: str, x, y, layer: str = "AIRFOIL"):
    """CLI DXF export as polyline."""
    write_dxf_cli(path, x, y, layer=layer, mode="polyline")


def _triangle_normal(v1, v2, v3):
    n = np.cross(v2 - v1, v3 - v1)
    norm = np.linalg.norm(n)
    if norm <= 1e-15:
        return np.array([0.0, 0.0, 0.0], dtype=float)
    return n / norm


def write_stl_ascii(path: str, x, y, span: float, solid_name: str = "airfoil"):
    """Export an extruded airfoil mesh as ASCII STL."""
    mesh = build_extruded_mesh(x, y, span)
    triangles = []

    for quad in mesh["side_quads"]:
        p0, p1, p2, p3 = [np.asarray(v, dtype=float) for v in quad]
        triangles.append((p0, p1, p2))
        triangles.append((p0, p2, p3))

    root = [np.asarray(v, dtype=float) for v in mesh["root_cap"]]
    tip = [np.asarray(v, dtype=float) for v in mesh["tip_cap"]]
    for i in range(1, len(root) - 1):
        triangles.append((root[0], root[i], root[i + 1]))
    for i in range(1, len(tip) - 1):
        triangles.append((tip[0], tip[i], tip[i + 1]))

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"solid {solid_name}\n")
        for v1, v2, v3 in triangles:
            n = _triangle_normal(v1, v2, v3)
            f.write(f"  facet normal {n[0]:.9e} {n[1]:.9e} {n[2]:.9e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]:.9e} {v1[1]:.9e} {v1[2]:.9e}\n")
            f.write(f"      vertex {v2[0]:.9e} {v2[1]:.9e} {v2[2]:.9e}\n")
            f.write(f"      vertex {v3[0]:.9e} {v3[1]:.9e} {v3[2]:.9e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {solid_name}\n")


def naca4_points_base(code: str, n_side: int = 100, chord: float = 1.0):
    """
    Backward compatible with previous API:
    returns x, y, z for flat profile in order upper TE -> LE -> lower TE.
    """
    x, y = build_base_airfoil_xy(code=code, n_side=n_side, chord=chord)
    z = np.zeros_like(x)
    return x, y, z


def build_pts_text(
    code: str,
    n_side: int,
    chord: float,
    angle_deg: float,
    mirror_x: bool,
    mirror_y: bool,
    decimals: int = 6,
):
    """
    Backward compatible with previous API:
    generates .pts text with global transforms applied.
    """
    x, y, z = naca4_points_base(code=code, n_side=n_side, chord=chord)
    x, y = transform_points(x, y, angle_deg=angle_deg, mirror_x=mirror_x, mirror_y=mirror_y)
    pts_text, x, y, z = write_pts_text(x, y, decimals=decimals)
    return pts_text, x, y, z


def generate_airfoil_xy(values):
    """Selects generation mode and applies final transforms."""
    if values["mode"] == "flat":
        x, y = build_base_airfoil_xy(
            code=values["code"],
            n_side=values["n_side"],
            chord=values["chord"],
        )
    else:
        x, y = build_curved_airfoil_xy(
            code=values["code"],
            n_side=values["n_side"],
            chord=values["chord"],
            radius=values["radius"],
            convex=values["curvature_dir"] == "convex",
            keep_developed_chord=values["keep_developed_chord"],
        )

    x, y = transform_points(
        x,
        y,
        angle_deg=values["angle_deg"],
        mirror_x=values["mirror_x"],
        mirror_y=values["mirror_y"],
    )
    return x, y


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Airfoil Tools")
        self.style = ttk.Style()
        self.theme_var = tk.StringVar(
            value=THEME_KEY_TO_LABEL.get(GUI_DEFAULTS["theme"], THEME_OPTION_LABELS[0])
        )
        self.tk_scale_widgets = []
        self.set_window_icon()
        self.apply_theme(GUI_DEFAULTS["theme"])
        self.configure_initial_window_size()

        self._update_job = None
        self._syncing_code = False

        self.build_compact_layout()

        self.last_pts_text = ""
        self.last_x = None
        self.last_y = None
        self.plot_mode = "2d"
        self._pan_state = None
        self._default_3d_view = {"elev": 10, "azim": -102}

        self.update_mode_fields()
        self.update_fluid_fields()
        self.update_preview()

    def configure_initial_window_size(self):
        self.root.update_idletasks()
        screen_w = max(self.root.winfo_screenwidth(), 1280)
        screen_h = max(self.root.winfo_screenheight(), 800)

        if screen_h <= 1080:
            height = screen_h
        else:
            height = 1080
        window_ratio = (16 / 9) * 1.2
        width = max(1260, int(height * window_ratio))

        width = min(width, screen_w - 40)
        height = min(height, screen_h - 80)

        pos_x = max((screen_w - width) // 2, 0)
        pos_y = max((screen_h - height) // 2, 0)

        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.minsize(1160, 680)

    def set_window_icon(self):
        icon_path = os.path.join("images", "ico.ico")
        if not os.path.exists(icon_path):
            return
        try:
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def get_theme_key(self, theme_value):
        if theme_value in THEME_PRESETS:
            return theme_value
        return THEME_LABEL_TO_KEY.get(theme_value, GUI_DEFAULTS["theme"])

    def apply_theme(self, theme_value=None):
        theme_key = self.get_theme_key(theme_value or self.theme_var.get())
        self.colors = dict(THEME_PRESETS[theme_key]["colors"])
        self.theme_var.set(THEME_KEY_TO_LABEL[theme_key])
        self.root.configure(bg=self.colors["bg"])

        themes = self.style.theme_names()
        if "clam" in themes:
            self.style.theme_use("clam")

        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"])
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["panel"], foreground=self.colors["fg"], font=("Segoe UI", 9))
        self.style.configure("TSeparator", background=self.colors["border"])
        self.style.configure(
            "TLabelframe",
            background=self.colors["panel"],
            borderwidth=1,
            relief="solid",
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
        )
        self.style.configure(
            "TLabelframe.Label",
            background=self.colors["panel"],
            foreground=self.colors["fg"],
            font=("Segoe UI Semibold", 10),
        )
        self.style.configure(
            "TEntry",
            fieldbackground=self.colors["entry"],
            foreground=self.colors["text"],
            insertcolor=self.colors["text"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            padding=(6, 4),
        )
        self.style.map(
            "TEntry",
            fieldbackground=[
                ("readonly", self.colors["entry"]),
                ("disabled", self.colors["panel_alt"]),
            ],
            foreground=[
                ("readonly", self.colors["text"]),
                ("disabled", self.colors["muted"]),
            ],
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=self.colors["entry"],
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["fg"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            padding=(6, 4),
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.colors["entry"])],
            background=[("readonly", self.colors["panel_alt"])],
            foreground=[
                ("readonly", self.colors["text"]),
                ("disabled", self.colors["muted"]),
            ],
            selectbackground=[("readonly", self.colors["selection"])],
            selectforeground=[("readonly", self.colors["text"])],
        )
        self.style.configure(
            "TSpinbox",
            fieldbackground=self.colors["entry"],
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["fg"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            padding=(6, 4),
        )
        self.style.map(
            "TSpinbox",
            fieldbackground=[
                ("readonly", self.colors["entry"]),
                ("disabled", self.colors["panel_alt"]),
            ],
            foreground=[
                ("readonly", self.colors["text"]),
                ("disabled", self.colors["muted"]),
            ],
        )
        self.style.configure(
            "TCheckbutton",
            background=self.colors["panel"],
            foreground=self.colors["fg"],
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", self.colors["panel_alt"])],
            foreground=[("disabled", self.colors["muted"])],
        )
        self.style.configure(
            "TButton",
            background=self.colors["button"],
            foreground=self.colors["fg"],
            borderwidth=1,
            focuscolor=self.colors["accent"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            font=("Segoe UI Semibold", 9),
            padding=(8, 5),
        )
        self.style.map(
            "TButton",
            background=[
                ("active", self.colors["button_hover"]),
                ("pressed", self.colors["button_pressed"]),
            ],
            foreground=[("active", self.colors["button_text_active"])],
        )
        self.style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground=self.colors["button_text_active"],
            bordercolor=self.colors["accent"],
            lightcolor=self.colors["accent"],
            darkcolor=self.colors["accent"],
        )
        self.style.map(
            "Accent.TButton",
            background=[
                ("active", self.colors["accent_alt"]),
                ("pressed", self.colors["button_pressed"]),
            ],
            foreground=[("active", self.colors["button_text_active"])],
        )
        self.style.configure(
            "Panel.TFrame",
            background=self.colors["panel"],
        )
        self.style.configure(
            "Panel.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["fg"],
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Muted.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 8),
        )
        self.style.configure(
            "SummaryLabel.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 8),
        )
        self.style.configure(
            "SummaryValue.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["fg"],
            font=("Segoe UI Semibold", 9),
        )
        self.style.configure(
            "Hero.TFrame",
            background=self.colors["hero"],
        )
        self.style.configure(
            "HeroTitle.TLabel",
            background=self.colors["hero"],
            foreground=self.colors["hero_text"],
            font=("Segoe UI Semibold", 12),
        )
        self.style.configure(
            "HeroBody.TLabel",
            background=self.colors["hero"],
            foreground=self.colors["subtle"],
            font=("Segoe UI", 7),
        )
        self.style.configure(
            "HeroMeta.TLabel",
            background=self.colors["hero"],
            foreground=self.colors["hero_accent"],
            font=("Segoe UI", 7),
        )
        self.style.configure(
            "HeroValue.TLabel",
            background=self.colors["hero"],
            foreground=self.colors["hero_text"],
            font=("Segoe UI Semibold", 10),
        )
        self.style.configure(
            "HeroSignature.TLabel",
            background=self.colors["hero"],
            foreground=self.colors["subtle"],
            font=("Segoe UI", 7),
        )
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.colors["panel_alt"],
            troughcolor=self.colors["panel"],
            arrowcolor=self.colors["fg"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            background=self.colors["panel_alt"],
            troughcolor=self.colors["panel"],
            arrowcolor=self.colors["fg"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
        )
        self.style.configure(
            "KPIValue.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["lift"],
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "KPIValueAlt.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["drag"],
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "Footer.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        self.refresh_theme_widgets()

    def refresh_theme_widgets(self):
        self.root.configure(bg=self.colors["bg"])
        if getattr(self, "advanced_window", None) is not None:
            try:
                if self.advanced_window.winfo_exists():
                    self.advanced_window.configure(bg=self.colors["bg"])
            except Exception:
                pass

        if hasattr(self, "page_canvas"):
            self.page_canvas.configure(bg=self.colors["bg"], highlightbackground=self.colors["bg"])
        if hasattr(self, "code_entry"):
            self.code_entry.configure(
                bg=self.colors["entry"],
                fg=self.colors["text"],
                insertbackground=self.colors["text"],
                disabledbackground=self.colors["panel_alt"],
                disabledforeground=self.colors["muted"],
                highlightbackground=self.colors["border"],
                highlightcolor=self.colors["accent"],
            )
        if hasattr(self, "text"):
            self.text.configure(
                bg=self.colors["entry"],
                fg=self.colors["text"],
                insertbackground=self.colors["text"],
                selectbackground=self.colors["selection"],
                selectforeground=self.colors["text"],
                highlightbackground=self.colors["border"],
                highlightcolor=self.colors["accent"],
            )
        if hasattr(self, "canvas"):
            try:
                self.canvas.get_tk_widget().configure(
                    background=self.colors["panel"],
                    highlightbackground=self.colors["border"],
                )
            except Exception:
                pass

        for scale in self.tk_scale_widgets:
            if scale is None:
                continue
            scale.configure(
                bg=self.colors["panel"],
                fg=self.colors["fg"],
                highlightthickness=0,
                highlightbackground=self.colors["panel"],
                highlightcolor=self.colors["accent"],
                troughcolor=self.colors["entry"],
                activebackground=self.colors["accent"],
            )

        if hasattr(self, "canvas") and hasattr(self, "ax"):
            if self.last_x is None or self.last_y is None:
                self.configure_plot_theme()
                self.canvas.draw_idle()
            else:
                self.update_preview()

    def on_theme_changed(self, event=None):
        self.apply_theme(self.theme_var.get())

    def open_advanced_options(self):
        if self.advanced_window is not None:
            try:
                if self.advanced_window.winfo_exists():
                    self.advanced_window.lift()
                    self.advanced_window.focus_force()
                    return
            except Exception:
                self.advanced_window = None

        win = tk.Toplevel(self.root)
        win.title("Advanced options")
        win.configure(bg=self.colors["bg"])
        win.resizable(False, False)
        self.advanced_window = win

        def _close():
            try:
                win.destroy()
            finally:
                self.advanced_window = None
                self.advanced_mode_combo = None
                self.advanced_radius_entry = None
                self.advanced_curv_dir_combo = None

        win.protocol("WM_DELETE_WINDOW", _close)

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)

        profile = ttk.LabelFrame(outer, text="Custom profile", padding=10)
        profile.pack(fill="x")
        for col in (1, 3, 5):
            profile.columnconfigure(col, weight=1)

        ttk.Label(profile, text="NACA code").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        code_entry = ttk.Entry(profile, textvariable=self.code_var, width=10, justify="center")
        code_entry.grid(row=0, column=1, sticky="ew", pady=2)
        code_entry.bind("<KeyRelease>", self.schedule_update)

        ttk.Label(profile, text="Mode").grid(row=0, column=2, sticky="w", padx=(10, 6), pady=2)
        self.advanced_mode_combo = ttk.Combobox(
            profile,
            textvariable=self.mode_var,
            values=list(self.mode_map.keys()),
            state="readonly",
            width=18,
        )
        self.advanced_mode_combo.grid(row=0, column=3, sticky="ew", pady=2)
        self.advanced_mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        ttk.Label(profile, text="Rotation [deg]").grid(row=0, column=4, sticky="w", padx=(10, 6), pady=2)
        angle_entry = ttk.Entry(profile, textvariable=self.angle_var, width=10)
        angle_entry.grid(row=0, column=5, sticky="ew", pady=2)
        angle_entry.bind("<KeyRelease>", self.on_geometry_link_changed)

        ttk.Label(profile, text="Camber").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(6, 2))
        camber_spin = ttk.Spinbox(
            profile,
            from_=0,
            to=9,
            textvariable=self.naca_camber_var,
            width=8,
            command=self.on_digit_slider_changed,
        )
        camber_spin.grid(row=1, column=1, sticky="ew", pady=(6, 2))

        ttk.Label(profile, text="Position").grid(row=1, column=2, sticky="w", padx=(10, 6), pady=(6, 2))
        pos_spin = ttk.Spinbox(
            profile,
            from_=0,
            to=9,
            textvariable=self.naca_pos_var,
            width=8,
            command=self.on_digit_slider_changed,
        )
        pos_spin.grid(row=1, column=3, sticky="ew", pady=(6, 2))

        ttk.Label(profile, text="Thickness").grid(row=1, column=4, sticky="w", padx=(10, 6), pady=(6, 2))
        thickness_spin = ttk.Spinbox(
            profile,
            from_=1,
            to=40,
            textvariable=self.naca_thickness_var,
            width=8,
            command=self.on_digit_slider_changed,
        )
        thickness_spin.grid(row=1, column=5, sticky="ew", pady=(6, 2))

        for spin in (camber_spin, pos_spin, thickness_spin):
            spin.bind("<KeyRelease>", self.on_digit_spinbox_changed)
            spin.bind("<FocusOut>", self.on_digit_spinbox_changed)

        ttk.Label(profile, text="Chord [mm]").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=(6, 2))
        chord_entry = ttk.Entry(profile, textvariable=self.chord_var, width=10)
        chord_entry.grid(row=2, column=1, sticky="ew", pady=(6, 2))
        chord_entry.bind("<KeyRelease>", self.on_geometry_link_changed)

        ttk.Label(profile, text="Span [mm]").grid(row=2, column=2, sticky="w", padx=(10, 6), pady=(6, 2))
        span_entry = ttk.Entry(profile, textvariable=self.span_var, width=10)
        span_entry.grid(row=2, column=3, sticky="ew", pady=(6, 2))
        span_entry.bind("<KeyRelease>", self.schedule_update)

        ttk.Label(profile, text="Radius [mm]").grid(row=2, column=4, sticky="w", padx=(10, 6), pady=(6, 2))
        self.advanced_radius_entry = ttk.Entry(profile, textvariable=self.radius_var, width=10)
        self.advanced_radius_entry.grid(row=2, column=5, sticky="ew", pady=(6, 2))
        self.advanced_radius_entry.bind("<KeyRelease>", self.schedule_update)

        ttk.Label(profile, text="Curvature").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=(6, 2))
        self.advanced_curv_dir_combo = ttk.Combobox(
            profile,
            textvariable=self.curvature_dir_var,
            values=["convex", "concave"],
            state="readonly",
            width=12,
        )
        self.advanced_curv_dir_combo.grid(row=3, column=1, sticky="ew", pady=(6, 2))
        self.advanced_curv_dir_combo.bind("<<ComboboxSelected>>", self.schedule_update)

        ttk.Label(
            profile,
            text="These controls mirror the main panel and update the live profile in real time.",
            style="Muted.TLabel",
        ).grid(row=3, column=2, columnspan=4, sticky="w", padx=(10, 0), pady=(6, 2))

        export = ttk.LabelFrame(outer, text="Export formats", padding=10)
        export.pack(fill="x", pady=(8, 0))
        export.columnconfigure(1, weight=1)

        ttk.Label(export, text="DXF entity").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        dxf_combo = ttk.Combobox(
            export,
            textvariable=self.dxf_mode_var,
            values=["spline", "polyline"],
            state="readonly",
            width=14,
        )
        dxf_combo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(export, text="PTS format").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        pts_combo = ttk.Combobox(
            export,
            textvariable=self.pts_format_var,
            values=["xyz", "xy"],
            state="readonly",
            width=14,
        )
        pts_combo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(export, text="CSV format").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        csv_combo = ttk.Combobox(
            export,
            textvariable=self.csv_format_var,
            values=["xyz", "xy"],
            state="readonly",
            width=14,
        )
        csv_combo.grid(row=2, column=1, sticky="ew", pady=4)

        geom = ttk.LabelFrame(outer, text="Geometry (advanced)", padding=10)
        geom.pack(fill="x", pady=(8, 0))
        geom.columnconfigure(1, weight=1)
        ttk.Label(geom, text="Points/side").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        e = ttk.Entry(geom, textvariable=self.n_side_var, width=10)
        e.grid(row=0, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(geom, text="Decimals").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        e = ttk.Entry(geom, textvariable=self.decimals_var, width=10)
        e.grid(row=1, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        appearance = ttk.LabelFrame(outer, text="Appearance", padding=10)
        appearance.pack(fill="x", pady=(8, 0))
        appearance.columnconfigure(1, weight=1)
        ttk.Label(appearance, text="Theme", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        theme_combo = ttk.Combobox(
            appearance,
            textvariable=self.theme_var,
            values=THEME_OPTION_LABELS,
            state="readonly",
            width=18,
        )
        theme_combo.grid(row=0, column=1, sticky="ew", pady=2)
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_changed)
        ttk.Label(
            appearance,
            text="Choose the interface tone that feels more comfortable for long editing sessions.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.update_mode_fields()

    def build_compact_layout(self):
        shell = ttk.Frame(self.root, padding=0)
        shell.pack(fill="both", expand=True)

        self.page_canvas = tk.Canvas(
            shell,
            bg=self.colors["bg"],
            highlightthickness=0,
            borderwidth=0,
        )
        page_scroll = ttk.Scrollbar(shell, orient="vertical", command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=page_scroll.set)
        self.page_canvas.pack(side="left", fill="both", expand=True)
        page_scroll.pack(side="right", fill="y")

        main = ttk.Frame(self.page_canvas, padding=8)
        self.page_canvas_window = self.page_canvas.create_window((0, 0), window=main, anchor="nw")

        def _update_scrollregion(event=None):
            self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

        def _update_width(event):
            self.page_canvas.itemconfigure(self.page_canvas_window, width=event.width)

        main.bind("<Configure>", _update_scrollregion)
        self.page_canvas.bind("<Configure>", _update_width)

        self.header_profile_var = tk.StringVar(value="NACA 2412")
        self.header_status_var = tk.StringVar(value="Flat profile | chord 100 mm | span 200 mm")
        self.preview_mode_var = tk.StringVar(value="Flat")
        self.preview_points_var = tk.StringVar(value="-")
        self.preview_format_var = tk.StringVar(value=GUI_DEFAULTS["pts_format"].upper())

        header = ttk.Frame(main, style="Hero.TFrame", padding=(10, 5))
        header.pack(fill="x", pady=(0, 6))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        header_left = ttk.Frame(header, style="Hero.TFrame")
        header_left.grid(row=0, column=0, sticky="nsew")
        title_row = ttk.Frame(header_left, style="Hero.TFrame")
        title_row.pack(anchor="w")
        ttk.Label(title_row, text="Airfoil Tools", style="HeroTitle.TLabel").pack(side="left")
        ttk.Label(title_row, text="Manta AirLab | Fabio Giuliodori — Explore https://duilio.cc", style="HeroSignature.TLabel").pack(side="left", padx=(8, 0), pady=(2, 0))

        header_right = ttk.Frame(header, style="Hero.TFrame", padding=(10, 0, 0, 0))
        header_right.grid(row=0, column=1, sticky="e")
        ttk.Label(header_right, text="Current profile", style="HeroMeta.TLabel").pack(anchor="e")
        ttk.Label(header_right, textvariable=self.header_profile_var, style="HeroValue.TLabel").pack(anchor="e")
        ttk.Label(header_right, textvariable=self.header_status_var, style="HeroBody.TLabel").pack(anchor="e")

        main_panes = ttk.Panedwindow(main, orient="horizontal")
        main_panes.pack(fill="both", expand=True)
        self.main_panes = main_panes

        left = ttk.Frame(main_panes, padding=(0, 0, 8, 0))
        right = ttk.Frame(main_panes)
        main_panes.add(left, weight=0)
        main_panes.add(right, weight=1)

        self.code_var = tk.StringVar(value=GUI_DEFAULTS["code"])
        self.chord_var = tk.StringVar(value=GUI_DEFAULTS["chord_mm"])
        self.n_side_var = tk.StringVar(value=GUI_DEFAULTS["points_side"])
        self.mode_var = tk.StringVar(value=GUI_DEFAULTS["mode"])
        self.radius_var = tk.StringVar(value=GUI_DEFAULTS["radius_mm"])
        self.curvature_dir_var = tk.StringVar(value=GUI_DEFAULTS["curvature_dir"])
        self.keep_developed_var = tk.BooleanVar(value=GUI_DEFAULTS["keep_developed_chord"])
        self.angle_var = tk.StringVar(value=GUI_DEFAULTS["angle_deg"])
        self.decimals_var = tk.StringVar(value=GUI_DEFAULTS["decimals"])
        self.mirror_x_var = tk.BooleanVar(value=GUI_DEFAULTS["mirror_x"])
        self.mirror_y_var = tk.BooleanVar(value=GUI_DEFAULTS["mirror_y"])
        self.dxf_mode_var = tk.StringVar(value=GUI_DEFAULTS["dxf_mode"])
        self.pts_format_var = tk.StringVar(value=GUI_DEFAULTS["pts_format"])
        self.csv_format_var = tk.StringVar(value=GUI_DEFAULTS["csv_format"])
        self.advanced_window = None
        self.advanced_mode_combo = None
        self.advanced_radius_entry = None
        self.advanced_curv_dir_combo = None
        # Advanced aerodynamic source toggle kept for future UI re-enable.
        # To restore it, add back the checkbox in the Aerodynamics panel and
        # switch `use_internal_library=True` in `compute_aero_results()` to this variable.
        self.use_internal_aero_var = tk.BooleanVar(value=True)
        self.fluid_var = tk.StringVar(value=GUI_DEFAULTS["fluid"])
        self.velocity_var = tk.StringVar(value=GUI_DEFAULTS["velocity_kmh"])
        self.aero_chord_var = tk.StringVar(value=GUI_DEFAULTS["aero_chord_mm"])
        self.span_var = tk.StringVar(value=GUI_DEFAULTS["span_mm"])
        self.alpha_attack_var = tk.StringVar(value=GUI_DEFAULTS["alpha_deg"])
        self.density_var = tk.StringVar(value=str(FLUID_PRESETS["water"]["rho"]))
        self.viscosity_var = tk.StringVar(value=str(FLUID_PRESETS["water"]["mu"]))
        self.override_cd0_var = tk.StringVar(value="")
        self.override_k_drag_var = tk.StringVar(value="")
        self.override_cl_max_var = tk.StringVar(value="")
        self.override_alpha0_var = tk.StringVar(value="")
        self.reynolds_out_var = tk.StringVar(value="-")
        self.cl_out_var = tk.StringVar(value="-")
        self.cd_out_var = tk.StringVar(value="-")
        self.lift_out_var = tk.StringVar(value="-")
        self.drag_out_var = tk.StringVar(value="-")
        self.ld_out_var = tk.StringVar(value="-")
        self.lift_label_var = tk.StringVar(value="Lift [kg]")
        self.drag_label_var = tk.StringVar(value="Drag [kg]")
        self.naca_camber_var = tk.IntVar(value=GUI_DEFAULTS["naca_camber"])
        self.naca_pos_var = tk.IntVar(value=GUI_DEFAULTS["naca_pos"])
        self.naca_thickness_var = tk.IntVar(value=GUI_DEFAULTS["naca_thickness"])
        # Expert-mode state is intentionally kept even if the toggle is hidden.
        # To re-enable advanced controls, restore the Expert checkbox and relax
        # the row filtering inside `update_expert_visibility()`.
        self.show_expert_var = tk.BooleanVar(value=GUI_DEFAULTS["show_expert"])

        geom = ttk.LabelFrame(left, text="Section Geometry", padding=8)
        geom.pack(fill="x")
        geom.columnconfigure(1, weight=1)
        geom.columnconfigure(3, weight=1)

        row = 0
        ttk.Label(geom, text="NACA profile", style="Panel.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=(1, 1))
        self.code_entry = tk.Entry(
            geom,
            textvariable=self.code_var,
            width=12,
            justify="center",
            font=("Segoe UI", 15, "bold"),
            bg=self.colors["entry"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["accent"],
        )
        self.code_entry.grid(row=row, column=1, sticky="ew", pady=(2, 0))
        self.code_entry.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(geom, text="Mode", style="Panel.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=1)
        self.mode_map = {
            "Flat profile": "flat",
            "Curved profile (radius)": "curved",
        }
        mode_combo = ttk.Combobox(
            geom,
            textvariable=self.mode_var,
            values=list(self.mode_map.keys()),
            state="readonly",
            width=18,
        )
        mode_combo.current(0)
        mode_combo.grid(row=row, column=3, sticky="ew", pady=2)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)
        self.mode_combo = mode_combo

        row += 1
        ttk.Label(geom, text="Camber | camber position | thickness", style="Muted.TLabel").grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(1, 4)
        )

        row += 1
        slider_specs = (
            ("Camber", self.naca_camber_var, 0, 9),
            ("Pos", self.naca_pos_var, 0, 9),
        )
        for col, (label, var, min_v, max_v) in enumerate(slider_specs):
            ttk.Label(geom, text=label, style="Panel.TLabel").grid(row=row, column=col, sticky="w", pady=(0, 1))
            scale = tk.Scale(
                geom,
                from_=min_v,
                to=max_v,
                orient="horizontal",
                variable=var,
                showvalue=True,
                resolution=1,
                bg=self.colors["panel"],
                fg=self.colors["fg"],
                highlightthickness=0,
                troughcolor=self.colors["entry"],
                activebackground=self.colors["accent"],
                length=108,
                command=self.on_digit_slider_changed,
            )
            scale.grid(row=row + 1, column=col, sticky="ew", padx=(0, 4), pady=(0, 2))
            self.tk_scale_widgets.append(scale)

        ttk.Label(geom, text="Thickness", style="Panel.TLabel").grid(row=row, column=2, columnspan=2, sticky="w", pady=(0, 1))
        self.thickness_scale = tk.Scale(
            geom,
            from_=1,
            to=40,
            orient="horizontal",
            variable=self.naca_thickness_var,
            showvalue=True,
            resolution=1,
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            highlightthickness=0,
            troughcolor=self.colors["entry"],
            activebackground=self.colors["accent"],
            length=220,
            command=self.on_digit_slider_changed,
        )
        self.thickness_scale.grid(row=row + 1, column=2, columnspan=2, sticky="ew", padx=(0, 4), pady=(0, 2))
        self.tk_scale_widgets.append(self.thickness_scale)

        row += 2
        ttk.Label(geom, text="Chord [mm]", style="Panel.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=(3, 1))
        e = ttk.Entry(geom, textvariable=self.chord_var, width=10)
        e.grid(row=row, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(geom, text="Span [mm]", style="Panel.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=(3, 1))
        e = ttk.Entry(geom, textvariable=self.span_var, width=10)
        e.grid(row=row, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        self.chord_scale = tk.Scale(
            geom,
            from_=10,
            to=2000,
            orient="horizontal",
            variable=self.chord_var,
            showvalue=False,
            resolution=1,
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            highlightthickness=0,
            troughcolor=self.colors["entry"],
            activebackground=self.colors["accent"],
            command=lambda _value: self.schedule_update(),
        )
        self.chord_scale.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self.tk_scale_widgets.append(self.chord_scale)

        self.span_scale = tk.Scale(
            geom,
            from_=10,
            to=5000,
            orient="horizontal",
            variable=self.span_var,
            showvalue=False,
            resolution=1,
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            highlightthickness=0,
            troughcolor=self.colors["entry"],
            activebackground=self.colors["accent"],
            command=lambda _value: self.schedule_update(),
        )
        self.span_scale.grid(row=row, column=2, columnspan=2, sticky="ew", pady=(0, 2))
        self.tk_scale_widgets.append(self.span_scale)

        trans = ttk.LabelFrame(left, text="Transform", padding=8)
        trans.pack(fill="x", pady=(8, 0))
        trans.columnconfigure(1, weight=1)
        trans.columnconfigure(3, weight=1)

        row = 0
        ttk.Label(trans, text="Radius [mm]", style="Panel.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=1)
        self.radius_entry = ttk.Entry(trans, textvariable=self.radius_var, width=10)
        self.radius_entry.grid(row=row, column=1, sticky="ew", pady=2)
        self.radius_entry.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(trans, text="Curvature", style="Panel.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=1)
        self.curv_dir_combo = ttk.Combobox(
            trans,
            textvariable=self.curvature_dir_var,
            values=["convex", "concave"],
            state="readonly",
            width=10,
        )
        self.curv_dir_combo.grid(row=row, column=3, sticky="ew", pady=2)
        self.curv_dir_combo.bind("<<ComboboxSelected>>", self.schedule_update)

        row += 1
        ttk.Checkbutton(
            trans,
            text="Mirror X axis",
            variable=self.mirror_x_var,
            command=self.update_preview,
        ).grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        ttk.Checkbutton(
            trans,
            text="Mirror Y axis",
            variable=self.mirror_y_var,
            command=self.update_preview,
        ).grid(row=row, column=1, sticky="w", pady=2)
        ttk.Label(trans, text="Rotation [deg]", style="Panel.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=1)
        e = ttk.Entry(trans, textvariable=self.angle_var, width=10)
        e.grid(row=row, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        self.rotation_scale = tk.Scale(
            trans,
            from_=-60,
            to=60,
            orient="horizontal",
            variable=self.angle_var,
            showvalue=False,
            resolution=1,
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            highlightthickness=0,
            troughcolor=self.colors["entry"],
            activebackground=self.colors["accent"],
            command=lambda _value: self.schedule_update(),
        )
        self.rotation_scale.grid(row=row, column=2, columnspan=2, sticky="ew", pady=(0, 2))
        self.tk_scale_widgets.append(self.rotation_scale)

        aero = ttk.LabelFrame(left, text="Flight Estimate", padding=8)
        aero.pack(fill="x", pady=(8, 0))
        aero.columnconfigure(1, weight=1)
        aero.columnconfigure(3, weight=1)
        self.aero_frame = aero

        arow = 0
        ttk.Label(aero, text="Fluid", style="Panel.TLabel").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=1)
        self.fluid_combo = ttk.Combobox(
            aero,
            textvariable=self.fluid_var,
            values=["air", "water", "salt water", "custom"],
            state="readonly",
            width=10,
        )
        self.fluid_combo.grid(row=arow, column=1, sticky="ew", pady=2)
        self.fluid_combo.bind("<<ComboboxSelected>>", self.on_fluid_changed)
        ttk.Label(aero, text="Velocity [km/h]", style="Panel.TLabel").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=1)
        e = ttk.Entry(aero, textvariable=self.velocity_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        # Advanced readonly field kept so Geometry can still drive a hidden
        # aerodynamic chord input. Re-show this row if you want the user to
        # inspect the linked value directly.
        ttk.Label(aero, text="Aero chord [mm]").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        self.aero_chord_entry = ttk.Entry(aero, textvariable=self.aero_chord_var, width=10, state="readonly")
        self.aero_chord_entry.grid(row=arow, column=1, sticky="ew", pady=2)

        self.velocity_scale = tk.Scale(
            aero,
            from_=1,
            to=300,
            orient="horizontal",
            variable=self.velocity_var,
            showvalue=False,
            resolution=1,
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            highlightthickness=0,
            troughcolor=self.colors["entry"],
            activebackground=self.colors["accent"],
            command=lambda _value: self.schedule_update(),
        )
        self.velocity_scale.grid(row=arow, column=2, columnspan=2, sticky="ew", pady=(18, 2))
        self.tk_scale_widgets.append(self.velocity_scale)


        arow += 1
        self.density_entry = ttk.Entry(aero, textvariable=self.density_var, width=10)
        self.density_entry.grid(row=arow, column=1, sticky="ew", pady=2)
        self.density_entry.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Viscosity [Pa*s]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        self.viscosity_entry = ttk.Entry(aero, textvariable=self.viscosity_var, width=10)
        self.viscosity_entry.grid(row=arow, column=3, sticky="ew", pady=2)
        self.viscosity_entry.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="Override cd0").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.override_cd0_var, width=10)
        e.grid(row=arow, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Override k").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.override_k_drag_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="Override cl_max").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.override_cl_max_var, width=10)
        e.grid(row=arow, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Override alpha0 [deg]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.override_alpha0_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Separator(aero, orient="horizontal").grid(row=arow, column=0, columnspan=4, sticky="ew", pady=3)

        arow += 1
        ttk.Label(aero, text="Reynolds [-]").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.reynolds_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="CL").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.cl_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="CD").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.cd_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, textvariable=self.lift_label_var).grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.lift_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, textvariable=self.drag_label_var).grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.drag_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="L/D").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.ld_out_var).grid(row=arow, column=1, sticky="w", pady=1)

        actions = ttk.LabelFrame(left, text="Export & Tools", padding=8)
        actions.pack(fill="x", pady=(8, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="STL", command=self.save_stl).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        ttk.Button(actions, text="PTS", command=self.save_pts).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)
        ttk.Button(actions, text="DXF", command=self.save_dxf).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)
        ttk.Button(actions, text="CSV", command=self.save_csv).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)
        ttk.Button(actions, text="Copy", command=self.copy_preview).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 2))
        ttk.Button(actions, text="Advanced options", command=self.open_advanced_options).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(4, 1),
        )

        right_panes = ttk.Panedwindow(right, orient="vertical")
        right_panes.pack(fill="both", expand=True)
        self.right_panes = right_panes

        graph_frame = ttk.LabelFrame(right_panes, text="Live Profile", padding=8)
        bottom_frame = ttk.Frame(right_panes)
        right_panes.add(graph_frame, weight=4)
        right_panes.add(bottom_frame, weight=1)

        graph_toolbar = ttk.Frame(graph_frame, style="Panel.TFrame")
        graph_toolbar.pack(fill="x", pady=(0, 4))
        ttk.Label(graph_toolbar, text="View", style="Panel.TLabel").pack(side="left")
        self.view_mode_var = tk.StringVar(value="2D")
        self.view_mode_combo = ttk.Combobox(
            graph_toolbar,
            textvariable=self.view_mode_var,
            values=["2D", "3D"],
            state="readonly",
            width=8,
        )
        self.view_mode_combo.pack(side="left", padx=(6, 0))
        self.view_mode_combo.bind("<<ComboboxSelected>>", self.on_view_mode_changed)
        ttk.Label(
            graph_toolbar,
            text="Mouse wheel zoom | drag to pan or rotate",
            style="Muted.TLabel",
        ).pack(side="right")

        self.figure = Figure(figsize=(7, 3.55), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.035, right=0.985, bottom=0.055, top=0.955)
        self.configure_plot_theme()

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("scroll_event", self.on_plot_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_plot_button_press)
        self.canvas.mpl_connect("button_release_event", self.on_plot_button_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_plot_mouse_move)

        kpi_frame = ttk.LabelFrame(bottom_frame, text="Estimated Forces", padding=8)
        kpi_frame.pack(fill="x", expand=False, pady=(8, 0))
        kpi_frame.columnconfigure(1, weight=1)
        kpi_frame.columnconfigure(3, weight=1)
        ttk.Label(kpi_frame, textvariable=self.lift_label_var, style="SummaryLabel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 4))
        ttk.Label(kpi_frame, textvariable=self.lift_out_var, style="KPIValue.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 18))
        ttk.Label(kpi_frame, textvariable=self.drag_label_var, style="SummaryLabel.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 4))
        ttk.Label(kpi_frame, textvariable=self.drag_out_var, style="KPIValueAlt.TLabel").grid(row=0, column=3, sticky="w")

        preview_frame = ttk.LabelFrame(bottom_frame, text="Point Preview", padding=8)
        preview_frame.pack(fill="x", expand=False, pady=(8, 0))

        summary = ttk.Frame(preview_frame, style="Panel.TFrame")
        summary.pack(fill="x", pady=(0, 4))
        summary_labels = [
            ("Mode", self.preview_mode_var),
            ("Points", self.preview_points_var),
            ("Format", self.preview_format_var),
        ]
        for idx, (lbl, var) in enumerate(summary_labels):
            col = idx * 2
            summary.columnconfigure(col + 1, weight=1)
            ttk.Label(summary, text=lbl, style="SummaryLabel.TLabel").grid(row=0, column=col, sticky="w", padx=(0, 4))
            ttk.Label(summary, textvariable=var, style="SummaryValue.TLabel").grid(row=0, column=col + 1, sticky="w", padx=(0, 12))

        text_row = ttk.Frame(preview_frame, style="Panel.TFrame")
        text_row.pack(fill="x", expand=False)

        self.text = tk.Text(
            text_row,
            wrap="none",
            font=("Consolas", 10),
            height=2,
            bg=self.colors["entry"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            selectbackground=self.colors["selection"],
            relief="flat",
            borderwidth=1,
            padx=6,
            pady=6,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["accent"],
        )
        self.text.pack(side="left", fill="x", expand=True)

        yscroll = ttk.Scrollbar(text_row, orient="vertical", command=self.text.yview)
        yscroll.pack(side="right", fill="y")
        xscroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.text.xview)
        xscroll.pack(fill="x", pady=(2, 0))
        self.text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        footer = ttk.Label(
            right,
            text="Manta AirLab | Fabio Giuliodori — Explore https://duilio.cc",
            style="Footer.TLabel",
        )
        footer.pack(anchor="e", pady=(10, 0))
        self.setup_variable_sync()
        self.root.after_idle(self.initialize_pane_layout)

    def configure_plot_theme(self):
        self.figure.patch.set_facecolor(self.colors["plot_bg"])
        self.ax.set_facecolor(self.colors["plot_bg"])
        self.ax.tick_params(colors=self.colors["fg"])
        if hasattr(self.ax, "spines"):
            for spine in self.ax.spines.values():
                spine.set_color(self.colors["muted"])
        self.ax.title.set_color(self.colors["fg"])
        self.ax.xaxis.label.set_color(self.colors["fg"])
        self.ax.yaxis.label.set_color(self.colors["fg"])
        if hasattr(self.ax, "zaxis"):
            self.ax.zaxis.label.set_color(self.colors["fg"])
            for axis in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                try:
                    axis.pane.set_facecolor(self.colors["panel_alt"])
                    axis.pane.set_edgecolor(self.colors["muted"])
                except Exception:
                    pass
                try:
                    axis._axinfo["grid"]["color"] = self.colors["grid"]
                except Exception:
                    pass

    def configure_figure_layout(self, mode):
        if mode == "3d":
            self.figure.subplots_adjust(left=0.03, right=0.985, bottom=0.05, top=0.95)
            try:
                self.ax.set_position([0.015, 0.07, 0.97, 0.84])
            except Exception:
                pass
        else:
            self.figure.subplots_adjust(left=0.055, right=0.985, bottom=0.08, top=0.94)
            try:
                self.ax.set_position([0.06, 0.12, 0.91, 0.76])
            except Exception:
                pass

    def ensure_plot_axes(self, mode):
        projection = "3d" if mode == "3d" else None
        current_name = getattr(self.ax, "name", "")
        if current_name != ("3d" if mode == "3d" else "rectilinear"):
            self.figure.delaxes(self.ax)
            if projection is None:
                self.ax = self.figure.add_subplot(111)
            else:
                self.ax = self.figure.add_subplot(111, projection=projection)
        self.plot_mode = mode
        self.configure_figure_layout(mode)
        self.configure_plot_theme()

    def on_view_mode_changed(self, event=None):
        selected = self.view_mode_var.get().strip().upper()
        mode = "3d" if selected == "3D" else "2d"
        self.ensure_plot_axes(mode)
        self.update_preview()

    def initialize_pane_layout(self):
        try:
            self.root.update_idletasks()
            total_width = max(self.main_panes.winfo_width(), 2)
            self.main_panes.sashpos(0, total_width // 2)

            total_height = max(self.right_panes.winfo_height(), 2)
            self.right_panes.sashpos(0, int(total_height * 0.66))
        except Exception:
            pass

    def on_plot_scroll(self, event):
        if event.inaxes != self.ax:
            return

        button = getattr(event, "button", "")
        step = getattr(event, "step", 0)
        zoom_in = button == "up" or step > 0
        scale = 1.0 / 1.15 if zoom_in else 1.15

        if getattr(self.ax, "name", "") == "3d":
            self.zoom_3d_axes(scale)
        else:
            self.zoom_2d_axes(scale, event.xdata, event.ydata)

        self.canvas.draw_idle()

    def on_plot_button_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return

        if getattr(self.ax, "name", "") == "3d":
            self._pan_state = {
                "mode": "3d",
                "x": event.x,
                "y": event.y,
                "xlim": self.ax.get_xlim3d(),
                "ylim": self.ax.get_ylim3d(),
                "zlim": self.ax.get_zlim3d(),
            }
        else:
            if event.xdata is None or event.ydata is None:
                return
            self._pan_state = {
                "mode": "2d",
                "xdata": event.xdata,
                "ydata": event.ydata,
                "xlim": self.ax.get_xlim(),
                "ylim": self.ax.get_ylim(),
            }

    def on_plot_button_release(self, event):
        if event.button == 1:
            self._pan_state = None

    def on_plot_mouse_move(self, event):
        if not self._pan_state:
            return
        if event.inaxes != self.ax:
            return

        if self._pan_state["mode"] == "3d":
            self.pan_3d_axes(event)
        else:
            self.pan_2d_axes(event)

        self.canvas.draw_idle()

    def zoom_2d_axes(self, scale, x_center=None, y_center=None):
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        if x_center is None:
            x_center = 0.5 * (xmin + xmax)
        if y_center is None:
            y_center = 0.5 * (ymin + ymax)

        new_xmin = x_center - (x_center - xmin) * scale
        new_xmax = x_center + (xmax - x_center) * scale
        new_ymin = y_center - (y_center - ymin) * scale
        new_ymax = y_center + (ymax - y_center) * scale

        self.ax.set_xlim(new_xmin, new_xmax)
        self.ax.set_ylim(new_ymin, new_ymax)

    def zoom_3d_axes(self, scale):
        xlim = self.ax.get_xlim3d()
        ylim = self.ax.get_ylim3d()
        zlim = self.ax.get_zlim3d()

        def _scaled_limits(limits):
            lo, hi = limits
            center = 0.5 * (lo + hi)
            half = 0.5 * (hi - lo) * scale
            min_half = 0.5
            half = max(half, min_half)
            return center - half, center + half

        self.ax.set_xlim3d(*_scaled_limits(xlim))
        self.ax.set_ylim3d(*_scaled_limits(ylim))
        self.ax.set_zlim3d(*_scaled_limits(zlim))

    def pan_2d_axes(self, event):
        if event.xdata is None or event.ydata is None:
            return

        state = self._pan_state
        dx = event.xdata - state["xdata"]
        dy = event.ydata - state["ydata"]
        xmin, xmax = state["xlim"]
        ymin, ymax = state["ylim"]
        self.ax.set_xlim(xmin - dx, xmax - dx)
        self.ax.set_ylim(ymin - dy, ymax - dy)

    def pan_3d_axes(self, event):
        state = self._pan_state
        dx_px = event.x - state["x"]
        dy_px = event.y - state["y"]

        xlim = state["xlim"]
        ylim = state["ylim"]
        zlim = state["zlim"]
        x_span = xlim[1] - xlim[0]
        y_span = ylim[1] - ylim[0]
        z_span = zlim[1] - zlim[0]

        pixel_ref = max(float(self.canvas.get_tk_widget().winfo_width()), float(self.canvas.get_tk_widget().winfo_height()), 1.0)
        shift_x = -(dx_px / pixel_ref) * x_span
        shift_y = (dy_px / pixel_ref) * y_span
        shift_z = (dy_px / pixel_ref) * z_span * 0.35

        self.ax.set_xlim3d(xlim[0] + shift_x, xlim[1] + shift_x)
        self.ax.set_ylim3d(ylim[0] + shift_y, ylim[1] + shift_y)
        self.ax.set_zlim3d(zlim[0] + shift_z, zlim[1] + shift_z)

    def mode_internal_value(self):
        return self.mode_map.get(self.mode_var.get().strip(), "flat")

    def on_mode_changed(self, event=None):
        self.update_mode_fields()
        self.update_preview()

    def update_mode_fields(self):
        is_curved = self.mode_internal_value() == "curved"
        state = "normal" if is_curved else "disabled"
        readonly_state = "readonly" if is_curved else "disabled"

        self.radius_entry.config(state=state)
        self.curv_dir_combo.config(state=readonly_state)
        if self.advanced_radius_entry is not None:
            try:
                self.advanced_radius_entry.config(state=state)
            except Exception:
                pass
        if self.advanced_curv_dir_combo is not None:
            try:
                self.advanced_curv_dir_combo.config(state=readonly_state)
            except Exception:
                pass
        self.keep_developed_var.set(True)

    def on_fluid_changed(self, event=None):
        fluid = self.fluid_var.get().strip().lower()
        if fluid in FLUID_PRESETS:
            self.density_var.set(str(FLUID_PRESETS[fluid]["rho"]))
            self.viscosity_var.set(str(FLUID_PRESETS[fluid]["mu"]))
        self.update_fluid_fields()
        self.update_preview()

    def update_fluid_fields(self):
        fluid = self.fluid_var.get().strip().lower()
        state = "normal" if fluid == "custom" else "disabled"
        self.density_entry.config(state=state)
        self.viscosity_entry.config(state=state)

    def update_expert_visibility(self):
        # Advanced rows are currently hidden on purpose to keep the release UI
        # compact. To re-enable them, remove the target rows from
        # `always_hidden_rows` and optionally restore a visible Expert toggle.
        # Row 1 keeps only the velocity slider visible; rows 2+ are advanced.
        always_hidden_rows = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}

        for widget in self.aero_frame.grid_slaves():
            image_value = ""
            try:
                image_value = str(widget.cget("image"))
            except Exception:
                image_value = ""

            if image_value:
                widget.grid_remove()
                continue

            row = int(widget.grid_info().get("row", -1))
            column = int(widget.grid_info().get("column", -1))
            if row == 1 and column < 2:
                widget.grid_remove()
                continue
            if row in always_hidden_rows:
                widget.grid_remove()

    def schedule_update(self, event=None):
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
        self._update_job = self.root.after(200, self.update_preview)

    def setup_variable_sync(self):
        self.code_var.trace_add("write", self.on_code_var_changed)
        self.chord_var.trace_add("write", self.on_geometry_link_changed)
        self.angle_var.trace_add("write", self.on_geometry_link_changed)
        self.sync_digit_vars_from_code()
        self.sync_aero_inputs_from_geometry()
        self.update_expert_visibility()

    def on_geometry_link_changed(self, *_args):
        self.sync_aero_inputs_from_geometry()
        self.schedule_update()

    def sync_aero_inputs_from_geometry(self):
        self.aero_chord_var.set(self.chord_var.get())
        try:
            alpha = float(self.angle_var.get().replace(",", "."))
            self.alpha_attack_var.set(f"{alpha:g}")
        except ValueError:
            self.alpha_attack_var.set("")

    def on_code_var_changed(self, *_args):
        if self._syncing_code:
            return
        self.sync_digit_vars_from_code()

    def sync_digit_vars_from_code(self):
        code = self.code_var.get().strip()
        if len(code) != 4 or not code.isdigit():
            return
        camber, pos, thickness = self.normalize_naca_digits(int(code[0]), int(code[1]), int(code[2:4]))
        normalized_code = f"{camber}{pos}{thickness:02d}"
        self._syncing_code = True
        try:
            self.naca_camber_var.set(camber)
            self.naca_pos_var.set(pos)
            self.naca_thickness_var.set(thickness)
            if code != normalized_code:
                self.code_var.set(normalized_code)
        finally:
            self._syncing_code = False

    @staticmethod
    def normalize_naca_digits(camber, pos, thickness):
        camber = max(0, min(int(camber), 9))
        pos = max(0, min(int(pos), 9))
        thickness = max(1, min(int(thickness), 40))
        if camber != 0 and pos == 0:
            pos = 1
        return camber, pos, thickness

    def on_digit_spinbox_changed(self, _event=None):
        self.root.after_idle(self._sync_digit_spinboxes)

    def _sync_digit_spinboxes(self):
        if self._syncing_code:
            return
        try:
            camber = self.naca_camber_var.get()
            pos = self.naca_pos_var.get()
            thickness = self.naca_thickness_var.get()
        except (tk.TclError, ValueError):
            return
        camber, pos, thickness = self.normalize_naca_digits(camber, pos, thickness)
        self.naca_camber_var.set(camber)
        self.naca_pos_var.set(pos)
        self.naca_thickness_var.set(thickness)
        self.on_digit_slider_changed()

    def on_digit_slider_changed(self, _value=None):
        if self._syncing_code:
            return
        camber, pos, thickness = self.normalize_naca_digits(
            self.naca_camber_var.get(),
            self.naca_pos_var.get(),
            self.naca_thickness_var.get(),
        )
        self.naca_camber_var.set(camber)
        self.naca_pos_var.set(pos)
        self.naca_thickness_var.set(thickness)
        self._syncing_code = True
        try:
            self.code_var.set(f"{camber}{pos}{thickness:02d}")
        finally:
            self._syncing_code = False
        self.schedule_update()

    @staticmethod
    def _parse_optional_float(txt):
        raw = txt.strip()
        if not raw:
            return None
        return float(raw.replace(",", "."))

    def compute_aero_results(self, vals, alpha_override=None):
        code = vals["code"]
        alpha = vals["angle_deg"] if alpha_override is None else float(alpha_override)
        if vals["mirror_x"]:
            # For an inverted section, the visually intuitive rotation that
            # increases downforce is opposite to the baseline aero sign.
            alpha = -alpha
        velocity_kmh = float(self.velocity_var.get().replace(",", "."))
        span_mm = float(self.span_var.get().replace(",", "."))
        velocity = velocity_kmh / 3.6
        chord = vals["chord"]
        span = span_mm / 1000.0

        fluid = self.fluid_var.get().strip().lower()
        if fluid in FLUID_PRESETS:
            density = FLUID_PRESETS[fluid]["rho"]
            viscosity = FLUID_PRESETS[fluid]["mu"]
        else:
            density = float(self.density_var.get().replace(",", "."))
            viscosity = float(self.viscosity_var.get().replace(",", "."))

        area = chord * span
        if velocity <= 0:
            raise ValueError("Velocity must be greater than zero.")
        if span <= 0:
            raise ValueError("Span must be greater than zero.")

        reynolds = compute_reynolds(velocity, chord, density, viscosity)
        overrides = {
            "cd0": self._parse_optional_float(self.override_cd0_var.get()),
            "k_drag": self._parse_optional_float(self.override_k_drag_var.get()),
            "cl_max": self._parse_optional_float(self.override_cl_max_var.get()),
            "alpha_zero_lift_deg": self._parse_optional_float(self.override_alpha0_var.get()),
        }
        params = get_airfoil_parameters(
            code=code,
            reynolds=reynolds,
            use_internal_library=True,
            overrides=overrides,
        )
        cl, cd = compute_cl_cd(alpha_deg=alpha, params=params)
        if vals["mirror_x"]:
            cl = -cl
        lift, drag, ld_ratio = compute_lift_drag(density=density, velocity=velocity, area=area, cl=cl, cd=cd)

        return {
            "reynolds": reynolds,
            "cl": cl,
            "cd": cd,
            "lift": lift,
            "drag": drag,
            "ld_ratio": ld_ratio,
            "params_source": params.get("source", "fallback"),
        }

    def update_aero_display(self, aero):
        if aero is None:
            self.reynolds_out_var.set("-")
            self.cl_out_var.set("-")
            self.cd_out_var.set("-")
            self.lift_out_var.set("-")
            self.drag_out_var.set("-")
            self.ld_out_var.set("-")
            self.lift_label_var.set("Lift [kg]")
            self.drag_label_var.set("Drag [kg]")
            return
        self.reynolds_out_var.set(f"{aero['reynolds']:.3e}")
        self.cl_out_var.set(f"{aero['cl']:.4f}")
        self.cd_out_var.set(f"{aero['cd']:.4f}")
        lift_kg = aero["lift"] / 9.80665
        drag_kg = aero["drag"] / 9.80665
        self.lift_label_var.set("Downforce [kg]" if lift_kg < 0 else "Lift [kg]")
        self.drag_label_var.set("Drag [kg]")
        self.lift_out_var.set(f"{lift_kg:.1f}")
        self.drag_out_var.set(f"{drag_kg:.1f}")
        self.ld_out_var.set(f"{aero['ld_ratio']:.3f}")

    def get_values(self):
        mode = self.mode_internal_value()
        code = self.code_var.get().strip()
        chord_mm = float(self.chord_var.get().replace(",", "."))
        chord = chord_mm / 1000.0
        span_mm = float(self.span_var.get().replace(",", "."))
        span = span_mm / 1000.0
        n_side = int(self.n_side_var.get())
        angle_deg = float(self.angle_var.get().replace(",", "."))
        decimals = int(self.decimals_var.get())

        if chord <= 0:
            raise ValueError("Chord must be greater than zero.")
        if span <= 0:
            raise ValueError("Span must be greater than zero.")
        if n_side < 2:
            raise ValueError("Points per side must be at least 2.")
        if decimals < 0 or decimals > 12:
            raise ValueError("Decimals must be between 0 and 12.")
        if mode not in {"flat", "curved"}:
            raise ValueError("Invalid mode.")

        radius = None
        if mode == "curved":
            radius_mm = float(self.radius_var.get().replace(",", "."))
            radius = radius_mm / 1000.0
            if radius <= 0:
                raise ValueError("Curvature radius must be greater than zero.")

        curvature_dir = self.curvature_dir_var.get().strip().lower()
        if curvature_dir not in {"convex", "concave"}:
            curvature_dir = "convex"

        return {
            "mode": mode,
            "code": code,
            "chord": chord,
            "span": span,
            "n_side": n_side,
            "radius": radius,
            "curvature_dir": curvature_dir,
            "keep_developed_chord": True,
            "angle_deg": angle_deg,
            "decimals": decimals,
            "mirror_x": self.mirror_x_var.get(),
            "mirror_y": self.mirror_y_var.get(),
        }

    def update_preview(self):
        self._update_job = None
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)
            pts_fmt = self.pts_format_var.get().strip().lower()
            if pts_fmt == "xy":
                pts_text, x, y, _ = write_pts_xy_text(x, y, decimals=vals["decimals"])
            else:
                pts_text, x, y, _ = write_pts_text(x, y, decimals=vals["decimals"])
            mode_label = "Flat" if vals["mode"] == "flat" else "Curved"
            self.header_profile_var.set(f"NACA {vals['code']}")
            self.header_status_var.set(
                f"{mode_label} profile | chord {vals['chord'] * 1000:.0f} mm | span {vals['span'] * 1000:.0f} mm"
            )
            self.preview_mode_var.set(mode_label)
            self.preview_points_var.set(str(len(x)))
            self.preview_format_var.set(pts_fmt.upper())
            # With the UI convention, positive clockwise rotation corresponds to
            # positive aerodynamic angle of attack. Mirror X flips lift sign.
            # Mirror Y still disables aero because it reverses the profile
            # against the assumed left-to-right flow of this simplified model.
            aero_enabled = vals["mode"] == "flat" and not vals["mirror_y"]
            aero = self.compute_aero_results(vals) if aero_enabled else None

            self.last_pts_text = pts_text
            self.last_x = x
            self.last_y = y

            self.text.delete("1.0", "end")
            self.text.insert("1.0", pts_text)
            self.update_aero_display(aero)

            self.redraw_plot(x, y, vals, aero)
        except Exception as e:
            self.header_profile_var.set("Profile")
            self.header_status_var.set("Check the current inputs")
            self.preview_mode_var.set("-")
            self.preview_points_var.set("-")
            self.preview_format_var.set("-")
            self.reynolds_out_var.set("-")
            self.cl_out_var.set("-")
            self.cd_out_var.set("-")
            self.lift_out_var.set("-")
            self.drag_out_var.set("-")
            self.ld_out_var.set("-")
            self.last_pts_text = ""
            self.last_x = None
            self.last_y = None
            self.text.delete("1.0", "end")
            self.show_plot_error(str(e))

    def compute_force_references(self, vals):
        max_lift = 1e-9
        max_drag = 1e-9
        for alpha in np.linspace(0.0, 90.0, 19):
            aero = self.compute_aero_results(vals, alpha_override=float(alpha))
            max_lift = max(max_lift, abs(aero["lift"]))
            max_drag = max(max_drag, abs(aero["drag"]))
        return {
            "lift": max_lift,
            "drag": max_drag,
        }

    def redraw_plot(self, x, y, vals, aero):
        plot_mode = "3d" if self.view_mode_var.get().strip().upper() == "3D" else "2d"
        self.ensure_plot_axes(plot_mode)
        if plot_mode == "3d":
            self.redraw_plot_3d(x, y, vals)
            return

        self.redraw_plot_2d(x, y, vals, aero)

    def redraw_plot_2d(self, x, y, vals, aero):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["plot_bg"])
        x_mm = np.array(x) * 1000.0
        y_mm = np.array(y) * 1000.0
        line_color = self.colors["accent"]
        self.ax.plot(x_mm, y_mm, marker=".", markersize=2, linewidth=1.3, color=line_color)

        mode_txt = "Flat profile" if vals["mode"] == "flat" else "Curved profile"
        title = (
            f"NACA {vals['code']} | chord={vals['chord'] * 1000:.1f} mm | "
            f"span={vals['span'] * 1000:.1f} mm | {mode_txt}"
        )
        if vals["mode"] == "curved":
            title += f" | R={vals['radius'] * 1000:.1f} mm"
        if vals["angle_deg"]:
            title += f" | rot={vals['angle_deg']} deg"

        self.ax.set_title(title)
        self.ax.set_xlabel("X [mm]")
        self.ax.set_ylabel("Y [mm]")
        self.ax.grid(True, color=self.colors["grid"], alpha=0.7, linestyle="--", linewidth=0.6)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.tick_params(colors=self.colors["fg"])
        self.ax.xaxis.label.set_color(self.colors["fg"])
        self.ax.yaxis.label.set_color(self.colors["fg"])
        self.ax.title.set_color(self.colors["fg"])
        for spine in self.ax.spines.values():
            spine.set_color(self.colors["muted"])

        try:
            velocity_kmh = float(self.velocity_var.get().replace(",", "."))
        except ValueError:
            velocity_kmh = 0.0

        if len(x_mm) > 0:
            xmin, xmax = float(np.min(x_mm)), float(np.max(x_mm))
            ymin, ymax = float(np.min(y_mm)), float(np.max(y_mm))
            dx = xmax - xmin
            dy = ymax - ymin
            base = max(vals["chord"] * 1000.0 * 0.02, 1e-6)
            x_center = 0.5 * (xmin + xmax)
            y_center = 0.5 * (ymin + ymax)
            span_ref = max(dx, dy, vals["chord"] * 1000.0)
            pad_x = max(dx * 0.08, base)
            pad_y = max(dy * 0.12, base)
            drag_arrow = None
            flow_arrow_len = None
            if aero is not None:
                arrow_ref = max(span_ref * 0.28, 12.0)
                force_refs = self.compute_force_references(vals)
                force_scale = max(force_refs["lift"], force_refs["drag"], 1e-9)
                min_force_arrow = max(span_ref * 0.06, 6.0)
                lift_len = max(arrow_ref * (abs(aero["lift"]) / force_scale), min_force_arrow)
                drag_len = max(arrow_ref * (abs(aero["drag"]) / force_scale), min_force_arrow)
                flow_arrow_len = lift_len + drag_len
                lift_tip_y = y_center + (lift_len if aero["lift"] >= 0 else -lift_len)

                self.ax.annotate(
                    "",
                    xy=(x_center, lift_tip_y),
                    xytext=(x_center, y_center),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=self.colors["lift"],
                        lw=1.6,
                        mutation_scale=11,
                        shrinkA=0,
                        shrinkB=0,
                    ),
                )
                xmin = min(xmin, x_center)
                xmax = max(xmax, x_center)
                ymin = min(ymin, y_center, lift_tip_y)
                ymax = max(ymax, y_center, lift_tip_y)

                drag_arrow = {
                    "length": drag_len,
                    "origin_x": x_center,
                    "origin_y": y_center,
                }

            flow_y = ymax + pad_y * 0.45
            flow_x0 = xmin - pad_x * 0.25
            if flow_arrow_len is None:
                flow_arrow_len = compute_flow_arrow_length(span_ref, velocity_kmh)
            flow_x1 = flow_x0 + flow_arrow_len
            self.ax.annotate(
                "",
                xy=(flow_x1, flow_y),
                xytext=(flow_x0, flow_y),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=self.colors["muted"],
                    lw=1.6,
                    mutation_scale=11,
                    alpha=0.85,
                    shrinkA=0,
                    shrinkB=0,
                ),
            )

            if drag_arrow is not None:
                drag_x0 = drag_arrow["origin_x"]
                drag_band_y = drag_arrow["origin_y"]
                drag_tip_x = drag_x0 + drag_arrow["length"]
                self.ax.annotate(
                    "",
                    xy=(drag_tip_x, drag_band_y),
                    xytext=(drag_x0, drag_band_y),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=self.colors["drag"],
                        lw=1.6,
                        mutation_scale=11,
                        shrinkA=0,
                        shrinkB=0,
                    ),
                )
                xmin = min(xmin, drag_x0, drag_tip_x)
                xmax = max(xmax, drag_tip_x)
                ymin = min(ymin, drag_band_y)
                ymax = max(ymax, drag_band_y)

            xmax = max(xmax, flow_x1)
            ymax = max(ymax, flow_y)
            self.ax.set_xlim(xmin - pad_x, xmax + pad_x)
            self.ax.set_ylim(ymin - pad_y, ymax + pad_y)

        self.canvas.draw_idle()

    def redraw_plot_3d(self, x, y, vals):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["plot_bg"])
        mesh = build_extruded_mesh(x, y, vals["span"])
        root_mm = mesh["root"] * 1000.0
        tip_mm = mesh["tip"] * 1000.0
        side_quads_mm = [[vertex * 1000.0 for vertex in quad] for quad in mesh["side_quads"]]
        root_cap_mm = [vertex * 1000.0 for vertex in mesh["root_cap"]]
        tip_cap_mm = [vertex * 1000.0 for vertex in mesh["tip_cap"]]

        poly = Poly3DCollection(
            side_quads_mm,
            facecolors=self.colors["accent"],
            edgecolors=self.colors["plot_bg"],
            linewidths=0.35,
            alpha=0.35,
        )
        self.ax.add_collection3d(poly)

        cap_poly = Poly3DCollection(
            [root_cap_mm, tip_cap_mm],
            facecolors=[self.colors["plot_fill"], self.colors["plot_fill_alt"]],
            edgecolors=self.colors["muted"],
            linewidths=0.7,
            alpha=0.48,
        )
        self.ax.add_collection3d(cap_poly)

        root_closed = np.vstack([root_mm, root_mm[0]])
        tip_closed = np.vstack([tip_mm, tip_mm[0]])
        self.ax.plot(root_closed[:, 0], root_closed[:, 1], root_closed[:, 2], color=self.colors["accent"], linewidth=1.4)
        self.ax.plot(tip_closed[:, 0], tip_closed[:, 1], tip_closed[:, 2], color=self.colors["accent_alt"], linewidth=1.4)

        step = max(1, len(root_mm) // 24)
        for i in range(0, len(root_mm), step):
            rib = np.vstack([root_mm[i], tip_mm[i]])
            self.ax.plot(rib[:, 0], rib[:, 1], rib[:, 2], color=self.colors["muted"], linewidth=0.7, alpha=0.8)

        mode_txt = "Flat profile" if vals["mode"] == "flat" else "Curved profile"
        title = (
            f"NACA {vals['code']} | chord={vals['chord'] * 1000:.1f} mm | "
            f"span={vals['span'] * 1000:.1f} mm | {mode_txt}"
        )
        self.ax.set_title(title)
        self.ax.set_xlabel("X [mm]")
        self.ax.set_ylabel("Y [mm]")
        self.ax.set_zlabel("Z [mm]")
        self.ax.grid(True, color=self.colors["grid"], alpha=0.7, linestyle="--", linewidth=0.6)
        self.ax.tick_params(colors=self.colors["fg"])
        self.ax.set_proj_type("persp")
        try:
            self.ax.set_anchor("C")
        except Exception:
            pass

        xyz = np.vstack([root_mm, tip_mm])
        display = compute_display_limits_3d(xyz)
        self.ax.set_xlim(*display["xlim"])
        self.ax.set_ylim(*display["ylim"])
        self.ax.set_zlim(*display["zlim"])
        try:
            ax_span, ay_span, az_span = display["aspect"]
            self.ax.set_box_aspect(
                (ax_span * 1.45, ay_span * 0.62, az_span * 0.44),
                zoom=1.18,
            )
        except TypeError:
            try:
                self.ax.set_box_aspect((ax_span * 1.45, ay_span * 0.62, az_span * 0.44))
            except Exception:
                pass
        except Exception:
            pass
        self.ax.tick_params(axis="both", which="major", pad=0, labelsize=7)
        try:
            self.ax.zaxis.set_tick_params(pad=0, labelsize=7)
        except Exception:
            pass
        try:
            self.ax.yaxis.labelpad = 2
            self.ax.zaxis.labelpad = 2
            self.ax.xaxis.labelpad = 2
        except Exception:
            pass
        self.ax.view_init(
            elev=self._default_3d_view["elev"],
            azim=self._default_3d_view["azim"],
        )
        self.configure_plot_theme()
        self.canvas.draw_idle()

    def show_plot_error(self, msg):
        self.ensure_plot_axes("2d")
        self.ax.clear()
        self.ax.set_facecolor(self.colors["plot_bg"])
        self.ax.text(0.5, 0.5, msg, ha="center", va="center", wrap=True, color=self.colors["fg"])
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def save_pts(self):
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)
            fmt = self.pts_format_var.get().strip().lower()
            if fmt == "xy":
                pts_text, _, _, _ = write_pts_xy_text(x, y, decimals=vals["decimals"])
            else:
                pts_text, _, _, _ = write_pts_text(x, y, decimals=vals["decimals"])

            default_name = f"NACA{vals['code']}.pts"
            path = filedialog.asksaveasfilename(
                title="Save .pts file",
                defaultextension=".pts",
                initialfile=default_name,
                filetypes=[("PTS files", "*.pts"), ("All files", "*.*")],
            )
            if not path:
                return

            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(pts_text)

            messagebox.showinfo("Saved", f"File saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_csv(self):
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)
            fmt = self.csv_format_var.get().strip().lower()
            if fmt == "xy":
                csv_text, _, _, _ = write_csv_xy_text(x, y, decimals=vals["decimals"])
            else:
                csv_text, _, _, _ = write_csv_xyz_text(x, y, decimals=vals["decimals"])

            default_name = f"NACA{vals['code']}.csv"
            path = filedialog.asksaveasfilename(
                title="Save .csv file",
                defaultextension=".csv",
                initialfile=default_name,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
            if not path:
                return

            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(csv_text)

            messagebox.showinfo("Saved", f"CSV saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_dxf(self):
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)

            default_name = f"NACA{vals['code']}.dxf"
            path = filedialog.asksaveasfilename(
                title="Save .dxf file",
                defaultextension=".dxf",
                initialfile=default_name,
                filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")],
            )
            if not path:
                return

            mode = self.dxf_mode_var.get().strip().lower()
            write_dxf(path, x, y, mode=mode)
            messagebox.showinfo("Saved", f"DXF saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_stl(self):
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)

            default_name = f"NACA{vals['code']}.stl"
            path = filedialog.asksaveasfilename(
                title="Save .stl file",
                defaultextension=".stl",
                initialfile=default_name,
                filetypes=[("STL files", "*.stl"), ("All files", "*.*")],
            )
            if not path:
                return

            write_stl_ascii(path, x, y, vals["span"], solid_name=f"NACA{vals['code']}")
            messagebox.showinfo("Saved", f"STL saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_preview(self):
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
            self._update_job = None
        self.update_preview()
        txt = self.last_pts_text.strip()
        if not txt:
            messagebox.showwarning("Copy unavailable", "No preview text is available to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        self.root.update_idletasks()
        messagebox.showinfo("Copied", "Preview copied to clipboard.")


def main():
    exit_code = run_cli(sys.argv[1:])
    if exit_code is None:
        if not ensure_required_deps():
            return
        root = tk.Tk()
        try:
            style = ttk.Style()
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except Exception:
            pass
        App(root)
        root.mainloop()
        return
    if exit_code != 0:
        raise SystemExit(exit_code)


def _positive_float(value: str, name: str):
    parsed = float(value)
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return parsed


def _positive_int(value: str, name: str, minimum: int = 1):
    parsed = int(value)
    if parsed < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return parsed


def build_cli_parser():
    parser = argparse.ArgumentParser(
        prog="airfoil_tools.py",
        description="Airfoil Tools CLI (GUI remains the default with no arguments).",
    )
    subparsers = parser.add_subparsers(dest="command")

    export_cmd = subparsers.add_parser("export", help="Export NACA 4-digit profile to .pts, .dxf, .stl, or .csv.")
    export_cmd.add_argument("code", help="NACA 4-digit code, e.g. 2412.")
    export_cmd.add_argument(
        "--format",
        choices=["pts", "dxf", "stl", "csv"],
        default=CLI_DEFAULTS["export_format"],
        help="Output format (default: pts).",
    )
    export_cmd.add_argument(
        "--dxf-mode",
        choices=["spline", "polyline"],
        default=CLI_DEFAULTS["dxf_mode"],
        help="DXF entity type (default: spline).",
    )
    export_cmd.add_argument(
        "--pts-format",
        choices=["xyz", "xy"],
        default=CLI_DEFAULTS["pts_format"],
        help="PTS format (default: xyz).",
    )
    export_cmd.add_argument(
        "--csv-format",
        choices=["xyz", "xy"],
        default=CLI_DEFAULTS["csv_format"],
        help="CSV format (default: xyz).",
    )
    export_cmd.add_argument("-o", "--output", help="Output file path. Default: NACA<code>.<format>")
    export_cmd.add_argument(
        "--chord-mm",
        default=CLI_DEFAULTS["chord_mm"],
        type=float,
        help="Chord in millimeters (default: 100).",
    )
    export_cmd.add_argument(
        "--points-side",
        default=CLI_DEFAULTS["points_side"],
        type=int,
        help="Points per side (default: 100).",
    )
    export_cmd.add_argument(
        "--rotation-deg",
        default=CLI_DEFAULTS["rotation_deg"],
        type=float,
        help="Clockwise rotation in degrees.",
    )
    export_cmd.add_argument(
        "--span-mm",
        default=CLI_DEFAULTS["span_mm"],
        type=float,
        help="Span in millimeters (used for .stl, default: 200).",
    )
    export_cmd.add_argument("--mirror-x", action="store_true", help="Mirror across X axis.")
    export_cmd.add_argument("--mirror-y", action="store_true", help="Mirror across Y axis.")
    export_cmd.add_argument(
        "--decimals",
        default=CLI_DEFAULTS["decimals"],
        type=int,
        help="Decimals for .pts output (default: 6).",
    )

    analyze_cmd = subparsers.add_parser("analyze", help="Quick aerodynamic estimate for a NACA 4-digit profile.")
    analyze_cmd.add_argument("code", help="NACA 4-digit code, e.g. 0012.")
    analyze_cmd.add_argument(
        "--velocity-kmh",
        default=CLI_DEFAULTS["velocity_kmh"],
        type=float,
        help="Flow speed in km/h (default: 50).",
    )
    analyze_cmd.add_argument(
        "--span-mm",
        default=CLI_DEFAULTS["span_mm"],
        type=float,
        help="Span in millimeters (default: 200).",
    )
    analyze_cmd.add_argument(
        "--chord-mm",
        default=CLI_DEFAULTS["chord_mm"],
        type=float,
        help="Chord in millimeters (default: 100).",
    )
    analyze_cmd.add_argument(
        "--alpha-deg",
        default=CLI_DEFAULTS["alpha_deg"],
        type=float,
        help="Angle of attack in degrees (default: 0).",
    )
    analyze_cmd.add_argument("--mirror-x", action="store_true", help="Invert the airfoil vertically for aero sign/convention.")
    analyze_cmd.add_argument(
        "--fluid",
        default=CLI_DEFAULTS["fluid"],
        choices=["air", "water", "salt water", "custom"],
        help="Fluid preset (default: water).",
    )
    analyze_cmd.add_argument("--density", type=float, help="Density [kg/m^3] for --fluid custom.")
    analyze_cmd.add_argument("--viscosity", type=float, help="Dynamic viscosity [Pa*s] for --fluid custom.")

    return parser


def run_cli(argv):
    if not argv:
        return None

    parser = build_cli_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return None

    try:
        parse_naca4_code(args.code)
        if args.command == "export":
            ensure_numpy()
            chord = _positive_float(str(args.chord_mm), "Chord") / 1000.0
            span = _positive_float(str(args.span_mm), "Span") / 1000.0
            n_side = _positive_int(str(args.points_side), "Points per side", minimum=2)
            decimals = _positive_int(str(args.decimals), "Decimals", minimum=0)
            if decimals > 12:
                raise ValueError("Decimals must be between 0 and 12.")

            values = {
                "mode": "flat",
                "code": args.code.strip(),
                "chord": chord,
                "n_side": n_side,
                "angle_deg": float(args.rotation_deg),
                "mirror_x": bool(args.mirror_x),
                "mirror_y": bool(args.mirror_y),
            }
            x, y = generate_airfoil_xy(values)
            fmt = args.format
            output = args.output or f"NACA{args.code}.{fmt}"
            if fmt == "pts":
                pts_fmt = args.pts_format.strip().lower()
                if pts_fmt == "xy":
                    pts_text, _, _, _ = write_pts_xy_text(x, y, decimals=decimals)
                else:
                    pts_text, _, _, _ = write_pts_text(x, y, decimals=decimals)
                with open(output, "w", encoding="utf-8", newline="\n") as f:
                    f.write(pts_text)
            elif fmt == "dxf":
                write_dxf_cli(output, x, y, mode=args.dxf_mode.strip().lower())
            elif fmt == "csv":
                csv_fmt = args.csv_format.strip().lower()
                if csv_fmt == "xy":
                    csv_text, _, _, _ = write_csv_xy_text(x, y, decimals=decimals)
                else:
                    csv_text, _, _, _ = write_csv_xyz_text(x, y, decimals=decimals)
                with open(output, "w", encoding="utf-8", newline="\n") as f:
                    f.write(csv_text)
            else:
                write_stl_ascii(output, x, y, span=span, solid_name=f"NACA{args.code}")

            print(f"Saved {fmt.upper()} file: {output}")
            return 0

        if args.command == "analyze":
            chord = _positive_float(str(args.chord_mm), "Chord") / 1000.0
            span = _positive_float(str(args.span_mm), "Span") / 1000.0
            velocity = _positive_float(str(args.velocity_kmh), "Velocity") / 3.6
            alpha_deg = float(args.alpha_deg)

            if args.fluid == "custom":
                if args.density is None or args.viscosity is None:
                    raise ValueError("Custom fluid requires both --density and --viscosity.")
                density = _positive_float(str(args.density), "Density")
                viscosity = _positive_float(str(args.viscosity), "Viscosity")
            else:
                density = FLUID_PRESETS[args.fluid]["rho"]
                viscosity = FLUID_PRESETS[args.fluid]["mu"]

            reynolds = compute_reynolds(velocity=velocity, chord=chord, density=density, viscosity=viscosity)
            params = get_airfoil_parameters(code=args.code.strip(), reynolds=reynolds, use_internal_library=True, overrides={})
            alpha_for_aero = -alpha_deg if args.mirror_x else alpha_deg
            cl, cd = compute_cl_cd(alpha_deg=alpha_for_aero, params=params)
            if args.mirror_x:
                cl = -cl
            area = chord * span
            lift, drag, ld_ratio = compute_lift_drag(density=density, velocity=velocity, area=area, cl=cl, cd=cd)

            mirror_note = " | mirror_x" if args.mirror_x else ""
            print(f"NACA {args.code.strip()} | alpha={alpha_deg:g} deg{mirror_note} | fluid={args.fluid}")
            print(f"Reynolds: {reynolds:.3e}")
            print(f"Cl: {cl:.4f}")
            print(f"Cd: {cd:.4f}")
            print(f"Lift: {lift:.3f} N ({lift / 9.80665:.3f} kgf)")
            print(f"Drag: {drag:.3f} N ({drag / 9.80665:.3f} kgf)")
            print(f"L/D: {ld_ratio:.3f}")
            print(f"Model source: {params.get('source', 'fallback')}")
            return 0

    except Exception as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    main()

