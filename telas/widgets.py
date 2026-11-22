"""
Widget reutilizável para telas de cadastro (Clientes, Fornecedores, Produtos).
Fornece: lista com busca, form lateral, botões salvar/cancelar/excluir.
"""
import customtkinter as ctk
from tkinter import ttk, messagebox


def estilo_tree():
    s = ttk.Style()
    s.theme_use("default")
    s.configure("SAC.Treeview",         rowheight=28, font=("Segoe UI", 10))
    s.configure("SAC.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e8edf2")
    s.map("SAC.Treeview", background=[("selected", "#1a73e8")],
          foreground=[("selected", "white")])


def label(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text, **kw)


def entry(parent, width=220, **kw):
    return ctk.CTkEntry(parent, height=32, width=width, **kw)
