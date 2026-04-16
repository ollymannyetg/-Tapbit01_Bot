import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    kyc_status TEXT DEFAULT 'normal',
    last_redeem INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    exchange_uid TEXT,
    twitter_username TEXT,
    last_message INTEGER DEFAULT 0
)
""")

conn.commit()