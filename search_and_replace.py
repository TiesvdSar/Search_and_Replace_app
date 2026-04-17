import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import os
import re
import shutil
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".txt", ".csv", ".json", ".xml", ".html", ".htm",
    ".py", ".js", ".ts", ".css", ".md", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".log", ".bat", ".sh",
}

ACCENT = "#2563EB"
BG = "#F8FAFC"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT = "#1E293B"
MUTED = "#64748B"
SUCCESS = "#16A34A"
ERROR = "#DC2626"


class MassReplaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Massa Replace")
        self.root.configure(bg=BG)
        self.root.minsize(700, 620)
        self.root.resizable(True, True)

        self.target_paths = []
        self.csv_path = tk.StringVar()
        self.mappings = []

        self.opt_case_sensitive = tk.BooleanVar(value=False)
        self.opt_whole_word = tk.BooleanVar(value=False)
        self.opt_backup = tk.BooleanVar(value=True)
        self.opt_recursive = tk.BooleanVar(value=False)

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Title
        tk.Label(outer, text="Massa Replace", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 14))

        # ── Section 1: Target files ───────────────────────────────────────────
        self._section(outer, "1  Kies bestanden of map")

        files_frame = self._card(outer)
        self.files_listbox = tk.Listbox(
            files_frame, height=4, bg=CARD, fg=TEXT,
            selectbackground=ACCENT, activestyle="none",
            font=("Segoe UI", 9), bd=0, highlightthickness=0,
            relief="flat",
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=6)
        sb = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=6)
        self.files_listbox.configure(yscrollcommand=sb.set)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill=tk.X, pady=(4, 10))
        self._btn(btn_row, "Bestanden kiezen", self._pick_files).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(btn_row, "Map kiezen", self._pick_folder).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(btn_row, "Wissen", self._clear_files, danger=True).pack(side=tk.LEFT)

        # ── Section 2: CSV mapping ────────────────────────────────────────────
        self._section(outer, "2  CSV-bestand  (kolommen: oud, nieuw)")

        csv_frame = tk.Frame(outer, bg=BG)
        csv_frame.pack(fill=tk.X, pady=(4, 0))

        self.csv_entry = tk.Entry(
            csv_frame, textvariable=self.csv_path,
            font=("Segoe UI", 9), bg=CARD, fg=TEXT,
            bd=1, relief="solid", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        self.csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 6))
        self._btn(csv_frame, "Bladeren", self._pick_csv).pack(side=tk.LEFT)

        # Preview table
        self.preview_frame = tk.Frame(outer, bg=BG)
        self.preview_frame.pack(fill=tk.X, pady=(6, 10))

        # ── Section 3: Options ────────────────────────────────────────────────
        self._section(outer, "3  Opties")

        opts = tk.Frame(outer, bg=BG)
        opts.pack(fill=tk.X, pady=(4, 14))
        checks = [
            ("Hoofdlettergevoelig", self.opt_case_sensitive),
            ("Heel woord",         self.opt_whole_word),
            ("Maak backup",        self.opt_backup),
            ("Submappen doorzoeken", self.opt_recursive),
        ]
        for label, var in checks:
            tk.Checkbutton(
                opts, text=label, variable=var,
                bg=BG, fg=TEXT, activebackground=BG,
                selectcolor=CARD, font=("Segoe UI", 9),
            ).pack(side=tk.LEFT, padx=(0, 18))

        # ── Start button ──────────────────────────────────────────────────────
        tk.Button(
            outer, text="Start vervangen", command=self._run,
            bg=ACCENT, fg="white", activebackground="#1D4ED8",
            font=("Segoe UI", 11, "bold"), bd=0, padx=20, pady=8,
            cursor="hand2", relief="flat",
        ).pack(anchor="w", pady=(0, 12))

        # ── Log ───────────────────────────────────────────────────────────────
        self._section(outer, "Logboek")
        self.log = scrolledtext.ScrolledText(
            outer, height=8, bg="#0F172A", fg="#94A3B8",
            font=("Consolas", 8), bd=0, relief="flat",
            insertbackground="white", wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_configure("ok",  foreground="#4ADE80")
        self.log.tag_configure("err", foreground="#F87171")
        self.log.tag_configure("inf", foreground="#60A5FA")

    # ── Helper widgets ────────────────────────────────────────────────────────

    def _section(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(6, 2))

    def _card(self, parent):
        f = tk.Frame(parent, bg=CARD, bd=1, relief="solid",
                     highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill=tk.X, pady=(2, 0))
        return f

    def _btn(self, parent, text, cmd, danger=False):
        color = "#EF4444" if danger else ACCENT
        hover = "#B91C1C" if danger else "#1D4ED8"
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="white", activebackground=hover,
            font=("Segoe UI", 9), bd=0, padx=12, pady=5,
            cursor="hand2", relief="flat",
        )
        return b

    # ── Actions ───────────────────────────────────────────────────────────────

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Kies bestanden",
            filetypes=[("Tekstbestanden", " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)),
                       ("Alle bestanden", "*.*")],
        )
        for p in paths:
            if p not in self.target_paths:
                self.target_paths.append(p)
                self.files_listbox.insert(tk.END, p)

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Kies een map")
        if folder and folder not in self.target_paths:
            self.target_paths.append(folder)
            self.files_listbox.insert(tk.END, f"[map]  {folder}")

    def _clear_files(self):
        self.target_paths.clear()
        self.files_listbox.delete(0, tk.END)

    def _pick_csv(self):
        path = filedialog.askopenfilename(
            title="Kies CSV-bestand",
            filetypes=[("CSV-bestanden", "*.csv"), ("Alle bestanden", "*.*")],
        )
        if path:
            self.csv_path.set(path)
            self._load_csv(path)

    def _load_csv(self, path):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        self.mappings = []
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            messagebox.showerror("CSV-fout", str(e))
            return

        if not rows:
            return

        header = [h.strip().lower() for h in rows[0]]
        old_idx, new_idx = self._find_csv_columns(header)
        data_rows = rows[1:] if old_idx is not None else rows

        if old_idx is None:
            old_idx, new_idx = 0, 1

        for row in data_rows:
            if len(row) > max(old_idx, new_idx):
                old_val = row[old_idx].strip()
                new_val = row[new_idx].strip()
                if old_val:
                    self.mappings.append((old_val, new_val))

        self._render_preview()

    def _find_csv_columns(self, header):
        old_names = {"oud", "old", "zoek", "search", "van", "from", "original"}
        new_names = {"nieuw", "new", "vervang", "replace", "naar", "to", "replacement"}
        old_idx = new_idx = None
        for i, h in enumerate(header):
            if h in old_names and old_idx is None:
                old_idx = i
            if h in new_names and new_idx is None:
                new_idx = i
        return old_idx, new_idx

    def _render_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        if not self.mappings:
            return

        cols = ("Oud (zoeken)", "Nieuw (vervangen)")
        tree = ttk.Treeview(self.preview_frame, columns=cols, show="headings", height=5)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=260, anchor="w")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=22,
                        background=CARD, fieldbackground=CARD, foreground=TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        for old, new in self.mappings[:50]:
            tree.insert("", tk.END, values=(old, new))

        if len(self.mappings) > 50:
            tree.insert("", tk.END, values=(f"… {len(self.mappings) - 50} meer rijen", ""))

        vsb = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log(f"CSV geladen: {len(self.mappings)} vervangingen gevonden.", "inf")

    # ── Core replacement logic ────────────────────────────────────────────────

    def _collect_files(self):
        files = []
        recursive = self.opt_recursive.get()
        for path in self.target_paths:
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                pattern = "**/*" if recursive else "*"
                for f in Path(path).glob(pattern):
                    if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files.append(str(f))
        return files

    def _make_pattern(self, old_text):
        escaped = re.escape(old_text)
        if self.opt_whole_word.get():
            escaped = r"\b" + escaped + r"\b"
        flags = 0 if self.opt_case_sensitive.get() else re.IGNORECASE
        return re.compile(escaped, flags)

    def _replace_in_file(self, filepath, mappings):
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return False, f"Leesfout: {e}", 0

        original = content
        total_count = 0
        for old, new in mappings:
            pattern = self._make_pattern(old)
            new_content, n = pattern.subn(new, content)
            total_count += n
            content = new_content

        if content == original:
            return True, None, 0

        if self.opt_backup.get():
            try:
                shutil.copy2(filepath, filepath + ".bak")
            except Exception as e:
                return False, f"Backupfout: {e}", 0

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            return False, f"Schrijffout: {e}", 0

        return True, None, total_count

    def _run(self):
        if not self.target_paths:
            messagebox.showwarning("Geen bestanden", "Kies eerst bestanden of een map.")
            return
        if not self.mappings:
            if not self.csv_path.get():
                messagebox.showwarning("Geen CSV", "Kies eerst een CSV-bestand.")
            else:
                messagebox.showwarning("Lege CSV", "Het CSV-bestand bevat geen geldige rijen.")
            return

        files = self._collect_files()
        if not files:
            messagebox.showinfo("Geen bestanden gevonden",
                                "Geen ondersteunde bestanden gevonden in de opgegeven locaties.")
            return

        self._log(f"Start — {len(files)} bestanden, {len(self.mappings)} vervangingen…", "inf")
        changed = 0
        errors = 0

        for filepath in files:
            ok, err, count = self._replace_in_file(filepath, self.mappings)
            name = os.path.basename(filepath)
            if not ok:
                self._log(f"  ✗  {name}: {err}", "err")
                errors += 1
            elif count:
                self._log(f"  ✓  {name}: {count}× vervangen", "ok")
                changed += 1
            else:
                self._log(f"  –  {name}: niets gevonden", "inf")

        self._log(
            f"\nKlaar — {changed}/{len(files)} bestanden gewijzigd"
            + (f", {errors} fout(en)" if errors else "") + ".",
            "ok" if not errors else "err",
        )
        messagebox.showinfo(
            "Klaar",
            f"{changed} van {len(files)} bestanden gewijzigd."
            + (f"\n{errors} fout(en) — zie het logboek." if errors else ""),
        )

    # ── Log helper ────────────────────────────────────────────────────────────

    def _log(self, message, tag="inf"):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n", tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = MassReplaceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
