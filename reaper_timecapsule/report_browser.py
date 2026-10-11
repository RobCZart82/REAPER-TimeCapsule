"""Paginated read-only file policy browser; never opens inspected resource files."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .background import BackgroundTask
from .operation import OperationControl
from .reports import report_page, export_report, PAGE_SIZE


class ReportBrowser(tk.Toplevel):
    def __init__(self, parent, report):
        super().__init__(parent)
        self.title('File policies — REAPER Time Capsule')
        self.report, self.page_number = report, 0
        self.runner = BackgroundTask()
        self.control = OperationControl()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.geometry('960x560')
        self.minsize(640, 360)
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Read-only scan results • keep / review / regenerate / exclude').pack(anchor='w')
        ttk.Label(body, text='Completed scan: ' + report['generated_utc']).pack(anchor='w')
        ttk.Label(body, text='Source: ' + report['source_resource'], wraplength=900).pack(anchor='w')
        filters = ttk.Frame(body)
        filters.pack(fill='x', pady=8)
        self.policy = tk.StringVar(value='all')
        self.query = tk.StringVar()
        ttk.Combobox(filters, textvariable=self.policy, values=('all', 'keep', 'review', 'regenerate', 'exclude'), state='readonly', width=12).pack(side='left')
        ttk.Entry(filters, textvariable=self.query).pack(side='left', fill='x', expand=True, padx=8)
        ttk.Button(filters, text='Filter', command=self._filter).pack(side='left')
        table = ttk.Frame(body)
        table.pack(fill='both', expand=True)
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=('path', 'policy', 'size', 'reason'), show='headings')
        for key, width in [('path', 360), ('policy', 90), ('size', 100), ('reason', 420)]:
            self.tree.heading(key, text=key.capitalize())
            self.tree.column(key, width=width, stretch=False)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(table, orient='horizontal', command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        footer = ttk.Frame(body)
        footer.pack(fill='x', pady=(8, 0))
        self.previous = ttk.Button(footer, text='Previous', command=lambda: self._page(-1))
        self.previous.pack(side='left')
        self.next = ttk.Button(footer, text='Next', command=lambda: self._page(1))
        self.next.pack(side='left', padx=8)
        self.status = tk.StringVar()
        ttk.Label(footer, textvariable=self.status).pack(side='left')
        ttk.Button(footer, text='Export private JSON…', command=self._export).pack(side='right')
        self._render()

    def _filter(self):
        if self.runner.active:
            return
        self.page_number = 0
        self._render()

    def _page(self, direction):
        if self.runner.active:
            return
        self.page_number += direction
        self._render()

    def _render(self):
        if self.runner.active:
            return
        policy, query, number = self.policy.get(), self.query.get(), self.page_number
        self._start(lambda: report_page(self.report, policy=policy, query=query, page=number, control=self.control), 'page')

    def _show_page(self, page):
        self.tree.delete(*self.tree.get_children())
        for entry in page['rows']:
            self.tree.insert('', 'end', values=(entry['path'], entry['policy'], entry['size'], entry['reason']))
        self.previous.configure(state='normal' if self.page_number else 'disabled')
        self.next.configure(state='normal' if (self.page_number + 1) * PAGE_SIZE < page['matches'] else 'disabled')
        self.status.set(f"{page['matches']} matches • page {self.page_number + 1} • at most {PAGE_SIZE} rows")

    def _export(self):
        destination = filedialog.asksaveasfilename(parent=self, title='Export private report to NEW file', defaultextension='.json', filetypes=[('JSON', '*.json')])
        if destination and not self.runner.active and messagebox.askyesno(
                'Save private report?', 'The complete report may contain local paths and filenames. '
                'Save it only in a folder you trust. Continue?', parent=self):
            source = self.report.get('source_resource')
            self._start(lambda: export_report(self.report, destination, forbidden_root=source,
                                              control=self.control), 'export')

    def _start(self, action, kind):
        self.control = OperationControl()
        self.pending_kind = kind
        self.status.set('Working…')
        self.runner.submit(action)
        self.after(50, self._poll)

    def _poll(self):
        result = self.runner.poll()
        if result is None:
            self.after(50, self._poll)
            return
        kind, payload = result
        if kind == 'success' and self.pending_kind == 'page':
            self._show_page(payload)
        elif kind == 'success':
            self.status.set('Private report exported')
        elif kind == 'error':
            self.status.set('Operation failed')
            messagebox.showerror('Report operation failed', str(payload), parent=self)
        else:
            self.status.set('Operation cancelled')

    def _close(self):
        if self.runner.active:
            self.control.cancel()
            self.after(50, self._close_when_idle)
        else:
            self.destroy()

    def _close_when_idle(self):
        # Polling owns delivery; never destroy while its scheduled callback needs Tk.
        if self.runner.active:
            self.after(50, self._close_when_idle)
        else:
            self.destroy()
