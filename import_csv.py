import sqlite3
import csv

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('nutrition.db')
c = conn.cursor()

# إنشاء الجدول إذا لم يكن موجودًا
c.execute('''
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        calories REAL,
        protein REAL,
        carbs REAL,
        fat REAL,
        unit TEXT,
        grams_per_unit REAL
    )
''')

# قراءة ملف CSV وإدخاله
with open('foods.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # تخطي السطر الأول (العناوين)

    for row in reader:
        name = row[0]
        calories = float(row[1])
        protein = float(row[2])
        carbs = float(row[3])
        fat = float(row[4])
        unit = row[5]
        grams_per_unit = float(row[6])

        c.execute('''
            INSERT INTO foods (name, calories, protein, carbs, fat, unit, grams_per_unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, calories, protein, carbs, fat, unit, grams_per_unit))

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("✅ تم استيراد الأطعمة بنجاح!")
