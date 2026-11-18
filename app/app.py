import os

import mysql.connector
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "employee_user"),
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "employee_db"),
        connection_timeout=5,
    )


@app.get("/")
def index():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, name, role FROM employees ORDER BY id DESC"
        )
        employees = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template("index.html", employees=employees)


@app.post("/employees")
def add_employee():
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip()

    if not name or not role:
        return "Name and role are required", 400

    if len(name) > 100 or len(role) > 100:
        return "Name and role must not exceed 100 characters", 400

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO employees (name, role) VALUES (%s, %s)",
            (name, role),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("index"))


@app.post("/employees/<int:employee_id>/delete")
def delete_employee(employee_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM employees WHERE id = %s",
            (employee_id,),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("index"))


@app.get("/health")
def health():
    return jsonify(status="healthy")


@app.get("/ready")
def ready():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        cursor.fetchone()
        return jsonify(status="ready"), 200
    except mysql.connector.Error:
        return jsonify(status="not_ready"), 503
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
