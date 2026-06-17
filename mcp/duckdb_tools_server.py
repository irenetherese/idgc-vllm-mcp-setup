import json
import os
from pathlib import Path

import duckdb
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("duckdb-tools")

DUCKDB_PATH = os.environ["GAMING_DATA_ANALYTICS_DB_PATH"]

METADATA_PATH = Path(
    os.environ["GAMING_DATA_ANALYTICS_METADATA"]
)

METRICS_PATH = Path(
    os.environ["GAMING_DATA_ANALYTICS_METRICS"]
)


def load_metadata():

    if METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            return json.load(f)

    return {}


def load_metrics():

    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            return json.load(f)

    return {}


#
# Tables
#
@mcp.tool()
def list_tables():
    """
    List all tables in DuckDB.
    """

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:

        rows = con.execute(
            "SHOW TABLES"
        ).fetchall()

    return [r[0] for r in rows]


#
# Columns
#
@mcp.tool()
def list_columns():
    """
    List all columns for every table.
    """

    result = {}

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

            result[table] = [
                {
                    "column": col,
                    "type": dtype
                }
                for col, dtype, *_ in columns
            ]

    return result


#
# Table information
#
@mcp.tool()
def get_table_info(table: str):
    """
    Return metadata and columns of a table.

    Example:
        bets
        players
        wagers
    """

    metadata = load_metadata()

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:

        columns = con.execute(
            f"DESCRIBE {table}"
        ).fetchall()

    return {
        "table": table,
        "metadata": metadata.get("tables", {}).get(table, {}),
        "columns": [
            {
                "column": col,
                "type": dtype
            }
            for col, dtype, *_ in columns
        ]
    }


#
# Find business concepts, columns, tables, and metrics in database
#
@mcp.tool()
def search_schema(query: str):
    """
    Search business concepts, columns, tables, and metrics.

    Examples:
        Player
        League
        Wager
        Ticket
        GGR
        Turnover
    """

    metadata = load_metadata()
    metrics = load_metrics()

    query = query.lower()

    matches = []

    #
    # Search columns
    #
    for column, info in metadata.get("columns", {}).items():

        business_name = info.get(
            "business_name",
            ""
        )

        description = info.get(
            "description",
            ""
        )

        searchable_text = (
            f"{column} "
            f"{business_name} "
            f"{description}"
        ).lower()

        if query in searchable_text:

            matches.append(
                {
                    "type": "column",
                    "physical_name": column,
                    "business_name": business_name,
                    "description": description,
                    "tables": info.get("tables", [])
                }
            )

    #
    # Search tables
    #
    for table, info in metadata.get("tables", {}).items():

        business_name = info.get(
            "business_name",
            ""
        )

        description = info.get(
            "description",
            ""
        )

        searchable_text = (
            f"{table} "
            f"{business_name} "
            f"{description}"
        ).lower()

        if query in searchable_text:

            matches.append(
                {
                    "type": "table",
                    "physical_name": table,
                    "business_name": business_name,
                    "description": description
                }
            )

    #
    # Search metrics
    #
    for metric, info in metrics.items():

        business_name = info.get(
            "business_name",
            ""
        )

        description = info.get(
            "description",
            ""
        )

        formula = info.get(
            "formula",
            ""
        )

        searchable_text = (
            f"{metric} "
            f"{business_name} "
            f"{description} "
            f"{formula}"
        ).lower()

        if query in searchable_text:

            matches.append(
                {
                    "type": "metric",
                    "name": metric,
                    "business_name": business_name,
                    "description": description,
                    "formula": formula,
                    "columns": info.get("columns", [])
                }
            )

    return {
        "query": query,
        "matches": matches
    }


#
# Sample rows
#
@mcp.tool()
def sample_rows(
    table: str,
    limit: int = 5
):
    """
    Show sample rows.

    Example:
        bets
        players
    """

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:

        df = con.execute(
            f"""
            SELECT *
            FROM {table}
            LIMIT {limit}
            """
        ).fetchdf()

    return df.to_dict("records")


#
# Execute SQL
#
ALLOWED = (
    "SELECT",
    "WITH",
    "SHOW",
    "DESCRIBE",
    "EXPLAIN",
)


@mcp.tool()
def execute_sql(sql: str):
    """
    Execute read-only SQL.

    Always verify table names and columns before querying.

    Example:

    SELECT *
    FROM wagers
    LIMIT 10

    Example:

    SELECT
        Player_ID,
        SUM(Bet_Amount) AS Total_Wager
    FROM bets
    GROUP BY Player_ID
    """

    q = sql.strip().upper()

    if not q.startswith(ALLOWED):
        raise ValueError(
            "Only read-only queries are allowed."
        )

    with duckdb.connect(
        DUCKDB_PATH,
        read_only=True
    ) as con:

        df = con.execute(
            sql
        ).fetchdf()

    return df.to_dict(
        orient="records"
    )


if __name__ == "__main__":

    mcp.run(
        transport="streamable-http"
    )