"""
SQLite read-only access layer for `database/airfoil.db`.
"""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any


if getattr(sys, "frozen", False):
    REPO_ROOT = Path(sys.executable).resolve().parent
else:
    REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = REPO_ROOT / "database" / "airfoil.db"


class AirfoilDbError(RuntimeError):
    pass


def _parse_raw_dat_points(raw_dat: str) -> tuple[list[float], list[float]]:
    x_vals: list[float] = []
    y_vals: list[float] = []
    for idx, raw_line in enumerate(raw_dat.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("#", "!", ";", "//")):
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            x = float(parts[0])
            y = float(parts[1])
        except ValueError:
            if idx == 0:
                continue
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            raise AirfoilDbError("Geometry contains non-finite values in raw_dat.")
        x_vals.append(x)
        y_vals.append(y)
    return x_vals, y_vals


def _ensure_geometry(x_vals: list[float], y_vals: list[float]) -> tuple[list[float], list[float]]:
    if len(x_vals) != len(y_vals):
        raise AirfoilDbError("Geometry length mismatch between x and y arrays.")
    if len(x_vals) < 3:
        raise AirfoilDbError("Geometry must contain at least 3 points.")
    for x, y in zip(x_vals, y_vals):
        if not (math.isfinite(x) and math.isfinite(y)):
            raise AirfoilDbError("Geometry contains non-finite values.")
    return x_vals, y_vals


class AirfoilDb:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    def _connect(self) -> sqlite3.Connection:
        resolved = self.db_path.resolve()
        if not resolved.exists():
            raise AirfoilDbError(f"Database not found: {resolved}")
        uri = f"file:{resolved.as_posix()}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        return con

    def _table_columns(self, con: sqlite3.Connection, table_name: str) -> set[str]:
        rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

    def _table_exists(self, con: sqlite3.Connection, table_name: str) -> bool:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            [table_name],
        ).fetchone()
        return row is not None

    def list_profiles(
        self,
        *,
        include_excluded: bool = False,
        only_valid_geometry: bool = True,
        only_xfoil_compatible: bool = False,
        search: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        where_parts: list[str] = []
        params: list[Any] = []

        if not include_excluded:
            where_parts.append("COALESCE(exclude_from_final, 0) = 0")
        if only_valid_geometry:
            where_parts.append("COALESCE(is_valid_geometry, 0) = 1")
        if only_xfoil_compatible:
            where_parts.append("COALESCE(is_xfoil_compatible, 0) = 1")
        if search:
            where_parts.append("(name LIKE ? OR title LIKE ? OR family LIKE ?)")
            token = f"%{search.strip()}%"
            params.extend([token, token, token])

        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        limit_sql = " LIMIT ?" if limit is not None and limit > 0 else ""
        if limit_sql:
            params.append(limit)

        query = (
            "SELECT name, title, family, source, source_url, n_points, "
            "max_thickness, max_thickness_x, max_camber, max_camber_x, "
            "is_valid_geometry, is_xfoil_compatible, exclude_from_final "
            "FROM airfoils "
            f"{where_sql} "
            "ORDER BY name ASC"
            f"{limit_sql}"
        )

        with self._connect() as con:
            rows = con.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_filter_presets(self) -> list[dict[str, Any]]:
        with self._connect() as con:
            if not self._table_exists(con, "airfoil_filter_presets"):
                return []
            rows = con.execute(
                """
                SELECT label, profile_type_filter, usage_filter, display_order, enabled
                FROM airfoil_filter_presets
                WHERE COALESCE(enabled, 1) = 1
                ORDER BY display_order ASC, label ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def list_profiles_with_ratings(
        self,
        *,
        include_excluded: bool = False,
        only_valid_geometry: bool = True,
        only_xfoil_compatible: bool = False,
        search: str | None = None,
        usage_filter: str | None = None,
        usage_filters: list[str] | None = None,
        profile_type_filter: str | None = None,
        profile_type_filters: list[str] | None = None,
        autostable_min_score: float | None = None,
        high_lift_min_score: float | None = None,
        famous_min_score: float | None = None,
        rotating_min_score: float | None = None,
        hydro_min_score: float | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        where_parts: list[str] = []
        params: list[Any] = []

        usage_filter_tokens: list[str] = []
        for raw_token in [usage_filter, *(usage_filters or [])]:
            token = (raw_token or "").strip()
            if token:
                usage_filter_tokens.append(token)

        profile_tokens_raw: list[str] = []
        for raw_token in [profile_type_filter, *(profile_type_filters or [])]:
            token = (raw_token or "").strip()
            if token:
                profile_tokens_raw.append(token)
        seen_profile_tokens: set[str] = set()
        profile_tokens: list[str] = []
        for token in profile_tokens_raw:
            key = token.lower()
            if key in seen_profile_tokens:
                continue
            seen_profile_tokens.add(key)
            profile_tokens.append(token)

        if not include_excluded:
            where_parts.append("COALESCE(a.exclude_from_final, 0) = 0")
        if only_valid_geometry:
            where_parts.append("COALESCE(a.is_valid_geometry, 0) = 1")
        if only_xfoil_compatible:
            where_parts.append("COALESCE(a.is_xfoil_compatible, 0) = 1")
        if search:
            where_parts.append("(a.name LIKE ? OR a.title LIKE ? OR a.family LIKE ?)")
            token = f"%{search.strip()}%"
            params.extend([token, token, token])
        for usage_token in usage_filter_tokens:
            where_parts.append(
                "EXISTS ("
                "SELECT 1 FROM airfoil_applications ap "
                "WHERE ap.matched_profile_name = a.name "
                "AND (ap.role_label LIKE ? OR ap.aircraft_section LIKE ? OR ap.aircraft_name LIKE ?)"
                ")"
            )
            u = f"%{usage_token}%"
            params.extend([u, u, u])

        with self._connect() as con:
            rating_cols = self._table_columns(con, "airfoil_ratings")
            versatility_expr = "ar.versatility_score" if "versatility_score" in rating_cols else "0.0"
            has_usage_summary = self._table_exists(con, "airfoil_usage_summary")
            usage_summary_cols = self._table_columns(con, "airfoil_usage_summary") if has_usage_summary else set()

            if has_usage_summary:
                usage_join_sql = "LEFT JOIN airfoil_usage_summary aus ON aus.airfoil_name = a.name "
                top_usage_expr = "aus.top_usage"
                top_aircraft_expr = "aus.top_aircraft"
                top_usages_expr = "aus.top_usages"
                usage_count_expr = "aus.usage_count"
                autostable_score_expr = "aus.autostable_score"
                high_lift_score_expr = "aus.high_lift_score"
                famous_score_expr = "aus.famous_score"
                rotating_score_expr = "aus.rotating_score" if "rotating_score" in usage_summary_cols else "NULL"
                hydro_score_expr = "aus.hydro_score" if "hydro_score" in usage_summary_cols else "NULL"
            else:
                usage_join_sql = ""
                top_usage_expr = (
                    "("
                    "SELECT ap.role_label FROM airfoil_applications ap "
                    "WHERE ap.matched_profile_name = a.name AND ap.role_label IS NOT NULL "
                    "ORDER BY COALESCE(ap.confidence, 0) DESC, ap.id DESC LIMIT 1"
                    ")"
                )
                top_aircraft_expr = (
                    "("
                    "SELECT ap.aircraft_name FROM airfoil_applications ap "
                    "WHERE ap.matched_profile_name = a.name AND ap.aircraft_name IS NOT NULL "
                    "AND TRIM(ap.aircraft_name) <> '' "
                    "ORDER BY COALESCE(ap.confidence, 0) DESC, ap.id DESC LIMIT 1"
                    ")"
                )
                top_usages_expr = (
                    "("
                    "SELECT GROUP_CONCAT(item, ' | ') FROM ("
                    "SELECT CASE "
                    "WHEN ap.aircraft_name IS NOT NULL AND TRIM(ap.aircraft_name) <> '' "
                    "THEN TRIM(ap.role_label) || ' @ ' || TRIM(ap.aircraft_name) "
                    "ELSE TRIM(ap.role_label) END AS item "
                    "FROM airfoil_applications ap "
                    "WHERE ap.matched_profile_name = a.name "
                    "AND ap.role_label IS NOT NULL AND TRIM(ap.role_label) <> '' "
                    "ORDER BY COALESCE(ap.confidence, 0) DESC, ap.id DESC "
                    "LIMIT 3"
                    ")"
                    ")"
                )
                usage_count_expr = (
                    "("
                    "SELECT COUNT(*) FROM airfoil_applications ap "
                    "WHERE ap.matched_profile_name = a.name"
                    ")"
                )
                autostable_score_expr = "NULL"
                high_lift_score_expr = "NULL"
                famous_score_expr = "NULL"
                rotating_score_expr = "NULL"
                hydro_score_expr = "NULL"

            if (
                high_lift_min_score is not None
                and has_usage_summary
                and "high_lift_score" in usage_summary_cols
            ):
                min_score = max(0.0, min(100.0, float(high_lift_min_score)))
                where_parts.append("COALESCE(aus.high_lift_score, -1000.0) >= ?")
                params.append(min_score)
            if (
                famous_min_score is not None
                and has_usage_summary
                and "famous_score" in usage_summary_cols
            ):
                min_score = max(0.0, min(100.0, float(famous_min_score)))
                where_parts.append("COALESCE(aus.famous_score, -1000.0) >= ?")
                params.append(min_score)
            if (
                rotating_min_score is not None
                and has_usage_summary
                and "rotating_score" in usage_summary_cols
            ):
                min_score = max(0.0, min(100.0, float(rotating_min_score)))
                where_parts.append("COALESCE(aus.rotating_score, -1000.0) >= ?")
                params.append(min_score)
            if (
                hydro_min_score is not None
                and has_usage_summary
                and "hydro_score" in usage_summary_cols
            ):
                min_score = max(0.0, min(100.0, float(hydro_min_score)))
                where_parts.append("COALESCE(aus.hydro_score, -1000.0) >= ?")
                params.append(min_score)

            has_autostable_token = any(token.lower() == "autostable" for token in profile_tokens)
            has_high_lift_token = any(token.lower() == "high_lift" for token in profile_tokens)
            has_famous_token = any(token.lower() == "famous" for token in profile_tokens)
            has_rotating_token = any(token.lower() == "rotating" for token in profile_tokens)
            has_hydro_token = any(token.lower() == "hydro" for token in profile_tokens)
            if (
                has_autostable_token
                and has_usage_summary
                and "autostable_score" in usage_summary_cols
            ):
                min_score = float(autostable_min_score if autostable_min_score is not None else 20.0)
                where_parts.append("COALESCE(aus.autostable_score, -1000.0) >= ?")
                params.append(min_score)
            if (
                has_high_lift_token
                and high_lift_min_score is None
                and has_usage_summary
                and "high_lift_score" in usage_summary_cols
            ):
                where_parts.append("COALESCE(aus.high_lift_score, -1000.0) >= ?")
                params.append(0.0)
            if (
                has_famous_token
                and famous_min_score is None
                and has_usage_summary
                and "famous_score" in usage_summary_cols
            ):
                where_parts.append("COALESCE(aus.famous_score, -1000.0) >= ?")
                params.append(0.0)
            if (
                has_rotating_token
                and rotating_min_score is None
                and has_usage_summary
                and "rotating_score" in usage_summary_cols
            ):
                where_parts.append("COALESCE(aus.rotating_score, -1000.0) >= ?")
                params.append(20.0)
            if (
                has_hydro_token
                and hydro_min_score is None
                and has_usage_summary
                and "hydro_score" in usage_summary_cols
            ):
                where_parts.append("COALESCE(aus.hydro_score, -1000.0) >= ?")
                params.append(20.0)

            for profile_token in profile_tokens:
                token_lower = profile_token.lower()
                if (
                    token_lower == "autostable"
                    and has_usage_summary
                    and "autostable_score" in usage_summary_cols
                ):
                    continue
                if (
                    token_lower == "high_lift"
                    and has_usage_summary
                    and "high_lift_score" in usage_summary_cols
                ):
                    continue
                if (
                    token_lower == "famous"
                    and has_usage_summary
                    and "famous_score" in usage_summary_cols
                ):
                    continue
                if (
                    token_lower == "rotating"
                    and has_usage_summary
                    and "rotating_score" in usage_summary_cols
                ):
                    continue
                if (
                    token_lower == "hydro"
                    and has_usage_summary
                    and "hydro_score" in usage_summary_cols
                ):
                    continue

                where_parts.append(
                    "EXISTS ("
                    "SELECT 1 FROM airfoil_applications ap "
                    "WHERE ap.matched_profile_name = a.name "
                    "AND ("
                    "COALESCE(ap.profile_type_tag, '') = ? COLLATE NOCASE "
                    "OR COALESCE(ap.reason_tag, '') = ? COLLATE NOCASE "
                    "OR LOWER(COALESCE(ap.role_label, '')) LIKE ? "
                    "OR LOWER(COALESCE(ap.aircraft_section, '')) LIKE ?"
                    ")"
                    ")"
                )
                like_token = f"%{token_lower}%"
                params.extend([profile_token, profile_token, like_token, like_token])

            where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
            limit_sql = " LIMIT ?" if limit is not None and limit > 0 else ""
            query_params = list(params)
            if limit_sql:
                query_params.append(limit)

            query = (
                "WITH latest_ratings AS ("
                "SELECT r.* FROM airfoil_ratings r "
                "JOIN ("
                "SELECT airfoil_name, MAX(id) AS max_id "
                "FROM airfoil_ratings GROUP BY airfoil_name"
                ") x ON x.max_id = r.id"
                ") "
                "SELECT "
                "a.name, a.title, a.family, a.source, a.source_url, a.n_points, "
                "a.max_thickness, a.max_thickness_x, a.max_camber, a.max_camber_x, "
                "a.is_valid_geometry, a.is_xfoil_compatible, a.exclude_from_final, "
                "ar.performance_score, ar.docility_score, ar.robustness_score, ar.confidence_score, "
                f"{versatility_expr} AS versatility_score, "
                "ar.rating_version, ar.rating_notes, "
                f"{top_usage_expr} AS top_usage, "
                f"{top_aircraft_expr} AS top_aircraft, "
                f"{top_usages_expr} AS top_usages, "
                f"{usage_count_expr} AS usage_count, "
                f"{autostable_score_expr} AS autostable_score, "
                f"{high_lift_score_expr} AS high_lift_score, "
                f"{famous_score_expr} AS famous_score, "
                f"{rotating_score_expr} AS rotating_score, "
                f"{hydro_score_expr} AS hydro_score "
                "FROM airfoils a "
                "LEFT JOIN latest_ratings ar ON ar.airfoil_name = a.name "
                f"{usage_join_sql}"
                f"{where_sql} "
                "ORDER BY a.name ASC"
                f"{limit_sql}"
            )
            rows = con.execute(query, query_params).fetchall()
        return [dict(row) for row in rows]

    def get_profile_geometry(self, profile_name: str) -> dict[str, Any]:
        name = profile_name.strip()
        if not name:
            raise AirfoilDbError("profile_name is required.")

        query = (
            "SELECT name, title, family, n_points, x_json, y_json, raw_dat "
            "FROM airfoils WHERE name = ?"
        )
        with self._connect() as con:
            row = con.execute(query, [name]).fetchone()
        if row is None:
            raise AirfoilDbError(f"Profile not found: {name}")

        source = ""
        if row["x_json"] and row["y_json"]:
            try:
                x_vals = [float(v) for v in json.loads(row["x_json"])]
                y_vals = [float(v) for v in json.loads(row["y_json"])]
                source = "json"
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise AirfoilDbError(f"Invalid x_json/y_json for profile: {name}") from exc
        elif row["raw_dat"]:
            x_vals, y_vals = _parse_raw_dat_points(str(row["raw_dat"]))
            source = "raw_dat"
        else:
            raise AirfoilDbError(f"No geometry data for profile: {name}")

        x_vals, y_vals = _ensure_geometry(x_vals, y_vals)
        return {
            "name": row["name"],
            "title": row["title"],
            "family": row["family"],
            "n_points": row["n_points"],
            "x": x_vals,
            "y": y_vals,
            "source": source,
        }

    def list_polar_sets(self, profile_name: str) -> list[dict[str, Any]]:
        query = (
            "SELECT mach, ncrit, COUNT(*) AS rows_count, "
            "SUM(CASE WHEN COALESCE(converged, 0) = 1 THEN 1 ELSE 0 END) AS converged_rows "
            "FROM airfoil_polars_xfoil "
            "WHERE airfoil_name = ? "
            "GROUP BY mach, ncrit "
            "ORDER BY rows_count DESC, mach ASC, ncrit ASC"
        )
        with self._connect() as con:
            rows = con.execute(query, [profile_name]).fetchall()
        return [dict(row) for row in rows]

    def list_reynolds(
        self,
        profile_name: str,
        *,
        mach: float | None = None,
        ncrit: float | None = None,
        converged_only: bool = True,
    ) -> list[float]:
        where_parts = ["airfoil_name = ?"]
        params: list[Any] = [profile_name]
        if mach is not None:
            where_parts.append("mach = ?")
            params.append(float(mach))
        if ncrit is not None:
            where_parts.append("ncrit = ?")
            params.append(float(ncrit))
        if converged_only:
            where_parts.append("COALESCE(converged, 0) = 1")

        where_sql = " AND ".join(where_parts)
        query = (
            "SELECT DISTINCT reynolds FROM airfoil_polars_xfoil "
            f"WHERE {where_sql} "
            "ORDER BY reynolds ASC"
        )
        with self._connect() as con:
            rows = con.execute(query, params).fetchall()
        return [float(row["reynolds"]) for row in rows]

    def get_polar_rows(
        self,
        profile_name: str,
        reynolds: float,
        *,
        mach: float | None = None,
        ncrit: float | None = None,
        converged_only: bool = True,
    ) -> list[dict[str, Any]]:
        where_parts = ["airfoil_name = ?", "reynolds = ?"]
        params: list[Any] = [profile_name, float(reynolds)]
        if mach is not None:
            where_parts.append("mach = ?")
            params.append(float(mach))
        if ncrit is not None:
            where_parts.append("ncrit = ?")
            params.append(float(ncrit))
        if converged_only:
            where_parts.append("COALESCE(converged, 0) = 1")

        where_sql = " AND ".join(where_parts)
        query = (
            "SELECT reynolds, mach, ncrit, alpha_deg, cl, cd, cm, converged "
            "FROM airfoil_polars_xfoil "
            f"WHERE {where_sql} "
            "ORDER BY alpha_deg ASC"
        )
        with self._connect() as con:
            rows = con.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_profile_rating(self, profile_name: str) -> dict[str, Any] | None:
        query = (
            "SELECT airfoil_name, performance_score, docility_score, robustness_score, "
            "confidence_score, rating_version, rating_notes, created_at "
            "FROM airfoil_ratings "
            "WHERE airfoil_name = ? "
            "ORDER BY id DESC LIMIT 1"
        )
        with self._connect() as con:
            row = con.execute(query, [profile_name]).fetchone()
        return dict(row) if row is not None else None

    def list_profile_usage(self, profile_name: str, limit: int = 30) -> list[dict[str, Any]]:
        cap = max(1, int(limit))
        query = (
            "SELECT matched_profile_name, aircraft_name, aircraft_section, role_code, role_label, "
            "confidence, source, source_url "
            "FROM airfoil_applications "
            "WHERE matched_profile_name = ? "
            "ORDER BY confidence DESC, aircraft_name ASC "
            "LIMIT ?"
        )
        with self._connect() as con:
            rows = con.execute(query, [profile_name, cap]).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    db = AirfoilDb()
    profiles = db.list_profiles(limit=5)
    print(f"profiles={len(profiles)}")
    for item in profiles:
        print(item["name"], item.get("title") or "")
