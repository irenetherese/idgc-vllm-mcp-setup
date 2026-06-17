import json
import os
import duckdb
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("duckdb-tools")

DUCKDB_PATH = os.environ["GAMING_DATA_ANALYTICS_DB_PATH"]
METADATA_PATH = Path(os.environ["GAMING_DATA_ANALYTICS_METADATA"])


def load_metadata():
    if METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            return json.load(f)

    return {}


#
# Metadata
#
@mcp.tool()
def get_metadata():
    """
    Return business metadata for tables and columns.
    """
    return load_metadata()


#
# Tables
#
@mcp.tool()
def list_tables():
    """
    List all tables in DuckDB.
    """
    with duckdb.connect(DUCKDB_PATH,read_only=True) as con:
        rows = con.execute("SHOW TABLES").fetchall()

    return [r[0] for r in rows]


#
# Schema
#
@mcp.tool()
def describe_table(table: str):
    """
    Describe columns of a table.
    """
    with duckdb.connect(DUCKDB_PATH,read_only=True) as con:
        rows = con.execute(
            f"DESCRIBE {table}"
        ).fetchall()

    return rows

@mcp.tool()
def search_tables(keyword: str):
    """
    Search tables by name.
    """

    keyword = keyword.lower()

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:
        tables = con.execute(
            "SHOW TABLES"
        ).fetchall()

    return [
        table
        for (table,) in tables
        if keyword in table.lower()
    ]


@mcp.tool()
def search_columns(keyword: str):
    """
    Search columns across all tables.
    """

    keyword = keyword.lower()

    matches = []

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:

        tables = con.execute(
            "SHOW TABLES"
        ).fetchall()

        for (table,) in tables:

            columns = con.execute(
                f"DESCRIBE {table}"
            ).fetchall()

            for col, dtype, *_ in columns:

                if keyword in col.lower():

                    matches.append(
                        {
                            "table": table,
                            "column": col,
                            "type": dtype,
                        }
                    )

    return matches

#
# Sample data
#
@mcp.tool()
def sample_rows(
    table: str,
    limit: int = 5
):
    """
    Show sample rows from a table.
    """
    with duckdb.connect(DUCKDB_PATH) as con:
        df = con.execute(
            f"""
            SELECT *
            FROM {table}
            LIMIT {limit}
            """
        ).fetchdf()

    return df.to_dict("records")


#
# Read-only SQL
#
ALLOWED = (
    "SELECT",
    "WITH",
    "SHOW",
    "DESCRIBE",
    "EXPLAIN",
)


@mcp.tool()
def run_query(query: str):
    """
    Execute read-only SQL.
    """

    q = query.strip().upper()

    if not q.startswith(ALLOWED):
        raise ValueError(
            "Only read-only queries are allowed."
        )

    with duckdb.connect(DUCKDB_PATH,read_only=True) as con:
        df = con.execute(query).fetchdf()

    return df.to_dict("records")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )