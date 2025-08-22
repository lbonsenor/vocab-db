from typing import Dict, List
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection
from psycopg2 import sql

import os
import dotenv

lang = ""

# --- Database Connection ---
def connect(language: str):
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

    global lang
    lang = language
    return connection


# --- Table Creation ---
def create_tables(conn: connection):
    queries = [
        sql.SQL("""
            CREATE SCHEMA IF NOT EXISTS {};
        """).format(sql.Identifier(lang)),

        sql.SQL("""
            CREATE TABLE IF NOT EXISTS public.upos_tags (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL
            );
        """),

        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.xpos_tags (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL
            );
        """).format(sql.Identifier(lang)),

        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.morphemes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                text TEXT NOT NULL,
                xpos_id TEXT REFERENCES {}.xpos_tags(id),
                translation TEXT
            );
        """).format(sql.Identifier(lang), sql.Identifier(lang)),

        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.words (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                text TEXT NOT NULL,
                upos_id TEXT REFERENCES public.upos_tags(id),
                translation TEXT
            );
        """).format(sql.Identifier(lang)),

        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.lemmas (
                word_id UUID REFERENCES {}.words(id),
                index BIGINT NOT NULL,
                morpheme_id UUID REFERENCES {}.morphemes(id),
                PRIMARY KEY (word_id, index)
            );
        """).format(sql.Identifier(lang), sql.Identifier(lang), sql.Identifier(lang)),
    ]

    cur = conn.cursor()
    for query in queries:
        cur.execute(query)
    conn.commit()
    print(f"All tables created successfully in the '{lang}' schema.")


# --- Get UPOS label ---
def get_upos(conn, tag: str) -> str:
    query = sql.SQL("SELECT label FROM public.upos_tags WHERE id = %s")
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (tag,))
        result = cur.fetchone()
        return result["label"].capitalize() if result else None


# --- Get or Prompt XPOS tags ---
def get_xpos(conn, tags: List[str]) -> List[str]:
    unique_ids = list(set(tags))
    found: Dict[str, str] = {}

    query = sql.SQL("SELECT id, label FROM {}.xpos_tags WHERE id = ANY(%s)").format(
        sql.Identifier(lang)
    )
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (unique_ids,))
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
        query = sql.SQL("INSERT INTO {}.xpos_tags (id, label) VALUES %s ON CONFLICT (id) DO NOTHING").format(
            sql.Identifier(lang)
        )
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, query.as_string(conn), new_entries)
        conn.commit()

    return result


# --- Get or Insert Morphemes ---
def get_morphemes(conn, morphemes: List[str], xpos_tags: List[str]):
    results = []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for text, xpos_id in zip(morphemes, xpos_tags):
            query = sql.SQL("""
                SELECT m.id, m.text, m.translation, x.label as xpos
                FROM {}.morphemes m
                JOIN {}.xpos_tags x ON m.xpos_id = x.id
                WHERE m.text = %s AND m.xpos_id = %s
            """).format(sql.Identifier(lang), sql.Identifier(lang))

            cur.execute(query, (text, xpos_id))
            row = cur.fetchone()

            if row:
                results.append(row)
            else:
                while True:
                    translation = input(f"Morpheme '{text}' with XPOS tag '{xpos_id}' not found. Enter translation: ").strip()
                    if translation:
                        break
                    print("Input cannot be empty. Try again.")

                query = sql.SQL("""
                    INSERT INTO {}.morphemes (text, xpos_id, translation)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """).format(sql.Identifier(lang))

                cur.execute(query, (text, xpos_id, translation))
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
        query = sql.SQL("SELECT translation FROM {}.words WHERE text = %s AND upos_id = %s").format(
            sql.Identifier(lang)
        )
        cur.execute(query, (text, upos_tag))
        row = cur.fetchone()

        if row:
            return row["translation"]
        else:
            while True:
                translation = input(f"Word '{text}' with UPOS tag '{upos_tag}' not found. Enter translation: ").strip()
                if translation:
                    break
                print("Input cannot be empty. Try again.")

            query = sql.SQL("""
                INSERT INTO {}.words (text, upos_id, translation)
                VALUES (%s, %s, %s)
                RETURNING id
            """).format(sql.Identifier(lang))
            cur.execute(query, (text, upos_tag, translation))
            word_id = cur.fetchone()["id"]

            lemmas = [(word_id, idx, m["id"]) for idx, m in enumerate(morphemes)]

            query = sql.SQL("""
                INSERT INTO {}.lemmas (word_id, index, morpheme_id)
                VALUES %s ON CONFLICT DO NOTHING
            """).format(sql.Identifier(lang))
            psycopg2.extras.execute_values(cur, query.as_string(conn), lemmas)

            conn.commit()
            return translation
