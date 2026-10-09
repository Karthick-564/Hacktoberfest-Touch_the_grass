import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "field_guide.db"

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[Path] = None):
    """Initializes the SQLite database schema."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_km REAL NOT NULL DEFAULT 20.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS species (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id INTEGER NOT NULL,
            category TEXT NOT NULL DEFAULT 'birds',
            scientific_name TEXT NOT NULL,
            common_name TEXT NOT NULL,
            tamil_name TEXT,                             -- Tamil vernacular name from Wikidata
            observation_count INTEGER NOT NULL DEFAULT 0,
            rarity TEXT NOT NULL CHECK(rarity IN ('Everyday', 'Regular', 'Special find')),
            peak_months TEXT NOT NULL,                   -- JSON list of peak months derived from GBIF month facets
            summary TEXT NOT NULL,                       -- Wikipedia overview extract
            description_text TEXT NOT NULL,              -- Wikipedia 'Description' section (grounded truth)
            key_traits TEXT NOT NULL,                    -- JSON traits extracted strictly from description text
            local_fact TEXT NOT NULL,                    -- Grounded locality observation context
            image_url TEXT,                              -- Original remote image URL
            image_local_path TEXT,                       -- Local offline path (e.g. /static/images/...)
            FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE,
            UNIQUE(region_id, scientific_name)
        );

        CREATE TABLE IF NOT EXISTS user_collection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            photo_path TEXT,
            FOREIGN KEY (species_id) REFERENCES species(id) ON DELETE CASCADE,
            UNIQUE(species_id)
        );

        CREATE INDEX IF NOT EXISTS idx_species_region ON species(region_id);
        CREATE INDEX IF NOT EXISTS idx_species_category ON species(category);
        """)
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database schema initialized at {DB_PATH}")
