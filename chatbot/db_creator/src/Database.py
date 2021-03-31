from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import sys


class Database:

    def __init__(self, name, pw):
        try:
            self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=(name, pw))
        except ServiceUnavailable:
            sys.exit("Database server not reachable!")

    def close(self):
        return self.driver.close()

    def write_query(self, query):
        with self.driver.session() as session:
            session.write_transaction(self._write_query, query.replace('\n', ' '))

    def read_query(self, query):
        with self.driver.session() as session:
            return session.read_transaction(self._read_query, query.replace('\n', ' '))

    def read_query_with_list(self, query, list_param):
        with self.driver.session() as session:
            return session.read_transaction(self._read_query_with_list, query.replace('\n', ' '), list_param)

    @staticmethod
    def _write_query(tx, query):
        tx.run(query)

    @staticmethod
    def _read_query(tx, query):
        result = tx.run(query)
        return result.values()

    @staticmethod
    def _read_query_with_list(tx, query, list_param):
        result = tx.run(query, list_param=list_param)
        return result.values()
