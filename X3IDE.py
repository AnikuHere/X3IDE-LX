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
### Last Modified: 29th March 2026 ###
LAST_MODIFIED="29th March 2026"
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
    base_dir = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "X3IDE"
    )

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
def get_license_path():
    base_dir = os.path.join(os.getenv("LOCALAPPDATA"), "X3IDE")
    os.makedirs(base_dir, exist_ok=True)

    license_path = os.path.join(base_dir, "license.txt")
    url = "https://raw.githubusercontent.com/XFydro/X3IDE/main/LICENSE"

    try:
        remote_text = requests.get(url, timeout=5).text
    except:
        return license_path 

    if not os.path.exists(license_path):
        with open(license_path, "w", encoding="utf-8") as f:
            f.write(remote_text)
    else:
        with open(license_path, "r", encoding="utf-8") as f:
            local_text = f.read()

        if local_text != remote_text:
            with open(license_path, "w", encoding="utf-8") as f:
                f.write(remote_text)

    return license_path

class X3IDE:
    def __init__(self, root, file_to_open=None):
        self.root = root
        self.root.title("X3 IDE")
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
        self.dirty=False
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
        icon =os.path.join(sys._MEIPASS, "Logo.png") if getattr(sys, "frozen", False) else os.path.join(os.path.dirname(__file__), "Logo.png")
        root.iconphoto(True, tk.PhotoImage(file=icon))
        if self.settings.get("auto_check_updates", True):
            self.root.after(2000, self.check_for_updates)
    # Update Check
    def check_for_updates(self, manual=False):
        url = "https://raw.githubusercontent.com/XFydro/X3IDE/refs/heads/main/X3IDE.py"

        try:
            import requests

            res = requests.get(url, timeout=5)
            text = res.text
            remote_version = None
            for line in text.splitlines():
                if line.startswith("VERSION"):
                    remote_version = line.split("=")[1].strip().strip('"').strip("'")
                    break

            if not remote_version:
                if manual:
                    messagebox.showerror("Update Check", "VERSION not found in remote file.")
                return
            def parse(v):
                try:
                    return tuple(int(x) for x in str(v).split("."))
                except:
                    return (0,)

            local_v = parse(VERSION)
            remote_v = parse(remote_version)
            if remote_v > local_v:
                msg = f"Update available!\n\nCurrent: {VERSION}\nLatest: {remote_version}"
                title = "Update Available"
            elif remote_v == local_v:
                msg = f"You are up to date.\n\nVersion: {VERSION}"
                title = "Up to Date"
            else:
                msg = f"You are on a newer/dev version.\n\nCurrent: {VERSION}\nLatest: {remote_version}"
                title = "Dev Version"
            if manual:
                messagebox.showinfo(title, msg)
            else:
                if remote_v > local_v:
                    messagebox.showinfo(title, msg)

        except Exception as e:
            if manual:
                messagebox.showerror("Update Check Failed", str(e))
    # THEMES
    def set_editor_theme(self, name):
        self.editor_theme = name
        self._apply_editor_theme()

    def set_console_theme(self, name):
        self.console_theme = name
        self._apply_console_theme()

    def save_settings(self):
        path = get_settings_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)
    def _setup_themes(self):
        """Theme Format v1.9:
            "name": {
                "name": "Display_Name",
                "colors": {
                    "bg": "#000000",          # background
                    "fg": "#000000",          # text / heading
                    "input_bg": "#000000",    # input entry
                    "input_fg": "#000000",    # input text color for good contrast
                    "frame_bg": "#000000",    # input frame / outer box
                    "root_bg": "#000000"      # root background same as bg
                    "string": "#000000",      # string literal color
                    "number": "#000000",      # number literal color
                    "keyword": "#000000",     # keywords color
                    "boolean": "#000000"      # boolean literal color
                },
                "ui": {
                    "border": "#000000",      # border color for frames
                    "font": ("font_name_on_ur_pc", 11), # font name and size
                    "cursor": "arrow"         # cursor style
                }
            },        

        """
        self.themes = {
"dark": {
"name": "Dark Mode",
"colors": {
"bg": "#000000",
"fg": "#ffffff",
"input_bg": "#1a1a1a",
"input_fg": "#ffffff",
"frame_bg": "#101010",
"root_bg": "#101010",

"string": "#ffffff",
"number": "#ffffff",
"keyword": "#ffffff",
"boolean": "#ffffff"
},
"ui": {
"border": "#ffffff",
"font": ["Sixtyfour Convergence", 9],
"cursor": "xterm"
}
},
"light": {
"name": "Light Mode",
"colors": {
"bg": "#f0f0f0",
"fg": "#000000",
"input_bg": "#ffffff",
"input_fg": "#000000",
"frame_bg": "#dddddd",
"root_bg": "#dddddd",

"string": "#000000",
"number": "#000000",
"keyword": "#000000",
"boolean": "#000000"
},
"ui": {
"border": "#000000",
"font": ["Arial", 11],
"cursor": "arrow"
}
},
"solarized": {
"name": "Solarized",
"colors": {
"bg": "#002b36",
"fg": "#839496",
"input_bg": "#073642",
"input_fg": "#eee8d5",
"frame_bg": "#586e75",
"root_bg": "#073642",

"string": "#eee8d5",
"number": "#cb4b16",
"keyword": "#DD3D3D",
"boolean": "#839400"    
},
"ui": {
"border": "#cb4b16",
"font": ["Courier New", 12, "bold"],
"cursor": "dotbox"
}
},
"monokai": {
"name": "Monokai",
"colors": {
"bg": "#272822",
"fg": "#f8f8f2",
"input_bg": "#49483e",
"input_fg": "#a6e22e",
"frame_bg": "#3e3d32",
"root_bg": "#272822",

"string": "#6cc648",
"number": "#f0254b",
"keyword": "#be6eff",
"boolean": "#ff7e29"
},
"ui": {
"border": "#75715e",
"font": ["Consolas", 12],
"cursor": "pirate"
}
},
"gruvbox": {
"name": "Gruvbox",
"colors": {
"bg": "#000000",
"fg": "#ebdbb2",
"input_bg": "#3c3836",
"input_fg": "#d5c4a1",
"frame_bg": "#504945",
"root_bg": "#282828",

"string": "#ffffff",
"number": "#0000ff",
"keyword": "#ff0000",
"boolean": "#00ff00"
},
"ui": {
"border": "#1d2021",
"font": ["Fixedsys", 11],
"cursor": "heart"
}
},
"neon": {
"name": "Midnight Neon",
"colors": {
"bg": "#0f0f1f",
"fg": "#39ff14",
"input_bg": "#1a1a2f",
"input_fg": "#ff00ff",
"frame_bg": "#202040",
"root_bg": "#0f0f1f",

"string": "#ff00ff",
"number": "#39ff14",
"keyword": "#ff00f0",
"boolean": "#39ff00"
},
"ui": {
"border": "#39ff14",
"font": ["OCR A Extended", 10],
"cursor": "plus"
}
},
"matrix": {
"name": "Matrix",
"colors": {
"bg": "#000000",
"fg": "#00ff00",
"input_bg": "#001100",
"input_fg": "#00ff00",
"frame_bg": "#002200",
"root_bg": "#000000",

"string": "#00ff00",
"number": "#00ff00",
"keyword": "#008400",
"boolean": "#00ff00"
},
"ui": {
"border": "#00ff00",
"font": ["Courier New", 10],
"cursor": "trek"
}
},
"pastel": {
"name": "Pastel Dream",
"colors": {
"bg": "#fbeaff",
"fg": "#7e5a9b",
"input_bg": "#f0d9ff",
"input_fg": "#7e5a9b",
"frame_bg": "#fad0c9",
"root_bg": "#fbeaff",

"string": "#7e5a9b",
"number": "#7e5a9b",
"keyword": "#ffae00",
"boolean": "#7e5a00"
},
"ui": {
"border": "#7e5a9b",
"font": ["Bradley Hand ITC", 17],
"cursor": "star"
}
},
"void": {
"name": "The Void",
"colors": {
"bg": "#000000", "fg": "#444444",
"input_bg": "#111111", "input_fg": "#333333",
"frame_bg": "#0a0a0a", "root_bg": "#000000",
"string": "#333333",
"number": "#222222",
"keyword": "#444444",
"boolean": "#444444"
}
,
"ui": {
"border": "#222222",
"font": ["Terminus", 9],
"cursor": "target"
}
},
"clownfiesta": {
"name": "Clown Fiesta",
"colors": {
"bg": "#ff00ff", "fg": "#00ffff",
"input_bg": "#ffff00", "input_fg": "#0000ff",
"frame_bg": "#ff8800", "root_bg": "#ff00ff",
"string": "#0000ff",
"number": "#00ff00",
"keyword": "#00ffff",
"boolean": "#00ff00"
},
"ui": {
"border": "#00ff00",
"font": ["Impact", 12, "bold"],
"cursor": "spider"
}
},
"terminal": {
"name": "Retro Terminal",
"colors": {
"bg": "#1e1e1e", "fg": "#00ffcc",
"input_bg": "#2a2a2a", "input_fg": "#ffffff",
"frame_bg": "#333333", "root_bg": "#1e1e1e",
"string": "#ffffff",
"number": "#00ffcc",
"keyword": "#0084ff",
"boolean": "#00ff00"
},
"ui": {
"border": "#00ffcc",
"font": ["Terminal", 10],
"cursor": "tcross"
}
},
"cottoncandy": {
"name": "Cotton Candy",
"colors": {
"bg": "#ffccf9", "fg": "#6a0572",
"input_bg": "#ffe4fa", "input_fg": "#7e5a9b",
"frame_bg": "#ffc8dd", "root_bg": "#ffccf9",
"string": "#7e5a9b",
"number": "#b186c9",
"keyword": "#6a0572",
"boolean": "#6a0500"
}
,
"ui": {
"border": "#e0aaff",
"font": ["Comic Sans MS", 11],
"cursor": "dot"
}
},
"brutalist": {
"name": "Brutalist UI",
"colors": {
"bg": "#ffffff", "fg": "#000000",
"input_bg": "#eeeeee", "input_fg": "#000000",
"frame_bg": "#dddddd", "root_bg": "#ffffff",
"string": "#000000",
"number": "#000000",
"keyword": "#000000",
"boolean": "#000000"
}
,
"ui": {
"border": "#000000",
"font": ["Helvetica", 9, "bold"],
"cursor": "cross"
}
},
"shrekcore": {
"name": "Shrekcore",
"colors": {
"bg": "#395d00", "fg": "#affc41",
"input_bg": "#4c7c0c", "input_fg": "#d0ff8c",
"frame_bg": "#2d3e00", "root_bg": "#395d00",
"string": "#d0ff8c",
"number": "#7bb661",
"keyword": "#affc41",
"boolean": "#affc00"
}
,
"ui": {
"border": "#7bb661",
"font": ["Papyrus", 10],
"cursor": "exchange"
}
},
"mirrorverse": {
"name": "Mirrorverse",
"colors": {
"bg": "#ffffff", "fg": "#000000",
"input_bg": "#000000", "input_fg": "#000000",
"frame_bg": "#222222", "root_bg": "#ffffff",
"string": "#000000",
"number": "#aaaaaa",
"keyword": "#000000",
"boolean": "#000000"
}
,
"ui": {
"border": "#aaaaaa",
"font": ["Segoe UI", 10, "italic"],
"cursor": "sizing"
}
},
"depressionos": {
"name": "depressionOS",
"colors": {
"bg": "#1a1a1a", "fg": "#5f5f5f",
"input_bg": "#2b2b2b", "input_fg": "#8f8f8f",
"frame_bg": "#1f1f1f", "root_bg": "#1a1a1a",
"string": "#8f8f8f",
"number": "#404040",
"keyword": "#5f5f5f",
"boolean": "#5f5f00"
}
,
"ui": {
"border": "#404040",
"font": ["Lucida Console", 9],
"cursor": "circle"
}
},
"synthwave": {
"name": "Synthwave '84",
"colors": {
"bg": "#2b213a", "fg": "#f8f8f2",
"input_bg": "#3e2d54", "input_fg": "#ff79c6",
"frame_bg": "#1e152a", "root_bg": "#2b213a",
"string": "#ff79c6",
"number": "#ff79c6",
"keyword": "#ff47ed",
"boolean": "#f8f800"
}
,
"ui": {
"border": "#ff79c6",
"font": ["Copperplate Gothic Light", 11],
"cursor": "spraycan"
}
},
"MorningSkyLight": {
"name": "Morning Skylight",
"colors": {
"bg": "#e0f7fa", "fg": "#006064",
"input_bg": "#ffffff", "input_fg": "#004d40",
"frame_bg": "#b2ebf2", "root_bg": "#e0f7fa",
"string": "#004d40",
"number": "#4dd0e1",
"keyword": "#003E40",
"boolean": "#006000"
}
,
"ui": {
"border": "#4dd0e1",
"font": ["Verdana", 10],
"cursor": "hand2"
}
},
"meowmix": {
"name": "MeowMix",
"colors": {
"bg": "#ffe0f0", "fg": "#333333",
"input_bg": "#fff0fa", "input_fg": "#c71585",
"frame_bg": "#ffc0cb", "root_bg": "#ffe0f0",
"string": "#c71585",
"number": "#ff69b4",
"keyword": "#333333",
"boolean": "#333300"
}
,
"ui": {
"border": "#ff69b4",
"font": ["Century Gothic", 10, "italic"],
"cursor": "mouse"
}
},
"cyberpunk": {
"name": "Cyberpunk",
"colors": {
"bg": "#0f0f0f",
"fg": "#00ffcc",
"input_bg": "#1a1a1a",
"input_fg": "#ff00ff",
"frame_bg": "#202020",
"root_bg": "#0f0f00",

"string": "#ff00ff",
"number": "#00ffcc",
"keyword": "#0400FF",
"boolean": "#0084FF"
},
"ui": {
"border": "#00ffcc",
"font": ["Courier New", 10],
"cursor": "xterm"
}
},
"x3": {
"name": "X3 Default",
"colors": {
"bg": "#101010", "fg": "#00efc9",
"input_bg": "#6a50ff", "input_fg": "#5dffe4",
"frame_bg": "#101010", "root_bg": "#101010",
"string": "#70d2ff",
"number": "#00efc9",
"keyword": "#ffffff",
"boolean": "#ffff34"
}
,
"ui": {
"border": "#00efc9",
"font": ["Berlin Sans FB", 12],
"cursor": "xterm"
}
},
"sunset": {
"name": "Sunset Bliss",
"colors": {
"bg": "#ffcccb", "fg": "#2c2c54",
"input_bg": "#ffe4e1", "input_fg": "#ff6b81",
"frame_bg": "#ffd1dc", "root_bg": "#ffcccb",
"string": "#de2e48",
"number": "#ff6b81",
"keyword": "#2c2c54",
"boolean": "#2c2c00"
}
,
"ui": {
"border": "#ff6b81",
"font": ["Georgia", 11],
"cursor": "circle"
}
},
"vaporwave": {
"name": "Vaporwave",
"colors": {
"bg": "#fdf6e3", "fg": "#d33682",
"input_bg": "#eee8d5", "input_fg": "#6c71c4",
"frame_bg": "#fdf6e3", "root_bg": "#fdf6e3",
"string": "#6c71c4",
"number": "#cb4b16",
"keyword": "#d33682",
"boolean": "#d33600"
}
,
"ui": {
"border": "#cb4b16",
"font": ["Fira Code", 12],
"cursor": "exchange"
}
},
"hell": {
"name": "Hellfire Red",
"colors": {
"bg": "#1a0000", "fg": "#ff1a1a",
"input_bg": "#330000", "input_fg": "#ff4d4d",
"frame_bg": "#4d0000", "root_bg": "#1a0000",
"string": "#ff4d4d",
"number": "#ff3333",
"keyword": "#ff1a1a",
"boolean": "#ff0000"
}
,
"ui": {
"border": "#ff3333",
"font": ["Impact", 12],
"cursor": "man"
}
},
"bubblegum": {
"name": "Bubblegum",
"colors": {
"bg": "#ffc1cc", "fg": "#6a0572",
"input_bg": "#ffddee", "input_fg": "#7e5a9b",
"frame_bg": "#ffe0f0", "root_bg": "#ffc1cc",
"string": "#7e5a9b",
"number": "#ff69b4",
"keyword": "#6a0572",
"boolean": "#ff00d9"
}
,
"ui": {
"border": "#ff69b4",
"font": ["Comic Sans MS", 11],
"cursor": "heart"
}
},
"raincode": {
"name": "Raincode",
"colors": {
"bg": "#0f2027", "fg": "#2c5364",
"input_bg": "#203a43", "input_fg": "#fefefe",
"frame_bg": "#2c5364", "root_bg": "#0f2027",
"string": "#fefefe",
"number": "#66fcf1",
"keyword": "#558093",
"boolean": "#2c5300"
}
,
"ui": {
"border": "#66fcf1",
"font": ["Juice ITC", 16],
"cursor": "pencil"
}
},
"pixelpunk": {
"name": "Pixel Punk",
"colors": {
"bg": "#1b1b2f", "fg": "#e43f5a",
"input_bg": "#162447", "input_fg": "#e43f5a",
"frame_bg": "#1f4068", "root_bg": "#1b1b2f",
"string": "#ec5871",
"number": "#ff1b1b",
"keyword": "#ff0040",
"boolean": "#e95419"
}
,
"ui": {
"border": "#e43f5a",
"font": ["OCR A Extended", 13],
"cursor": "cross"
}
},
"lemonade": {
"name": "Lemonade",
"colors": {
"bg": "#fffacd", "fg": "#333300",
"input_bg": "#ffffe0", "input_fg": "#9bb545",
"frame_bg": "#f5f5dc", "root_bg": "#fffacd",
"string": "#7a9e2d",
"number": "#cccc00",
"keyword": "#FFFF00",
"boolean": "#1DAF35"
}
,
"ui": {
"border": "#cccc00",
"font": ["Verdana", 11],
"cursor": "hand2"
}
},
"oceanic": {
"name": "Oceanic Depths",
"colors": {
"bg": "#011627", "fg": "#2ec4b6",
"input_bg": "#003049", "input_fg": "#00a8e8",
"frame_bg": "#012a4a", "root_bg": "#011627",
"string": "#00a8e8",
"number": "#90e0ef",
"keyword": "#2ec4b6",
"boolean": "#000d57"
}
,
"ui": {
"border": "#90e0ef",
"font": ["Consolas", 11],
"cursor": "shuttle"
}
},
"dreamscape": {
"name": "Dreamscape",
"colors": {
"bg": "#2c2743", "fg": "#cba6f7",
"input_bg": "#2d2a4a", "input_fg": "#e0aaff",
"frame_bg": "#3b3a5c", "root_bg": "#1f1c2c",
"string": "#e0aaff",
"number": "#f38ba8",
"keyword": "#cba6f7",
"boolean": "#cba600"
}
,
"ui": {
"border": "#f38ba8",
"font": ["Georgia", 12],
"cursor": "dotbox"
}
},
"forestwitch": {
"name": "Forest Witch",
"colors": {
"bg": "#0b3d0b", "fg": "#a1ffce",
"input_bg": "#1a4d1a", "input_fg": "#caffbf",
"frame_bg": "#2b6e2b", "root_bg": "#0b3d0b",
"string": "#caffbf",
"number": "#90ee90",
"keyword": "#a1ffce",
"boolean": "#a1ff00"
}
,
"ui": {
"border": "#90ee90",
"font": ["Garamond", 11],
"cursor": "target"
},
},
"amethyst_twilight": {
"name": "Amethyst Twilight",
"colors": {
"bg": "#50207C", "fg": "#FF006A",
"input_bg": "#73C2BE", "input_fg": "#FF006A",
"frame_bg": "#73EEDC", "root_bg": "#997EB3",
"string": "#EA00FF",
"number": "#F046FF",
"keyword": "#C587D1",
"boolean": "#C800E2"
}
,
"ui": {
"border": "#5F1A37",
"font": ["Consolas", 11],
"cursor": "arrow"
}
},
"orange_burn": {
"name": "Orange Burn",
"colors": {
"bg": "#000000", "fg": "#FF5F1F",
"input_bg": "#1a1a1a", "input_fg": "#FF6F2C",
"frame_bg": "#262626", "root_bg": "#ff7b00",
"string": "#FF6E0D",
"number": "#FF9E78",
"keyword": "#FF2600",
"boolean": "#FF9100"
}
,
"ui": {
"border": "#FF5F1F",
"font": ["Bodoni MT", 11],
"cursor": "pirate"
}
}


}
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("320x260")
        win.resizable(False, False)

        frame = tk.Frame(win, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Editor Theme ---
        tk.Label(frame, text="Editor Theme").pack(anchor="w")
        editor_theme_var = tk.StringVar(value=self.settings.get("editor_theme", "dark"))
        editor_theme_menu = ttk.Combobox(
            frame,
            textvariable=editor_theme_var,
            values=list(self.themes.keys()),
            state="readonly"
        )
        editor_theme_menu.pack(fill=tk.X, pady=4)

        # --- Console Theme ---
        tk.Label(frame, text="Console Theme").pack(anchor="w")
        console_theme_var = tk.StringVar(value=self.settings.get("console_theme", "dark"))
        console_theme_menu = ttk.Combobox(
            frame,
            textvariable=console_theme_var,
            values=list(self.themes.keys()),
            state="readonly"
        )
        console_theme_menu.pack(fill=tk.X, pady=4)

        # --- Font Size ---
        tk.Label(frame, text="Font Size").pack(anchor="w")
        font_var = tk.IntVar(value=self.settings.get("font_size", 12))
        font_spin = tk.Spinbox(frame, from_=8, to=32, textvariable=font_var)
        font_spin.pack(fill=tk.X, pady=4)

        # --- Auto Update ---
        auto_update_var = tk.BooleanVar(value=self.settings.get("auto_check_updates", True))
        tk.Checkbutton(
            frame,
            text="Auto Check Updates",
            variable=auto_update_var
        ).pack(anchor="w", pady=6)

        # --- Buttons ---
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        def save_settings():
            self.settings["editor_theme"] = editor_theme_var.get()
            self.settings["console_theme"] = console_theme_var.get()
            self.settings["font_size"] = font_var.get()
            self.settings["auto_check_updates"] = auto_update_var.get()

            # Apply instantly
            self.editor_theme = self.settings["editor_theme"]
            self.console_theme = self.settings["console_theme"]
            self.editor_font_size = self.settings["font_size"]
            self.console_font_size = self.settings["font_size"]

            self._apply_editor_theme()
            self._apply_console_theme()
            self.save_settings()

            win.destroy()

        tk.Button(btn_frame, text="Save", command=save_settings).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    # Syntax Highlighting
    def _setup_tags(self):
        c = self.themes[self.editor_theme]["colors"]

        tag_colors = {
            "keyword": c["keyword"],
            "number": c["number"],
            "boolean": c["boolean"],
            "variable": c["boolean"],
            "string": c["string"],
            "comment": "#7F7F7F",
        }

        for tag, color in tag_colors.items():
            self.editor.tag_configure(tag, foreground=color)

        self.editor.tag_configure("search_highlight", background="#4444aa")


    def highlight_syntax(self, event=None):
        text = self.editor.get("1.0", "end-1c")

        # Remove previous highlighting
        for tag in ("keyword", "number", "boolean", "comment", "variable", "string"):
            self.editor.tag_remove(tag, "1.0", "end")

        patterns = [
            (BOOLEANS, "boolean"),
            (NUMBERS, "number"),
            (KEYWORDS, "keyword"),
            (VARIABLE, "variable"),
            (STRINGS, "string"),
            (COMMENTS, "comment"),
        ]

        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.editor.tag_add(tag, start, end)

        if self.current_search_term:
            self.highlight_search(self.current_search_term)


    def highlight_search(self, term):
        if not term:
            # Clear search highlights if term is empty
            self.editor.tag_remove("search_highlight", "1.0", "end")
            return


        # Clear old search highlights (FIXES your bug)
        self.editor.tag_remove("search_highlight", "1.0", "end")

        start = "1.0"

        while True:
            pos = self.editor.search(term, start, stopindex="end")

            if not pos:
                break

            end = f"{pos}+{len(term)}c"
            self.editor.tag_add("search_highlight", pos, end)

            start = end
    # UI
    def _build_ui(self):
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.root.option_add('*tearOff', False)

        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Run File",command=lambda: self.run_file())
        file_menu.add_command(label="Open Settings", command=self.open_settings)
        file_menu.add_command(label="Info...", command=self.display_info)
        self.interpreter_bar = tk.Label(
            root,
            text="",
            anchor="w",
            padx=8)
        self.interpreter_bar_visible = False

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.confirm_exit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)


        pref_menu = Menu(self.menu_bar, tearoff=0)
        editor_theme_menu = Menu(pref_menu, tearoff=0)
        console_theme_menu = Menu(pref_menu, tearoff=0)

        for x in self.themes:
            editor_theme_menu.add_command(
                label=self.themes[x]["name"],
                command=lambda n=x: self.set_editor_theme(n)
            )
            console_theme_menu.add_command(
                label=self.themes[x]["name"],
                command=lambda n=x: self.set_console_theme(n)
            )


        pref_menu.add_cascade(label="Editor Theme", menu=editor_theme_menu)
        pref_menu.add_cascade(label="Console Theme", menu=console_theme_menu)
        pref_menu.add_separator()
        pref_menu.add_command(label="Editor Font +", command=self.editor_font_up)
        pref_menu.add_command(label="Editor Font -", command=self.editor_font_down)
        pref_menu.add_command(label="Console Font +", command=self.console_font_up)
        pref_menu.add_command(label="Console Font -", command=self.console_font_down)

        self.menu_bar.add_cascade(label="Preferences", menu=pref_menu)
        self.recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.editor_frame = tk.Frame(self.notebook)
        self.editor = scrolledtext.ScrolledText(
            self.editor_frame, wrap=tk.NONE, undo=True
        )
        self.editor.pack(fill=tk.BOTH, expand=True)

        self.dirty = False
        self.editor.bind("<<Modified>>", self._on_edit)

        self.editor.bind("<KeyRelease>", self.highlight_syntax)

        self.notebook.add(self.editor_frame,text="Editor")
        self.tab_types[str(self.editor_frame)] = "editor"

        self._apply_editor_theme()
        self._apply_console_theme()
        self.editor.focus_set()
        self.update_interpreter_bar()
    def on_tab_changed(self, event):
        tab_id = event.widget.select()
        if not tab_id:
            self.hide_interpreter_bar()
            return

        tab_type = self.tab_types.get(tab_id)

        if tab_type == "console":
            self.show_interpreter_bar()
            self.update_interpreter_bar()
        else:
            self.hide_interpreter_bar()

    def _on_edit(self, event):
        if not self.dirty:
            self.dirty = True
            title = self.root.title()
            if not title.startswith("●"):
                self.root.title("● " + title)
        self.editor.edit_modified(False)

    def _rebuild_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for path in self.recent_files:
            self.recent_menu.add_command(
                label=os.path.basename(path),
                command=lambda p=path: self.load_file(p)
            )

    # FILES
    def add_recent_file(self, path):
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]
        self._rebuild_recent_menu()
        self.save_settings()


    def new_file(self):
        self.editor.delete("1.0", tk.END)
        self.current_file = None
        self.root.title("X3 IDE")

    def open_file(self):
        if self.dirty==True:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Open file anyway?"
            ):
                return
        path = filedialog.askopenfilename(filetypes=[("X3 Files", "*.x3"), ("All", "*.*")])
        if path:
            self.load_file(path)
        self.dirty = False
        self.highlight_syntax()
        time.sleep(1)
        self.dirty = False

    def load_file(self, path):
        self.add_recent_file(path)
        with open(path, "r", encoding="utf-8") as f:
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", f.read())

        self.current_file = path
        self.root.title(f"X3 IDE - {os.path.basename(path)}")
        self.highlight_syntax()
        self.dirty = False
    def save_file(self):
        if not self.current_file:
            self.save_file_as()
            return
        with open(self.current_file, "w", encoding="utf-8") as f:
            f.write(self.editor.get("1.0", tk.END))
        self.dirty = False
        self.root.title(f"X3 IDE - {os.path.basename(self.current_file)}")

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".x3")
        if path:
            self.current_file = path
            self.save_file()
            self.add_recent_file(path)

        self.dirty = False
        self.root.title(f"X3 IDE - {os.path.basename(self.current_file)}")

    def run_file(self):
        if not self.current_file:
            messagebox.showerror("No file", "Load a file to run first, save the editor contents to a file before running.")
            return
        
        self.show_interpreter_bar()
        self.update_interpreter_bar()

        tab = tk.Frame(self.notebook)
        output = scrolledtext.ScrolledText(tab, state=tk.DISABLED)
        toolbar = tk.Frame(tab)
        toolbar.pack(fill=tk.X)
        status = tk.Label(toolbar, text="Running", fg="green")
        status.pack(side=tk.RIGHT, padx=6)
        entry = tk.Entry(tab)
        entry.pack(fill=tk.X)
        output.pack(fill=tk.BOTH, expand=True)




        self.notebook.add(tab, text=f"Run: {os.path.basename(self.current_file)}")
        tab_id = self.notebook.tabs()[-1]
        self.tab_types[tab_id] = "console"
        self.notebook.select(tab)
        self.tab_types[tab] = "console"
        start_time = time.perf_counter()

        cmd = ["python", get_interpreter(), "-f", self.current_file]
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=creation_flags,
            encoding="utf-8",
            errors="replace"
        )
        self.console_tabs[tab] = {
            "output": output,
            "entry": entry,
            "process": proc,
            "running": True,
            "status": status,
            "start_time": start_time
        }

        def write(text):
            self.root.after(0, lambda: _write(text))

        def _write(text):
            output.config(state=tk.NORMAL)
            output.insert(tk.END, text)
            output.see(tk.END)
            output.config(state=tk.DISABLED)

        def reader(pipe, tab):
            while True:
                if tab not in self.console_tabs:
                    break

                line = pipe.readline()
                if not line:
                    break

                write(line)

            info = self.console_tabs.get(tab)
            if info and info["running"]:
                info["running"] = False
                self.root.after(0, lambda: info["entry"].configure(state=tk.DISABLED))
                write("\n[Process exited]\n")
                elapsed = time.perf_counter() - info["start_time"]
                info["status"].config(text=f"{elapsed:.3f}s | Stopped",fg="red")
        threading.Thread(target=reader, args=(proc.stdout,tab), daemon=True).start()
        threading.Thread(target=reader, args=(proc.stderr,tab), daemon=True).start()

        def send_cmd(event=None):
            cmd = entry.get()
            entry.delete(0, tk.END)

            info = self.console_tabs.get(tab)
            if not info or not info["running"]:
                return

            output = info["output"]
            output.config(state=tk.NORMAL)
            output.insert(tk.END, cmd + "\n")
            output.see(tk.END)
            output.config(state=tk.DISABLED)

            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()

        entry.bind("<Return>", send_cmd)


        stop_btn = tk.Button(
            toolbar, text="Stop",
            command=lambda t=tab: self.stop_console(t)
        )
        stop_btn.pack(side=tk.LEFT, padx=4)

        close_btn = tk.Button(
            toolbar, text="Close",
            command=lambda t=tab: self.close_console_tab(t)
        )
        close_btn.pack(side=tk.LEFT)

        restart_btn = tk.Button(
            toolbar, text="Restart",
            command=lambda t=tab: self.restart_console(t)
        )
        restart_btn.pack(side=tk.LEFT, padx=4)

        def clear_output():
            output.config(state=tk.NORMAL)
            output.delete("1.0", tk.END)
            output.config(state=tk.DISABLED)

        clear_btn = tk.Button(toolbar, text="Clear", command=clear_output)
        clear_btn.pack(side=tk.LEFT, padx=4)

        status.pack(side=tk.RIGHT, padx=6)
        self._apply_console_theme()
        self._apply_console_theme()
        self._apply_theme_to_run_tabs()
        
    def display_info(self):
        info_window = tk.Toplevel(self.root)
        info_window.title("Info...")
        info_window.geometry("350x180")
        info_window.resizable(False, False)

        label = tk.Label(
            info_window,
            text=f"X3 IDE\nv{VERSION}\nAn IDE for the X3 language.\nLast Modified:{LAST_MODIFIED}\nCreated on 8th March 2025\n© Raven Corvidae 2025-2026",
            justify="center",
            padx=20,
            pady=20
        )
        label.pack()

        def show_license():
            license_window = tk.Toplevel(self.root)
            license_window.title("License")
            license_window.geometry("600x400")

            text = scrolledtext.ScrolledText(
                license_window,
                wrap=tk.WORD
            )
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            try:
                with open(get_license_path(), "r", encoding="utf-8") as f:
                    license_text = f.read()
            except:
                license_text = "License file not found."

            text.insert("1.0", license_text)
            text.config(state=tk.DISABLED)
        license_button = tk.Button(
            info_window,
            text="License Info",
            command=show_license
        )
        license_button.pack(pady=10)
    def confirm_exit(self):
        if self.dirty:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Exit anyway?"
            ):
                return
        
        for tab, info in self.console_tabs.items():
            if info["running"]:
                try:
                    info["process"].kill()
                except Exception:
                    pass
        
        self.root.quit()

    def restart_console(self, tab):
        if tab not in self.console_tabs:
            return

        info = self.console_tabs[tab]

        if info["running"]:
            self.stop_console(tab)

        self.notebook.forget(tab)
        self.run_file()

    def stop_console(self, tab):
        info = self.console_tabs.get(tab)
        if not info or not info["running"]:
            return

        proc = info["process"]
        try:
            proc.kill()
        except Exception:
            pass

        info["running"] = False
        info["entry"].configure(state=tk.DISABLED)

        output = info["output"]
        output.config(state=tk.NORMAL)
        output.insert(tk.END, "\n[Process stopped]\n")
        output.config(state=tk.DISABLED)
        elapsed = time.perf_counter() - info["start_time"]
        info["status"].config(text=f"{elapsed:.3f}s | Stopped",fg="red")


    def close_console_tab(self, tab):
        if tab not in self.console_tabs:
            return
        self.tab_types.pop(tab, None)

        info = self.console_tabs[tab]

        if info["running"]:
            if not messagebox.askyesno(
                "Process Running",
                "This process is still running. Stop and close?"
            ):
                return
            self.stop_console(tab)

        del self.console_tabs[tab]
        self.notebook.forget(tab)
        if not self.console_tabs:
            self.hide_interpreter_bar()
        elapsed = time.perf_counter() - info["start_time"]
        info["status"].config(text=f"{elapsed:.3f}s | Stopped",fg="red")

    # Interpreter Bar (Only shows on console tabs cuz why would you even need it in editor mode)
    def show_interpreter_bar(self):
        if not self.interpreter_bar_visible:
            self.interpreter_bar.pack(side=tk.BOTTOM, fill=tk.X)
            self.interpreter_bar_visible = True

    def hide_interpreter_bar(self):
        if self.interpreter_bar_visible:
            self.interpreter_bar.pack_forget()
            self.interpreter_bar_visible = False
    def update_interpreter_bar(self):
        path = get_interpreter()
        version = get_interpreter_version()
        source = get_interpreter_type(path)
        pyver = sys.version.split()[0]
        
        self.interpreter_bar.config(
            text=f"X3 v{version} | {source} ({path}) | Python {pyver}"
        )
    # THEME
    def _apply_editor_theme(self):
        t = self.themes[self.editor_theme]
        f = font.Font(
            family=t["ui"]["font"][0],
            size=t["ui"]["font"][1]
        )

        self.editor.configure(
            bg=t["colors"]["bg"],
            fg=t["colors"]["fg"],
            insertbackground=t["colors"]["fg"],
            font=f
        )
        self.settings["editor_theme"] = self.editor_theme
        self.settings["editor_font_size"] = self.editor_font_size
        self.save_settings()
        self._setup_tags()
        self.highlight_syntax()
    def _apply_console_theme(self):
        t = self.themes[self.console_theme]
        f = font.Font(
            family=t["ui"]["font"][0],
            size=self.console_font_size
        )

        for widgets in self.console_tabs.values():
            widgets["output"].configure(
                bg=t["colors"]["bg"],
                fg=t["colors"]["fg"],
                insertbackground=t["colors"]["fg"],
                font=f
            )
            widgets["entry"].configure(
                bg=t["colors"]["input_bg"],
                fg=t["colors"]["input_fg"],
                insertbackground=t["colors"]["input_fg"],
                font=f
            )
        self.settings["console_theme"] = self.console_theme
        self.settings["console_font_size"] = self.console_font_size
        self.save_settings()

    def _apply_theme_to_run_tabs(self):
        t = self.themes[self.console_theme]
        f = font.Font(
            family=t["ui"]["font"][0],
            size=self.console_font_size
        )

        for info in self.console_tabs.values():
            info["output"].configure(
                bg=t["colors"]["bg"],
                fg=t["colors"]["fg"],
                font=f
            )
            info["entry"].configure(
                bg=t["colors"]["input_bg"],
                fg=t["colors"]["input_fg"],
                font=f
            )

    # Font Settings
    def tab_font_up(self):
        tab_id = self.notebook.select()

        if self.tab_types.get(tab_id) == "console":
            self.console_font_up()
        else:
            self.editor_font_up()


    def tab_font_down(self):
        tab_id = self.notebook.select()

        if self.tab_types.get(tab_id) == "console":
            self.console_font_down()
        else:
            self.editor_font_down()
    def editor_font_up(self):
        self.themes[self.editor_theme]["ui"]["font"][1] = self.themes[self.editor_theme]["ui"]["font"][1] + 1
        self._apply_editor_theme()

    def editor_font_down(self):
        self.themes[self.editor_theme]["ui"]["font"][1] = max(6, self.themes[self.editor_theme]["ui"]["font"][1] - 1)
        self._apply_editor_theme()

    def console_font_up(self):
        self.console_font_size += 1
        self._apply_console_theme()


    def console_font_down(self):
        self.console_font_size = max(9, self.console_font_size - 1)
        self._apply_console_theme()


    #Keyboard Shortcuts bcuz cool
    def _bind_keys(self):
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind("<Control-r>", lambda e: self.run_file())

        self.root.bind("<Control-equal>", lambda e: self.tab_font_up())
        self.root.bind("<Control-minus>", lambda e: self.tab_font_down())

        self.root.bind("<Control-w>", self.close_current_tab)
        self.root.bind("<Control-q>", lambda e: self.confirm_exit())
        self.root.bind("<Control-f>", self.open_search)
    def open_search(self, event=None):
        import tkinter.simpledialog as sd
        term = sd.askstring("Search", "Enter search term:")
        if term:
            self.current_search_term = term
            self.highlight_search(term)
    def close_current_tab(self, event=None):
        tab = self.notebook.select()
        if not tab:
            return

        widget = self.root.nametowidget(tab)
        if widget in self.console_tabs:
            self.close_console_tab(widget)


if __name__ == "__main__":
    root = tk.Tk()
    X3IDE(root)
    root.mainloop()
