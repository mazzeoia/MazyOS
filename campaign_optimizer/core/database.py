"""Local SQLite storage for Creative campaign optimizer."""
from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "campaign_optimizer"
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "creative_campaigns.db"
CLIENTS_DIR = ROOT / "clientes"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own_conn = conn is None
    conn = conn or get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            niche TEXT DEFAULT '',
            objective TEXT DEFAULT '',
            channels TEXT DEFAULT '',
            monthly_budget REAL DEFAULT 0,
            target_cpl REAL DEFAULT 0,
            waste_limit REAL DEFAULT 100,
            min_ctr REAL DEFAULT 0.8,
            max_frequency REAL DEFAULT 3.0,
            meta_account TEXT DEFAULT '',
            google_account TEXT DEFAULT '',
            links TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaign_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            source_file TEXT DEFAULT '',
            date TEXT NOT NULL,
            campaign TEXT NOT NULL,
            ad_group TEXT DEFAULT '',
            ad_name TEXT DEFAULT '',
            impressions INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            cpc REAL DEFAULT 0,
            cpm REAL DEFAULT 0,
            frequency REAL DEFAULT 0,
            spend REAL DEFAULT 0,
            leads INTEGER DEFAULT 0,
            cpl REAL DEFAULT 0,
            balance REAL DEFAULT NULL,
            raw_json TEXT DEFAULT '',
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            campaign TEXT NOT NULL,
            entity_level TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            action TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'dry-run',
            reason TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        );
        """
    )
    conn.commit()
    if own_conn:
        conn.close()


def slugify(value: str) -> str:
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return normalized or "cliente"


def ensure_client_folder(name: str) -> Path:
    folder = CLIENTS_DIR / slugify(name)
    for child in ["dados", "relatorios", "campanhas", "logs"]:
        (folder / child).mkdir(parents=True, exist_ok=True)
    return folder


def upsert_client(data: dict[str, Any]) -> int:
    init_db()
    ensure_client_folder(data["name"])
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM clients WHERE name = ?", (data["name"],)).fetchone()
        payload = {
            "name": data.get("name", "").strip(),
            "niche": data.get("niche", ""),
            "objective": data.get("objective", ""),
            "channels": data.get("channels", ""),
            "monthly_budget": float(data.get("monthly_budget") or 0),
            "target_cpl": float(data.get("target_cpl") or 0),
            "waste_limit": float(data.get("waste_limit") or 100),
            "min_ctr": float(data.get("min_ctr") or 0.8),
            "max_frequency": float(data.get("max_frequency") or 3.0),
            "meta_account": data.get("meta_account", ""),
            "google_account": data.get("google_account", ""),
            "links": data.get("links", ""),
            "notes": data.get("notes", ""),
        }
        if existing:
            conn.execute(
                """
                UPDATE clients SET niche=:niche, objective=:objective, channels=:channels,
                    monthly_budget=:monthly_budget, target_cpl=:target_cpl, waste_limit=:waste_limit,
                    min_ctr=:min_ctr, max_frequency=:max_frequency, meta_account=:meta_account,
                    google_account=:google_account, links=:links, notes=:notes,
                    updated_at=CURRENT_TIMESTAMP
                WHERE name=:name
                """,
                payload,
            )
            conn.commit()
            return int(existing["id"])
        cur = conn.execute(
            """
            INSERT INTO clients (name, niche, objective, channels, monthly_budget, target_cpl,
                waste_limit, min_ctr, max_frequency, meta_account, google_account, links, notes)
            VALUES (:name, :niche, :objective, :channels, :monthly_budget, :target_cpl,
                :waste_limit, :min_ctr, :max_frequency, :meta_account, :google_account, :links, :notes)
            """,
            payload,
        )
        conn.commit()
        return int(cur.lastrowid)


def list_clients() -> list[sqlite3.Row]:
    init_db()
    with get_connection() as conn:
        return conn.execute("SELECT * FROM clients ORDER BY name").fetchall()


def get_client(client_id: int) -> sqlite3.Row | None:
    init_db()
    with get_connection() as conn:
        return conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()


def insert_metrics(client_id: int, rows: list[dict[str, Any]]) -> int:
    init_db()
    if not rows:
        return 0
    fields = [
        "client_id", "platform", "source_file", "date", "campaign", "ad_group", "ad_name",
        "impressions", "reach", "clicks", "ctr", "cpc", "cpm", "frequency", "spend",
        "leads", "cpl", "balance", "raw_json",
    ]
    prepared = []
    for row in rows:
        item = {field: row.get(field) for field in fields}
        item["client_id"] = client_id
        prepared.append(item)
    placeholders = ", ".join([":" + f for f in fields])
    with get_connection() as conn:
        conn.executemany(
            f"INSERT INTO campaign_metrics ({', '.join(fields)}) VALUES ({placeholders})",
            prepared,
        )
        conn.commit()
    return len(prepared)


def replace_metrics_for_source(client_id: int, platform: str, source_file: str, rows: list[dict[str, Any]]) -> int:
    init_db()
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM campaign_metrics WHERE client_id = ? AND platform = ? AND source_file = ?",
            (client_id, platform, source_file),
        )
        conn.commit()
    return insert_metrics(client_id, rows)


def fetch_metrics(client_id: int | None = None, start: str | None = None, end: str | None = None):
    init_db()
    query = "SELECT m.*, c.name AS client_name, c.target_cpl, c.waste_limit, c.min_ctr, c.max_frequency FROM campaign_metrics m JOIN clients c ON c.id = m.client_id WHERE 1=1"
    params: list[Any] = []
    if client_id:
        query += " AND m.client_id = ?"
        params.append(client_id)
    if start:
        query += " AND m.date >= ?"
        params.append(start)
    if end:
        query += " AND m.date <= ?"
        params.append(end)
    query += " ORDER BY m.date DESC, m.platform, m.campaign"
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def log_action(action: dict[str, Any]) -> None:
    init_db()
    fields = ["client_id", "platform", "campaign", "entity_level", "entity_name", "rule_name", "action", "mode", "reason"]
    with get_connection() as conn:
        conn.execute(
            f"INSERT INTO action_logs ({', '.join(fields)}) VALUES ({', '.join(':'+f for f in fields)})",
            {field: action.get(field, "") for field in fields},
        )
        conn.commit()


def fetch_action_logs(client_id: int | None = None):
    init_db()
    query = "SELECT l.*, c.name AS client_name FROM action_logs l JOIN clients c ON c.id = l.client_id WHERE 1=1"
    params: list[Any] = []
    if client_id:
        query += " AND l.client_id = ?"
        params.append(client_id)
    query += " ORDER BY l.created_at DESC LIMIT 200"
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()
