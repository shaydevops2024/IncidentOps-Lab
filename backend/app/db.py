import psycopg2
from .config import DATABASE_URL

def get_conn():
    return psycopg2.connect(DATABASE_URL)
