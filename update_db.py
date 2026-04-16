import sqlite3

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

def add_column(sql):
    try:
        cursor.execute(sql)
        print("✅ Added:", sql)
    except Exception as e:
        print("⚠️ Skipped:", e)

# Add twitter column
add_column("ALTER TABLE users ADD COLUMN twitter_username TEXT")

conn.commit()
conn.close()

print("🎉 Database updated successfully!")