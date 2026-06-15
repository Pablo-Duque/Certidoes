import os
import sys
from threading import Thread

import tkinter as tk
from tkinter import ttk

from bot_worker import BotWorker


class App:
    def __init__(self, root):
        self._root = root
        self._root.protocol("WM_DELETE_WINDOW", self.close)

        self._keys = [
            "cadastro",
            "simples",
            "cnd",
            "fgts",
            "cndt",
        ]

        self._labels = {
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
        self._root.bind("<Return>", self.start_process)

        self._build_loading()

        self.show_main()

        self._worker = BotWorker()

    def _config(self):
        self._root.title("Certidões")

        if hasattr(sys, "_MEIPASS"):
            ico_path = os.path.join(sys._MEIPASS, "iconBy814anonimo.ico")
        else:
            ico_path = "./iconBy814anonimo.ico"

        if os.path.exists(ico_path):
            self._root.iconbitmap(ico_path)

        self._root.configure(bg="#0f1115")
        self._root.resizable(False, False)

    def _center(self, w, h):
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()

        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        self._root.geometry(f"{w}x{h}+{x}+{y}")

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
        value = self._cnpj_var.get()

        digits = "".join(filter(str.isdigit, value))[:14]
        cursor_pos = self._entry.index(tk.INSERT)
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

        self._cnpj_var.trace_remove("write", self._trace_id)
        self._cnpj_var.set(formatted)
        self._trace_id = self._cnpj_var.trace_add("write", self.format_cnpj)
        if was_at_end:
            self._root.after(1, lambda: self._entry.icursor("end"))

    def toggle_all(self):
        value = self._select_all_var.get()

        for key in ("simples", "cnd", "fgts", "cndt"):
            self._check_vars[key].set(value)

    def _build_main(self):
        self._main = tk.Frame(self._root, bg="#0f1115")

        tk.Label(
            self._main,
            text="CNPJ",
            fg="white",
            bg="#0f1115",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(20, 10))

        self._cnpj_var = tk.StringVar()

        self._trace_id = self._cnpj_var.trace_add("write", self.format_cnpj)

        self._entry = ttk.Entry(
            self._main,
            textvariable=self._cnpj_var,
            justify="center",
            style="Entry.TEntry",
        )
        self._entry.pack(ipadx=10, ipady=6)
        self._entry.focus_set()

        self._check_vars = {
            "cadastro": tk.BooleanVar(value=True),
            "simples": tk.BooleanVar(value=True),
            "cnd": tk.BooleanVar(value=False),
            "fgts": tk.BooleanVar(value=False),
            "cndt": tk.BooleanVar(value=False),
        }

        self.options_frame = tk.Frame(self._main, bg="#0f1115")
        self.options_frame.pack(pady=15)

        self.checkbuttons = {}
        self.option_labels = {}

        for key in self._keys:
            row = tk.Frame(self.options_frame, bg="#0f1115")
            row.pack(anchor="w")

            chk = tk.Checkbutton(
                row,
                variable=self._check_vars[key],
                bg="#0f1115",
                fg="white",
                selectcolor="#0f1115",
                activebackground="#0f1115",
                state=("disabled" if key in "cadastro" else "normal"),
                # ("cadastro", "simples")
            )
            chk.pack(side="left")

            label = tk.Label(
                row,
                text=self._labels[key],
                fg=("#808080" if key in "cadastro" else "white"),
                # ("cadastro", "simples")
                bg="#0f1115",
                anchor="w",
                font=("Segoe UI", 10),
            )
            label.pack(side="left")

            self.checkbuttons[key] = chk
            self.option_labels[key] = label

        self._select_all_var = tk.BooleanVar()

        row = tk.Frame(self.options_frame, bg="#0f1115")
        row.pack(anchor="w")

        tk.Checkbutton(
            row,
            variable=self._select_all_var,
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
            anchor="w",
            font=("Segoe UI", 10),
        ).pack(side="left")

        self.btn = ttk.Button(
            self._main,
            text="Gerar Certidões",
            command=self.start_process,
            style="Blue.TButton",
        )
        self.btn.pack(pady=15)

    def _build_loading(self):
        self.loading = tk.Frame(self._root, bg="#0f1115")

        tk.Label(
            self.loading,
            text="Gerando certidões...",
            fg="white",
            bg="#0f1115",
            font=("Segoe UI", 12),
        ).pack(pady=60)

    def show_main(self):
        self.loading.pack_forget()
        self._main.pack(fill="both", expand=True)

    def show_loading(self):
        self._main.pack_forget()
        self.loading.pack(fill="both", expand=True)

    def start_process(self, event=None):
        cnpj = "".join(filter(str.isdigit, self._cnpj_var.get()))

        selected_keys = [key for key, var in self._check_vars.items() if var.get()]

        self.show_loading()

        Thread(target=self.run_bot, args=(cnpj, selected_keys)).start()

    def validate_cnpj(self, cnpj):
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False

        def calculate_digit(slice_data, weights):
            total = sum(int(num) * weight for num, weight in zip(slice_data, weights))
            remainder = total % 11
            return "0" if remainder < 2 else str(11 - remainder)

        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        digit1 = calculate_digit(cnpj[:12], weights1)
        digit2 = calculate_digit(cnpj[:13], weights2)

        return cnpj[-2:] == (digit1 + digit2)

    def run_bot(self, cnpj, selected_keys):
        if not self.validate_cnpj(cnpj):
            result = {}
            for key in selected_keys:
                result[key] = ("CNPJ inválido!", "#FC1B1B")
        else:
            result_queue = self._worker.submit(cnpj, selected_keys)
            success, response = result_queue.get()
            if success:
                result = response
            else:
                result = {}
                for key in self._keys:
                    if key in result:
                        result[key] = ("Erro na thread", "#FC1B1B")
        self._root.after(0, lambda: self.finish(result))

    def finish(self, result):
        for key in self._keys:
            if key not in result:
                text = "Não selecionado"
                color = "#FFFFFF"

            elif result[key] is None:
                text = "Erro de atribuição"
                color = "#FC1B1B"

            else:
                text, color = result[key]

            self.option_labels[key].config(
                text=f"{self._labels[key]}: {text}", fg=color
            )

            self.checkbuttons[key].config(state="disabled")

        self._entry.config(state="disabled")
        self.btn.config(text="Consultar Novamente")
        self.btn.config(command=self.reset_screen)
        self._root.unbind("<Return>")
        self._root.bind("<Return>", self.reset_screen)

        self.show_main()

    def reset_screen(self, Event=None):
        self._entry.config(state="normal")
        self._entry.focus_set()

        for key in self._keys:
            self.checkbuttons[key].config(
                state=("disabled" if key in "cadastro" else "normal"),
                # ("cadastro", "simples")
            )

            self.option_labels[key].config(
                text=self._labels[key],
                fg=("#808080" if key in "cadastro" else "white"),
                # ("cadastro", "simples")
            )
        self.btn.config(text="Gerar Certidões", command=self.start_process)
        self._root.unbind("<Return>")
        self._root.bind("<Return>", self.start_process)

    def close(self):
        self._root.destroy()
        self._worker.stop()
