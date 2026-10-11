"""Small self-contained Tk desktop shell; advanced functions available via CLI."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .background import BackgroundTask
from .operation import OperationControl
from .core import VERSION, default_resource, make_backup, preview, preview_backup, restore_backup, scan
from .midi_validation import validate_midi_workflow
from .config_migration import preview_migration
from .reapack_profile import inspect_registry, parse_profile


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("REAPER TimeCapsule " + VERSION)
        self.geometry("1080x570")
        self.runner = BackgroundTask()
        self.interactive = []
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.source = tk.StringVar(value=str(default_resource()))
        self.archive = tk.StringVar()
        self.destination = tk.StringVar(value=str(Path.home() / "Desktop" / "TimeCapsule-Restored"))
        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="REAPER TimeCapsule — Smart Backup", font=("Arial", 17, "bold")).pack(anchor="w", pady=(0, 14))
        for label, variable, chooser in (
            ("REAPER resource folder", self.source, filedialog.askdirectory),
            ("Snapshot ZIP", self.archive, lambda: filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])) ,
            ("Restore to NEW folder", self.destination, self._select_restore_destination),
        ):
            row = ttk.Frame(body)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=26).pack(side="left")
            entry = ttk.Entry(row, textvariable=variable)
            entry.pack(side="left", fill="x", expand=True)
            browse = ttk.Button(row, text="Browse", command=lambda v=variable, c=chooser: v.set(c() or v.get()))
            browse.pack(side="left", padx=8)
            self.interactive.extend((entry, browse))
        archive_choices = ttk.Frame(body)
        archive_choices.pack(anchor="w", pady=3)
        for label, chooser in (("Open existing snapshot", lambda: filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])),
                               ("Choose new backup ZIP", lambda: filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")]))):
            button = ttk.Button(archive_choices, text=label, command=lambda c=chooser: self.archive.set(c() or self.archive.get()))
            button.pack(side="left", padx=5)
            self.interactive.append(button)
        row = ttk.Frame(body)
        row.pack(anchor="w", pady=17)
        for label, fn in (
            ("Scan / Preview", lambda: self._do(lambda: self._brief(preview(self.source.get())))),
            ("MIDI Audit", lambda: self._do(lambda: validate_midi_workflow(Path(self.source.get()), scan(Path(self.source.get()))))),
            ("ReaPack Audit", lambda: self._do(lambda: {
                "profile": parse_profile(Path(self.source.get()) / "reapack.ini"),
                "registry": inspect_registry(Path(self.source.get()) / "ReaPack" / "registry.db"),
            })),
            ("Config Preview", self._config_preview),
            ("Backup", lambda: self._start_io("backup")),
            ("Verify", lambda: self._start_io("verify")),
            ("Restore", self._restore),
        ):
            button = ttk.Button(row, text=label, command=fn)
            button.pack(side="left", padx=5)
            self.interactive.append(button)
        ttk.Label(body, text="REAPER must be closed. Restore NEVER overwrites an existing folder.").pack(anchor="w")
        ttk.Label(body, text="Machine-dependent and uncertain files are isolated under NeedsReview/.").pack(anchor="w")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(body, textvariable=self.status).pack(anchor="w")
        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.pack(fill="x", pady=4)
        self.cancel_button = ttk.Button(body, text="Cancel operation", command=self._cancel_io, state="disabled")
        self.cancel_button.pack(anchor="w")
        self.log = tk.Text(body, height=10, wrap="word")
        self.log.pack(fill="both", expand=True, pady=10)
        self.log.insert("end", "Scan the source before creating a backup.\n")

    @staticmethod
    def _select_restore_destination():
        parent = filedialog.askdirectory(title="Choose parent folder for new restored folder")
        return str(Path(parent) / "TimeCapsule-Restored") if parent else ""

    @staticmethod
    def _brief(result):
        return {key: result[key] for key in
                ("files", "counts", "bytes", "portable_names_ready", "portability_issues")}

    def _do(self, action):
        try:
            output = action()
            self.log.insert("end", json.dumps(output, ensure_ascii=False, indent=2) + "\n")
            self.log.see("end")
        except Exception as exc:
            messagebox.showerror("TimeCapsule error", str(exc))

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
            "backup": lambda: make_backup(source, archive, control=control),
            "verify": lambda: preview_backup(archive, control=control),
            "restore": lambda: restore_backup(archive, destination, control=control),
        }
        self._set_busy(True, operation.capitalize() + " in progress — please wait")
        try:
            self.runner.submit(actions[operation])
        except Exception as exc:
            self._set_busy(False)
            messagebox.showerror("TimeCapsule error", str(exc))
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
            messagebox.showerror("TimeCapsule error", str(payload))
        else:
            self.status.set("Operation completed")
            self._do(lambda: payload)

    def _on_close(self):
        if self.runner.active:
            messagebox.showinfo("Operation in progress", "Wait for the operation to finish before closing. "
                                "Use Cancel operation and wait for cleanup.")
            return
        self.destroy()

    def _restore(self):
        if messagebox.askyesno("Restore", "Restore to a NEW folder? Existing REAPER files will NOT be modified."):
            self._start_io("restore")
