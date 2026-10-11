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
        self.title('About REAPER TimeCapsule')
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
        heading = tk.Frame(body, background=bg)
        heading.pack(fill='x')
        tk.Label(heading, image=self.images['icon'], background=bg).pack(side='left', padx=(0, 22))
        title = tk.Frame(heading, background=bg)
        title.pack(side='left')
        tk.Label(title, text='REAPER TimeCapsule', font=('Arial', 22, 'bold'),
                 foreground=paper, background=bg).pack(anchor='w')
        tk.Label(title, text='Preserve your REAPER setup.\nRestore with confidence.',
                 font=('Arial', 11), justify='left', foreground=muted, background=bg).pack(anchor='w', pady=(8, 0))
        tk.Label(body, text=f'VERSION {VERSION}  ·  BETA', font=('Arial', 10, 'bold'),
                 foreground=accent, background=bg).pack(anchor='w', pady=(18, 16))
        tk.Frame(body, background='#35505e', height=1).pack(fill='x')
        identity = tk.Frame(body, background=bg)
        identity.pack(fill='x', pady=(20, 16))
        tk.Label(identity, image=self.images['logo'], background=bg).pack(side='left', padx=(24, 34))
        tk.Label(identity, image=self.images['signature'], background=bg).pack(side='right', padx=(12, 12))
        tk.Frame(body, background='#35505e', height=1).pack(fill='x')
        tk.Label(body, text='Offline backups · Read-only previews · Careful recovery',
                 font=('Arial', 10), foreground=muted, background=bg).pack(pady=(16, 5))
        tk.Label(body, text='GPL-3.0-only · Provided without warranty\nIndependent project — not affiliated with Cockos / REAPER.',
                 font=('Arial', 9), foreground=muted, background=bg, justify='center').pack()
        footer = tk.Frame(body, background=bg)
        footer.pack(fill='x', pady=(18, 0))
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
        self.geometry(f'+{max(0, x)}+{max(0, y)}')
