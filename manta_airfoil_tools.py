"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Main application module for Manta AirLab.
Provides the desktop GUI, CLI entry points, geometry generation workflow,
preview rendering, export operations, and quick aerodynamic estimates for
4-digit NACA airfoils.
"""

# SPDX-License-Identifier: GPL-3.0-only
#
# This file is part of Manta AirLab.
# See LICENSE for details.

import importlib
import argparse
import math
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import time

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

from aero import compute_cl_cd, compute_flow_arrow_length, compute_lift_drag, compute_reynolds
from airfoil_db_sqlite import AirfoilDb
from airfoil_library import get_airfoil_parameters
from defaults import CLI_DEFAULTS, FLUID_PRESETS, GUI_DEFAULTS
from exporters import write_csv_xy_text, write_csv_xyz_text, write_dxf, write_dxf_cli, write_pts_text, write_pts_xy_text, write_stl_ascii
from geometry import (
    build_base_airfoil_xy,
    build_extruded_mesh,
    compute_display_limits_3d,
    curve_profile_xy_generic,
    generate_airfoil_xy,
    parse_naca4_code,
    strip_duplicate_closing_point,
    transform_points,
)
from setup import ensure_local_directories, ensure_python_packages, ensure_runtime_assets

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
            "drag": "#ff7666",
            "source_db": "#8fb9ff",
            "source_live": "#5fd88f",
            "source_fallback": "#f5b967",
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
            "drag": "#d84b2c",
            "source_db": "#1a5fb4",
            "source_live": "#0c8c57",
            "source_fallback": "#b07207",
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

    if not ensure_python_packages(required, context="The app cannot start without these packages."):
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






class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Manta AirLab")
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
        self._airfoil_db = AirfoilDb()
        self._library_profiles = []
        self._library_geometry_cache = {}
        self._library_polar_sets_cache = {}
        self._library_reynolds_cache = {}
        self._library_usable_reynolds_cache = {}
        self._library_polar_rows_cache = {}
        self._library_display_to_name = {}
        self._xfoil_live_result = None
        self._re_extrapolation_limit = float(GUI_DEFAULTS.get("nd_re_extrapolation_limit", "3.0"))
        self._alpha_extrapolation_steps_limit = float(GUI_DEFAULTS.get("nd_alpha_steps_limit", "2.0"))
        self._library_load_error = ""

        self.build_compact_layout()

        self.last_pts_text = ""
        self.last_x = None
        self.last_y = None
        self.plot_mode = "2d"
        self._pan_state = None
        self._default_3d_view = {"elev": 10, "azim": -102}

        self.update_mode_fields()
        self.update_fluid_fields()
        self.update_nd_limits_from_vars()
        self.refresh_library_profiles()
        self.update_source_fields()
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
            "AeroSourceLabel.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 8),
        )
        self.style.configure(
            "AeroSourceDb.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["source_db"],
            font=("Segoe UI Semibold", 8),
        )
        self.style.configure(
            "AeroSourceLive.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["source_live"],
            font=("Segoe UI Semibold", 8),
        )
        self.style.configure(
            "AeroSourceFallback.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["source_fallback"],
            font=("Segoe UI Semibold", 8),
        )
        self.style.configure(
            "XfoilStatusInfo.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 8),
        )
        self.style.configure(
            "XfoilStatusOk.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["source_live"],
            font=("Segoe UI Semibold", 8),
        )
        self.style.configure(
            "XfoilStatusError.TLabel",
            background=self.colors["panel"],
            foreground=self.colors["source_fallback"],
            font=("Segoe UI Semibold", 8),
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

        guards = ttk.LabelFrame(outer, text="Interpolation guards", padding=10)
        guards.pack(fill="x", pady=(8, 0))
        guards.columnconfigure(1, weight=1)
        ttk.Label(guards, text="ND Re ratio limit").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        re_guard_entry = ttk.Entry(guards, textvariable=self.nd_re_limit_var, width=10)
        re_guard_entry.grid(row=0, column=1, sticky="ew", pady=2)
        re_guard_entry.bind("<KeyRelease>", self.on_nd_limits_changed)
        re_guard_entry.bind("<FocusOut>", self.on_nd_limits_changed)
        ttk.Label(guards, text="ND alpha step limit").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        alpha_guard_entry = ttk.Entry(guards, textvariable=self.nd_alpha_steps_var, width=10)
        alpha_guard_entry.grid(row=1, column=1, sticky="ew", pady=2)
        alpha_guard_entry.bind("<KeyRelease>", self.on_nd_limits_changed)
        alpha_guard_entry.bind("<FocusOut>", self.on_nd_limits_changed)
        ttk.Label(
            guards,
            text="Higher values reduce ND and allow broader clamping outside validated points.",
            style="Muted.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.update_mode_fields()

    def open_library_browser(self):
        if self.library_browser_window is not None:
            try:
                if self.library_browser_window.winfo_exists():
                    self.library_browser_window.lift()
                    self.library_browser_window.focus_force()
                    self.refresh_library_browser_results()
                    return
            except Exception:
                self.library_browser_window = None

        win = tk.Toplevel(self.root)
        win.title("Library Browser")
        win.configure(bg=self.colors["bg"])
        win.geometry("980x620")
        self.library_browser_window = win

        def _close():
            try:
                win.destroy()
            finally:
                self.library_browser_window = None
                self.library_results_listbox = None

        win.protocol("WM_DELETE_WINDOW", _close)

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        filters = ttk.LabelFrame(outer, text="Filters & Ranking", padding=8)
        filters.pack(fill="x")
        for col in (1, 3):
            filters.columnconfigure(col, weight=1)

        ttk.Label(filters, text="Search").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        search_entry = ttk.Entry(filters, textvariable=self.library_search_var, width=18)
        search_entry.grid(row=0, column=1, sticky="ew", pady=2)
        search_entry.bind("<KeyRelease>", self.on_library_filter_changed)

        ttk.Label(filters, text="Usage").grid(row=0, column=2, sticky="w", padx=(10, 6), pady=2)
        usage_entry = ttk.Entry(filters, textvariable=self.library_usage_filter_var, width=18)
        usage_entry.grid(row=0, column=3, sticky="ew", pady=2)
        usage_entry.bind("<KeyRelease>", self.on_library_filter_changed)

        ttk.Label(filters, text="Sort").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        sort_combo = ttk.Combobox(
            filters,
            textvariable=self.library_sort_var,
            values=["Name", "Performance", "Docility", "Robustness", "Confidence", "Weighted"],
            state="readonly",
            width=16,
        )
        sort_combo.grid(row=1, column=1, sticky="ew", pady=2)
        sort_combo.bind("<<ComboboxSelected>>", self.on_library_filter_changed)

        ttk.Label(filters, text="Top N").grid(row=1, column=2, sticky="w", padx=(10, 6), pady=2)
        topn_entry = ttk.Entry(filters, textvariable=self.library_top_n_var, width=10)
        topn_entry.grid(row=1, column=3, sticky="ew", pady=2)
        topn_entry.bind("<KeyRelease>", self.on_library_filter_changed)

        ttk.Label(filters, text="Weights: Perf / Doc / Rob / Conf", style="Muted.TLabel").grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(4, 2)
        )
        scales_row = ttk.Frame(filters)
        scales_row.grid(row=3, column=0, columnspan=4, sticky="ew")
        for idx in range(4):
            scales_row.columnconfigure(idx, weight=1)
        for idx, var in enumerate((self.rank_perf_var, self.rank_doc_var, self.rank_rob_var, self.rank_conf_var)):
            scale = tk.Scale(
                scales_row,
                from_=0,
                to=100,
                orient="horizontal",
                variable=var,
                showvalue=False,
                resolution=1,
                bg=self.colors["panel"],
                fg=self.colors["fg"],
                highlightthickness=0,
                troughcolor=self.colors["entry"],
                activebackground=self.colors["accent"],
                command=self.on_library_weight_changed,
            )
            scale.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0))

        results = ttk.LabelFrame(outer, text="Profiles", padding=8)
        results.pack(fill="both", expand=True, pady=(8, 0))
        self.library_results_listbox = tk.Listbox(
            results,
            activestyle="none",
            bg=self.colors["entry"],
            fg=self.colors["text"],
            selectbackground=self.colors["selection"],
            selectforeground=self.colors["text"],
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["accent"],
        )
        self.library_results_listbox.pack(side="left", fill="both", expand=True)
        self.library_results_listbox.bind("<Double-Button-1>", self.apply_selected_library_profile)

        yscroll = ttk.Scrollbar(results, orient="vertical", command=self.library_results_listbox.yview)
        yscroll.pack(side="right", fill="y")
        self.library_results_listbox.config(yscrollcommand=yscroll.set)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Apply profile", command=self.apply_selected_library_profile).pack(side="left")
        ttk.Button(actions, text="Close", command=_close).pack(side="right")

        self.refresh_library_browser_results()

    def refresh_library_browser_results(self):
        if self.library_browser_window is None or self.library_results_listbox is None:
            return
        try:
            display_values = self._build_library_browser_rows()
        except Exception as exc:
            self._library_load_error = str(exc)
            display_values = []
        lb = self.library_results_listbox
        lb.delete(0, "end")
        for item in display_values:
            lb.insert("end", item)
        current_name = self._get_selected_library_profile_name()
        if current_name:
            for idx, text in enumerate(display_values):
                if self._library_display_to_name.get(text, "") == current_name:
                    lb.selection_set(idx)
                    lb.see(idx)
                    break

    def apply_selected_library_profile(self, _event=None):
        if self.library_results_listbox is None:
            return
        selected_idx = self.library_results_listbox.curselection()
        if not selected_idx:
            return
        label = self.library_results_listbox.get(selected_idx[0])
        name = self._library_display_to_name.get(label, "")
        if not name:
            return
        values = list(self.library_profile_combo.cget("values"))
        if name not in values:
            values.append(name)
            self.library_profile_combo["values"] = values
        self.library_profile_var.set(name)
        self.schedule_update()

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
        ttk.Label(title_row, text="Manta AirLab", style="HeroTitle.TLabel").pack(side="left")
        ttk.Label(title_row, text="by Fabio Giuliodori | duilio.cc", style="HeroSignature.TLabel").pack(side="left", padx=(8, 0), pady=(2, 0))

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
        self.source_kind_var = tk.StringVar(value="NACA")
        self.library_profile_var = tk.StringVar(value="")
        self.library_search_var = tk.StringVar(value="")
        self.library_usage_filter_var = tk.StringVar(value="")
        self.library_sort_var = tk.StringVar(value="Name")
        self.library_top_n_var = tk.StringVar(value="60")
        self.rank_perf_var = tk.DoubleVar(value=1.0)
        self.rank_doc_var = tk.DoubleVar(value=1.0)
        self.rank_rob_var = tk.DoubleVar(value=1.0)
        self.rank_conf_var = tk.DoubleVar(value=1.0)
        self.nd_re_limit_var = tk.StringVar(value=GUI_DEFAULTS.get("nd_re_extrapolation_limit", "3.0"))
        self.nd_alpha_steps_var = tk.StringVar(value=GUI_DEFAULTS.get("nd_alpha_steps_limit", "2.0"))
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
        self.library_browser_window = None
        self.library_results_listbox = None
        # Advanced aerodynamic source toggle kept for future UI re-enable.
        # To restore it, add back the checkbox in the Aerodynamics panel and
        # switch `use_internal_library=True` in `compute_aero_results()` to this variable.
        self.use_internal_aero_var = tk.BooleanVar(value=True)
        self.fluid_var = tk.StringVar(value=GUI_DEFAULTS["fluid"])
        self.velocity_var = tk.StringVar(value=GUI_DEFAULTS["velocity_kmh"])
        self.temperature_c_var = tk.StringVar(value=GUI_DEFAULTS.get("temperature_c", "20"))
        self.aero_chord_var = tk.StringVar(value=GUI_DEFAULTS["aero_chord_mm"])
        self.span_var = tk.StringVar(value=GUI_DEFAULTS["span_mm"])
        self.alpha_attack_var = tk.StringVar(value=GUI_DEFAULTS["alpha_deg"])
        self.density_var = tk.StringVar(value=str(FLUID_PRESETS["water"]["rho"]))
        self.viscosity_var = tk.StringVar(value=str(FLUID_PRESETS["water"]["mu"]))
        self.aero_re_scale_var = tk.StringVar(value="1.0")
        self.aero_alpha_offset_var = tk.StringVar(value="0.0")
        self.aero_cl_scale_var = tk.StringVar(value="1.0")
        self.aero_cd_scale_var = tk.StringVar(value="1.0")
        self.override_cd0_var = tk.StringVar(value="")
        self.override_k_drag_var = tk.StringVar(value="")
        self.override_cl_max_var = tk.StringVar(value="")
        self.override_alpha0_var = tk.StringVar(value="")
        self.reynolds_out_var = tk.StringVar(value="-")
        self.cl_out_var = tk.StringVar(value="-")
        self.cd_out_var = tk.StringVar(value="-")
        self.cm_out_var = tk.StringVar(value="-")
        self.aero_source_var = tk.StringVar(value="db_interpolated")
        self.xfoil_status_var = tk.StringVar(value="XFOIL idle")
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
        ttk.Label(geom, text="Source", style="Panel.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 4), pady=(1, 1))
        self.source_combo = ttk.Combobox(
            geom,
            textvariable=self.source_kind_var,
            values=["NACA", "Library"],
            state="readonly",
            width=12,
        )
        self.source_combo.grid(row=row, column=1, sticky="ew", pady=(2, 0))
        self.source_combo.bind("<<ComboboxSelected>>", self.on_source_changed)
        ttk.Label(geom, text="Library profile", style="Panel.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 4), pady=(1, 1))
        self.library_profile_combo = ttk.Combobox(
            geom,
            textvariable=self.library_profile_var,
            state="readonly",
            width=18,
        )
        self.library_profile_combo.grid(row=row, column=3, sticky="ew", pady=(2, 0))
        self.library_profile_combo.bind("<<ComboboxSelected>>", self.schedule_update)

        row += 1
        self.library_browse_button = ttk.Button(geom, text="Browse Library...", command=self.open_library_browser)
        self.library_browse_button.grid(row=row, column=2, columnspan=2, sticky="ew", pady=(2, 0))

        row += 1
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
            command=self.on_transform_toggle_changed,
        ).grid(row=row, column=0, sticky="w", padx=(0, 4), pady=2)
        ttk.Checkbutton(
            trans,
            text="Mirror Y axis",
            variable=self.mirror_y_var,
            command=self.on_transform_toggle_changed,
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
        self.temperature_label = ttk.Label(aero, text="Temperature [C] (1-40)", style="Panel.TLabel")
        self.temperature_label.grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        self.temperature_entry = ttk.Entry(aero, textvariable=self.temperature_c_var, width=10)
        self.temperature_entry.grid(row=arow, column=1, sticky="ew", pady=2)
        self.temperature_entry.bind("<KeyRelease>", self.on_temperature_changed)
        self.temperature_entry.bind("<FocusOut>", self.on_temperature_changed)

        # Keep velocity slider prominently visible in compact mode.
        # Advanced readonly field kept so Geometry can still drive a hidden
        # aerodynamic chord input. Re-show this row if you want the user to
        # inspect the linked value directly.
        arow += 1
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
        self.velocity_scale.grid(row=arow, column=2, columnspan=2, sticky="ew", pady=(4, 2))
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
        ttk.Label(aero, text="Re scale (DB)").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.aero_re_scale_var, width=10)
        e.grid(row=arow, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="Alpha offset [deg]").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.aero_alpha_offset_var, width=10)
        e.grid(row=arow, column=3, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)

        arow += 1
        ttk.Label(aero, text="CL scale").grid(row=arow, column=0, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.aero_cl_scale_var, width=10)
        e.grid(row=arow, column=1, sticky="ew", pady=2)
        e.bind("<KeyRelease>", self.schedule_update)
        ttk.Label(aero, text="CD scale").grid(row=arow, column=2, sticky="w", padx=(8, 4), pady=2)
        e = ttk.Entry(aero, textvariable=self.aero_cd_scale_var, width=10)
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
        ttk.Label(aero, text="CM").grid(row=arow, column=0, sticky="w", pady=1)
        ttk.Label(aero, textvariable=self.cm_out_var).grid(row=arow, column=1, sticky="w", pady=1)
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

        graph_actions = ttk.Frame(graph_frame, style="Panel.TFrame")
        graph_actions.pack(fill="x", pady=(4, 0))
        self.xfoil_button = ttk.Button(graph_actions, text="XFOIL Simulation", command=self.run_xfoil_simulation)
        self.xfoil_button.pack(side="left")
        self.aero_source_label = ttk.Label(graph_actions, text="Coeff source", style="AeroSourceLabel.TLabel")
        self.aero_source_label.pack(side="left", padx=(12, 4))
        self.aero_source_value_label = ttk.Label(graph_actions, textvariable=self.aero_source_var, style="AeroSourceDb.TLabel")
        self.aero_source_value_label.pack(side="left")
        self.xfoil_status_label = ttk.Label(graph_actions, textvariable=self.xfoil_status_var, style="XfoilStatusInfo.TLabel")
        self.xfoil_status_label.pack(side="left", padx=(12, 0))
        self.xfoil_progress = ttk.Progressbar(graph_frame, orient="horizontal", mode="determinate")
        self.xfoil_progress.pack(fill="x", pady=(3, 0))
        self.xfoil_progress.configure(maximum=100.0, value=0.0)

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
            text="Manta AirLab — Airfoil Tools by Fabio Giuliodori | duilio.cc",
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
        self.clear_xfoil_override()
        self.update_mode_fields()
        self.update_preview()

    def on_transform_toggle_changed(self):
        self.clear_xfoil_override()
        self.update_preview()

    def source_internal_value(self):
        source = self.source_kind_var.get().strip().lower()
        return "library" if source == "library" else "naca"

    def on_source_changed(self, _event=None):
        self.clear_xfoil_override()
        self.update_source_fields()
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

    def refresh_library_profiles(self):
        self._library_load_error = ""
        try:
            self._library_profiles = self._airfoil_db.list_profiles(limit=3000)
        except Exception as exc:
            self._library_profiles = []
            self._library_load_error = str(exc)

        self._library_profiles.sort(key=lambda item: (item.get("name") or "").lower())
        names = [item.get("name", "") for item in self._library_profiles if item.get("name")]
        current_name = self._get_selected_library_profile_name()
        self.library_profile_combo["values"] = names
        if names:
            self.library_profile_var.set(current_name if current_name in names else names[0])
        else:
            self.library_profile_var.set("")
        self._library_display_to_name = {}

    def _build_library_browser_rows(self):
        rows = self._airfoil_db.list_profiles_with_ratings(
            search=self.library_search_var.get().strip() or None,
            usage_filter=self.library_usage_filter_var.get().strip() or None,
            limit=3000,
        )
        sort_mode = self.library_sort_var.get().strip().lower()
        wp = max(float(self.rank_perf_var.get()), 0.0)
        wd = max(float(self.rank_doc_var.get()), 0.0)
        wr = max(float(self.rank_rob_var.get()), 0.0)
        wc = max(float(self.rank_conf_var.get()), 0.0)
        wsum = max(wp + wd + wr + wc, 1e-9)
        wp, wd, wr, wc = wp / wsum, wd / wsum, wr / wsum, wc / wsum

        weighted_score = {}
        for item in rows:
            name = item.get("name") or ""
            weighted_score[name] = (
                wp * float(item.get("performance_score") or 0.0)
                + wd * float(item.get("docility_score") or 0.0)
                + wr * float(item.get("robustness_score") or 0.0)
                + wc * float(item.get("confidence_score") or 0.0)
            )

        if sort_mode == "performance":
            rows.sort(key=lambda item: float(item.get("performance_score") or -1e9), reverse=True)
        elif sort_mode == "docility":
            rows.sort(key=lambda item: float(item.get("docility_score") or -1e9), reverse=True)
        elif sort_mode == "robustness":
            rows.sort(key=lambda item: float(item.get("robustness_score") or -1e9), reverse=True)
        elif sort_mode == "confidence":
            rows.sort(key=lambda item: float(item.get("confidence_score") or -1e9), reverse=True)
        elif sort_mode == "weighted":
            rows.sort(
                key=lambda item: (
                    weighted_score.get(item.get("name") or "", 0.0),
                    float(item.get("confidence_score") or 0.0),
                    item.get("name") or "",
                ),
                reverse=True,
            )
        else:
            rows.sort(key=lambda item: (item.get("name") or "").lower())

        top_n = int(max(1, min(500, self._parse_float_or_default(self.library_top_n_var.get(), 60))))
        self.library_top_n_var.set(str(top_n))
        rows = rows[:top_n]
        display_values = []
        self._library_display_to_name = {}
        for item in rows:
            name = item.get("name") or ""
            if not name:
                continue
            usage = (item.get("top_usage") or "-").strip()
            if sort_mode == "performance":
                score_val = float(item.get("performance_score") or 0.0)
            elif sort_mode == "docility":
                score_val = float(item.get("docility_score") or 0.0)
            elif sort_mode == "robustness":
                score_val = float(item.get("robustness_score") or 0.0)
            elif sort_mode == "confidence":
                score_val = float(item.get("confidence_score") or 0.0)
            else:
                score_val = weighted_score.get(name, 0.0)
            label = f"{name} | S={score_val:.3f} | use={usage}"
            display_values.append(label)
            self._library_display_to_name[label] = name
        return display_values

    def _get_selected_library_profile_name(self):
        selected = self.library_profile_var.get().strip()
        if not selected:
            return ""
        return self._library_display_to_name.get(selected, selected)

    def on_library_filter_changed(self, _event=None):
        self.refresh_library_browser_results()

    def on_library_weight_changed(self, _value=None):
        if self.library_sort_var.get().strip().lower() == "weighted":
            self.refresh_library_browser_results()

    def on_nd_limits_changed(self, _event=None):
        self.update_nd_limits_from_vars()
        self.schedule_update()

    def update_nd_limits_from_vars(self):
        re_limit = self._parse_float_or_default(self.nd_re_limit_var.get(), self._re_extrapolation_limit)
        alpha_limit = self._parse_float_or_default(self.nd_alpha_steps_var.get(), self._alpha_extrapolation_steps_limit)
        re_limit = max(1.0, re_limit)
        alpha_limit = max(0.0, alpha_limit)
        self._re_extrapolation_limit = re_limit
        self._alpha_extrapolation_steps_limit = alpha_limit
        self.nd_re_limit_var.set(f"{re_limit:g}")
        self.nd_alpha_steps_var.set(f"{alpha_limit:g}")

    def update_source_fields(self):
        is_naca = self.source_internal_value() == "naca"
        naca_state = "normal" if is_naca else "disabled"
        naca_slider_state = "normal" if is_naca else "disabled"
        self.code_entry.config(state=naca_state)
        self.mode_combo.config(state="readonly")
        self.thickness_scale.config(state=naca_slider_state)
        for widget in self.tk_scale_widgets:
            if widget is self.thickness_scale:
                continue
            try:
                if widget.cget("variable") in {
                    str(self.naca_camber_var),
                    str(self.naca_pos_var),
                }:
                    widget.config(state=naca_slider_state)
            except Exception:
                pass
        self.update_mode_fields()
        self.library_profile_combo.config(state="readonly" if not is_naca else "disabled")
        self.library_browse_button.config(state="normal" if not is_naca else "disabled")

    def build_library_airfoil_xy(self, vals):
        profile_name = vals.get("library_profile_name", "").strip()
        if not profile_name:
            raise ValueError("Select a library profile.")
        geom = self._library_geometry_cache.get(profile_name)
        if geom is None:
            geom = self._airfoil_db.get_profile_geometry(profile_name)
            self._library_geometry_cache[profile_name] = geom
        x = np.array(geom["x"], dtype=float) * vals["chord"]
        y = np.array(geom["y"], dtype=float) * vals["chord"]
        if vals["mode"] == "curved":
            x, y = curve_profile_xy_generic(
                x,
                y,
                radius=vals["radius"],
                convex=vals["curvature_dir"] == "convex",
                keep_developed_chord=vals["keep_developed_chord"],
            )
        x, y = transform_points(
            x,
            y,
            angle_deg=vals["angle_deg"],
            mirror_x=vals["mirror_x"],
            mirror_y=vals["mirror_y"],
        )
        return x, y

    @staticmethod
    def _safe_name(text):
        raw = (text or "").strip()
        if not raw:
            return "profile"
        cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        cleaned = cleaned.strip("_")
        return cleaned or "profile"

    def generate_profile_xy(self, vals):
        if vals.get("source_kind") == "library":
            return self.build_library_airfoil_xy(vals)
        return generate_airfoil_xy(vals)

    def default_export_stem(self, vals):
        if vals.get("source_kind") == "library":
            return self._safe_name(vals.get("library_profile_name") or "airfoil")
        return f"NACA{vals['code']}"

    def _get_library_polar_set(self, profile_name):
        cached = self._library_polar_sets_cache.get(profile_name)
        if cached is not None:
            return cached
        polar_sets = self._airfoil_db.list_polar_sets(profile_name)
        if not polar_sets:
            raise ValueError(f"No polar data available for profile '{profile_name}'.")
        chosen = polar_sets[0]
        self._library_polar_sets_cache[profile_name] = chosen
        return chosen

    def _get_library_reynolds_grid(self, profile_name, mach, ncrit):
        key = (profile_name, float(mach), float(ncrit))
        cached = self._library_reynolds_cache.get(key)
        if cached is not None:
            return cached
        re_values = self._airfoil_db.list_reynolds(
            profile_name,
            mach=mach,
            ncrit=ncrit,
            converged_only=True,
        )
        if not re_values:
            re_values = self._airfoil_db.list_reynolds(
                profile_name,
                mach=mach,
                ncrit=ncrit,
                converged_only=False,
            )
        if not re_values:
            raise ValueError(f"No Reynolds samples available for profile '{profile_name}'.")
        self._library_reynolds_cache[key] = re_values
        return re_values

    def _get_library_polar_rows(self, profile_name, reynolds, mach, ncrit):
        key = (profile_name, float(reynolds), float(mach), float(ncrit))
        cached = self._library_polar_rows_cache.get(key)
        if cached is not None:
            return cached
        rows = self._airfoil_db.get_polar_rows(
            profile_name,
            reynolds,
            mach=mach,
            ncrit=ncrit,
            converged_only=True,
        )
        if not rows:
            rows = self._airfoil_db.get_polar_rows(
                profile_name,
                reynolds,
                mach=mach,
                ncrit=ncrit,
                converged_only=False,
            )
        cleaned = []
        for row in rows:
            try:
                alpha = float(row["alpha_deg"])
                cl = float(row["cl"])
                cd = float(row["cd"])
                cm_val = row.get("cm")
                cm = float(cm_val) if cm_val is not None else 0.0
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(alpha) and math.isfinite(cl) and math.isfinite(cd) and math.isfinite(cm)):
                continue
            cleaned.append({"alpha": alpha, "cl": cl, "cd": cd, "cm": cm})
        cleaned.sort(key=lambda item: item["alpha"])
        if len(cleaned) < 2:
            raise ValueError(f"Insufficient polar points at Re={reynolds:.0f} for profile '{profile_name}'.")
        self._library_polar_rows_cache[key] = cleaned
        return cleaned

    def _get_usable_reynolds_grid(self, profile_name, mach, ncrit):
        key = (profile_name, float(mach), float(ncrit))
        cached = self._library_usable_reynolds_cache.get(key)
        if cached is not None:
            return cached
        raw_grid = self._get_library_reynolds_grid(profile_name, mach, ncrit)
        usable = []
        for re_value in raw_grid:
            try:
                self._get_library_polar_rows(profile_name, re_value, mach, ncrit)
                usable.append(re_value)
            except ValueError:
                continue
        if not usable:
            raise ValueError(f"No usable polar rows for profile '{profile_name}'.")
        self._library_usable_reynolds_cache[key] = usable
        return usable

    def _interpolate_alpha_from_rows(self, rows, alpha_deg):
        alpha = float(alpha_deg)
        if len(rows) < 2:
            raise ValueError("ND: insufficient alpha samples.")
        min_alpha = rows[0]["alpha"]
        max_alpha = rows[-1]["alpha"]
        lower_step = max(rows[1]["alpha"] - rows[0]["alpha"], 1e-9)
        upper_step = max(rows[-1]["alpha"] - rows[-2]["alpha"], 1e-9)

        if alpha <= rows[0]["alpha"]:
            alpha_nd = (min_alpha - alpha) > self._alpha_extrapolation_steps_limit * lower_step
            return {
                "cl": rows[0]["cl"],
                "cd": rows[0]["cd"],
                "cm": rows[0]["cm"],
                "alpha_clamped": True,
                "alpha_nd": alpha_nd,
            }
        if alpha >= rows[-1]["alpha"]:
            alpha_nd = (alpha - max_alpha) > self._alpha_extrapolation_steps_limit * upper_step
            return {
                "cl": rows[-1]["cl"],
                "cd": rows[-1]["cd"],
                "cm": rows[-1]["cm"],
                "alpha_clamped": True,
                "alpha_nd": alpha_nd,
            }

        for i in range(len(rows) - 1):
            left = rows[i]
            right = rows[i + 1]
            if left["alpha"] <= alpha <= right["alpha"]:
                span = right["alpha"] - left["alpha"]
                if abs(span) <= 1e-12:
                    t = 0.0
                else:
                    t = (alpha - left["alpha"]) / span
                return {
                    "cl": left["cl"] + t * (right["cl"] - left["cl"]),
                    "cd": left["cd"] + t * (right["cd"] - left["cd"]),
                    "cm": left["cm"] + t * (right["cm"] - left["cm"]),
                    "alpha_clamped": False,
                    "alpha_nd": False,
                }

        return {
            "cl": rows[-1]["cl"],
            "cd": rows[-1]["cd"],
            "cm": rows[-1]["cm"],
            "alpha_clamped": True,
            "alpha_nd": True,
        }

    def interpolate_library_coeffs(self, profile_name, reynolds, alpha_deg):
        polar_set = self._get_library_polar_set(profile_name)
        mach = float(polar_set["mach"])
        ncrit = float(polar_set["ncrit"])
        re_grid = self._get_usable_reynolds_grid(profile_name, mach, ncrit)

        target_re = max(float(reynolds), 1.0)
        re_clamped = False
        re_nd = False
        if target_re <= re_grid[0]:
            re_nd = (re_grid[0] / target_re) > self._re_extrapolation_limit
            re_low = re_grid[0]
            re_high = re_grid[0]
            re_clamped = True
        elif target_re >= re_grid[-1]:
            re_nd = (target_re / re_grid[-1]) > self._re_extrapolation_limit
            re_low = re_grid[-1]
            re_high = re_grid[-1]
            re_clamped = True
        else:
            re_low = re_grid[0]
            re_high = re_grid[-1]
            for idx in range(len(re_grid) - 1):
                if re_grid[idx] <= target_re <= re_grid[idx + 1]:
                    re_low = re_grid[idx]
                    re_high = re_grid[idx + 1]
                    break

        low_rows = self._get_library_polar_rows(profile_name, re_low, mach, ncrit)
        high_rows = self._get_library_polar_rows(profile_name, re_high, mach, ncrit)
        low = self._interpolate_alpha_from_rows(low_rows, alpha_deg)
        high = self._interpolate_alpha_from_rows(high_rows, alpha_deg)

        if abs(re_high - re_low) <= 1e-12:
            blend = 0.0
        else:
            blend = (math.log(target_re) - math.log(re_low)) / (math.log(re_high) - math.log(re_low))
            blend = max(0.0, min(1.0, blend))

        cl = low["cl"] + blend * (high["cl"] - low["cl"])
        cd = low["cd"] + blend * (high["cd"] - low["cd"])
        cm = low["cm"] + blend * (high["cm"] - low["cm"])
        return {
            "cl": cl,
            "cd": cd,
            "cm": cm,
            "mach": mach,
            "ncrit": ncrit,
            "re_low": re_low,
            "re_high": re_high,
            "alpha_clamped": bool(low["alpha_clamped"] or high["alpha_clamped"]),
            "re_clamped": re_clamped,
            "force_nd": bool(re_nd or low.get("alpha_nd") or high.get("alpha_nd")),
        }

    def on_fluid_changed(self, event=None):
        self.clear_xfoil_override()
        fluid = self.fluid_var.get().strip().lower()
        if fluid in FLUID_PRESETS:
            temp_c = self.parse_temperature_c()
            density, viscosity = self.compute_fluid_properties(fluid, temp_c)
            self.density_var.set(f"{density:.6g}")
            self.viscosity_var.set(f"{viscosity:.6g}")
        self.update_fluid_fields()
        self.update_preview()

    def on_temperature_changed(self, _event=None):
        self.clear_xfoil_override()
        temp_c = self.parse_temperature_c()
        self.temperature_c_var.set(f"{temp_c:g}")
        fluid = self.fluid_var.get().strip().lower()
        if fluid in FLUID_PRESETS:
            density, viscosity = self.compute_fluid_properties(fluid, temp_c)
            self.density_var.set(f"{density:.6g}")
            self.viscosity_var.set(f"{viscosity:.6g}")
        self.schedule_update()

    def parse_temperature_c(self):
        raw = self.temperature_c_var.get().replace(",", ".").strip()
        if not raw:
            temp = 20.0
        else:
            try:
                temp = float(raw)
            except ValueError:
                temp = 20.0
        return max(1.0, min(40.0, temp))

    @staticmethod
    def compute_fluid_properties(fluid, temperature_c):
        t_c = max(1.0, min(40.0, float(temperature_c)))
        if fluid == "air":
            t_k = t_c + 273.15
            rho = 101325.0 / (287.05 * t_k)
            mu = 1.458e-6 * (t_k ** 1.5) / (t_k + 110.4)
            return rho, mu
        if fluid == "water":
            rho = 1000.0 * (
                1.0
                - ((t_c + 288.9414) / (508929.2 * (t_c + 68.12963))) * ((t_c - 3.9863) ** 2)
            )
            mu = 2.414e-5 * (10.0 ** (247.8 / (t_c + 133.15)))
            return rho, mu
        if fluid == "salt water":
            rho_w, mu_w = App.compute_fluid_properties("water", t_c)
            rho = rho_w + 27.0 - 0.06 * (t_c - 20.0)
            mu = mu_w * 1.12
            return rho, mu
        preset = FLUID_PRESETS.get(fluid, FLUID_PRESETS["water"])
        return float(preset["rho"]), float(preset["mu"])

    @staticmethod
    def _parse_float_or_default(text, default):
        raw = str(text).replace(",", ".").strip()
        if not raw:
            return float(default)
        try:
            return float(raw)
        except ValueError:
            return float(default)

    @staticmethod
    def _build_aero_signature(vals, reynolds, alpha):
        return (
            vals.get("source_kind", "naca"),
            vals.get("code", ""),
            vals.get("library_profile_name", ""),
            vals.get("mode", ""),
            round(float(vals.get("chord", 0.0)), 8),
            round(float(reynolds), 3),
            round(float(alpha), 4),
        )

    @staticmethod
    def _parse_xfoil_polar_rows(polar_path: Path):
        if not polar_path.exists():
            raise RuntimeError("XFOIL did not produce a polar file.")
        rows = []
        with open(polar_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("-"):
                    continue
                lower = line.lower()
                if "alpha" in lower or "xfoil" in lower or "re =" in lower or "mach =" in lower or "ncrit" in lower:
                    continue
                parts = line.split()
                if len(parts) < 7:
                    continue
                try:
                    alpha = float(parts[0])
                    cl = float(parts[1])
                    cd = float(parts[2])
                    cm = float(parts[4])
                except ValueError:
                    continue
                rows.append({"alpha": alpha, "cl": cl, "cd": cd, "cm": cm})
        if not rows:
            raise RuntimeError("XFOIL produced no valid polar rows.")
        return rows

    @staticmethod
    def _pick_nearest_alpha_row(rows, target_alpha):
        return min(rows, key=lambda row: abs(float(row["alpha"]) - float(target_alpha)))

    @staticmethod
    def _build_xfoil_input(dat_name, polar_name, reynolds, mach, ncrit, operation_lines):
        lines = [
            "PLOP",
            "G F",
            "",
            f"LOAD {dat_name}",
            "PANE",
            "OPER",
            f"VISC {reynolds:.6f}",
            f"MACH {max(0.0, float(mach)):.4f}",
            "VPAR",
            f"N {float(ncrit):.3f}",
            "",
            "ITER 150",
            "PACC",
            polar_name,
            "",
            *operation_lines,
            "PACC",
            "",
            "QUIT",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_xfoil_single_alpha_input(dat_name, polar_name, reynolds, mach, ncrit, alpha_deg):
        return App._build_xfoil_input(
            dat_name=dat_name,
            polar_name=polar_name,
            reynolds=reynolds,
            mach=mach,
            ncrit=ncrit,
            operation_lines=[f"ALFA {float(alpha_deg):.6f}", ""],
        )

    @staticmethod
    def _build_xfoil_aseq_input(dat_name, polar_name, reynolds, mach, ncrit, alpha_deg, use_init=False):
        alpha_target = float(alpha_deg)
        step = 0.5 if alpha_target >= 0.0 else -0.5
        op = []
        if use_init:
            op.extend(["INIT", ""])
        op.extend([f"ASEQ 0.000000 {alpha_target:.6f} {step:.6f}", ""])
        return App._build_xfoil_input(
            dat_name=dat_name,
            polar_name=polar_name,
            reynolds=reynolds,
            mach=mach,
            ncrit=ncrit,
            operation_lines=op,
        )

    @staticmethod
    def _normalize_profile_chord_one(x_vals, y_vals):
        x = np.asarray(x_vals, dtype=float)
        y = np.asarray(y_vals, dtype=float)
        x, y = strip_duplicate_closing_point(x, y)
        if len(x) < 3:
            raise RuntimeError("Geometry invalid for XFOIL.")
        xmin = float(np.min(x))
        xmax = float(np.max(x))
        span = xmax - xmin
        if span <= 1e-12:
            raise RuntimeError("Geometry invalid for XFOIL (zero chord).")
        x_norm = (x - xmin) / span
        y_norm = y / span
        return x_norm, y_norm

    def _build_xfoil_profile_points(self, vals):
        if vals["source_kind"] == "library":
            profile_name = vals.get("library_profile_name", "").strip()
            if not profile_name:
                raise RuntimeError("Geometry invalid for XFOIL.")
            geom = self._library_geometry_cache.get(profile_name)
            if geom is None:
                geom = self._airfoil_db.get_profile_geometry(profile_name)
                self._library_geometry_cache[profile_name] = geom
            x_raw = np.array(geom["x"], dtype=float)
            y_raw = np.array(geom["y"], dtype=float)
            return self._normalize_profile_chord_one(x_raw, y_raw)

        x_raw, y_raw = build_base_airfoil_xy(
            code=vals["code"],
            n_side=vals["n_side"],
            chord=1.0,
        )
        return self._normalize_profile_chord_one(x_raw, y_raw)

    def _set_aero_source_visual(self, source):
        src = (source or "").strip().lower()
        self.aero_source_var.set(src or "-")
        if not hasattr(self, "aero_source_value_label"):
            return
        if src == "xfoil_live":
            self.aero_source_value_label.configure(style="AeroSourceLive.TLabel")
        elif src in {"db_interpolated", "db"}:
            self.aero_source_value_label.configure(style="AeroSourceDb.TLabel")
        else:
            self.aero_source_value_label.configure(style="AeroSourceFallback.TLabel")

    def _set_xfoil_status(self, text, kind="info"):
        self.xfoil_status_var.set(text)
        if not hasattr(self, "xfoil_status_label"):
            return
        if kind == "ok":
            self.xfoil_status_label.configure(style="XfoilStatusOk.TLabel")
        elif kind == "error":
            self.xfoil_status_label.configure(style="XfoilStatusError.TLabel")
        else:
            self.xfoil_status_label.configure(style="XfoilStatusInfo.TLabel")

    def _set_xfoil_progress_ui(self, elapsed_s, timeout_s, phase_label):
        if not hasattr(self, "xfoil_button"):
            return
        timeout_s = max(float(timeout_s), 1e-6)
        elapsed = max(0.0, min(float(elapsed_s), timeout_s))
        pct = int(round((elapsed / timeout_s) * 100.0))
        remaining = max(0.0, timeout_s - elapsed)
        self.xfoil_button.configure(text=f"XFOIL {pct}% ({remaining:.1f}s)", state="disabled")
        if hasattr(self, "xfoil_progress"):
            self.xfoil_progress.configure(maximum=timeout_s, value=elapsed)
        self._set_xfoil_status(f"XFOIL running ({phase_label})...", kind="info")
        try:
            self.root.update_idletasks()
        except Exception:
            pass

    def _reset_xfoil_progress_ui(self):
        if hasattr(self, "xfoil_button"):
            self.xfoil_button.configure(text="XFOIL Simulation", state="normal")
        if hasattr(self, "xfoil_progress"):
            self.xfoil_progress.configure(maximum=100.0, value=0.0)

    def run_xfoil_simulation(self):
        try:
            self._set_xfoil_status("XFOIL running...", kind="info")
            self._reset_xfoil_progress_ui()
            vals = self.get_values()
            if vals["mode"] != "flat":
                raise ValueError("invalid_geometry")
            if vals["mirror_y"]:
                raise ValueError("invalid_geometry")

            alpha = vals["angle_deg"]
            if vals["mirror_x"]:
                alpha = -alpha

            fluid = self.fluid_var.get().strip().lower()
            if fluid in FLUID_PRESETS:
                temp_c = self.parse_temperature_c()
                density, viscosity = self.compute_fluid_properties(fluid, temp_c)
                self.density_var.set(f"{density:.6g}")
                self.viscosity_var.set(f"{viscosity:.6g}")
            else:
                density = float(self.density_var.get().replace(",", "."))
                viscosity = float(self.viscosity_var.get().replace(",", "."))
            velocity = float(self.velocity_var.get().replace(",", ".")) / 3.6
            reynolds = compute_reynolds(velocity, vals["chord"], density, viscosity)

            repo_root = Path(__file__).resolve().parent
            xfoil_path = repo_root / "xfoil" / "xfoil.exe"
            if not xfoil_path.exists():
                results = ensure_runtime_assets(include_airfoil_db=False, include_xfoil=True, assume_yes=True)
                installed = results.get("xfoil")
                if installed:
                    xfoil_path = Path(installed)
            if not xfoil_path.exists():
                raise RuntimeError("xfoil_missing")

            x_pts, y_pts = self._build_xfoil_profile_points(vals)
            if vals["source_kind"] == "library":
                try:
                    polar_set = self._get_library_polar_set(vals["library_profile_name"])
                    mach = float(polar_set.get("mach") or 0.0)
                    ncrit = float(polar_set.get("ncrit") or 9.0)
                except Exception:
                    mach = 0.0
                    ncrit = 9.0
            else:
                mach = 0.0
                ncrit = 9.0

            with tempfile.TemporaryDirectory(prefix="manta_xfoil_") as tmpdir:
                tmp = Path(tmpdir)
                dat_path = tmp / "profile.dat"
                polar_path = tmp / "polar.txt"
                log_path = tmp / "xfoil.log"
                inp_path = tmp / "xfoil.inp"
                with open(dat_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write("MantaProfile\n")
                    for xv, yv in zip(x_pts, y_pts):
                        f.write(f"{float(xv):.8f} {float(yv):.8f}\n")

                startupinfo = None
                creationflags = 0
                if os.name == "nt":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

                def _exec_xfoil(script_text, timeout_s):
                    if polar_path.exists():
                        try:
                            polar_path.unlink()
                        except OSError:
                            pass
                    with open(inp_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(script_text)
                    with open(inp_path, "r", encoding="utf-8") as stdin_file, open(log_path, "w", encoding="utf-8", newline="\n") as log_file:
                        proc = subprocess.Popen(
                            [str(xfoil_path)],
                            stdin=stdin_file,
                            stdout=log_file,
                            stderr=subprocess.STDOUT,
                            cwd=str(tmp),
                            startupinfo=startupinfo,
                            creationflags=creationflags,
                        )
                        started = time.monotonic()
                        phase = "single" if timeout_s <= 4.01 else ("aseq" if timeout_s <= 6.01 else "init+aseq")
                        while True:
                            rc = proc.poll()
                            elapsed = time.monotonic() - started
                            self._set_xfoil_progress_ui(elapsed, timeout_s, phase)
                            if rc is not None:
                                if rc != 0:
                                    raise RuntimeError("non_converged")
                                break
                            if elapsed >= timeout_s:
                                proc.kill()
                                try:
                                    proc.wait(timeout=2)
                                except Exception:
                                    pass
                                raise RuntimeError("timeout")
                            time.sleep(0.06)
                    rows = self._parse_xfoil_polar_rows(polar_path)
                    return self._pick_nearest_alpha_row(rows, alpha)

                sample = None
                try:
                    sample = _exec_xfoil(
                        self._build_xfoil_single_alpha_input(
                            dat_name=dat_path.name,
                            polar_name=polar_path.name,
                            reynolds=reynolds,
                            mach=mach,
                            ncrit=ncrit,
                            alpha_deg=alpha,
                        ),
                        timeout_s=4,
                    )
                except Exception:
                    try:
                        sample = _exec_xfoil(
                            self._build_xfoil_aseq_input(
                                dat_name=dat_path.name,
                                polar_name=polar_path.name,
                                reynolds=reynolds,
                                mach=mach,
                                ncrit=ncrit,
                                alpha_deg=alpha,
                                use_init=False,
                            ),
                            timeout_s=6,
                        )
                    except Exception:
                        sample = _exec_xfoil(
                            self._build_xfoil_aseq_input(
                                dat_name=dat_path.name,
                                polar_name=polar_path.name,
                                reynolds=reynolds,
                                mach=mach,
                                ncrit=ncrit,
                                alpha_deg=alpha,
                                use_init=True,
                            ),
                            timeout_s=7.5,
                        )

            signature = self._build_aero_signature(vals, reynolds, alpha)
            self._xfoil_live_result = {
                "signature": signature,
                "cl": float(sample["cl"]),
                "cd": max(float(sample["cd"]), 1e-6),
                "cm": float(sample["cm"]),
            }
            self._set_xfoil_status(
                f"XFOIL ok | alpha={alpha:.2f} | CL={sample['cl']:.3f} CD={sample['cd']:.4f}",
                kind="ok",
            )
            self.update_preview()
        except Exception as exc:
            message = str(exc).lower()
            if "xfoil_missing" in message or "xfoil.exe" in message:
                status = "XFOIL non trovato"
            elif "invalid_geometry" in message or "geometry invalid" in message:
                status = "Geometria non valida"
            elif "no valid polar rows" in message or "non_converged" in message or "timeout" in message:
                status = "Non converge"
            else:
                status = "Errore XFOIL"
            self._set_xfoil_status(status, kind="error")
        finally:
            self._reset_xfoil_progress_ui()

    def update_fluid_fields(self):
        fluid = self.fluid_var.get().strip().lower()
        state = "normal" if fluid == "custom" else "disabled"
        self.density_entry.config(state=state)
        self.viscosity_entry.config(state=state)
        if fluid in FLUID_PRESETS:
            temp_c = self.parse_temperature_c()
            density, viscosity = self.compute_fluid_properties(fluid, temp_c)
            self.density_var.set(f"{density:.6g}")
            self.viscosity_var.set(f"{viscosity:.6g}")

    def update_expert_visibility(self):
        # Advanced rows are currently hidden on purpose to keep the release UI
        # compact. To re-enable them, remove the target rows from
        # `always_hidden_rows` and optionally restore a visible Expert toggle.
        # Row 1 keeps temperature controls plus velocity slider visible; rows 2+ are advanced.
        always_hidden_rows = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
        persistent_widgets = {
            getattr(self, "temperature_label", None),
            getattr(self, "temperature_entry", None),
            getattr(self, "xfoil_button", None),
            getattr(self, "aero_source_label", None),
            getattr(self, "aero_source_value_label", None),
        }

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
            if row == 1 and column < 2 and widget not in persistent_widgets:
                widget.grid_remove()
                continue
            if widget in persistent_widgets:
                continue
            if row in always_hidden_rows:
                widget.grid_remove()

    def schedule_update(self, event=None):
        self.clear_xfoil_override()
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
        self._update_job = self.root.after(200, self.update_preview)

    def clear_xfoil_override(self):
        had_override = self._xfoil_live_result is not None
        self._xfoil_live_result = None
        if had_override:
            self._set_xfoil_status("XFOIL override cleared (input changed)", kind="info")

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
        source_kind = vals.get("source_kind", "naca")
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
            temp_c = self.parse_temperature_c()
            density, viscosity = self.compute_fluid_properties(fluid, temp_c)
            self.density_var.set(f"{density:.6g}")
            self.viscosity_var.set(f"{viscosity:.6g}")
        else:
            temp_c = self.parse_temperature_c()
            density = float(self.density_var.get().replace(",", "."))
            viscosity = float(self.viscosity_var.get().replace(",", "."))

        area = chord * span
        if velocity <= 0:
            raise ValueError("Velocity must be greater than zero.")
        if span <= 0:
            raise ValueError("Span must be greater than zero.")

        reynolds = compute_reynolds(velocity, chord, density, viscosity)
        signature = self._build_aero_signature(vals, reynolds, alpha)
        if self._xfoil_live_result and self._xfoil_live_result.get("signature") == signature:
            cl = float(self._xfoil_live_result["cl"])
            cd = max(float(self._xfoil_live_result["cd"]), 1e-6)
            cm = float(self._xfoil_live_result.get("cm", 0.0))
            params_source = "xfoil_live"
            force_nd = False
        elif source_kind == "library":
            profile_name = vals.get("library_profile_name", "").strip()
            if not profile_name:
                raise ValueError("Select a library profile.")
            re_scale = max(self._parse_float_or_default(self.aero_re_scale_var.get(), 1.0), 1e-6)
            alpha_offset = self._parse_float_or_default(self.aero_alpha_offset_var.get(), 0.0)
            cl_scale = self._parse_float_or_default(self.aero_cl_scale_var.get(), 1.0)
            cd_scale = max(self._parse_float_or_default(self.aero_cd_scale_var.get(), 1.0), 1e-6)
            coeffs = self.interpolate_library_coeffs(profile_name, reynolds * re_scale, alpha + alpha_offset)
            cl = float(coeffs["cl"]) * cl_scale
            cd = max(float(coeffs["cd"]) * cd_scale, 1e-6)
            cm = float(coeffs["cm"])
            params_source = "db_interpolated"
            force_nd = bool(coeffs.get("force_nd"))
        else:
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
            cm = 0.0
            params_source = params.get("source", "fallback")
            force_nd = False
        if vals["mirror_x"]:
            cl = -cl
        lift, drag, ld_ratio = compute_lift_drag(density=density, velocity=velocity, area=area, cl=cl, cd=cd)

        return {
            "reynolds": reynolds,
            "cl": cl,
            "cd": cd,
            "cm": cm,
            "temperature_c": temp_c,
            "lift": lift,
            "drag": drag,
            "ld_ratio": ld_ratio,
            "params_source": params_source,
            "force_nd": force_nd,
        }

    def update_aero_display(self, aero):
        if aero is None:
            self.reynolds_out_var.set("-")
            self.cl_out_var.set("-")
            self.cd_out_var.set("-")
            self.cm_out_var.set("-")
            self.lift_out_var.set("-")
            self.drag_out_var.set("-")
            self.ld_out_var.set("-")
            self.lift_label_var.set("Lift [kg]")
            self.drag_label_var.set("Drag [kg]")
            self._set_aero_source_visual("-")
            return
        self.reynolds_out_var.set(f"{aero['reynolds']:.3e}")
        self.cl_out_var.set(f"{aero['cl']:.4f}")
        self.cd_out_var.set(f"{aero['cd']:.4f}")
        self.cm_out_var.set(f"{aero.get('cm', 0.0):.4f}")
        lift_kg = aero["lift"] / 9.80665
        drag_kg = aero["drag"] / 9.80665
        self.lift_label_var.set("Downforce [kg]" if lift_kg < 0 else "Lift [kg]")
        self.drag_label_var.set("Drag [kg]")
        self.lift_out_var.set(f"{lift_kg:.1f}")
        self.drag_out_var.set(f"{drag_kg:.1f}")
        self.ld_out_var.set(f"{aero['ld_ratio']:.3f}")
        self._set_aero_source_visual(aero.get("params_source", "fallback"))

    def show_aero_forces_nd(self):
        self.lift_out_var.set("ND")
        self.drag_out_var.set("ND")
        self.ld_out_var.set("ND")

    def get_values(self):
        source_kind = self.source_internal_value()
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
            "source_kind": source_kind,
            "library_profile_name": self._get_selected_library_profile_name(),
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
            x, y = self.generate_profile_xy(vals)
            pts_fmt = self.pts_format_var.get().strip().lower()
            if pts_fmt == "xy":
                pts_text, x, y, _ = write_pts_xy_text(x, y, decimals=vals["decimals"])
            else:
                pts_text, x, y, _ = write_pts_text(x, y, decimals=vals["decimals"])
            mode_label = "Flat" if vals["mode"] == "flat" else "Curved"
            if vals["source_kind"] == "library":
                self.header_profile_var.set(vals["library_profile_name"] or "Library profile")
            else:
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
            aero = None
            aero_error = ""
            if aero_enabled:
                try:
                    aero = self.compute_aero_results(vals)
                except Exception as exc:
                    aero_error = str(exc)

            self.last_pts_text = pts_text
            self.last_x = x
            self.last_y = y

            self.text.delete("1.0", "end")
            self.text.insert("1.0", pts_text)
            self.update_aero_display(aero)
            if aero is not None and aero.get("force_nd"):
                self.show_aero_forces_nd()
                self.header_status_var.set(
                    f"{mode_label} profile | chord {vals['chord'] * 1000:.0f} mm | span {vals['span'] * 1000:.0f} mm | aero ND"
                )

            self.redraw_plot(x, y, vals, aero)
        except Exception as e:
            self.header_profile_var.set("Profile")
            if self.source_internal_value() == "library" and self._library_load_error:
                self.header_status_var.set(f"Library unavailable: {self._library_load_error}")
            else:
                self.header_status_var.set("Check the current inputs")
            self.preview_mode_var.set("-")
            self.preview_points_var.set("-")
            self.preview_format_var.set("-")
            self.reynolds_out_var.set("-")
            self.cl_out_var.set("-")
            self.cd_out_var.set("-")
            self.cm_out_var.set("-")
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
        profile_label = vals["library_profile_name"] if vals.get("source_kind") == "library" else f"NACA {vals['code']}"
        title = (
            f"{profile_label} | chord={vals['chord'] * 1000:.1f} mm | "
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
        profile_label = vals["library_profile_name"] if vals.get("source_kind") == "library" else f"NACA {vals['code']}"
        title = (
            f"{profile_label} | chord={vals['chord'] * 1000:.1f} mm | "
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
            x, y = self.generate_profile_xy(vals)
            fmt = self.pts_format_var.get().strip().lower()
            if fmt == "xy":
                pts_text, _, _, _ = write_pts_xy_text(x, y, decimals=vals["decimals"])
            else:
                pts_text, _, _, _ = write_pts_text(x, y, decimals=vals["decimals"])

            default_name = f"{self.default_export_stem(vals)}.pts"
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
            x, y = self.generate_profile_xy(vals)
            fmt = self.csv_format_var.get().strip().lower()
            if fmt == "xy":
                csv_text, _, _, _ = write_csv_xy_text(x, y, decimals=vals["decimals"])
            else:
                csv_text, _, _, _ = write_csv_xyz_text(x, y, decimals=vals["decimals"])

            default_name = f"{self.default_export_stem(vals)}.csv"
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
            x, y = self.generate_profile_xy(vals)

            default_name = f"{self.default_export_stem(vals)}.dxf"
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
            x, y = self.generate_profile_xy(vals)

            default_name = f"{self.default_export_stem(vals)}.stl"
            path = filedialog.asksaveasfilename(
                title="Save .stl file",
                defaultextension=".stl",
                initialfile=default_name,
                filetypes=[("STL files", "*.stl"), ("All files", "*.*")],
            )
            if not path:
                return

            write_stl_ascii(path, x, y, vals["span"], solid_name=self.default_export_stem(vals))
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
    ensure_local_directories()
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
        prog="manta_airfoil_tools.py",
        description="Manta AirLab CLI for Airfoil Tools (GUI remains the default with no arguments).",
        epilog="Manta AirLab — Airfoil Tools by Fabio Giuliodori | duilio.cc",
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

    setup_cmd = subparsers.add_parser("setup", help="Install runtime Python packages and external assets.")
    setup_cmd.add_argument("--yes", action="store_true", help="Install without interactive confirmation prompts.")
    setup_cmd.add_argument("--skip-python", action="store_true", help="Skip Python package installation checks.")
    setup_cmd.add_argument(
        "--skip-airfoil-db",
        action="store_true",
        help="Skip airfoil.db update/download.",
    )
    setup_cmd.add_argument("--skip-xfoil", action="store_true", help="Skip XFOIL download.")

    return parser


def run_cli(argv):
    if not argv:
        return None

    parser = build_cli_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return None

    try:
        if args.command == "setup":
            ok = True
            if not args.skip_python:
                packages = []
                if np is None:
                    packages.append("numpy")
                if FigureCanvasTkAgg is None or Figure is None or Poly3DCollection is None:
                    packages.append("matplotlib")
                if not ensure_python_packages(
                    packages,
                    context="Needed for GUI plotting and numeric processing.",
                    assume_yes=args.yes,
                ):
                    ok = False

            results = ensure_runtime_assets(
                include_airfoil_db=not args.skip_airfoil_db,
                include_xfoil=not args.skip_xfoil,
                assume_yes=args.yes,
                refresh_airfoil_db=not args.skip_airfoil_db,
            )
            if not args.skip_airfoil_db and not results.get("airfoil_db"):
                ok = False
            if not args.skip_xfoil and not results.get("xfoil"):
                ok = False

            if ok:
                print("Setup completed.")
                if results.get("airfoil_db"):
                    print(f"airfoil.db: {results['airfoil_db']}")
                if results.get("xfoil"):
                    print(f"xfoil.exe: {results['xfoil']}")
                return 0
            return 1

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


