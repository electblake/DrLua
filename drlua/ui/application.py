from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import sys
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk

from drlua import __version__
from drlua.config import LOG_PATH, PROCESSED_DATA_DIR
from drlua.create_bins import create_bins
from drlua.section_category_data import SECTION_CATEGORY_DATA
from drlua.updates import download_setup, latest_release, version_tuple


def _default_release_name(path_value: str) -> str:
    path = Path(path_value).expanduser().resolve()
    return path.name if path.is_dir() else path.stem


def _split_tags(text: str) -> list[str]:
    return [tag.strip() for tag in re.split(r"[\r\n,]", text) if tag.strip()]


def _split_source_paths(text: str) -> list[str]:
    return [path.strip() for path in re.split(r"[|\r\n]+", text) if path.strip()]


def _run_create_bins_from_form(
    source_paths: list[str],
    name: str,
    section: str,
    group: str,
    tags: list[str],
) -> None:
    create_bins(
        [Path(source_path) for source_path in source_paths],
        name=name,
        section=section,
        group_name=group or None,
        tag=tags,
    )


class ApplicationView(ttk.Frame):
    def __init__(self, parent: tk.Misc, input_paths: list[Path] | None = None):
        super().__init__(parent, padding=16)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.log_path = LOG_PATH
        with self.log_path.open(encoding="utf-8") as stream:
            stream.read()
            self.log_position = stream.tell()
        self.busy = False
        self.poll_id = None
        self.update_poll_id = None
        self.setup_path = None
        self.name = tk.StringVar(self)
        self.section = tk.StringVar(self)
        self.category = tk.StringVar(self)
        self.group = tk.StringVar(self)
        self.status = tk.StringVar(self, value="Choose source folders or files to get started.")

        heading = ttk.Frame(self)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.title_font = font.Font(self, family="Segoe UI", size=20, weight="bold")
        ttk.Label(heading, text="DrLua", font=self.title_font).pack(side="left")
        ttk.Label(heading, text=f"v{__version__}  ·  DaVinci Resolve Lua scripts").pack(side="left", padx=14)
        self.check_updates = ttk.Button(heading, text="Check for updates", command=self.check_for_updates)
        self.check_updates.pack(side="right")

        panes = ttk.Panedwindow(self, orient=tk.VERTICAL)
        panes.grid(row=1, column=0, sticky="nsew")
        form = ttk.Frame(panes, padding=(0, 0, 0, 12))
        form.columnconfigure(0, weight=1)
        form.rowconfigure(3, weight=1)
        panes.add(form, weight=3)

        sources = ttk.LabelFrame(form, text="Source paths", padding=10)
        sources.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        sources.columnconfigure(0, weight=1)
        self.sources = tk.Text(sources, height=3, width=40, wrap="none", undo=True)
        self.sources.grid(row=0, column=0, sticky="nsew")
        source_scroll = ttk.Scrollbar(sources, command=self.sources.yview)
        source_scroll.grid(row=0, column=1, sticky="ns")
        self.sources.configure(yscrollcommand=source_scroll.set)
        browse = ttk.Frame(sources)
        browse.grid(row=0, column=2, sticky="n", padx=(10, 0))
        ttk.Button(browse, text="Add folder…", command=self.add_folder).pack(fill="x")
        ttk.Button(browse, text="Add files…", command=self.add_files).pack(fill="x", pady=(6, 0))
        ttk.Label(sources, text="One path per line, or separate paths with |.").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.sources.bind("<FocusOut>", self.sources_changed)
        self.sources.bind("<<Modified>>", self.source_edited)

        fields = ttk.Frame(form)
        fields.grid(row=1, column=0, sticky="ew")
        for column in range(3):
            fields.columnconfigure(column, weight=1, uniform="fields")
        for column, label in enumerate(("Name", "Section", "Category")):
            ttk.Label(fields, text=label).grid(row=0, column=column, sticky="w", padx=(0, 10))
        self.name_entry = ttk.Entry(fields, textvariable=self.name)
        self.name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(4, 10))
        self.sections = ttk.Combobox(fields, textvariable=self.section, values=_section_options())
        self.sections.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(4, 10))
        self.categories = ttk.Combobox(fields, textvariable=self.category)
        self.categories.grid(row=1, column=2, sticky="ew", pady=(4, 10))
        ttk.Label(fields, text="Group").grid(row=2, column=0, sticky="w")
        ttk.Entry(fields, textvariable=self.group).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 10))
        ttk.Label(form, text="Tags (one per line or comma-separated)").grid(row=2, column=0, sticky="w")
        tag_frame = ttk.Frame(form)
        tag_frame.grid(row=3, column=0, sticky="nsew", pady=(4, 10))
        tag_frame.columnconfigure(0, weight=1)
        tag_frame.rowconfigure(0, weight=1)
        self.tags = tk.Text(tag_frame, height=4, width=40, wrap="word", undo=True)
        self.tags.grid(row=0, column=0, sticky="nsew")
        tag_scroll = ttk.Scrollbar(tag_frame, command=self.tags.yview)
        tag_scroll.grid(row=0, column=1, sticky="ns")
        self.tags.configure(yscrollcommand=tag_scroll.set)

        actions = ttk.Frame(form)
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(1, weight=1)
        self.send = ttk.Button(actions, text="Generate Lua script", command=self.submit, state="disabled")
        self.send.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(actions, mode="indeterminate")
        self.progress.grid(row=0, column=1, sticky="ew", padx=12)
        self.progress.grid_remove()
        ttk.Button(actions, text="Open output folder", command=self.open_output).grid(row=0, column=2)

        output_frame = ttk.LabelFrame(panes, text="Output", padding=10)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        panes.add(output_frame, weight=2)
        self.output = tk.Text(output_frame, height=8, width=40, wrap="word", state="disabled", font="TkFixedFont")
        self.output.grid(row=0, column=0, sticky="nsew")
        output_scroll = ttk.Scrollbar(output_frame, command=self.output.yview)
        output_scroll.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=output_scroll.set)
        ttk.Button(output_frame, text="Copy output", command=self.copy_output).grid(row=1, column=0, sticky="e", pady=(8, 0))
        ttk.Label(self, textvariable=self.status).grid(row=2, column=0, sticky="w", pady=(10, 0))

        self.section.trace_add("write", self.section_changed)
        self.category.trace_add("write", self.category_changed)
        section_options = _section_options()
        self.section.set(section_options[0] if section_options else "")
        if input_paths:
            self.append_sources([str(path.expanduser().resolve()) for path in input_paths])
        self.sources.focus_set()

    def source_edited(self, _event=None):
        self.sources.edit_modified(False)
        self.send.state(["!disabled"] if self.source_paths() and not self.busy else ["disabled"])

    def source_paths(self):
        return _split_source_paths(self.sources.get("1.0", "end-1c"))

    def sources_changed(self, _event=None):
        paths = self.source_paths()
        if paths:
            if not self.name.get().strip():
                self.name.set(_default_release_name(paths[0]))
            section, category = _match_section_category(paths[0])
            if section:
                self.section.set(section)
                self.category.set(category or "")

    def append_sources(self, paths):
        current = self.sources.get("1.0", "end-1c").strip()
        self.sources.delete("1.0", "end")
        self.sources.insert("1.0", "\n".join(([current] if current else []) + paths))
        self.sources_changed()
        self.source_edited()
        self.status.set("Ready to generate a Lua script.")

    def add_folder(self):
        selected = filedialog.askdirectory(parent=self, title="Add source folder")
        if selected:
            self.append_sources([selected])

    def add_files(self):
        selected = filedialog.askopenfilenames(parent=self, title="Add media or export files")
        if selected:
            self.append_sources(list(selected))

    def section_changed(self, *_):
        self.categories.configure(values=_category_options(self.section.get().strip()))
        self.category.set("")

    def category_changed(self, *_):
        tags = _category_tags(self.section.get().strip(), self.category.get().strip())
        self.tags.delete("1.0", "end")
        self.tags.insert("1.0", "\n".join(tags))

    def append_output(self, text):
        text = re.sub(r"\x1b\[[0-9;]*m", "", text)
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def submit(self):
        if self.busy or not self.source_paths():
            return
        args = (self.source_paths(), self.name.get().strip(), self.section.get().strip(),
                self.group.get().strip(), _split_tags(self.tags.get("1.0", "end-1c")))
        self.busy = True
        self.send.state(["disabled"])
        self.check_updates.state(["disabled"])
        self.status.set("Generating Lua script…")
        self.progress.grid()
        self.progress.start(12)
        self.future = self.executor.submit(_run_create_bins_from_form, *args)
        self.poll_id = self.after(100, self.poll_result)

    def refresh_output(self):
        with self.log_path.open(encoding="utf-8") as stream:
            stream.seek(self.log_position)
            output = stream.read()
            self.log_position = stream.tell()
        if output:
            self.append_output(output)

    def poll_result(self):
        self.poll_id = None
        self.refresh_output()
        if not self.future.done():
            self.poll_id = self.after(100, self.poll_result)
            return
        self.busy = False
        self.check_updates.state(["!disabled"])
        self.progress.stop()
        self.progress.grid_remove()
        self.source_edited()
        self.future.result()
        self.refresh_output()
        self.status.set("Lua script created. Paste the dofile command into Resolve.")

    def open_output(self):
        folder = PROCESSED_DATA_DIR / "create_bins"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def copy_output(self):
        self.clipboard_clear()
        self.clipboard_append(self.output.get("1.0", "end-1c"))

    def check_for_updates(self):
        self.busy = True
        self.send.state(["disabled"])
        self.check_updates.state(["disabled"])
        self.status.set("Checking for updates…")
        self.update_future = self.executor.submit(latest_release)
        self.update_poll_id = self.after(100, self.poll_update)

    def poll_update(self):
        self.update_poll_id = None
        if not self.update_future.done():
            self.update_poll_id = self.after(100, self.poll_update)
            return
        release = self.update_future.result()
        if version_tuple(release["tag_name"]) > version_tuple(__version__):
            if messagebox.askyesno(
                "DrLua update available",
                f"DrLua {release['tag_name']} is available.\n\n"
                "Download the update and close DrLua to run setup?\n"
                "The current form will be discarded.",
                parent=self,
            ):
                self.status.set("Downloading update…")
                self.update_future = self.executor.submit(download_setup, release)
                self.update_poll_id = self.after(100, self.poll_download)
                return
            self.status.set("Update cancelled.")
        else:
            self.status.set(f"DrLua {__version__} is up to date.")
        self.busy = False
        self.source_edited()
        self.check_updates.state(["!disabled"])

    def poll_download(self):
        self.update_poll_id = None
        if not self.update_future.done():
            self.update_poll_id = self.after(100, self.poll_download)
            return
        self.setup_path = self.update_future.result()
        self.winfo_toplevel().destroy()

    def destroy(self):
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
        if self.update_poll_id is not None:
            self.after_cancel(self.update_poll_id)
        self.progress.stop()
        self.executor.shutdown(wait=False)
        super().destroy()


def run_application(input_paths: list[Path] | None = None) -> int:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        create_mutex = ctypes.windll.kernel32.CreateMutexW
        create_mutex.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        create_mutex.restype = wintypes.HANDLE
        mutex = create_mutex(None, False, "electblake.DrLua.Running")

    root = tk.Tk()
    root.title(f"DrLua v{__version__}")
    root.geometry("920x780")
    root.minsize(700, 660)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    view = ApplicationView(root, input_paths)
    view.grid(row=0, column=0, sticky="nsew")
    root.mainloop()
    view.executor.shutdown(wait=True)
    if sys.platform == "win32":
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL
        close_handle(mutex)
    if view.setup_path is not None:
        os.startfile(view.setup_path)
    return 0


def _section_options() -> list[str]:
    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    return list(sections) if isinstance(sections, dict) else []


def _section_data(section: str) -> dict:
    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    if not isinstance(sections, dict):
        return {}
    value = sections.get(section, {})
    return value if isinstance(value, dict) else {}


def _category_data(section: str, category: str) -> dict:
    categories = _section_data(section).get("Categories", {})
    if not isinstance(categories, dict):
        return {}
    value = categories.get(category, {})
    return value if isinstance(value, dict) else {}


def _category_options(section: str) -> list[str]:
    categories = _section_data(section).get("Categories", {})
    if isinstance(categories, dict) and categories:
        return list(categories)

    section_path = str(_section_data(section).get("Path", "")).strip()
    if not section_path:
        return []

    root = Path(section_path).expanduser()
    if not root.is_dir():
        return []

    return sorted(child.name for child in root.iterdir() if child.is_dir())


def _category_tags(section: str, category: str) -> list[str]:
    category_data = _category_data(section, category)
    raw_tags = category_data.get("Tags")
    if isinstance(raw_tags, list) and raw_tags:
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    return [category] if category else []


def _match_section_category(path_value: str) -> tuple[str | None, str | None]:
    selected_path = Path(path_value).expanduser()
    selected_display = str(selected_path.resolve() if selected_path.exists() else selected_path).rstrip("\\/")
    selected_text = selected_display.casefold()
    best_section: str | None = None
    best_category: str | None = None
    best_length = -1

    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    if not isinstance(sections, dict):
        return None, None

    for section, raw_section_data in sections.items():
        if not isinstance(raw_section_data, dict):
            continue

        section_path = str(raw_section_data.get("Path", "")).rstrip("\\/")
        if _path_is_under(selected_text, section_path) and len(section_path) > best_length:
            best_section = str(section)
            best_category = _category_from_section_path(selected_display, section_path)
            best_length = len(section_path)

        categories = raw_section_data.get("Categories", {})
        if not isinstance(categories, dict):
            continue
        for category, raw_category_data in categories.items():
            if not isinstance(raw_category_data, dict):
                continue
            category_path = str(raw_category_data.get("Path", "")).rstrip("\\/")
            if _path_is_under(selected_text, category_path) and len(category_path) > best_length:
                best_section = str(section)
                best_category = str(category)
                best_length = len(category_path)

    return best_section, best_category


def _category_from_section_path(selected_path: str, section_path: str) -> str | None:
    if not section_path:
        return None

    relative = selected_path[len(section_path.rstrip("\\/")):].lstrip("\\/")
    if not relative:
        return None
    return re.split(r"[\\/]", relative, maxsplit=1)[0] or None


def _path_is_under(selected_text: str, root_path: str) -> bool:
    if not root_path:
        return False
    root_text = root_path.casefold()
    return selected_text == root_text or selected_text.startswith(f"{root_text}\\") or selected_text.startswith(f"{root_text}/")
