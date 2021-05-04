import traceback
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

ERRORS = defaultdict(int)


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
