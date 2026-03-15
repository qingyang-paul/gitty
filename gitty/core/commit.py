import os
import logging
from typing import List, Dict, Any
from gitty.core.index import read_index, IndexEntry
from gitty.core.hash_object import write_object

def _build_tree_recursive(repo_path: str, tree_dict: Dict[str, Any]) -> bytes:
    """Recursively builds tree objects and returns the SHA-1 bytes of this tree."""
    entries_data = bytearray()
    
    # Sort children by name for consistent tree hash
    sorted_names = sorted(tree_dict.keys())
    
    for name in sorted_names:
        item = tree_dict[name]
        if isinstance(item, IndexEntry):
            # It's a file
            # Format: [mode] [name]\0[20 byte hash]
            # Convert mode to octal string without '0o' prefix (e.g. 100644)
            mode_str = oct(item.mode)[2:]
            entry = f"{mode_str} {name}\0".encode('utf-8') + item.sha1
            entries_data.extend(entry)
        else:
            # It's a subdirectory (dict)
            # Recursively build subtree
            sub_sha1 = _build_tree_recursive(repo_path, item)
            # Directory mode is typically 40000 in git
            entry = f"40000 {name}\0".encode('utf-8') + sub_sha1
            entries_data.extend(entry)
            
    # Write the combined entries as a tree object
    return write_object(repo_path, bytes(entries_data), obj_type="tree")

def build_tree_from_index(repo_path: str, entries: List[IndexEntry]) -> str:
    """Builds the root tree from index entries and returns its hex SHA-1."""
    if not entries:
        return None
        
    # Build a nested dictionary representing the directory structure
    root = {}
    
    for entry in entries:
        parts = entry.name.split('/')
        current = root
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = entry
        
    # Recursively hash
    root_sha1_bytes = _build_tree_recursive(repo_path, root)
    return root_sha1_bytes.hex()

def commit(repo_path: str, message: str, author_name: str, author_email: str, timestamp: int, tz_offset: str):
    """
    Creates a commit object. All parameters MUST be explicitly provided.
    tz_offset string like "+0800".
    """
    if not all([repo_path, message, author_name, author_email, timestamp, tz_offset]):
        raise ValueError("All commit parameters (author, email, time, tz) must be explicitly provided.")
        
    repo_path = os.path.abspath(repo_path)
    entries = read_index(repo_path)
    
    if not entries:
        logging.error("Nothing to commit (index is empty).")
        return
        
    root_tree_hash = build_tree_from_index(repo_path, entries)
    
    # Resolve HEAD to find parent
    head_path = os.path.join(repo_path, ".gitty", "HEAD")
    parent_hash = None
    ref_path = None
    
    if os.path.exists(head_path):
        with open(head_path, "r", encoding="utf-8") as f:
            head_content = f.read().strip()
            
        if head_content.startswith("ref: "):
            ref_rel_path = head_content[5:]
            ref_path = os.path.join(repo_path, ".gitty", ref_rel_path)
            if os.path.exists(ref_path):
                with open(ref_path, "r", encoding="utf-8") as f:
                    parent_hash = f.read().strip()
        else:
            # Detached head
            parent_hash = head_content
            
    # Format the commit string
    commit_lines = []
    commit_lines.append(f"tree {root_tree_hash}")
    if parent_hash:
        commit_lines.append(f"parent {parent_hash}")
        
    author_line = f"author {author_name} <{author_email}> {timestamp} {tz_offset}"
    committer_line = f"committer {author_name} <{author_email}> {timestamp} {tz_offset}"
    
    commit_lines.append(author_line)
    commit_lines.append(committer_line)
    commit_lines.append("")
    commit_lines.append(message)
    
    commit_data = "\n".join(commit_lines).encode("utf-8")
    
    # Save commit object
    commit_sha1_bytes = write_object(repo_path, commit_data, obj_type="commit")
    commit_hex = commit_sha1_bytes.hex()
    
    # Update reference
    if ref_path:
        # Create refs directories if they don't exist
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, "w", encoding="utf-8") as f:
            f.write(commit_hex + "\n")
    else:
        # Detached head update
        with open(head_path, "w", encoding="utf-8") as f:
            f.write(commit_hex + "\n")
            
    print(f"[{'root-commit' if not parent_hash else 'commit'} {commit_hex[:7]}] {message.split(chr(10))[0]}")