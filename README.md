# Gitty

A simplified Git core logic implemented in Python.

**Author**: Lynn | **Year**: 2026

## Project Overview

Gitty is a Git clone written in pure Python, without relying on any third-party Git wrapper libraries. The project implements from scratch a low-level binary index system (Index), an object compression and addressing system (Objects), and connects the complete workflow from initialization and staging to version committing.

**Key Features**:

* **No implicit dependencies**: System information (such as timestamps and usernames) must be explicitly passed into core functions, eliminating implicit bugs caused by OS differences.
* **Modern engineering**: Uses `uv` for virtual environment and package management, with a comprehensive integration test suite built on `pytest`.

## Core Mechanisms

Gitty implements the three core areas of standard Git:

1. **Working Directory**
The local filesystem monitored by the `status` command. Automatically skips the `.gitty` directory and supports a `.gittyignore` ignore list.
2. **Index (Staging Area)**
A pure-byte binary file built with `struct` (following the Git spec: 62-byte fixed header + dynamically padded name structure). Records metadata (`ctime`, `mtime`, `ino`, `size`, etc.) and the 20-byte SHA-1 file hash for tracked files.
3. **Objects / HEAD**
* **Blob (file object)**: Concatenates the header `[type] [size]\0` with the raw data, compresses it with `zlib`, and stores it distributed under `.gitty/objects` by SHA-1 hash.
* **Tree (tree object)**: Converts the linear Index records into tree nodes nested by directory hierarchy, restoring a snapshot of the project directory at a specific point in time.
* **Commit (commit object)**: Records the author, timestamp, root Tree hash, and parent Commit hash, then pushes the update to the branch pointed to by `.gitty/HEAD`.



## Data Structures

### Index (Staging Area)

| Field Category | Description | Length |
| --- | --- | --- |
| **Metadata** | `ctime/mtime` (timestamps), `dev/ino` (identifiers), `mode` (permissions), `uid/gid` (owner), `size` (size) | 10 * 4 bytes (timestamps may occupy 8 bytes) |
| **Hash mapping** | Binary SHA-1 signature of the file content, pointing to the corresponding Blob | 20 bytes |
| **Status flags** | Flag (contains name length) and dynamically-sized padded UTF-8 encoded filename | 2 bytes + variable |

### Tree Object

* **Structure**: `tree [total byte count]\0[mode] [name]\0[20-byte binary hash]...`
* Trees can nest files and subtrees (distinguished by the `40000` directory mode), used to restore the real file hierarchy.

### Commit Object

* **Structure** (text key-value format):
```text
tree [40-char root Tree hash]
parent [40-char parent Commit hash] (absent for the initial commit)
author [name] <email> [timestamp] [timezone]
committer [name] <email> [timestamp] [timezone]

[Message]

```



## Quick Start

Requirements: Python >= 3.12 with the `uv` package manager installed.

1. **Initialize a repository**
```bash
uv run gitty init

```


*Generates the `.gitty` directory, an empty `.gittyignore` file, and a `.gitty/config` configuration file. If no username or email is found in the environment, a terminal prompt will be triggered at this step to record them for future reads.*

2. **Stage files**
```bash
uv run gitty add <file_or_directory>
# Or stage all changes in the current directory: uv run gitty add .

```


3. **Commit a version**
```bash
uv run gitty commit -m "Initialize project structure"

```


*(Note: To avoid the opacity caused by implicit magic, commits carry no default values. Username and email are read accurately from the `.gitty/config` that was just initialized.)*

4. **Check status**
```bash
uv run gitty status

```


*Distinguishes Untracked, Staged, and Modified states. If a file's modification time has changed but the content hash is identical, the metadata in the Index is automatically updated.*

