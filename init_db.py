"""Create the ShopSphere tables (and optionally the sample products) in your MySQL database.

    python init_db.py            # create tables
    python init_db.py --seed     # create tables + insert the sample products

Uses the same DB_* settings as the app (.env locally, or exported variables).
Run it from your own computer against your Aiven database - it only needs to run once.
"""
import json
import os
import sys

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    options = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "charset": "utf8mb4",
        "connection_timeout": 15,
    }
    if os.getenv("DB_SSL_DISABLED", "false").lower() == "true":
        options["ssl_disabled"] = True

    db = mysql.connector.connect(**options)
    cursor = db.cursor()

    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as handle:
        statements = [s.strip() for s in handle.read().split(";") if s.strip()]
    for statement in statements:
        if not "".join(line for line in statement.splitlines() if not line.strip().startswith("--")).strip():
            continue
        cursor.execute(statement)
    db.commit()
    print(f"Tables ready ({len(statements)} statements).")

    if "--seed" in sys.argv:
        with open(os.path.join(BASE_DIR, "seed_items.json"), encoding="utf-8") as handle:
            items = json.load(handle)
        for item in items:
            cursor.execute(
                """
                INSERT IGNORE INTO items
                    (itemid, item_name, item_description, item_about, item_price,
                     item_quantity, item_category, item_filename, added_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s)
                """,
                (
                    bytes.fromhex(item["itemid"]),
                    item["item_name"],
                    item["item_description"],
                    item["item_about"],
                    item["item_price"],
                    item["item_quantity"],
                    item["item_category"],
                    item["item_filename"],
                    item["created_at"],
                ),
            )
        db.commit()
        print(f"Sample products inserted ({len(items)}).")

    cursor.close()
    db.close()


if __name__ == "__main__":
    main()
