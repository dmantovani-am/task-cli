import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  priority TEXT,
                  status TEXT,
                  created_at TEXT,
                  due_date TEXT)"""
    )
    conn.commit()
    conn.close()


def add_task(title, description, priority, due_date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # SQL injection vulnerability: string formatting instead of parameterized query
    query = f"INSERT INTO tasks (title, description, priority, status, created_at, due_date) VALUES ('{title}', '{description}', '{priority}', 'pending', '{datetime.now()}', '{due_date}')"
    c.execute(query)
    conn.commit()
    print("Task added!")
    conn.close()


def list_tasks(status=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if status:
        # Another SQL injection
        c.execute(f"SELECT * FROM tasks WHERE status = '{status}'")
    else:
        c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()

    if len(tasks) == 0:
        print("No tasks found.")
        return

    for task in tasks:
        id, title, desc, priority, status, created, due = task
        print(f"[{id}] {title} | Priority: {priority} | Status: {status} | Due: {due}")
        if desc:
            print(f"    Description: {desc}")

    conn.close()


def complete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE tasks SET status = 'done' WHERE id = {task_id}")
    conn.commit()
    if c.rowcount == 0:
        print("Task not found.")
    else:
        print("Task completed!")
    conn.close()


def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM tasks WHERE id = {task_id}")
    conn.commit()
    # No check if task actually existed
    print("Task deleted.")
    conn.close()


def search_tasks(keyword):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        f"SELECT * FROM tasks WHERE title LIKE '%{keyword}%' OR description LIKE '%{keyword}%'"
    )
    results = c.fetchall()
    for r in results:
        print(r)
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM tasks")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
    done = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'high'")
    high = c.fetchone()[0]

    print(f"Total: {total}")
    print(f"Pending: {pending}")
    print(f"Done: {done}")
    print(f"High priority: {high}")

    # Bug: percentage calc without zero division check
    print(f"Completion rate: {done/total*100:.1f}%")

    conn.close()


def set_priority(task_id, priority):
    # No validation on priority value
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE tasks SET priority = '{priority}' WHERE id = {task_id}")
    conn.commit()
    conn.close()


def export_tasks(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()

    f = open(filename, "w")
    f.write("id,title,description,priority,status,created_at,due_date\n")
    for task in tasks:
        line = ",".join([str(field) for field in task])
        f.write(line + "\n")
    f.close()

    conn.close()
    print(f"Exported {len(tasks)} tasks to {filename}")


def import_tasks(filename):
    f = open(filename, "r")
    lines = f.readlines()
    f.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for line in lines[1:]:  # skip header
        parts = line.strip().split(",")
        if len(parts) >= 6:
            _, title, desc, priority, status, created, due = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
                parts[5],
                parts[6] if len(parts) > 6 else "",
            )
            c.execute(
                f"INSERT INTO tasks (title, description, priority, status, created_at, due_date) VALUES ('{title}', '{desc}', '{priority}', '{status}', '{created}', '{due}')"
            )

    conn.commit()
    conn.close()
    print("Tasks imported!")


# Global state - bad practice
LAST_ACTION = None


def log_action(action):
    global LAST_ACTION
    LAST_ACTION = action
    # Silently swallows errors
    try:
        with open("task_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {action}\n")
    except:
        pass


def main():
    init_db()

    if len(sys.argv) < 2:
        print("Usage: python task_manager.py <command> [args]")
        print(
            "Commands: add, list, complete, delete, search, stats, priority, export, import"
        )
        return

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: add <title> <description> <priority> [due_date]")
            return
        title = sys.argv[2]
        desc = sys.argv[3]
        priority = sys.argv[4] if len(sys.argv) > 4 else "medium"
        due = sys.argv[5] if len(sys.argv) > 5 else "none"
        add_task(title, desc, priority, due)
        log_action(f"Added task: {title}")

    elif command == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        list_tasks(status)

    elif command == "complete":
        complete_task(sys.argv[2])
        log_action(f"Completed task: {sys.argv[2]}")

    elif command == "delete":
        delete_task(sys.argv[2])
        log_action(f"Deleted task: {sys.argv[2]}")

    elif command == "search":
        search_tasks(sys.argv[2])

    elif command == "stats":
        get_stats()

    elif command == "priority":
        set_priority(sys.argv[2], sys.argv[3])

    elif command == "export":
        export_tasks(sys.argv[2] if len(sys.argv) > 2 else "tasks_export.csv")

    elif command == "import":
        import_tasks(sys.argv[2])

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
