import streamlit as st

from dados.fonte import get_boxscores, get_games

boxscores = get_boxscores()

dados_bs = st.container()

with dados_bs:
    st.dataframe(boxscores)