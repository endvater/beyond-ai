"""
Beyond AI — Shared Neo4j Connector

Zentrale Neo4j-Verbindung für alle Module.
Konfiguration via Umgebungsvariablen oder .env-Datei.
"""

import os
from contextlib import contextmanager

from neo4j import GraphDatabase


class Neo4jConnector:
    """Thread-safe Neo4j connector with session management."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str = "neo4j",
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    @contextmanager
    def session(self):
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()

    def execute(self, query: str, parameters: dict | None = None) -> list:
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def verify_connectivity(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
