import sqlite3

conn = sqlite3.connect('foods.db')
c = conn.cursor()

# إنشاء جدول الأطعمة
c.execute('''
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    calories REAL NOT NULL,
    protein REAL NOT NULL,
    carbs REAL NOT NULL,
    fat REAL NOT NULL
)
''')

# بيانات أولية للأطعمة
foods_data = [
    ("صدر دجاج مشوي", 165, 31, 0, 3.6),
    ("رز أبيض مطبوخ", 130, 2.4, 28, 0.3),
    ("بيضة مسلوقة", 78, 6.3, 0.6, 5.3),
    ("شوفان", 389, 17, 66, 7),
]

# إدخال البيانات في الجدول
c.executemany('INSERT INTO foods (name, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?)', foods_data)

conn.commit()
conn.close()

print("قاعدة البيانات تم إنشاؤها وتعبئتها بنجاح.")
