import json
import re
import uuid
from datetime import datetime
from pathlib import Path


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_folder_name(name):
    value = re.sub(r'[<>:"/\\|?*]', "_", name).strip(" .")
    return value or "Новый проект"


class ProjectStore:
    def __init__(self, root_folder):
        self.root = Path(root_folder)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_projects(self):
        projects = []

        for project_file in self.root.glob("*/project.json"):
            try:
                data = json.loads(project_file.read_text(encoding="utf-8"))
                data["path"] = str(project_file.parent)
                projects.append(data)
            except (OSError, json.JSONDecodeError):
                continue

        projects.sort(
            key=lambda item: item.get("modified_at", ""),
            reverse=True
        )
        return projects

    def create_project(self, name, mode):
        name = name.strip()
        if not name:
            raise ValueError("Название проекта не может быть пустым.")

        if mode not in ("2D", "3D"):
            raise ValueError("Неизвестный режим проекта.")

        project_id = str(uuid.uuid4())
        folder_name = safe_folder_name(name)
        project_folder = self.root / folder_name

        counter = 2
        while project_folder.exists():
            project_folder = self.root / f"{folder_name} ({counter})"
            counter += 1

        project_folder.mkdir(parents=True)

        timestamp = now_iso()
        data = {
            "id": project_id,
            "name": name,
            "mode": mode,
            "created_at": timestamp,
            "modified_at": timestamp,
            "version": 1
        }

        (project_folder / "project.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )
        (project_folder / "code.py").write_text("", encoding="utf-8")

        return {**data, "path": str(project_folder)}

    def load_code(self, project):
        project_folder = Path(project["path"]).resolve()
        if project_folder.parent != self.root.resolve():
            raise ValueError("Путь проекта находится вне папки проектов.")

        code_file = project_folder / "code.py"
        if not code_file.is_file():
            return ""

        return code_file.read_text(encoding="utf-8")

    def save_code(self, project, code):
        project_folder = Path(project["path"]).resolve()
        if project_folder.parent != self.root.resolve():
            raise ValueError("Путь проекта находится вне папки проектов.")

        metadata_file = project_folder / "project.json"
        if not metadata_file.is_file():
            raise FileNotFoundError("Файл проекта не найден.")

        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        if data.get("id") != project.get("id"):
            raise ValueError("Идентификатор проекта не совпадает.")

        code_file = project_folder / "code.py"
        temporary_code = project_folder / "code.py.tmp"
        temporary_code.write_text(code, encoding="utf-8")
        temporary_code.replace(code_file)

        data["modified_at"] = now_iso()
        temporary_metadata = project_folder / "project.json.tmp"
        temporary_metadata.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )
        temporary_metadata.replace(metadata_file)

        project["modified_at"] = data["modified_at"]

    def delete_project(self, project):
        project_path = Path(project["path"]).resolve()
        root = self.root.resolve()

        if project_path.parent != root:
            raise ValueError("Путь проекта находится вне папки проектов.")

        metadata = project_path / "project.json"
        if not metadata.is_file():
            raise FileNotFoundError("Файл проекта не найден.")

        import shutil
        shutil.rmtree(project_path)
