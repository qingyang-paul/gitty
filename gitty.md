# gitty

目标：自主实现的git

作者：Lynn

日期： 2026.3.15

##  设计

### 文件夹内容

**config**

配置用户名、邮箱、远程仓库地址（gitty remote add 才写入）

**objects/**

存放打包好的内容

**HEAD**

存放当前的head：refs/head/main

**/refs/heads/main**

存放最近一次提交的hash

**index**

存放文件和内容的对应关系(第一次add的时候才会创建)



### gitty init

新建.gitty文件夹下的相关文件

**创建根目录：** 创建 `.gitty/` 文件夹。

**创建核心子目录：**

- `.gitty/objects/`
- `.gitty/refs/heads/`
- `.gitty/refs/tags/`

**创建 `HEAD` 文件：** 写入默认内容 `ref: refs/heads/main\n`。

**创建 `config` 文件：** 写入基础配置的 INI 格式文本。

创建.gittyignore

### gitty status

Untracked: 

1. 扫描磁盘的文件名
2. 去除index里记录的
3. 取出.gittyignore里记录的
4. 剩下的都是Untrack

Modified（红色-工作区修改，未提交stage）:

1. 针对所有index里记录的文件
2. 比较元数据（修改时间，文件大小，inode）
3. 如果元数据没区别，过滤掉
4. 如果元数据有修改，计算哈希，（如果哈希没变，那就更新元数据到最新）
5. 如果哈希也有区别，标记为modified（)

Modified（绿色 - stage暂存的变化）：

1. 找到最新一次commit
2. 展开tree里的结构
3. 对比当前index
4. 根据哈希的变化，决定新增文件、删除文件、和修改文件



### gitty add

把文件内容加上header【blob, 大小】，压缩打包，放进objects, 在index做登记

### gitty commit

把index的所有内容展开，所有文件夹分别作为一个tree对象，打包后丢进objects/

创建一个commit对象，放进objects/

更新指针：打开 `.gitty/HEAD` 文件，顺藤摸瓜找到当前的分支文件（比如 `.gitty/refs/heads/main`）。

​	**如果是第一次提交：** 这个 `main` 文件还不存在，你需要**创建它**，并把这 40 位哈希值写进去。

​	**如果不是第一次：** 你需要**覆盖**这个文件，写入新的哈希值。

### gitty checkout

检查当前是否有未提交的修改代码

用commit对象下的tree对象展开，对比当前工作区，准备恢复

### gitty merge

分支A，分支B，最晚的共同节点C

对比【A，C】，【B，C】，

如果只有A修改，保留A；如果只有B修改，保留B；如果都修改了，交给人工审核。



## 数据结构

**index**

| **字段类别** | **字段名** | **长度 (字节)** | **描述**                                 |
| ------------ | ---------- | --------------- | ---------------------------------------- |
| **元数据**   | `ctime`    | 8               | 文件元数据最后修改时间（秒+纳秒）        |
|              | `mtime`    | 8               | 文件内容最后修改时间（秒+纳秒）          |
|              | `dev`      | 4               | 文件所在磁盘的设备 ID                    |
|              | `ino`      | 4               | **inode 编号**                           |
|              | `mode`     | 4               | 文件权限（如 100644, 100755）            |
|              | `uid`      | 4               | 用户 ID                                  |
|              | `gid`      | 4               | 组 ID                                    |
|              | `size`     | 4               | 文件在磁盘上的原始大小                   |
| **Git 数据** | **SHA-1**  | 20              | **该文件内容的哈希值（指向 Blob 对象）** |
|              | `flags`    | 2               | 包含文件名长度和 **Stage 槽位 (0-3)**    |
| **路径**     | `name`     | 不定            | 文件的完整路径名（如 `src/main.py`）     |



**Blob**

- **Header**: `blob [字节数]\0`

- **Content**: 文件的原始二进制数据。

- **例子**: 内容为 `hi` 的文件。

  > `blob 2\0hi`



**Tree 对象**

- **Header**: `tree [总字节数]\0`

- **Content**: 由多个 Entry 组成的列表，每个 Entry 的格式为： `[mode] [name]\0[20字节二进制哈希]`

- **注意**: Tree 里的哈希不是 40 位十六进制字符串，而是 **20 字节的原始二进制**。

- **例子**:

  > `tree 36\0100644 test.txt\0[20字节二进制SHA-1]`



**Commit 对象**

- **Header**: `commit [总字节数]\0`

- **Content**: 一个键值对格式的文本块。

- **结构**:

  ```Plaintext
  tree [40位根Tree哈希]
  parent [40位父Commit哈希] (可选，根提交没有)
  author [姓名] <邮箱> [时间戳] [时区]
  committer [姓名] <邮箱> [时间戳] [时区]
  
  [提交信息(Message)]
  ```