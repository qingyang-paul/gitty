import os
import logging
from gitty.core.hash_object import write_object
from gitty.core.index import IndexEntry, update_index_entries

def is_ignored(path: str, repo_path: str) -> bool:
    # A simple implementation to ignore .gitty itself and some basics
    # In a full implementation we would parse .gittyignore
    if ".gitty" in path.split(os.sep):
        return True
    return False

def add(repo_path: str, paths: list[str]):
    repo_path = os.path.abspath(repo_path)
    new_entries = []

    for path_arg in paths:
        target_path = os.path.abspath(os.path.join(repo_path, path_arg))

        if not os.path.exists(target_path):
            logging.error(f"fatal: pathspec '{path_arg}' did not match any files")
            continue

        files_to_add = []
        if os.path.isfile(target_path):
            files_to_add.append(target_path)
        elif os.path.isdir(target_path):
            for root, _, files in os.walk(target_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    if not is_ignored(full_path, repo_path):
                        files_to_add.append(full_path)

        for p in files_to_add:
            try:
                with open(p, "rb") as f:
                    data = f.read()
            except Exception as e:
                logging.error(f"Could not read {p}: {e}")
                continue

            # Calculate hash and save blob
            sha1_bytes = write_object(repo_path, data, obj_type="blob")
            
            # Create IndexEntry
            stat_res = os.stat(p)
            rel_path = os.path.relpath(p, repo_path)
            
            # The ctime/mtime in struct should be cast to integer 
            ctime_int = int(stat_res.st_ctime)
            mtime_int = int(stat_res.st_mtime)
            
            entry = IndexEntry(
                ctime=ctime_int,
                mtime=mtime_int,
                dev=int(stat_res.st_dev),
                ino=int(stat_res.st_ino),
                mode=int(stat_res.st_mode),
                uid=int(stat_res.st_uid),
                gid=int(stat_res.st_gid),
                size=int(stat_res.st_size),
                sha1=sha1_bytes,
                flags=len(rel_path.encode('utf-8')) & 0x0FFF,
                name=rel_path
            )
            new_entries.append(entry)
            logging.debug(f"Added '{rel_path}' to index.")

    if new_entries:
        update_index_entries(repo_path, new_entries)
        print(f"Added {len(new_entries)} files to the index.")