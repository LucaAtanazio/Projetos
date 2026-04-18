import sqlite3
import redis
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import os
import sys

# Ajuste Dinâmico de Caminho [Ref: 01_hardware_setup.md]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_DB = os.path.join(BASE_DIR, 'conta.db')

FONTE_PADRAO = ("OpenSymbol", 11)
FONTE_TITULO = ("OpenSymbol", 28, "bold")

def conectar():
    try:
        conn = sqlite3.connect(CAMINHO_DB)
        return conn
    except sqlite3.OperationalError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        sys.exit(1)

def configurar_db():
    """Cria as tabelas caso o banco de dados seja novo [Ref: 03_estrutura_projetos.md]."""
    conn = conectar()
    cursor = conn.cursor()
    # Tabela de Entradas (Recebidos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recebidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            obs TEXT,
            valor REAL NOT NULL
        )
    """)
    # Tabela de Saídas (Enviados)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            obs TEXT,
            valor REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    
# Conexão Redis com Fallback
try:
    r_cache = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=1)
    r_cache.ping()
except Exception:
    r_cache = None # No Windows/Lenovo, operamos sem cache se o serviço estiver off

def processar_dados(tabela):
    """Busca dados no SQLite e tenta cachear no Redis se disponível."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"SELECT categoria, SUM(valor) FROM {tabela} GROUP BY categoria")
    dados = cursor.fetchall()
    conn.close()
    
    if r_cache:
        try:
            r_cache.delete(tabela)
            for cat, val in dados:
                r_cache.hset(tabela, cat, val)
        except:
            pass
    return dados

def exibir_grafico(tipo_db):
    # No Lenovo, se o Redis falhar, processamos direto do SQLite [cite: 5, 7]
    dados = processar_dados(tipo_db)
    
    if not dados:
        messagebox.showinfo("Aviso", "Não há dados suficientes.")
        return
    
    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]
    
    plt.figure(figsize=(8, 6))
    plt.pie(valores, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Distribuição de {'Ganhos' if tipo_db == 'recebidos' else 'Gastos'}")
    plt.show()

def editar_item():
    """Versão corrigida e completa da função."""
    item_r = tree_recebidos.selection()
    item_e = tree_enviados.selection()
    tree, t_name = (tree_recebidos, "recebidos") if item_r else (tree_enviados, "enviados")
    
    if tree and tree.selection():
        v = tree.item(tree.selection())['values']
        # v[0] é o ID, v[1] Categoria, v[2] Obs, v[3] Valor
        n_cat = simpledialog.askstring("Editar", "Categoria:", initialvalue=v[1])
        n_obs = simpledialog.askstring("Editar", "Observação:", initialvalue=v[2])
        n_val = simpledialog.askfloat("Editar", "Valor:", initialvalue=float(v[3]))

        if n_cat and n_obs and n_val is not None:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {t_name} SET categoria=?, obs=?, valor=? WHERE id=?", 
                          (n_cat, n_obs, n_val, v[0]))
            conn.commit()
            conn.close()
            atualizar_telas()
    else:
        messagebox.showwarning("Aviso", "Selecione um item para editar.")



def atualizar_telas():
    """Limpa e recarrega os dados do banco nas tabelas."""
    for tree in [tree_recebidos, tree_enviados]:
        for item in tree.get_children():
            tree.delete(item)
    
    conn = conectar()
    cursor = conn.cursor()
    
    # Carrega Recebidos (Verde/Entradas) [cite: 3]
    cursor.execute("SELECT id, categoria, obs, valor FROM recebidos")
    for row in cursor.fetchall():
        tree_recebidos.insert("", tk.END, values=row)
        
    # Carrega Enviados (Vermelho/Saídas) [cite: 3]
    cursor.execute("SELECT id, categoria, obs, valor FROM enviados")
    for row in cursor.fetchall():
        tree_enviados.insert("", tk.END, values=row)
    
    conn.close()

def nova_transacao(tabela):
    """Abre diálogos para inserir novos dados no SQLite[cite: 3]."""
    categoria = simpledialog.askstring("Novo Registro", "Digite a Categoria:")
    if not categoria: return
    
    obs = simpledialog.askstring("Novo Registro", "Observação:")
    valor = simpledialog.askfloat("Novo Registro", "Valor (R$):")
    
    if categoria and valor is not None:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {tabela} (categoria, obs, valor) VALUES (?, ?, ?)", 
                      (categoria, obs, valor))
        conn.commit()
        conn.close()
        atualizar_telas()

# --- INICIALIZAÇÃO CRÍTICA ---
configurar_db()  # Garante que as tabelas existam antes de atualizar_telas()

root = tk.Tk()
root.title("Sistema Conta Corrente V3.0 - Lenovo")
root.geometry("900x600")

# --- Configuração da Janela Principal ---
root = tk.Tk()
root.title("Sistema Conta Corrente V3.0 - Unidade Portátil")
root.geometry("900x600") # Define um tamanho inicial para não virar mini janela

# Cabeçalho
label_titulo = tk.Label(root, text="CONTROLE DE CAIXA", font=FONTE_TITULO)
label_titulo.pack(pady=10)

# Frame para as Tabelas
frame_tabelas = tk.Frame(root)
frame_tabelas.pack(expand=True, fill="both", padx=10)

# Configuração das Colunas das Tabelas
colunas = ("ID", "Categoria", "Observação", "Valor")

# Tabela de Ganhos
tk.Label(frame_tabelas, text="GANHOS (Entradas)", fg="green", font=("Arial", 12, "bold")).grid(row=0, column=0)
tree_recebidos = ttk.Treeview(frame_tabelas, columns=colunas, show="headings", height=8)
for col in colunas:
    tree_recebidos.heading(col, text=col)
    tree_recebidos.column(col, width=100)
tree_recebidos.grid(row=1, column=0, padx=5, sticky="nsew")

# Tabela de Gastos
tk.Label(frame_tabelas, text="GASTOS (Saídas)", fg="red", font=("Arial", 12, "bold")).grid(row=0, column=1)
tree_enviados = ttk.Treeview(frame_tabelas, columns=colunas, show="headings", height=8)
for col in colunas:
    tree_enviados.heading(col, text=col)
    tree_enviados.column(col, width=100)
tree_enviados.grid(row=1, column=1, padx=5, sticky="nsew")

# --- Frame de Botões (Atualizado com Adicionar) ---
frame_botoes = tk.Frame(root)
frame_botoes.pack(pady=20)

# Botões de Transação (Novos)
btn_add_ganho = tk.Button(frame_botoes, text="+ Novo Ganho", bg="#28a745", fg="white", 
                          font=("Arial", 10, "bold"), width=15, 
                          command=lambda: nova_transacao("recebidos"))
btn_add_ganho.grid(row=0, column=0, padx=5)

btn_add_gasto = tk.Button(frame_botoes, text="- Novo Gasto", bg="#dc3545", fg="white", 
                          font=("Arial", 10, "bold"), width=15, 
                          command=lambda: nova_transacao("enviados"))
btn_add_gasto.grid(row=0, column=1, padx=5)

# Botões de Gráficos e Edição (Existentes)
btn_graf_gastos = tk.Button(frame_botoes, text="Gráfico Gastos", bg="#ffcccc", 
                            command=lambda: exibir_grafico('enviados'))
btn_graf_gastos.grid(row=0, column=2, padx=5)

btn_graf_ganhos = tk.Button(frame_botoes, text="Gráfico Ganhos", bg="#ccffcc", 
                            command=lambda: exibir_grafico('recebidos'))
btn_graf_ganhos.grid(row=0, column=3, padx=5)

btn_editar = tk.Button(frame_botoes, text="Editar Selecionado", 
                       command=editar_item, width=18)
btn_editar.grid(row=0, column=4, padx=5)

# Inicializa os dados nas tabelas
atualizar_telas()

root.mainloop()