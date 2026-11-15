# TaskFlow – Project Management System

**TaskFlow** is a professional desktop application designed for project and task management, built natively in Python using **CustomTkinter** for high-DPI modern user interfaces and **SQLite** for reliable, zero-config permanent data storage.

---

## Active Developed Projects

The system comes pre-synchronized with three real developed projects permanently recorded in SQLite:

1. **To-Do List App**
   - **Category**: Productivity
   - **Status**: Completed (100% Progress)
   - **Description**: A task management application for organizing daily tasks.

2. **Jazeela Makeup Studio**
   - **Category**: Beauty & Business Website
   - **Status**: Completed (100% Progress)
   - **Description**: A professional makeup studio website.

3. **TripVista**
   - **Category**: Travel & Tourism
   - **Status**: Completed (100% Progress)
   - **Description**: A Pakistan-based travel booking website built with React.js and Tailwind CSS.

---

## Highlights & Features

1. **Executive Modern Dashboard**:
   - **Real-Time KPI Counts**: Total Projects (3), Completed Projects (3), Pending Projects (0), In Progress Projects (0), and Overall Progress (100.0%).
   - **Attractive Project Cards**: Displays each developed project with a distinct **✓ Completed** badge, category pill, full description, and 100% burgundy progress bar.
   - **Instant Shortcuts**: One-click buttons to open **Project Details** or jump straight to deliverables.

2. **Projects Portfolio Section**:
   - Displays all three completed projects with responsive search and filtering.
   - **Project Details Modal**: Open full project specifications, overview, deliverables list, and milestones.
   - **Full CRUD Support**: Add new initiatives, edit existing specifications, or remove projects with foreign key cascade protection.
   - **Idempotency**: Guarantees no duplicate projects are created upon application restarts.

3. **Task Lifecycle Management**:
   - Manage milestones associated with any project.
   - **Task Statuses**: `To Do`, `In Progress`, and `Completed`.
   - **Priority Levels**: `High` (Deep Burgundy), `Medium` (Warm Terracotta/Auburn), and `Low` (Muted Slate Charcoal).
   - One-click status cycling (`To Do` ➔ `In Progress` ➔ `Completed`) directly from the table.

4. **Permanent SQLite Persistence**:
   - Stored in `taskflow.db` with schema enforcement (`PRAGMA foreign_keys = ON;`).
   - All projects, tasks, and status changes are permanently saved and stay synchronized between the Dashboard and the database.

---

## UI/UX Design System

- **Palette**: Signature deep royal burgundy (`#7A1C2E`), executive charcoal (`#1D1E22`, `#35383F`), and warm subtle beige/ivory accents (`#F6F3EC`, `#DDD6C8`).
- **Background**: Crisp modern off-white (`#F4F5F7`) with pure white structured cards (`#FFFFFF`).
- **Strict Guidelines**: **Zero** greenish, teal, neon, or bright garish tones.

---

## Project Structure

```text
TaskFlow/
├── assets/
│   ├── icon.ico         # Application desktop window icon
│   └── icon.png         # High-resolution brand monogram icon
├── database.py          # SQLite database connection, queries, schema sync, and analytics
├── main.py              # CustomTkinter GUI layout, modals, views, and navigation
├── models.py            # Data classes (Project, Task) and Theme color tokens
├── requirements.txt     # Python dependencies
├── test_app.py          # Automated verification test suite
└── README.md            # Comprehensive documentation
```

---

## Installation & Setup

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Launch the Application
```powershell
python main.py
```

### 3. Run Automated Tests
```powershell
python test_app.py
```
