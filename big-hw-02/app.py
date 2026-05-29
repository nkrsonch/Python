from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


DATA_PATH = Path(__file__).with_name("course_data.json")
HOST = "0.0.0.0"
PORT = 1337
VALID_HOMEWORKS = {"hw-01", "hw-02"}


@dataclass(frozen=True)
class Student:
    student_id: int
    name: str
    group_id: str
    scores: dict[str, float]
    credit_score: float


def load_students() -> list[Student]:
    with DATA_PATH.open(encoding="utf-8") as file:
        raw_students: list[dict[str, Any]] = json.load(file)

    students: list[Student] = []
    for raw_student in raw_students:
        students.append(
            Student(
                student_id=int(raw_student["student_id"]),
                name=str(raw_student["name"]),
                group_id=str(raw_student["group_id"]),
                scores={
                    "hw-01": float(raw_student["scores"]["hw-01"]),
                    "hw-02": float(raw_student["scores"]["hw-02"]),
                },
                credit_score=float(raw_student["credit_score"]),
            )
        )

    return students


STUDENTS = load_students()
STUDENTS_BY_ID = {student.student_id: student for student in STUDENTS}


def make_error(message: str, status_code: int) -> tuple[dict[str, str], int]:
    return {"error": message}, status_code


def get_group_students(group_id: str) -> list[Student]:
    return [student for student in STUDENTS if student.group_id == group_id]


def get_query_value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [""])
    return values[0].strip()


def is_valid_homework(hw_name: str) -> bool:
    return hw_name in VALID_HOMEWORKS


def calculate_mean_score(students: list[Student], hw_name: str) -> float:
    scores = [student.scores[hw_name] for student in students]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def calculate_mark(credit_score: float) -> int:
    if credit_score >= 50:
        return 5
    if credit_score >= 30:
        return 4
    if credit_score >= 1:
        return 3
    return 2


def build_course_table_html(hw_name: str, students: list[Student], group_id: str) -> str:
    body_rows = []
    for student in students:
        body_rows.append(
            "<tr>"
            f"<td>{student.student_id}</td>"
            f"<td>{student.name}</td>"
            f"<td>{student.group_id}</td>"
            f"<td>{student.scores[hw_name]}</td>"
            "</tr>"
        )

    rows_html = "".join(body_rows)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Course table</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #f5f5f5;
      color: #202020;
      margin: 24px;
    }}
    table {{
      border-collapse: collapse;
      background: #ffffff;
      width: 100%;
      max-width: 900px;
    }}
    th, td {{
      border: 1px solid #bfbfbf;
      padding: 8px 10px;
      text-align: left;
    }}
    th {{
      background: #e9e9e9;
    }}
  </style>
</head>
<body>
  <h1>Таблица по {hw_name}</h1>
  <p>Группа: {group_id}</p>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>ФИ</th>
        <th>Группа</th>
        <th>Баллы</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</body>
</html>"""


def handle_names() -> tuple[dict[str, list[str]], int]:
    return {"names": [student.name for student in STUDENTS]}, HTTPStatus.OK


def handle_homework_mean(hw_name: str) -> tuple[dict[str, float] | dict[str, str], int]:
    if not is_valid_homework(hw_name):
        return make_error("unknown homework", HTTPStatus.NOT_FOUND)

    return {"mean_score": calculate_mean_score(STUDENTS, hw_name)}, HTTPStatus.OK


def handle_group_homework_mean(
    hw_name: str,
    group_id: str,
) -> tuple[dict[str, float] | dict[str, str], int]:
    if not is_valid_homework(hw_name):
        return make_error("unknown homework", HTTPStatus.NOT_FOUND)

    group_students = get_group_students(group_id)
    if not group_students:
        return make_error("unknown group", HTTPStatus.NOT_FOUND)

    return {"mean_score": calculate_mean_score(group_students, hw_name)}, HTTPStatus.OK


def handle_mean_score_query(query: dict[str, list[str]]) -> tuple[dict[str, float] | dict[str, str], int]:
    hw_name = get_query_value(query, "hw_name")
    group_id = get_query_value(query, "group_id")

    if not hw_name or not group_id:
        return make_error("hw_name and group_id are required", HTTPStatus.BAD_REQUEST)

    return handle_group_homework_mean(hw_name, group_id)


def handle_mark(query: dict[str, list[str]]) -> tuple[dict[str, float | int] | dict[str, str], int]:
    student_id = get_query_value(query, "student_id")
    group_id = get_query_value(query, "group_id")

    if not student_id and not group_id:
        return make_error("student_id or group_id is required", HTTPStatus.BAD_REQUEST)

    if student_id and group_id:
        return make_error("use only one parameter", HTTPStatus.BAD_REQUEST)

    if student_id:
        if not student_id.isdigit():
            return make_error("student_id must be a number", HTTPStatus.BAD_REQUEST)

        student = STUDENTS_BY_ID.get(int(student_id))
        if student is None:
            return make_error("student not found", HTTPStatus.NOT_FOUND)

        return {"mark": calculate_mark(student.credit_score)}, HTTPStatus.OK

    group_students = get_group_students(group_id)
    if not group_students:
        return make_error("unknown group", HTTPStatus.NOT_FOUND)

    marks = [calculate_mark(student.credit_score) for student in group_students]
    return {"mean_mark": round(sum(marks) / len(marks), 2)}, HTTPStatus.OK


def handle_course_table(query: dict[str, list[str]]) -> tuple[str | dict[str, str], int, str]:
    hw_name = get_query_value(query, "hw_name")
    group_id = get_query_value(query, "group_id")

    if not hw_name:
        return make_error("hw_name is required", HTTPStatus.BAD_REQUEST)[0], HTTPStatus.BAD_REQUEST, "application/json; charset=utf-8"

    if not is_valid_homework(hw_name):
        return make_error("unknown homework", HTTPStatus.NOT_FOUND)[0], HTTPStatus.NOT_FOUND, "application/json; charset=utf-8"

    students = STUDENTS if not group_id else get_group_students(group_id)
    if group_id and not students:
        return make_error("unknown group", HTTPStatus.NOT_FOUND)[0], HTTPStatus.NOT_FOUND, "application/json; charset=utf-8"

    html = build_course_table_html(hw_name, students, group_id or "all")
    return html, HTTPStatus.OK, "text/html; charset=utf-8"


class CourseHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/") or "/"
        query = parse_qs(parsed_url.query)

        if path == "/names":
            payload, status_code = handle_names()
            self.send_json(payload, status_code)
            return

        if path == "/mean_score":
            payload, status_code = handle_mean_score_query(query)
            self.send_json(payload, status_code)
            return

        if path == "/mark":
            payload, status_code = handle_mark(query)
            self.send_json(payload, status_code)
            return

        if path == "/course_table":
            body, status_code, content_type = handle_course_table(query)
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(self.serialize_body(body))
            return

        path_parts = [part for part in path.split("/") if part]
        if len(path_parts) == 2 and path_parts[1] == "mean_score":
            payload, status_code = handle_homework_mean(path_parts[0])
            self.send_json(payload, status_code)
            return

        if len(path_parts) == 3 and path_parts[2] == "mean_score":
            payload, status_code = handle_group_homework_mean(path_parts[0], path_parts[1])
            self.send_json(payload, status_code)
            return

        self.send_json({"error": "unknown endpoint"}, HTTPStatus.NOT_FOUND)

    def send_json(self, payload: dict[str, Any], status_code: int) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.serialize_body(payload))

    @staticmethod
    def serialize_body(body: str | dict[str, Any]) -> bytes:
        if isinstance(body, str):
            return body.encode("utf-8")
        return json.dumps(body, ensure_ascii=False).encode("utf-8")

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    server = ThreadingHTTPServer((HOST, PORT), CourseHandler)
    print(f"Server is running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
