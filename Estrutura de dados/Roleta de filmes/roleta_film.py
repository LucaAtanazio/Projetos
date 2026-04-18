import pandas as pd
import random
import time
import os
import webbrowser


MAGENTA = '\033[95m'
VERDE = '\033[32m'
RESET = '\033[0m'
NEGRITO = '\033[1m'

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def executar_sorteio():
    try:
        df = pd.read_csv('watchlist_18-04-2026.csv')
        filmes_dados = df[['Name', 'Year', 'Letterboxd URI']].dropna().values.tolist()
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        input("Pressione Enter para sair...")
        return None

    if not filmes_dados:
        print("Watchlist vazia.")
        input()
        return None

   
    iteracoes = 40
    for i in range(iteracoes):
        limpar_tela()
        filme_temp, ano_temp, _ = random.choice(filmes_dados)
        
        print(f"\n{MAGENTA}" + "="*40)
        print(f"       SORTEANDO FILME...")
        print("="*40 + f"{RESET}")
        print(f"\n   >>> {NEGRITO}{filme_temp}{RESET} ({int(ano_temp)}) <<<")
        print(f"\n{MAGENTA}" + "="*40 + f"{RESET}")
        
        wait = 0.05 + (i / iteracoes)**2 * 0.3
        time.sleep(wait)


    limpar_tela()
    filme_sorteado, ano_sorteado, link_sorteado = random.choice(filmes_dados)
    
    print(f"\n{MAGENTA}" + "★"*40)
    print("         FILME SORTEADO!")
    print(" " + "★"*40 + f"{RESET}")
    print(f"\n   {NEGRITO}{filme_sorteado.upper()}{RESET}  -  {MAGENTA}{int(ano_sorteado)}{RESET}")
    print(f"\n   Link: {VERDE} {link_sorteado}")
    print(f"\n{MAGENTA}" + "★"*40 + f"{RESET}")
    
    return link_sorteado


while True:
    link_atual = executar_sorteio()
    if link_atual is None: break
        
    print(f"\n[{MAGENTA}R{RESET}] Tentar novamente | [{VERDE}L{RESET}] Abrir no Letterboxd | [Enter] Sair")
    escolha = input("> ").strip().lower()
    
    if escolha == 'r': continue
    elif escolha == 'l':
        webbrowser.open(link_atual)
        print(f"\n[{MAGENTA}R{RESET}] Sortear outro | [Enter] Sair")
        if input("> ").strip().lower() != 'r': break
    else:
        print("\nBoa sessão, Luca!")
        break