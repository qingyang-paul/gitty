import os
import time
import pytest
from gitty.core.init import init
from gitty.core.add import add
from gitty.core.commit import commit

def test_initial_commit(tmp_path):
    repo_path = str(tmp_path)
    
    # 1. Init
    init(repo_path, default_name="Test User", default_email="test@example.com")
    
    # 2. Add some files
    file1 = tmp_path / "hello.txt"
    file1.write_text("hello world")
    
    dir1 = tmp_path / "src"
    dir1.mkdir()
    file2 = dir1 / "main.py"
    file2.write_text("print('test')")
    
    add(repo_path, ["."])
    
    # 3. Commit (explicit args as requested)
    author = "Test User"
    email = "test@example.com"
    timestamp = 1672531200 # Fixed time for testing
    tz = "+0800"
    msg = "Initial testing commit"
    
    commit(repo_path, msg, author, email, timestamp, tz)
    
    # Assert HEAD points to main and main has a hash
    head_file = tmp_path / ".gitty" / "HEAD"
    assert head_file.exists()
    assert head_file.read_text().strip() == "ref: refs/heads/main"
    
    main_ref = tmp_path / ".gitty" / "refs" / "heads" / "main"
    assert main_ref.exists()
    
    commit_hash = main_ref.read_text().strip()
    assert len(commit_hash) == 40
    
    # Assert commit object exists
    commit_obj_path = tmp_path / ".gitty" / "objects" / commit_hash[:2] / commit_hash[2:]
    assert commit_obj_path.exists()

def test_commit_missing_args(tmp_path):
    repo_path = str(tmp_path)
    init(repo_path, default_name="Test User", default_email="test@example.com")
    
    with pytest.raises(ValueError):
        commit(repo_path, "msg", "Test", "test@test.com", None, "+0800")
