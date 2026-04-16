import sqlite3

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

# safe helper
def add_column(sql):
    try:
        cursor.execute(sql)
    except Exception as e:
        print("Skipped:", e)

# ADD MISSING COLUMNS SAFELY
add_column("ALTER TABLE users ADD COLUMN last_daily INTEGER DEFAULT 0")
add_column("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
add_column("ALTER TABLE users ADD COLUMN last_redeem INTEGER DEFAULT 0")
add_column("ALTER TABLE users ADD COLUMN exchange_uid TEXT")
add_column("ALTER TABLE users ADD COLUMN last_message INTEGER DEFAULT 0")

conn.commit()
conn.close()

print("✅ Database updated safely!")s