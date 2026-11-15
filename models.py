"""
TaskFlow - Project Management System
Data Models and Theme Configuration
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Tuple


# ==========================================
# STRICT PALETTE: Burgundy, Charcoal & Subtle Beige
# ABSOLUTELY NO GREEN, TEAL, NEON OR BRIGHT COLORS
# ==========================================
class Theme:
    # Backgrounds
    BG_ROOT = "#F4F5F7"          # Crisp modern off-white app background
    BG_CARD = "#FFFFFF"          # Pure white card background
    BG_CARD_ALT = "#FAF8F5"      # Subtle warm beige-tinted card background
    BG_SIDEBAR = "#1D1E22"       # Deep executive charcoal sidebar
    BG_SIDEBAR_ACTIVE = "#2D2E35"# Active sidebar item background
    BG_MODAL = "#FFFFFF"         # Pure white modal dialog background
    
    # Charcoal Accents
    CHARCOAL_DARK = "#1E1F24"    # Deepest charcoal for headers and titles
    CHARCOAL_MED = "#35383F"     # Medium charcoal for secondary text & icons
    CHARCOAL_MUTED = "#636773"   # Muted charcoal for captions & labels
    CHARCOAL_LIGHT = "#9CA0AC"   # Subtle placeholder charcoal
    CHARCOAL_BORDER = "#E2E4E8"  # Clean card divider / subtle border
    
    # Burgundy Accents
    BURGUNDY_PRIMARY = "#7A1C2E" # Signature deep royal burgundy
    BURGUNDY_HOVER = "#5F1322"   # Darker burgundy on hover
    BURGUNDY_LIGHT = "#F8ECEF"   # Light burgundy wash for badges / highlights
    BURGUNDY_BORDER = "#D8A7B1"  # Border for burgundy elements
    BURGUNDY_DARK = "#4A0E1A"    # Deepest wine
    
    # Beige & Warm Neutrals
    BEIGE_LIGHT = "#F6F3EC"      # Warm ivory / beige container
    BEIGE_HOVER = "#EDE7DC"      # Warm beige hover
    BEIGE_BORDER = "#DDD6C8"     # Warm beige outline border
    BEIGE_TEXT = "#524B42"       # Deep warm charcoal-beige text
    
    # Status Colors (Strictly Burgundy, Charcoal & Warm Muted Taupe)
    STATUS_TODO_BG = "#EAEBED"
    STATUS_TODO_FG = "#3B3F47"
    
    STATUS_IN_PROGRESS_BG = "#F4EBE3"
    STATUS_IN_PROGRESS_FG = "#684534"
    
    STATUS_PENDING_BG = "#EAEBED"
    STATUS_PENDING_FG = "#495057"
    
    STATUS_COMPLETED_BG = "#1E1F24"  # Executive Charcoal Completed Badge
    STATUS_COMPLETED_FG = "#FFFFFF"
    
    # Priority Colors (High: Burgundy, Medium: Warm Terracotta/Auburn, Low: Muted Charcoal)
    PRIORITY_HIGH_BG = "#7A1C2E"
    PRIORITY_HIGH_FG = "#FFFFFF"
    
    PRIORITY_MED_BG = "#9B5D52"
    PRIORITY_MED_FG = "#FFFFFF"
    
    PRIORITY_LOW_BG = "#616773"
    PRIORITY_LOW_FG = "#FFFFFF"
    
    # Progress Bar Fill (Executive Burgundy)
    PROGRESS_FILL = "#7A1C2E"
    PROGRESS_BG = "#E5E1D8"

    @classmethod
    def get_project_status_theme(cls, status: str) -> Tuple[str, str, str]:
        """Returns (badge_text, bg_color, fg_color) for a project status."""
        status_clean = status.strip().title() if status else "Pending"
        if status_clean == "Completed":
            return "✓ COMPLETED", cls.STATUS_COMPLETED_BG, cls.STATUS_COMPLETED_FG
        elif status_clean == "In Progress":
            return "IN PROGRESS", cls.BURGUNDY_PRIMARY, "#FFFFFF"
        else:  # Pending
            return "PENDING", cls.STATUS_PENDING_BG, cls.STATUS_PENDING_FG


class Status:
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ALL = [TODO, IN_PROGRESS, COMPLETED]


class ProjectStatus:
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ALL = [PENDING, IN_PROGRESS, COMPLETED]


class Priority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    ALL = [LOW, MEDIUM, HIGH]


@dataclass
class Project:
    id: Optional[int]
    name: str
    description: str
    category: str
    status: str = ProjectStatus.COMPLETED
    deadline: Optional[str] = None
    created_at: Optional[str] = None
    task_count: int = 0
    completed_task_count: int = 0

    @property
    def is_completed(self) -> bool:
        return self.status == ProjectStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        return self.status == ProjectStatus.PENDING

    @property
    def is_in_progress(self) -> bool:
        return self.status == ProjectStatus.IN_PROGRESS

    @property
    def progress_percentage(self) -> float:
        if self.is_completed:
            return 100.0
        if self.is_pending:
            if self.task_count == 0:
                return 0.0
            return round((self.completed_task_count / self.task_count) * 100, 1)
        if self.task_count == 0:
            return 0.0
        return round((self.completed_task_count / self.task_count) * 100, 1)

    @property
    def progress_fraction(self) -> float:
        if self.is_completed:
            return 1.0
        if self.task_count == 0:
            return 0.0
        return min(1.0, self.completed_task_count / self.task_count)

    @property
    def formatted_deadline(self) -> str:
        if not self.deadline:
            return "Completed" if self.is_completed else "No deadline"
        try:
            d = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            return d.strftime("%b %d, %Y")
        except ValueError:
            return self.deadline


@dataclass
class Task:
    id: Optional[int]
    project_id: int
    title: str
    description: str
    priority: str
    status: str
    deadline: Optional[str]
    created_at: Optional[str] = None
    project_name: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        return self.status == Status.COMPLETED

    @property
    def is_overdue(self) -> bool:
        if self.is_completed or not self.deadline:
            return False
        try:
            d = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            return d < date.today()
        except ValueError:
            return False

    @property
    def is_due_soon(self) -> bool:
        if self.is_completed or not self.deadline:
            return False
        try:
            d = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = date.today()
            delta = (d - today).days
            return 0 <= delta <= 7
        except ValueError:
            return False

    @property
    def deadline_relative_text(self) -> str:
        if self.is_completed:
            return "Completed"
        if not self.deadline:
            return "No deadline"
        try:
            d = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = date.today()
            delta = (d - today).days
            if delta < 0:
                days_ago = abs(delta)
                return f"Overdue by {days_ago} day{'s' if days_ago != 1 else ''}"
            elif delta == 0:
                return "Due today"
            elif delta == 1:
                return "Due tomorrow"
            elif delta <= 7:
                return f"Due in {delta} days"
            else:
                return d.strftime("%b %d, %Y")
        except ValueError:
            return self.deadline

    @property
    def formatted_deadline(self) -> str:
        if not self.deadline:
            return "Completed" if self.is_completed else "None"
        try:
            d = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            return d.strftime("%b %d, %Y")
        except ValueError:
            return self.deadline
