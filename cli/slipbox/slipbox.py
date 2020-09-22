"""Sqlite database wrapper."""

from collections import namedtuple
from itertools import chain
from pathlib import Path
import sqlite3
import sys
from time import time
from typing import Iterable, Iterator, List, Tuple

from . import scan, page
from .data import warning
from .initializer import DotSlipbox
from .utils import sqlite_string, check_options

Notes = namedtuple("Notes", "added modified deleted")

class Slipbox:
    """Slipbox main functions."""
    def __init__(self, dot: DotSlipbox):
        self.conn = sqlite3.connect(dot.path/"data.db")
        self.dot = dot
        self.path = dot.parent
        self.config = dot.config
        if not check_options(self.config.get("slipbox", "content_options")):
            config_path = dot.path/"config.cfg"
            sys.exit(f"invalid content_options value in {config_path.resolve()!s}")

    @property
    def timestamp(self) -> float:
        """Get timestamp from Meta table."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Meta WHERE key = 'timestamp'")
        _, value = cur.fetchone()
        return value

    @timestamp.setter
    def timestamp(self, value: float) -> None:
        """Set timestamp in Meta table."""
        self.conn.execute("UPDATE Meta SET value = ? WHERE key = 'timestamp'", (value,))
        self.conn.commit()

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def __enter__(self) -> "Slipbox":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None: # type: ignore
        self.close()

    def find_notes(self) -> Notes:
        """Return a named tuple containing lists of new, modified and deleted notes."""
        return Notes(
            added=added_notes(self),
            modified=modified_notes(self),
            deleted=deleted_notes(self),
        )

    def suggest_edits(self, notes: Notes) -> Iterator[Tuple[int, str, Path]]:
        """Suggest notes to edit based on the given set of notes.

        The suggestion includes
        - notes that link to notes that have been modified/deleted
        - notes that define an alias for modified/deleted notes
        and excludes notes that have been deleted.
        """
        outdated = chain(notes.modified, notes.deleted)
        filenames = [sqlite_string(str(path)) for path in outdated]

        sql = """
            SELECT owner FROM Notes JOIN Aliases USING (id)
                WHERE filename IN ({})
        """.format(",".join(filenames))
        owners = self.conn.execute(sql)

        sql = """
            SELECT src FROM Notes JOIN Links ON id = dest
                WHERE filename IN ({})
        """.format(",".join(filenames))
        backlinks = self.conn.execute(sql)

        affected = (repr(nid) for nid, in chain(owners, backlinks))

        sql = """
            SELECT id, title, filename FROM Notes
                WHERE id IN ({}) ORDER BY id
        """.format(",".join(affected))

        for nid, title, filename in self.conn.execute(sql):
            path = Path(filename)
            if path not in notes.deleted:
                yield nid, title, path

    def purge(self, paths: Iterable[Path]) -> None:
        """Purge filenames from the database."""
        filenames = ((str(path),) for path in paths)
        cur = self.conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.executemany("DELETE FROM Files WHERE filename IN (?)", filenames)

    def process(self, paths: Iterable[Path]) -> None:
        """Process input files."""
        inputs = list(set(paths))
        for batch in scan.group_by_file_extension(inputs):
            scan.process_batch(self.conn, list(batch), self.config)
        self.timestamp = time()

    def compile(self) -> None:
        """Compile processed HTML into final output."""
        options = self.config.get("slipbox", "document_options")
        page.generate_complete_html(self.conn, options)

    def run(self) -> None:
        """Run all steps needed to compile output."""
        notes = self.find_notes()
        suggestions = list(self.suggest_edits(notes))
        self.purge(chain(notes.modified, notes.deleted))
        self.process(chain(notes.added, notes.modified))
        self.compile()
        if suggestions:
            warning(
                "The notes below are related to notes that have recently been updated.",
                "You might want to review them for inconsistent links.",
                *(f"  {nid}. {title} in {str(path)!r}."
                  for nid, title, path in suggestions)
            )

def added_notes(slipbox: Slipbox) -> List[Path]:
    """Return list of newly added notes."""
    patterns = slipbox.dot.patterns
    added = scan.find_new_files(slipbox.conn, [slipbox.path], patterns)
    return list(added)

def modified_notes(slipbox: Slipbox) -> List[Path]:
    """Return list of notes modified since the last scan."""
    files = scan.fetch_files(slipbox.conn)
    return [p for p in files if scan.is_recently_modified(slipbox.timestamp, p)]

def deleted_notes(slipbox: Slipbox) -> List[Path]:
    """Return list of notes that have been deleted from the file system."""
    files = scan.fetch_files(slipbox.conn)
    return [p for p in files if not p.exists()]