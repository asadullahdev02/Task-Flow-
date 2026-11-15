"""
Automated Verification Suite for TaskFlow with Real Developed Projects
Verifies exact 3 projects, Jazeela Makeup Studio, Pending/In-Progress/Completed pipelines, and CustomTkinter UI.
"""

import os
import sys

from database import DatabaseManager
from models import Status, Priority, ProjectStatus, Project, Task


def test_real_projects_and_metrics():
    print("[1/3] Testing SQLite Real Projects, Jazeela Makeup Studio, and Status Synchronization...")
    db = DatabaseManager("taskflow.db")

    # 1. Verify exact 3 projects
    projects = db.get_all_projects()
    assert len(projects) == 3, f"Expected exactly 3 projects, got {len(projects)}"

    expected_projects = {
        "To-Do List App": ("Productivity", "Completed", "A task management application for organizing daily tasks."),
        "Jazeela Makeup Studio": ("Beauty & Business Website", "Completed", "A professional makeup studio website."),
        "TripVista": ("Travel & Tourism", "Completed", "A Pakistan-based travel booking website built with React.js and Tailwind CSS.")
    }

    for p in projects:
        assert p.name in expected_projects, f"Unexpected project found: {p.name}"
        exp_cat, exp_stat, exp_desc = expected_projects[p.name]
        assert p.category == exp_cat, f"Category mismatch for {p.name}: got {p.category}, expected {exp_cat}"
        assert p.status == exp_stat, f"Status mismatch for {p.name}: got {p.status}, expected {exp_stat}"
        assert p.description == exp_desc, f"Description mismatch for {p.name}: got {p.description}"
        assert p.progress_percentage == 100.0, f"Progress mismatch for {p.name}: got {p.progress_percentage}%"
        print(f"  [OK] Project '{p.name}' ({p.category}) verified as 100% Completed.")

    # 2. Verify Initial Dashboard Metrics
    m = db.get_dashboard_metrics()
    assert m["total_projects"] == 3, f"Expected 3 total projects, got {m['total_projects']}"
    assert m["completed_projects"] == 3, f"Expected 3 completed projects, got {m['completed_projects']}"
    assert m["pending_projects"] == 0, f"Expected 0 pending projects, got {m['pending_projects']}"
    assert m["in_progress_projects"] == 0, f"Expected 0 in-progress projects, got {m['in_progress_projects']}"
    assert m["completion_rate"] == 100.0, f"Expected 100% completion rate, got {m['completion_rate']}%"
    print("  [OK] Initial counts: Total=3, Completed=3, Pending=0, In Progress=0, Completion Rate=100.0%.")

    # 3. Test Adding a Future Project with Pending Status
    print("  -> Testing creation of future project with Pending status...")
    new_pid = db.create_project(
        name="Automated Inventory Portal",
        description="Warehouse management system",
        category="Operations",
        deadline=None,
        status=ProjectStatus.PENDING
    )
    assert new_pid > 0, "Failed to create new Pending project"
    
    # Verify Dashboard updates automatically based on SQLite project status
    m_after_pending = db.get_dashboard_metrics()
    assert m_after_pending["total_projects"] == 4, f"Expected 4 total projects, got {m_after_pending['total_projects']}"
    assert m_after_pending["completed_projects"] == 3, f"Expected 3 completed projects, got {m_after_pending['completed_projects']}"
    assert m_after_pending["pending_projects"] == 1, f"Expected 1 pending project, got {m_after_pending['pending_projects']}"
    assert m_after_pending["in_progress_projects"] == 0, f"Expected 0 in-progress projects, got {m_after_pending['in_progress_projects']}"
    print("  [OK] Dynamic Dashboard update verified: Total=4, Completed=3, Pending=1, In Progress=0.")

    # 4. Test Transitioning Status to In Progress
    db.update_project(
        project_id=new_pid,
        name="Automated Inventory Portal",
        description="Warehouse management system",
        category="Operations",
        deadline=None,
        status=ProjectStatus.IN_PROGRESS
    )
    m_after_progress = db.get_dashboard_metrics()
    assert m_after_progress["pending_projects"] == 0
    assert m_after_progress["in_progress_projects"] == 1
    print("  [OK] Transition to In Progress verified: Pending=0, In Progress=1.")

    # Clean up test project
    db.delete_project(new_pid)
    m_final = db.get_dashboard_metrics()
    assert m_final["total_projects"] == 3
    assert m_final["pending_projects"] == 0
    print("  [OK] Test project cleaned up. Portfolio restored to exact 3 completed projects.")

    # 5. Verify Idempotency (no duplicates on second initialization)
    db2 = DatabaseManager("taskflow.db")
    assert len(db2.get_all_projects()) == 3, "Duplication detected on database re-initialization!"
    print("  [OK] Idempotency verified: exactly 3 projects preserved without duplicates on restart.")


def test_ui_and_dialogs():
    print("[2/3] Testing CustomTkinter UI, Dashboard Cards, and Project Details...")
    from main import TaskFlowApp

    app = TaskFlowApp()
    app.withdraw()  # Headless test

    # Verify navigation and rendering across all 5 views
    for view in ["dashboard", "projects", "tasks", "deadlines", "about"]:
        app.navigate_to(view)
        app.update()
        print(f"  [OK] View '{view}' rendered successfully.")

    # Verify projects portfolio rendering
    app.navigate_to("projects")
    app._filter_projects_list()
    app.update()

    # Verify task filtering
    app.navigate_to("tasks")
    app._refresh_tasks_table()
    app.update()

    app.destroy()
    print("[3/3] UI and modal components passed cleanly.")


if __name__ == "__main__":
    print("=== TaskFlow Verification: Jazeela Makeup Studio & Pending Status Update ===")
    test_real_projects_and_metrics()
    test_ui_and_dialogs()
    print("=== All Verification Tests Passed Successfully! ===")
