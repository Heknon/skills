import argparse

from notify.mailer import send_all
from notify.summary import build_messages


def main():
    parser = argparse.ArgumentParser(prog="notify-send")
    parser.add_argument("--date", help="day to summarise, YYYY-MM-DD; default yesterday")
    args = parser.parse_args()
    send_all(build_messages(args.date))
