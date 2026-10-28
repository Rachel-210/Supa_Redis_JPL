import os
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "postgres"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "12307729.ia."),
    "host": os.environ.get("DB_HOST", "db.jnochfkwqpgdbepavzft.supabase.co"),
    "port": os.environ.get("DB_PORT", "5432")
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

REDIS_URL = os.environ.get("REDIS_URL", "redis://default:n1exh7hldOTyll8O9xv5VD8iMouUx1KD@brumal-nautical-zebra-52847.db.redis.io:10654")

def get_redis_connection():
    r = redis.from_url(
        REDIS_URL,
        decode_responses=True 
    )
    return r