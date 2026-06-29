import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'idcardmaker'),
        user=os.getenv('DB_USER', 'flakka'),
        password=os.getenv('DB_PASS', 'Psqlkayannyaenakeuy#9'),
        port=os.getenv('DB_PORT', '5432')
    )