import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import json
import webbrowser


class NotesTime:
    def __init__(self, root):
        self.root = root
        self.root.title("Note Time")
        self.root.geometry("700x700")
        self.root.resizable(False, False)
        
        self.db_path = os.path.join(os.getcwd(), "MyNotes_Data")
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)

        self.current_file = None
        self.image_refs = {} 
        self.link_map = {}   

        # Dragging states
        self.dragging_image = None
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0

        # ── NEW: Auto-Save Timer State ──
        self.autosave_timer = None

        # Theme states
        self.current_theme = "dark"
        self.themes = {
            "light": {
                "bg": "#ffffff",
                "fg": "#000000",
                "toolbar_bg": "#f0f0f0",
                "btn_bg": "#e1e1e1",
                "btn_fg": "#000000",
                "sidebar_bg": "#f5f5f5",
                "menu_bg": "#ffffff",
                "menu_fg": "#000000"
            },
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "toolbar_bg": "#2d2d2d",
                "btn_bg": "#3c3c3c",
                "btn_fg": "#ffffff",
                "sidebar_bg": "#252526",
                "menu_bg": "#2d2d2d",
                "menu_fg": "#ffffff"
            }
        }

        self.setup_ui()
        self.setup_shortcuts()
        self.refresh_sidebar()
        self.apply_theme() 

    def setup_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # --- TOOLBAR ---
        self.toolbar = tk.Frame(self.root, height=45)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        btns = [
            ("📁 +Folder", self.add_folder),
            ("📄 +Note", self.add_note),
            ("🖼 +Image", self.insert_image),
            ("✅ Task", self.add_checkbox),
            ("🔗 +Link", self.add_web_link),
            ("📂 +FilePath", self.add_file_link)
        ]

        self.toolbar_btns = []
        for text, cmd in btns:
            b = tk.Button(self.toolbar, text=text, command=cmd, takefocus=0, relief="flat", padx=10)
            b.pack(side="left", padx=2, pady=5)
            self.toolbar_btns.append(b)

        # ── NEW: Always on Top Button ──
        self.top_btn = tk.Button(self.toolbar, text="📌 Float: OFF", command=self.toggle_top, takefocus=0, relief="flat", padx=10)
        self.top_btn.pack(side="left", padx=2, pady=5)
        self.toolbar_btns.append(self.top_btn)

        self.theme_btn = tk.Button(self.toolbar, text="🌙 Dark Mode", command=self.toggle_theme, takefocus=0, relief="flat", padx=10)
        self.theme_btn.pack(side="right", padx=5, pady=5)

        # --- SIDEBAR ---
        self.sidebar_frame = tk.Frame(self.root)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.columnconfigure(0, weight=1)
        self.sidebar_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.sidebar_frame)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.load_note)

        # --- EDITOR ---
        self.editor = tk.Text(self.root, font=("Segoe UI", 14), undo=True, wrap="word", padx=20, pady=20)
        self.editor.grid(row=1, column=1, sticky="nsew")

        self.editor.tag_configure("bold", font=("Segoe UI", 14, "bold"))
        self.editor.tag_configure("underline", underline=True)
        self.editor.tag_configure("completed", overstrike=True, foreground="#888888")

        # --- TEXT POPUP MENU ---
        self.quick_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 10))
        self.quick_menu.add_command(label="𝗕 Bold", command=lambda: self.toggle_tag("bold"))
        self.quick_menu.add_command(label="𝗨 Underline", command=lambda: self.toggle_tag("underline"))
        self.quick_menu.add_command(label="🎨 Color...", command=self.choose_color)
        self.quick_menu.add_command(label="🔗 +Link", command=self.add_web_link)
        self.quick_menu.add_command(label="📂 +FilePath", command=self.add_file_link)
        self.quick_menu.add_separator()
        self.quick_menu.add_command(label="A+ Larger", command=lambda: self.change_font_size(2))
        self.quick_menu.add_command(label="A- Smaller", command=lambda: self.change_font_size(-2))

        # --- IMAGE POPUP MENU ---
        self.image_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 10))
        self.image_menu.add_command(label="➕ Make Larger", command=lambda: self.resize_image(1.2))
        self.image_menu.add_command(label="➖ Make Smaller", command=lambda: self.resize_image(0.8))
        self.image_menu.add_separator()
        self.image_menu.add_command(label="❌ Delete Image", command=self.delete_image)
        self.active_image_label = None

        # General bindings
        self.editor.bind("<Button-3>", self.show_quick_menu)
        self.editor.bind("<Button-1>", self.hide_quick_menu, add="+")
        self.editor.bind("<Key>", self.hide_quick_menu, add="+")
        self.editor.bind("<Button-1>", self.on_editor_click, add="+")

        # ── Bind KeyRelease for the Smart Auto-Save ──
        self.editor.bind("<KeyRelease>", self.reset_autosave_timer, add="+")

        # ── SCROLL BINDINGS: reposition images whenever the viewport moves ──
        self.editor.bind("<MouseWheel>",
                         lambda e: self.root.after(1, self._reposition_images))
        self.editor.bind("<Button-4>",                          # Linux scroll up
                         lambda e: self.root.after(1, self._reposition_images))
        self.editor.bind("<Button-5>",                          # Linux scroll down
                         lambda e: self.root.after(1, self._reposition_images))
        self.editor.bind("<Configure>",                         # window resize
                         lambda e: self.root.after(1, self._reposition_images))

    # ── SCROLL SYNC ─────────────────────────────────────────────────────────
    def _reposition_images(self, event=None):
        """
        Re-anchor every floating image label to its stored text mark.
        Called after any scroll or resize so images track document position,
        not viewport position. Images scrolled off-screen are hidden.
        """
        for child in self.editor.winfo_children():
            if not (isinstance(child, tk.Label) and hasattr(child, 'img_name')):
                continue
            ref = self.image_refs.get(child.img_name)
            if not ref:
                continue
            mark = ref.get("mark")
            if not mark:
                continue
            try:
                bbox = self.editor.bbox(mark)
                if bbox:
                    _, mark_y, _, _ = bbox
                    child.place(x=ref["x_offset"], y=mark_y)
                    child.lift()
                else:
                    # Mark is off-screen — hide until scrolled back into view
                    child.place_forget()
            except tk.TclError:
                pass

    # --- KEYBOARD SHORTCUTS ---
    def setup_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_note(e))
        self.root.bind("<Control-S>", lambda e: self.save_note(e))

        self.root.bind("<Control-a>", lambda e: self.editor.tag_add("sel", "1.0", "end"))
        self.root.bind("<Control-A>", lambda e: self.editor.tag_add("sel", "1.0", "end"))

        # Check box
        self.root.bind("<Control-t>", lambda e: self.add_checkbox(e))
        self.root.bind("<Control-T>", lambda e: self.add_checkbox(e))

        # Bold text
        self.root.bind("<Control-b>", lambda e: self.toggle_tag("bold"))
        self.root.bind("<Control-B>", lambda e: self.toggle_tag("bold"))

        # Under line
        self.root.bind("<Control-u>", lambda e: self.toggle_tag("underline"))
        self.root.bind("<Control-U>", lambda e: self.toggle_tag("underline"))

        self.editor.bind("<Control-BackSpace>", self.delete_word)

    def delete_word(self, event):
        try:
            if self.editor.tag_ranges("sel"):
                self.editor.delete("sel.first", "sel.last")
            else:
                start_index = self.editor.index("insert -1c wordstart")
                cursor_index = self.editor.index("insert")
                self.editor.delete(start_index, cursor_index)

        except tk.TclError:
            pass
        return "break"

    # --- CHECKBOX ---
    def add_checkbox(self, event=None):
        self.editor.insert("insert", "☐ ")
        return "break"
    
    def on_editor_click(self, event):
        self.hide_quick_menu(event)
        index = self.editor.index(f"@{event.x},{event.y}")
        char = self.editor.get(index)
    
        if char == "☐":
            self.editor.delete(index)
            self.editor.insert(index, "☑")
            self.editor.tag_add("completed", f"{index} + 1c", f"{index} lineend")
            return "break"
        elif char == "☑":
            self.editor.delete(index)
            self.editor.insert(index, "☐")
            self.editor.tag_remove("completed", f"{index} + 1c", f"{index}  lineend")
            return "break"

    # --- POPUP MENUS ---
    def show_quick_menu(self, event):
        try:
            if self.editor.tag_ranges("sel"):
                self.quick_menu.post(event.x_root + 10, event.y_root + 10)
        except Exception:
            pass

        return "break"

    def hide_quick_menu(self, event):
        self.quick_menu.unpost()

    def change_font_size(self, delta):
        try:
            self.editor.index(tk.SEL_FIRST) 
            current_tags = self.editor.tag_names(tk.SEL_FIRST)
            current_size = 14 
            for t in current_tags:
                if t.startswith("size_"):
                    current_size = int(t.split("_")[1])
                    break
            new_size = max(8, min(72, current_size + delta))
            new_tag = f"size_{new_size}"
            self.editor.tag_configure(new_tag, font=("Segoe UI", new_size))
            for t in self.editor.tag_names():
                if t.startswith("size_"):
                    self.editor.tag_remove(t, tk.SEL_FIRST, tk.SEL_LAST)
            self.editor.tag_add(new_tag, tk.SEL_FIRST, tk.SEL_LAST)
            self.reset_autosave_timer(None)

        except tk.TclError:
            pass

    # --- THEME ---
    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_btn.config(text="☀️ Light Mode")
        else:
            self.current_theme = "light"
            self.theme_btn.config(text="🌙 Dark Mode")
        self.apply_theme()

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        self.root.configure(bg=theme["bg"])
        self.toolbar.configure(bg=theme["toolbar_bg"])
        self.sidebar_frame.configure(bg=theme["sidebar_bg"])
        self.editor.configure(bg=theme["bg"], fg=theme["fg"], insertbackground=theme["fg"])
        self.quick_menu.configure(bg=theme["menu_bg"], fg=theme["menu_fg"],
                                  activebackground=theme["btn_bg"], activeforeground=theme["btn_fg"])
        self.image_menu.configure(bg=theme["menu_bg"], fg=theme["menu_fg"],
                                  activebackground=theme["btn_bg"], activeforeground=theme["btn_fg"])
        for btn in self.toolbar_btns:
            btn.configure(bg=theme["btn_bg"], fg=theme["btn_fg"],
                          activebackground=theme["btn_bg"], activeforeground=theme["btn_fg"])
        self.theme_btn.configure(bg=theme["btn_bg"], fg=theme["btn_fg"],
                                 activebackground=theme["btn_bg"], activeforeground=theme["btn_fg"])
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=theme["sidebar_bg"],
                        fieldbackground=theme["sidebar_bg"], foreground=theme["fg"])
        style.configure("Treeview.Heading", background=theme["toolbar_bg"], foreground=theme["fg"])
        for child in self.editor.winfo_children():
            if isinstance(child, tk.Label) and hasattr(child, 'image'):
                child.configure(bg=theme["bg"])

    # --- HYPERLINKS ---
    def add_web_link(self):
        try:
            self.editor.index(tk.SEL_FIRST)
        except tk.TclError:
            messagebox.showinfo("Selection Required", "Please highlight the word(s) you want to turn into a link first!")
            return
        url = simpledialog.askstring("Add Link", "Enter website URL (e.g., https://www.google.com):")
        if url: self._create_hyperlink(url)

    def add_file_link(self):
        try:
            self.editor.index(tk.SEL_FIRST)
        except tk.TclError:
            messagebox.showinfo("Selection Required", "Please highlight the word(s) you want to turn into a file shortcut first!")
            return
        file_path = filedialog.askopenfilename(title="Select a file to link to")
        if file_path: self._create_hyperlink(file_path)

    def _create_hyperlink(self, target):
        link_id = f"link_{len(self.link_map)}"
        self.link_map[link_id] = target
        self.editor.tag_add(link_id, tk.SEL_FIRST, tk.SEL_LAST)
        self.editor.tag_configure(link_id, foreground="#0066cc", underline=True)
        self.editor.tag_bind(link_id, "<Button-1>", lambda e, t=target: self.open_hyperlink(t))
        self.editor.tag_bind(link_id, "<Enter>", lambda e: self.editor.config(cursor="hand2"))
        self.editor.tag_bind(link_id, "<Leave>", lambda e: self.editor.config(cursor=""))

    def open_hyperlink(self, target):
        try:
            webbrowser.open(target)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link: {e}")

    # ── IMAGE HANDLING ───────────────────────────────────────────────────────
    def insert_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self._add_image_to_widget(path, 50, 50)

    def _add_image_to_widget(self, path, x_pos, y_pos, width=300, height=None, mark_index=None):
        """
        Places a floating image label inside the Text editor and anchors it
        to a text-document mark so it tracks scrolling correctly.

        mark_index: optional character index string (e.g. "3.5") used when
                    re-loading a saved note — positions the mark precisely.
        """
        try:
            original_img = Image.open(path)
            
            if height is None:
                ratio = width / float(original_img.width)
                height = int(original_img.height * ratio)

            img_resized = original_img.resize((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)
            
            img_name  = f"img_{len(self.image_refs)}"
            mark_name = f"mark_{img_name}"

            # ── Anchor the mark to a document position ──────────────────────
            if mark_index:
                try:
                    self.editor.mark_set(mark_name, mark_index)
                except tk.TclError:
                    self.editor.mark_set(mark_name, self.editor.index(f"@{x_pos},{y_pos}"))
            else:
                self.editor.mark_set(mark_name, self.editor.index(f"@{x_pos},{y_pos}"))

            self.editor.mark_gravity(mark_name, "left")

            self.image_refs[img_name] = {
                "obj":      photo,
                "path":     path,
                "original": original_img,
                "width":    width,
                "height":   height,
                "mark":     mark_name,   
                "x_offset": x_pos        
            }
            
            theme = self.themes[self.current_theme]
            lbl = tk.Label(self.editor, image=photo, bd=0, cursor="fleur", bg=theme["bg"])
            lbl.image    = photo
            lbl.img_name = img_name

            lbl.bind("<Button-1>",      self.on_image_click)
            lbl.bind("<B1-Motion>",     self.on_image_drag)
            lbl.bind("<ButtonRelease-1>", self.on_drag_release)
            lbl.bind("<Button-3>",      self.show_image_menu)

            lbl.place(x=x_pos, y=y_pos)
            lbl.lift()

            self.root.after(10, self._reposition_images)

        except Exception as e:
            print(f"Error inserting image: {e}")

    def show_image_menu(self, event):
        self.active_image_label = event.widget
        self.image_menu.post(event.x_root, event.y_root)

    def resize_image(self, scale_factor):
        if not self.active_image_label: return
        lbl      = self.active_image_label
        img_name = lbl.img_name
        ref      = self.image_refs[img_name]
        new_w    = int(ref["width"]  * scale_factor)
        new_h    = int(ref["height"] * scale_factor)
        if new_w < 30 or new_w > 3000: return
        img_resized = ref["original"].resize((new_w, new_h), Image.LANCZOS)
        new_photo   = ImageTk.PhotoImage(img_resized)
        ref["width"]  = new_w
        ref["height"] = new_h
        ref["obj"]    = new_photo
        lbl.configure(image=new_photo)
        lbl.image = new_photo 

    def delete_image(self):
        if self.active_image_label:
            img_name = self.active_image_label.img_name
            ref = self.image_refs.get(img_name)
            if ref and ref.get("mark"):
                try:
                    self.editor.mark_unset(ref["mark"])
                except tk.TclError:
                    pass
            self.active_image_label.destroy()
            self.active_image_label = None

    # ── DRAG & DROP ─────────────────────────────────────────────────────────
    def on_image_click(self, event):
        self.dragging_image  = event.widget
        self.mouse_offset_x  = event.x
        self.mouse_offset_y  = event.y
        self.dragging_image.lift()

    def on_image_drag(self, event):
        if not self.dragging_image: return
        x = self.dragging_image.winfo_x() + event.x - self.mouse_offset_x
        y = self.dragging_image.winfo_y() + event.y - self.mouse_offset_y
        self.dragging_image.place(x=x, y=y)

    def on_drag_release(self, event):
        """After drag, update both x_offset and the document mark to the new position."""
        if not self.dragging_image: return

        img_name = self.dragging_image.img_name
        ref      = self.image_refs.get(img_name)

        if ref:
            new_x = self.dragging_image.winfo_x()
            new_y = self.dragging_image.winfo_y()

            ref["x_offset"] = new_x

            try:
                nearest = self.editor.index(f"@{new_x},{new_y}")
                self.editor.mark_set(ref["mark"], nearest)
            except tk.TclError:
                pass

        self.dragging_image = None

    # ── SAVE & LOAD ─────────────────────────────────────────────────────────
    def save_note(self, event=None):
        if not self.current_file: return "break"

        content_dump  = self.editor.dump("1.0", tk.END, text=True, tag=True)
        placed_images = []

        for child in self.editor.winfo_children():
            if not (isinstance(child, tk.Label) and hasattr(child, 'img_name')):
                continue
            img_name = child.img_name
            data     = self.image_refs[img_name]
            mark     = data.get("mark", "")

            # Persist the mark as a character index so reload is position-exact
            mark_index = ""
            if mark:
                try:
                    mark_index = self.editor.index(mark)
                except tk.TclError:
                    pass

            placed_images.append({
                "name":       img_name,
                "path":       data["path"],
                "x":          data.get("x_offset", child.winfo_x()),  # kept for compat
                "y":          child.winfo_y(),                         # kept for compat
                "mark_index": mark_index,   # primary positioning field
                "x_offset":   data.get("x_offset", child.winfo_x()),
                "width":      data["width"],
                "height":     data["height"]
            })

        custom_colors = {}
        custom_sizes  = {}
        for tag in self.editor.tag_names():
            if tag.startswith("color_"):
                custom_colors[tag] = self.editor.tag_cget(tag, "foreground")
            elif tag.startswith("size_"):
                try:
                    custom_sizes[tag]  = int(tag.split("_")[1])
                except IndexError:
                    pass

        package = {
            "dump":   content_dump,
            "colors": custom_colors,
            "sizes":  custom_sizes,
            "images": placed_images,
            "links":  self.link_map
        }

        with open(self.current_file, 'w') as f:
            json.dump(package, f)
        self.root.title(f"Nexus Notes - Saved: {os.path.basename(self.current_file)}")

        return "break"

    def load_note(self, event):
        item = self.tree.selection()
        if not item: return
        path = self.tree.item(item[0], "values")[0]

        if os.path.isdir(path) or not path.endswith(".json"):
            if os.path.isfile(path): os.startfile(path)
            return

        self.current_file = path
        self.editor.delete("1.0", tk.END)
        self.image_refs = {}
        self.link_map   = {}

        for child in self.editor.winfo_children():
            if isinstance(child, tk.Label) and hasattr(child, 'image'):
                child.destroy()

        with open(path, 'r') as f:
            data = json.load(f)

        self.apply_theme()
        self.link_map = data.get("links", {})

        for tag, color in data.get("colors", {}).items():
            self.editor.tag_configure(tag, foreground=color)
        for tag, size in data.get("sizes", {}).items():
            self.editor.tag_configure(tag, font=("Segoe UI", size))

        for entry_type, value, index in data.get("dump", []):
            if entry_type == "text":
                self.editor.insert(tk.END, value)
            elif entry_type == "tagon":
                if value not in ("sel", "current"):
                    self.tag_start = self.editor.index(tk.END + "-1c")
            elif entry_type == "tagoff":
                if value not in ("sel", "current"):
                    if value.startswith("link_") and value in self.link_map:
                        target = self.link_map[value]
                        self.editor.tag_configure(value, foreground="#0066cc", underline=True)
                        self.editor.tag_bind(value, "<Button-1>", lambda e, t=target: self.open_hyperlink(t))
                        self.editor.tag_bind(value, "<Enter>",  lambda e: self.editor.config(cursor="hand2"))
                        self.editor.tag_bind(value, "<Leave>",  lambda e: self.editor.config(cursor=""))
                    self.editor.tag_add(value, self.tag_start, tk.END + "-1c")

        for img_data in data.get("images", []):
            self._add_image_to_widget(
                img_data["path"],
                img_data.get("x_offset", img_data.get("x", 50)),
                img_data.get("y", 50),
                img_data.get("width",  300),
                img_data.get("height", None),
                mark_index=img_data.get("mark_index", None)   # None → compute from coords
            )

        # Wait for the layout to settle, then sync image positions
        self.root.after(50, self._reposition_images)

    # ── ALWAYS ON TOP TOGGLE ───────────────────────────────────────────
    def toggle_top(self):
        is_top = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not is_top)
        
        if not is_top:
            self.top_btn.config(text="📌 Float: ON", relief="sunken")
        else:
            self.top_btn.config(text="📌 Float: OFF", relief="flat")

    # ── DEBOUNCED AUTO SAVE ────────────────────────────────────────────
    def reset_autosave_timer(self, event):
        if not self.current_file:
            return
            
        if self.autosave_timer:
            self.root.after_cancel(self.autosave_timer)
            
        self.root.title(f"Nexus Notes - {os.path.basename(self.current_file)} (Typing...)")
        
        # Start a new timer for 2500 milliseconds (2.5 seconds)
        self.autosave_timer = self.root.after(2500, self.auto_save_trigger)
        
    def auto_save_trigger(self):
        self.save_note()
        self.autosave_timer = None

    # --- UTILS ---
    def toggle_tag(self, tag):
        try:
            if tag in self.editor.tag_names(tk.SEL_FIRST):
                self.editor.tag_remove(tag, tk.SEL_FIRST, tk.SEL_LAST)
            else:
                self.editor.tag_add(tag, tk.SEL_FIRST, tk.SEL_LAST)

            self.reset_autosave_timer(None)
        except: pass

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            tag = f"color_{color}"
            self.editor.tag_configure(tag, foreground=color)
            self.toggle_tag(tag)
            self.reset_autosave_timer(None)

    def add_folder(self):
        name = filedialog.asksaveasfilename(initialdir=self.db_path)
        if name: os.makedirs(name, exist_ok=True); self.refresh_sidebar()

    def add_note(self):
        path = filedialog.asksaveasfilename(initialdir=self.db_path, defaultextension=".json")
        if path:
            with open(path, 'w') as f: json.dump({}, f)
            self.refresh_sidebar()

    # --- RECURSIVE SIDEBAR FIX ---
    def refresh_sidebar(self):
        self.tree.delete(*self.tree.get_children())
        self._populate_tree("", self.db_path)

    def _populate_tree(self, parent, path):
        for item in sorted(os.listdir(path)):
            abs_path = os.path.join(path, item)
            node = self.tree.insert(parent, "end", text=item, values=(abs_path,))
            if os.path.isdir(abs_path):
                self._populate_tree(node, abs_path)

if __name__ == "__main__":
    root = tk.Tk()
    app  = NotesTime(root)
    root.mainloop()
#to change the file from .py to .exe
#pyinstaller --noconsole --onefile --name "Notes-Time" main.py
