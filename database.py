"""
TaskFlow - Project Management System
SQLite Database Operations and Persistence Layer
"""

import sqlite3
import os
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from models import Project, Task, Status, Priority, ProjectStatus


DB_FILE = "taskflow.db"


class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        """Initialize SQLite database tables, ensure schema migrations, and sync real projects."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'General',
                    status TEXT DEFAULT 'Completed',
                    deadline TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Ensure 'status' column exists if upgrading an existing database
            cursor.execute("PRAGMA table_info(projects);")
            columns = [c[1] for c in cursor.fetchall()]
            if "status" not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'Completed';")

            # Tasks Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'To Do',
                    deadline TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
            """)
            conn.commit()

            # Clean up old demo sample projects if present
            cursor.execute("""
                DELETE FROM projects 
                WHERE name IN ('Executive Portal Redesign', 'Client Security Audit', 'Annual Operations Blueprint')
            """)
            conn.commit()

            # Rename any legacy project names to "Jazeela Makeup Studio"
            cursor.execute("""
                UPDATE projects 
                SET name = 'Jazeela Makeup Studio' 
                WHERE name IN ('Manzila Makeup Studio', 'Manzila', 'JazeeLa', 'Jazeela', 'Jazeela makeup studio')
            """)
            conn.commit()

            # Synchronize the 3 Real Developed Projects permanently without duplication
            self._sync_real_projects(cursor)
            conn.commit()

    def _sync_real_projects(self, cursor: sqlite3.Cursor):
        """
        Ensure the 3 real projects exist in the database with Completed status:
        1. To-Do List App
        2. Jazeela Makeup Studio
        3. TripVista
        Does NOT create duplicates on application restarts.
        """
        today = date.today()
        completion_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        # 3 Real Developed Projects
        real_projects = [
            {
                "name": "To-Do List App",
                "category": "Productivity",
                "status": ProjectStatus.COMPLETED,
                "description": "A task management application for organizing daily tasks.",
                "deadline": completion_date,
                "tasks": [
                    ("Task CRUD Architecture (Add, Edit, Delete)", "Engineered complete task lifecycle management.", Priority.HIGH),
                    ("Category & Priority Filtering", "Developed instant multi-criteria task filters.", Priority.MEDIUM),
                    ("Local Data Persistence", "Implemented permanent offline storage and state synchronization.", Priority.HIGH)
                ]
            },
            {
                "name": "Jazeela Makeup Studio",
                "category": "Beauty & Business Website",
                "status": ProjectStatus.COMPLETED,
                "description": "A professional makeup studio website.",
                "deadline": completion_date,
                "tasks": [
                    ("Service Catalog & Bridal Packages", "Curated full studio service directory and pricing tiers.", Priority.HIGH),
                    ("Appointment Booking Workflow", "Integrated direct client consultation and reservation channels.", Priority.MEDIUM),
                    ("High-Resolution Portfolio Gallery", "Designed responsive showcase featuring studio transformations.", Priority.MEDIUM)
                ]
            },
            {
                "name": "TripVista",
                "category": "Travel & Tourism",
                "status": ProjectStatus.COMPLETED,
                "description": "A Pakistan-based travel booking website built with React.js and Tailwind CSS.",
                "deadline": completion_date,
                "tasks": [
                    ("React.js Component Architecture", "Developed modular UI components for itinerary browsing.", Priority.HIGH),
                    ("Tailwind CSS Responsive Design", "Crafted mobile-optimized travel cards and hero banners.", Priority.HIGH),
                    ("Pakistani Destination Search Engine", "Built curated regional tourism catalogs and booking workflows.", Priority.MEDIUM)
                ]
            }
        ]

        for p_data in real_projects:
            # Check by exact name or previous names for Jazeela Makeup Studio
            if p_data["name"] == "Jazeela Makeup Studio":
                cursor.execute("SELECT id FROM projects WHERE name IN ('Jazeela Makeup Studio', 'Jazeela makeup studio', 'JazeeLa', 'Jazeela', 'Manzila Makeup Studio')")
            else:
                cursor.execute("SELECT id FROM projects WHERE name = ?", (p_data["name"],))
            
            row = cursor.fetchone()
            if row:
                proj_id = row["id"]
                # Keep fields synchronized
                cursor.execute("""
                    UPDATE projects 
                    SET name = ?, category = ?, description = ?, status = ?, deadline = ?
                    WHERE id = ?
                """, (p_data["name"], p_data["category"], p_data["description"], p_data["status"], p_data["deadline"], proj_id))
            else:
                # Insert project
                cursor.execute("""
                    INSERT INTO projects (name, description, category, status, deadline)
                    VALUES (?, ?, ?, ?, ?)
                """, (p_data["name"], p_data["description"], p_data["category"], p_data["status"], p_data["deadline"]))
                proj_id = cursor.lastrowid

            # Ensure associated deliverables exist and are marked Completed
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE project_id = ?", (proj_id,))
            t_count = cursor.fetchone()[0]
            if t_count == 0:
                for t_title, t_desc, t_pri in p_data["tasks"]:
                    cursor.execute("""
                        INSERT INTO tasks (project_id, title, description, priority, status, deadline)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (proj_id, t_title, t_desc, t_pri, Status.COMPLETED, completion_date))

    # ==========================================
    # PROJECT OPERATIONS
    # ==========================================
    def create_project(
        self,
        name: str,
        description: str,
        category: str,
        deadline: Optional[str],
        status: str = ProjectStatus.PENDING
    ) -> int:
        """Create a new project with Pending, In Progress, or Completed status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (name, description, category, status, deadline)
                VALUES (?, ?, ?, ?, ?)
            """, (name.strip(), description.strip(), category.strip(), status.strip(), deadline if deadline else None))
            conn.commit()
            return cursor.lastrowid

    def update_project(
        self,
        project_id: int,
        name: str,
        description: str,
        category: str,
        deadline: Optional[str],
        status: str = ProjectStatus.PENDING
    ):
        """Update an existing project's attributes and status."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE projects
                SET name = ?, description = ?, category = ?, status = ?, deadline = ?
                WHERE id = ?
            """, (name.strip(), description.strip(), category.strip(), status.strip(), deadline if deadline else None, project_id))
            conn.commit()

    def delete_project(self, project_id: int):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    def get_project(self, project_id: int) -> Optional[Project]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.*,
                    COUNT(t.id) as task_count,
                    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_task_count
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                name=row["name"],
                description=row["description"] or "",
                category=row["category"] or "General",
                status=row["status"] if "status" in row.keys() and row["status"] else ProjectStatus.PENDING,
                deadline=row["deadline"],
                created_at=row["created_at"],
                task_count=row["task_count"] or 0,
                completed_task_count=row["completed_task_count"] or 0
            )

    def get_all_projects(self, search: Optional[str] = None) -> List[Project]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.*,
                    COUNT(t.id) as task_count,
                    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_task_count
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
            """
            params = []
            if search:
                query += " WHERE p.name LIKE ? OR p.description LIKE ? OR p.category LIKE ? OR p.status LIKE ?"
                like_str = f"%{search.strip()}%"
                params.extend([like_str, like_str, like_str, like_str])
            query += " GROUP BY p.id ORDER BY p.id ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Project(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"] or "",
                    category=row["category"] or "General",
                    status=row["status"] if "status" in row.keys() and row["status"] else ProjectStatus.PENDING,
                    deadline=row["deadline"],
                    created_at=row["created_at"],
                    task_count=row["task_count"] or 0,
                    completed_task_count=row["completed_task_count"] or 0
                )
                for row in rows
            ]

    # ==========================================
    # TASK OPERATIONS
    # ==========================================
    def create_task(self, project_id: int, title: str, description: str, priority: str, status: str, deadline: Optional[str]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (project_id, title, description, priority, status, deadline)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, title.strip(), description.strip(), priority, status, deadline if deadline else None))
            conn.commit()
            return cursor.lastrowid

    def update_task(self, task_id: int, project_id: int, title: str, description: str, priority: str, status: str, deadline: Optional[str]):
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE tasks
                SET project_id = ?, title = ?, description = ?, priority = ?, status = ?, deadline = ?
                WHERE id = ?
            """, (project_id, title.strip(), description.strip(), priority, status, deadline if deadline else None, task_id))
            conn.commit()

    def update_task_status(self, task_id: int, new_status: str):
        with self.get_connection() as conn:
            conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            conn.commit()

    def delete_task(self, task_id: int):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    def get_task(self, task_id: int) -> Optional[Task]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, p.name as project_name
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE t.id = ?
            """, (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"] or "",
                priority=row["priority"],
                status=row["status"],
                deadline=row["deadline"],
                created_at=row["created_at"],
                project_name=row["project_name"]
            )

    def get_all_tasks(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        filter_type: Optional[str] = None,
        sort_by: str = "deadline"
    ) -> List[Task]:
        """Query tasks with filtering and sorting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT t.*, p.name as project_name
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE 1=1
            """
            params = []

            if project_id and project_id > 0:
                query += " AND t.project_id = ?"
                params.append(project_id)

            if status and status != "All":
                query += " AND t.status = ?"
                params.append(status)

            if priority and priority != "All":
                query += " AND t.priority = ?"
                params.append(priority)

            if search:
                query += " AND (t.title LIKE ? OR t.description LIKE ? OR p.name LIKE ?)"
                like_term = f"%{search.strip()}%"
                params.extend([like_term, like_term, like_term])

            today_str = date.today().strftime("%Y-%m-%d")
            next_week_str = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

            if filter_type == "overdue":
                query += f" AND t.status != '{Status.COMPLETED}' AND t.deadline IS NOT NULL AND t.deadline < ?"
                params.append(today_str)
            elif filter_type == "upcoming":
                query += f" AND t.status != '{Status.COMPLETED}' AND t.deadline IS NOT NULL AND t.deadline >= ? AND t.deadline <= ?"
                params.extend([today_str, next_week_str])

            # Sorting
            if sort_by == "deadline":
                query += " ORDER BY CASE WHEN t.deadline IS NULL THEN 1 ELSE 0 END, t.deadline ASC, t.id DESC"
            elif sort_by == "priority":
                query += """
                    ORDER BY CASE t.priority
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                        ELSE 4
                    END ASC, t.deadline ASC
                """
            elif sort_by == "status":
                query += """
                    ORDER BY CASE t.status
                        WHEN 'In Progress' THEN 1
                        WHEN 'To Do' THEN 2
                        WHEN 'Completed' THEN 3
                        ELSE 4
                    END ASC
                """
            elif sort_by == "newest":
                query += " ORDER BY t.id DESC"
            else:
                query += " ORDER BY t.id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Task(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    description=row["description"] or "",
                    priority=row["priority"],
                    status=row["status"],
                    deadline=row["deadline"],
                    created_at=row["created_at"],
                    project_name=row["project_name"]
                )
                for row in rows
            ]

    # ==========================================
    # DASHBOARD & ANALYTICS
    # ==========================================
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Compute summary metrics synchronized with SQLite in real time."""
        today_str = date.today().strftime("%Y-%m-%d")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Projects Status Breakdown
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_projects,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_projects,
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_projects
                FROM projects
            """)
            p_row = cursor.fetchone()
            total_projects = p_row["total_projects"] or 0
            completed_projects = p_row["completed_projects"] or 0
            in_progress_projects = p_row["in_progress_projects"] or 0
            pending_projects = p_row["pending_projects"] or 0

            # Tasks Breakdown
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN status = 'To Do' THEN 1 ELSE 0 END) as todo_tasks,
                    SUM(CASE WHEN status != 'Completed' AND deadline IS NOT NULL AND deadline < ? THEN 1 ELSE 0 END) as overdue_tasks
                FROM tasks
            """, (today_str,))
            t_row = cursor.fetchone()
            
            total_tasks = t_row["total_tasks"] or 0
            completed_tasks = t_row["completed_tasks"] or 0
            in_progress_tasks = t_row["in_progress_tasks"] or 0
            todo_tasks = t_row["todo_tasks"] or 0
            overdue_tasks = t_row["overdue_tasks"] or 0

            # Completion rate dynamically calculated from project completion
            completion_rate = round((completed_projects / total_projects * 100), 1) if total_projects > 0 else 0.0

            # All Projects
            projects = self.get_all_projects()

            # Urgent / Overdue Tasks
            cursor.execute("""
                SELECT t.*, p.name as project_name
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                WHERE t.status != 'Completed'
                ORDER BY 
                    CASE WHEN t.deadline IS NOT NULL AND t.deadline < ? THEN 0 ELSE 1 END,
                    CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
                    t.deadline ASC
                LIMIT 5
            """, (today_str,))
            urgent_rows = cursor.fetchall()
            urgent_tasks = [
                Task(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    description=r["description"] or "",
                    priority=r["priority"],
                    status=r["status"],
                    deadline=r["deadline"],
                    created_at=r["created_at"],
                    project_name=r["project_name"]
                )
                for r in urgent_rows
            ]

            return {
                "total_projects": total_projects,
                "completed_projects": completed_projects,
                "in_progress_projects": in_progress_projects,
                "pending_projects": pending_projects,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "todo_tasks": todo_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": completion_rate,
                "active_projects": projects,
                "urgent_tasks": urgent_tasks
            }
