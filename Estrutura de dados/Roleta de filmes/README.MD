# Movie Roulette - Watchlist Randomizer

Um sistema simples e eficiente para resolver o "paralisia de escolha" na hora de decidir qual filme assistir. O projeto lê uma watchlist exportada do Letterboxd e realiza um sorteio aleatório com efeito visual de roleta.

## Estrutura do Projeto

* `watchlist_(DATA-EXPORTACAO).csv`: Base de dados contendo a lista de filmes.
* `roleta_film.py`: Script Python principal para execução via terminal.
* `roleta.bat`: Atalho para execução rápida no Windows (Desktop/Notebook).
* `roleta_test.ipynb`: Ambiente de testes e prototipação em Jupyter Notebook.

## Como Usar

### Execução Rápida 
Basta dar dois cliques no arquivo **`roleta.bat`**. 
Ele chamará o interpretador Python e iniciará a animação do sorteio automaticamente no terminal.

### Ambiente de Desenvolvimento
Para testar novas funcionalidades ou visualizar o sorteio com interface HTML:
1. Abra o `roleta_test.ipynb` no VS Code ou Jupyter Lab.
2. Certifique-se de que o `ipykernel` e `pandas` estão instalados.
3. Execute as células para ver o sorteio estilizado.

## Requisitos
* Python 3.x
* Pandas (`pip install pandas`)

