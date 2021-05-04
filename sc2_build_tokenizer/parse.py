import traceback
from collections import defaultdict, namedtuple
from zephyrus_sc2_parser import parse_replay

from sc2_build_tokenizer.constants import IGNORE_OBJECTS

# 22.4 gameloops per second
SEVEN_MINUTES = 9408
ERRORS = defaultdict(int)
Build = namedtuple('Build', ['race', 'build'])


def recurse(dir_path, fn):
    """
    Recursively searches directories to parse replay files
    """
    if dir_path.is_file():
        try:
            replay = parse_replay(dir_path, local=True, network=False)
        except Exception:
            ERRORS[traceback.format_exc()] += 1

        return fn(replay)

    results = []
    for obj_path in dir_path.iterdir():
        if obj_path.is_file():
            try:
                replay = parse_replay(obj_path, local=True, network=False)
            except Exception:
                ERRORS[traceback.format_exc()] += 1
                continue

            results.append(fn(replay))
        elif obj_path.is_dir():
            results.extend(recurse(obj_path, fn))

    return results


def parse_builds(replays, end=SEVEN_MINUTES, ignore=IGNORE_OBJECTS):
    """
    9408 = 7min
    """
    parsed_replays = replays
    if type(replays) is str:
        parsed_replays = recurse(replays)

    builds = []
    for replay in parsed_replays:
        replay_builds = []
        for p_id, player in replay.players.items():
            player_build = Build(player.race, [])
            for obj in player.objects.values():
                if (
                    not obj.birth_time
                    or obj.birth_time > end
                    or obj.name_at_gameloop(0) in ignore
                ):
                    continue

                if 'BUILDING' in obj.type:
                    player_build.build.append(obj.name_at_gameloop(0))
            replay_builds.append(player_build)
        builds.append(replay_builds)

    if len(builds) == 1:
        return builds[0]
    return builds
