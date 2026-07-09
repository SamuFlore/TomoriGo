## TomoriGo

```c
/***
*       ___           ___           ___           ___           ___                       ___           ___     
*      /\  \         /\  \         /\__\         /\  \         /\  \          ___        /\  \         /\  \    
*      \:\  \       /::\  \       /::|  |       /::\  \       /::\  \        /\  \      /::\  \       /::\  \   
*       \:\  \     /:/\:\  \     /:|:|  |      /:/\:\  \     /:/\:\  \       \:\  \    /:/\:\  \     /:/\:\  \  
*       /::\  \   /:/  \:\  \   /:/|:|__|__   /:/  \:\  \   /::\~\:\  \      /::\__\  /:/  \:\  \   /:/  \:\  \ 
*      /:/\:\__\ /:/__/ \:\__\ /:/ |::::\__\ /:/__/ \:\__\ /:/\:\ \:\__\  __/:/\/__/ /:/__/_\:\__\ /:/__/ \:\__\
*     /:/  \/__/ \:\  \ /:/  / \/__/~~/:/  / \:\  \ /:/  / \/_|::\/:/  / /\/:/  /    \:\  /\ \/__/ \:\  \ /:/  /
*    /:/  /       \:\  /:/  /        /:/  /   \:\  /:/  /     |:|::/  /  \::/__/      \:\ \:\__\    \:\  /:/  / 
*    \/__/         \:\/:/  /        /:/  /     \:\/:/  /      |:|\/__/    \:\__\       \:\/:/  /     \:\/:/  /  
*                   \::/  /        /:/  /       \::/  /       |:|  |       \/__/        \::/  /       \::/  /   
*                    \/__/         \/__/         \/__/         \|__|                     \/__/         \/__/    
*/
```

TomoriGo，让 Tomori 帮你写 Commit message。  

## 安装

### 克隆仓库

```bash
git clone <repo_url>
cd tomorigo
```

### 安装
   
```bash
pip install -e .
```

### 配置 API Key

可选择配置全局 API Key 和项目 API Key，后者覆盖前者。

#### 全局配置

在 `~/` 下创建 `.gitcommit.toml`，并填写以下内容：

```toml
[provider]
name = "" # e.g. DeepSeek
api_key = "" # e.g. sk-***
model = "" # e.g. deepseek-v4-flash
endpoint = "" # e.g. https://api.deepseek.com

[format]
language = "" # e.g. zh
```

字段说明：

|字段|值|含义|
|---|--|---|
|name|str|AI Provider 名|
|api_key|str|API Key|
|model|str|模型名|
|endpoint|str|OpenAI 兼容的 API 地址（base URL）|
|language|zh 或 en|Commit message 语言，简体中文或英文|

#### 项目配置

TOML 文件同上，但放置在项目文件夹中。

## 使用
指令名：`tmrgo`  

获取帮助：`tmrgo -h`

```txt
usage: tmrgo [-h] [-p PROVIDER] [-m MODEL] [-f FORMAT] [-n] [--config]

TomoriGo，让 Tomori 帮你写 Commit Message！

options:
  -h, --help            show this help message and exit
  -p, --provider PROVIDER
                        AI provider 名称（覆盖配置文件）
  -m, --model MODEL     模型名称（覆盖配置文件）
  -f, --format FORMAT   自定义 message 格式模板
  -n, --dry-run         只生成和展示 message，不执行 git commit
  --config              显示当前生效的配置
```

### 可选项

1. `Yes, commit`：同意生成的 Commit message，并自动执行 `git commit`。
2. `Edit message`：编辑生成的 Commit message。
3. `Regenerate`：重新生成 Commit message。
4. `I prefer nonsense`：让 AI 生成无意义的 Commit message。
5. `Cancel`：退出工具。

用方向键选择可选项，回车以选择。

## 注意

1. 使用 `tmrgo` 前，需要先 `git add` 将文件提交到暂存区。
2. `.gitcommit.toml` 中包含 API Key，请勿泄露。