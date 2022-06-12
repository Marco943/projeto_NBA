import streamlit as st, pandas as pd

@st.experimental_memo
def get_games():
    df = pd.read_parquet('dados/Jogos.parquet')
    df['SEASON_TYPE'] = df['SEASON_ID'].astype(str).str[0].astype(int)
    df['SEASON'] = df['SEASON_ID'].astype(str).str[1:].astype(int)
    df['MATCHUP'] = df['GAME_DATE'].dt.strftime('%d/%m/%Y') + ' - ' + df['MATCHUP'] + " (" + df['WL'] + ")"
    df['GAME_ID'] = df['GAME_ID'].astype(int)
    return df

@st.experimental_memo
def get_boxscores():
    df = pd.read_parquet('dados/BoxScores.parquet').drop(columns = ['FG_PCT', 'FG3_PCT', 'FT_PCT'])
    df['GAME_ID'] = df['GAME_ID'].astype(int)
    return df