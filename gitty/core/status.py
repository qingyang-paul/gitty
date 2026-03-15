import os
from gitty.core.index import read_index, update_index_entries
from gitty.core.tree import get_head_tree
from gitty.core.hash_object import hash_content
from gitty.core.add import is_ignored

def status(repo_path: str):
    repo_path = os.path.abspath(repo_path)
    
    # 1. Grab data sources
    index_entries = read_index(repo_path)
    index_dict = {e.name: e for e in index_entries}
    
    head_tree = get_head_tree(repo_path)
    
    # scan working directory
    working_files = set()
    for root, _, files in os.walk(repo_path):
        for f in files:
            full_path = os.path.join(root, f)
            if not is_ignored(full_path, repo_path):
                rel_path = os.path.relpath(full_path, repo_path)
                working_files.add(rel_path)
                
    # Initialize output buckets
    untracked = []
    
    modified_red_deleted = []
    modified_red_updated = []
    
    modified_green_new = []
    modified_green_deleted = []
    modified_green_updated = []
    
    entries_to_update = []
    
    # 2. Untracked
    for wf in working_files:
        if wf not in index_dict:
            untracked.append(wf)
            
    # 3. Modified Red (Working Tree vs Index)
    for name, entry in index_dict.items():
        if name not in working_files:
            modified_red_deleted.append(name)
        else:
            full_path = os.path.join(repo_path, name)
            stat_res = os.stat(full_path)
            
            ctime_int = int(stat_res.st_ctime)
            mtime_int = int(stat_res.st_mtime)
            size_int = stat_res.st_size
            
            # Simple check: if metadata differs, we hash check
            if entry.mtime != mtime_int or entry.size != size_int:
                with open(full_path, "rb") as f:
                    data = f.read()
                current_sha1_bytes, _ = hash_content(data, obj_type="blob")
                
                if current_sha1_bytes != entry.sha1:
                    modified_red_updated.append(name)
                else:
                    # User Note: "如果哈希一致，要更新现有index里的元数据"
                    entry.mtime = mtime_int
                    entry.ctime = ctime_int
                    entry.size = size_int
                    entry.ino = stat_res.st_ino
                    entry.dev = stat_res.st_dev
                    entries_to_update.append(entry)
                    
    # Save back metadata updates if any
    if entries_to_update:
        update_index_entries(repo_path, entries_to_update)
        
    # 4. Modified Green (Index vs HEAD Tree)
    for name, entry in index_dict.items():
        # If it's already deleted in red, git usually still considers it staged if it differs from HEAD,
        # but for simplicity let's compare index strictly.
        if name not in head_tree:
            modified_green_new.append(name)
        else:
            if entry.sha1.hex() != head_tree[name]:
                modified_green_updated.append(name)
                
    for head_name in head_tree:
        if head_name not in index_dict:
            modified_green_deleted.append(head_name)
            
    # 5. Print out the results
    print("On branch main\n") # Simplification
    
    has_changes = False
    
    if modified_green_new or modified_green_deleted or modified_green_updated:
        has_changes = True
        print("Changes to be committed:")
        print("  (use \"gitty restore --staged <file>...\" to unstage)\n")
        
        for f in sorted(modified_green_new):
            print(f"\tnew file:   {f}")
        for f in sorted(modified_green_updated):
            print(f"\tmodified:   {f}")
        for f in sorted(modified_green_deleted):
            print(f"\tdeleted:    {f}")
        print("")
        
    if modified_red_updated or modified_red_deleted:
        has_changes = True
        print("Changes not staged for commit:")
        print("  (use \"gitty add <file>...\" to update what will be committed)\n")
        
        for f in sorted(modified_red_updated):
            print(f"\tmodified:   {f}")
        for f in sorted(modified_red_deleted):
            print(f"\tdeleted:    {f}")
        print("")
        
    if untracked:
        has_changes = True
        print("Untracked files:")
        print("  (use \"gitty add <file>...\" to include in what will be committed)\n")
        for f in sorted(untracked):
            print(f"\t{f}")
        print("")
            
    if not has_changes:
        print("nothing to commit, working tree clean")