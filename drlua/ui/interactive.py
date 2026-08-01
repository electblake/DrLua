from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import re
from threading import Thread as PythonThread
import traceback

from drlua.create_bins import create_bins
from drlua.section_category_data import SECTION_CATEGORY_DATA


def _default_release_name(path_value: str) -> str:
    path = Path(path_value).expanduser().resolve()
    return path.name if path.is_dir() else path.stem


def _split_tags(text: str) -> list[str]:
    return [tag.strip() for tag in re.split(r"[\r\n,]", text) if tag.strip()]


def _run_create_bins_from_form(
    source_path: str,
    name: str,
    section: str,
    group: str,
    tags: list[str],
) -> tuple[int, str]:
    output = io.StringIO()
    result = 0

    with redirect_stdout(output), redirect_stderr(output):
        try:
            create_result = create_bins(
                Path(source_path),
                name=name or None,
                section=section or None,
                group_name=group or None,
                tag=tags,
                prompt_for_missing_tags=False,
            )
            result = int(create_result or 0)
        except Exception:
            result = 1
            traceback.print_exc()

    return result, output.getvalue().rstrip()


def launch_interactive(input_path: str | Path | None = None) -> int:
    try:
        import clr

        clr.AddReference("System.Drawing")  # type: ignore[attr-defined]
        clr.AddReference("System.Windows.Forms")  # type: ignore[attr-defined]

        from System.Threading import ApartmentState, Thread, ThreadStart  # type: ignore[import-not-found]
    except Exception:
        traceback.print_exc()
        return 1

    result = {"exit_code": 1}

    def run() -> None:
        try:
            result["exit_code"] = _show_launcher(input_path)
        except Exception:
            traceback.print_exc()
            result["exit_code"] = 1

    thread = Thread(ThreadStart(run))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()
    thread.Join()
    return int(result["exit_code"])


def _show_launcher(input_path: str | Path | None = None) -> int:
    from System import Action  # type: ignore[import-not-found]
    from System.Drawing import Font, Point, Size  # type: ignore[import-not-found]
    from System.Windows.Forms import (  # type: ignore[import-not-found]
        Application,
        Button,
        ComboBox,
        ComboBoxStyle,
        DialogResult,
        Form,
        FormStartPosition,
        Label,
        OpenFileDialog,
        ProgressBar,
        ProgressBarStyle,
        ScrollBars,
        TextBox,
    )

    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)

    resolved_input_path = _resolve_initial_input_path(input_path, OpenFileDialog, DialogResult)
    if resolved_input_path is None:
        return 0

    default_name = _default_release_name(resolved_input_path)
    section_options = _section_options()
    matched_section, matched_category = _match_section_category(resolved_input_path)

    form = Form()
    form.Text = "DrLua Launcher"
    form.StartPosition = FormStartPosition.CenterScreen
    form.Size = Size(804, 620)
    form.MinimumSize = Size(804, 620)

    source_label = Label()
    source_label.Location = Point(12, 14)
    source_label.Size = Size(100, 20)
    source_label.Text = "Source Path"
    form.Controls.Add(source_label)

    source_text_box = TextBox()
    source_text_box.Location = Point(12, 36)
    source_text_box.Size = Size(680, 24)
    source_text_box.Text = resolved_input_path
    form.Controls.Add(source_text_box)

    browse_button = Button()
    browse_button.Location = Point(700, 34)
    browse_button.Size = Size(72, 28)
    browse_button.Text = "Browse"
    form.Controls.Add(browse_button)

    name_label = Label()
    name_label.Location = Point(12, 76)
    name_label.Size = Size(100, 20)
    name_label.Text = "Name"
    form.Controls.Add(name_label)

    name_text_box = TextBox()
    name_text_box.Location = Point(12, 98)
    name_text_box.Size = Size(250, 24)
    name_text_box.Text = default_name
    form.Controls.Add(name_text_box)

    section_label = Label()
    section_label.Location = Point(282, 76)
    section_label.Size = Size(100, 20)
    section_label.Text = "Section"
    form.Controls.Add(section_label)

    section_combo_box = ComboBox()
    section_combo_box.Location = Point(282, 98)
    section_combo_box.Size = Size(230, 24)
    section_combo_box.DropDownStyle = ComboBoxStyle.DropDown
    for option in section_options:
        section_combo_box.Items.Add(option)
    section_combo_box.Text = matched_section or (section_options[0] if section_options else "")
    form.Controls.Add(section_combo_box)

    category_label = Label()
    category_label.Location = Point(532, 76)
    category_label.Size = Size(100, 20)
    category_label.Text = "Category"
    form.Controls.Add(category_label)

    category_combo_box = ComboBox()
    category_combo_box.Location = Point(532, 98)
    category_combo_box.Size = Size(240, 24)
    category_combo_box.DropDownStyle = ComboBoxStyle.DropDown
    form.Controls.Add(category_combo_box)

    group_label = Label()
    group_label.Location = Point(12, 138)
    group_label.Size = Size(100, 20)
    group_label.Text = "Group"
    form.Controls.Add(group_label)

    group_text_box = TextBox()
    group_text_box.Location = Point(12, 160)
    group_text_box.Size = Size(760, 24)
    form.Controls.Add(group_text_box)

    tag_label = Label()
    tag_label.Location = Point(12, 200)
    tag_label.Size = Size(240, 20)
    tag_label.Text = "Tags (one per line or comma-separated)"
    form.Controls.Add(tag_label)

    tag_text_box = TextBox()
    tag_text_box.Location = Point(12, 222)
    tag_text_box.Size = Size(760, 140)
    tag_text_box.Multiline = True
    tag_text_box.AcceptsReturn = True
    tag_text_box.AcceptsTab = False
    tag_text_box.ScrollBars = ScrollBars.Vertical
    form.Controls.Add(tag_text_box)

    send_button = Button()
    send_button.Location = Point(12, 376)
    send_button.Size = Size(150, 34)
    send_button.Text = "Send to DrLua"
    form.Controls.Add(send_button)

    progress_bar = ProgressBar()
    progress_bar.Location = Point(174, 383)
    progress_bar.Size = Size(598, 20)
    progress_bar.Style = ProgressBarStyle.Marquee
    progress_bar.Visible = False
    form.Controls.Add(progress_bar)

    status_label = Label()
    status_label.Location = Point(12, 424)
    status_label.Size = Size(100, 20)
    status_label.Text = "Output"
    form.Controls.Add(status_label)

    output_text_box = TextBox()
    output_text_box.Location = Point(12, 446)
    output_text_box.Size = Size(760, 120)
    output_text_box.Multiline = True
    output_text_box.ReadOnly = True
    output_text_box.ScrollBars = ScrollBars.Vertical
    output_text_box.Font = Font("Consolas", 9)
    form.Controls.Add(output_text_box)

    def browse_clicked(_sender: object, _event: object) -> None:
        selected_path = _select_input_path(OpenFileDialog, DialogResult, source_text_box.Text)
        if selected_path is None:
            return

        source_text_box.Text = selected_path
        if not name_text_box.Text.strip():
            name_text_box.Text = _default_release_name(selected_path)
        apply_path_match(selected_path)

    def set_category_options(section: str, selected_category: str | None = None) -> None:
        category_combo_box.Items.Clear()
        categories = _category_options(section)
        for category in categories:
            category_combo_box.Items.Add(category)
        category_combo_box.Enabled = True
        category_combo_box.Text = selected_category or ""

    def set_tags_for_category(section: str, category: str) -> None:
        tags = _category_tags(section, category)
        tag_text_box.Text = "\r\n".join(tags)

    def apply_path_match(path_value: str) -> None:
        section, category = _match_section_category(path_value)
        if section:
            section_combo_box.Text = section
            set_category_options(section, category)
        if section and category:
            set_tags_for_category(section, category)

    def section_changed(_sender: object, _event: object) -> None:
        set_category_options(section_combo_box.Text.strip())

    def category_changed(_sender: object, _event: object) -> None:
        set_tags_for_category(section_combo_box.Text.strip(), category_combo_box.Text.strip())

    def run_on_ui(action) -> None:
        if form.IsDisposed or not form.IsHandleCreated:
            return
        form.BeginInvoke(Action(action))

    def finish_run(result: int, output: str) -> None:
        def update() -> None:
            if output:
                output_text_box.AppendText(output.replace("\n", "\r\n") + "\r\n")
            output_text_box.AppendText(f"Exit code: {result}\r\n")
            form.UseWaitCursor = False
            progress_bar.Visible = False
            send_button.Enabled = True
            status_label.Text = "Output"

        run_on_ui(update)

    def run_create_bins(source_path: str, name: str, section: str, group: str, tags: list[str]) -> None:
        result, output = _run_create_bins_from_form(source_path, name, section, group, tags)
        finish_run(result, output)

    def send_clicked(_sender: object, _event: object) -> None:
        source_path = source_text_box.Text.strip()
        name = name_text_box.Text.strip()
        section = section_combo_box.Text.strip()
        group = group_text_box.Text.strip()
        tags = _split_tags(tag_text_box.Text)
        arguments = _preview_arguments(
            source_path,
            name,
            section,
            group,
            tags,
        )
        output_text_box.Text = f"Running:\r\ndrlua {' '.join(arguments)}\r\n\r\n"

        send_button.Enabled = False
        form.UseWaitCursor = True
        progress_bar.Visible = True
        status_label.Text = "Running"
        PythonThread(
            target=run_create_bins,
            args=(source_path, name, section, group, tags),
            daemon=True,
        ).start()

    browse_button.Click += browse_clicked
    section_combo_box.SelectedIndexChanged += section_changed
    section_combo_box.TextChanged += section_changed
    category_combo_box.SelectedIndexChanged += category_changed
    category_combo_box.TextChanged += category_changed
    send_button.Click += send_clicked

    set_category_options(section_combo_box.Text.strip(), matched_category)
    if matched_section and matched_category:
        set_tags_for_category(matched_section, matched_category)

    form.ShowDialog()
    return 0


def _resolve_initial_input_path(input_path: str | Path | None, folder_browser_dialog, dialog_result) -> str | None:
    if input_path is not None:
        return str(Path(input_path).expanduser().resolve())

    return _select_input_path(folder_browser_dialog, dialog_result)


def _select_input_path(open_file_dialog, dialog_result, initial_path: str | None = None) -> str | None:
    dialog = open_file_dialog()
    dialog.Title = "Select source folder or file"
    dialog.Filter = "Media, export, or any file (*.*)|*.*"
    dialog.CheckFileExists = False
    dialog.CheckPathExists = True
    dialog.ValidateNames = False
    dialog.FileName = "Select this folder"

    if initial_path:
        initial = Path(initial_path).expanduser()
        if initial.is_file():
            dialog.InitialDirectory = str(initial.parent.resolve())
            dialog.FileName = initial.name
        elif initial.is_dir():
            dialog.InitialDirectory = str(initial.resolve())

    if dialog.ShowDialog() != dialog_result.OK:
        return None

    selected = Path(str(dialog.FileName)).expanduser()
    if selected.exists():
        return str(selected.resolve())
    if selected.name == "Select this folder" and selected.parent.exists():
        return str(selected.parent.resolve())
    return str(selected.resolve())


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


def _preview_arguments(source_path: str, name: str, section: str, group: str, tags: list[str]) -> list[str]:
    arguments = [source_path.strip()]
    if name.strip():
        arguments.extend(["--name", name.strip()])
    if section.strip():
        arguments.extend(["--section", section.strip()])
    if group.strip():
        arguments.extend(["--group", group.strip()])
    for tag in tags:
        arguments.extend(["--tag", tag])
    return [_quote_preview_argument(argument) for argument in arguments]


def _quote_preview_argument(argument: str) -> str:
    if re.search(r'\s|"', argument):
        return '"' + argument.replace('"', '\\"') + '"'
    return argument
