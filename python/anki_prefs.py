import sqlite3
import pickle
import os
import json
import sys

home_dir = os.path.expanduser("~")
db_path = os.path.join(home_dir, ".local", "share", "Anki2", "prefs21.db")


def read_anki_prefs_db(db_path: str):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Connected to db: {db_path}")
        cursor.execute("SELECT name, data FROM profiles")
        rows = cursor.fetchall()
        return rows
        for _name, blob_data in rows:
            unpickled: dict = pickle.loads(blob_data)
            # print(json.dumps(unpickled, indent=2))
            # break
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except FileNotFoundError:
        print(f"Error: db file not found at {db_path}")
    except Exception as e:
        print(f"An unecpected error occorred: {e}")
    finally:
        if conn:
            conn.close()
            print("db connection closed")


if __name__ == "__main__" and not sys.flags.interactive:
    read_anki_prefs_db(db_path)
