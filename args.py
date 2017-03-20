import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--courses-list-only',
    dest='courses_list_only',
    action='store_true',
    help='Only creates the DATA_COURSE_LIST.json file')

arguments = parser.parse_args()
