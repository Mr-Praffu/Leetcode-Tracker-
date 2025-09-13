from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Create DB table if not exists ---
def init_db():
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            difficulty TEXT,
            notes TEXT,
            review_count INTEGER DEFAULT 0,
            last_reviewed TEXT,
            next_review TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- Home page ---
@app.route('/')
def index():
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT * FROM problems ORDER BY id DESC")
    problems = c.fetchall()
    conn.close()
    return render_template('index.html', problems=problems)
# --- Filter by Difficulty ---
@app.route('/filter/<level>')
def filter_difficulty(level):
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT * FROM problems WHERE difficulty = ? ORDER BY id DESC", (level,))
    problems = c.fetchall()
    conn.close()
    return render_template('index.html', problems=problems)

# --- Add problem ---
@app.route('/add', methods=['POST'])
def add_problem():
    title = request.form['title']
    link = request.form['link']
    difficulty = request.form['difficulty']
    notes = request.form['notes']
    now = datetime.now()
    next_review = now + timedelta(days=1)

    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("INSERT INTO problems (title, link, difficulty, notes, last_reviewed, next_review) VALUES (?, ?, ?, ?, ?, ?)",
              (title, link, difficulty, notes, now.strftime('%Y-%m-%d'), next_review.strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    return redirect('/')

# --- Mark as Reviewed ---
@app.route('/review/<int:id>', methods=['POST'])
def review_problem(id):
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()

    # Get current review count
    c.execute("SELECT review_count FROM problems WHERE id = ?", (id,))
    result = c.fetchone()
    if not result:
        return redirect('/')

    current_count = result[0]
    new_count = current_count + 1

    # Calculate next review date using spaced repetition logic
    intervals = [1, 3, 7, 14, 30]
    days = intervals[min(new_count, len(intervals)-1)]
    now = datetime.now()
    next_review = now + timedelta(days=days)

    # Update review count, last reviewed date, next review
    c.execute('''
        UPDATE problems
        SET review_count = ?, last_reviewed = ?, next_review = ?
        WHERE id = ?
    ''', (new_count, now.strftime('%Y-%m-%d'), next_review.strftime('%Y-%m-%d'), id))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:id>', methods=['POST'])
def delete_problem(id):
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("DELETE FROM problems WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_problem(id):
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        link = request.form['link']
        difficulty = request.form['difficulty']
        notes = request.form['notes']
        c.execute('''
            UPDATE problems
            SET title = ?, link = ?, difficulty = ?, notes = ?
            WHERE id = ?
        ''', (title, link, difficulty, notes, id))
        conn.commit()
        conn.close()
        return redirect('/')

    # GET method: show edit form
    c.execute("SELECT * FROM problems WHERE id = ?", (id,))
    problem = c.fetchone()
    conn.close()
    return render_template('edit.html', problem=problem)

@app.route('/stats')
def stats():
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT difficulty, COUNT(*) FROM problems GROUP BY difficulty")
    data = c.fetchall()
    conn.close()

    labels = [row[0] for row in data]
    counts = [row[1] for row in data]
    return render_template('stats.html', labels=labels, counts=counts)


@app.route('/due-today')
def due_today():
    today = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT * FROM problems WHERE next_review = ?", (today,))
    due_problems = c.fetchall()
    conn.close()

    return render_template('due_today.html', due_problems=due_problems, today=today)

@app.route('/review-trend')
def review_trend():
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT last_reviewed, COUNT(*) FROM problems GROUP BY last_reviewed ORDER BY last_reviewed")
    data = c.fetchall()
    conn.close()

    dates = [row[0] for row in data]
    counts = [row[1] for row in data]

    return render_template('review_trend.html', dates=dates, counts=counts)

import csv
from flask import Response

@app.route('/export')
def export_csv():
    conn = sqlite3.connect('leetcode.db')
    c = conn.cursor()
    c.execute("SELECT * FROM problems")
    data = c.fetchall()
    conn.close()

    def generate():
        yield 'ID,Title,Link,Difficulty,Notes,Review_Count,Last_Reviewed,Next_Review\n'
        for row in data:
            csv_row = ','.join([f'"{str(item).replace(",", " ")}"' for item in row])
            yield f'{csv_row}\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=leetcode_export.csv"})



# --- Run ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)

   

    
