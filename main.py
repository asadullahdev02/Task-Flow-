"""
TaskFlow – Project Management System
Desktop Application built with Python 3, CustomTkinter, and SQLite.

Author: Antigravity
Theme: Burgundy, Charcoal & Subtle Beige (Strictly No Green, Teal or Neon)
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from typing import Optional, List, Callable

import customtkinter as ctk
from PIL import Image

from models import Theme, Status, Priority, ProjectStatus, Project, Task
from database import DatabaseManager


# Set CustomTkinter configuration
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")  # Explicitly overridden with Theme tokens


# ============================================================================
# REUSABLE CUSTOM DIALOGS & MODALS
# ============================================================================

class BaseModal(ctk.CTkToplevel):
    """Base modal dialog with consistent executive styling and centering."""
    def __init__(self, parent, title: str, width: int = 540, height: int = 600):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}{height}")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_ROOT)
        
        # Center dialog relative to parent
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - width) // 2
            y = py + (ph - height) // 2
            self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.result = None

    def _on_cancel(self):
        self.grab_release()
        self.destroy()


class ConfirmationDialog(BaseModal):
    """Confirmation modal for destructive operations."""
    def __init__(self, parent, title: str, message: str, confirm_label: str = "Delete"):
        super().__init__(parent, title, width=450, height=230)
        self.confirmed = False

        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12,
                                 border_width=1, border_color=Theme.CHARCOAL_BORDER)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = ctk.CTkLabel(
            container, text=title, font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        )
        title_lbl.pack(anchor="w", padx=20, pady=(20, 10))

        msg_lbl = ctk.CTkLabel(
            container, text=message, font=ctk.CTkFont(size=13),
            text_color=Theme.CHARCOAL_MED, wraplength=390, justify="left"
        )
        msg_lbl.pack(anchor="w", padx=20, pady=(0, 20))

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(10, 20), side="bottom")

        cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel", fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK,
            hover_color=Theme.BEIGE_HOVER, border_width=1, border_color=Theme.BEIGE_BORDER,
            height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"),
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        confirm_btn = ctk.CTkButton(
            btn_row, text=confirm_label, fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF",
            hover_color=Theme.BURGUNDY_HOVER, height=36, corner_radius=8,
            font=ctk.CTkFont(weight="bold"), command=self._on_confirm
        )
        confirm_btn.pack(side="right")

    def _on_confirm(self):
        self.confirmed = True
        self.grab_release()
        self.destroy()


class ProjectDetailsDialog(BaseModal):
    """Detailed modal view for inspect project attributes and deliverables."""
    def __init__(self, parent, project: Project, db: DatabaseManager, on_view_tasks: Optional[Callable] = None):
        super().__init__(parent, f"Project Details – {project.name}", width=600, height=640)
        self.project = project
        self.db = db
        self.on_view_tasks = on_view_tasks

        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12,
                            border_width=1, border_color=Theme.CHARCOAL_BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Top Header
        top_header = ctk.CTkFrame(card, fg_color="transparent")
        top_header.pack(fill="x", padx=24, pady=(22, 10))

        title_box = ctk.CTkFrame(top_header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box, text=project.name, font=ctk.CTkFont(size=20, weight="bold"),
            text_color=Theme.CHARCOAL_DARK, wraplength=380, justify="left"
        ).pack(anchor="w")

        # Badges Row (Category & Completed Status)
        badges_row = ctk.CTkFrame(top_header, fg_color="transparent")
        badges_row.pack(side="right")

        # Status Badge (Dynamic: Completed, In Progress, Pending)
        badge_text, bg_col, fg_col = Theme.get_project_status_theme(project.status)
        comp_badge = ctk.CTkFrame(badges_row, fg_color=bg_col, corner_radius=6)
        comp_badge.pack(side="right", padx=(6, 0))
        ctk.CTkLabel(
            comp_badge, text=badge_text, font=ctk.CTkFont(size=11, weight="bold"),
            text_color=fg_col
        ).pack(padx=10, pady=4)

        # Category Badge
        cat_badge = ctk.CTkFrame(badges_row, fg_color=Theme.BEIGE_LIGHT, corner_radius=6)
        cat_badge.pack(side="right")
        ctk.CTkLabel(
            cat_badge, text=project.category, font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.BEIGE_TEXT
        ).pack(padx=10, pady=4)

        # Divider
        ctk.CTkFrame(card, height=1, fg_color=Theme.CHARCOAL_BORDER).pack(fill="x", padx=24, pady=(0, 14))

        # Description Section
        desc_box = ctk.CTkFrame(card, fg_color=Theme.BG_ROOT, corner_radius=8,
                                border_width=1, border_color=Theme.CHARCOAL_BORDER)
        desc_box.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            desc_box, text="PROJECT OVERVIEW", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.CHARCOAL_MUTED
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            desc_box, text=project.description or "No description provided.",
            font=ctk.CTkFont(size=13), text_color=Theme.CHARCOAL_MED,
            wraplength=510, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # Progress Section
        prog_box = ctk.CTkFrame(card, fg_color="transparent")
        prog_box.pack(fill="x", padx=24, pady=(0, 16))

        prog_meta = ctk.CTkFrame(prog_box, fg_color="transparent")
        prog_meta.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            prog_meta, text=f"Completion Benchmark: {project.progress_percentage}%",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=Theme.CHARCOAL_DARK
        ).pack(side="left")

        ctk.CTkLabel(
            prog_meta, text=f"Target: {project.formatted_deadline}",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
        ).pack(side="right")

        pbar = ctk.CTkProgressBar(
            prog_box, height=9, corner_radius=5, progress_color=Theme.PROGRESS_FILL,
            fg_color=Theme.PROGRESS_BG
        )
        pbar.set(project.progress_fraction)
        pbar.pack(fill="x")

        # Deliverables / Tasks Preview
        ctk.CTkLabel(
            card, text="ASSOCIATED MILESTONES & TASKS", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        ).pack(anchor="w", padx=24, pady=(0, 6))

        tasks_scroll = ctk.CTkScrollableFrame(card, height=160, fg_color=Theme.BG_ROOT, corner_radius=8)
        tasks_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        tasks = self.db.get_all_tasks(project_id=project.id)
        if not tasks:
            ctk.CTkLabel(
                tasks_scroll, text="No individual sub-tasks registered for this project.",
                font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
            ).pack(pady=20)
        else:
            for t in tasks:
                t_row = ctk.CTkFrame(tasks_scroll, fg_color=Theme.BG_CARD, corner_radius=6,
                                     border_width=1, border_color=Theme.CHARCOAL_BORDER)
                t_row.pack(fill="x", padx=4, pady=3)

                t_inner = ctk.CTkFrame(t_row, fg_color="transparent")
                t_inner.pack(fill="x", padx=12, pady=8)

                ctk.CTkLabel(
                    t_inner, text=f"✓  {t.title}", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=Theme.CHARCOAL_DARK, anchor="w"
                ).pack(side="left", fill="x", expand=True)

                p_pill = ctk.CTkFrame(t_inner, fg_color=Theme.BEIGE_LIGHT, corner_radius=4)
                p_pill.pack(side="right", padx=(6, 0))
                ctk.CTkLabel(
                    p_pill, text=t.priority, font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=Theme.BEIGE_TEXT
                ).pack(padx=6, pady=1)

                s_pill = ctk.CTkFrame(t_inner, fg_color=Theme.STATUS_COMPLETED_BG, corner_radius=4)
                s_pill.pack(side="right")
                ctk.CTkLabel(
                    s_pill, text=t.status, font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="#FFFFFF"
                ).pack(padx=6, pady=1)

        # Bottom Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(6, 16), side="bottom")

        close_btn = ctk.CTkButton(
            actions, text="Close Details", fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK,
            hover_color=Theme.BEIGE_HOVER, border_width=1, border_color=Theme.BEIGE_BORDER,
            height=36, corner_radius=8, font=ctk.CTkFont(weight="bold"),
            command=self._on_cancel
        )
        close_btn.pack(side="right")

        if self.on_view_tasks:
            view_tasks_btn = ctk.CTkButton(
                actions, text="Open in Tasks Tab", fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF",
                hover_color=Theme.BURGUNDY_HOVER, height=36, corner_radius=8,
                font=ctk.CTkFont(weight="bold"), command=self._trigger_view_tasks
            )
            view_tasks_btn.pack(side="right", padx=(0, 10))

    def _trigger_view_tasks(self):
        self._on_cancel()
        if self.on_view_tasks:
            self.on_view_tasks(self.project.id)


class ProjectDialog(BaseModal):
    """Modal for creating or editing a project."""
    def __init__(self, parent, project: Optional[Project] = None):
        super().__init__(parent, "Edit Project" if project else "Create New Project", width=540, height=620)
        self.project = project
        self.saved = False

        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12,
                            border_width=1, border_color=Theme.CHARCOAL_BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header_text = "Edit Project Specification" if project else "Create New Project"
        ctk.CTkLabel(
            card, text=header_text, font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            card, text="Define deliverables, category, project status, and target deadlines.",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
        ).pack(anchor="w", padx=24, pady=(0, 14))

        # Project Name
        ctk.CTkLabel(card, text="Project Name *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        self.name_entry = ctk.CTkEntry(
            card, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK,
            placeholder_text="e.g., Enterprise Platform Modernization"
        )
        self.name_entry.pack(fill="x", padx=24, pady=(0, 10))
        if project:
            self.name_entry.insert(0, project.name)

        # Category and Status in 2 Columns
        cat_stat_row = ctk.CTkFrame(card, fg_color="transparent")
        cat_stat_row.pack(fill="x", padx=24, pady=(0, 10))

        # Category Left
        cat_col = ctk.CTkFrame(cat_stat_row, fg_color="transparent")
        cat_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(cat_col, text="Category / Domain", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", pady=(0, 4))
        self.category_entry = ctk.CTkComboBox(
            cat_col, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=["Productivity", "Beauty & Business Website", "Travel & Tourism", "Engineering", "Operations", "Compliance"]
        )
        self.category_entry.pack(fill="x")
        if project and project.category:
            self.category_entry.set(project.category)
        else:
            self.category_entry.set("Productivity")

        # Status Right
        stat_col = ctk.CTkFrame(cat_stat_row, fg_color="transparent")
        stat_col.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(stat_col, text="Project Status", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", pady=(0, 4))
        self.status_combo = ctk.CTkComboBox(
            stat_col, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=ProjectStatus.ALL
        )
        self.status_combo.pack(fill="x")
        if project and project.status:
            self.status_combo.set(project.status)
        else:
            self.status_combo.set(ProjectStatus.PENDING)

        # Description
        ctk.CTkLabel(card, text="Description", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        self.desc_textbox = ctk.CTkTextbox(
            card, height=75, corner_radius=8, border_width=1, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK
        )
        self.desc_textbox.pack(fill="x", padx=24, pady=(0, 10))
        if project and project.description:
            self.desc_textbox.insert("1.0", project.description)

        # Target Deadline
        ctk.CTkLabel(card, text="Target Deadline (YYYY-MM-DD)", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        
        deadline_row = ctk.CTkFrame(card, fg_color="transparent")
        deadline_row.pack(fill="x", padx=24, pady=(0, 6))

        self.deadline_entry = ctk.CTkEntry(
            deadline_row, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK,
            placeholder_text="YYYY-MM-DD"
        )
        self.deadline_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if project and project.deadline:
            self.deadline_entry.insert(0, project.deadline)

        # Quick preset date buttons
        preset_row = ctk.CTkFrame(card, fg_color="transparent")
        preset_row.pack(fill="x", padx=24, pady=(0, 10))
        
        for label, days in [("Today", 0), ("+2 Weeks", 14), ("+1 Month", 30), ("Clear", -1)]:
            cmd = self._clear_date if days == -1 else (lambda d=days: self._set_date_preset(d))
            btn = ctk.CTkButton(
                preset_row, text=label, width=68, height=26, corner_radius=6,
                fg_color=Theme.BEIGE_LIGHT, text_color=Theme.BEIGE_TEXT,
                hover_color=Theme.BEIGE_HOVER, font=ctk.CTkFont(size=11),
                command=cmd
            )
            btn.pack(side="left", padx=(0, 6))

        # Error notification
        self.error_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color=Theme.BURGUNDY_PRIMARY)
        self.error_lbl.pack(anchor="w", padx=24, pady=(0, 6))

        # Bottom Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(6, 16), side="bottom")

        cancel_btn = ctk.CTkButton(
            actions, text="Cancel", fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK,
            hover_color=Theme.BEIGE_HOVER, border_width=1, border_color=Theme.BEIGE_BORDER,
            height=38, corner_radius=8, font=ctk.CTkFont(weight="bold"),
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(
            actions, text="Save Project", fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF",
            hover_color=Theme.BURGUNDY_HOVER, height=38, corner_radius=8,
            font=ctk.CTkFont(weight="bold"), command=self._on_save
        )
        save_btn.pack(side="right")

    def _set_date_preset(self, days: int):
        target = date.today() + timedelta(days=days)
        self.deadline_entry.delete(0, "end")
        self.deadline_entry.insert(0, target.strftime("%Y-%m-%d"))

    def _clear_date(self):
        self.deadline_entry.delete(0, "end")

    def _on_save(self):
        name = self.name_entry.get().strip()
        category = self.category_entry.get().strip()
        status = self.status_combo.get().strip()
        description = self.desc_textbox.get("1.0", "end-1c").strip()
        deadline = self.deadline_entry.get().strip()

        if not name:
            self.error_lbl.configure(text="Please enter a valid project name.")
            return

        if deadline:
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                self.error_lbl.configure(text="Deadline must be YYYY-MM-DD format (e.g. 2026-11-20).")
                return
        else:
            deadline = None

        self.form_data = {
            "name": name,
            "category": category,
            "status": status,
            "description": description,
            "deadline": deadline
        }
        self.saved = True
        self.grab_release()
        self.destroy()


class TaskDialog(BaseModal):
    """Modal for creating or editing a task."""
    def __init__(self, parent, projects: List[Project], task: Optional[Task] = None, preselected_project_id: Optional[int] = None):
        super().__init__(parent, "Edit Task" if task else "Create New Task", width=560, height=640)
        self.projects = projects
        self.task = task
        self.saved = False

        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12,
                            border_width=1, border_color=Theme.CHARCOAL_BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header_text = "Edit Task Specification" if task else "Create New Task"
        ctk.CTkLabel(
            card, text=header_text, font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            card, text="Define title, associated project, status, priority, and deadline.",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
        ).pack(anchor="w", padx=24, pady=(0, 14))

        # Project Selection
        ctk.CTkLabel(card, text="Parent Project *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        
        project_names = [f"#{p.id}: {p.name}" for p in self.projects]
        self.project_combo = ctk.CTkComboBox(
            card, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=project_names or ["No projects available"]
        )
        self.project_combo.pack(fill="x", padx=24, pady=(0, 10))

        # Set selected project
        if task:
            for p in self.projects:
                if p.id == task.project_id:
                    self.project_combo.set(f"#{p.id}: {p.name}")
                    break
        elif preselected_project_id:
            for p in self.projects:
                if p.id == preselected_project_id:
                    self.project_combo.set(f"#{p.id}: {p.name}")
                    break
        elif project_names:
            self.project_combo.set(project_names[0])

        # Title
        ctk.CTkLabel(card, text="Task Title *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        self.title_entry = ctk.CTkEntry(
            card, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK,
            placeholder_text="e.g., Conduct Security Threat Matrix Review"
        )
        self.title_entry.pack(fill="x", padx=24, pady=(0, 10))
        if task:
            self.title_entry.insert(0, task.title)

        # Priority & Status Row
        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(fill="x", padx=24, pady=(0, 10))

        # Priority
        pri_col = ctk.CTkFrame(meta_row, fg_color="transparent")
        pri_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(pri_col, text="Priority", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", pady=(0, 4))
        self.priority_combo = ctk.CTkComboBox(
            pri_col, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=Priority.ALL
        )
        self.priority_combo.pack(fill="x")
        self.priority_combo.set(task.priority if task else Priority.MEDIUM)

        # Status
        stat_col = ctk.CTkFrame(meta_row, fg_color="transparent")
        stat_col.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(stat_col, text="Status", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", pady=(0, 4))
        self.status_combo = ctk.CTkComboBox(
            stat_col, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=Status.ALL
        )
        self.status_combo.pack(fill="x")
        self.status_combo.set(task.status if task else Status.TODO)

        # Description
        ctk.CTkLabel(card, text="Description", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        self.desc_textbox = ctk.CTkTextbox(
            card, height=70, corner_radius=8, border_width=1, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK
        )
        self.desc_textbox.pack(fill="x", padx=24, pady=(0, 10))
        if task and task.description:
            self.desc_textbox.insert("1.0", task.description)

        # Deadline
        ctk.CTkLabel(card, text="Task Deadline (YYYY-MM-DD)", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Theme.CHARCOAL_DARK).pack(anchor="w", padx=24, pady=(0, 4))
        
        self.deadline_entry = ctk.CTkEntry(
            card, height=36, corner_radius=8, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK,
            placeholder_text="YYYY-MM-DD"
        )
        self.deadline_entry.pack(fill="x", padx=24, pady=(0, 6))
        if task and task.deadline:
            self.deadline_entry.insert(0, task.deadline)

        # Date Presets
        preset_row = ctk.CTkFrame(card, fg_color="transparent")
        preset_row.pack(fill="x", padx=24, pady=(0, 8))
        for label, days in [("Today", 0), ("+3 Days", 3), ("+7 Days", 7), ("+14 Days", 14), ("Clear", -1)]:
            cmd = self._clear_date if days == -1 else (lambda d=days: self._set_date_preset(d))
            btn = ctk.CTkButton(
                preset_row, text=label, width=64, height=26, corner_radius=6,
                fg_color=Theme.BEIGE_LIGHT, text_color=Theme.BEIGE_TEXT,
                hover_color=Theme.BEIGE_HOVER, font=ctk.CTkFont(size=11),
                command=cmd
            )
            btn.pack(side="left", padx=(0, 6))

        # Error notification
        self.error_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color=Theme.BURGUNDY_PRIMARY)
        self.error_lbl.pack(anchor="w", padx=24, pady=(0, 6))

        # Bottom Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(8, 16), side="bottom")

        cancel_btn = ctk.CTkButton(
            actions, text="Cancel", fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK,
            hover_color=Theme.BEIGE_HOVER, border_width=1, border_color=Theme.BEIGE_BORDER,
            height=38, corner_radius=8, font=ctk.CTkFont(weight="bold"),
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(
            actions, text="Save Task", fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF",
            hover_color=Theme.BURGUNDY_HOVER, height=38, corner_radius=8,
            font=ctk.CTkFont(weight="bold"), command=self._on_save
        )
        save_btn.pack(side="right")

    def _set_date_preset(self, days: int):
        target = date.today() + timedelta(days=days)
        self.deadline_entry.delete(0, "end")
        self.deadline_entry.insert(0, target.strftime("%Y-%m-%d"))

    def _clear_date(self):
        self.deadline_entry.delete(0, "end")

    def _on_save(self):
        selected_proj_str = self.project_combo.get()
        if not selected_proj_str or "#" not in selected_proj_str:
            self.error_lbl.configure(text="Please select or create a valid project first.")
            return

        try:
            proj_id = int(selected_proj_str.split(":")[0].replace("#", "").strip())
        except ValueError:
            self.error_lbl.configure(text="Invalid project selection.")
            return

        title = self.title_entry.get().strip()
        if not title:
            self.error_lbl.configure(text="Please provide a task title.")
            return

        priority = self.priority_combo.get()
        status = self.status_combo.get()
        description = self.desc_textbox.get("1.0", "end-1c").strip()
        deadline = self.deadline_entry.get().strip()

        if deadline:
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                self.error_lbl.configure(text="Deadline format must be YYYY-MM-DD.")
                return
        else:
            deadline = None

        self.form_data = {
            "project_id": proj_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": status,
            "deadline": deadline
        }
        self.saved = True
        self.grab_release()
        self.destroy()


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class TaskFlowApp(ctk.CTk):
    """
    TaskFlow – Executive Project Management System
    """
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("TaskFlow – Project Management System")
        self.geometry("1220x780")
        self.minsize(1040, 640)
        self.configure(fg_color=Theme.BG_ROOT)

        # App Icon Setup
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Database Manager (initializes and synchronizes real projects)
        self.db = DatabaseManager()

        # State Variables
        self.current_view = "dashboard"
        self.task_project_filter_id: Optional[int] = None

        # Build Main Layout
        self._build_layout()

        # Initial Navigation to Dashboard
        self.navigate_to("dashboard")

    # ========================================================================
    # LAYOUT STRUCTURE
    # ========================================================================
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. SIDEBAR FRAME
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0, fg_color=Theme.BG_SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self._build_sidebar()

        # 2. MAIN CONTENT AREA
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color=Theme.BG_ROOT)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Top Bar
        self._build_topbar()

        # Dynamic View Container
        self.view_container = ctk.CTkFrame(self.content_area, corner_radius=0, fg_color=Theme.BG_ROOT)
        self.view_container.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self):
        # Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(28, 30))

        # Monogram Badge
        logo_badge = ctk.CTkFrame(brand_frame, width=38, height=38, corner_radius=8, fg_color=Theme.BURGUNDY_PRIMARY)
        logo_badge.pack(side="left", padx=(0, 12))
        logo_badge.pack_propagate(False)
        ctk.CTkLabel(
            logo_badge, text="TF", font=ctk.CTkFont(size=15, weight="bold"), text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

        brand_text_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text_box.pack(side="left", fill="both")
        
        ctk.CTkLabel(
            brand_text_box, text="TaskFlow", font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text_box, text="PROJECT SYSTEM", font=ctk.CTkFont(size=9, weight="bold"),
            text_color=Theme.CHARCOAL_LIGHT
        ).pack(anchor="w")

        # Navigation Links
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "Dashboard"),
            ("projects", "Projects"),
            ("tasks", "All Tasks"),
            ("deadlines", "Upcoming & Overdue"),
            ("about", "System Specs"),
        ]

        ctk.CTkLabel(
            self.sidebar, text="NAVIGATION", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.CHARCOAL_MUTED
        ).pack(anchor="w", padx=24, pady=(0, 8))

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {label}", height=42, corner_radius=8,
                fg_color="transparent", text_color="#C7C9D1", hover_color=Theme.BG_SIDEBAR_ACTIVE,
                anchor="w", font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[key] = btn

        # Quick Actions Section inside Sidebar
        ctk.CTkLabel(
            self.sidebar, text="QUICK ACTIONS", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.CHARCOAL_MUTED
        ).pack(anchor="w", padx=24, pady=(28, 8))

        quick_task_btn = ctk.CTkButton(
            self.sidebar, text="+ Add New Task", height=38, corner_radius=8,
            fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"), command=self.open_new_task_modal
        )
        quick_task_btn.pack(fill="x", padx=16, pady=4)

        quick_proj_btn = ctk.CTkButton(
            self.sidebar, text="+ New Project", height=36, corner_radius=8,
            fg_color=Theme.BG_SIDEBAR_ACTIVE, text_color="#EDE7DC", hover_color=Theme.CHARCOAL_MED,
            border_width=1, border_color="#3E4048",
            font=ctk.CTkFont(size=12, weight="bold"), command=self.open_new_project_modal
        )
        quick_proj_btn.pack(fill="x", padx=16, pady=4)

        # Bottom System Info
        sys_box = ctk.CTkFrame(self.sidebar, fg_color=Theme.BG_SIDEBAR_ACTIVE, corner_radius=8)
        sys_box.pack(side="bottom", fill="x", padx=14, pady=16)

        ctk.CTkLabel(
            sys_box, text="Permanent SQLite Storage", font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            sys_box, text="taskflow.db active", font=ctk.CTkFont(size=10),
            text_color=Theme.CHARCOAL_LIGHT
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def _build_topbar(self):
        self.topbar = ctk.CTkFrame(self.content_area, height=72, fg_color=Theme.BG_ROOT)
        self.topbar.grid(row=0, column=0, sticky="ew", padx=28, pady=(18, 14))
        self.topbar.grid_columnconfigure(0, weight=1)

        # Title & Subtitle Left
        title_box = ctk.CTkFrame(self.topbar, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        self.topbar_title = ctk.CTkLabel(
            title_box, text="Executive Dashboard", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        )
        self.topbar_title.pack(anchor="w")

        self.topbar_subtitle = ctk.CTkLabel(
            title_box, text="Real-time project portfolio metrics, deliverables, and completion status.",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
        )
        self.topbar_subtitle.pack(anchor="w")

        # Action Buttons Right
        top_actions = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_actions.grid(row=0, column=1, sticky="e")

        refresh_btn = ctk.CTkButton(
            top_actions, text="Refresh", width=86, height=36, corner_radius=8,
            fg_color=Theme.BG_CARD, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_LIGHT,
            border_width=1, border_color=Theme.CHARCOAL_BORDER, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._refresh_current_view
        )
        refresh_btn.pack(side="left", padx=(0, 8))

        top_new_proj_btn = ctk.CTkButton(
            top_actions, text="+ New Project", height=36, corner_radius=8,
            fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"), command=self.open_new_project_modal
        )
        top_new_proj_btn.pack(side="left")

    # ========================================================================
    # NAVIGATION HANDLER
    # ========================================================================
    def navigate_to(self, view_name: str, **kwargs):
        self.current_view = view_name

        # Update sidebar active highlights
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(fg_color=Theme.BG_SIDEBAR_ACTIVE, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#C7C9D1")

        # Clear existing view
        for widget in self.view_container.winfo_children():
            widget.destroy()

        # Render selected view
        if view_name == "dashboard":
            self.topbar_title.configure(text="Executive Dashboard")
            self.topbar_subtitle.configure(text="High-level operational overview, project progress, and task metrics.")
            self._render_dashboard()
        elif view_name == "projects":
            self.topbar_title.configure(text="Projects Portfolio")
            self.topbar_subtitle.configure(text="Review, inspect details, and manage deliverables across all projects.")
            self._render_projects()
        elif view_name == "tasks":
            self.topbar_title.configure(text="Task Management")
            self.topbar_subtitle.configure(text="Track, prioritize, and manage deliverables across all projects.")
            filter_proj = kwargs.get("filter_project_id", self.task_project_filter_id)
            self._render_tasks(filter_project_id=filter_proj)
        elif view_name == "deadlines":
            self.topbar_title.configure(text="Upcoming & Overdue Deliverables")
            self.topbar_subtitle.configure(text="Review critical milestones, schedules, and completed deliveries.")
            self._render_deadlines()
        elif view_name == "about":
            self.topbar_title.configure(text="System Architecture & Portfolio Specs")
            self.topbar_subtitle.configure(text="Permanent SQLite persistence, design tokens, and runtime environment.")
            self._render_about()

    def _refresh_current_view(self):
        self.navigate_to(self.current_view)

    # ========================================================================
    # VIEW: 1. MODERN DASHBOARD
    # ========================================================================
    def _render_dashboard(self):
        metrics = self.db.get_dashboard_metrics()

        scroll = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 1. METRICS BANNER (Exact Dashboard Requirements: Total: 3, Completed: 3, Pending: 0, In Progress: 0)
        kpi_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        for col in range(5):
            kpi_frame.grid_columnconfigure(col, weight=1, uniform="kpi")

        kpi_configs = [
            ("Total Projects", str(metrics["total_projects"]), "Developed Initiatives", Theme.CHARCOAL_DARK, None),
            ("Completed Projects", str(metrics["completed_projects"]), "100% Finished", Theme.CHARCOAL_DARK, Theme.BEIGE_LIGHT),
            ("Pending Projects", str(metrics["pending_projects"]), "Upcoming Pipeline", Theme.CHARCOAL_MED, None),
            ("In Progress", str(metrics["in_progress_projects"]), "Active Development", Theme.CHARCOAL_MED, None),
            ("Overall Progress", f"{metrics['completion_rate']}%", "All Deliverables Completed", Theme.BURGUNDY_PRIMARY, Theme.BURGUNDY_LIGHT)
        ]

        for idx, (title, val, sub, text_color, bg_tint) in enumerate(kpi_configs):
            card = ctk.CTkFrame(
                kpi_frame, fg_color=bg_tint if bg_tint else Theme.BG_CARD,
                corner_radius=12, border_width=1,
                border_color=Theme.BURGUNDY_BORDER if bg_tint == Theme.BURGUNDY_LIGHT else Theme.CHARCOAL_BORDER
            )
            card.grid(row=0, column=idx, padx=5, pady=4, sticky="nsew")

            ctk.CTkLabel(
                card, text=title.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                text_color=Theme.CHARCOAL_MUTED
            ).pack(anchor="w", padx=16, pady=(16, 2))

            ctk.CTkLabel(
                card, text=val, font=ctk.CTkFont(size=28, weight="bold"),
                text_color=text_color
            ).pack(anchor="w", padx=16, pady=0)

            ctk.CTkLabel(
                card, text=sub, font=ctk.CTkFont(size=11),
                text_color=Theme.BURGUNDY_PRIMARY if bg_tint == Theme.BURGUNDY_LIGHT else Theme.CHARCOAL_MED
            ).pack(anchor="w", padx=16, pady=(2, 16))

        # 2. FEATURED PROJECTS SECTION (Displays all 3 real projects with Completed badge & 100% progress)
        p_section_header = ctk.CTkFrame(scroll, fg_color="transparent")
        p_section_header.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(
            p_section_header, text="Developed Projects Portfolio",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=Theme.CHARCOAL_DARK
        ).pack(side="left")

        ctk.CTkLabel(
            p_section_header, text="Completed applications permanently stored in SQLite",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
        ).pack(side="left", padx=14)

        ctk.CTkButton(
            p_section_header, text="View Projects Portfolio →", width=160, height=30, corner_radius=6,
            fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_HOVER,
            border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.navigate_to("projects")
        ).pack(side="right")

        # Render 3 Attractive Project Cards on Dashboard
        projects = metrics["active_projects"]
        for proj in projects:
            card = ctk.CTkFrame(
                scroll, fg_color=Theme.BG_CARD, corner_radius=12,
                border_width=1, border_color=Theme.CHARCOAL_BORDER
            )
            card.pack(fill="x", pady=6, padx=2)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=20, pady=(16, 6))

            # Left Name & Badges
            title_left = ctk.CTkFrame(top_row, fg_color="transparent")
            title_left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                title_left, text=proj.name, font=ctk.CTkFont(size=16, weight="bold"),
                text_color=Theme.CHARCOAL_DARK
            ).pack(side="left", padx=(0, 10))

            # Status Badge (Dynamic: Completed, In Progress, Pending)
            badge_text, bg_col, fg_col = Theme.get_project_status_theme(proj.status)
            comp_badge = ctk.CTkFrame(title_left, fg_color=bg_col, corner_radius=6)
            comp_badge.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                comp_badge, text=badge_text, font=ctk.CTkFont(size=10, weight="bold"),
                text_color=fg_col
            ).pack(padx=8, pady=3)

            # Category Badge
            cat_frame = ctk.CTkFrame(title_left, fg_color=Theme.BEIGE_LIGHT, corner_radius=6)
            cat_frame.pack(side="left")
            ctk.CTkLabel(
                cat_frame, text=proj.category, font=ctk.CTkFont(size=10, weight="bold"),
                text_color=Theme.BEIGE_TEXT
            ).pack(padx=8, pady=3)

            # Action Buttons Right
            btn_box = ctk.CTkFrame(top_row, fg_color="transparent")
            btn_box.pack(side="right")

            details_btn = ctk.CTkButton(
                btn_box, text="Project Details", width=105, height=30, corner_radius=6,
                fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_HOVER,
                border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=proj: self.open_project_details_modal(p)
            )
            details_btn.pack(side="left", padx=(0, 6))

            view_tasks_btn = ctk.CTkButton(
                btn_box, text="View Tasks", width=88, height=30, corner_radius=6,
                fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_LIGHT,
                border_width=1, border_color=Theme.CHARCOAL_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda pid=proj.id: self.navigate_to("tasks", filter_project_id=pid)
            )
            view_tasks_btn.pack(side="left")

            # Description
            if proj.description:
                ctk.CTkLabel(
                    card, text=proj.description, font=ctk.CTkFont(size=12),
                    text_color=Theme.CHARCOAL_MED, wraplength=860, justify="left"
                ).pack(anchor="w", padx=20, pady=(0, 10))

            # Progress Bar (Display 100% progress for all three projects)
            prog_row = ctk.CTkFrame(card, fg_color="transparent")
            prog_row.pack(fill="x", padx=20, pady=(0, 16))

            pbar = ctk.CTkProgressBar(
                prog_row, height=8, corner_radius=4, progress_color=Theme.PROGRESS_FILL,
                fg_color=Theme.PROGRESS_BG
            )
            pbar.set(proj.progress_fraction)
            pbar.pack(fill="x", pady=(2, 6))

            meta_row = ctk.CTkFrame(prog_row, fg_color="transparent")
            meta_row.pack(fill="x")

            ctk.CTkLabel(
                meta_row,
                text=f"Progress: {proj.progress_percentage}% ({proj.completed_task_count} of {proj.task_count} milestones completed)",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK
            ).pack(side="left")

            ctk.CTkLabel(
                meta_row, text=f"Status: {proj.status}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.BURGUNDY_PRIMARY
            ).pack(side="right")

        # 3. PORTFOLIO COMPLETION SUMMARY BOX
        sum_box = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        sum_box.pack(fill="x", pady=(14, 10), padx=2)

        s_inner = ctk.CTkFrame(sum_box, fg_color="transparent")
        s_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            s_inner, text="Deliverables & Operations Status", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=Theme.CHARCOAL_DARK
        ).pack(anchor="w")

        ctk.CTkLabel(
            s_inner,
            text=f"Portfolio includes {metrics['total_projects']} projects (featuring To-Do List App, Jazeela Makeup Studio, and TripVista) with {metrics['completed_projects']} completed, {metrics['in_progress_projects']} in progress, and {metrics['pending_projects']} pending across SQLite storage.",
            font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MED, wraplength=880, justify="left"
        ).pack(anchor="w", pady=(4, 0))

    # ========================================================================
    # VIEW: 2. PROJECTS PORTFOLIO
    # ========================================================================
    def _render_projects(self):
        # Controls Frame (Search + Add Project)
        controls = ctk.CTkFrame(self.view_container, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 16))

        self.proj_search_entry = ctk.CTkEntry(
            controls, width=340, height=38, corner_radius=8,
            fg_color=Theme.BG_CARD, border_color=Theme.CHARCOAL_BORDER,
            text_color=Theme.CHARCOAL_DARK, placeholder_text="Search projects by name, category, or description..."
        )
        self.proj_search_entry.pack(side="left")
        self.proj_search_entry.bind("<KeyRelease>", lambda e: self._filter_projects_list())

        new_proj_btn = ctk.CTkButton(
            controls, text="+ Create Project", height=38, corner_radius=8,
            fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"), command=self.open_new_project_modal
        )
        new_proj_btn.pack(side="right")

        # Scrollable container for Project Cards
        self.projects_scroll = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.projects_scroll.pack(fill="both", expand=True)

        self._filter_projects_list()

    def _filter_projects_list(self):
        for widget in self.projects_scroll.winfo_children():
            widget.destroy()

        search_query = self.proj_search_entry.get().strip() if hasattr(self, "proj_search_entry") else ""
        projects = self.db.get_all_projects(search=search_query if search_query else None)

        if not projects:
            empty_box = ctk.CTkFrame(self.projects_scroll, fg_color=Theme.BG_CARD, corner_radius=12,
                                     border_width=1, border_color=Theme.CHARCOAL_BORDER)
            empty_box.pack(fill="x", pady=20, padx=20)
            ctk.CTkLabel(
                empty_box, text="No matching projects found.", font=ctk.CTkFont(size=14, weight="bold"),
                text_color=Theme.CHARCOAL_DARK
            ).pack(pady=(30, 4))
            ctk.CTkLabel(
                empty_box, text="Click '+ Create Project' to register a new initiative.",
                font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
            ).pack(pady=(0, 30))
            return

        # Render Project Cards
        for proj in projects:
            card = ctk.CTkFrame(
                self.projects_scroll, fg_color=Theme.BG_CARD, corner_radius=12,
                border_width=1, border_color=Theme.CHARCOAL_BORDER
            )
            card.pack(fill="x", pady=8, padx=2)

            # Top Header Row: Name, Completed Badge, Category Pill, Action Buttons
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=20, pady=(18, 6))

            title_left = ctk.CTkFrame(top_row, fg_color="transparent")
            title_left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                title_left, text=proj.name, font=ctk.CTkFont(size=16, weight="bold"),
                text_color=Theme.CHARCOAL_DARK
            ).pack(side="left", padx=(0, 10))

            # Status Badge (Dynamic: Completed, In Progress, Pending)
            badge_text, bg_col, fg_col = Theme.get_project_status_theme(proj.status)
            stat_badge = ctk.CTkFrame(title_left, fg_color=bg_col, corner_radius=6)
            stat_badge.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                stat_badge, text=badge_text, font=ctk.CTkFont(size=10, weight="bold"),
                text_color=fg_col
            ).pack(padx=8, pady=3)

            # Category Frame
            cat_frame = ctk.CTkFrame(title_left, fg_color=Theme.BEIGE_LIGHT, corner_radius=6)
            cat_frame.pack(side="left")
            ctk.CTkLabel(
                cat_frame, text=proj.category, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.BEIGE_TEXT
            ).pack(padx=8, pady=3)

            # Right action buttons
            btn_box = ctk.CTkFrame(top_row, fg_color="transparent")
            btn_box.pack(side="right")

            details_btn = ctk.CTkButton(
                btn_box, text="Project Details", width=105, height=30, corner_radius=6,
                fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_HOVER,
                border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=proj: self.open_project_details_modal(p)
            )
            details_btn.pack(side="left", padx=(0, 6))

            view_tasks_btn = ctk.CTkButton(
                btn_box, text="View Tasks", width=86, height=30, corner_radius=6,
                fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_LIGHT,
                border_width=1, border_color=Theme.CHARCOAL_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda pid=proj.id: self.navigate_to("tasks", filter_project_id=pid)
            )
            view_tasks_btn.pack(side="left", padx=(0, 6))

            edit_btn = ctk.CTkButton(
                btn_box, text="Edit", width=60, height=30, corner_radius=6,
                fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_LIGHT,
                border_width=1, border_color=Theme.CHARCOAL_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=proj: self.open_edit_project_modal(p)
            )
            edit_btn.pack(side="left", padx=(0, 6))

            del_btn = ctk.CTkButton(
                btn_box, text="Delete", width=64, height=30, corner_radius=6,
                fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda pid=proj.id, pname=proj.name: self._confirm_delete_project(pid, pname)
            )
            del_btn.pack(side="left")

            # Description
            if proj.description:
                ctk.CTkLabel(
                    card, text=proj.description, font=ctk.CTkFont(size=12),
                    text_color=Theme.CHARCOAL_MED, wraplength=860, justify="left"
                ).pack(anchor="w", padx=20, pady=(0, 12))

            # Progress Bar and Metrics (100% progress)
            prog_row = ctk.CTkFrame(card, fg_color="transparent")
            prog_row.pack(fill="x", padx=20, pady=(0, 16))

            pbar = ctk.CTkProgressBar(
                prog_row, height=8, corner_radius=4, progress_color=Theme.PROGRESS_FILL,
                fg_color=Theme.PROGRESS_BG
            )
            pbar.set(proj.progress_fraction)
            pbar.pack(fill="x", pady=(2, 8))

            meta_row = ctk.CTkFrame(prog_row, fg_color="transparent")
            meta_row.pack(fill="x")

            ctk.CTkLabel(
                meta_row,
                text=f"Progress: {proj.progress_percentage}% ({proj.completed_task_count} of {proj.task_count} milestones completed)",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK
            ).pack(side="left")

            ctk.CTkLabel(
                meta_row, text=f"Status: {proj.status}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.BURGUNDY_PRIMARY
            ).pack(side="right")

    # ========================================================================
    # VIEW: 3. TASK MANAGEMENT & FILTERING
    # ========================================================================
    def _render_tasks(self, filter_project_id: Optional[int] = None):
        self.task_project_filter_id = filter_project_id

        # Controls & Filter Bar
        filter_card = ctk.CTkFrame(
            self.view_container, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        filter_card.pack(fill="x", pady=(0, 14))

        f_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=16, pady=14)

        # Row 1: Search Entry + New Task Button
        r1 = ctk.CTkFrame(f_inner, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 10))

        self.task_search_entry = ctk.CTkEntry(
            r1, width=320, height=36, corner_radius=8,
            fg_color=Theme.BG_ROOT, border_color=Theme.CHARCOAL_BORDER,
            text_color=Theme.CHARCOAL_DARK, placeholder_text="Search tasks by title, description, or project..."
        )
        self.task_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.task_search_entry.bind("<KeyRelease>", lambda e: self._refresh_tasks_table())

        add_task_btn = ctk.CTkButton(
            r1, text="+ Add New Task", height=36, corner_radius=8,
            fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.open_new_task_modal(preselected_project_id=self.task_project_filter_id)
        )
        add_task_btn.pack(side="right")

        # Row 2: Filter Dropdowns
        r2 = ctk.CTkFrame(f_inner, fg_color="transparent")
        r2.pack(fill="x")

        # Project Filter
        projects = self.db.get_all_projects()
        self.proj_lookup = {f"#{p.id}: {p.name}": p.id for p in projects}
        proj_options = ["All Projects"] + list(self.proj_lookup.keys())

        ctk.CTkLabel(r2, text="Project:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK).pack(side="left", padx=(0, 4))
        self.filter_proj_combo = ctk.CTkComboBox(
            r2, width=190, height=32, corner_radius=6, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=proj_options, command=lambda v: self._refresh_tasks_table()
        )
        self.filter_proj_combo.pack(side="left", padx=(0, 12))

        # Preset project if passed
        if filter_project_id:
            for opt, pid in self.proj_lookup.items():
                if pid == filter_project_id:
                    self.filter_proj_combo.set(opt)
                    break
        else:
            self.filter_proj_combo.set("All Projects")

        # Status Filter
        ctk.CTkLabel(r2, text="Status:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK).pack(side="left", padx=(0, 4))
        self.filter_stat_combo = ctk.CTkComboBox(
            r2, width=130, height=32, corner_radius=6, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=["All"] + Status.ALL, command=lambda v: self._refresh_tasks_table()
        )
        self.filter_stat_combo.pack(side="left", padx=(0, 12))
        self.filter_stat_combo.set("All")

        # Priority Filter
        ctk.CTkLabel(r2, text="Priority:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK).pack(side="left", padx=(0, 4))
        self.filter_pri_combo = ctk.CTkComboBox(
            r2, width=120, height=32, corner_radius=6, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=["All"] + Priority.ALL, command=lambda v: self._refresh_tasks_table()
        )
        self.filter_pri_combo.pack(side="left", padx=(0, 12))
        self.filter_pri_combo.set("All")

        # Sort Dropdown
        ctk.CTkLabel(r2, text="Sort By:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.CHARCOAL_DARK).pack(side="left", padx=(0, 4))
        self.sort_combo = ctk.CTkComboBox(
            r2, width=140, height=32, corner_radius=6, border_color=Theme.CHARCOAL_BORDER,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, button_color=Theme.CHARCOAL_MED,
            values=["Deadline", "Priority", "Status", "Newest"], command=lambda v: self._refresh_tasks_table()
        )
        self.sort_combo.pack(side="left", padx=(0, 12))
        self.sort_combo.set("Deadline")

        # Reset Filters Button
        ctk.CTkButton(
            r2, text="Reset Filters", width=90, height=32, corner_radius=6,
            fg_color=Theme.BEIGE_LIGHT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_HOVER,
            border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=11),
            command=self._reset_task_filters
        ).pack(side="right")

        # Task Table Header Row
        tbl_header = ctk.CTkFrame(self.view_container, height=32, fg_color="transparent")
        tbl_header.pack(fill="x", padx=12, pady=(0, 6))

        self.task_count_lbl = ctk.CTkLabel(
            tbl_header, text="Loading deliverables...", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.CHARCOAL_MUTED
        )
        self.task_count_lbl.pack(side="left")

        # Scrollable Task List
        self.tasks_scroll = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tasks_scroll.pack(fill="both", expand=True)

        self._refresh_tasks_table()

    def _reset_task_filters(self):
        self.task_search_entry.delete(0, "end")
        self.filter_proj_combo.set("All Projects")
        self.filter_stat_combo.set("All")
        self.filter_pri_combo.set("All")
        self.sort_combo.set("Deadline")
        self.task_project_filter_id = None
        self._refresh_tasks_table()

    def _refresh_tasks_table(self):
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        search = self.task_search_entry.get().strip()
        proj_str = self.filter_proj_combo.get()
        proj_id = self.proj_lookup.get(proj_str, None) if proj_str != "All Projects" else None
        status = self.filter_stat_combo.get()
        priority = self.filter_pri_combo.get()
        sort_choice = self.sort_combo.get().lower()

        tasks = self.db.get_all_tasks(
            project_id=proj_id,
            status=status if status != "All" else None,
            priority=priority if priority != "All" else None,
            search=search if search else None,
            sort_by=sort_choice
        )

        self.task_count_lbl.configure(text=f"Displaying {len(tasks)} deliverable{'s' if len(tasks) != 1 else ''}")

        if not tasks:
            empty = ctk.CTkFrame(self.tasks_scroll, fg_color=Theme.BG_CARD, corner_radius=12,
                                 border_width=1, border_color=Theme.CHARCOAL_BORDER)
            empty.pack(fill="x", pady=20, padx=20)
            ctk.CTkLabel(
                empty, text="No tasks found matching filter criteria.",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=Theme.CHARCOAL_DARK
            ).pack(pady=(28, 4))
            ctk.CTkLabel(
                empty, text="Try adjusting your search terms or add a new task.",
                font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
            ).pack(pady=(0, 28))
            return

        for task in tasks:
            self._render_task_row(task)

    def _render_task_row(self, task: Task):
        row = ctk.CTkFrame(
            self.tasks_scroll, fg_color=Theme.BG_CARD, corner_radius=10,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        row.pack(fill="x", pady=4, padx=2)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # 1. Status Cycle Button
        is_done = task.is_completed
        cycle_btn = ctk.CTkButton(
            inner, text="DONE" if is_done else ("IN PROG" if task.status == Status.IN_PROGRESS else "TODO"),
            width=68, height=28, corner_radius=6,
            fg_color=Theme.STATUS_COMPLETED_BG if is_done else (Theme.STATUS_IN_PROGRESS_BG if task.status == Status.IN_PROGRESS else Theme.STATUS_TODO_BG),
            text_color=Theme.STATUS_COMPLETED_FG if is_done else (Theme.STATUS_IN_PROGRESS_FG if task.status == Status.IN_PROGRESS else Theme.STATUS_TODO_FG),
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda tid=task.id, curr=task.status: self._cycle_task_status(tid, curr)
        )
        cycle_btn.pack(side="left", padx=(0, 14))

        # 2. Main Details (Title & Project Subtitle)
        center_col = ctk.CTkFrame(inner, fg_color="transparent")
        center_col.pack(side="left", fill="x", expand=True)

        title_text = task.title
        title_font = ctk.CTkFont(size=13, weight="bold", overstrike=1 if is_done else 0)
        title_color = Theme.CHARCOAL_MUTED if is_done else Theme.CHARCOAL_DARK

        ctk.CTkLabel(
            center_col, text=title_text, font=title_font, text_color=title_color,
            anchor="w", justify="left"
        ).pack(fill="x")

        sub_info = f"Project: {task.project_name or 'General'}"
        if task.description:
            desc_short = (task.description[:75] + "...") if len(task.description) > 75 else task.description
            sub_info += f"  •  {desc_short}"

        ctk.CTkLabel(
            center_col, text=sub_info, font=ctk.CTkFont(size=11),
            text_color=Theme.CHARCOAL_MUTED, anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # 3. Badges (Priority, Deadline)
        badge_box = ctk.CTkFrame(inner, fg_color="transparent")
        badge_box.pack(side="left", padx=12)

        # Priority Badge
        p_bg = Theme.PRIORITY_HIGH_BG if task.priority == Priority.HIGH else (
            Theme.PRIORITY_MED_BG if task.priority == Priority.MEDIUM else Theme.PRIORITY_LOW_BG
        )
        pri_badge = ctk.CTkFrame(badge_box, fg_color=p_bg, corner_radius=6)
        pri_badge.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            pri_badge, text=task.priority, font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#FFFFFF"
        ).pack(padx=8, pady=2)

        # Deadline Relative Badge
        if task.deadline:
            is_ov = task.is_overdue
            d_bg = Theme.BURGUNDY_PRIMARY if is_ov else Theme.BEIGE_LIGHT
            d_fg = "#FFFFFF" if is_ov else Theme.CHARCOAL_DARK

            dead_badge = ctk.CTkFrame(badge_box, fg_color=d_bg, corner_radius=6)
            dead_badge.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                dead_badge, text=task.deadline_relative_text,
                font=ctk.CTkFont(size=10, weight="bold"), text_color=d_fg
            ).pack(padx=8, pady=2)

        # 4. Action Buttons (Edit, Delete)
        action_box = ctk.CTkFrame(inner, fg_color="transparent")
        action_box.pack(side="right")

        edit_btn = ctk.CTkButton(
            action_box, text="Edit", width=56, height=28, corner_radius=6,
            fg_color=Theme.BG_ROOT, text_color=Theme.CHARCOAL_DARK, hover_color=Theme.BEIGE_LIGHT,
            border_width=1, border_color=Theme.CHARCOAL_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda t=task: self.open_edit_task_modal(t)
        )
        edit_btn.pack(side="left", padx=(0, 6))

        del_btn = ctk.CTkButton(
            action_box, text="Delete", width=58, height=28, corner_radius=6,
            fg_color=Theme.BURGUNDY_PRIMARY, text_color="#FFFFFF", hover_color=Theme.BURGUNDY_HOVER,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda tid=task.id, tname=task.title: self._confirm_delete_task(tid, tname)
        )
        del_btn.pack(side="left")

    def _cycle_task_status(self, task_id: int, current_status: str):
        if current_status == Status.TODO:
            next_status = Status.IN_PROGRESS
        elif current_status == Status.IN_PROGRESS:
            next_status = Status.COMPLETED
        else:
            next_status = Status.TODO
        
        self.db.update_task_status(task_id, next_status)
        self._refresh_tasks_table()

    def _quick_toggle_task(self, task_id: int, new_status: str):
        self.db.update_task_status(task_id, new_status)
        self._refresh_current_view()

    # ========================================================================
    # VIEW: 4. UPCOMING & OVERDUE DELIVERABLES
    # ========================================================================
    def _render_deadlines(self):
        container = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        overdue_tasks = self.db.get_all_tasks(filter_type="overdue")
        upcoming_tasks = self.db.get_all_tasks(filter_type="upcoming")
        completed_tasks = self.db.get_all_tasks(status=Status.COMPLETED)

        # 1. OVERDUE SECTION
        ov_card = ctk.CTkFrame(
            container, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.BURGUNDY_BORDER
        )
        ov_card.pack(fill="x", pady=(0, 16))

        ov_header = ctk.CTkFrame(ov_card, fg_color="transparent")
        ov_header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            ov_header, text=f"Overdue Tasks ({len(overdue_tasks)})",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=Theme.BURGUNDY_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            ov_header, text="Critical deadlines that have elapsed and require action.",
            font=ctk.CTkFont(size=11), text_color=Theme.CHARCOAL_MUTED
        ).pack(side="left", padx=14)

        if not overdue_tasks:
            ctk.CTkLabel(
                ov_card, text="✓ Zero overdue deliverables. All project milestones are on track!",
                font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MED
            ).pack(pady=24)
        else:
            for task in overdue_tasks:
                item = ctk.CTkFrame(ov_card, fg_color=Theme.BURGUNDY_LIGHT, corner_radius=8,
                                   border_width=1, border_color=Theme.BURGUNDY_BORDER)
                item.pack(fill="x", padx=20, pady=4)

                i_inner = ctk.CTkFrame(item, fg_color="transparent")
                i_inner.pack(fill="x", padx=14, pady=10)

                info_left = ctk.CTkFrame(i_inner, fg_color="transparent")
                info_left.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    info_left, text=task.title, font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=Theme.BURGUNDY_DARK, anchor="w"
                ).pack(fill="x")

                ctk.CTkLabel(
                    info_left, text=f"Project: {task.project_name}  •  Due: {task.formatted_deadline}",
                    font=ctk.CTkFont(size=11), text_color=Theme.CHARCOAL_MED, anchor="w"
                ).pack(fill="x", pady=(2, 0))

                act_right = ctk.CTkFrame(i_inner, fg_color="transparent")
                act_right.pack(side="right")

                pill = ctk.CTkFrame(act_right, fg_color=Theme.BURGUNDY_PRIMARY, corner_radius=6)
                pill.pack(side="left", padx=(0, 10))
                ctk.CTkLabel(
                    pill, text=task.deadline_relative_text.upper(),
                    font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF"
                ).pack(padx=8, pady=3)

                ctk.CTkButton(
                    act_right, text="Mark Done", width=84, height=28, corner_radius=6,
                    fg_color=Theme.CHARCOAL_DARK, text_color="#FFFFFF", hover_color=Theme.CHARCOAL_MED,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda tid=task.id: self._quick_toggle_task(tid, Status.COMPLETED)
                ).pack(side="left", padx=(0, 6))

                ctk.CTkButton(
                    act_right, text="+3 Days", width=68, height=28, corner_radius=6,
                    fg_color=Theme.BEIGE_LIGHT, text_color=Theme.BEIGE_TEXT, hover_color=Theme.BEIGE_HOVER,
                    border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda t=task: self._extend_task_deadline(t, 3)
                ).pack(side="left")

        # 2. UPCOMING DEADLINES SECTION
        up_card = ctk.CTkFrame(
            container, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        up_card.pack(fill="x", pady=(0, 16))

        up_header = ctk.CTkFrame(up_card, fg_color="transparent")
        up_header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            up_header, text=f"Upcoming Deliverables (Next 7 Days: {len(upcoming_tasks)})",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=Theme.CHARCOAL_DARK
        ).pack(side="left")

        if not upcoming_tasks:
            ctk.CTkLabel(
                up_card, text="No immediate deadlines pending in the next 7 days.",
                font=ctk.CTkFont(size=12), text_color=Theme.CHARCOAL_MUTED
            ).pack(pady=24)
        else:
            for task in upcoming_tasks:
                item = ctk.CTkFrame(up_card, fg_color=Theme.BG_ROOT, corner_radius=8,
                                   border_width=1, border_color=Theme.CHARCOAL_BORDER)
                item.pack(fill="x", padx=20, pady=4)

                i_inner = ctk.CTkFrame(item, fg_color="transparent")
                i_inner.pack(fill="x", padx=14, pady=10)

                info_left = ctk.CTkFrame(i_inner, fg_color="transparent")
                info_left.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    info_left, text=task.title, font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=Theme.CHARCOAL_DARK, anchor="w"
                ).pack(fill="x")

                ctk.CTkLabel(
                    info_left, text=f"Project: {task.project_name}  •  Due: {task.formatted_deadline}",
                    font=ctk.CTkFont(size=11), text_color=Theme.CHARCOAL_MUTED, anchor="w"
                ).pack(fill="x", pady=(2, 0))

                act_right = ctk.CTkFrame(i_inner, fg_color="transparent")
                act_right.pack(side="right")

                pill = ctk.CTkFrame(act_right, fg_color=Theme.BEIGE_LIGHT, corner_radius=6)
                pill.pack(side="left", padx=(0, 10))
                ctk.CTkLabel(
                    pill, text=task.deadline_relative_text,
                    font=ctk.CTkFont(size=10, weight="bold"), text_color=Theme.CHARCOAL_DARK
                ).pack(padx=8, pady=3)

                ctk.CTkButton(
                    act_right, text="Complete", width=84, height=28, corner_radius=6,
                    fg_color=Theme.CHARCOAL_DARK, text_color="#FFFFFF", hover_color=Theme.CHARCOAL_MED,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda tid=task.id: self._quick_toggle_task(tid, Status.COMPLETED)
                ).pack(side="left")

        # 3. VERIFIED COMPLETED MILESTONES SECTION
        done_card = ctk.CTkFrame(
            container, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        done_card.pack(fill="x", pady=(0, 10))

        done_header = ctk.CTkFrame(done_card, fg_color="transparent")
        done_header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            done_header, text=f"Completed Deliverables ({len(completed_tasks)})",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=Theme.CHARCOAL_DARK
        ).pack(side="left")

        ctk.CTkLabel(
            done_header, text="Verified milestones finished across developed projects.",
            font=ctk.CTkFont(size=11), text_color=Theme.CHARCOAL_MUTED
        ).pack(side="left", padx=14)

        for task in completed_tasks[:6]:
            item = ctk.CTkFrame(done_card, fg_color=Theme.BG_ROOT, corner_radius=8,
                               border_width=1, border_color=Theme.CHARCOAL_BORDER)
            item.pack(fill="x", padx=20, pady=3)

            i_inner = ctk.CTkFrame(item, fg_color="transparent")
            i_inner.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(
                i_inner, text=f"✓  {task.title}", font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.CHARCOAL_DARK
            ).pack(side="left")

            ctk.CTkLabel(
                i_inner, text=f"in {task.project_name}", font=ctk.CTkFont(size=11),
                text_color=Theme.CHARCOAL_MUTED
            ).pack(side="right")

    def _extend_task_deadline(self, task: Task, days_to_add: int):
        new_date = date.today() + timedelta(days=days_to_add)
        self.db.update_task(
            task_id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            deadline=new_date.strftime("%Y-%m-%d")
        )
        self._refresh_current_view()

    # ========================================================================
    # VIEW: 5. SYSTEM SPECIFICATIONS & ABOUT
    # ========================================================================
    def _render_about(self):
        container = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        card = ctk.CTkFrame(
            container, fg_color=Theme.BG_CARD, corner_radius=12,
            border_width=1, border_color=Theme.CHARCOAL_BORDER
        )
        card.pack(fill="x", padx=4, pady=4)

        c_inner = ctk.CTkFrame(card, fg_color="transparent")
        c_inner.pack(fill="x", padx=24, pady=24)

        ctk.CTkLabel(
            c_inner, text="TaskFlow – Project Management System",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=Theme.CHARCOAL_DARK
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            c_inner,
            text="High-performance native desktop productivity platform built with Python 3, CustomTkinter, and permanent SQLite database persistence.",
            font=ctk.CTkFont(size=13), text_color=Theme.CHARCOAL_MUTED, wraplength=800, justify="left"
        ).pack(anchor="w", pady=(0, 20))

        # Specifications Grid
        specs_box = ctk.CTkFrame(c_inner, fg_color=Theme.BG_ROOT, corner_radius=8,
                                 border_width=1, border_color=Theme.CHARCOAL_BORDER)
        specs_box.pack(fill="x", pady=(0, 20))

        specs = [
            ("Core Framework", "Python 3.14 + CustomTkinter (High-DPI Desktop Engine)"),
            ("Database Engine", f"SQLite 3 ({os.path.abspath(self.db.db_path)})"),
            ("Active Projects", "To-Do List App, Jazeela Makeup Studio, TripVista (All Completed)"),
            ("Project Pipeline", "Full support for Pending, In Progress, and Completed project pipelines"),
            ("Color Standards", "Burgundy (#7A1C2E), Executive Charcoal (#1D1E22), Subtle Beige (#F6F3EC)"),
            ("Design Constraints", "Strictly zero green, teal, neon or distracting tones"),
            ("Data Integrity", "Foreign key cascades & persistent offline storage in taskflow.db")
        ]

        for label, val in specs:
            row = ctk.CTkFrame(specs_box, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(
                row, text=label, width=190, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.CHARCOAL_DARK, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=val, font=ctk.CTkFont(size=12),
                text_color=Theme.CHARCOAL_MED, anchor="w"
            ).pack(side="left")

        # Database Reset / Sync Option
        btn_row = ctk.CTkFrame(c_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        reset_btn = ctk.CTkButton(
            btn_row, text="Re-Sync Real Developed Projects", height=36, corner_radius=8,
            fg_color=Theme.BEIGE_LIGHT, text_color=Theme.BEIGE_TEXT, hover_color=Theme.BEIGE_HOVER,
            border_width=1, border_color=Theme.BEIGE_BORDER, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._confirm_resync_projects
        )
        reset_btn.pack(side="left")

    def _confirm_resync_projects(self):
        diag = ConfirmationDialog(
            self,
            title="Re-Synchronize Real Projects",
            message="This will ensure To-Do List App, Jazeela Makeup Studio, and TripVista are synchronized as 100% completed in SQLite. Proceed?",
            confirm_label="Re-Sync"
        )
        self.wait_window(diag)
        if diag.confirmed:
            with self.db.get_connection() as conn:
                self.db._sync_real_projects(conn.cursor())
                conn.commit()
            self._refresh_current_view()

    # ========================================================================
    # PROJECT OPERATIONS & MODAL TRIGGERS
    # ========================================================================
    def open_project_details_modal(self, project: Project):
        diag = ProjectDetailsDialog(
            self, project=project, db=self.db,
            on_view_tasks=lambda pid: self.navigate_to("tasks", filter_project_id=pid)
        )
        self.wait_window(diag)

    def open_new_project_modal(self):
        diag = ProjectDialog(self)
        self.wait_window(diag)
        if diag.saved and diag.form_data:
            self.db.create_project(
                name=diag.form_data["name"],
                description=diag.form_data["description"],
                category=diag.form_data["category"],
                status=diag.form_data.get("status", ProjectStatus.PENDING),
                deadline=diag.form_data["deadline"]
            )
            self._refresh_current_view()

    def open_edit_project_modal(self, project: Project):
        diag = ProjectDialog(self, project=project)
        self.wait_window(diag)
        if diag.saved and diag.form_data:
            self.db.update_project(
                project_id=project.id,
                name=diag.form_data["name"],
                description=diag.form_data["description"],
                category=diag.form_data["category"],
                status=diag.form_data.get("status", ProjectStatus.COMPLETED),
                deadline=diag.form_data["deadline"]
            )
            self._refresh_current_view()

    def _confirm_delete_project(self, project_id: int, project_name: str):
        diag = ConfirmationDialog(
            self,
            title=f"Delete '{project_name}'?",
            message=f"Are you sure you want to permanently delete '{project_name}'? Associated deliverables will also be removed.",
            confirm_label="Delete Project"
        )
        self.wait_window(diag)
        if diag.confirmed:
            self.db.delete_project(project_id)
            self._refresh_current_view()

    # ========================================================================
    # TASK OPERATIONS & MODAL TRIGGERS
    # ========================================================================
    def open_new_task_modal(self, preselected_project_id: Optional[int] = None):
        projects = self.db.get_all_projects()
        if not projects:
            messagebox.showinfo(
                "Project Required",
                "Please create at least one project before adding tasks."
            )
            self.open_new_project_modal()
            return

        diag = TaskDialog(self, projects=projects, preselected_project_id=preselected_project_id)
        self.wait_window(diag)
        if diag.saved and diag.form_data:
            self.db.create_task(
                project_id=diag.form_data["project_id"],
                title=diag.form_data["title"],
                description=diag.form_data["description"],
                priority=diag.form_data["priority"],
                status=diag.form_data["status"],
                deadline=diag.form_data["deadline"]
            )
            self._refresh_current_view()

    def open_edit_task_modal(self, task: Task):
        projects = self.db.get_all_projects()
        diag = TaskDialog(self, projects=projects, task=task)
        self.wait_window(diag)
        if diag.saved and diag.form_data:
            self.db.update_task(
                task_id=task.id,
                project_id=diag.form_data["project_id"],
                title=diag.form_data["title"],
                description=diag.form_data["description"],
                priority=diag.form_data["priority"],
                status=diag.form_data["status"],
                deadline=diag.form_data["deadline"]
            )
            self._refresh_current_view()

    def _confirm_delete_task(self, task_id: int, task_title: str):
        diag = ConfirmationDialog(
            self,
            title=f"Delete Task?",
            message=f"Are you sure you want to remove '{task_title}'? This action cannot be undone.",
            confirm_label="Delete Task"
        )
        self.wait_window(diag)
        if diag.confirmed:
            self.db.delete_task(task_id)
            self._refresh_current_view()


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    app = TaskFlowApp()
    app.mainloop()
