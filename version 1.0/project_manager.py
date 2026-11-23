
import sqlite3
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Project:
  id: int
  name: str
  code: str
  created_at: str
  updated_at: str


class ProjectManager:

  def __init__(self, folder):
    self.folder = Path(folder)
    self.folder.mkdir(parents=True, exist_ok=True)

    self.db_path = self.folder / "geometry_playground.db"

    self.connection = sqlite3.connect(self.db_path)
    self.connection.row_factory = sqlite3.Row

    self._initialize_database()

  def _initialize_database(self):

    self.connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    self.connection.commit()

  def get_all_projects(self):

    rows = self.connection.execute("""
            SELECT *
            FROM projects
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

    return [
        Project(
            id=row["id"],
            name=row["name"],
            code=row["code"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        for row in rows
    ]

  def get_project(self, project_id):

    row = self.connection.execute("""
            SELECT *
            FROM projects
            WHERE id = ?
        """, (project_id,)).fetchone()

    if row is None:
      return None

    return Project(
        id=row["id"],
        name=row["name"],
        code=row["code"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

  def create_project(self, name="Новый проект", code=""):

    cursor = self.connection.execute("""
            INSERT INTO projects (name, code)
            VALUES (?, ?)
        """, (name, code))

    self.connection.commit()

    return self.get_project(cursor.lastrowid)

  def update_project(self, project_id, code):

    self.connection.execute("""
            UPDATE projects
            SET code = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (code, project_id))

    self.connection.commit()

  def rename_project(self, project_id, new_name):

    new_name = new_name.strip()

    if not new_name:
      raise ValueError("Название проекта не может быть пустым")

    self.connection.execute("""
            UPDATE projects
            SET name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_name, project_id))

    self.connection.commit()

  def delete_project(self, project_id):

    self.connection.execute("""
            DELETE FROM projects
            WHERE id = ?
        """, (project_id,))

    self.connection.commit()

  def close(self):

    if self.connection:
      self.connection.close()
      self.connection = None
