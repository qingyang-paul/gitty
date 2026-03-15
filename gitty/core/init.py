import os
import logging

def init(repo_path: str, default_name: str = None, default_email: str = None):
    """
    Initialize a new git repository at repo_path.
    If default_name or default_email are provided (usually in tests), they bypass prompts.
    """
    git_dir = os.path.join(repo_path, ".gitty")

    if os.path.exists(git_dir):
        logging.info(f"Reinitialized existing Gitty repository in {git_dir}")
        return

    # Determine user info
    name = default_name or os.environ.get("GITTY_AUTHOR_NAME")
    email = default_email or os.environ.get("GITTY_AUTHOR_EMAIL")
    
    if not name:
        name = input("Please enter your name for Gitty config: ").strip()
    if not email:
        email = input("Please enter your email for Gitty config: ").strip()
        
    if not name or not email:
        raise ValueError("Cannot initialize Gitty without user name and email.")

    # 创建核心子目录
    dirs_to_create = [
        git_dir,
        os.path.join(git_dir, "objects"),
        os.path.join(git_dir, "refs", "heads"),
        os.path.join(git_dir, "refs", "tags"),
    ]

    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        logging.debug(f"Created directory: {d}")

    # 创建 HEAD 文件
    head_path = os.path.join(git_dir, "HEAD")
    with open(head_path, "w", encoding="utf-8") as f:
        f.write("ref: refs/heads/main\n")
    logging.debug(f"Created file: {head_path}")

    # 创建 config 文件
    config_path = os.path.join(git_dir, "config")
    config_content = f"""[core]
\trepositoryformatversion = 0
\tfilemode = true
\tbare = false
\tlogallrefupdates = true

[user]
\tname = {name}
\temail = {email}
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    logging.debug(f"Created file: {config_path}")

    # 创建 .gittyignore 文件
    ignore_path = os.path.join(repo_path, ".gittyignore")
    if not os.path.exists(ignore_path):
        with open(ignore_path, "w", encoding="utf-8") as f:
            pass
        logging.debug(f"Created file: {ignore_path}")

    print(f"Initialized empty Gitty repository in {git_dir}")
