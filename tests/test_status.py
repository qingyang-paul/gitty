import os
import time
from gitty.core.init import init
from gitty.core.add import add
from gitty.core.status import status
from gitty.core.commit import commit

def test_status_workflow(tmp_path, capsys):
    repo_path = str(tmp_path)
    
    # 1. Init
    init(repo_path, default_name="Test User", default_email="test@example.com")
    capsys.readouterr() # clear stdout
    
    # 2. Status empty initially (but init creates .gittyignore, so it's untracked)
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "Untracked files:" in out
    assert ".gittyignore" in out
    
    # Let's add and commit the .gittyignore to get a clean slate
    add(repo_path, ["."])
    commit(repo_path, "init", "A", "b@c.com", 1, "+0")
    capsys.readouterr() # clear

    # Clean slate status
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "nothing to commit" in out
    
    # 3. Create Untracked File
    file1 = tmp_path / "hello.txt"
    file1.write_text("hello 1")
    
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "Untracked files:" in out
    assert "hello.txt" in out
    
    # 4. Add file (Green New)
    add(repo_path, ["."])
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "Changes to be committed:" in out
    assert "new file:   hello.txt" in out
    
    # 5. Commit
    commit(repo_path, "msg", "Test", "test@t.com", int(time.time()), "+0800")
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "nothing to commit" in out
    
    # 6. Modify file (Red Modified)
    # The mtime in stat is cast to integer seconds in our implementation,
    # so we must literally wait 1 second to ensure the modified time changes!
    time.sleep(1.1)
    file1.write_text("hello 2")
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "Changes not staged for commit:" in out
    assert "modified:   hello.txt" in out
    
    # 7. Add Modified (Green Modified)
    add(repo_path, ["."])
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "Changes to be committed:" in out
    assert "modified:   hello.txt" in out
    
    # 8. Delete file (Red Deleted)
    file1.unlink()
    status(repo_path)
    out, _ = capsys.readouterr()
    assert "deleted:    hello.txt" in out
