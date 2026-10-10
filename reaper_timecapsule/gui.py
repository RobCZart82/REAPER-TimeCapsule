"""Small self-contained Tk desktop shell; advanced functions available via CLI."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import VERSION, default_resource, make_backup, preview, preview_backup, restore_backup, scan
from .midi_validation import validate_midi_workflow
from .reapack_profile import inspect_registry, parse_profile


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("REAPER TimeCapsule " + VERSION)
        self.geometry("1080x570")
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
            ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Browse", command=lambda v=variable, c=chooser: v.set(c() or v.get())).pack(side="left", padx=8)
        row = ttk.Frame(body)
        row.pack(anchor="w", pady=17)
        for label, fn in (
            ("Scan / Preview", lambda: self._do(lambda: self._brief(preview(self.source.get())))),
            ("MIDI Audit", lambda: self._do(lambda: validate_midi_workflow(Path(self.source.get()), scan(Path(self.source.get()))))),
            ("ReaPack Audit", lambda: self._do(lambda: {
                "profile": parse_profile(Path(self.source.get()) / "reapack.ini"),
                "registry": inspect_registry(Path(self.source.get()) / "ReaPack" / "registry.db"),
            })),
            ("Backup", lambda: self._do(lambda: make_backup(self.source.get(), self.archive.get()))),
            ("Verify", lambda: self._do(lambda: preview_backup(self.archive.get()))),
            ("Restore", self._restore),
        ):
            ttk.Button(row, text=label, command=fn).pack(side="left", padx=5)
        ttk.Label(body, text="REAPER must be closed. Restore NEVER overwrites an existing folder.").pack(anchor="w")
        ttk.Label(body, text="Machine-dependent and uncertain files are isolated under NeedsReview/.").pack(anchor="w")
        self.log = tk.Text(body, height=10, wrap="word")
        self.log.pack(fill="both", expand=True, pady=10)
        self.log.insert("end", "Scan the source before creating a backup.\n")

    @staticmethod
    def _select_restore_destination():
        parent = filedialog.askdirectory(title="Choose parent folder for new restored folder")
        return str(Path(parent) / "TimeCapsule-Restored") if parent else ""

    @staticmethod
    def _brief(result):
        return {"files": result["files"], "counts": result["counts"], "bytes": result["bytes"]}

    def _do(self, action):
        try:
            output = action()
            self.log.insert("end", json.dumps(output, ensure_ascii=False, indent=2) + "\n")
            self.log.see("end")
        except Exception as exc:
            messagebox.showerror("TimeCapsule error", str(exc))

    def _restore(self):
        if messagebox.askyesno("Restore", "Restore to a NEW folder? Existing REAPER files will NOT be modified."):
            self._do(lambda: restore_backup(self.archive.get(), self.destination.get()))
