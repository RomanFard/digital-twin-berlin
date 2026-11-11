import psycopg2
from psycopg2 import pool
from config import DB_HOST, DB_NAME, DB_USER, DB_POOL_MIN, DB_POOL_MAX

# Connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    DB_POOL_MIN, DB_POOL_MAX,
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER
)

def get_connection():
    return connection_pool.getconn()

def return_connection(conn):
    connection_pool.putconn(conn)