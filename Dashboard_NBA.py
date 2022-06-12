import streamlit as st, pandas as pd, subprocess, sys, altair as alt, json
from st_aggrid import AgGrid, GridOptionsBuilder
from fonte import get_boxscores, get_games

st.set_page_config(page_title='Dashboard NBA', layout='wide')
pd.options.mode.chained_assignment = None

stats = json.load(open('dados/stats_rename.json'))
stats_fmt = json.load(open('dados/stats_rename.json'))
games = get_games()
boxscores = get_boxscores()

def get_table(df, selection=False):
    indexes = df.index.names
    cols = df.columns
    df = df.reset_index()

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(cellStyle = {'fontSize': '14px', 'fontFamily': 'Sans Serif'})
    for col in df.columns:
        gb.configure_column(col, header_name=stats.get(col))
    gb.configure_columns(indexes, pinned='left')
    gb.configure_columns(cols, type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2, maxWidth=100)
    gb.configure_columns(['FGPCT', 'FG3PCT', 'FTPCT', 'W%'], type=["numericColumn","numberColumnFilter","customNumericFormat"], valueFormatter='(value*100).toFixed(2)+"%"')
    if selection: gb.configure_selection(selection_mode='multiple', use_checkbox=True)
    return AgGrid(df, gridOptions=gb.build(), theme='streamlit', update_mode='MANUAL', data_return_mode='FILTERED')

cabecalho = st.container()
dados_jogos = st.container()
dados_scatter = st.container()
dados_bs = st.container()
dados_jogador = st.container()

with cabecalho:
    st.header('App NBA')

with st.sidebar:
    cols = st.columns([3,1])

    with cols[1]:
        if st.button('↺', help='Atualizar dados'):
            subprocess.run([f'{sys.executable}', 'atualizacao.py'])
            st.experimental_memo.clear()
    with cols[0]:
        st.write('Jogos até {}'.format(games['GAME_DATE'].max().strftime('%d/%m/%Y')))

    season_types = {1: 'Pre Season', 2: 'Regular Season', 3: 'All Star', 4: 'Playoffs'}
    
    # FILTRO DE TIPO DE TEMPORADA
    options_types = st.multiselect(
        label = 'Tipo',
        options = list(season_types.keys()), default = [2,4],
        format_func = lambda x: season_types.get(x)
    )

    seasons = {0: 'Todas'} | {SEASON: SEASON for SEASON in list(sorted(games['SEASON'].unique(), reverse = True))}
    
    # FILTRO DE TEMPORADAS
    options_seasons = st.selectbox(
        label = 'Season',
        options = list(seasons.keys()), index = 1,
        format_func = lambda x: seasons.get(x)
    )

    if not options_seasons == 0:
        f_games_s = games[(games['SEASON'] == options_seasons) & (games['SEASON_TYPE'].isin(options_types))]
    else:
        f_games_s = games[games['SEASON_TYPE'].isin(options_types)]
    f_boxscores_s = boxscores[boxscores['GAME_ID'].isin(f_games_s['GAME_ID'])]

    teams = {0: 'Todos'} | f_games_s.set_index('TEAM_ID')['TEAM_NAME'].drop_duplicates().sort_values().to_dict()

    # FILTRO DE TIMES
    options_teams = st.selectbox(
        label = 'Times',
        options = list(teams.keys()), index = 0,
        format_func= lambda x: teams.get(x))

    if not options_teams == 0:
        f_games_s_t = f_games_s[f_games_s['TEAM_ID'] == options_teams]
        f_boxscores_s_t = f_boxscores_s[f_boxscores_s['TEAM_ID'] == options_teams]
    else:
        f_games_s_t = f_games_s
        f_boxscores_s_t = f_boxscores_s
    
    matchups = f_games_s_t.set_index('GAME_ID')['MATCHUP'].to_dict()

    # FILTRO DE JOGOS
    options_games = st.multiselect(
        label = 'Jogos', options = list(matchups.keys()),
        format_func = lambda x: matchups.get(x))
    
    if len(options_games) == 0:
        f_boxscores_s_t_g = f_boxscores_s_t
    else:
        f_boxscores_s_t_g = f_boxscores_s_t[f_boxscores_s_t['GAME_ID'].isin(options_games)]

    # FILTRO DE STATS PER
    options_stats_per = st.radio(
        label='Agrupamento de stats',
        options=['Total', 'Per Game', 'Per 36', 'Per 48'], index=1
    )

    with st.expander('Links úteis'):
        st.write('https://streamlit-aggrid.readthedocs.io/en/docs/index.html')
        st.write('https://docs.streamlit.io/')
        st.write('https://github.com/swar/nba_api')
        st.write('https://altair-viz.github.io/user_guide/internals.html')

with dados_jogos:
    df = f_games_s
    df['W'] = df[df['WL']=='W']['WL']
    df['L'] = df[df['WL']=='L']['WL']
    df['G'] = df['WL']
    df = (df
    .groupby(['TEAM_ID', 'TEAM_NAME'])
    .agg({
        'W': 'count',
        'L':'count',
        'G': 'size',
        'PTS': 'mean',
        'AST': 'mean',
        'REB': 'mean',
        'FGM': 'mean',
        'FGA': 'mean',
        'FG3M': 'mean',
        'FG3A': 'mean',
        'FTM': 'mean',
        'FTA': 'mean',
        'STL':'mean',
        'BLK': 'mean',
        'OREB': 'mean',
        'DREB': 'mean',
        'PF': 'mean',
        'PLUS_MINUS': 'mean'
    })
    .reset_index(level='TEAM_ID', drop=True)
    )
    df['W%'] = df['W']/df['G']
    df['FGPCT'] = df['FGM']/df['FGA']
    df['FG3PCT'] = df['FG3M']/df['FG3A']
    df['FTPCT'] = df['FTM']/df['FTA']
    df = df[['W', 'L', 'G', 'W%', 'PTS', 'AST', 'REB', 'STL', 'BLK', 'PF', 'FGM', 'FGA', 'FGPCT', 'FG3M', 'FG3A', 'FG3PCT', 'FTM', 'FTA', 'FTPCT', 'OREB', 'DREB', 'PLUS_MINUS']]

    get_table(df)

    tabela = st.dataframe(df, )

with dados_bs:
    stats_per = 'sum' if options_stats_per == 'Total' else 'mean'

    df = (f_boxscores_s_t_g
        .drop(columns = ['TEAM_ID', 'GAME_ID'])
        .groupby(['PLAYER_ID', 'PLAYER_NAME'])
        .agg(stats_per)
        .reset_index(level='PLAYER_ID', drop = True)
    )

    if (options_stats_per == 'Per 36') or (options_stats_per == 'Per 48'):
        stat_min = 36 if options_stats_per == 'Per 36' else 48
        for column in df.columns:
            df[column] = df[column]/df['MIN'] * stat_min

    df['FGPCT'] = df['FGM']/df['FGA']
    df['FG3PCT'] = df['FG3M']/df['FG3A']
    df['FTPCT'] = df['FTM']/df['FTA']
    df_bs = df[['MIN', 'PTS', 'AST', 'REB', 'STL', 'BLK', 'PF', 'FGM', 'FGA', 'FGPCT', 'FG3M', 'FG3A', 'FG3PCT', 'FTM', 'FTA', 'FTPCT', 'OREB', 'DREB', 'PLUS_MINUS']]

    boxscore_response = get_table(df, selection=True)

    selected_players = pd.DataFrame(boxscore_response['selected_rows'])
    filtered_players = pd.DataFrame(boxscore_response['data'])

with dados_jogador:
    if not selected_players.empty:

        options_stat = st.selectbox(
            label = 'Stat', options = list(stats.keys())[3:],
            format_func = lambda x: stats.get(x)
        )

        df = f_boxscores_s_t[f_boxscores_s_t['PLAYER_NAME'].isin(selected_players['PLAYER_NAME'])]
        df['GAME_DATE'] = pd.to_datetime(df['GAME_ID'].map(matchups).str[:10], format='%d/%m/%Y')
        df = (df
            .groupby(['GAME_DATE', 'PLAYER_NAME'])
            .agg(stats_per)
        )

        df['FGPCT'] = df['FGM']/df['FGA']
        df['FG3PCT'] = df['FG3M']/df['FG3A']
        df['FTPCT'] = df['FTM']/df['FTA']

        df = df.reset_index().rename(columns = stats)

        #st.plotly_chart(fig, use_container_width=True)

        lines = alt.Chart(df).mark_line(interpolate='basis').encode(
            x = 'Date',
            y = stats.get(options_stat),
            color = 'Player'
        )
        hover = alt.selection(type='single', nearest=True, on='mouseover', fields=['Date'], empty='none')
        tooltips = alt.Chart(df).mark_rule().encode(
            x = 'Date',
            y = stats.get(options_stat),
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip('Date', title='Date'), alt.Tooltip(stats.get(options_stat), title='Stat')]
        ).add_selection(hover)
        
        st.altair_chart(alt.layer(lines, tooltips).interactive(), use_container_width=True)

    else:
        st.write('Selecione jogadores na tabela.')

with dados_scatter:
    scatter_stat = st.columns([1,1,4])

    with scatter_stat[0]:
        scatter_stat_x = st.selectbox(
            label = 'Stat no eixo X', options = list(stats.keys())[3:], index = 0,
            format_func = lambda x: stats.get(x)
        )
    with scatter_stat[1]:
        scatter_stat_y = st.selectbox(
            label = 'Stat no eixo Y', options = list(stats.keys())[3:],index = 7,
            format_func = lambda x: stats.get(x)
        )

    df = df_bs.reset_index(drop=False)
    df = df[df['PLAYER_NAME'].isin(filtered_players['PLAYER_NAME'])]

    points = alt.Chart(df).mark_circle().encode(
        x = alt.X(scatter_stat_x, axis = alt.Axis(format=stats_fmt.get(scatter_stat_x), title = stats.get(scatter_stat_x))),
        y = alt.Y(scatter_stat_y, axis = alt.Axis(format=stats_fmt.get(scatter_stat_y), title = stats.get(scatter_stat_y))),
        color = 'PLAYER_NAME',
        tooltip = [
            alt.Tooltip(field = 'PLAYER_NAME', title = 'Player'),
            alt.Tooltip(field = scatter_stat_x, title = stats.get(scatter_stat_x), format = stats_fmt.get(scatter_stat_x).replace('0', '2')),
            alt.Tooltip(field = scatter_stat_y, title = stats.get(scatter_stat_y), format = stats_fmt.get(scatter_stat_y).replace('0', '2'))
        ]
    )
    st.altair_chart(points.interactive(),  use_container_width=True)