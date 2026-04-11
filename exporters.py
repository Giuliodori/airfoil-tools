"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Export helper module for Manta AirLab.
Writes profile geometry to PTS, CSV, DXF, and STL formats.
"""

from __future__ import annotations

import numpy as np

from geometry import build_extruded_mesh, close_profile, naca4_points_base, transform_points
from setup import ensure_python_packages


def format_number(value: float, decimals: int = 6) -> str:
    if abs(value) < 0.5 * 10 ** (-decimals):
        return "0"
    if abs(value - round(value)) < 0.5 * 10 ** (-decimals):
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def write_pts_text(x, y, decimals: int = 6):
    x, y = close_profile(x, y)
    z = np.zeros_like(x)
    lines = [
        f"{format_number(float(xv), decimals)}\t{format_number(float(yv), decimals)}\t{format_number(float(zv), decimals)}"
        for xv, yv, zv in zip(x, y, z)
    ]
    return "\n".join(lines), x, y, z


def write_pts_xy_text(x, y, decimals: int = 6):
    x, y = close_profile(x, y)
    lines = [
        f"{format_number(float(xv), decimals)}\t{format_number(float(yv), decimals)}"
        for xv, yv in zip(x, y)
    ]
    return "\n".join(lines), x, y, None


def write_csv_xyz_text(x, y, decimals: int = 6):
    x, y = close_profile(x, y)
    z = np.zeros_like(x)
    lines = [
        f"{format_number(float(xv), decimals)},{format_number(float(yv), decimals)},{format_number(float(zv), decimals)}"
        for xv, yv, zv in zip(x, y, z)
    ]
    return "\n".join(lines), x, y, z


def write_csv_xy_text(x, y, decimals: int = 6):
    x, y = close_profile(x, y)
    lines = [
        f"{format_number(float(xv), decimals)},{format_number(float(yv), decimals)}"
        for xv, yv in zip(x, y)
    ]
    return "\n".join(lines), x, y, None


def _load_ezdxf(prompt_install: bool):
    try:
        import ezdxf
    except ImportError as exc:
        if not prompt_install:
            raise RuntimeError("DXF export requires 'ezdxf'. Install with: pip install ezdxf") from exc
        if not ensure_python_packages(["ezdxf"], context="Needed to export DXF files."):
            raise RuntimeError("Library 'ezdxf' is not installed. Install with: pip install ezdxf") from exc
        try:
            import ezdxf  # type: ignore
        except Exception as err:
            raise RuntimeError("Library 'ezdxf' was installed but could not be imported.") from err
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
    write_dxf(path, x, y, layer=layer, mode="polyline")


def write_dxf_polyline_cli(path: str, x, y, layer: str = "AIRFOIL"):
    write_dxf_cli(path, x, y, layer=layer, mode="polyline")


def _triangle_normal(v1, v2, v3):
    n = np.cross(v2 - v1, v3 - v1)
    norm = np.linalg.norm(n)
    if norm <= 1e-15:
        return np.array([0.0, 0.0, 0.0], dtype=float)
    return n / norm


def write_stl_ascii(path: str, x, y, span: float, solid_name: str = "airfoil"):
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


def build_pts_text(code: str, n_side: int, chord: float, angle_deg: float, mirror_x: bool, mirror_y: bool, decimals: int = 6):
    x, y, z = naca4_points_base(code=code, n_side=n_side, chord=chord)
    x, y = transform_points(x, y, angle_deg=angle_deg, mirror_x=mirror_x, mirror_y=mirror_y)
    pts_text, x, y, z = write_pts_text(x, y, decimals=decimals)
    return pts_text, x, y, z
