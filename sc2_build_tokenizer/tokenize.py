import copy
from pathlib import Path
from collections import defaultdict, namedtuple

from sc2_build_tokenizer.data import TOKEN_INFORMATION
from sc2_build_tokenizer.data import TOKEN_PROBABILITY

TEST_REPLAY_PATH = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('IEM')
BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
TokenizedBuild = namedtuple('TokenizedBuild', [
    'tokens',
    'probability',
    'probability_values',
    'information',
    'information_values',
])


def generate_build_tokens(build, source=None):
    builds = build
    if type(build) is not list:
        builds = [build]

    build_tokens = source
    if not source:
        build_tokens = defaultdict(int)

    for b in builds:
        for i in range(0, len(b)):
            for index in range(1, 9):
                token = b[i:i + index]
                build_tokens[tuple(token)] += 1

                # exit if we're at the end of the build
                if i + index >= len(build):
                    break

    return build_tokens


def _generate_next_tokens(
    build,
    *,
    player_race=None,
    opp_race=None,
    max_token_size=8,
    build_index=0,
    build_tokens=[],
    probability=1,
    probability_values=[],
    information=0,
    information_values=[],
    token_probability=TOKEN_PROBABILITY,
    token_information=TOKEN_INFORMATION,
):
    if player_race and opp_race:
        if (
            player_race in token_probability
            and opp_race in token_probability[player_race]
        ):
            token_probability = token_probability[player_race][opp_race]

        if (
            player_race in token_information
            and opp_race in token_information[player_race]
        ):
            token_information = token_information[player_race][opp_race]

    build_length = len(build)
    all_paths = []
    # generate new path information for each possible new token
    for i in range(1, max_token_size + 1):
        # don't need copies for values, but it keeps things explicit
        updated_tokens = copy.deepcopy(build_tokens)
        updated_probability = copy.deepcopy(probability)
        updated_probability_values = copy.deepcopy(probability_values)
        updated_information = copy.deepcopy(information)
        updated_information_values = copy.deepcopy(information_values)

        token = tuple(build[build_index:build_index + i])

        # if we don't have a record of the preceding sequence,
        # it was too unlikely to record so we bail
        if token not in token_probability:
            continue

        token_prob = 1
        # print(token, len(token))
        for index in range(0, len(token)):
            token_fragment = token[:index + 1]
            token_prob *= token_probability[token_fragment]
            updated_probability_values.append(
                token_probability[token_fragment]
            )
            updated_information += token_information[token_fragment]
            updated_information_values.append(
                token_information[token_fragment]
            )
            # print(
            #     index + 1,
            #     TOKEN_PROBABILITY[player_race][opp_race][token_fragment],
            #     token_prob,
            #     token_fragment,
            # )
        # print('\n')
        updated_probability *= token_prob
        updated_tokens.append(token)

        # exit if we're at the end of the build
        if build_index + i >= build_length:
            # print(new_path, token, build_index, i, build_index + i)
            all_paths.append(TokenizedBuild(
                updated_tokens,
                updated_probability,
                updated_probability_values,
                updated_information,
                updated_information_values,
            ))
            return all_paths

        calculated_paths = _generate_next_tokens(
            build,
            player_race=player_race,
            opp_race=opp_race,
            build_index=build_index + i,
            build_tokens=updated_tokens,
            probability=updated_probability,
            probability_values=updated_probability_values,
            information=updated_information,
            information_values=updated_information_values,
            token_probability=token_probability,
            token_information=token_information
        )
        all_paths.extend(calculated_paths)
    return all_paths


def generate_paths(build, player_race, opp_race):
    paths = _generate_next_tokens(
        build,
        player_race=player_race,
        opp_race=opp_race,
    )
    # sort by overall conditional probability of path
    paths.sort(key=lambda x: x[2], reverse=True)
    for pa, i, pr, ip, pp in paths:
        print(i, pr, pa, ip, pp, '\n')
    print(build)
    return paths
