import re
from datetime import datetime, timedelta
from pathlib import Path
from tkinter.filedialog import askdirectory


# Affects grouping stats of separate shots.
# If your backups are named f.e.:
# shot3_1_bak1.hip, shot3_1_bak2.hip, shot3_2_bak1.hip, shot3_2_bak2.hip
# then by default (with UNDERSCORES set to 1) it's assumed your core shot name ends after first underscore, so:
# shot3_1_bak1 and shot3_2_bak1 are both the same shot = shot3
UNDERSCORES = 1;

# Printed out column width (character count)
COL_WIDTH = 25

# how many minutes between backups are considered different sessions
# (time between sessions is not counted)
# if you save often - 30 is ok, if rarely, set it to 60 or more
NEXT_SESSION = 30


# taken from https://stackoverflow.com/a/4836734
def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


# group hips into shots (the same rule as described on top of the file)
def split_shots(hips):
    shots = []
    prev_base = ""
    for h in hips:
        base = "_".join(Path(h).stem.split("_")[:UNDERSCORES])
        if prev_base != base:
            shots.append([h])
        else:
            shots[-1].append(h)

        prev_base = base

    return shots


# get readable datetime / timedelta str  (remove milliseconds essentially)
def rd(d):
    return str(d).split(".")[0]


# print list with elements aligned based on min number of characters
def print_table(*l):
    print(str(("{: <" + str(COL_WIDTH) + "} ")*len(l)).format(*l))


def main():
    d = askdirectory(title="Where to look for backups? (Yea, it searches in subdirs)")
    p = Path(d)

    hips = natural_sort([str(p) for p in p.glob('**/*bak*.hip*')])

    shots = split_shots(hips)

    total_dur = timedelta()

    for shot in shots:
        prev_hip = None
        session_start = None
        prev_date = None

        shot_dur = timedelta()

        print('-'*100)
        print("_".join(Path(shot[0]).stem.split("_")[:UNDERSCORES]), "sessions:\n")
        print_table("last file:", "start:", "end:", "duration:")

        for idx, hip in enumerate(shot):
            hip = Path(hip)
            date = datetime.fromtimestamp(hip.stat().st_ctime)

            if not session_start:
                prev_hip = hip
                session_start = date
                prev_date = date
                continue

            # consider end of session if time delta between backups is above NN minutes
            diff = date - prev_date
            end_session = (diff.total_seconds()/60) > NEXT_SESSION

            # or iterated hip is the last one in subshot
            last_hip = idx == len(shot)-1

            if end_session:
                session_dur = prev_date - session_start
                print_table(prev_hip.name, rd(session_start), rd(prev_date), rd(session_dur))

                shot_dur += session_dur
                session_start = prev_date = None
            elif last_hip:
                session_dur = date - session_start
                print_table(hip.name, rd(session_start), rd(date), rd(session_dur))

                shot_dur += session_dur
            else:
                prev_hip = hip
                prev_date = date

        print_table("", "", "total:", rd(shot_dur))

        total_dur += shot_dur

    print('-'*100)
    print(">>> >>> >>> duration of everything:", rd(total_dur), " <<< <<< <<<")


if __name__ == '__main__':
    main()

