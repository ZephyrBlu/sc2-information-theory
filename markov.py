import math
import copy
import traceback
from pathlib import Path
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

from extracted_builds import BUILDS
from token_information import TOKEN_INFORMATION
from token_probability import TOKEN_PROBABILITY


test_replay = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
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

        extracted.append((player.race, opp_race, build))

        for i in range(0, len(build)):
            for index in range(1, 9):
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
    build_index=0,
    build_path=[],
    information=0,
    information_path=[],
    probability=1,
    probability_path=[],
):
    build_length = len(build)
    all_paths = []
    for i in range(1, 9):
        new_path = copy.deepcopy(build_path)
        new_information = copy.deepcopy(information)
        new_information_path = copy.deepcopy(information_path)
        new_prob = copy.deepcopy(probability)
        new_prob_path = copy.deepcopy(probability_path)

        token = tuple(build[build_index:build_index + i])
        if token not in TOKEN_INFORMATION[player_race][opp_race]:
            continue

        token_prob = 1
        # print(token, len(token))
        for index in range(0, len(token)):
            token_fragment = token[:index + 1]
            token_prob *= TOKEN_PROBABILITY[player_race][opp_race][token_fragment]
            new_prob_path.append(
                TOKEN_PROBABILITY[player_race][opp_race][token_fragment]
            )
            new_information += TOKEN_INFORMATION[player_race][opp_race][token_fragment]
            new_information_path.append(
                TOKEN_INFORMATION[player_race][opp_race][token_fragment]
            )
            # print(
            #     index + 1,
            #     TOKEN_PROBABILITY[player_race][opp_race][token_fragment],
            #     token_prob,
            #     token_fragment,
            # )
        # print('\n')
        new_prob *= token_prob
        new_path.append(token)

        # exit if we're at the end of the build
        if build_index + i >= build_length:
            # print(new_path, token, build_index, i, build_index + i)
            all_paths.append((
                new_path,
                new_information,
                new_prob,
                new_information_path,
                new_prob_path,
            ))
            return all_paths

        calculated_paths = calc_information(
            player_race,
            opp_race,
            build,
            build_index + i,
            new_path,
            new_information,
            new_information_path,
            new_prob,
            new_prob_path,
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

        paths = list(calc_information(player.race, opp_race, build))
        paths.sort(key=lambda x: x[2], reverse=True)
        for pa, i, pr, ip, pp in paths:
            print(i, pr, pa, ip, pp, '\n')
        print(build)


def write_token_data():
    """
    How should probabilities be calculated?

    Probability of length n-token? I.e. given all n length tokens, probability it's this one

    Markov chain of probabilities? I.e. P(n|n-1) for all n in the token

    Markov state of probability? I.e. given previous n-1 token, what's the probability of token n

    Pr(x) = Pr(x1, x2,..., xL )
          = Pr(x1)Pr(x2 | x1)...Pr(xL | x1,..., xL−1)
    Ex: Pr(cggt) = Pr(c)Pr(g | c)Pr(g | cg)Pr(t|cgg)
    """
    for player_race, other_races in build_chains.items():
        for opp_race, chain in other_races.items():
            print(f'{player_race} vs {opp_race}')

            tokenized = list(chain.items())
            tokenized.sort(key=lambda x: x[1], reverse=True)

            unigrams = {}
            ngram_tokens = defaultdict(dict)
            for tokens, count in tokenized:
                if len(tokens) == 1:
                    unigrams[tokens] = count
                    continue

                ngram = tokens[:-1]
                predicted = tokens[-1]

                ngram_tokens[ngram][predicted] = count

            total = sum(unigrams.values())
            tokens = list(unigrams.items())
            tokens.sort(key=lambda x: x[1], reverse=True)
            for token, count in tokens:
                token_probability[player_race][opp_race][token] = count / total
                token_information[player_race][opp_race][token] = -math.log2(count / total)
                print(count, token_probability[player_race][opp_race][token], token)

            print('\n\n')

            for tokens, outcomes in ngram_tokens.items():
                total = sum(outcomes.values())
                if total < 10:
                    continue

                predicted = list(outcomes.items())
                predicted.sort(key=lambda x: x[1], reverse=True)
                print(tokens)
                for token, count in predicted:
                    token_probability[player_race][opp_race][(*tokens, token)] = count / total
                    token_information[player_race][opp_race][(*tokens, token)] = -math.log2(count / total)
                    print(count, token_probability[player_race][opp_race][(*tokens, token)], token)
                print('\n')

            # print(f'{player_race} vs {opp_race}')
            # total = sum(chain.values())
            # print(total, chain.values())
            # for tokens, count in tokenized:
            #     token_probability[player_race][opp_race][tokens] = count / total
            #     token_information[player_race][opp_race][tokens] = -math.log2(count / total)
            #     print(count, round(count / total, 3), round(-math.log2(count / total), 3), tokens)
            # print('\n')

    def to_dict(struct):
        for k, v in struct.items():
            if isinstance(v, dict):
                struct[k] = to_dict(v)
        return dict(struct)

    with open('token_probability.py', 'w') as probabilities:
        probabilities.write(f'TOKEN_PROBABILITY = {to_dict(token_probability)}')

    with open('token_information.py', 'w') as information:
        information.write(f'TOKEN_INFORMATION = {to_dict(token_information)}')


def write_builds():
    with open('extracted_builds.py', 'w') as builds:
        builds.write(f'BUILDS = {extracted}')


extracted = []
# {<building token>: <token count>}
build_chains = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
token_probability = defaultdict(lambda: defaultdict(dict))
token_information = defaultdict(lambda: defaultdict(dict))
recurse(test_replay, analyze_build)

# if not BUILDS:
#     print('No existing builds, parsing replays')
#     recurse(replays, extract_build)
#     write_builds()
# else:
#     print('Found existing builds')
#     for player_race, opp_race, build in BUILDS:
#         for i in range(0, len(build)):
#             for index in range(1, 9):
#                 token = build[i:i + index]
#                 build_chains[player_race][opp_race][tuple(token)] += 1

#                 # exit if we're at the end of the build
#                 if i + index >= len(build):
#                     break

# write_token_data()
