"""Query functions for the Delhivery Commerce AI data layer.

All functions accept a sqlite3.Connection (with row_factory=sqlite3.Row)
and return plain dicts.  Pydantic models are layered on top in Task 2.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def _rows_to_dicts(cursor: sqlite3.Cursor) -> List[dict]:
    """Convert all rows from a cursor into a list of plain dicts."""
    return [dict(row) for row in cursor.fetchall()]


def _row_to_dict(cursor: sqlite3.Cursor) -> Optional[dict]:
    """Fetch one row and return it as a dict, or None."""
    row = cursor.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Merchant snapshot
# ---------------------------------------------------------------------------

def get_merchant_snapshot(db: sqlite3.Connection, merchant_id: str) -> dict:
    """Return merchant info, warehouse nodes, distributions, and benchmark gaps."""

    # Merchant info
    merchant = _row_to_dict(
        db.execute("SELECT * FROM merchants WHERE merchant_id = ?", (merchant_id,))
    )
    if merchant is None:
        return {}

    # Warehouse nodes
    warehouse_nodes = _rows_to_dicts(
        db.execute(
            "SELECT * FROM warehouse_nodes WHERE merchant_id = ? AND is_active = 1",
            (merchant_id,),
        )
    )

    # Category distribution
    category_dist = _rows_to_dicts(
        db.execute(
            """
            SELECT category, COUNT(*) AS order_count
            FROM orders
            WHERE merchant_id = ?
            GROUP BY category
            """,
            (merchant_id,),
        )
    )

    # Price band distribution
    price_band_dist = _rows_to_dicts(
        db.execute(
            """
            SELECT price_band, COUNT(*) AS order_count
            FROM orders
            WHERE merchant_id = ?
            GROUP BY price_band
            """,
            (merchant_id,),
        )
    )

    # Payment mode distribution
    payment_mode_dist = _rows_to_dicts(
        db.execute(
            """
            SELECT payment_mode, COUNT(*) AS order_count
            FROM orders
            WHERE merchant_id = ?
            GROUP BY payment_mode
            """,
            (merchant_id,),
        )
    )

    # Benchmark gaps: merchant delivery rate vs peer avg per cohort dimension
    benchmark_gaps = _rows_to_dicts(
        db.execute(
            """
            WITH merchant_rates AS (
                SELECT
                    category,
                    price_band,
                    payment_mode,
                    origin_node,
                    destination_cluster,
                    COUNT(*) AS order_count,
                    AVG(CASE WHEN delivery_outcome = 'delivered' THEN 1.0 ELSE 0.0 END) AS merchant_rate
                FROM orders
                WHERE merchant_id = ?
                GROUP BY category, price_band, payment_mode, origin_node, destination_cluster
            ),
            peer_rates AS (
                SELECT
                    category,
                    price_band,
                    payment_mode,
                    origin_node,
                    destination_cluster,
                    AVG(CASE WHEN delivery_outcome = 'delivered' THEN 1.0 ELSE 0.0 END) AS peer_rate,
                    COUNT(*) AS peer_sample_size
                FROM orders
                WHERE merchant_id != ?
                GROUP BY category, price_band, payment_mode, origin_node, destination_cluster
            )
            SELECT
                m.category,
                m.price_band,
                m.payment_mode,
                m.origin_node,
                m.destination_cluster,
                m.order_count,
                m.merchant_rate,
                p.peer_rate,
                p.peer_sample_size,
                (m.merchant_rate - p.peer_rate) AS gap
            FROM merchant_rates m
            LEFT JOIN peer_rates p
                ON m.category = p.category
                AND m.price_band = p.price_band
                AND m.payment_mode = p.payment_mode
                AND m.origin_node = p.origin_node
                AND m.destination_cluster = p.destination_cluster
            """,
            (merchant_id, merchant_id),
        )
    )

    return {
        "merchant_id": merchant["merchant_id"],
        "name": merchant.get("name"),
        "warehouse_nodes": warehouse_nodes,
        "category_distribution": {r["category"]: r["order_count"] for r in category_dist},
        "price_band_distribution": {r["price_band"]: r["order_count"] for r in price_band_dist},
        "payment_mode_distribution": {r["payment_mode"]: r["order_count"] for r in payment_mode_dist},
        "benchmark_gaps": benchmark_gaps,
    }


# ---------------------------------------------------------------------------
# Cohort benchmarks
# ---------------------------------------------------------------------------

def get_cohort_benchmarks(db: sqlite3.Connection, merchant_id: str) -> list[dict]:
    """Return cohort-level stats for a merchant grouped by cohort dimensions."""
    return _rows_to_dicts(
        db.execute(
            """
            SELECT
                category,
                price_band,
                payment_mode,
                origin_node,
                destination_cluster,
                COUNT(*) AS order_count,
                AVG(CASE WHEN delivery_outcome = 'delivered' THEN 1.0 ELSE 0.0 END) AS delivery_rate
            FROM orders
            WHERE merchant_id = ?
            GROUP BY category, price_band, payment_mode, origin_node, destination_cluster
            """,
            (merchant_id,),
        )
    )


# ---------------------------------------------------------------------------
# Peer benchmarks
# ---------------------------------------------------------------------------

def get_peer_benchmarks(
    db: sqlite3.Connection,
    merchant_id: str,
    category: str,
    price_band: str,
) -> list[dict]:
    """Compare merchant's cohort performance against peers in same category/price_band."""
    return _rows_to_dicts(
        db.execute(
            """
            WITH merchant_cohorts AS (
                SELECT
                    category || '|' || price_band || '|' || payment_mode
                        || '|' || origin_node || '|' || destination_cluster AS cohort_key,
                    AVG(CASE WHEN delivery_outcome = 'delivered' THEN 1.0 ELSE 0.0 END) AS merchant_score
                FROM orders
                WHERE merchant_id = ?
                  AND category = ?
                  AND price_band = ?
                GROUP BY cohort_key
            ),
            peer_cohorts AS (
                SELECT
                    category || '|' || price_band || '|' || payment_mode
                        || '|' || origin_node || '|' || destination_cluster AS cohort_key,
                    AVG(CASE WHEN delivery_outcome = 'delivered' THEN 1.0 ELSE 0.0 END) AS peer_avg_score,
                    COUNT(*) AS peer_sample_size
                FROM orders
                WHERE merchant_id != ?
                  AND category = ?
                  AND price_band = ?
                GROUP BY cohort_key
            )
            SELECT
                m.cohort_key,
                m.merchant_score,
                COALESCE(p.peer_avg_score, 0.0) AS peer_avg_score,
                COALESCE(p.peer_sample_size, 0) AS peer_sample_size,
                (m.merchant_score - COALESCE(p.peer_avg_score, 0.0)) AS gap
            FROM merchant_cohorts m
            LEFT JOIN peer_cohorts p ON m.cohort_key = p.cohort_key
            """,
            (merchant_id, category, price_band, merchant_id, category, price_band),
        )
    )


# ---------------------------------------------------------------------------
# Recent orders
# ---------------------------------------------------------------------------

def get_recent_orders(
    db: sqlite3.Connection, merchant_id: str, limit: int = 50
) -> list[dict]:
    """Return most recent orders for a merchant, sorted by created_at desc."""
    return _rows_to_dicts(
        db.execute(
            """
            SELECT *
            FROM orders
            WHERE merchant_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (merchant_id, limit),
        )
    )


# ---------------------------------------------------------------------------
# Historical analogs
# ---------------------------------------------------------------------------

def get_historical_analogs(
    db: sqlite3.Connection,
    category: str,
    price_band: str,
    payment_mode: str,
    origin_node: str,
    destination_cluster: str,
    min_orders: int = 50,
) -> dict:
    """Return historical stats for orders matching the given cohort dimensions."""
    row = _row_to_dict(
        db.execute(
            """
            SELECT
                COUNT(*) AS sample_size,
                AVG(CASE WHEN delivery_outcome != 'delivered' THEN 1.0 ELSE 0.0 END) AS rto_rate
            FROM orders
            WHERE category = ?
              AND price_band = ?
              AND payment_mode = ?
              AND origin_node = ?
              AND destination_cluster = ?
            """,
            (category, price_band, payment_mode, origin_node, destination_cluster),
        )
    )

    # Peer average RTO rate across all merchants for same category + price_band
    peer_row = _row_to_dict(
        db.execute(
            """
            SELECT
                AVG(CASE WHEN delivery_outcome != 'delivered' THEN 1.0 ELSE 0.0 END) AS peer_avg_rto_rate
            FROM orders
            WHERE category = ?
              AND price_band = ?
            """,
            (category, price_band),
        )
    )

    sample_size = (row or {}).get("sample_size", 0) or 0
    rto_rate = (row or {}).get("rto_rate", 0.0) or 0.0
    peer_avg_rto_rate = (peer_row or {}).get("peer_avg_rto_rate", 0.0) or 0.0

    return {
        "rto_rate": rto_rate if sample_size >= min_orders else None,
        "sample_size": sample_size,
        "peer_avg_rto_rate": peer_avg_rto_rate,
    }


# ---------------------------------------------------------------------------
# Intervention history & counts
# ---------------------------------------------------------------------------

def get_intervention_history(
    db: sqlite3.Connection, merchant_id: str, period_days: int = 30
) -> list[dict]:
    """Return intervention logs for a merchant within the given period."""
    cutoff = (datetime.utcnow() - timedelta(days=period_days)).isoformat()
    return _rows_to_dicts(
        db.execute(
            """
            SELECT *
            FROM interventions
            WHERE merchant_id = ?
              AND executed_at >= ?
            ORDER BY executed_at DESC
            """,
            (merchant_id, cutoff),
        )
    )


def get_intervention_counts(
    db: sqlite3.Connection, merchant_id: str, period_days: int = 30
) -> dict:
    """Return intervention counts grouped by type and outcome."""
    cutoff = (datetime.utcnow() - timedelta(days=period_days)).isoformat()

    by_type = _rows_to_dicts(
        db.execute(
            """
            SELECT intervention_type, COUNT(*) AS count
            FROM interventions
            WHERE merchant_id = ?
              AND executed_at >= ?
            GROUP BY intervention_type
            """,
            (merchant_id, cutoff),
        )
    )

    by_outcome = _rows_to_dicts(
        db.execute(
            """
            SELECT outcome, COUNT(*) AS count
            FROM interventions
            WHERE merchant_id = ?
              AND executed_at >= ?
              AND outcome IS NOT NULL
            GROUP BY outcome
            """,
            (merchant_id, cutoff),
        )
    )

    total = sum(r["count"] for r in by_type)

    return {
        "by_type": {r["intervention_type"]: r["count"] for r in by_type},
        "by_outcome": {r["outcome"]: r["count"] for r in by_outcome},
        "total": total,
    }


# ---------------------------------------------------------------------------
# Rate limits
# ---------------------------------------------------------------------------

def check_rate_limits(db: sqlite3.Connection, merchant_id: str) -> dict:
    """Check current intervention usage against daily and hourly caps."""
    now = datetime.utcnow()
    daily_cutoff = (now - timedelta(hours=24)).isoformat()
    hourly_cutoff = (now - timedelta(hours=1)).isoformat()

    daily_row = _row_to_dict(
        db.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM interventions
            WHERE merchant_id = ?
              AND executed_at >= ?
            """,
            (merchant_id, daily_cutoff),
        )
    )

    hourly_row = _row_to_dict(
        db.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM interventions
            WHERE merchant_id = ?
              AND executed_at >= ?
            """,
            (merchant_id, hourly_cutoff),
        )
    )

    # Get caps from merchant_permissions (use max across intervention types)
    caps_row = _row_to_dict(
        db.execute(
            """
            SELECT
                MAX(daily_cap) AS daily_cap,
                MAX(hourly_cap) AS hourly_cap
            FROM merchant_permissions
            WHERE merchant_id = ?
            """,
            (merchant_id,),
        )
    )

    daily_used = (daily_row or {}).get("cnt", 0) or 0
    hourly_used = (hourly_row or {}).get("cnt", 0) or 0
    daily_cap = (caps_row or {}).get("daily_cap", 500) or 500
    hourly_cap = (caps_row or {}).get("hourly_cap", 100) or 100

    return {
        "daily_used": daily_used,
        "daily_cap": daily_cap,
        "hourly_used": hourly_used,
        "hourly_cap": hourly_cap,
        "is_within_limits": daily_used < daily_cap and hourly_used < hourly_cap,
    }


# ---------------------------------------------------------------------------
# Log intervention
# ---------------------------------------------------------------------------

def log_intervention(db: sqlite3.Connection, intervention: dict) -> None:
    """Insert an intervention log entry."""
    db.execute(
        """
        INSERT INTO interventions (
            intervention_id, order_id, merchant_id, intervention_type,
            action_owner, initiated_by, confidence_score, outcome,
            executed_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            intervention["intervention_id"],
            intervention["order_id"],
            intervention["merchant_id"],
            intervention["intervention_type"],
            intervention["action_owner"],
            intervention["initiated_by"],
            intervention.get("confidence_score"),
            intervention.get("outcome"),
            intervention["executed_at"],
            intervention.get("completed_at"),
        ),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Merchant permissions
# ---------------------------------------------------------------------------

def get_merchant_permissions(db: sqlite3.Connection, merchant_id: str) -> dict:
    """Return merchant permissions including auto_cancel and express_upgrade config."""
    rows = _rows_to_dicts(
        db.execute(
            """
            SELECT *
            FROM merchant_permissions
            WHERE merchant_id = ?
            """,
            (merchant_id,),
        )
    )

    if not rows:
        return {
            "merchant_id": merchant_id,
            "permissions": {},
            "daily_cap": 500,
            "hourly_cap": 100,
            "auto_cancel_enabled": False,
            "auto_cancel_threshold": 0.9,
            "express_upgrade_enabled": False,
            "impulse_categories": ["fashion", "beauty"],
        }

    permissions: dict[str, bool] = {}
    daily_cap = 500
    hourly_cap = 100
    auto_cancel_enabled = False
    auto_cancel_threshold = 0.9
    express_upgrade_enabled = False
    impulse_categories: list[str] = ["fashion", "beauty"]

    for row in rows:
        itype = row["intervention_type"]
        permissions[itype] = bool(row["is_enabled"])
        # Take the max caps across all permission rows
        daily_cap = max(daily_cap, row.get("daily_cap") or 500)
        hourly_cap = max(hourly_cap, row.get("hourly_cap") or 100)
        # Auto-cancel config
        if row.get("auto_cancel_enabled"):
            auto_cancel_enabled = True
        if row.get("auto_cancel_threshold") is not None:
            auto_cancel_threshold = row["auto_cancel_threshold"]
        # Express upgrade config
        if row.get("express_upgrade_enabled"):
            express_upgrade_enabled = True
        # Impulse categories (comma-separated string)
        if row.get("impulse_categories"):
            impulse_categories = [
                c.strip() for c in row["impulse_categories"].split(",") if c.strip()
            ]

    return {
        "merchant_id": merchant_id,
        "permissions": permissions,
        "daily_cap": daily_cap,
        "hourly_cap": hourly_cap,
        "auto_cancel_enabled": auto_cancel_enabled,
        "auto_cancel_threshold": auto_cancel_threshold,
        "express_upgrade_enabled": express_upgrade_enabled,
        "impulse_categories": impulse_categories,
    }


# ---------------------------------------------------------------------------
# Customer delivered orders (first-time buyer check)
# ---------------------------------------------------------------------------

def get_customer_delivered_orders(
    db: sqlite3.Connection, customer_ucid: str, merchant_id: str
) -> list[dict]:
    """Return all delivered orders for a customer with a specific merchant."""
    return _rows_to_dicts(
        db.execute(
            """
            SELECT *
            FROM orders
            WHERE customer_ucid = ?
              AND merchant_id = ?
              AND delivery_outcome = 'delivered'
            ORDER BY created_at DESC
            """,
            (customer_ucid, merchant_id),
        )
    )


# ---------------------------------------------------------------------------
# Cluster RTO rate
# ---------------------------------------------------------------------------

def get_cluster_rto_rate(
    db: sqlite3.Connection, destination_cluster: str, payment_mode: str = "COD"
) -> float:
    """Return the RTO rate for a destination cluster filtered by payment mode."""
    row = _row_to_dict(
        db.execute(
            """
            SELECT
                AVG(CASE WHEN delivery_outcome != 'delivered' THEN 1.0 ELSE 0.0 END) AS rto_rate
            FROM orders
            WHERE destination_cluster = ?
              AND payment_mode = ?
            """,
            (destination_cluster, payment_mode),
        )
    )
    return (row or {}).get("rto_rate", 0.0) or 0.0
