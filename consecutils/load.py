"""A home for common data load nodes"""

import csv
import sqlite3

import pandas as pd

from consecutils.core import (
    Node,
    SQLConnectionNode,
    PandasSQLConnectionNode,
    SQLAlchemyConnectionNode,
    SQLDBAPIConnectionNode,
    SQLiteConnectionNode,
)
from consecutils.utils import st, pp
from consecutils.sql_utils import (
    TemporaryTable,
    SQLiteTemporaryTable,
    get_bulk_replace,
    get_bulk_insert,
    get_temp_table,
)


class LoggingLoader(Node):
    """Simple logging node"""
    def run(self, item):
        """Pretty print the item and then push"""
        print("---- %s ----" % self.name)
        pp(item)
        self.push(item)


# -------- Pandas Loaders


class DataFrameCSVLoader(Node):
    """Load data into a CSV from a Pandas DataFrame"""
    def begin(self):
        """Initialize state for CSV writing"""
        self.wrote_header = False

    def run(self, df, outfile, **kwargs):
        """Use Pandas to_csv to output a DataFrame"""

        if "header" not in kwargs:
            kwargs["header"] = not self.wrote_header
            if not self.wrote_header:
                self.wrote_header = True
        df.to_csv(outfile, **kwargs)
        self.push(df)

    def end(self):
        """Reset state in case the node gets reused"""
        self.wrote_header = False


class DataFrameExcelLoader(Node):
    """Load data into an Excel file from a Pandas DataFrame"""
    def run(self, df, outfile, **kwargs):
        """Use Pandas to_excel to output a DataFrame"""
        df.to_excel(outfile, **kwargs)
        self.push(df)


class DataFrameSQLLoader(PandasSQLConnectionNode):
    """Load data into a SQL db from a Pandas DataFrame"""
    def run(self, df, conn, table, **kwargs):
        """Use Pandas to_sql to output a DataFrame"""
        df.to_sql(table, conn, **kwargs)
        self.push(df)


class DataFrameSQLTempLoader(PandasSQLConnectionNode):
    """Load data into a SQL temp table from a Pandas DataFrame"""
    def run(self, df, conn, schema=None, **kwargs):
        """Use Pandas to_sql to output a DataFrame to a temporary table"""
        assert not isinstance(
            conn, sqlite3.Connection
        ), "sqlite3 connections not supported due to bug in Pandas' has_table()?"
        table = get_temp_table(conn, df, schema=schema, create=True)
        df.to_sql(table.name, conn, if_exists="append", **kwargs)
        self.push([table.name])


# -------- Row-based Loaders


class RowCSVLoader(Node):
    """Load data into a CSV using DictWriter"""
    def begin(self):
        """Initialize state for CSV writing"""
        self.writer = None

    def run(self, rows, outfile, **kwargs):
        """Use DictWriter to output dict rows to a CSV. Assumes outfile is an open
        file handle."""
        if not self.writer:
            self.writer = csv.DictWriter(outfile, fieldnames=rows[0].keys(), **kwargs)
            self.writer.writeheader()
        self.writer.writerows(rows)
        self.push(rows)

    def end(self):
        """Reset state in case the node gets reused"""
        self.writer = None


class RowSQLiteLoader(SQLiteConnectionNode):
    """Load date with a SQLite connection"""
    def run(self, rows, conn, table, cursor=None, **kwargs):
        """Form SQL statement and use bulk execute to write rows to table"""
        assert isinstance(rows[0], sqlite3.Row), "Only sqlite3.Row rows are supported"
        sql = get_bulk_replace(table, rows[0].keys(), dicts=False, value_string="?")
        if not cursor:
            cursor = conn.cursor()
        cursor.executemany(sql, rows)
        self.push(rows)


class RowSQLDBAPILoader(SQLDBAPIConnectionNode):
    """Load data with a DBAPI-based connection"""
    def run(self, rows, conn, table, cursor=None, **kwargs):
        """Form SQL statement and use bulk execute to write rows to table"""
        sql = get_bulk_replace(table, rows[0].keys())
        if not cursor:
            cursor = conn.cursor()
        cursor.executemany(sql, rows)
        self.push(rows)


class RowSQLAlchemyLoader(SQLAlchemyConnectionNode):
    """Load data with a SQLAlchemy connection"""
    def run(self, rows, conn, table, **kwargs):
        """Form SQL statement and use bulk execute to write rows to table"""
        sql = get_bulk_replace(table, rows[0].keys(), dicts=False)
        conn.execute(sql, rows)
        self.push(rows)


class RowSQLiteTempLoader(SQLiteConnectionNode):
    """Load data into a temp table with a SQLite connection"""
    def run(self, rows, conn, cursor=None, schema=None, **kwargs):
        """Create and bulk load a temp table"""
        assert isinstance(rows[0], sqlite3.Row), "Only sqlite3.Row rows are supported"
        table = get_temp_table(conn, rows, create=True, schema=schema)
        sql = get_bulk_replace(
            table.name, rows[0].keys(), dicts=False, value_string="?"
        )
        if not cursor:
            cursor = conn.cursor()
        cursor.executemany(sql, rows)
        self.push([table.name])


class RowSQLLoader(SQLConnectionNode):
    """Generic SQL loader"""

    def run(self, rows, conn, table, cursor=None, **kwargs):
        """Form SQL statement and use bulk execute to write rows to table"""
        sql = self.get_bulk_replace(conn, table, rows)
        if not cursor:
            cursor = self.get_sql_executor(conn)
        self.sql_executemany(conn, cursor, sql, rows)
        self.push(rows)


class RowSQLTempLoader(SQLConnectionNode):
    """Generic SQL temp table loader"""
    def run(self, rows, conn, cursor=None, schema=None, **kwargs):
        """Create and bulk load a temp table"""
        table = get_temp_table(conn, rows, create=True, schema=schema)
        sql = self.get_bulk_replace(conn, table.name, rows)
        if not cursor:
            cursor = self.get_sql_executor(conn)
        self.sql_executemany(conn, cursor, sql, rows)
        self.push([table.name])
