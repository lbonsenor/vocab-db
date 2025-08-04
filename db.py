from typing import Dict, List
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection

import os
import dotenv


# --- Database Connection ---
def connect():
    # Fetch variables
    USER = os.environ.get("user")
    PASSWORD = os.environ.get("password")
    HOST = os.environ.get("host")
    PORT = os.environ.get("port")
    DBNAME = os.environ.get("dbname")

    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")

    return connection


# --- Table Creation ---
def create_tables(conn: connection):
    queries = [
        # POS tag tables
        """
        CREATE TABLE IF NOT EXISTS public.upos_tags (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS public.xpos_tags (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL
        );
        """,

        # morphemes
        """
        CREATE TABLE IF NOT EXISTS public.morphemes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            text TEXT NOT NULL,
            xpos_id TEXT REFERENCES public.xpos_tags(id),
            translation TEXT
        );
        """,

        # words
        """
        CREATE TABLE IF NOT EXISTS public.words (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            text TEXT NOT NULL,
            upos_id TEXT REFERENCES public.upos_tags(id),
            translation TEXT
        );
        """,

        # lemmas (junction table)
        """
        CREATE TABLE IF NOT EXISTS public.lemmas (
            word_id UUID REFERENCES public.words(id),
            index BIGINT NOT NULL,
            morpheme_id UUID REFERENCES public.morphemes(id),
            PRIMARY KEY (word_id, index)
        );
        """
    ]

    for query in queries:
        conn.cursor().execute(query)
    
    conn.commit()
    print("All tables created succesfully in the 'public' schema.")

# --- Get UPOS label ---
def get_upos(conn, tag: str) -> str:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT label FROM public.upos_tags WHERE id = %s", (tag,))
        result = cur.fetchone()
        return result["label"].capitalize() if result else None

# --- Get or Prompt XPOS tags ---
def get_xpos(conn, tags: List[str]) -> List[str]:
    unique_ids = list(set(tags))
    found: Dict[str, str] = {}

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, label FROM public.xpos_tags WHERE id = ANY(%s)",
            (unique_ids,)
        )
        for row in cur.fetchall():
            found[row["id"]] = row["label"]

    result = []
    new_entries = []

    for tag in tags:
        if tag in found:
            result.append(found[tag])
        else:
            while True:
                label = input(f"XPOS tag '{tag}' not found. Please enter a label for it: ").strip()
                if label:
                    break
                print("Input cannot be empty or whitespace. Try again.")

            found[tag] = label
            result.append(label)
            new_entries.append((tag, label))

    if new_entries:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO public.xpos_tags (id, label) VALUES %s ON CONFLICT (id) DO NOTHING",
                new_entries
            )
        conn.commit()

    return result

# --- Get or Insert Morphemes ---
def get_morphemes(conn, morphemes: List[str], xpos_tags: List[str]):
    results = []

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for text, xpos_id in zip(morphemes, xpos_tags):
            cur.execute("""
                SELECT m.id, m.text, m.translation, x.label as xpos
                FROM public.morphemes m
                JOIN public.xpos_tags x ON m.xpos_id = x.id
                WHERE m.text = %s AND m.xpos_id = %s
            """, (text, xpos_id))
            row = cur.fetchone()

            if row:
                results.append(row)
            else:
                while True:
                    translation = input(f"Morpheme '{text}' with XPOS tag '{xpos_id}' not found. Enter translation: ").strip()
                    if translation:
                        break
                    print("Input cannot be empty. Try again.")

                cur.execute("""
                    INSERT INTO public.morphemes (text, xpos_id, translation)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (text, xpos_id, translation))
                morpheme_id = cur.fetchone()["id"]
                conn.commit()

                results.append({
                    "id": morpheme_id,
                    "text": text,
                    "xpos": xpos_id,
                    "translation": translation
                })

    return results

# --- Get or Insert Word and Lemmas ---
def get_translation(conn, text: str, upos_tag: str, morphemes: List[Dict]):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT translation FROM public.words
            WHERE text = %s AND upos_id = %s
        """, (text, upos_tag))
        row = cur.fetchone()

        if row:
            return row["translation"]
        else:
            while True:
                translation = input(f"Word '{text}' with UPOS tag '{upos_tag}' not found. Enter translation: ").strip()
                if translation:
                    break
                print("Input cannot be empty. Try again.")

            cur.execute("""
                INSERT INTO public.words (text, upos_id, translation)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (text, upos_tag, translation))
            word_id = cur.fetchone()["id"]

            lemmas = [(word_id, idx, m["id"]) for idx, m in enumerate(morphemes)]

            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO public.lemmas (word_id, index, morpheme_id)
                VALUES %s ON CONFLICT DO NOTHING
                """,
                lemmas
            )

            conn.commit()
            return translation
