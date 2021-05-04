import traceback
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

from sc2_build_tokenizer.constants import IGNORE_OBJECTS

ERRORS = defaultdict(int)
BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def recurse(dir_path, fn):
    """
    Recursively searches directories to parse replay files
    """
    if dir_path.is_file():
        try:
            replay = parse_replay(dir_path, local=True, network=False)
            print('Parsed Replay')
        except Exception:
            ERRORS[traceback.format_exc()] += 1

        fn(replay)
        return

    for obj_path in dir_path.iterdir():
        if obj_path.is_file():
            try:
                replay = parse_replay(obj_path, local=True, network=False)
                print('Parsed Replay')
            except Exception:
                ERRORS[traceback.format_exc()] += 1
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
                continue

            if 'BUILDING' in obj.type:
                build.append(obj.name_at_gameloop(0))

        extracted.append((player.race, opp_race, build))

        for i in range(0, len(build)):
            for index in range(1, 9):
                token = build[i:i + index]
                BUILD_TOKENS[player.race][opp_race][tuple(token)] += 1

                # exit if we're at the end of the build
                if i + index >= len(build):
                    break
