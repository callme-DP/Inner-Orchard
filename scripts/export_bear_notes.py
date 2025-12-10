#!/usr/bin/env python3
"""
Export Bear notes to Markdown with front matter, including clickable Bear/file links.

Usage examples:
  python scripts/export_bear_notes.py --tag system --output-dir output-system
  python scripts/export_bear_notes.py --ids 123,ABCDEF-UUID --output-dir output-test
  python scripts/export_bear_notes.py --since-days 1 --output-dir output-latest

Defaults assume Bear is installed at:
  DB:  ~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite
  Files: ~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import sqlite3
import sys
from typing import Dict, List, Optional


DEFAULT_DB = os.path.expanduser(
    "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"
)
DEFAULT_FILES_BASE = os.path.expanduser(
    "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
)
EPOCH = datetime.datetime(2001, 1, 1)


def apple_to_iso(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    return (EPOCH + datetime.timedelta(seconds=ts)).isoformat(timespec="seconds")


def fetch_note_lookup(conn: sqlite3.Connection) -> Dict[int, Dict[str, Optional[str]]]:
    lookup: Dict[int, Dict[str, Optional[str]]] = {}
    title_index: Dict[str, List[Dict[str, Optional[str]]]] = {}
    for r in conn.execute(
        "SELECT Z_PK, ZTITLE, ZUNIQUEIDENTIFIER FROM ZSFNOTE WHERE ZPERMANENTLYDELETED=0"
    ):
        pk, title, ident = r
        lookup[pk] = {"title": title, "identifier": ident}
        if title:
            title_index.setdefault(title, []).append({"title": title, "identifier": ident})
    return lookup, title_index


def fetch_tags(conn: sqlite3.Connection) -> Dict[int, str]:
    return {r["Z_PK"]: r["ZTITLE"] for r in conn.execute("SELECT Z_PK, ZTITLE FROM ZSFNOTETAG")}


def fetch_note_tags(conn: sqlite3.Connection, tags: Dict[int, str]) -> Dict[int, List[str]]:
    note_tags: Dict[int, List[str]] = {}
    for r in conn.execute("SELECT Z_5NOTES as note_pk, Z_13TAGS as tag_pk FROM Z_5TAGS"):
        if r["tag_pk"] in tags:
            note_tags.setdefault(r["note_pk"], []).append(tags[r["tag_pk"]])
    return note_tags


def fetch_backlinks(conn: sqlite3.Connection, note_lookup: Dict[int, Dict[str, Optional[str]]]):
    backlinks: Dict[int, List[Dict[str, Optional[str]]]] = {}
    for r in conn.execute("SELECT ZLINKINGTO, ZLINKEDBY FROM ZSFNOTEBACKLINK"):
        target, linker = r
        if target in note_lookup and linker in note_lookup:
            info = note_lookup[linker]
            backlinks.setdefault(target, []).append(
                {
                    "title": info["title"],
                    "identifier": info["identifier"],
                    "bear_link": f"bear://x-callback-url/open-note?id={info['identifier']}"
                    if info["identifier"]
                    else None,
                }
            )
    return backlinks


def fetch_attachments(conn: sqlite3.Connection, files_base: str) -> Dict[int, List[Dict[str, str]]]:
    attachments: Dict[int, List[Dict[str, str]]] = {}
    for r in conn.execute("SELECT ZNOTE, ZUNIQUEIDENTIFIER, ZFILENAME FROM ZSFNOTEFILE"):
        note_pk, uid, fname = r
        if note_pk is None or uid is None or fname is None:
            continue
        path = os.path.join(files_base, uid, fname)
        attachments.setdefault(note_pk, []).append(
            {"path": path, "file_link": f"file://{path}"}
        )
    return attachments


def resolve_forward_links(text: str, title_index: Dict[str, List[Dict[str, Optional[str]]]]):
    forward = []
    for t in re.findall(r"\[\[(.+?)\]\]", text or ""):
        matches = title_index.get(t, [])
        forward.append(
            {
                "title": t,
                "identifier": matches[0]["identifier"] if matches else None,
                "bear_link": f"bear://x-callback-url/open-note?id={matches[0]['identifier']}"
                if matches and matches[0]["identifier"]
                else None,
            }
        )
    return forward


def query_notes(
    conn: sqlite3.Connection,
    note_pks: List[int],
) -> List[sqlite3.Row]:
    placeholders = ",".join("?" for _ in note_pks)
    sql = f"""
        SELECT Z_PK, ZTITLE, ZTEXT, ZUNIQUEIDENTIFIER, ZCREATIONDATE, ZMODIFICATIONDATE,
               ZARCHIVED, ZPINNED, ZTRASHED, ZPERMANENTLYDELETED, ZTODOCOMPLETED,
               ZHASSOURCECODE, ZHASIMAGES, ZHASFILES, ZLASTEDITINGDEVICE, ZSUBTITLE
        FROM ZSFNOTE
        WHERE Z_PK IN ({placeholders}) AND ZPERMANENTLYDELETED = 0
    """
    return conn.execute(sql, note_pks).fetchall()


def select_note_pks(
    conn: sqlite3.Connection,
    tags_map: Dict[int, List[str]],
    tag_titles: Dict[int, str],
    tag_name: Optional[str],
    ids: Optional[List[str]],
    since_days: Optional[int],
) -> List[int]:
    pks: List[int] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        sql = f"SELECT Z_PK FROM ZSFNOTE WHERE ZPERMANENTLYDELETED=0 AND ZUNIQUEIDENTIFIER IN ({placeholders})"
        pks = [r[0] for r in conn.execute(sql, ids)]
    elif tag_name:
        target = {tag_name, f"#{tag_name}", f"/{tag_name}"}
        for note_pk, tag_list in tags_map.items():
            if any(t in target for t in tag_list):
                pks.append(note_pk)
    elif since_days is not None:
        since = datetime.datetime.now() - datetime.timedelta(days=since_days)
        since_apple = (since - EPOCH).total_seconds()
        sql = """
            SELECT Z_PK FROM ZSFNOTE
            WHERE ZPERMANENTLYDELETED=0 AND ZMODIFICATIONDATE >= ?
        """
        pks = [r[0] for r in conn.execute(sql, (since_apple,))]
    else:
        pks = [r[0] for r in conn.execute("SELECT Z_PK FROM ZSFNOTE WHERE ZPERMANENTLYDELETED=0")]
    return pks


def write_note(out_dir: pathlib.Path, note: sqlite3.Row, meta: Dict[str, object]):
    filename = f"note-{note['ZUNIQUEIDENTIFIER'] or note['Z_PK']}.md"
    out_path = out_dir / filename
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    content = "\n".join(lines) + "\n\n" + (note["ZTEXT"] or "")
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Export Bear notes to Markdown with links.")
    parser.add_argument("--tag", help="Filter by tag name (without #).")
    parser.add_argument("--ids", help="Comma-separated list of note identifiers.")
    parser.add_argument("--since-days", type=int, help="Export notes modified in the last N days.")
    parser.add_argument("--output-dir", default="output-export", help="Output directory.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to Bear database.sqlite.")
    parser.add_argument(
        "--attachments-dir",
        default=DEFAULT_FILES_BASE,
        help="Path to Bear 'Note Files' directory.",
    )
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = pathlib.Path(args.db_path)
    if not db_path.exists():
        sys.stderr.write(f"DB not found: {db_path}\n")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    note_lookup, title_index = fetch_note_lookup(conn)
    tag_titles = fetch_tags(conn)
    note_tags_map = fetch_note_tags(conn, tag_titles)
    backlinks_map = fetch_backlinks(conn, note_lookup)
    attachments_map = fetch_attachments(conn, args.attachments_dir)

    ids = [s.strip() for s in args.ids.split(",")] if args.ids else None
    note_pks = select_note_pks(conn, note_tags_map, tag_titles, args.tag, ids, args.since_days)
    if not note_pks:
        print("No notes found for given filters.")
        sys.exit(0)

    notes = query_notes(conn, note_pks)
    for note in notes:
        pk = note["Z_PK"]
        forward_links = resolve_forward_links(note["ZTEXT"] or "", title_index)
        meta = {
            "title": note["ZTITLE"],
            "subtitle": note["ZSUBTITLE"],
            "identifier": note["ZUNIQUEIDENTIFIER"],
            "creation_date": apple_to_iso(note["ZCREATIONDATE"]),
            "modification_date": apple_to_iso(note["ZMODIFICATIONDATE"]),
            "archived": bool(note["ZARCHIVED"]),
            "pinned": bool(note["ZPINNED"]),
            "trashed": bool(note["ZTRASHED"]),
            "todo_completed": bool(note["ZTODOCOMPLETED"]),
            "has_source_code": bool(note["ZHASSOURCECODE"]),
            "has_images": bool(note["ZHASIMAGES"]),
            "has_files": bool(note["ZHASFILES"]),
            "last_editing_device": note["ZLASTEDITINGDEVICE"],
            "tags": note_tags_map.get(pk, []),
            "backlinks": backlinks_map.get(pk, []),
            "forward_links": forward_links,
            "attachments": attachments_map.get(pk, []),
        }
        out_path = write_note(output_dir, note, meta)
        print(out_path)

    conn.close()


if __name__ == "__main__":
    main()
