import math
import copy
import traceback
from pathlib import Path
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

from token_information import TOKEN_INFORMATION
# from token_probability import TOKEN_PROBABILITY


# replays = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 6 - Reynor vs Zest - Z vs P - Pillars of Gold LE.SC2Replay')
replays = Path('IEM')
buildings = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
units = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
ignored = defaultdict(int)
errors = defaultdict(int)

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
    if dir_path.is_file():
        try:
            replay = parse_replay(dir_path, local=True, network=False)
            print('Parsed Replay')
        except Exception:
            errors[traceback.format_exc()] += 1

        fn(replay)
        return

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


def extract_build(replay):
    """
    1) Extract full build
    2) Iterate through build, create Markov Chains at each tick interval
    3)
    """
    for p_id, player in replay.players.items():
        opp_id = 1 if p_id == 2 else 2
        opp_race = replay.players[opp_id].race

        build = []
        objects = player.objects.values()
        for obj in objects:
            if (
                not obj.birth_time
                # 9408 = 7min
                or obj.birth_time > 9408
                or obj.name_at_gameloop(0) in IGNORE_OBJECTS
            ):
                ignored[obj.name_at_gameloop(0)] += 1
                continue

            if 'BUILDING' in obj.type:
                build.append(obj.name_at_gameloop(0))

        for i in range(0, len(build)):
            for index in range(1, 11):
                token = build[i:i + index]
                build_chains[player.race][opp_race][tuple(token)] += 1

                # exit if we're at the end of the build
                if i + index >= len(build):
                    break

    print('Recorded Building Frequencies\n')


def calc_information(
    player_race,
    opp_race,
    build,
    build_index,
    path,
    total,
):
    build_length = len(build)
    all_paths = []
    for i in range(1, 11):
        new_path = copy.deepcopy(path)
        new_total = copy.deepcopy(total)

        token = tuple(build[build_index:build_index + i])
        new_total += TOKEN_INFORMATION[player_race][opp_race][token]
        new_path.append(token)

        # exit if we're at the end of the build
        if build_index + i >= build_length:
            # print(new_path, token, build_index, i, build_index + i)
            all_paths.append((new_path, new_total))
            return all_paths

        calculated_paths = calc_information(
            player_race, opp_race, build, build_index + i, new_path, new_total
        )
        all_paths.extend(calculated_paths)
    return all_paths


def analyze_build(replay):
    """
    1) Extract full build
    2) Iterate through build, create Markov Chains at each tick interval
    3)
    """
    for p_id, player in replay.players.items():
        opp_id = 1 if p_id == 2 else 2
        opp_race = replay.players[opp_id].race

        build = []
        objects = player.objects.values()
        for obj in objects:
            if (
                not obj.birth_time
                # 9408 = 7min
                or obj.birth_time > 9408
                or obj.name_at_gameloop(0) in IGNORE_OBJECTS
            ):
                ignored[obj.name_at_gameloop(0)] += 1
                continue

            if 'BUILDING' in obj.type:
                build.append(obj.name_at_gameloop(0))

        paths = list(calc_information(player.race, opp_race, build, 0, [], 0))
        paths.sort(key=lambda x: x[1], reverse=True)
        for p, c in paths:
            print(c, p, '\n')
        print(build)


def write_token_data():
    for player_race, other_races in build_chains.items():
        for opp_race, chain in other_races.items():
            tokenized = list(chain.items())
            tokenized.sort(key=lambda x: x[1], reverse=True)

            print(f'{player_race} vs {opp_race}')
            total = sum(chain.values())
            print(total, chain.values())
            for tokens, count in tokenized:
                token_probability[player_race][opp_race][tokens] = count / total
                token_information[player_race][opp_race][tokens] = -math.log2(count / total)
                print(count, round(count / total, 3), round(-math.log2(count / total), 3), tokens)
            print('\n')

    def to_dict(struct):
        for k, v in struct.items():
            if isinstance(v, dict):
                struct[k] = to_dict(v)
        return dict(struct)

    with open('token_probability.py', 'w') as probabilities:
        probabilities.write(f'TOKEN_PROBABILITY = {to_dict(token_probability)}')

    with open('token_information.py', 'w') as information:
        information.write(f'TOKEN_INFORMATION = {to_dict(token_information)}')


# {<building token>: <token count>}
build_chains = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
token_probability = defaultdict(lambda: defaultdict(dict))
token_information = defaultdict(lambda: defaultdict(dict))
recurse(replays, extract_build)
write_token_data()
