from db import conn, cursor

cursor.execute("ALTER TABLE users ADD COLUMN exchange_uid TEXT")
conn.commit()

print("Done adding exchange_uid")