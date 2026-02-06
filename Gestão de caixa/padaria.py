import sqlite3

# --- 1. CONFIGURAÇÃO DA BASE DE DADOS ---
# Caminho absoluto para garantir que ele encontre o ficheiro
CAMINHO_DB = '/home/lucaatanazio/Documentos/Projetos/Gestão de caixa/padaria.db'

def inicializar_sistema():
    """Cria a tabela no banco de dados se ela não existir."""
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    conexao.commit()
    conexao.close()
    print("Base de dados pronta para uso!")

# --- 2. LÓGICA DE BACK-END ---
def adicionar_produto(nome, qtd):
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO produtos (nome, quantidade) VALUES (?, ?)", (nome, qtd))
    conexao.commit()
    conexao.close()
    print(f"Sucesso: {nome} adicionado ao inventário.")

def deletar_produto(nome):
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos WHERE nome = ?", (nome,))
    conexao.commit()
    conexao.close()
    print(f"Sucesso: {nome} foi deletado do inventário.")

def atualizar_stock(nome, nova_qtd):
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute("UPDATE produtos SET quantidade = ? WHERE nome = ?", (nova_qtd, nome))
    conexao.commit()
    if cursor.rowcount > 0:
        print(f"Stock atualizado: {nome} agora tem {nova_qtd} unidades.")
    else:
        print(f"Aviso: Produto '{nome}' não encontrado.")
    conexao.close()

def listar_produtos():
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM produtos")
    itens = cursor.fetchall()
    print("\n--- STOCK ATUAL DA PADARIA ---")
    for item in itens:
        print(f"ID: {item[0]} | Produto: {item[1]} | Quantidade: {item[2]}")
    print("-------------------------------\n")
    conexao.close()

def limpar_tabela():
    conexao = sqlite3.connect(CAMINHO_DB)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos")
    conexao.commit()
    conexao.close()
    print("Tabela limpa!")

# --- 3. MENU INTERATIVO ---
if __name__ == "__main__":
    inicializar_sistema()
    while True:
        print("\n=== Sistema de Gestão - PADARIA GOSTOSIN ===")
        print("1. Adicionar Novo produto")
        print("2. Atualizar Quantidade")
        print("3. Listar Inventário")
        print("4. Remover Produto")
        print("5. Limpar Tudo")
        print("0. Sair")

        opcao = input("\nEscolha uma opção: ")

        try:
            if opcao == "1":
                nome = input("Nome: ")
                qtd = int(input("Quantidade: "))
                adicionar_produto(nome, qtd)
            elif opcao == "2":
                nome = input("Nome: ")
                nova_qtd = int(input("Nova quantidade: "))
                atualizar_stock(nome, nova_qtd)
            elif opcao == "3":
                listar_produtos()
            elif opcao == "4":
                nome = input("Nome: ")
                deletar_produto(nome)
            elif opcao == "5":
                limpar_tabela()
            elif opcao == "0":
                print("A encerrar...")
                break
            else:
                print("Opção inválida!")
        except ValueError:
            print("Erro: Digite apenas números inteiros para as quantidades!")