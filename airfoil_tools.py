# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-Duilio-Commercial
#
# This file is part of Airfoil Tools.
# See LICENSE and COMMERCIAL-LICENSE.md for details.

import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


FLUID_PRESETS = {
    "air": {"rho": 1.225, "mu": 1.81e-5},
    "water": {"rho": 997.0, "mu": 8.9e-4},
}


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


def parse_naca4_code(code: str):
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA code must have 4 digits, for example 2412 or 0012.")
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:4]) / 100.0
    return {"code": code, "m": m, "p": p, "t": t, "is_symmetric": (code[:2] == "00")}


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

    if use_internal_library and code in AIRFOIL_DB:
        for bucket in AIRFOIL_DB[code]["re_buckets"]:
            if bucket["re_min"] <= reynolds < bucket["re_max"]:
                base = dict(bucket)
                base["source"] = "library"
                break
        if base is None:
            base = dict(AIRFOIL_DB[code]["re_buckets"][-1])
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


def compute_reynolds(velocity: float, chord: float, density: float, viscosity: float):
    if viscosity <= 0:
        raise ValueError("Dynamic viscosity must be greater than zero.")
    if chord <= 0:
        raise ValueError("Chord must be greater than zero.")
    return density * velocity * chord / viscosity


def compute_cl_cd(alpha_deg: float, params):
    cl_alpha = float(params["cl_alpha_per_deg"])
    alpha_zero = float(params["alpha_zero_lift_deg"])
    cl_max = max(float(params["cl_max"]), 0.05)
    cd0 = max(float(params["cd0_base"]), 0.0001)
    k_drag = max(float(params["k_drag"]), 0.0001)
    alpha_stall = max(float(params["alpha_stall_deg"]), 1.0)

    alpha_eff = alpha_deg - alpha_zero
    cl_linear = cl_alpha * alpha_eff
    sign = 1.0 if cl_linear >= 0 else -1.0

    if abs(alpha_eff) <= alpha_stall:
        cl = max(-cl_max, min(cl_max, cl_linear))
        stall_drag = 0.0
    else:
        cl_stall = cl_alpha * alpha_stall
        excess = abs(alpha_eff) - alpha_stall
        degraded = abs(cl_stall) * math.exp(-0.12 * excess)
        min_post_stall = 0.18 * cl_max
        cl = sign * max(min_post_stall, min(cl_max, degraded))
        stall_drag = 0.015 * excess ** 1.25

    cd = cd0 + k_drag * cl**2 + stall_drag
    return cl, cd


def compute_lift_drag(density: float, velocity: float, area: float, cl: float, cd: float):
    if area <= 0:
        raise ValueError("Wing area must be greater than zero.")
    q = 0.5 * density * velocity**2
    lift = q * area * cl
    drag = q * area * cd
    ld_ratio = lift / drag if abs(drag) > 1e-12 else float("inf")
    return lift, drag, ld_ratio


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

    # local arc normal (rotated +90°)
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
    """Global final mirrors and rotation."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    if mirror_x:
        y = -y

    if mirror_y:
        x = -x

    if angle_deg:
        ang = math.radians(angle_deg)
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


def write_dxf_polyline(path: str, x, y, layer: str = "AIRFOIL"):
    """Esporta contorno chiuso come LWPOLYLINE 2D nel piano XY."""
    try:
        import ezdxf
    except ImportError as exc:
        raise RuntimeError(
            "Library 'ezdxf' is not installed. Install with: pip install ezdxf"
        ) from exc

    x, y = close_profile(x, y)

    doc = ezdxf.new("R2010")
    if layer not in doc.layers:
        doc.layers.add(name=layer)

    msp = doc.modelspace()
    points_2d = [(float(xv), float(yv)) for xv, yv in zip(x, y)]
    msp.add_lwpolyline(points_2d, format="xy", dxfattribs={"layer": layer, "closed": True})

    doc.saveas(path)


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
        self.root.geometry("1180x730")
        self.logo_image = None
        self.set_window_icon()
        self.setup_dark_theme()

        self._update_job = None

        self.build_compact_layout()

        self.last_pts_text = ""
        self.last_x = None
        self.last_y = None

        self.update_mode_fields()
        self.update_fluid_fields()
        self.update_preview()

    def set_window_icon(self):
        icon_path = os.path.join("images", "ico.ico")
        if not os.path.exists(icon_path):
            return
        try:
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def setup_dark_theme(self):
        self.colors = {
            "bg": "#202124",
            "panel": "#292a2d",
            "panel_alt": "#3c4043",
            "fg": "#e8eaed",
            "muted": "#9aa0a6",
            "accent": "#8ab4f8",
            "accent_alt": "#669df6",
            "entry": "#303134",
            "text": "#e8eaed",
            "plot_bg": "#202124",
            "grid": "#5f6368",
        }
        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        themes = style.theme_names()
        if "clam" in themes:
            style.theme_use("clam")

        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TSeparator", background=self.colors["panel_alt"])
        style.configure("TLabelframe", background=self.colors["panel"], borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["fg"])
        style.configure("TEntry", fieldbackground=self.colors["entry"], foreground=self.colors["text"], insertcolor=self.colors["text"])
        style.configure("TCombobox", fieldbackground=self.colors["entry"], background=self.colors["entry"], foreground=self.colors["text"])
        style.map("TCombobox", fieldbackground=[("readonly", self.colors["entry"])], foreground=[("readonly", self.colors["text"])])
        style.configure("TCheckbutton", background=self.colors["panel"], foreground=self.colors["fg"])
        style.map("TCheckbutton", background=[("active", self.colors["panel_alt"])], foreground=[("disabled", self.colors["muted"])])
        style.configure("TButton", background=self.colors["panel_alt"], foreground=self.colors["fg"], borderwidth=1, focuscolor=self.colors["accent"], padding=(10, 6))
        style.map("TButton", background=[("active", self.colors["accent"]), ("pressed", self.colors["accent_alt"])], foreground=[("active", "#ffffff")])
        style.configure("KPIValue.TLabel", background=self.colors["panel"], foreground=self.colors["accent"], font=("Segoe UI", 20, "bold"))
        style.configure("KPIValueAlt.TLabel", background=self.colors["panel"], foreground=self.colors["accent_alt"], font=("Segoe UI", 20, "bold"))
        style.configure("Footer.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 9))

    def build_logo_header(self, parent):
        logo_path = os.path.join("images", "logo_airfoil_tools.png")
        if not os.path.exists(logo_path):
            return
        try:
            logo_image = tk.PhotoImage(file=logo_path)
        except Exception:
            self.logo_image = None
            return

        target_width = 36
        if logo_image.width() > target_width:
            downsample = max(1, math.ceil(logo_image.width() / target_width))
            logo_image = logo_image.subsample(downsample, downsample)

        self.logo_image = logo_image
        logo_box = ttk.Frame(parent)
        logo_box.pack(fill="x", pady=(0, 6))
        ttk.Label(logo_box, image=self.logo_image).pack(anchor="w")

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

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        # Logo moved inside Aerodynamics panel (bottom-right under overrides)

        self.code_var = tk.StringVar(value="2412")
        self.chord_var = tk.StringVar(value="100")
        self.n_side_var = tk.StringVar(value="100")
        self.mode_var = tk.StringVar(value="Flat profile")
        self.radius_var = tk.StringVar(value="100")
        self.curvature_dir_var = tk.StringVar(value="convex")
        self.keep_developed_var = tk.BooleanVar(value=True)
        self.angle_var = tk.StringVar(value="0")
        self.decimals_var = tk.StringVar(value="6")
        self.mirror_x_var = tk.BooleanVar(value=False)
        self.mirror_y_var = tk.BooleanVar(value=False)
        self.use_internal_aero_var = tk.BooleanVar(value=True)
        self.fluid_var = tk.StringVar(value="water")
        self.velocity_var = tk.StringVar(value="50")
        self.aero_chord_var = tk.StringVar(value="100")
        self.span_var = tk.StringVar(value="200")
        self.alpha_attack_var = tk.StringVar(value="0.0")
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

        geom = ttk.LabelFrame(left, text="Geometry", padding=8)
        geom.pack(fill="x")
        geom.columnconfigure(1, weight=1)
        geom.columnconfigure(3, weight=1)

        row = 0
        ttk.Label(geom, text="NACA").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(geom, textvariable=self.code_var, width=10)
        e.grid(row=row, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(geom, text="Mode").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=2)
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
        ttk.Label(geom, text="Chord [mm]").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(geom, textvariable=self.chord_var, width=10)
        e.grid(row=row, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(geom, text="Points/side").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(geom, textvariable=self.n_side_var, width=10)
        e.grid(row=row, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        trans = ttk.LabelFrame(left, text="Curvature / Transform", padding=8)
        trans.pack(fill="x", pady=(6, 0))
        trans.columnconfigure(1, weight=1)
        trans.columnconfigure(3, weight=1)

        row = 0
        ttk.Label(trans, text="Radius [mm]").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        self.radius_entry = ttk.Entry(trans, textvariable=self.radius_var, width=10)
        self.radius_entry.grid(row=row, column=1, sticky="ew", pady=2)
        self.radius_entry.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(trans, text="Curvature").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=2)
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
        ttk.Label(trans, text="Rotation [°]").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(trans, textvariable=self.angle_var, width=10)
        e.grid(row=row, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Label(trans, text="Decimals").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(trans, textvariable=self.decimals_var, width=10)
        e.grid(row=row, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Checkbutton(
            trans,
            text="Mirror X axis",
            variable=self.mirror_x_var,
            command=self.update_preview,
        ).grid(row=row, column=2, sticky="w", padx=(8, 4), pady=2)
        ttk.Checkbutton(
            trans,
            text="Mirror Y axis",
            variable=self.mirror_y_var,
            command=self.update_preview,
        ).grid(row=row, column=3, sticky="w", pady=2)

        aero = ttk.LabelFrame(left, text="Aerodynamics", padding=8)
        aero.pack(fill="x", pady=(6, 0))
        aero.columnconfigure(1, weight=1)
        aero.columnconfigure(3, weight=1)

        arow = 0
        ttk.Checkbutton(
            aero,
            text="Use internal NACA library",
            variable=self.use_internal_aero_var,
            command=self.update_preview,
        ).grid(row=arow, column=0, columnspan=4, sticky="w", pady=2)

        arow += 1
        ttk.Label(aero, text="Fluid").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        self.fluid_combo = ttk.Combobox(
            aero,
            textvariable=self.fluid_var,
            values=["air", "water", "custom"],
            state="readonly",
            width=10,
        )
        self.fluid_combo.grid(row=arow, column=1, sticky="ew", pady=2)
        self.fluid_combo.bind("<<ComboboxSelected>>", self.on_fluid_changed)
        ttk.Label(aero, text="Velocity [km/h]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.velocity_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="Aero chord [mm]").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.aero_chord_var, width=10)
        e.grid(row=arow, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Span [mm]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.span_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="Angle α [°]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.alpha_attack_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="Density [kg/m³]").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        self.density_entry = ttk.Entry(aero, textvariable=self.density_var, width=10)
        self.density_entry.grid(row=arow, column=1, sticky="ew", pady=2)
        self.density_entry.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Viscosity [Pa·s]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
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
        ttk.Label(aero, text="Override α0°").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.override_alpha0_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        logo_path = os.path.join("images", "logo_airfoil_tools.png")
        if os.path.exists(logo_path):
            try:
                logo_image = tk.PhotoImage(file=logo_path)
                target_width = 72
                if logo_image.width() > target_width:
                    downsample = max(1, math.ceil(logo_image.width() / target_width))
                    logo_image = logo_image.subsample(downsample, downsample)
                self.logo_image = logo_image
                ttk.Label(aero, image=self.logo_image).grid(
                    row=arow,
                    column=3,
                    sticky="e",
                    pady=(2, 4),
                )
            except Exception:
                self.logo_image = None

        arow += 1
        ttk.Separator(aero, orient="horizontal").grid(row=arow, column=0, columnspan=4, sticky="ew", pady=3)

        arow += 1
        metrics_start_row = arow
        ttk.Label(aero, text="Reynolds [-]").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.reynolds_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="CL").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.cl_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="CD").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.cd_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="Lift [kg]").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.lift_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="Drag [kg]").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.drag_out_var).grid(row=arow, column=1, sticky="w", pady=1)
        arow += 1
        ttk.Label(aero, text="L/D").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.ld_out_var).grid(row=arow, column=1, sticky="w", pady=1)

        logo_path = ""
        for candidate in (
            os.path.join("images", "logo_airfoil_tools_clean.png"),
            os.path.join("images", "logo_airfoil_tools.png"),
        ):
            if os.path.exists(candidate):
                logo_path = candidate
                break
        if logo_path:
            try:
                logo_image = tk.PhotoImage(file=logo_path)
                target_width = 132
                if logo_image.width() > target_width:
                    downsample = max(1, math.ceil(logo_image.width() / target_width))
                    logo_image = logo_image.subsample(downsample, downsample)
                self.logo_image = logo_image
                ttk.Label(aero, image=self.logo_image).grid(
                    row=metrics_start_row,
                    column=3,
                    rowspan=6,
                    sticky="se",
                    pady=(0, 2),
                )
            except Exception:
                self.logo_image = None

        actions = ttk.LabelFrame(left, text="Actions", padding=8)
        actions.pack(fill="x", pady=(6, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Update", command=self.update_preview).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        ttk.Button(actions, text="Save .pts", command=self.save_pts).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Button(actions, text="Save .dxf", command=self.save_dxf).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)
        ttk.Button(actions, text="Copy preview", command=self.copy_preview).grid(row=1, column=1, sticky="ew", pady=2)

        note = ttk.LabelFrame(left, text="Quick workflow", padding=8)
        note.pack(fill="x", pady=(6, 0))
        ttk.Label(
            note,
            text=(
                "1) Enter NACA code and main parameters.\n"
                "2) Check live plot and aero values.\n"
                "3) Save .pts or .dxf from Actions.\n"
                "4) Use 'Copy preview' for quick export."
            ),
            justify="left",
        ).pack(anchor="w")

        graph_frame = ttk.LabelFrame(right, text="Airfoil plot (live)", padding=8)
        graph_frame.pack(fill="both", expand=True)

        self.figure = Figure(figsize=(7, 4.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.configure_plot_theme()

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        kpi_frame = ttk.LabelFrame(right, text="Flight KPIs", padding=10)
        kpi_frame.pack(fill="x", expand=False, pady=(8, 0))
        kpi_frame.columnconfigure(1, weight=1)
        kpi_frame.columnconfigure(3, weight=1)
        ttk.Label(kpi_frame, text="Lift [kg]").grid(row=0, column=0, sticky="w")
        ttk.Label(kpi_frame, textvariable=self.lift_out_var, style="KPIValue.TLabel").grid(row=0, column=1, sticky="w", padx=(4, 12))
        ttk.Label(kpi_frame, text="Drag [kg]").grid(row=0, column=2, sticky="w")
        ttk.Label(kpi_frame, textvariable=self.drag_out_var, style="KPIValueAlt.TLabel").grid(row=0, column=3, sticky="w", padx=(4, 0))

        preview_frame = ttk.LabelFrame(right, text=".pts preview", padding=8)
        preview_frame.pack(fill="x", expand=False, pady=(8, 0))

        summary = ttk.Frame(preview_frame)
        summary.pack(fill="x", pady=(0, 4))
        summary_labels = [("Re [-]", self.reynolds_out_var), ("CL [-]", self.cl_out_var), ("CD [-]", self.cd_out_var)]
        for idx, (lbl, var) in enumerate(summary_labels):
            col = idx * 2
            summary.columnconfigure(col + 1, weight=1)
            ttk.Label(summary, text=f"{lbl}:").grid(row=0, column=col, sticky="w", padx=(0, 2))
            ttk.Label(summary, textvariable=var).grid(row=0, column=col + 1, sticky="w", padx=(0, 8))

        text_row = ttk.Frame(preview_frame)
        text_row.pack(fill="x", expand=False)

        self.text = tk.Text(
            text_row,
            wrap="none",
            font=("Consolas", 10),
            height=6,
            bg=self.colors["entry"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            selectbackground=self.colors["accent"],
            relief="flat",
            borderwidth=1,
        )
        self.text.pack(side="left", fill="x", expand=True)

        yscroll = ttk.Scrollbar(text_row, orient="vertical", command=self.text.yview)
        yscroll.pack(side="right", fill="y")
        xscroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.text.xview)
        xscroll.pack(fill="x", pady=(2, 0))
        self.text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        footer = ttk.Label(right, text="© Fabio Giuliodori", style="Footer.TLabel")
        footer.pack(anchor="e", pady=(8, 0))

    def configure_plot_theme(self):
        self.figure.patch.set_facecolor(self.colors["plot_bg"])
        self.ax.set_facecolor(self.colors["plot_bg"])
        self.ax.tick_params(colors=self.colors["fg"])
        for spine in self.ax.spines.values():
            spine.set_color(self.colors["muted"])
        self.ax.title.set_color(self.colors["fg"])
        self.ax.xaxis.label.set_color(self.colors["fg"])
        self.ax.yaxis.label.set_color(self.colors["fg"])

    def mode_internal_value(self):
        return self.mode_map.get(self.mode_combo.get().strip(), "flat")

    def on_mode_changed(self, event=None):
        self.update_mode_fields()
        self.update_preview()

    def update_mode_fields(self):
        is_curved = self.mode_internal_value() == "curved"
        state = "normal" if is_curved else "disabled"
        readonly_state = "readonly" if is_curved else "disabled"

        self.radius_entry.config(state=state)
        self.curv_dir_combo.config(state=readonly_state)
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

    def schedule_update(self, event=None):
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
        self._update_job = self.root.after(200, self.update_preview)

    @staticmethod
    def _parse_optional_float(txt):
        raw = txt.strip()
        if not raw:
            return None
        return float(raw.replace(",", "."))

    def compute_aero_results(self, vals):
        code = vals["code"]
        alpha = float(self.alpha_attack_var.get().replace(",", "."))
        velocity_kmh = float(self.velocity_var.get().replace(",", "."))
        chord_mm = float(self.aero_chord_var.get().replace(",", "."))
        span_mm = float(self.span_var.get().replace(",", "."))
        velocity = velocity_kmh / 3.6
        chord = chord_mm / 1000.0
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
            use_internal_library=self.use_internal_aero_var.get(),
            overrides=overrides,
        )
        cl, cd = compute_cl_cd(alpha_deg=alpha, params=params)
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
        self.reynolds_out_var.set(f"{aero['reynolds']:.3e}")
        self.cl_out_var.set(f"{aero['cl']:.4f}")
        self.cd_out_var.set(f"{aero['cd']:.4f}")
        lift_kg = aero["lift"] / 9.80665
        drag_kg = aero["drag"] / 9.80665
        self.lift_out_var.set(f"{lift_kg:.3f}")
        self.drag_out_var.set(f"{drag_kg:.3f}")
        self.ld_out_var.set(f"{aero['ld_ratio']:.3f}")

    def get_values(self):
        mode = self.mode_internal_value()
        code = self.code_var.get().strip()
        chord_mm = float(self.chord_var.get().replace(",", "."))
        chord = chord_mm / 1000.0
        n_side = int(self.n_side_var.get())
        angle_deg = float(self.angle_var.get().replace(",", "."))
        decimals = int(self.decimals_var.get())

        if chord <= 0:
            raise ValueError("Chord must be greater than zero.")
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
            pts_text, x, y, _ = write_pts_text(x, y, decimals=vals["decimals"])
            aero = self.compute_aero_results(vals)

            self.last_pts_text = pts_text
            self.last_x = x
            self.last_y = y

            self.text.delete("1.0", "end")
            self.text.insert("1.0", pts_text)
            self.update_aero_display(aero)

            self.redraw_plot(x, y, vals)
        except Exception as e:
            self.reynolds_out_var.set("-")
            self.cl_out_var.set("-")
            self.cd_out_var.set("-")
            self.lift_out_var.set("-")
            self.drag_out_var.set("-")
            self.ld_out_var.set("-")
            self.show_plot_error(str(e))

    def redraw_plot(self, x, y, vals):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["plot_bg"])
        x_mm = np.array(x) * 1000.0
        y_mm = np.array(y) * 1000.0
        line_color = self.colors["accent"]
        self.ax.plot(x_mm, y_mm, marker=".", markersize=2, linewidth=1.3, color=line_color)

        mode_txt = "Flat profile" if vals["mode"] == "flat" else "Curved profile"
        title = f"NACA {vals['code']} | chord={vals['chord'] * 1000:.1f} mm | {mode_txt}"
        if vals["mode"] == "curved":
            title += f" | R={vals['radius'] * 1000:.1f} mm"
        if vals["angle_deg"]:
            title += f" | rot={vals['angle_deg']}°"

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

        if len(x_mm) > 0:
            xmin, xmax = float(np.min(x_mm)), float(np.max(x_mm))
            ymin, ymax = float(np.min(y_mm)), float(np.max(y_mm))
            dx = xmax - xmin
            dy = ymax - ymin
            base = max(vals["chord"] * 1000.0 * 0.02, 1e-6)
            pad_x = max(dx * 0.08, base)
            pad_y = max(dy * 0.12, base)
            self.ax.set_xlim(xmin - pad_x, xmax + pad_x)
            self.ax.set_ylim(ymin - pad_y, ymax + pad_y)

        self.canvas.draw_idle()

    def show_plot_error(self, msg):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["plot_bg"])
        self.ax.text(0.5, 0.5, msg, ha="center", va="center", wrap=True, color=self.colors["fg"])
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def save_pts(self):
        try:
            vals = self.get_values()
            x, y = generate_airfoil_xy(vals)
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

            write_dxf_polyline(path, x, y)
            messagebox.showinfo("Saved", f"DXF saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_preview(self):
        txt = self.text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        self.root.update()
        messagebox.showinfo("Copied", "Preview copied to clipboard.")


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
