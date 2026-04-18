import pandas as pd
import random
import time
import os

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

try:
    df = pd.read_csv('watchlist_18-04-2026.csv')
    filmes = df['Name'].dropna().tolist()
except Exception as e:
    print(f"Erro ao ler arquivo: {e}")
    input("Pressione Enter para sair...")
    exit()

if not filmes:
    print("Watchlist vazia.")
    input()
    exit()


iteracoes = 40
for i in range(iteracoes):
    limpar_tela()
    filme_temp = random.choice(filmes)
    
    print("\n" + "="*40)
    print(f"       SORTEANDO FILME...")
    print("="*40)
    print(f"\n   >>> {filme_temp} <<<")
    print("\n" + "="*40)
    

    wait = 0.05 + (i / iteracoes)**2 * 0.3
    time.sleep(wait)

limpar_tela()
filme_sorteado = random.choice(filmes)
print("\n" + "★"*40)
print("         FILME SORTEADO!")
print(" " + "★"*40)
print(f"\n   {filme_sorteado.upper()}")
print("\n" + "★"*40)
print("\nBom filme")
input("\nPressione Enter para fechar...")