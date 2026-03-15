import os
import zlib
from typing import Dict

def parse_tree_entries(data: bytes) -> list:
    """Parse tree object content into a list of tuples: (mode, name, sha1)."""
    entries = []
    offset = 0
    while offset < len(data):
        # find the null byte marking end of [mode] [name]
        null_idx = data.find(b'\0', offset)
        if null_idx == -1:
            break
            
        mode_name = data[offset:null_idx].decode('utf-8')
        mode, name = mode_name.split(' ', 1)
        
        # next 20 bytes is the binary sha1
        sha1_start = null_idx + 1
        sha1 = data[sha1_start:sha1_start+20]
        
        entries.append((mode, name, sha1))
        offset = sha1_start + 20
        
    return entries

def read_tree_recursive(repo_path: str, tree_sha1: str, base_path: str = "") -> Dict[str, str]:
    """
    Recursively parse a tree object and return a flat dictionary mapping 
    file paths to their hex SHA-1 values.
    """
    results = {}
    
    dir_name = tree_sha1[:2]
    file_name = tree_sha1[2:]
    obj_path = os.path.join(repo_path, ".gitty", "objects", dir_name, file_name)
    
    if not os.path.exists(obj_path):
        return results
        
    with open(obj_path, "rb") as f:
        data = zlib.decompress(f.read())
        
    # extract header 'tree [size]\0'
    null_idx = data.find(b'\0')
    if null_idx == -1:
        return results
        
    content = data[null_idx+1:]
    entries = parse_tree_entries(content)
    
    for mode, name, sha1 in entries:
        full_path = os.path.join(base_path, name) if base_path else name
        sha1_hex = sha1.hex()
        
        if mode == "40000":
            # It's a directory
            subtree_results = read_tree_recursive(repo_path, sha1_hex, full_path)
            results.update(subtree_results)
        else:
            # It's a file
            results[full_path] = sha1_hex
            
    return results

def get_head_tree(repo_path: str) -> Dict[str, str]:
    """
    Get the flat file dict representation of the current HEAD commit's tree.
    Returns empty dict if no commits exist.
    """
    head_path = os.path.join(repo_path, ".gitty", "HEAD")
    commit_hash = None
    
    if not os.path.exists(head_path):
        return {}
        
    with open(head_path, "r", encoding="utf-8") as f:
        head_content = f.read().strip()
        
    if head_content.startswith("ref: "):
        ref_path = os.path.join(repo_path, ".gitty", head_content[5:])
        if os.path.exists(ref_path):
            with open(ref_path, "r", encoding="utf-8") as f:
                commit_hash = f.read().strip()
    else:
        # detached HEAD
        if len(head_content) == 40:
            commit_hash = head_content
            
    if not commit_hash:
        return {}
        
    # Read commit object to get tree hash
    dir_name = commit_hash[:2]
    file_name = commit_hash[2:]
    commit_obj_path = os.path.join(repo_path, ".gitty", "objects", dir_name, file_name)
    
    if not os.path.exists(commit_obj_path):
        return {}
        
    with open(commit_obj_path, "rb") as f:
        commit_data = zlib.decompress(f.read())
        
    null_idx = commit_data.find(b'\0')
    commit_content = commit_data[null_idx+1:].decode('utf-8')
    
    tree_hash = None
    for line in commit_content.split('\n'):
        if line.startswith("tree "):
            tree_hash = line.split(" ")[1]
            break
            
    if not tree_hash:
        return {}
        
    return read_tree_recursive(repo_path, tree_hash)
