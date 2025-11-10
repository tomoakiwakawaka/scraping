import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ehf import scrape_player_data, save_to_csv

class ScraperGUIDirect(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Scraper GUI - Direct Execution')
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

        # Buttons
        self.run_btn = ttk.Button(frm, text='Run Scraper', command=self.on_run)
        self.run_btn.grid(column=0, row=4, pady=(12,6), sticky='w')

        ttk.Button(frm, text='Quit', command=self.quit).grid(column=1, row=4, pady=(12,6), sticky='w')

        # Output console
        ttk.Label(frm, text='Output:').grid(column=0, row=5, sticky='w')
        self.txt = tk.Text(frm, height=18, wrap='none')
        self.txt.grid(column=0, row=6, columnspan=3, sticky='nsew', pady=(4,0))
        scrollbar = ttk.Scrollbar(frm, orient='vertical', command=self.txt.yview)
        scrollbar.grid(column=3, row=6, sticky='ns')
        self.txt['yscrollcommand'] = scrollbar.set

        # Layout weight
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(6, weight=1)

    def on_run(self):
        url = self.url_var.get().strip()
        out = self.out_var.get().strip()
        debug = self.debug_var.get()

        if not url:
            messagebox.showwarning('Missing URL', 'URLを入力してください。')
            return

        self.run_btn.config(state='disabled')
        self.txt.delete('1.0', tk.END)

        try:
            # スクレイピング実行
            self.txt.insert(tk.END, f'Starting scrape for URL: {url}\n')
            roster = scrape_player_data(url)

            if not roster:
                self.txt.insert(tk.END, 'No player data found.\n')
                if debug:
                    import requests
                    try:
                        resp = requests.get(url, timeout=10)
                        with open('debug.html', 'wb') as f:
                            f.write(resp.content)
                        self.txt.insert(tk.END, 'Saved fetched HTML to debug.html for inspection.\n')
                    except Exception as e:
                        self.txt.insert(tk.END, f'Could not fetch/save debug HTML: {e}\n')
            else:
                save_to_csv(roster, out)
                self.txt.insert(tk.END, f'Data saved to {out}\n')

        except Exception as e:
            self.txt.insert(tk.END, f'Error: {e}\n')

        finally:
            self.run_btn.config(state='normal')


def main():
    app = ScraperGUIDirect()
    app.mainloop()


if __name__ == '__main__':
    main()