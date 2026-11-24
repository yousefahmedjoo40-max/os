#!/usr/bin/env python3
"""
يساعدك — النسخة الرسومية (واجهة محادثة بسيطة)
"""
import threading
import tkinter as tk
from tkinter import scrolledtext

import yesaedak


class Chat(tk.Tk):
    BG, CARD, FG, ACCENT = "#101418", "#1a2129", "#e8eef4", "#38bdf8"

    def __init__(self):
        super().__init__()
        self.title("يساعدك — مساعد BaridOS الذكي")
        self.configure(bg=self.BG)
        self.geometry("520x600")
        self.history = []
        self._build()

    def _build(self):
        tk.Label(self, text="❄ يساعدك", bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 16, "bold")).pack(pady=(10, 2))
        tk.Label(self, text="مدعوم بـ Gemini 3.5 Flash-Lite", bg=self.BG, fg="#8aa0b4",
                 font=("Segoe UI", 9)).pack()

        self.chat = scrolledtext.ScrolledText(self, bg=self.CARD, fg=self.FG, insertbackground=self.FG,
                                              font=("Segoe UI", 11), relief="flat", wrap="word")
        self.chat.pack(fill="both", expand=True, padx=12, pady=8)
        self.chat.config(state="disabled")
        self._add("يساعدك: أهلاً! أنا يساعدك، مساعد نظام BaridOS. اسألني أي حاجة 🌬\n")

        row = tk.Frame(self, bg=self.BG)
        row.pack(fill="x", padx=12, pady=(0, 10))
        self.entry = tk.Entry(row, bg=self.CARD, fg=self.FG, insertbackground=self.FG,
                              font=("Segoe UI", 11), relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.entry.bind("<Return>", lambda e: self._send())
        tk.Button(row, text="إرسال", command=self._send, bg=self.ACCENT, fg="#06202e",
                  relief="flat", font=("Segoe UI", 10, "bold"), padx=14).pack(side="left", padx=(8, 0))

    def _add(self, text):
        self.chat.config(state="normal")
        self.chat.insert("end", text + "\n")
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _send(self):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, "end")
        self._add("أنت: " + msg)
        self._add("يساعدك: ...")
        threading.Thread(target=self._reply, args=(msg,), daemon=True).start()

    def _reply(self, msg):
        reply = yesaedak.ask(msg, history=self.history)
        # remove typing line
        self.chat.config(state="normal")
        self.chat.delete("end-2l linestart", "end-1c")
        self.chat.config(state="disabled")
        self._add("يساعدك: " + reply)
        self.history += [
            {"role": "user", "parts": [{"text": msg}]},
            {"role": "model", "parts": [{"text": reply}]},
        ]
        self.history = self.history[-20:]  # keep context small & fast


if __name__ == "__main__":
    Chat().mainloop()
