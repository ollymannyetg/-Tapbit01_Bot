import sqlite3

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")

conn.commit()
conn.close()

print("Done ✔️")