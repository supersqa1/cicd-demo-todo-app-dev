import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
tasks_folder = 'tasks/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view_tasks')
def view_tasks():
    tasks = load_tasks()
    return render_template('view_tasks.html', tasks=tasks)

@app.route('/create_task')
def create_task():
    return render_template('create_task.html')

@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    description = request.form['description']
    save_task(title, description, 'todo')
    return redirect(url_for('view_tasks'))

@app.route('/delete/<filename>')
def delete(filename):
    delete_task(filename)
    return redirect(url_for('view_tasks'))

@app.route('/update_status/<filename>', methods=['POST'])
def update_status(filename):
    new_status = request.form['status']
    update_task_status(filename, new_status)
    return redirect(url_for('view_tasks'))

def load_tasks():
    tasks = []
    if not os.path.exists(tasks_folder):
        return tasks

    for filename in os.listdir(tasks_folder):
        filepath = os.path.join(tasks_folder, filename)
        with open(filepath, 'r') as file:
            lines = file.readlines()
            task = {
                'title': filename[:-4],  # Remove the file extension
                'description': lines[0].strip(),
                'status': lines[1].strip() if len(lines) > 1 else 'todo',
                'filename': filename
            }
            tasks.append(task)

    return tasks

def save_task(title, description, status):
    if not os.path.exists(tasks_folder):
        os.makedirs(tasks_folder)

    filename = f"{title}.txt"
    filepath = os.path.join(tasks_folder, filename)
    with open(filepath, 'w') as file:
        file.write(f"{description}\n{status}")

def delete_task(filename):
    filepath = os.path.join(tasks_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def update_task_status(filename, new_status):
    filepath = os.path.join(tasks_folder, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            lines = file.readlines()
        if len(lines) > 1:
            lines[1] = f"{new_status}\n"
        else:
            lines.append(f"{new_status}\n")
        with open(filepath, 'w') as file:
            file.writelines(lines)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5151)
