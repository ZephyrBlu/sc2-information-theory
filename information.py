import json
import math
import traceback
from pathlib import Path
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

replays = Path('IEM')
buildings = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
units = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
ignored = defaultdict(int)
errors = defaultdict(int)

THIRTY_SEC = 672
IGNORE_OBJECTS = [
    'Pylon',
    'Overlord',
    'SupplyDepot',
    'MissileTurret',
    'SensorTower',
    'SpineCrawler',
    'SporeCrawler',
    'PhotonCannon',
    'Interceptor',
    'MULE',
    'AutoTurret',
    'Larva',
    'Egg',
    'LocustMP',
    'LocustMPPrecursor',
    'LocustMPFlying',
    'ShieldBattery',
    'Bunker',
    'CreepTumor',
    'CreepTumorQueen',
    'CreepTumorBurrowed',
    'Broodling',
    'BroodlingEscort',
    'NydusCanal',

    # remove gas buildings and workers to reduce noise
    'Extractor',
    'Assimilator',
    'Refinery',
    'Probe',
    'Drone',
    'SCV',
]


def recurse(dir_path, fn):
    """
    Recursively searches directories to parse replay files
    """
    for obj_path in dir_path.iterdir():
        if obj_path.is_file():
            try:
                replay = parse_replay(obj_path, local=True, network=False)
                print('Parsed Replay')
            except Exception:
                errors[traceback.format_exc()] += 1
                continue

            fn(replay)
        elif obj_path.is_dir():
            recurse(obj_path, fn)


def extract_objects(replay):
    for p_id, player in replay.players.items():
        opp_id = 1 if p_id == 2 else 2
        opp_race = replay.players[opp_id].race

        objects = player.objects.values()
        tick = 1
        for obj in objects:
            if not obj.birth_time or obj.name_at_gameloop(0) in IGNORE_OBJECTS:
                ignored[obj.name_at_gameloop(0)] += 1
                continue

            if obj.birth_time > tick * THIRTY_SEC:
                tick += 1
            gameloop = tick * THIRTY_SEC

            if 'UNIT' in obj.type:
                units[player.race][opp_race][gameloop][obj.name_at_gameloop(0)] += 1
            elif 'BUILDING' in obj.type:
                buildings[player.race][opp_race][gameloop][obj.name_at_gameloop(0)] += 1
    print('Recorded Object Frequencies\n')


# recurse(replays, extract_objects)

# with open('object_frequency.json', 'w') as obj_freq:
#     freq_data = {
#         'buildings': buildings,
#         'units': units,
#         'ignored': ignored,
#     }
#     json.dump(freq_data, obj_freq, indent=4)

# for e, c in errors.items():
#     print(f'{c} Errors:', e)

finals = Path('IEM/1 - Playoffs/Finals')
# finals = Path('IEM/1 - Playoffs/Round of 8/3 - TY vs PartinG')
# finals = Path('IEM/1 - Playoffs/Round of 4/1 - Reynor vs Maru')
with open('object_frequency.json', 'r') as obj_freq:
    freq = json.load(obj_freq)
    obj_proba = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))))

    for obj_type, type_data in freq.items():
        if obj_type == 'ignored':
            continue

        for player_race, opp_race_data in type_data.items():
            for opp_race, ticks in opp_race_data.items():
                for tick, objs in ticks.items():

                    total_count = 0
                    for obj_name, obj_count in objs.items():
                        total_count += obj_count

                    for obj_name, obj_count in objs.items():
                        obj_proba[obj_type][player_race][opp_race][tick][obj_name] = obj_count / total_count


def calc_information(replay):
    for p_id, player in replay.players.items():
        opp_id = 1 if p_id == 2 else 2
        opp_race = replay.players[opp_id].race

        objects = []
        for obj in player.objects.values():
            if obj.birth_time:
                objects.append(obj)
        objects.sort(key=lambda x: x.birth_time)

        buildings = []
        units = []
        tick = 1
        for obj in objects:
            if obj.birth_time > tick * THIRTY_SEC:
                tick += 1
            gameloop = str(tick * THIRTY_SEC)

            if (
                'BUILDING' in obj.type
                and obj.name_at_gameloop(0) in obj_proba['buildings'][player.race][opp_race][gameloop]
            ):
                information = -math.log2(obj_proba['buildings'][player.race][opp_race][gameloop][obj.name_at_gameloop(0)])
                buildings.append((int(gameloop), round(information, 2), obj.name_at_gameloop(0), obj.birth_time))
            elif (
                'UNIT' in obj.type
                and obj.name_at_gameloop(0) in obj_proba['units'][player.race][opp_race][gameloop]
            ):
                information = -math.log2(obj_proba['units'][player.race][opp_race][gameloop][obj.name_at_gameloop(0)])
                units.append((int(gameloop), round(information, 2), obj.name_at_gameloop(0), obj.birth_time))

        building_information = []
        for gameloop, info, name, birth_time in buildings:
            building_information.append((gameloop, info, name, birth_time))

        for b in building_information:
            print(b)
        print()

        unit_information = []
        for gameloop, info, name, birth_time in units:
            unit_information.append((gameloop, info, name, birth_time))

        for u in unit_information:
            print(u)
        print('\n')


recurse(finals, calc_information)
