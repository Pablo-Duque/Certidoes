import os
import sys
from threading import Thread

import tkinter as tk
from tkinter import ttk

from certidoes import Bot


class App:
    def __init__(self, root):
        self.root = root

        self.keys = [
            "cadastro",
            "simples",
            "cnd",
            "fgts",
            "cndt",
        ]

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

        style.configure(
            "Entry.TEntry",
            fieldbackground="#1a1d24",
            foreground="white",
            insertcolor="white",
        )

        style.configure("Blue.TButton", background="#1d4ed8", foreground="white")
        style.map(
            "Blue.TButton",
            background=[
                ("active", "#0642c4"),
                ("pressed", "#0332cc"),
            ],
        )

    def format_cnpj(self, *_):
        value = self.cnpj_var.get()

        digits = "".join(filter(str.isdigit, value))[:14]
        cursor_pos = self.entry.index(tk.INSERT)
        was_at_end = cursor_pos == len(value)

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
        if was_at_end:
            self.root.after(1, lambda: self.entry.icursor("end"))

    def toggle_all(self):
        value = self.select_all_var.get()

        for key in ("cnd", "fgts", "cndt"):
            self.check_vars[key].set(value)

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

        self.check_vars = {
            "cadastro": tk.BooleanVar(value=True),
            "simples": tk.BooleanVar(value=True),
            "cnd": tk.BooleanVar(value=False),
            "fgts": tk.BooleanVar(value=False),
            "cndt": tk.BooleanVar(value=False),
        }

        self.options_frame = tk.Frame(self.main, bg="#0f1115")
        self.options_frame.pack(pady=15)

        self.checkbuttons = {}
        self.option_labels = {}

        for key in self.keys:
            row = tk.Frame(self.options_frame, bg="#0f1115")
            row.pack(anchor="w")

            chk = tk.Checkbutton(
                row,
                variable=self.check_vars[key],
                bg="#0f1115",
                fg="white",
                selectcolor="#0f1115",
                activebackground="#0f1115",
                state=("disabled" if key in ("cadastro", "simples") else "normal"),
            )
            chk.pack(side="left")

            label = tk.Label(
                row,
                text=self.labels[key],
                fg=("#808080" if key in ("cadastro", "simples") else "white"),
                bg="#0f1115",
                width=20,
                anchor="w",
                font=("Segoe UI", 10),
            )
            label.pack(side="left")

            self.checkbuttons[key] = chk
            self.option_labels[key] = label

        self.select_all_var = tk.BooleanVar()

        row = tk.Frame(self.options_frame, bg="#0f1115")
        row.pack(anchor="w")

        tk.Checkbutton(
            row,
            variable=self.select_all_var,
            command=self.toggle_all,
            bg="#0f1115",
            fg="white",
            selectcolor="#0f1115",
            activebackground="#0f1115",
        ).pack(side="left")

        tk.Label(
            row,
            text="Marcar todos",
            fg="white",
            bg="#0f1115",
            width=20,
            anchor="w",
            font=("Segoe UI", 10),
        ).pack(side="left")

        self.btn = ttk.Button(
            self.main,
            text="Gerar Certidões",
            command=self.start_process,
            style="Blue.TButton",
        )
        self.btn.pack(pady=15)

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

        selected_keys = [key for key, var in self.check_vars.items() if var.get()]

        self.show_loading()

        Thread(
            target=self.run_bot,
            args=(cnpj, selected_keys),
            daemon=True,
        ).start()

    def run_bot(self, cnpj, selected_keys):
        bot = Bot(cnpj, selected_keys)

        result = bot.search()

        self.root.after(0, lambda: self.finish(result))

    def set_result(self, key, text, color):
        if key in self.result_labels:
            self.result_labels[key].config(text=text, fg=color)

    def apply_result(self, result):
        for key in self.keys:
            if key not in result:
                self.set_result(key, f"{self.labels[key]}: Não selecionado", "#FFFFFF")

            elif result[key] is None:
                self.set_result(
                    key, f"{self.labels[key]}: Erro de atribuição", "#FC1B1B"
                )

            else:
                text, color = result[key]

                self.set_result(key, f"{self.labels[key]}: {text}", color)

    def finish(self, result):
        for key in self.keys:
            if key not in result:
                text = "Não selecionado"
                color = "#FFFFFF"

            elif result[key] is None:
                text = "Erro de atribuição"
                color = "#FC1B1B"

            else:
                text, color = result[key]

            self.option_labels[key].config(text=f"{self.labels[key]}: {text}", fg=color)

            self.checkbuttons[key].config(state="disabled")

        self.select_all_var.set(False)
        self.btn.config(text="Consultar Novamente")
        self.btn.config(command=self.reset_screen)

        self.show_main()

    def reset_screen(self):
        for key in self.keys:
            self.option_labels[key].config(
                text=self.labels[key],
                fg=("#808080" if key in ("cadastro", "simples") else "white"),
            )

            self.checkbuttons[key].config(
                state=("disabled" if key in ("cadastro", "simples") else "normal")
            )

        self.btn.config(text="Gerar Certidões", command=self.start_process)
