# Movie Roulette - Watchlist Randomizer

Um sistema simples e eficiente para resolver o "paralisia de escolha" na hora de decidir qual filme assistir. O projeto lê uma watchlist exportada do Letterboxd e realiza um sorteio aleatório com efeito visual de roleta.

## 🚀 Tecnologias e Ambiente
* **Linguagem:** Python 3.12.3
* **Interface Web:** Streamlit
* **Processamento de Dados:** Pandas
* **Ambiente:** Pop!_OS (Desktop com RTX 3050) / Windows 11 (Notebook)

## Estrutura do Projeto

* `watchlist_(DATA-EXPORTACAO).csv`: Base de dados contendo a lista de filmes.
* `app.py`: Dashboard principal em Streamlit.
* `roleta_film.py`: Script Python principal para execução via terminal.
* `sound/`: Pasta contendo os assets de áudio
* `roleta_test.ipynb`: Ambiente de testes e prototipação em Jupyter Notebook.

## Como Usar
0. *Exporte seus dados da Wacthlist em https://letterboxd.com/settings/data/ > Export Your Data*

1. Instale as bibliotecas representes em `requirements.txt`
   >> pip install -r requirements.txt
2. Edite os endereços de arquivos ou .venv para o código rodar na sua marca
3. Execute o streamlit no terminal
   >> streamlit run app.py

