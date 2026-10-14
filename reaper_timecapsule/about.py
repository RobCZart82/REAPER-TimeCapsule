"""Local branding resources and a non-modal About window."""
from pathlib import Path
import tkinter as tk
import webbrowser

from .core import VERSION

ASSETS = Path(__file__).with_name('assets')
PROJECT_URL = 'https://github.com/RobCZart82/REAPER-TimeCapsule'


def brand_image(master, name, *, half=False):
    image = tk.PhotoImage(master=master, file=str(ASSETS / name))
    return image.subsample(2) if half else image


class AboutWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('About REAPER Time Capsule')
        self.transient(parent)
        self.resizable(False, False)
        bg, paper, muted, accent = '#14222e', '#eee9dc', '#a8bbc5', '#32b9b1'
        self.configure(background=bg)
        self.images = {
            'icon': brand_image(self, 'timecapsule-96.png', half=True),
            'logo': brand_image(self, 'gyr-light.png', half=True),
            'signature': brand_image(self, 'signature-light.png', half=True),
        }
        body = tk.Frame(self, background=bg, padx=32, pady=26)
        body.pack(fill='both', expand=True)
        # Shared columns keep the creator logo below the floppy and the
        # signature on the same horizontal centerline as every text label.
        body.columnconfigure(0, minsize=118)
        body.columnconfigure(1, weight=1)
        self.icon_label = tk.Label(body, image=self.images['icon'], background=bg)
        self.icon_label.grid(row=0, column=0, sticky='n', padx=(0, 22))
        title = tk.Frame(body, background=bg)
        title.grid(row=0, column=1, sticky='ew')
        self.title_label = tk.Label(title, text='REAPER Time Capsule', font=('Arial', 22, 'bold'),
                                   foreground=paper, background=bg)
        self.title_label.pack()
        tk.Label(title, text='Preserve your REAPER setup.\nRestore with confidence.',
                 font=('Arial', 11), justify='center', foreground=muted, background=bg).pack(pady=(8, 0))
        tk.Label(title, text=f'VERSION {VERSION}', font=('Arial', 10, 'bold'),
                 foreground=accent, background=bg).pack(pady=(18, 0))
        tk.Frame(body, background='#35505e', height=1).grid(row=1, column=0, columnspan=2,
                                                          sticky='ew', pady=(18, 20))
        self.logo_label = tk.Label(body, image=self.images['logo'], background=bg)
        self.logo_label.grid(row=2, column=0, padx=(0, 22))
        self.signature_label = tk.Label(body, image=self.images['signature'], background=bg)
        self.signature_label.grid(row=2, column=1)
        tk.Frame(body, background='#35505e', height=1).grid(row=3, column=0, columnspan=2,
                                                          sticky='ew', pady=(16, 0))
        tk.Label(body, text='Offline backups · Read-only previews · Careful recovery',
                 font=('Arial', 10), foreground=muted, background=bg).grid(row=4, column=1, pady=(16, 5))
        tk.Label(body, text='GPL-3.0-only · Provided without warranty\nIndependent project — not affiliated with Cockos / REAPER.',
                 font=('Arial', 9), foreground=muted, background=bg, justify='center').grid(row=5, column=1)
        footer = tk.Frame(body, background=bg)
        footer.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(18, 0))
        link = tk.Label(footer, text='Project & documentation ↗', font=('Arial', 10, 'underline'),
                        foreground=accent, background=bg, cursor='hand2', takefocus=True)
        link.pack(side='left')
        link.bind('<Button-1>', lambda event: webbrowser.open(PROJECT_URL))
        link.bind('<Return>', lambda event: webbrowser.open(PROJECT_URL))
        tk.Button(footer, text='Close', command=self.destroy, padx=18, pady=3,
                  highlightthickness=0).pack(side='right')
        self.bind('<Escape>', lambda event: self.destroy())
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        # A leading '+' selects absolute desktop coordinates; the following
        # signed value preserves monitors left of/above the primary display.
        self.geometry(f'+{x}+{y}')
