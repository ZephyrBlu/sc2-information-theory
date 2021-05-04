import math
from pathlib import Path
from collections import defaultdict

from sc2_build_tokenizer import (
    tokenize,
    parse_builds,
    generate_build_tokens,
    generate_paths,
)

TEST_REPLAY_PATH = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('IEM')
BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def _write_token_data():
    for player_race, other_races in BUILD_TOKENS.items():
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
