"""Initialize notes repository."""

from argparse import Namespace
from configparser import ConfigParser
from pathlib import Path
from shlex import quote
from sqlite3 import Connection, connect
from typing import List, Sequence, Optional

def initialize_database(conn: Connection) -> None:
    """Initialize database with schema.sql."""
    sql = Path(__file__).with_name("schema.sql").read_text()
    conn.executescript(sql)
    conn.commit()

def default_config() -> ConfigParser:
    """Create ConfigParser object with default options."""
    css = quote(str(Path(__file__).with_name("pandoc.css").resolve()))
    config = ConfigParser()
    config["slipbox"] = {
        "content_options": "--mathjax",
        "document_options": f"--mathjax -H {css}",
        "convert_to_data_url": "False",
    }
    return config

def initialize(parent: Path, args: Optional[Namespace] = None) -> None:
    """Create .slipbox directory if it doesn't exist.

    Initializes .slipbox/data.db, .slipbox/patterns and ./slipbox/config.cfg.
    """
    _slipbox = parent/".slipbox"
    if not _slipbox.exists():
        _slipbox.mkdir()
        database = _slipbox.joinpath("data.db")
        with connect(database) as conn:
            initialize_database(conn)
        config = default_config()
        if args is not None:
            config["slipbox"].update(vars(args))
        with open(_slipbox/"config.cfg", "w") as config_file:
            config.write(config_file)
        _slipbox.joinpath("patterns").write_text("*.md\n*.markdown\n")

class DotSlipbox:
    """Initialized .slipbox/ directory."""
    def __init__(self, parent: Path = Path()):
        initialize(parent)
        self.parent = parent
        self.path = parent/".slipbox"

    @property
    def patterns(self) -> List[str]:
        """Return list of glob patterns."""
        text = self.path.joinpath("patterns").read_text()
        return [pat for pat in text.split('\n') if pat]

    @patterns.setter
    def patterns(self, value: Sequence[str]) -> None:
        """Set glob patterns."""
        with self.path.joinpath("patterns").open("w") as file:
            for pattern in value:
                if pattern:
                    print(pattern, file=file)

    @property
    def config(self) -> ConfigParser:
        """Return ConfigParser object from .slipbox/config.cfg."""
        config = ConfigParser()
        config.read(self.path/"config.cfg")
        return config