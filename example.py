from pathlib import Path
from collections import defaultdict

from sc2_build_tokenizer import (
    tokenize,
    parse_builds,
    generate_build_tokens,
    generate_token_distributions,
    generate_paths,
)
from sc2_build_tokenizer.data import PARSED_BUILDS

TEST_REPLAY_PATH = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('IEM')

BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
TOKEN_PROBABILITY = defaultdict(lambda: defaultdict(dict))
TOKEN_INFORMATION = defaultdict(lambda: defaultdict(dict))


def to_dict(struct):
    for k, v in struct.items():
        if isinstance(v, dict):
            struct[k] = to_dict(v)
    return dict(struct)


def manual_tokenize(*, _write_builds=False, _write_distributions=True):
    if _write_builds:
        parsed_builds = parse_builds(REPLAY_PATH)

        with open('sc2_build_tokenizer/data/parsed_builds.py', 'w') as builds:
            builds.write(f'BUILDS = {parsed_builds}')
    else:
        parsed_builds = PARSED_BUILDS

    for build in parsed_builds:
        races = []
        for player_build in build:
            races.append(build.race)

        for player_build in build:
            player_race = build.race
            opp_race = races[0] if races[1] == player_race else races[1]
            BUILD_TOKENS[player_race][opp_race] = generate_build_tokens(
                player_build,
                BUILD_TOKENS[player_race][opp_race],
            )

    for player_race, other_races in BUILD_TOKENS.items():
        for opp_race, chain in other_races.items():
            print(f'{player_race} vs {opp_race}')

            distributions = generate_token_distributions(chain)
            TOKEN_PROBABILITY[player_race][opp_race] = distributions.probability
            TOKEN_INFORMATION[player_race][opp_race] = distributions.information

    if _write_distributions:
        with open('sc2_build_tokenizer/data/token_probability.py', 'w') as probabilities:
            probabilities.write(f'TOKEN_PROBABILITY = {to_dict(TOKEN_PROBABILITY)}')

        with open('sc2_build_tokenizer/data/token_information.py', 'w') as information:
            information.write(f'TOKEN_INFORMATION = {to_dict(TOKEN_INFORMATION)}')

    test_builds = parse_builds(TEST_REPLAY_PATH)[0]
    races = []
    for build in test_builds:
        races.append(build.race)

    for build in test_builds:
        opp_race = races[0] if build.race == races[1] else races[1]
        paths = generate_paths(
            build.build,
            build.race,
            opp_race,
            TOKEN_PROBABILITY,
            TOKEN_INFORMATION,
        )
        for pa, i, pr, ip, pp in paths:
            print(i, pr, pa, ip, pp, '\n')
        print(build, '\n\n')


manual_tokenize(
    _write_builds=False,
    _write_distributions=True,
)
