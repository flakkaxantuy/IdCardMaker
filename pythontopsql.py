import psycopg2

hostname = 'localhost'
database = 'idcardmaker'
username = 'flakka'
pwd = 'Psqlkayannyaenakeuy#9'
port_id = 5432
conn = None
cur = None

def get_db_connection():
    return psycopg2.connect(
            host = hostname,
            dbname = database,
            user = username,
            password = pwd,
            port = port_id)