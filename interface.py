import os
import sys
import tkinter as tk

from threading import Thread
from tkinter import ttk
from certidoes import Bot


class App:
    def __init__(self, root):
        self.root = root

        self.keys = ["cadastro", "simples", "cnd", "fgts", "cndt"]

        self.labels = {
            "cadastro": "Situação Cadastral",
            "simples": "Simples",
            "cnd": "CND",
            "fgts": "FGTS",
            "cndt": "CNDT",
        }

        self._config()
        self._center(600, 400)

        self._style()

        self._build_main()
        self.entry.bind("<Return>", self.start_process)
        self._build_loading()

        self.show_main()

    def _config(self):
        self.root.title("Certidões")
        if hasattr(sys, "_MEIPASS"):
            ico_path = os.path.join(sys._MEIPASS, "iconBy814anonimo.ico")
        else:
            ico_path = "./iconBy814anonimo.ico"
        if os.path.exists(ico_path):
            self.root.iconbitmap(ico_path)

        self.root.configure(bg="#0f1115")
        self.root.resizable(False, False)

    def _center(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Entry.TEntry", fieldbackground="#1a1d24", foreground="white")
        style.configure("Blue.TButton", background="#2563eb", foreground="white")

    def format_cnpj(self, *_):
        value = self.cnpj_var.get()
        entry = self.entry

        digits = "".join(filter(str.isdigit, value))[:14]

        formatted = ""

        if len(digits) > 0:
            formatted += digits[:2]
        if len(digits) > 2:
            formatted += "." + digits[2:5]
        if len(digits) > 5:
            formatted += "." + digits[5:8]
        if len(digits) > 8:
            formatted += "/" + digits[8:12]
        if len(digits) > 12:
            formatted += "-" + digits[12:14]

        self.cnpj_var.trace_remove("write", self.trace_id)

        self.cnpj_var.set(formatted)

        self.trace_id = self.cnpj_var.trace_add("write", self.format_cnpj)

        self.root.after(1, lambda: entry.icursor("end"))

    def _build_main(self):
        self.main = tk.Frame(self.root, bg="#0f1115")

        tk.Label(
            self.main,
            text="CNPJ",
            fg="white",
            bg="#0f1115",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(20, 10))

        self.cnpj_var = tk.StringVar()
        self.trace_id = self.cnpj_var.trace_add("write", self.format_cnpj)
        self.entry = ttk.Entry(
            self.main,
            textvariable=self.cnpj_var,
            justify="center",
            style="Entry.TEntry",
        )
        self.entry.pack(ipadx=10, ipady=6)
        self.entry.focus_set()

        self.btn = ttk.Button(
            self.main,
            text="Gerar Certidões",
            command=self.start_process,
            style="Blue.TButton",
        )
        self.btn.pack(pady=15)

        self.result_labels = {}

        for key in self.keys:
            lbl = tk.Label(
                self.main,
                text=f"{self.labels[key]}: Aguardando...",
                fg="#ffffff",
                bg="#0f1115",
                font=("Segoe UI", 10),
            )
            lbl.pack(pady=(15, 0))

            self.result_labels[key] = lbl

    def _build_loading(self):
        self.loading = tk.Frame(self.root, bg="#0f1115")

        tk.Label(
            self.loading,
            text="Gerando certidões...",
            fg="white",
            bg="#0f1115",
            font=("Segoe UI", 12),
        ).pack(pady=60)

    def show_main(self):
        self.loading.pack_forget()
        self.main.pack(fill="both", expand=True)

    def show_loading(self):
        self.main.pack_forget()
        self.loading.pack(fill="both", expand=True)

    def start_process(self, event=None):
        cnpj = "".join(filter(str.isdigit, self.cnpj_var.get()))

        self.show_loading()

        Thread(target=self.run_bot, args=(cnpj,), daemon=True).start()

    def run_bot(self, cnpj):
        bot = Bot(cnpj, self.keys)
        result = bot.search()
        self.root.after(0, lambda: self.finish(result))

    def set_result(self, key, text, color):
        if key in self.result_labels:
            self.result_labels[key].config(text=text, fg=color)

    def apply_result(self, result):
        for key, (text, color) in result.items():
            self.set_result(key, f"{self.labels[key]}: {text}", color)

    def finish(self, result):
        self.apply_result(result)
        self.show_main()
