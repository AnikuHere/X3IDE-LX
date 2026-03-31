#!/usr/bin/env python3
from random import random
import re
import tkinter as tk
from tkinter import scrolledtext, Menu, PanedWindow, font, filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys
import time
import urllib.request
import importlib.util
import webbrowser
import json
import requests
import difflib

sys.path.append(os.path.dirname(__file__))

### X3IDE By Raven Corvidae ###
### X3IDE: LX fork, optimized for Linux devices by DeniusGG on 31st of March, 2026 ###
### Last Modified: 29th of March 2026 by original author (Raven Corvidae) for original variant, 31st March 2026 by DeniusGG for LX fork (X3IDELX) ###
LAST_MODIFIED="31st March 2026"
VERSION=1.3

# SYNTAX HIGHLIGHTING CONSTANTS
KEYWORDS = r"\b(if|else|while|for|end|fncend|def|dev.debug|setclientrule|switch|case|default|repeat|return|try|catch|exit|call|w_file|r_file|a_file|del_file|create_dir|delete_dir|search_file|inp|cls|sys_info|set_env|reg|log|prt|fetch|wait|sqrt|add|sub|mul|div|mod|inc|dec)\b"
NUMBERS  = r"\b\d+(\.\d+)?\b"
STRINGS  = r"\"(\\.|[^\"])*\"|'(\\.|[^'])*'"
COMMENTS = r"//.*"
BOOLEANS = r"\b(true|false)\b"
VARIABLE = r"\$(\w+)"

def get_interpreter():
    base_dir = os.path.expanduser("~/.x3")
    cache_dir = os.path.join(base_dir, "cache")
    local_runner = os.path.join(base_dir, "run.py")
    cached_interpreter = os.path.join(cache_dir, "interpreterME.py")
    if os.path.isfile(local_runner):
        return local_runner
    os.makedirs(cache_dir, exist_ok=True)
    if os.path.isfile(cached_interpreter):
        return cached_interpreter
    try:
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/XFydro/x3/refs/heads/main/interpreterME.py",
            cached_interpreter
        )
        return cached_interpreter
    except Exception as e:
        raise RuntimeError(f"Could not download X3 interpreter:\n{e}")

def get_interpreter_type(path):
    if path.startswith(os.path.expanduser("~/.x3")) and not "cache" in path:
        return "Local"
    if "cache" in path:
        return "Cached"
    return "Custom"

def get_interpreter_version():
    path = get_interpreter()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VERSION"):
                    return line.split("=")[1].strip().strip('"').strip("'").split("#")[0].strip()
    except Exception as e:
        print(f"Error occurred while reading interpreter version: {e}")
        return "Unknown"

def get_settings_path():
    appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~/.config")
    base_dir = os.path.join(appdata, "X3IDE")
    os.makedirs(base_dir, exist_ok=True)
    settings_path = os.path.join(base_dir, "settings.json")
    if not os.path.exists(settings_path):
        default_settings = {
            "editor_theme": "dark",
            "console_theme": "dark",
            "font_size": 12,
            "auto_check_updates": True,
            "last_opened_files": []
        }
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=4)
    return settings_path

class X3IDE:
    def __init__(self, root, file_to_open=None):
        self.root = root
        self.root.title("X3IDELX")
        self.root.geometry("800x550")
        self.current_file = None
        self.processes = {}
        self.settings = json.load(open(get_settings_path(), "r", encoding="utf-8"))
        self.editor_font_size = self.settings.get("font_size", 12)
        self.console_font_size = self.settings.get("font_size", 12)
        self.console_tabs = {}
        self.tab_types = {} 
        self.current_search_term = None
        self.editor_theme = self.settings.get("editor_theme", "x3")
        self.console_theme = self.settings.get("console_theme", "x3")
        self.dirty = False
        self._setup_themes()
        self._build_ui()
        self._bind_keys()
        self._setup_tags()
        self._apply_editor_theme()
        self._apply_console_theme()
        if file_to_open:
            self.load_file(file_to_open)
        self.recent_files = self.settings.get("last_opened_files", [])
        self._rebuild_recent_menu()
        
        icon_path = os.path.join(os.path.dirname(__file__), "Logo.png")
        try:
            root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass
        if self.settings.get("auto_check_updates", True):
            self.root.after(2000, self.check_for_updates)

    def _setup_themes(self):
        self.themes = {
            "dark": {"name": "Dark Mode", "colors": {"bg": "#000000", "fg": "#ffffff", "input_bg": "#1a1a1a", "input_fg": "#ffffff", "frame_bg": "#101010", "root_bg": "#101010", "string": "#ffffff", "number": "#ffffff", "keyword": "#ffffff", "boolean": "#ffffff"}, "ui": {"border": "#ffffff", "font": ["Sixtyfour Convergence", 9], "cursor": "xterm"}},
            "light": {"name": "Light Mode", "colors": {"bg": "#f0f0f0", "fg": "#000000", "input_bg": "#ffffff", "input_fg": "#000000", "frame_bg": "#dddddd", "root_bg": "#dddddd", "string": "#000000", "number": "#000000", "keyword": "#000000", "boolean": "#000000"}, "ui": {"border": "#000000", "font": ["Arial", 11], "cursor": "arrow"}},
            "solarized": {"name": "Solarized", "colors": {"bg": "#002b36", "fg": "#839496", "input_bg": "#073642", "input_fg": "#eee8d5", "frame_bg": "#586e75", "root_bg": "#073642", "string": "#eee8d5", "number": "#cb4b16", "keyword": "#DD3D3D", "boolean": "#839400"}, "ui": {"border": "#cb4b16", "font": ["Courier New", 12, "bold"], "cursor": "dotbox"}},
            "monokai": {"name": "Monokai", "colors": {"bg": "#272822", "fg": "#f8f8f2", "input_bg": "#49483e", "input_fg": "#a6e22e", "frame_bg": "#3e3d32", "root_bg": "#272822", "string": "#6cc648", "number": "#f0254b", "keyword": "#be6eff", "boolean": "#ff7e29"}, "ui": {"border": "#75715e", "font": ["Consolas", 12], "cursor": "pirate"}},
            "x3": {"name": "X3 Default", "colors": {"bg": "#101010", "fg": "#00efc9", "input_bg": "#6a50ff", "input_fg": "#5dffe4", "frame_bg": "#101010", "root_bg": "#101010", "string": "#70d2ff", "number": "#00efc9", "keyword": "#ffffff", "boolean": "#ffff34"}, "ui": {"border": "#00efc9", "font": ["Berlin Sans FB", 12], "cursor": "xterm"}},
        }

    def _build_ui(self):
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Run File", command=self.run_file)
        file_menu.add_command(label="Open Settings", command=self.open_settings)
        file_menu.add_command(label="Info...", command=self.display_info)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.confirm_exit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        self.recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.editor_frame = tk.Frame(self.notebook)
        self.editor = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.NONE, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.bind("<<Modified>>", self._on_edit)
        self.editor.bind("<KeyRelease>", self.highlight_syntax)
        self.notebook.add(self.editor_frame, text="Editor")
        self.tab_types[str(self.editor_frame)] = "editor"
        
        self.interpreter_bar = tk.Label(self.root, text="", anchor="w", padx=8)
        self.interpreter_bar_visible = False
        self.update_interpreter_bar()

    def new_file(self):
        self.editor.delete("1.0", tk.END)
        self.current_file, self.dirty = None, False
        self.root.title("X3IDELX")

    def open_file(self):
        if self.dirty and not messagebox.askyesno("Unsaved Changes", "Open file anyway?"): return
        path = filedialog.askopenfilename(filetypes=[("X3 Files", "*.x3"), ("All", "*.*")])
        if path: self.load_file(path)

    def load_file(self, path):
        self.add_recent_file(path)
        with open(path, "r", encoding="utf-8") as f:
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", f.read())
        self.current_file, self.dirty = path, False
        self.root.title(f"X3IDELX - {os.path.basename(path)}")
        self.highlight_syntax()

    def save_file(self):
        if not self.current_file: self.save_file_as(); return
        with open(self.current_file, "w", encoding="utf-8") as f: 
            f.write(self.editor.get("1.0", "end-1c"))
        self.dirty = False
        self.root.title(f"X3IDELX - {os.path.basename(self.current_file)}")

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".x3")
        if path: 
            self.current_file = path
            self.save_file()
            self.add_recent_file(path)

    def run_file(self):
        if not self.current_file:
            messagebox.showerror("No file", "Save the file first.")
            return
        tab = tk.Frame(self.notebook)
        output = scrolledtext.ScrolledText(tab, state=tk.DISABLED)
        toolbar = tk.Frame(tab); toolbar.pack(fill=tk.X)
        status = tk.Label(toolbar, text="Running", fg="green"); status.pack(side=tk.RIGHT, padx=6)
        entry = tk.Entry(tab); entry.pack(fill=tk.X); output.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(tab, text=f"Run: {os.path.basename(self.current_file)}")
        tab_id = self.notebook.tabs()[-1]; self.tab_types[tab_id] = "console"; self.notebook.select(tab)
        
        cmd = ["python3", get_interpreter(), "-f", self.current_file]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.console_tabs[tab] = {"output": output, "entry": entry, "process": proc, "running": True, "status": status}

        def reader(pipe, target_tab):
            while target_tab in self.console_tabs:
                line = pipe.readline()
                if not line: break
                output.config(state=tk.NORMAL); output.insert(tk.END, line); output.see(tk.END); output.config(state=tk.DISABLED)
            if target_tab in self.console_tabs:
                self.console_tabs[target_tab]["running"] = False
                status.config(text="Stopped", fg="red")

        threading.Thread(target=reader, args=(proc.stdout, tab), daemon=True).start()
        threading.Thread(target=reader, args=(proc.stderr, tab), daemon=True).start()
        
        entry.bind("<Return>", lambda e: (proc.stdin.write(entry.get() + "\n"), proc.stdin.flush(), entry.delete(0, tk.END)))
        
        tk.Button(toolbar, text="Stop", command=lambda: self.stop_console(tab)).pack(side=tk.LEFT)
        tk.Button(toolbar, text="Close", command=lambda: self.close_console_tab(tab)).pack(side=tk.LEFT)

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        tk.Label(win, text="Editor Theme").pack()
        ed_var = tk.StringVar(value=self.editor_theme)
        ttk.Combobox(win, textvariable=ed_var, values=list(self.themes.keys())).pack()
        def apply():
            self.editor_theme = ed_var.get()
            self._apply_editor_theme(); win.destroy()
        tk.Button(win, text="Save", command=apply).pack()

    def highlight_syntax(self, event=None):
        text = self.editor.get("1.0", "end-1c")
        for tag in ("keyword", "number", "boolean", "comment", "variable", "string"):
            self.editor.tag_remove(tag, "1.0", "end")
        patterns = [(BOOLEANS, "boolean"), (NUMBERS, "number"), (KEYWORDS, "keyword"), (VARIABLE, "variable"), (STRINGS, "string"), (COMMENTS, "comment")]
        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                self.editor.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def _setup_tags(self):
        c = self.themes[self.editor_theme]["colors"]
        tag_colors = {"keyword": c["keyword"], "number": c["number"], "boolean": c["boolean"], "variable": c["boolean"], "string": c["string"], "comment": "#7F7F7F"}
        for tag, color in tag_colors.items():
            self.editor.tag_configure(tag, foreground=color)

    def _apply_editor_theme(self):
        t = self.themes[self.editor_theme]
        f = font.Font(family=t["ui"]["font"][0], size=t["ui"]["font"][1])
        self.editor.configure(bg=t["colors"]["bg"], fg=t["colors"]["fg"], insertbackground=t["colors"]["fg"], font=f)
        self._setup_tags(); self.highlight_syntax()

    def _apply_console_theme(self):
        t = self.themes[self.console_theme]
        size = getattr(self, 'console_font_size', 12)
        f = font.Font(family=t["ui"]["font"][0], size=size)
        for w in self.console_tabs.values():
            w["output"].configure(bg=t["colors"]["bg"], fg=t["colors"]["fg"], font=f)
            w["entry"].configure(bg=t["colors"]["input_bg"], fg=t["colors"]["input_fg"], font=f)

    def _on_edit(self, event):
        if not self.dirty:
            self.dirty = True
            self.root.title("● " + self.root.title())
        self.editor.edit_modified(False)

    def on_tab_changed(self, event):
        tab_id = event.widget.select()
        if self.tab_types.get(tab_id) == "console":
            self.show_interpreter_bar(); self.update_interpreter_bar()
        else:
            self.hide_interpreter_bar()

    def show_interpreter_bar(self):
        if not self.interpreter_bar_visible: self.interpreter_bar.pack(side=tk.BOTTOM, fill=tk.X); self.interpreter_bar_visible = True

    def update_interpreter_bar(self):
        path, version = get_interpreter(), get_interpreter_version()
        self.interpreter_bar.config(text=f"X3 v{version} | {get_interpreter_type(path)} | Python {sys.version.split()[0]}")

    def hide_interpreter_bar(self):
        if self.interpreter_bar_visible: self.interpreter_bar.pack_forget(); self.interpreter_bar_visible = False

    def add_recent_file(self, path):
        if path in self.recent_files: self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]
        self._rebuild_recent_menu(); self.save_settings()

    def _rebuild_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for path in self.recent_files:
            self.recent_menu.add_command(label=os.path.basename(path), command=lambda p=path: self.load_file(p))

    def save_settings(self):
        path = get_settings_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    def check_for_updates(self, manual=False):
        url = "https://raw.githubusercontent.com/XFydro/X3IDE/refs/heads/main/X3IDE.py"
        try:
            res = requests.get(url, timeout=5)
            remote_version = None
            for line in res.text.splitlines():
                if line.startswith("VERSION"):
                    remote_version = line.split("=")[1].strip().strip('"').strip("'")
                    break
            if remote_version and remote_version > str(VERSION) and manual:
                messagebox.showinfo("Update", f"New version {remote_version} available.")
        except: pass

    def stop_console(self, tab):
        info = self.console_tabs.get(tab)
        if info and info["running"]:
            info["process"].kill(); info["running"] = False; info["status"].config(text="Stopped", fg="red")

    def close_console_tab(self, tab):
        self.stop_console(tab); del self.console_tabs[tab]; self.notebook.forget(tab)

    def display_info(self):
        info_text = f"X3IDELX (Linux Fork)\nAuthor: Raven Corvidae\nLX Fork developer: DeniusGG\nModified: {LAST_MODIFIED}"
        messagebox.showinfo("About X3IDELX", info_text)

    def confirm_exit(self):
        if not self.dirty or messagebox.askyesno("Unsaved Changes", "Exit anyway?"): self.root.quit()

    def _bind_keys(self):
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-r>", lambda e: self.run_file())
        self.root.bind("<Control-q>", lambda e: self.confirm_exit())

if __name__ == "__main__":
    root = tk.Tk()
    X3IDE(root)
    root.mainloop()
