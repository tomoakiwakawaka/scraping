#!/usr/bin/env python3
"""
シンプルなTkinterベースのGUIアプリ
URLを入力して `scrap.py` を実行するための小さなフロントエンドです。

使い方:
  python3 scraper_gui.py

このファイルは同じディレクトリにある `scrap.py` を呼び出します。
まずローカルの `.venv/bin/python` を探し、無ければ `sys.executable` を使います。
"""
import os
import sys
import threading
import subprocess
import queue
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox


def get_default_python():
    # プロジェクトの仮想環境を優先
    base = os.path.dirname(__file__)
    candidate = os.path.join(base, '.venv', 'bin', 'python')
    if os.path.exists(candidate):
        return candidate
    # フォールバック
    return sys.executable or 'python3'


class ScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Scraper GUI')
        self.geometry('700x480')

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill='both', expand=True)

        # URL
        ttk.Label(frm, text='Team page URL:').grid(column=0, row=0, sticky='w')
        self.url_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.url_var, width=80).grid(column=0, row=1, columnspan=3, sticky='ew', pady=(0,8))

        # Output filename
        ttk.Label(frm, text='Output CSV filename:').grid(column=0, row=2, sticky='w')
        self.out_var = tk.StringVar(value='player_roster.csv')
        ttk.Entry(frm, textvariable=self.out_var, width=40).grid(column=0, row=3, sticky='w')

        # Debug checkbox
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text='Save debug HTML when no data (--debug)', variable=self.debug_var).grid(column=1, row=3, sticky='w', padx=(8,0))

        # Python interpreter path
        ttk.Label(frm, text='Python interpreter (optional):').grid(column=0, row=4, sticky='w', pady=(10,0))
        self.python_var = tk.StringVar(value=get_default_python())
        py_entry = ttk.Entry(frm, textvariable=self.python_var, width=60)
        py_entry.grid(column=0, row=5, sticky='w')
        ttk.Button(frm, text='Browse', command=self.browse_python).grid(column=1, row=5, sticky='w', padx=(6,0))

        # Buttons
        self.run_btn = ttk.Button(frm, text='Run Scraper', command=self.on_run)
        self.run_btn.grid(column=0, row=6, pady=(12,6), sticky='w')

        ttk.Button(frm, text='Quit', command=self.quit).grid(column=1, row=6, pady=(12,6), sticky='w')

        # Output console
        ttk.Label(frm, text='Output:').grid(column=0, row=7, sticky='w')
        self.txt = tk.Text(frm, height=18, wrap='none')
        self.txt.grid(column=0, row=8, columnspan=3, sticky='nsew', pady=(4,0))
        scrollbar = ttk.Scrollbar(frm, orient='vertical', command=self.txt.yview)
        scrollbar.grid(column=3, row=8, sticky='ns')
        self.txt['yscrollcommand'] = scrollbar.set

        # Layout weight
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(8, weight=1)

        # thread -> ui queue
        self._q = queue.Queue()
        self._proc = None

        # schedule UI updater
        self.after(100, self._poll_queue)

    def browse_python(self):
        path = filedialog.askopenfilename(title='Select python executable')
        if path:
            self.python_var.set(path)

    def on_run(self):
        url = self.url_var.get().strip()
        out = self.out_var.get().strip()
        py = self.python_var.get().strip() or get_default_python()
        debug = self.debug_var.get()

        if not url:
            messagebox.showwarning('Missing URL', 'URLを入力してください。')
            return

        # disable button
        self.run_btn.config(state='disabled')
        self.txt.delete('1.0', tk.END)

        t = threading.Thread(target=self._run_scraper, args=(py, url, out, debug), daemon=True)
        t.start()

    def _run_scraper(self, python_exec, url, out, debug):
        try:
            script = os.path.join(os.path.dirname(__file__), 'scrap.py')
            cmd = [python_exec, script, '--url', url, '--output', out]
            if debug:
                cmd.append('--debug')

            self._q.put((None, f'Running: {" ".join(cmd)}\n'))

            # run the process and stream output
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(__file__), text=True, bufsize=1)
            self._proc = p
            for line in p.stdout or []:
                self._q.put((None, line))
            p.wait()
            ret = p.returncode
            self._q.put((None, f'Process exited with code {ret}\n'))
        except FileNotFoundError as e:
            self._q.put((None, f'Error: {e}\n'))
        except Exception as e:
            self._q.put((None, f'Unexpected error: {e}\n'))
        finally:
            self._q.put(('done', None))

    def _poll_queue(self):
        try:
            while True:
                item = self._q.get_nowait()
                tag, text = item
                if tag == 'done':
                    self.run_btn.config(state='normal')
                    self._proc = None
                else:
                    self.txt.insert(tk.END, text)
                    self.txt.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)


def main():
    app = ScraperGUI()
    app.mainloop()


if __name__ == '__main__':
    main()
