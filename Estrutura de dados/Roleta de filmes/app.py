import streamlit as st
import pandas as pd
import random
import time
import os
import base64


st.set_page_config(page_title="Movie Roulette - Watchlist Randomizer", page_icon="🍿")

def play_audio(file_path):
    full_path = os.path.expanduser(file_path)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            unique_id = random.randint(0, 9999)
            md = f"""
                <audio autoplay key="{unique_id}">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)


st.markdown("""
    <style>
    .stButton>button {
        background-color: #ff00ff;
        color: white;
        border-radius: 10px;
        border: 2px solid #cc00cc;
        width: 100%;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #ff00ff !important;
        text-align: center;
    }
    .movie-card {
        text-align: center;
        padding: 20px;
        border: 3px solid #ff00ff;
        border-radius: 15px;
        background: rgba(255, 0, 255, 0.05);
        box-shadow: 0 4px 15px rgba(255, 0, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Movie Roulette")

@st.cache_data
def load_data():
    df = pd.read_csv('watchlist_18-04-2026.csv')
    return df[['Name', 'Year', 'Letterboxd URI']].dropna()

try:
    df = load_data()
    filmes_lista = df.values.tolist()

    if st.button("GIRAR ROLETA 🎲"):
        placeholder = st.empty()
        
        play_audio("sound/Riser.mp3")
        
        iteracoes = 35
        duracao_total = 5.0
        
        for i in range(iteracoes):
            nome_temp, ano_temp, _ = random.choice(filmes_lista)
            with placeholder.container():
                st.markdown(f"""
                <div style='text-align: center;'>
                    <p style='color: #888;'>Sorteando...</p>
                    <h2 style='color: #ff00ff; font-size: 2.5em;'>{nome_temp}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            delay = (duracao_total / iteracoes) * (i / iteracoes * 2)
            time.sleep(max(0.05, delay))

        nome_f, ano_f, link_f = random.choice(filmes_lista)
        placeholder.empty()

        play_audio("sound/re4.mp3") 

        st.markdown(f"""
            <div class="movie-card">
                <h1 style='margin-bottom: 0;'>{nome_f.upper()}</h1>
                <h3 style='margin-top: 0; color: #ff00ff;'>{int(ano_f)}</h3>
                <hr style='border-color: #ff00ff;'>
                <a href="{link_f}" target="_blank" style="color: black; text-decoration: none; background: #13f502; padding: 10px 20px; border-radius: 5px; font-weight: bold;">VER NO LETTERBOXD</a>
            </div>
        """, unsafe_allow_html=True)
        
        st.balloons()

except Exception as e:
    st.error(f"Erro: {e}")