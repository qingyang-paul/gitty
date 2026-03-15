import os
import hashlib
import zlib

def hash_content(data: bytes, obj_type: str = "blob") -> bytes:
    """
    Format string: {type} {size}\\0{data}
    Returns raw SHA-1 bytes (20 bytes).
    """
    header = f"{obj_type} {len(data)}\0".encode("utf-8")
    store = header + data
    
    sha1 = hashlib.sha1()
    sha1.update(store)
    return sha1.digest(), store

def write_object(repo_path: str, data: bytes, obj_type: str = "blob") -> bytes:
    """
    Writes object to .gitty/objects/ and returns the 20-byte SHA-1.
    """
    sha1_bytes, store = hash_content(data, obj_type=obj_type)
    sha1_hex = sha1_bytes.hex()
    
    dir_name = sha1_hex[:2]
    file_name = sha1_hex[2:]
    
    obj_dir = os.path.join(repo_path, ".gitty", "objects", dir_name)
    os.makedirs(obj_dir, exist_ok=True)
    
    obj_path = os.path.join(obj_dir, file_name)
    
    if not os.path.exists(obj_path):
        compressed_data = zlib.compress(store)
        with open(obj_path, "wb") as f:
            f.write(compressed_data)
            
    return sha1_bytes
