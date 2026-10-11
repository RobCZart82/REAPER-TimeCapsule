"""Small self-contained Tk desktop shell; advanced functions available via CLI."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .background import BackgroundTask
from .operation import OperationControl
from .core import NonPortableNames, VERSION, default_resource, make_backup, preview, preview_backup, restore_backup, scan
from .midi_validation import validate_midi_workflow
from .config_migration import preview_migration
from .inventory import audit_reapack
from .reports import scan_report
from .report_browser import ReportBrowser
from .about import AboutWindow, brand_image

GUI_REPORT_MAX_CHARS = 256 * 1024
GUI_REPORT_CHUNK_CHARS = 8 * 1024
GUI_REPORT_MAX_ITEMS = 200
GUI_REPORT_MAX_NODES = 1000
GUI_REPORT_MAX_DEPTH = 12
GUI_REPORT_MAX_STRING_CHARS = 2048


def _bounded_report(value):
    """Copy a JSON-like report into a small, display-only preview."""
    remaining_nodes = [GUI_REPORT_MAX_NODES]

    def copy(item, depth=0):
        if remaining_nodes[0] <= 0:
            return "[display limit reached]"
        remaining_nodes[0] -= 1
        if depth >= GUI_REPORT_MAX_DEPTH:
            return "[nested value omitted: display depth limit]"
        if isinstance(item, str):
            if len(item) > GUI_REPORT_MAX_STRING_CHARS:
                omitted = len(item) - GUI_REPORT_MAX_STRING_CHARS
                return item[:GUI_REPORT_MAX_STRING_CHARS] + f"… [{omitted} characters omitted]"
            return item
        if isinstance(item, dict):
            result = {}
            for index, (key, child) in enumerate(item.items()):
                if index >= GUI_REPORT_MAX_ITEMS:
                    result["_display_note"] = f"{len(item) - index} additional fields omitted"
                    break
                result[str(key)] = copy(child, depth + 1)
            return result
        if isinstance(item, (list, tuple)):
            result = [copy(child, depth + 1) for child in item[:GUI_REPORT_MAX_ITEMS]]
            if len(item) > GUI_REPORT_MAX_ITEMS:
                result.append(f"[… {len(item) - GUI_REPORT_MAX_ITEMS} additional items omitted]")
            return result
        if item is None or isinstance(item, (bool, int, float)):
            return item
        return str(item)[:GUI_REPORT_MAX_STRING_CHARS]

    return copy(value)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("REAPER Time Capsule " + VERSION)
        self.app_icon = brand_image(self, 'timecapsule-128.png')
        self.small_icon = brand_image(self, 'timecapsule-32.png')
        self.iconphoto(True, self.app_icon, self.small_icon)
        self.about_window = None
        self.last_scan_report = None
        self.report_window = None
        if self.tk.call("tk", "windowingsystem") == "aqua":
            self.createcommand("tkAboutDialog", self._show_about)
        self.runner = BackgroundTask()
        self.interactive = []
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.source = tk.StringVar(value=str(default_resource()))
        self.archive = tk.StringVar()
        self.destination = tk.StringVar(value=str(Path.home() / "Desktop" / "TimeCapsule-Restored"))
        body = ttk.Frame(self, padding=(25, 20))
        body.pack(fill="both", expand=True)
        header = ttk.Frame(body)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="REAPER Time Capsule — Smart Backup", font=("Arial", 17, "bold")).pack(side="left")
        ttk.Button(header, text="About", command=self._show_about).pack(side="right")
        paths = ttk.Frame(body)
        paths.pack(fill="x")
        paths.columnconfigure(1, weight=1)
        self.path_labels, self.path_entries, self.browse_buttons = [], [], []
        for index, (label, variable, chooser) in enumerate((
            ("REAPER resource folder", self.source, filedialog.askdirectory),
            ("Snapshot ZIP", self.archive, lambda: filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])) ,
            ("Restore to NEW folder", self.destination, self._select_restore_destination),
        )):
            caption = ttk.Label(paths, text=label)
            caption.grid(row=index, column=0, sticky="w", padx=(0, 12), pady=5)
            entry = ttk.Entry(paths, textvariable=variable)
            entry.grid(row=index, column=1, sticky="ew", pady=5)
            browse = ttk.Button(paths, text="Browse", command=lambda v=variable, c=chooser: v.set(c() or v.get()))
            browse.grid(row=index, column=2, padx=(10, 0), pady=5)
            self.path_labels.append(caption)
            self.path_entries.append(entry)
            self.browse_buttons.append(browse)
            self.interactive.extend((entry, browse))
        archive_choices = ttk.Frame(body)
        archive_choices.pack(anchor="w", pady=3)
        for label, chooser in (("Open existing snapshot", lambda: filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])),
                               ("Choose new backup ZIP", lambda: filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")]))):
            button = ttk.Button(archive_choices, text=label, command=lambda c=chooser: self.archive.set(c() or self.archive.get()))
            button.pack(side="left", padx=(0, 10))
            self.interactive.append(button)
        row = ttk.Frame(body)
        row.pack(anchor="w", pady=17)
        self.action_row = row
        self.action_buttons = []
        for label, fn in (
            ("Scan / Preview", lambda: self._start_io("scan")),
            ("MIDI Audit", lambda: self._start_io("midi")),
            ("ReaPack Audit", lambda: self._start_io("reapack")),
            ("Config Preview", self._config_preview),
            ("Backup", lambda: self._start_io("backup")),
            ("Verify", lambda: self._start_io("verify")),
            ("Restore", self._restore),
        ):
            button = ttk.Button(row, text=label, command=fn)
            button.pack(side="left", padx=5)
            self.action_buttons.append(button)
            self.interactive.append(button)
        self.action_buttons[0].pack_configure(padx=(0, 5))
        self.action_buttons[-1].pack_configure(padx=(5, 0))
        ttk.Label(body, text="REAPER must be closed. Restore NEVER overwrites an existing folder.").pack(anchor="w")
        ttk.Label(body, text="Machine-dependent and uncertain files are isolated under NeedsReview/.").pack(anchor="w")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(body, textvariable=self.status).pack(anchor="w")
        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.pack(fill="x", pady=4)
        report_controls = ttk.Frame(body)
        report_controls.pack(anchor="w")
        self.cancel_button = ttk.Button(report_controls, text="Cancel operation", command=self._cancel_io, state="disabled")
        self.cancel_button.pack(side="left")
        self.report_button = ttk.Button(report_controls, text="File policies…", command=self._show_report)
        self.report_button.pack(side="left", padx=(10, 0))
        self.interactive.append(self.report_button)
        # Reserve the footer before the expanding output at the default height.
        self.resize_hint = ttk.Label(body, text="↓  Drag down to show more output",
                                     anchor="center", cursor="sb_v_double_arrow")
        self.resize_hint.pack(side="bottom", fill="x")
        self.resize_hint.bind("<ButtonPress-1>", self._begin_vertical_resize)
        self.resize_hint.bind("<B1-Motion>", self._drag_vertical_resize)
        output = ttk.Frame(body)
        output.pack(fill="both", expand=True, pady=10)
        output.columnconfigure(0, weight=1)
        output.rowconfigure(0, weight=1)
        self.log = tk.Text(output, width=1, height=10, wrap="none")
        self.log.grid(row=0, column=0, sticky="nsew")
        self.vertical_scroll = ttk.Scrollbar(output, orient="vertical", command=self.log.yview)
        self.vertical_scroll.grid(row=0, column=1, sticky="ns")
        self.horizontal_scroll = ttk.Scrollbar(output, orient="horizontal", command=self.log.xview)
        self.horizontal_scroll.grid(row=1, column=0, sticky="ew")
        # Reserve the rails even while hidden. Showing a horizontal bar must
        # not remove a visible text line and change the horizontal extent
        # again, causing an endless show/hide geometry feedback loop.
        output.columnconfigure(1, minsize=self.vertical_scroll.winfo_reqwidth())
        self.scroll_rail_height = self.horizontal_scroll.winfo_reqheight()
        output.rowconfigure(1, minsize=self.scroll_rail_height)
        self.vertical_scroll.grid_remove()
        self.horizontal_scroll.grid_remove()
        self.log.configure(yscrollcommand=lambda first, last: self._scroll_visibility(self.vertical_scroll, first, last),
                           xscrollcommand=lambda first, last: self._scroll_visibility(self.horizontal_scroll, first, last))
        self.log.insert("end", "Scan the source before creating a backup.\n")
        # Start afresh each time; no window geometry is read or persisted.
        # Keep the previously approved width: move the row's 5px end gaps
        # into the shared body padding so all left/right edges align.
        self.update_idletasks()
        self.default_width = self.action_row.winfo_reqwidth() + 50
        self.minimum_height = max(570, self.winfo_reqheight() - self.scroll_rail_height)
        self.geometry(f"{self.default_width}x{self.minimum_height}")
        self.minsize(self.default_width, self.minimum_height)
        self.resizable(True, True)

    @staticmethod
    def _scroll_visibility(scrollbar, first, last):
        scrollbar.set(first, last)
        visible = not (float(first) <= 0 and float(last) >= 1)
        if not visible and scrollbar.grid_info():
            scrollbar.grid_remove()
        elif visible and not scrollbar.grid_info():
            scrollbar.grid()

    def _show_report(self):
        if self.last_scan_report is None:
            messagebox.showinfo('Scan required', 'Run Scan / Preview first to inspect file policies.')
            return
        if self.report_window is not None and self.report_window.winfo_exists():
            self.report_window.lift()
            return
        self.report_window = ReportBrowser(self, self.last_scan_report)

    def _show_about(self):
        if self.about_window is not None and self.about_window.winfo_exists():
            self.about_window.lift()
            return self.about_window
        self.about_window = AboutWindow(self)
        return self.about_window

    def _begin_vertical_resize(self, event):
        self._resize_start = (event.y_root, self.winfo_height())

    def _drag_vertical_resize(self, event):
        start = getattr(self, "_resize_start", None)
        if start is not None:
            height = max(self.minimum_height, start[1] + event.y_root - start[0])
            self.geometry(f"{self.winfo_width()}x{height}")

    @staticmethod
    def _select_restore_destination():
        parent = filedialog.askdirectory(title="Choose parent folder for new restored folder")
        return str(Path(parent) / "TimeCapsule-Restored") if parent else ""

    @staticmethod
    def _brief(result):
        return {key: result[key] for key in
                ("files", "counts", "bytes", "portable_names_ready", "portability_issues", "skipped_entries")}

    def _do(self, action):
        try:
            output = _bounded_report(action())
            self._report_generation = getattr(self, "_report_generation", 0) + 1
            generation = self._report_generation
            self.log.delete("1.0", "end")
            self._report_encoder = json.JSONEncoder(ensure_ascii=False, indent=2).iterencode(output)
            self._report_pending = ""
            self._report_chars = 0
            self._append_report_chunk(generation)
        except Exception as exc:
            messagebox.showerror("Time Capsule error", str(exc))

    def _append_report_chunk(self, generation):
        """Render a bounded report over multiple UI turns to keep Tk responsive."""
        if generation != getattr(self, "_report_generation", None):
            return
        parts = []
        chunk_size = 0
        truncated = False
        while chunk_size < GUI_REPORT_CHUNK_CHARS:
            if self._report_pending:
                part = self._report_pending
                self._report_pending = ""
            else:
                try:
                    part = next(self._report_encoder)
                except StopIteration:
                    break
            output_remaining = GUI_REPORT_MAX_CHARS - self._report_chars - chunk_size
            chunk_remaining = GUI_REPORT_CHUNK_CHARS - chunk_size
            allowed = min(output_remaining, chunk_remaining)
            if allowed <= 0:
                truncated = True
                break
            if len(part) > allowed:
                rest = part[allowed:]
                part = part[:allowed]
                if output_remaining > allowed:
                    self._report_pending = rest
                else:
                    truncated = True
            parts.append(part)
            chunk_size += len(part)
            if truncated:
                break
        if parts:
            self.log.insert("end", "".join(parts))
            self._report_chars += chunk_size
        if truncated or self._report_chars >= GUI_REPORT_MAX_CHARS:
            self.log.insert("end", "\n\n[Display shortened at 256 KiB to keep the interface responsive. Use the CLI for the complete report.]\n")
            return
        if chunk_size:
            self.after(1, lambda: self._append_report_chunk(generation))

    def _config_preview(self):
        """Explicit selection only; cancellation never starts comparison."""
        options = {"parent": self, "filetypes": [("INI files", "*.ini"), ("All files", "*")]}
        source = filedialog.askopenfilename(title="Select old reaper.ini (read-only)", **options)
        if not source:
            return
        target = filedialog.askopenfilename(title="Select clean target reaper.ini (read-only)", **options)
        if not target:
            return
        source_version = simpledialog.askstring(
            "Source REAPER version", "Version from your source installation records (e.g. 7.82).\n"
            "Leave blank if unknown; approved preferences will require review.", parent=self)
        if source_version is None:
            return
        target_version = simpledialog.askstring(
            "Target REAPER version", "Version from your target installation records (e.g. 7.82).\n"
            "Leave blank if unknown. Preview does not modify either configuration.", parent=self)
        if target_version is None:
            return
        self._do(lambda: self._configuration_report(preview_migration(
            source, target, source_version=source_version.strip() or None,
            target_version=target_version.strip() or None)))

    @staticmethod
    def _configuration_report(report):
        """Keep safety and conflict information visible in the existing report pane."""
        return {
            "Configuration preview": "Read-only; neither file has been modified.",
            "Version provenance": "Caller supplied; executable versions are not verified.",
            "Version compatible": report["version_compatible"],
            "Summary": report["summary"],
            "Changes": report["changes"],
            "Entries": report["entries"],
            "Preference evidence catalog": report["preference_catalog"],
            "Next step": "Review conflicts manually. No merge or export is available.",
        }

    def _set_busy(self, busy, label=""):
        for widget in self.interactive:
            widget.configure(state="disabled" if busy else "normal")
        self.status.set(label if busy else "Ready")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        if busy:
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
        else:
            self.progress.stop()

    def _start_io(self, operation):
        if self.runner.active:
            return
        # Capture Tk values on the main thread. Workers see ordinary strings only.
        source, archive, destination = self.source.get(), self.archive.get(), self.destination.get()
        self.operation_control = OperationControl()
        control = self.operation_control
        actions = {
            "scan": lambda: preview(source, control=control),
            "midi": lambda: validate_midi_workflow(Path(source), scan(source, control=control), control=control),
            "reapack": lambda: audit_reapack(source, control=control),
            "native-backup": lambda: make_backup(source, archive, control=control, native_names=True),
            "backup": lambda: make_backup(source, archive, control=control),
            "verify": lambda: preview_backup(archive, control=control),
            "restore": lambda: restore_backup(archive, destination, control=control),
        }
        self._set_busy(True, operation.capitalize() + " in progress — please wait")
        try:
            self.runner.submit(actions[operation])
        except Exception as exc:
            self._set_busy(False)
            messagebox.showerror("Time Capsule error", str(exc))
            return
        self.after(100, self._poll_io)

    def _cancel_io(self):
        if self.runner.active:
            self.operation_control.cancel()
            self.cancel_button.configure(state="disabled")
            self.status.set("Cancellation requested — waiting for safe cleanup")

    def _poll_io(self):
        progress = self.operation_control.latest()
        if progress is not None:
            phase, completed, total = progress
            if total > 0 and not self.operation_control.cancel_requested:
                self.progress.stop()
                self.progress.configure(mode="determinate", maximum=total, value=completed)
                self.status.set(f"{phase}: {min(100, completed * 100 // total)}% of this phase")
            elif not self.operation_control.cancel_requested:
                self.status.set(phase + " — please wait")
        result = self.runner.poll()
        if result is None:
            self.after(100, self._poll_io)
            return
        self._set_busy(False)
        kind, payload = result
        if kind == "cancelled":
            self.status.set("Operation cancelled; no completed result published")
        elif kind == "error":
            self.status.set("Operation failed")
            if isinstance(payload, NonPortableNames):
                if messagebox.askyesno('Native filenames require a different backup format',
                        'Some filenames cannot be represented in a portable backup. No files were renamed.\n\n'
                        'Create a native-name capsule instead? This requires a newer Time Capsule build. '
                        'Original-name recovery is restricted to the same platform; portable recovery '
                        'uses isolated files and a name-mapping report.'):
                    self._start_io('native-backup')
            else:
                messagebox.showerror("Time Capsule error", str(payload))
        else:
            self.status.set("Operation completed")
            if isinstance(payload, dict) and "items" in payload and "portable_names_ready" in payload:
                self.last_scan_report = scan_report(payload)
                self._do(lambda: App._brief(payload))
            else:
                self._do(lambda: payload)

    def _on_close(self):
        browser = getattr(self, "report_window", None)
        if browser is not None and browser.winfo_exists() and browser.runner.active:
            messagebox.showinfo("Report in progress", "Close the report window and wait for cleanup before exiting.")
            return
        if self.runner.active:
            messagebox.showinfo("Operation in progress", "Wait for the operation to finish before closing. "
                                "Use Cancel operation and wait for cleanup.")
            return
        self.destroy()

    def _restore(self):
        if messagebox.askyesno("Restore", "Restore to a NEW folder? Existing REAPER files will NOT be modified."):
            self._start_io("restore")
