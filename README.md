# 📝 Notes-Time

A lightweight, offline-first desktop note-taking application built with Python and Tkinter. Supports rich text editing, floating images, clickable hyperlinks, task checkboxes, dark/light theming, and smart auto-save — all stored locally as JSON files.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Rich Text Editing** | Bold, underline, custom colors, and adjustable font sizes via right-click menu or keyboard shortcuts |
| **Floating Images** | Insert PNG/JPG images, drag to reposition, resize or delete via right-click — images scroll with the document |
| **Hyperlinks** | Attach web URLs or local file paths to selected text; click to open |
| **Task Checkboxes** | Insert `☐` checkboxes and click to toggle `☑` with strikethrough styling |
| **Folder & Note Tree** | Sidebar file tree with nested folder support — full recursive structure |
| **Smart Auto-Save** | Debounced 2.5-second auto-save triggers after typing stops; manual save via `Ctrl+S` |
| **Always on Top** | Pin the window to float above all other applications |
| **Dark / Light Theme** | Toggle between dark (`#1e1e1e`) and light (`#ffffff`) themes at runtime |
| **Local JSON Storage** | All notes saved to a `MyNotes_Data/` folder in the working directory — no database required |

---

## 📦 Requirements

**Python:** 3.8 or higher

**Dependencies:**

| Package | Version | Purpose |
|---|---|---|
| `Pillow` | ≥ 10.0.0 | Image loading, resizing, and rendering via `ImageTk` |
| `pyinstaller` | ≥ 6.0.0 | Compiling to standalone `.exe` |

> `tkinter` is part of the Python standard library. No separate install needed.

---

## ⚙️ Installation

### 1. Clone or download the project

```bash
git clone https://github.com/your-username/notes-time.git
cd notes-time
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run directly (development mode)

```bash
python main.py
```

---

## 🛠️ Build as `.exe` (Windows)

Compile to a single portable executable with no console window:

```bash
pyinstaller --noconsole --onefile --name "Notes-Time" main.py
```

**Output:** `dist/Notes-Time.exe`

> The `MyNotes_Data/` folder will be created automatically next to the `.exe` on first run.

**Build flags explained:**

| Flag | Effect |
|---|---|
| `--noconsole` | Suppresses the terminal/console window on launch |
| `--onefile` | Bundles everything into a single `.exe` file |
| `--name "Notes-Time"` | Sets the output executable name |

---

## 🚀 How to Use

### Creating Notes

1. Click **📁 +Folder** to create an organizational folder inside `MyNotes_Data/`
2. Click **📄 +Note** to create a new `.json` note file
3. Select any note from the sidebar to open it in the editor

### Text Formatting

- **Right-click** on selected text to open the formatting menu
- Options: Bold, Underline, Color picker, Font size (A+ / A-), Add Link, Add File Path
- Keyboard shortcuts:

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save note |
| `Ctrl+B` | Toggle bold |
| `Ctrl+U` | Toggle underline |
| `Ctrl+T` | Insert checkbox |
| `Ctrl+A` | Select all |
| `Ctrl+Backspace` | Delete previous word |

### Images

1. Click **🖼 +Image** to insert a PNG or JPG image
2. **Drag** the image to reposition it within the note
3. **Right-click** the image to resize (±20%) or delete it
4. Images are anchored to document text marks — they scroll with the content

### Links

1. Select text in the editor
2. Click **🔗 +Link** → enter a URL (e.g., `https://example.com`)
3. Or click **📂 +FilePath** → pick a local file to link to
4. Click the blue underlined text to open the link

### Tasks

1. Click **✅ Task** or press `Ctrl+T` to insert a `☐` checkbox
2. Click the `☐` symbol to check it → becomes `☑` with strikethrough

### Window Options

- **📌 Float: OFF/ON** — Toggles always-on-top mode
- **🌙 Dark Mode / ☀️ Light Mode** — Toggles the UI theme

---

## 🗂️ Data Storage

All notes are stored locally in:

```
<working directory>/
└── MyNotes_Data/
    ├── MyFolder/
    │   └── my-note.json
    └── another-note.json
```

Each `.json` file stores text content, formatting tags, image paths, link mappings, and image positions. **Image files are referenced by path — moving or deleting the original image file will break the embed.**

---

## 📁 Project Structure

```
notes-time/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── MyNotes_Data/        # Auto-created on first run
```

---

## 📄 License

MIT License — free to use, modify, and distribute.
