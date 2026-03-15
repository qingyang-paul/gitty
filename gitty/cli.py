import argparse
import os
import sys
import time
import logging
from gitty.core.init import init
from gitty.core.add import add
from gitty.core.commit import commit
from gitty.core.config import get_user_info

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_tz_offset():
    """Get formatted timezone offset e.g. +0800"""
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset_hours = abs(offset) // 3600
    offset_minutes = (abs(offset) % 3600) // 60
    sign = "-" if offset > 0 else "+"
    return f"{sign}{offset_hours:02d}{offset_minutes:02d}"

def main():
    parser = argparse.ArgumentParser(prog="gitty", description="A simple git clone")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Create an empty Git repository")
    init_parser.add_argument("path", nargs="?", default=".", help="Where to create the repository")

    # add command
    add_parser = subparsers.add_parser("add", help="Add file contents to the index")
    add_parser.add_argument("paths", nargs="+", help="Files to add content from")

    # commit command
    commit_parser = subparsers.add_parser("commit", help="Record changes to the repository")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")

    # status command
    status_parser = subparsers.add_parser("status", help="Show the working tree status")

    args = parser.parse_args()

    # Determine repo path (assuming current dir for now unless it's init <dir>)
    target_path = os.path.abspath(".")

    if args.command == "init":
        target_path = os.path.abspath(args.path)
        init(repo_path=target_path)
    elif args.command == "add":
        add(repo_path=target_path, paths=args.paths)
    elif args.command == "status":
        from gitty.core.status import status
        status(repo_path=target_path)
    elif args.command == "commit":
        name, email = get_user_info(target_path)
        timestamp = int(time.time())
        tz_offset = get_tz_offset()
        
        commit(
            repo_path=target_path,
            message=args.message,
            author_name=name,
            author_email=email,
            timestamp=timestamp,
            tz_offset=tz_offset
        )

if __name__ == "__main__":
    main()
