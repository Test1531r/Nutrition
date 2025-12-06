import sqlite3

conn = sqlite3.connect('nutrition.db')
c = conn.cursor()
c.execute("SELECT name, meal_type FROM foods")
for row in c.fetchall():
    print(row)
conn.close()
