import nflgame
from pprint import pprint

games = nflgame.games(2014)

for game in games:
  for drive_key in game.data['drives']:
    if drive_key == 'crntdrv':
      continue
    drive = game.data['drives'][drive_key]
    pprint(drive)
    for play_key in drive['plays']:
      # down, distance, yardline
      # 
      # pprint(drive['plays'][play_key])
      if drive['plays'][play_key]['note']:
        print drive['plays'][play_key]['note']
      # pprint(drive['plays'][play_key])
    break 
