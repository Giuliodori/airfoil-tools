"""Centralized default values for Airfoil Tools (GUI + CLI)."""

FLUID_PRESETS = {
    "air": {"rho": 1.225, "mu": 1.81e-5},
    "water": {"rho": 997.0, "mu": 8.9e-4},
    "salt water": {"rho": 1025.0, "mu": 1.08e-3},
}

GUI_DEFAULTS = {
    "code": "2412",
    "chord_mm": "100",
    "points_side": "100",
    "mode": "Flat profile",
    "radius_mm": "100",
    "curvature_dir": "convex",
    "keep_developed_chord": True,
    "angle_deg": "0",
    "decimals": "6",
    "mirror_x": False,
    "mirror_y": False,
    "fluid": "water",
    "velocity_kmh": "50",
    "aero_chord_mm": "100",
    "span_mm": "200",
    "alpha_deg": "0.0",
    "naca_camber": 2,
    "naca_pos": 4,
    "naca_thickness": 12,
    "show_expert": False,
}

CLI_DEFAULTS = {
    "export_format": "pts",
    "export_coord_mode": "xyz",
    "dxf_entity": "polyline",
    "chord_mm": 100.0,
    "points_side": 100,
    "rotation_deg": 0.0,
    "decimals": 6,
    "velocity_kmh": 50.0,
    "span_mm": 200.0,
    "alpha_deg": 0.0,
    "fluid": "water",
}
