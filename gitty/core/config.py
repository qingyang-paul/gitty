import os
import configparser

def get_user_info(repo_path: str):
    """
    Reads the user name and email from .gitty/config.
    Raises ValueError if missing, enforcing explicit requirements.
    """
    config_path = os.path.join(repo_path, ".gitty", "config")
    if not os.path.exists(config_path):
        raise ValueError("Gitty config file not found. Have you initialized?")
        
    config = configparser.ConfigParser()
    config.read(config_path)
    
    try:
        name = config.get("user", "name")
        email = config.get("user", "email")
    except (configparser.NoSectionError, configparser.NoOptionError):
        raise ValueError("User name or email not configured in .gitty/config")
        
    if not name or not email:
        raise ValueError("User name or email is empty in .gitty/config")
        
    return name, email
