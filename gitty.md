# gitty

Goal: A self-implemented git

Author: Lynn

Date: 2026.3.15

##  Design

### Folder Structure

**config**

Configures username, email, and remote repository address (written when `gitty remote add` is called)

**objects/**

Stores the packed content

**HEAD**

Stores the current head: refs/head/main

**/refs/heads/main**

Stores the hash of the most recent commit

**index**

Stores the mapping between files and their content (created on the first `add`)



### gitty init

Creates the relevant files under the `.gitty` folder

**Create root directory:** Create the `.gitty/` folder.

**Create core subdirectories:**

- `.gitty/objects/`
- `.gitty/refs/heads/`
- `.gitty/refs/tags/`

**Create `HEAD` file:** Write default content `ref: refs/heads/main\n`.

**Create `config` file:** Write the INI-format text with basic configuration.

Create .gittyignore

### gitty status

Untracked:

1. Scan filenames on disk
2. Remove those recorded in the index
3. Remove those recorded in .gittyignore
4. The rest are Untracked

Modified (red - working tree modification, not yet staged):

1. For all files recorded in the index
2. Compare metadata (mtime, file size, inode)
3. If metadata is identical, filter out
4. If metadata differs, compute hash (if hash is unchanged, update metadata to latest)
5. If hash also differs, mark as modified

Modified (green - changes staged in the index):

1. Find the most recent commit
2. Expand the tree structure
3. Compare against the current index
4. Based on hash differences, determine new files, deleted files, and modified files



### gitty add

Prepend a header `[blob, size]` to the file content, compress and pack it into objects, and register it in the index

### gitty commit

Expand all contents of the index; each directory becomes a separate tree object, packed into objects/

Create a commit object and place it in objects/

Update the pointer: Open the `.gitty/HEAD` file and follow the reference to find the current branch file (e.g., `.gitty/refs/heads/main`).

​	**If this is the first commit:** The `main` file does not yet exist; you need to **create it** and write the 40-character hash into it.

​	**If it is not the first commit:** You need to **overwrite** this file with the new hash value.

### gitty checkout

Check whether there are any uncommitted modifications in the current working tree

Expand the tree object under the commit object, compare against the current working directory, and prepare to restore

### gitty merge

Branch A, Branch B, their latest common ancestor C

Compare [A, C] and [B, C]:

If only A modified something, keep A's version; if only B modified it, keep B's version; if both modified it, hand it off for manual review.



## Data Structures

**index**

| **Field Category** | **Field Name** | **Length (bytes)** | **Description**                                                  |
| ------------------ | -------------- | ------------------ | ---------------------------------------------------------------- |
| **Metadata**       | `ctime`        | 8                  | Last metadata change time of the file (seconds + nanoseconds)   |
|                    | `mtime`        | 8                  | Last content modification time of the file (seconds + nanoseconds) |
|                    | `dev`          | 4                  | Device ID of the disk where the file resides                    |
|                    | `ino`          | 4                  | **inode number**                                                 |
|                    | `mode`         | 4                  | File permissions (e.g., 100644, 100755)                         |
|                    | `uid`          | 4                  | User ID                                                          |
|                    | `gid`          | 4                  | Group ID                                                         |
|                    | `size`         | 4                  | Raw size of the file on disk                                    |
| **Git Data**       | **SHA-1**      | 20                 | **Hash of the file content (points to the Blob object)**        |
|                    | `flags`        | 2                  | Contains the filename length and **Stage slot (0-3)**           |
| **Path**           | `name`         | variable           | Full path name of the file (e.g., `src/main.py`)                |



**Blob**

- **Header**: `blob [byte count]\0`

- **Content**: The raw binary data of the file.

- **Example**: A file with content `hi`.

  > `blob 2\0hi`



**Tree Object**

- **Header**: `tree [total byte count]\0`

- **Content**: A list of multiple entries; each entry has the format: `[mode] [name]\0[20-byte binary hash]`

- **Note**: The hash inside a tree is not a 40-character hex string, but a **20-byte raw binary**.

- **Example**:

  > `tree 36\0100644 test.txt\0[20-byte binary SHA-1]`



**Commit Object**

- **Header**: `commit [total byte count]\0`

- **Content**: A text block in key-value format.

- **Structure**:

  ```Plaintext
  tree [40-char root Tree hash]
  parent [40-char parent Commit hash] (optional, absent for the root commit)
  author [name] <email> [timestamp] [timezone]
  committer [name] <email> [timestamp] [timezone]

  [Commit message]
  ```
