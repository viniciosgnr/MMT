# Task: MMT Project Implementation

## Current Focus: Module M11 (Configuration)

### [x] Module M10: Reporting and Auditing
- [x] Create backend audit router and models.
- [x] Implement audit logging middleware/utility.
- [x] Create frontend Audit Log viewer.
- [x] Implement Export to Excel/PDF for audit logs.
- [x] Manual verification and walkthrough.

### [x] Module M3: Chemical Analysis (Samples)
- [x] Create sample management UI.
- [x] Implement API for sample registration.
- [x] Implement sample forecasting based on intervals.
- [x] Manual verification and walkthrough.

### [x] Module M5: Synchronization
- [x] Create Sync Sources Management UI.
- [x] Implement API for Sync Source registration via flow computers and PI.
- [x] Implement Sync Job History and Audit Trail.
- [x] Manual data upload via USB dump.
- [x] Manual verification and walkthrough.

### [/] Module M11: Configuration Module
- [x] Backend: Implement `configuration.py` router.
    - [x] Hierarchy tree builder endpoint (`/api/config/hierarchy/tree`).
    - [x] CRUD for `HierarchyNode`.
    - [x] CRUD for `AttributeDefinition` (with validation rules).
    - [x] CRUD for `AttributeValue`.
- [x] Backend: Implement specialized config models (Wells, Holiday, Stock).
- [x] Backend: Implement JSON-based validation logic.
- [x] Frontend: Enhance Configuration Dashboard.
    - [x] Full CRUD in `HierarchyTree`.
    - [x] Attribute Definition Editor with JSON rule builder.
    - [x] Specialized Configurations UI (Wells, Holidays, Stock).
    - [x] Frequency Management (API Integration).
    - [x] Property Editor for selected nodes (Dynamic values).
    - [x] Validation Rule Builder UI.
- [x] Manual verification and walkthrough.

### [/] Module M1: Equipment Management
- [x] Backend: Fix API route ordering conflict
- [x] Frontend: Fix API client calls
- [x] Backend: Add new endpoints (search, checklist, certificates upload)
- [x] Backend: Enhance models (InstallationChecklist, equipment fields)
- [ ] Backend: Implement calibration frequency auto-configuration
- [x] Frontend: Implement installation checklist workflow
- [x] Frontend: Create equipment datasheet modal
- [ ] Frontend: Implement advanced search
- [x] Frontend: Add certificate management UI
- [x] Manual verification and walkthrough

### [x] Module M2: Metrological Confirmation
- [x] Backend: Enhance CalibrationTask model (temporary dates, seals, certificate tracking)
- [x] Backend: Create SealHistory model
- [x] Backend: Enhance CalibrationResult model (CA validation fields)
- [x] Backend: Add status transition endpoints (plan, execute)
- [x] Backend: Add seal management endpoints
- [x] Backend: Add certificate upload and validation endpoints
- [x] Frontend: Create calibration dashboard with task kanban
- [x] Frontend: Create calibration task detail page with workflow
- [x] Frontend: Implement seal management component
- [x] Frontend: Implement certificate upload component
- [x] Frontend: Add temporary date visual indicators
- [x] Manual verification and walkthrough
- [x] **Bug Fixes (Post-MVP)**
    - [x] Fix "Failed to fetch" (API Port Conflict).
    - [x] Fix "Internal Server Error" (Status Enum Mismatch).
    - [x] Fix Frontend Status Sync (Planned vs Scheduled).
    - [x] Add Navigation (Back Button) and Icons.

### [x] Phase 3: Calculations & Verification (Gap Closure)
- [x] Backend: Create FC Verification Simulation endpoint (M6)
- [x] Frontend: Implement FC Verification Dashboard (M6)
- [x] Backend: Refine Chemical Analysis Validation Logic (M3)
- [x] Frontend: Update Sample Entry with statistical warnings (M3)
- [x] Manual verification and walkthrough

### [/] Module M4: Onshore Maintenance (Gap Closure)
- [x] Backend: Add self-referential 'connected_cards' to MaintenanceCard model.
- [x] Frontend: Implement 'Connected Cards' UI in Card Details.
- [x] Frontend: Update Kanban Board to show connection indicators with counts.
- [x] Frontend: Ensure rich text (line breaks) support for descriptions.
- [x] Manual verification and walkthrough
- [x] Fix List View Data Mappings (Status, Responsible, FPSO).
- [x] Implement List View Visual Enhancements (Colors).
- [x] Fix List View TypeScript Errors.

### [/] Module M8: Planning (Bug Fixes)
- [x] Fix "New Strategy" button not working (Implemented `NewStrategyDialog`).

### [/] Phase 4: Modernization (Supabase Migration)
- [/] **Planning & Setup**
    - [/] Install Supabase dependencies (frontend/backend).
    - [x] Create `implementation_plan_supabase.md`.
    - [/] Configure Environment Variables (`.env`).
    - [/] Verify Database Connectivity.
- [x] **Data Migration (SQLite -> Postgres)**
    - [x] Create `dump_sqlite.py` to export data to JSON.
    - [x] Create `restore_postgres.py` to import JSON to Supabase.
    - [x] Run migration scripts.
- [x] **Database Migration (Schema)**
    - [x] Update backend `database.py` to use Postgres URL.
    - [x] Run `Base.metadata.create_all` against Supabase.
- [x] **Authentication Integration**
    - [x] Implement Supabase Auth in Frontend (Login Screen, `AuthProvider`).
    - [x] Polish Login Page UI (Background, Typography).
    - [x] Implement Token Validation Guard in Backend (FastAPI dependency).
    - [x] Refactor all Frontend API calls to use `apiFetch` (Modules M1-M11).
- [x] **Real-time Enablement**

### [x] Phase 5: Advanced Supabase Features
- [x] **Realtime Enablement**
    - [x] M3 Chemical Dashboard (Live status updates).
- [x] **Storage Migration**
    - [x] M10 Reports (Upload to Bucket).
    - [x] M3 Evidence (Upload to Bucket).

### [/] Phase 6: Deployment & Evaluation
- [x] Create Backend Dockerfile (Verified).
- [x] Create Frontend Dockerfile (Verified and Configured).
- [x] Create Docker Compose configuration (Verified).
- [x] Create Deployment Guide.

## Legend
- [ ] Not started
- [/] In progress
- [x] Completed
