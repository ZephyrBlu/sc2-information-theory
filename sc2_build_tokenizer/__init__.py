from sc2_build_tokenizer.parse import parse_builds
from sc2_build_tokenizer.tokenize import generate_build_tokens, generate_paths


def tokenize(replay):
    builds = parse_builds(replay)
    races = []
    for build in builds:
        races.append(build.race)

    tokenized = []
    for build in builds:
        player_race = build.race
        opp_race = races[0] if races[1] == player_race else races[1]
        paths = generate_paths(build, player_race, opp_race)
        tokenized.append(paths[0])

    return tokenized
