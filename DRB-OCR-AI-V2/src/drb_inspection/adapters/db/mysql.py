from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.models import DatabaseSettings


@dataclass
class MySqlConnection:
    settings: DatabaseSettings
    connection: object | None = None
    cursor: object | None = None

    def connect(self) -> None:
        import pymysql

        self.connection = pymysql.connect(
            host=self.settings.host,
            user=self.settings.user,
            password=self.settings.password,
            database=self.settings.database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=self.settings.autocommit,
        )
        self.cursor = self.connection.cursor()

    def execute(self, query: str, params=None) -> None:
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        self.cursor.execute(query, params or ())
        self.connection.commit()

    def fetchall(self):
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        return self.cursor.fetchall()

    def fetchone(self):
        if self.cursor is None:
            raise RuntimeError("Database cursor is not initialized.")
        return self.cursor.fetchone()

    def close(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None


@dataclass
class SqlTableGateway:
    connection: MySqlConnection
    table_name: str

    def get_all(self):
        self.connection.execute(f"SELECT * FROM {self.table_name}")
        return self.connection.fetchall()

    def get_by(self, column: str, value):
        self.connection.execute(f"SELECT * FROM {self.table_name} WHERE {column}=%s", (value,))
        return self.connection.fetchall()

    def get_columns_by(self, select_cols: list[str], where: dict):
        columns = ", ".join(select_cols)
        where_clause = " AND ".join(["%s=%%s" % key for key in where.keys()])
        self.connection.execute(
            f"SELECT {columns} FROM {self.table_name} WHERE {where_clause}",
            tuple(where.values()),
        )
        return self.connection.fetchall()

    def insert(self, data: dict) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        self.connection.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            tuple(data.values()),
        )

    def update(self, column: str, value, updates: dict) -> None:
        set_clause = ", ".join(["`%s`=%%s" % key for key in updates.keys()])
        params = list(updates.values()) + [value]
        self.connection.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE `{column}`=%s",
            tuple(params),
        )

    def insert_or_update(self, data: dict) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        updates = ", ".join(["%s=VALUES(%s)" % (key, key) for key in data.keys()])
        self.connection.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {updates}",
            tuple(data.values()),
        )

