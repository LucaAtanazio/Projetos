print("Iniciando o programa...")

import sqlite3
import redis
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog

CAMINHO_DB = '/home/lucaatanazio/Documentos/Projetos/Conta corrente/conta.db'
FONTE_PADRAO = ("OpenSymbol", 11)
FONTE_TITULO = ("OpenSymbol", 28, "bold")

def conectar():
    return sqlite3.connect(CAMINHO_DB)

# Conexão Redis
try:
    r_cache = redis.Redis(host='localhost', port=6379, decode_responses=True)
    # Teste de conexão
    r_cache.ping()
except:
    r_cache = None

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS recebidos
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, obs TEXT, valor REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS enviados
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, obs TEXT, valor REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias_custom
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, tipo TEXT)''')
    conn.commit()
    conn.close()

# LÓGICA DE GRÁFICOS (REDIS + MATPLOTLIB) 

def processar_para_redis(tabela):
    if not r_cache:
        return None
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"SELECT categoria, SUM(valor) FROM {tabela} GROUP BY categoria")
    dados = cursor.fetchall()
    conn.close()
    
    # Atualiza o cache no Redis
    r_cache.delete(tabela)
    for cat, val in dados:
        r_cache.hset(tabela, cat, val)
    return dados

def exibir_grafico(tipo_db):
    """Gera gráfico de pizza usando os dados cacheados no Redis."""
    if not r_cache:
        messagebox.showerror("Erro Redis", "Servidor Redis não encontrado! Inicie com 'sudo systemctl start redis-server'")
        return

    dados = processar_para_redis(tipo_db)
    if not dados:
        messagebox.showinfo("Aviso", "Não há dados suficientes para gerar o gráfico.")
        return
    
    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]
    
    plt.figure(figsize=(8, 6))
    plt.pie(valores, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Distribuição de {'Ganhos' if tipo_db == 'recebidos' else 'Gastos'}")
    plt.show()

# AÇÕES DA INTERFACE

def obter_categorias(tipo):
    if tipo == '+':
        categorias = ["Caixa", "Bônus", "Uber", "Vendas"]
    else:
        categorias = ["Investimento", "Contas", "Tecnologia", "Lanche", "Uber", "Caixa"]
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM categorias_custom WHERE tipo = ?", (tipo,))
    extras = [linha[0] for linha in cursor.fetchall()]
    conn.close()
    return categorias + extras + ["+ Criar nova categoria"]

def calcular_saldo():
    conn = conectar()
    cursor = conn.cursor()
    r = cursor.execute("SELECT SUM(valor) FROM recebidos").fetchone()[0] or 0.0
    e = cursor.execute("SELECT SUM(valor) FROM enviados").fetchone()[0] or 0.0
    conn.close()
    return r - e

def realizar_pix():
    tipo = simpledialog.askstring("Operação Pix", "Digite '+' para Recebido ou '-' para Enviado:")
    if tipo not in ['+', '-']:
        return

    janela_cat = tk.Toplevel(janela)
    janela_cat.title("Selecionar Categoria")
    janela_cat.geometry("350x250")
    janela_cat.grab_set()

    tk.Label(janela_cat, text="Escolha a Categoria:", font=FONTE_PADRAO).pack(pady=10)

    categorias = obter_categorias(tipo)
    var_escolha = tk.StringVar(janela_cat)
    var_escolha.set(categorias[0])

    menu = tk.OptionMenu(janela_cat, var_escolha, *categorias)
    menu.config(font=FONTE_PADRAO)
    menu.pack(pady=10, padx=20, fill="x")

    def confirmar_e_prosseguir():
        escolha = var_escolha.get()
        janela_cat.destroy()
        
        if escolha == "+ Criar nova categoria":
            categoria_final = simpledialog.askstring("Nova Categoria", "Nome da nova categoria:")
            if categoria_final:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categorias_custom (nome, tipo) VALUES (?, ?)", (categoria_final, tipo))
                conn.commit()
                conn.close()
            else: return
        else:
            categoria_final = escolha

        obs = simpledialog.askstring("Observação", "Descrição do Pix:")
        valor = simpledialog.askfloat("Valor", "Valor do Pix:")
        
        if valor is not None:
            tabela_alvo = "recebidos" if tipo == '+' else "enviados"
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {tabela_alvo} (categoria, obs, valor) VALUES (?, ?, ?)", (categoria_final, obs, valor))
            conn.commit()
            conn.close()
            atualizar_telas()

    tk.Button(janela_cat, text="Confirmar", command=confirmar_e_prosseguir, bg="green", fg="white", font=FONTE_PADRAO).pack(pady=20)

def apagar_item():
    item_r = tree_recebidos.selection()
    item_e = tree_enviados.selection()
    target, t_name = (item_r, "recebidos") if item_r else (item_e, "enviados")
    
    if target:
        tree = tree_recebidos if item_r else tree_enviados
        id_reg = tree.item(target)['values'][0]
        if messagebox.askyesno("Confirmar", "Apagar este registro?"):
            conn = conectar(); cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {t_name} WHERE id = ?", (id_reg,))
            conn.commit(); conn.close()
            atualizar_telas()
    else:
        messagebox.showwarning("Aviso", "Selecione um item para apagar.")

def editar_item():
    item_r = tree_recebidos.selection()
    item_e = tree_enviados.selection()
    tree, t_name = (tree_recebidos, "recebidos") if item_r else (tree_enviados, "enviados")
    
    if tree and tree.selection():
        v = tree.item(tree.selection())['values']
        n_cat = simpledialog.askstring("Editar", "Categoria:", initialvalue=v[1])
        n_obs = simpledialog.askstring("Editar", "Observação:", initialvalue=v[2])
        n_val = simpledialog.askfloat("Editar", "Valor:", initialvalue=float(v[3]))

        if n_cat and n_obs and n_val is not None:
            conn = conectar(); cursor = conn.cursor