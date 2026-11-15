"""
TaskFlow Test Suite: Database Unit Tests & CustomTkinter UI Verification
"""

import os
import gc
import tempfile
import unittest
from database import DatabaseManager
from models import Status, Priority, ProjectStatus, Project, Task


class TaskFlowUnitTests(unittest.TestCase):
    def setUp(self):
        # Create temp db and immediately close the file handle so SQLite owns it
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = DatabaseManager(self.temp_db_path)

    def tearDown(self):
        del self.db
        gc.collect()
        try:
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except OSError:
            pass

    def test_database_integrity(self):
        """Verify SQLite PRAGMA integrity check returns OK."""
        self.assertTrue(self.db.check_integrity(), "Database integrity check failed.")

    def test_real_projects_initialized(self):
        """Verify baseline real projects are seeded accurately."""
        projects = self.db.get_all_projects()
        self.assertEqual(len(projects), 3, f"Expected 3 seeded projects, got {len(projects)}")
        project_names = [p.name for p in projects]
        self.assertIn("To-Do List App", project_names)
        self.assertIn("Jazeela Makeup Studio", project_names)
        self.assertIn("TripVista", project_names)

    def test_project_lifecycle_and_metrics(self):
        """Verify project creation, status transitions, and dynamic dashboard metrics."""
        m_initial = self.db.get_dashboard_metrics()
        self.assertEqual(m_initial["total_projects"], 3)
        self.assertEqual(m_initial["completed_projects"], 3)
        self.assertEqual(m_initial["pending_projects"], 0)

        # Create new Pending project
        pid = self.db.create_project(
            name="Cloud Sync Engine",
            description="Background synchronization agent",
            category="Infrastructure",
            deadline="2026-12-31",
            status=ProjectStatus.PENDING
        )
        self.assertGreater(pid, 0)

        m_pending = self.db.get_dashboard_metrics()
        self.assertEqual(m_pending["total_projects"], 4)
        self.assertEqual(m_pending["pending_projects"], 1)
        self.assertEqual(m_pending["completed_projects"], 3)

        # Transition to In Progress
        self.db.update_project(
            project_id=pid,
            name="Cloud Sync Engine",
            description="Background synchronization agent",
            category="Infrastructure",
            deadline="2026-12-31",
            status=ProjectStatus.IN_PROGRESS
        )
        m_prog = self.db.get_dashboard_metrics()
        self.assertEqual(m_prog["pending_projects"], 0)
        self.assertEqual(m_prog["in_progress_projects"], 1)

        # Delete project and verify cleanup
        self.db.delete_project(pid)
        m_final = self.db.get_dashboard_metrics()
        self.assertEqual(m_final["total_projects"], 3)

    def test_productivity_statistics(self):
        """Verify task productivity metrics calculation."""
        stats = self.db.get_productivity_stats()
        self.assertIn("priority_breakdown", stats)
        self.assertIn("category_breakdown", stats)
        self.assertIn("total_tasks", stats)
        self.assertIn("task_completion_rate", stats)
        self.assertIsInstance(stats["task_completion_rate"], float)

    def test_csv_and_json_exports(self):
        """Verify export to CSV and JSON generates valid, non-empty files."""
        temp_dir = tempfile.mkdtemp()
        try:
            csv_tasks = os.path.join(temp_dir, "tasks.csv")
            csv_projects = os.path.join(temp_dir, "projects.csv")
            json_db = os.path.join(temp_dir, "db.json")

            # Test exports
            self.assertTrue(self.db.export_tasks_to_csv(csv_tasks))
            self.assertTrue(self.db.export_projects_to_csv(csv_projects))
            self.assertTrue(self.db.export_database_to_json(json_db))

            # Verify files exist and have content
            self.assertGreater(os.path.getsize(csv_tasks), 50)
            self.assertGreater(os.path.getsize(csv_projects), 50)
            self.assertGreater(os.path.getsize(json_db), 100)
        finally:
            gc.collect()
            try:
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
            except OSError:
                pass

    def test_database_backup(self):
        """Verify SQLite hot backup functionality."""
        temp_dir = tempfile.mkdtemp()
        backup_file = os.path.join(temp_dir, "backup.db")
        try:
            self.assertTrue(self.db.backup_database(backup_file))
            self.assertTrue(os.path.exists(backup_file))
            self.assertGreater(os.path.getsize(backup_file), 0)

            # Check integrity of the backup database
            backup_db = DatabaseManager(backup_file)
            self.assertTrue(backup_db.check_integrity())
            del backup_db
            gc.collect()
        finally:
            try:
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rmdir(temp_dir)
            except OSError:
                pass


def run_ui_smoke_test():
    """Headless smoke test for CustomTkinter views."""
    print("Running CustomTkinter UI smoke test...")
    from main import TaskFlowApp

    app = TaskFlowApp()
    app.withdraw()  # Run headless

    for view in ["dashboard", "projects", "tasks", "deadlines", "about"]:
        app.navigate_to(view)
        app.update()

    app.destroy()
    print("CustomTkinter UI smoke test passed cleanly.")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TaskFlowUnitTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        run_ui_smoke_test()
        print("\n=== All TaskFlow Tests & Verifications Passed! ===")
    else:
        exit(1)
