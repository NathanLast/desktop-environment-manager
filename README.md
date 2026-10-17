# Desktop Environment Manager

An orchestration platform and terminal user interface for unifying component-specific hardware automations, profile snapshots, and multi-component environments.

---

## Overview

Interacting with hardware configurations on an operating system typically involves scattered scripts, disparate CLI utilities, registry hacks, or vendor-specific tools. While custom scripts can automate individual tasks, managing them across different devices and scenarios quickly becomes fragmented, lacking a unified lifecycle, state tracking, and a cohesive user experience.

**Desktop Environment Manager** is not a hardware driver or low-level utility itself. Instead, it is an **orchestration framework and UI layer** designed to:
1. **Unify Component-Specific Automation**: Bring together independent, component-specific automation scripts and external utilities under a standardized, pluggable interface.
2. **Standardize Profile Management**: Provide uniform creation, capture, application, and storage of configuration snapshots (profiles) across any connected component.
3. **Orchestrate Multi-Component Environments**: Synchronize multiple hardware components into cohesive workspaces (environments) that can be applied, switched, and exited together.
4. **Deliver a Polished Terminal Interface**: Offer a responsive, keyboard-driven Terminal User Interface (TUI) that manages all underlying hardware components consistently from a single application.

---

## Core Concepts

### 1. Components
A **Component** serves as an adapter between the orchestration platform and a specific hardware subsystem's automation logic.
- **B.Y.O.T. (Bring Your Own Tools)**: The component implementation encapsulates whatever scripts, binaries, or system calls are needed to interact with that hardware type.
- **Standardized Lifecycle Contract**: Every component implements a uniform interface:
  - `setup`: Automated provisioning of component-specific requirements (e.g., downloading binaries, checking prerequisites).
  - `init`: Runtime verification and readiness checks.
  - `capture_profile`: Reads the hardware's current live state and saves it to a structured file.
  - `enter_profile`: Applies a saved configuration profile to the hardware.
  - `exit_profile`: Teardown or cleanup when releasing a profile.
- **Pluggable Architecture**: Adding support for a new hardware domain requires only subclassing `Component` and implementing these lifecycle methods. The platform handles the storage, UI menus, and orchestration.

### 2. Profiles
A **Profile** represents a named, saved configuration snapshot for an individual component.
- **Capture**: Serializes the current state of the component to disk.
- **Apply (Enter)**: Reconfigures the hardware to match the profile.
- **Recapture**: Overwrites an existing profile with the hardware's updated live configuration.

### 3. Environments
An **Environment** orchestrates multiple bound components simultaneously, enabling full-system workspace switching with a single command. Environments support two distinct paradigms:

#### Static Environments
- **Preset Configurations**: Map each bound component to an existing, pre-configured profile.
- **Simultaneous Application**: Entering a static environment triggers all associated component profiles at once.
- **Stateless**: Because static environments function as predefined presets, they require no runtime tracking or teardown on exit.

#### Dynamic Environments
- **Live, Adaptive Workspaces**: Designed to preserve changes made to hardware configurations during active work sessions.
- **Baseline Capture**: Upon creation, a dynamic environment automatically captures the starting baseline state of all bound components.
- **Auto-Recapture on Exit**: When exiting a dynamic environment, any configuration adjustments made during the session are automatically recaptured and persisted back into the environment's state.
- **Inter-Session Persistence**: Dynamic environments remain active even if the application is closed. The active state is recorded on disk, allowing uninterrupted workflows across system restarts until explicitly exited by the user.

---

## Architecture & Code Structure

The platform is architected in decoupled layers:

```
repo/
├── components/          # Pluggable component implementations wrapping external automation logic
├── data/                # File-backed storage (component profiles, environment mappings, app state)
├── src/
│   ├── entities/        # Core models and execution contexts (AppContext, ComponentContext, Profile, Environment)
│   ├── services/        # Business logic for component management and environment orchestration
│   ├── storage/         # Transactional JSON state handling (StateHandler) and directory abstractions (StorageHandler)
│   ├── ui/              # Terminal User Interface powered by Textual
│   │   ├── templates/   # Reusable UI templates (MenuScreen, InputScreen, InfoScreen)
│   │   ├── units/       # Specialized screens (Catalogs, Menus, Loading screen, Error dialogs)
│   │   └── app.py       # TUI application lifecycle and async worker management
│   └── util/            # Shared utilities (system execution, network helpers, model serialization)
├── main.py              # Application entrypoint and lifespan coordinator
└── requirements.txt     # Python dependencies
```

### Key Technical Characteristics
- **Non-Blocking Background Workers**: External automation scripts and hardware queries can introduce latency. All hardware-interacting actions are executed asynchronously via background worker threads with an animated `LoadingScreen` spinner, keeping the TUI completely responsive.
- **Keyboard-First Navigation**: Optimized for speed with direct number key triggers (`1`–`9`), arrow navigation, and standard shortcuts (`Escape` / `q` to go back, `Ctrl+Q` to exit).
- **Isolated Storage Boundaries**: Each component and environment operates in an isolated storage namespace with transactional JSON state management.

---

## Installation & Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.12)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Launch the platform from the project root:
```bash
python -m main
```
Or execute the entry point directly:
```bash
python main.py
```

### 3. Keyboard Shortcuts
| Key | Action |
| --- | --- |
| `1` – `9` | Directly activate numbered menu option |
| `↑` / `↓` | Navigate options list |
| `Enter` | Select highlighted option |
| `Escape` / `q` | Go back to previous menu |
| `Ctrl + Q` | Quit the application |
