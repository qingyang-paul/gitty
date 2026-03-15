# Gitty

用 Python 实现的精简版 Git 核心逻辑。

**作者**：Lynn | **年份**：2026

## 项目介绍

Gitty 是一个使用纯 Python 编写的 Git 克隆，不依赖第三方的 Git 封装库。项目从零实现了底层的二进制索引系统（Index）、对象压缩与寻址系统（Objects），并打通了从初始化、暂存到版本提交的完整工作流。

**核心特点**：

* **无隐式依赖**：系统信息（如时间、用户名）必须显式传入核心函数，消除因操作系统差异带来的隐式 Bug。
* **现代工程化**：使用 `uv` 进行虚拟环境与包管理，并基于 `pytest` 构建了完善的集成测试流。

## 核心机制

Gitty 实现了标准 Git 的三大核心区域：

1. **工作区 (Working Directory)**
受 `status` 命令监控的本地文件系统。自动跳过 `.gitty` 目录，并支持 `.gittyignore` 忽略列表。
2. **暂存区 (Index)**
使用 `struct` 构建的纯字节二进制文件（遵循 Git 规范：62 字节头部 + 动态补齐名称结构）。记录被追踪文件的元数据（`ctime`, `mtime`, `ino`, `size` 等）及 20 字节的 SHA-1 文件哈希。
3. **版本库 (Objects / HEAD)**
* **Blob (文件对象)**：将头信息 `[type] [size]\0` 与原数据拼接，经 `zlib` 压缩后，按 SHA-1 哈希值分散存储至 `.gitty/objects`。
* **Tree (树对象)**：将线性的 Index 记录转换为按目录层级嵌套的树状节点，还原特定时刻的工程目录快照。
* **Commit (提交对象)**：记录作者、时间、根 Tree 哈希与父节点 Commit 哈希，并将更新推至 `.gitty/HEAD` 指向的分支。



## 数据结构

### Index (暂存区)

| 字段类别 | 描述 | 长度 |
| --- | --- | --- |
| **元数据** | `ctime/mtime` (时间), `dev/ino` (索引), `mode` (权限), `uid/gid` (拥有者), `size` (大小) | 10 * 4 字节（时间可能占 8 字节） |
| **哈希映射** | 文件内容的二进制 SHA-1 签名，指向对应的 Blob | 20 字节 |
| **状态标识** | Flag（包含名字长度）及动态长度的 Padded UTF-8 编码文件名 | 2 字节 + 不定 |

### Tree 对象

* **结构**：`tree [总字节数]\0[mode] [name]\0[20字节二进制哈希]...`
* 树结构中可嵌套文件及子树（以 `40000` 目录特征区分），用于还原真实的文件层级。

### Commit 对象

* **结构**（文本键值对格式）：
```text
tree [40位根Tree哈希]
parent [40位父Commit哈希] (初始提交无此项)
author [姓名] <邮箱> [时间戳] [时区]
committer [姓名] <邮箱> [时间戳] [时区]

[Message]

```



## 快速开始

环境要求：Python >= 3.12，并安装 `uv` 包管理器。

1. **初始化仓库**
```bash
uv run gitty init

```


*生成 `.gitty` 目录、一个空的 `.gittyignore` 文件以及 `.gitty/config` 配置文件（如果在环境中没有找到用户名和邮箱，会在此步骤触发终端询问并记录以便后续直接读取）。*
2. **暂存文件**
```bash
uv run gitty add <file_or_directory>
# 或暂存当前目录下所有变更: uv run gitty add .

```


3. **提交版本**
```bash
uv run gitty commit -m "Initialize project structure"

```


*(注：为了避免隐式魔法带来的行为不透明，提交不带任何默认值。用户名、邮箱均从刚刚初始化的 `.gitty/config` 中准确读取。)*
4. **查看状态**
```bash
uv run gitty status

```


*可区分 Untracked（未追踪）、Staged（已暂存）以及 Modified（已修改）状态。若检测到文件修改时间变更但内容哈希一致，会自动更新 Index 中的元数据。*

