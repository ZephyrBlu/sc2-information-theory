import math
import copy
from pathlib import Path
from collections import defaultdict, namedtuple
from zephyrus_sc2_parser import parse_replay

from sc2_build_tokenizer.data.tokenized_builds import BUILDS
from sc2_build_tokenizer.data.token_information import TOKEN_INFORMATION
from sc2_build_tokenizer.data.token_probability import TOKEN_PROBABILITY
from sc2_build_tokenizer.constants import IGNORE_OBJECTS


TEST_REPLAY_PATH = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('IEM')
TokenizedBuild = namedtuple('TokenizedBuild', ['race', 'build'])
BuildPath = namedtuple('BuildPath', [
    'path',
    'probability',
    'probability_values',
    'information',
    'information_values',
])


def tokenize(replay, end=9408, ignore=IGNORE_OBJECTS):
    """
    9408 = 7min
    """
    parsed_replay = replay
    if type(replay) is str:
        parsed_replay = parse_replay(replay, local=True, network=False)

    builds = []
    for p_id, player in parsed_replay.players.items():
        player_build = []
        for obj in player.objects.values():
            if (
                not obj.birth_time
                or obj.birth_time > end
                or obj.name_at_gameloop(0) in ignore
            ):
                continue

            if 'BUILDING' in obj.type:
                player_build.append(obj.name_at_gameloop(0))

    return builds


def _generate_next_tokens(
    build,
    *,
    player_race=None,
    opp_race=None,
    max_token_size=8,
    build_index=0,
    build_path=[],
    information=0,
    information_path=[],
    probability=1,
    probability_path=[],
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
        updated_path = copy.deepcopy(build_path)
        updated_probability = copy.deepcopy(probability)
        updated_probability_values = copy.deepcopy(probability_path)
        updated_information = copy.deepcopy(information)
        updated_information_values = copy.deepcopy(information_path)

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
        updated_path.append(token)

        # exit if we're at the end of the build
        if build_index + i >= build_length:
            # print(new_path, token, build_index, i, build_index + i)
            all_paths.append(BuildPath(
                updated_path,
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
            build_path=updated_path,
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
    """
    1) Extract full build
    2) Iterate through build, create Markov Chains at each tick interval
    3)
    """
    paths = _generate_next_tokens(player_race, opp_race, build)
    # sort by overall conditional probability of path
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
