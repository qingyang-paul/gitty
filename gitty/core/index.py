import struct
import os
import stat
from typing import List

# Index entry format: ctime(8), mtime(8), dev(4), ino(4), mode(4), uid(4), gid(4), size(4), sha1(20), flags(2)
INDEX_ENTRY_FORMAT = ">QQIIIIII20sH"
INDEX_ENTRY_SIZE = struct.calcsize(INDEX_ENTRY_FORMAT)

class IndexEntry:
    def __init__(self, ctime: int, mtime: int, dev: int, ino: int, mode: int, uid: int, gid: int, size: int, sha1: bytes, flags: int, name: str):
        self.ctime = ctime
        self.mtime = mtime
        self.dev = dev
        self.ino = ino
        self.mode = mode
        self.uid = uid
        self.gid = gid
        self.size = size
        self.sha1 = sha1
        self.flags = flags
        self.name = name

def read_index(repo_path: str) -> List[IndexEntry]:
    index_path = os.path.join(repo_path, ".gitty", "index")
    entries = []
    if not os.path.exists(index_path):
        return entries
    
    with open(index_path, "rb") as f:
        data = f.read()

    offset = 0
    while offset + INDEX_ENTRY_SIZE <= len(data):
        entry_data = data[offset:offset+INDEX_ENTRY_SIZE]
        ctime, mtime, dev, ino, mode, uid, gid, size, sha1, flags = struct.unpack(INDEX_ENTRY_FORMAT, entry_data)
        offset += INDEX_ENTRY_SIZE
        
        name_len = flags & 0x0FFF
        name_bytes = data[offset:offset+name_len]
        name = name_bytes.decode('utf-8')
        offset += name_len
        
        # pad to an 8-byte boundary length
        entry_len = INDEX_ENTRY_SIZE + name_len
        pad_len = 8 - (entry_len % 8)
        if pad_len == 0:
            pad_len = 8
        offset += pad_len
            
        entries.append(IndexEntry(
            ctime=ctime, mtime=mtime, dev=dev, ino=ino, mode=mode,
            uid=uid, gid=gid, size=size, sha1=sha1, flags=flags, name=name
        ))
    
    return entries

def write_index(repo_path: str, entries: List[IndexEntry]):
    index_path = os.path.join(repo_path, ".gitty", "index")
    
    # Write to a temporary list of bytes first
    out = bytearray()
    
    # Sort entries by name (standard git behavior)
    entries.sort(key=lambda e: e.name)
    
    for entry in entries:
        name_bytes = entry.name.encode('utf-8')
        flags = (entry.flags & 0xF000) | (len(name_bytes) & 0x0FFF)
        
        entry_data = struct.pack(
            INDEX_ENTRY_FORMAT,
            entry.ctime, entry.mtime, entry.dev, entry.ino, entry.mode,
            entry.uid, entry.gid, entry.size, entry.sha1, flags
        )
        
        out.extend(entry_data)
        out.extend(name_bytes)
        
        # pad to an 8-byte boundary for the whole entry
        entry_len = INDEX_ENTRY_SIZE + len(name_bytes)
        pad_len = 8 - (entry_len % 8)
        # In actual git, there is always at least 1 null byte for padding.
        # But wait, from `gitty.md` it is just say name is variable-length.
        # If we pad, we must pad 1 to 8 bytes.
        if pad_len == 0:
            pad_len = 8
        out.extend(b'\x00' * pad_len)
        
    with open(index_path, "wb") as f:
        f.write(out)

def update_index_entries(repo_path: str, new_entries: List[IndexEntry]):
    """Update existing entries or add new ones based on name."""
    existing_entries = read_index(repo_path)
    
    entry_dict = {e.name: e for e in existing_entries}
    for ne in new_entries:
        entry_dict[ne.name] = ne
        
    write_index(repo_path, list(entry_dict.values()))
