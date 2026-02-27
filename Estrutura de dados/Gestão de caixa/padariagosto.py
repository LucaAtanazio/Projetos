import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- 1. BACK-END (Conexão e Lógica) ---
CAMINHO_DB = '/home/lucaatanazio/Documentos/Projetos/Gestão de caixa/padaria.db'

def conectar():
    return sqlite3.connect(CAMINHO_DB)

def adicionar_ui():
    nome = entry_nome.get()
    qtd = entry_qtd.get()
    try:
        if nome and qtd:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO produtos (nome, quantidade) VALUES (?, ?)", (nome, int(qtd)))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"{nome} adicionado!")
            atualizar_tabela() # Atualiza a visão na hora!
            entry_nome.delete(0, tk.END)
            entry_qtd.delete(0, tk.END)
        else:
            messagebox.showwarning("Aviso", "Preencha tudo!")
    except ValueError:
        messagebox.showerror("Erro", "Quantidade deve ser um número!")

def remover_ui():
    # Pega o item selecionado na tabela
    selecionado = tabela.selection()
    if selecionado:
        # Pega o ID do produto (primeira coluna)
        item = tabela.item(selecionado)
        id_produto = item['values'][0]
        nome_produto = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"Desejas remover o produto {nome_produto}?"):
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
            conn.commit()
            conn.close()
            atualizar_tabela()
    else:
        messagebox.showwarning("Aviso", "Seleciona um produto na tabela para remover!")

def atualizar_tabela():
    # Limpa a tabela visual
    for i in tabela.get_children():
        tabela.delete(i)
    # Puxa os dados novos
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    for linha in cursor.fetchall():
        tabela.insert("", tk.END, values=linha)
    conn.close()

from tkinter import simpledialog # Adicione esta linha no topo com os outros imports

def vender_ui():
    selecionado = tabela.selection()
    if selecionado:
        item = tabela.item(selecionado)
        id_produto = item['values'][0]
        nome_produto = item['values'][1]
        qtd_atual = int(item['values'][2])

        qtd_venda = simpledialog.askinteger("Registrar Venda", f"Produto: {nome_produto}\nQuantidade vendida:", minvalue=1)

        if qtd_venda is not None:
            if qtd_atual >= qtd_venda:
                nova_qtd = qtd_atual - qtd_venda
                
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, id_produto))
                conn.commit()
                conn.close()
                
                atualizar_tabela()
                messagebox.showinfo("Sucesso", f"Venda de {qtd_venda} {nome_produto}(s) registrada!")
            else:
                messagebox.showwarning("Stock Insuficiente", f"Você tentou vender {qtd_venda}, mas só existem {qtd_atual} em stock!")
    else:
        messagebox.showwarning("Aviso", "Selecione um produto na tabela primeiro!")

# --- 2. FRONT-END (Janela) ---
janela = tk.Tk()
janela.title("Padaria Gostosin - Gestão Visual")
janela.geometry("600x450")

# Formulário
frame_input = tk.LabelFrame(janela, text=" Cadastro de Produtos ", padx=10, pady=10)
frame_input.pack(padx=10, pady=10, fill="x")

tk.Label(frame_input, text="Produto:").grid(row=0, column=0)
entry_nome = tk.Entry(frame_input)
entry_nome.grid(row=0, column=1, padx=5)

tk.Label(frame_input, text="Qtd:").grid(row=0, column=2)
entry_qtd = tk.Entry(frame_input, width=10)
entry_qtd.grid(row=0, column=3, padx=5)

btn_add = tk.Button(frame_input, text="Adicionar",command=adicionar_ui, bg="#4CAF50", fg="white")
btn_add.grid(row=0, column=4, padx=10)

# --- Tabela de Dados ---
tk.Label(janela, text="Inventário Atual", font=("Arial", 12, "bold")).pack(pady=5)
tabela = ttk.Treeview(janela, columns=("ID", "Nome", "Quantidade"), show="headings")
tabela.heading("ID", text="ID")
tabela.heading("Nome", text="Nome do Produto")
tabela.heading("Quantidade", text="Quantidade")
tabela.column("ID", width=50)
tabela.pack(padx=10, pady=10, fill="both", expand=True)

# --- Botões de Ação Inferiores ---
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

btn_remove = tk.Button(frame_botoes, text="Remover Selecionado", command=remover_ui, bg="#f44336", fg="white")
btn_remove.pack(side="left", padx=10)

btn_refresh = tk.Button(frame_botoes, text="Atualizar Lista", command=atualizar_tabela)
btn_refresh.pack(side="left", padx=10)

btn_venda = tk.Button(frame_botoes, text="Registrar Venda (-1)", command=vender_ui, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
btn_venda.pack(side="left", padx=10)

# Iniciar a tabela com o que já tem no banco
try:
    atualizar_tabela()
except:
    pass

janela.mainloop()