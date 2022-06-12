import opendatasets as od

# # Baixar dataset atualizado do kaggle
# dataset_url = 'https://www.kaggle.com/datasets/marcoantnio23/nba-datasets-atualizado'
# od.download(dataset_url, data_dir='./dados', force=True)

# Script de atualização
import pandas as pd, time
from nba_api.stats.endpoints import leaguegamelog, boxscoretraditionalv2

pd.set_option('display.max_columns', None)

games = pd.read_parquet('dados/Jogos.parquet')
games_last_season = games['SEASON_ID'].astype(str).str[1:].astype(int).max()
boxscores = pd.read_parquet('dados/BoxScores.parquet')

games = games[games['SEASON_ID'].astype(str).str[1:].astype(int) < games_last_season]

seasons = [season for season in range(games_last_season,3000)]
#seasons = [season for season in range(2020,3000)]
season_types = ['Pre Season', 'Regular Season', 'Playoffs']

for season_type in season_types:
    for season in seasons:
        games_season = leaguegamelog.LeagueGameLog(player_or_team_abbreviation='T', season=season, season_type_all_star=season_type).league_game_log.get_data_frame()
        if not games_season.empty:
            print('{0} de {1} atualizada.'.format(season_type, season))
            games = pd.concat([games, games_season])
            games = games[-games['WL'].isnull()]
            time.sleep(0.6)
        else:
            break

games['SEASON_ID'] = games['SEASON_ID'].astype(int)
games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
games.to_parquet('dados/Jogos.parquet', index=False)
i = 0
while True:
    boxscores_games_id = boxscores.GAME_ID
    games_to_update_id = games[-games.GAME_ID.isin(boxscores_games_id)]

    if games_to_update_id.empty:
        print('BoxScores atualizadas')
        break

    game_to_update_id = games_to_update_id.GAME_ID.min()
    
    print('Atualizando jogo {0}'.format(game_to_update_id))

    try:
        boxscore_update = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_to_update_id).player_stats.get_data_frame()
    except:
        print('Erro na API. Tentando novamente...')
        time.sleep(60)
        continue

    if boxscore_update.empty:
        boxscore_update = pd.DataFrame(data={'GAME_ID':[game_to_update_id]})
    else:
        try:
            boxscore_update['MIN'] = boxscore_update['MIN'].astype('str').str.replace('None','0').str.split(':', expand=True).pipe(lambda x: x[0].astype(float)+x[1].astype(float)/60)
        except:
            pass
    
    boxscores = pd.concat([boxscores, boxscore_update])
    i=i+1
    if i >= 100:
        boxscores.to_parquet('dados/BoxScores.parquet', index=False)
        i = 0
        continue

boxscores.to_parquet('dados/BoxScores.parquet', index=False)