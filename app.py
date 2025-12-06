from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
import random
import json
import io
from xhtml2pdf import pisa

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'nutrition.db'

# --- قاعدة البيانات ---

def create_user_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_test_user():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (email, password)
        VALUES (?, ?)
    ''', ('admin@admin.com', '123456'))
    conn.commit()
    conn.close()

def create_plans_table():
    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            gender TEXT,
            weight REAL,
            height REAL,
            age INTEGER,
            total_calories REAL,
            plan_type TEXT,
            macros TEXT,
            meals TEXT
        )
    ''')
    conn.commit()
    conn.close()

# نفذها مرّة واحدة مع البداية
create_plans_table()

def create_food_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
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
    conn.commit()

    # بيانات افتراضية
    c.execute('SELECT COUNT(*) FROM foods')
    if c.fetchone()[0] == 0:
        data = [
            ('صدر دجاج مشوي', 165, 31, 0, 3.6, 'قطعة متوسطة', 100),
            ('بيض مسلوق', 78, 6.3, 0.6, 5.3, 'بيضة واحدة', 50),
            ('توست أسمر', 70, 3, 12, 1, 'شريحة', 30),
            ('رز أبيض مطبوخ', 130, 2.5, 28, 0.3, 'نصف كوب', 100),
            ('سلطة خضراء', 25, 1.2, 5, 0.2, 'طبق صغير', 100),
            ('تفاح', 52, 0.3, 14, 0.2, 'ثمرة متوسطة', 150),
            ('موز', 89, 1.1, 23, 0.3, 'ثمرة متوسطة', 120),
            ('زبادي قليل الدسم', 60, 5, 6, 1.5, 'علبة صغيرة', 125),
            ('شوفان مطبوخ', 150, 5, 27, 2.5, 'نصف كوب', 120),
            ('جبنة قريش', 98, 11, 3.4, 4.3, 'نصف كوب', 100),
        ]
        c.executemany('''
            INSERT INTO foods (name, calories, protein, carbs, fat, unit, grams_per_unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()

    conn.close()

create_user_table()
add_test_user()
create_food_table()

# --- دوال المساعدة ---

import pandas as pd
from flask import render_template, request, redirect, url_for, flash, session
import sqlite3

# معاينة البيانات قبل الحفظ
@app.route('/preview_foods', methods=['POST'])
def preview_foods():
    if 'excel_file' not in request.files:
        flash('❌ لم يتم رفع أي ملف!', 'danger')
        return redirect(url_for('foods_table'))

    file = request.files['excel_file']
    if file.filename == '':
        flash('❌ لم يتم اختيار ملف!', 'danger')
        return redirect(url_for('foods_table'))

    try:
        df = pd.read_excel(file)
        required_columns = ['name','calories','protein','carbs','fat','unit','grams_per_unit']
        if not all(col in df.columns for col in required_columns):
            flash('❌ ملف Excel غير صالح. تأكد من الأعمدة المطلوبة.', 'danger')
            return redirect(url_for('foods_table'))

        preview_data = []
        for _, row in df.iterrows():
            valid = True
            try:
                if pd.isnull(row['name']) or float(row['calories']) <= 0:
                    valid = False
            except:
                valid = False
            preview_data.append({
                'name': row.get('name', ''),
                'calories': row.get('calories', ''),
                'protein': row.get('protein', ''),
                'carbs': row.get('carbs', ''),
                'fat': row.get('fat', ''),
                'unit': row.get('unit', ''),
                'grams_per_unit': row.get('grams_per_unit', ''),
                'valid': valid
            })

        # حفظ البيانات مؤقتًا في session للاستيراد النهائي
        session['preview_foods'] = preview_data
        return render_template('preview_foods.html', foods=preview_data)

    except Exception as e:
        flash(f'❌ حدث خطأ أثناء المعاينة: {e}', 'danger')
        return redirect(url_for('foods_table'))

@app.route('/import_foods_final', methods=['POST'])
def import_foods_final():
    if 'preview_foods' not in session:
        flash('❌ لا توجد بيانات للاستيراد.', 'danger')
        return redirect(url_for('foods_table'))

    data = session.pop('preview_foods')
    added = 0
    skipped = 0
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for food in data:
        if food['valid']:
            try:
                c.execute('''
                    INSERT INTO foods (name, calories, protein, carbs, fat, unit, grams_per_unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    food['name'], float(food['calories']), float(food['protein']),
                    float(food['carbs']), float(food['fat']), food['unit'],
                    float(food['grams_per_unit'])
                ))
                added += 1
            except:
                skipped += 1
        else:
            skipped += 1
    conn.commit()
    conn.close()
    flash(f'✅ تم إضافة {added} صنف بنجاح، وتخطي {skipped} صنف غير صالح.', 'success')
    return redirect(url_for('foods_table'))



def get_foods():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT name, calories, protein, carbs, fat, unit, grams_per_unit FROM foods')
    rows = c.fetchall()
    conn.close()
    return [
        {
            'name': row[0],
            'calories': row[1],
            'protein': row[2],
            'carbs': row[3],
            'fat': row[4],
            'unit': row[5],
            'grams_per_unit': row[6],
        }
        for row in rows
    ]

def generate_day_plan(total_calories, preferred_foods, other_foods, meal_names):
    plan = {}
    meal_distribution = {
        "فطور": 0.3,
        "سناك 1": 0.1,
        "غداء": 0.3,
        "سناك 2": 0.1,
        "عشاء": 0.2
    }

    available_foods = preferred_foods + other_foods
    protein_rich = [f for f in available_foods if f['protein'] >= 10]
    carb_rich = [f for f in available_foods if f['carbs'] >= 10]
    fat_rich = [f for f in available_foods if f['fat'] >= 5]

    used_foods = set()

    def calculate_units(food, portion_cals):
        if food and food['calories'] > 0:
            return round(portion_cals / food['calories'], 1)
        return 0

    for meal in meal_names:
        meal_foods = []
        target_cals = total_calories * meal_distribution.get(meal, 0.2)

        if meal in ["فطور", "غداء", "عشاء"]:
            def pick_food(food_list):
                choices = [f for f in food_list if f['name'] not in used_foods]
                return random.choice(choices) if choices else None

            prot_food = pick_food(protein_rich)
            carb_food = pick_food(carb_rich)
            fat_food = pick_food(fat_rich)

            portion_cals = target_cals / 3

            for food in [prot_food, carb_food, fat_food]:
                if food:
                    units = calculate_units(food, portion_cals)
                    meal_foods.append({
                        'name': food['name'],
                        'unit': food['unit'],
                        'units': units,
                        'grams': round(food['grams_per_unit'] * units, 1),
                        'calories': round(food['calories'] * units, 1),
                    })
                    used_foods.add(food['name'])

        else:
            snacks_candidates = [f for f in available_foods if f['name'] not in used_foods] or available_foods
            random.shuffle(snacks_candidates)
            max_foods = random.choice([1, 2])
            portion_cals = target_cals / max_foods

            for food in snacks_candidates[:max_foods]:
                units = calculate_units(food, portion_cals)
                meal_foods.append({
                    'name': food['name'],
                    'unit': food['unit'],
                    'units': units,
                    'grams': round(food['grams_per_unit'] * units, 1),
                    'calories': round(food['calories'] * units, 1),
                })
                used_foods.add(food['name'])

        plan[meal] = meal_foods

    return plan

# --- Routes ---

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    email = request.form.get('email')
    password = request.form.get('password')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='البريد أو كلمة المرور خاطئة')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/foods')
def foods_table():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM foods')
    foods = c.fetchall()
    conn.close()

    return render_template('foods_table.html', foods=foods)

@app.route('/foods/add', methods=['GET'])
def add_food():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('add_food.html')

@app.route('/foods/add', methods=['POST'])
def save_food():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form['name']
    calories = float(request.form['calories'])
    protein = float(request.form['protein'])
    carbs = float(request.form['carbs'])
    fat = float(request.form['fat'])
    unit = request.form['unit']
    grams_per_unit = float(request.form['grams_per_unit'])

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO foods (name, calories, protein, carbs, fat, unit, grams_per_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, calories, protein, carbs, fat, unit, grams_per_unit))
    conn.commit()
    conn.close()

    return redirect(url_for('foods_table'))

@app.route('/foods/edit/<int:food_id>', methods=['GET'])
def edit_food(food_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM foods WHERE id = ?', (food_id,))
    food = c.fetchone()
    conn.close()

    return render_template('edit_food.html', food=food)

@app.route('/foods/edit/<int:food_id>', methods=['POST'])
def update_food(food_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form['name']
    calories = float(request.form['calories'])
    protein = float(request.form['protein'])
    carbs = float(request.form['carbs'])
    fat = float(request.form['fat'])
    unit = request.form['unit']
    grams_per_unit = float(request.form['grams_per_unit'])

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('''
        UPDATE foods
        SET name=?, calories=?, protein=?, carbs=?, fat=?, unit=?, grams_per_unit=?
        WHERE id=?
    ''', (name, calories, protein, carbs, fat, unit, grams_per_unit, food_id))
    conn.commit()
    conn.close()

    return redirect(url_for('foods_table'))

@app.route('/foods/delete/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('DELETE FROM foods WHERE id = ?', (food_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('foods_table'))

@app.route('/plans')
def plans_table():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM plans')
    plans = c.fetchall()
    conn.close()

    return render_template('plans_table.html', plans=plans)

@app.route('/plans/add', methods=['GET'])
def add_plan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('add_plan.html')


@app.route('/plans/add', methods=['POST'])
def save_plan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form['description']
    total_calories = float(request.form['total_calories'])

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO plans (name, description, total_calories)
        VALUES (?, ?, ?)
    ''', (name, description, total_calories))
    conn.commit()
    conn.close()

    return redirect(url_for('plans_table'))

@app.route('/plans/edit/<int:plan_id>', methods=['GET'])
def edit_plan(plan_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM plans WHERE id = ?', (plan_id,))
    plan = c.fetchone()
    conn.close()

    return render_template('edit_plan.html', plan=plan)
@app.route('/plans/edit/<int:plan_id>', methods=['POST'])
def update_plan(plan_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form['description']
    total_calories = float(request.form['total_calories'])

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('''
        UPDATE plans
        SET name=?, description=?, total_calories=?
        WHERE id=?
    ''', (name, description, total_calories, plan_id))
    conn.commit()
    conn.close()

    return redirect(url_for('plans_table'))

@app.route('/plans/delete/<int:plan_id>', methods=['POST'])
def delete_plan(plan_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('nutrition.db')
    c = conn.cursor()
    c.execute('DELETE FROM plans WHERE id = ?', (plan_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('plans_table'))
@app.route('/plans/view/<int:plan_id>')
def view_plan(plan_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM plans WHERE id = ?', (plan_id,))
    plan_row = c.fetchone()
    conn.close()

    if plan_row:
        import json
        plan = dict(plan_row)
        plan['macros'] = json.loads(plan['macros'])
        plan['meals'] = json.loads(plan['meals'])
        return render_template('view_plan.html', plan=plan)
    else:
        return "الخطة غير موجودة", 404


@app.route('/calculate_form')
def calculate_form():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    foods = get_foods()
    return render_template('calculate_form.html', foods=foods)

@app.route('/calculate', methods=['POST'])
def calculate():
    if not session.get('logged_in'):
        return redirect(url_for('login'))



    patient_name = request.form.get('patient_name')
    gender = request.form['gender']
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    age = int(request.form['age'])
    activity = float(request.form['activity'])
    goal = request.form['goal']
    plan_type = request.form['plan_type']
    health_status = request.form.get('health_status')
    child_age = request.form.get('child_age')
    carb_ratio = request.form.get('carb_ratio')
    protein_ratio = request.form.get('protein_ratio')
    fat_ratio = request.form.get('fat_ratio')

    likes = request.form.getlist('likes')
    dislikes = request.form.getlist('dislikes')

    if 'child' in gender:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == 'male' else -161)

    total_calories = bmr * activity
    if goal == 'lose':
        total_calories -= 300
    elif goal == 'gain':
        total_calories += 300

    if carb_ratio and protein_ratio and fat_ratio:
        carb_ratio = float(carb_ratio) / 100
        protein_ratio = float(protein_ratio) / 100
        fat_ratio = float(fat_ratio) / 100
    else:
        carb_ratio, protein_ratio, fat_ratio = 0.5, 0.25, 0.25

    macros = {
        'carbs': round((total_calories * carb_ratio) / 4, 1),
        'protein': round((total_calories * protein_ratio) / 4, 1),
        'fat': round((total_calories * fat_ratio) / 9, 1),
        'carb_ratio': int(carb_ratio * 100),
        'protein_ratio': int(protein_ratio * 100),
        'fat_ratio': int(fat_ratio * 100),
    }

    foods = get_foods()
    foods = [f for f in foods if f['name'] not in dislikes]
    preferred_foods = [f for f in foods if f['name'] in likes]
    other_foods = [f for f in foods if f['name'] not in likes]

    meal_names = ["فطور", "سناك 1", "غداء", "سناك 2", "عشاء"]

    if plan_type == 'day':
        meals = generate_day_plan(total_calories, preferred_foods, other_foods, meal_names)

        # ✅ حفظ الخطة في قاعدة البيانات
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO plans (
                patient_name,
                gender,
                weight,
                height,
                age,
                total_calories,
                plan_type,
                macros,
                meals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_name,
            gender,
            weight,
            height,
            age,
            total_calories,
            plan_type,
            json.dumps(macros, ensure_ascii=False),
            json.dumps(meals, ensure_ascii=False)
        ))
        conn.commit()
        conn.close()

        return render_template('result.html',
                               patient_name=patient_name,
                               gender=gender,
                               weight=weight,
                               height=height,
                               age=age,
                               total_calories=int(total_calories),
                               meals=meals,
                               plan_type=plan_type,
                               macros=macros)
    else:
        weekly_plan = {}
        for i in range(1, 8):
            weekly_plan[i] = generate_day_plan(total_calories, preferred_foods, other_foods, meal_names)

        # ✅ حفظ الخطة الأسبوعية في قاعدة البيانات
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO plans (
                patient_name,
                gender,
                weight,
                height,
                age,
                total_calories,
                plan_type,
                macros,
                meals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_name,
            gender,
            weight,
            height,
            age,
            total_calories,
            plan_type,
            json.dumps(macros, ensure_ascii=False),
            json.dumps(weekly_plan, ensure_ascii=False)
        ))
        conn.commit()
        conn.close()

        return render_template('result.html',
                               patient_name=patient_name,
                               gender=gender,
                               weight=weight,
                               height=height,
                               age=age,
                               total_calories=int(total_calories),
                               weekly_plan=weekly_plan,
                               plan_type=plan_type,
                               macros=macros)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
