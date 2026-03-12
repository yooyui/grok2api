# Changelog

## [Unreleased]

### Performance

- **RequestStats debounce 写入** — 用 5 秒 debounce flush 替代每次请求写磁盘，高并发下减少 90%+ 磁盘 I/O (`request_stats.py`)
- **TokenPool.select 单次遍历** — normal/heavy bucket 均改为单次遍历完成筛选+最大值查找，消除 2-3 次重复扫描 (`token/pool.py`)
- **共享请求头模板** — 新建 `headers.py`，将 5 个服务文件中重复的 HTTP headers 构建统一收敛，净减 ~70 行重复代码 (`chat.py`, `usage.py`, `assets.py`, `media.py`)

### Bug Fixes

- **信号量竞态修复** — `assets.py`、`usage.py`、`media.py` 三处信号量配置变更时不再替换对象，改为动态调整内部计数器，避免正在等待旧信号量的协程失去并发控制
- **流式 processor 资源泄漏** — `chat.py` 的 `_wrapped_stream` finally 块增加 `processor.aclose()` 调用，确保消费者提前断开时 DownloadService session 被清理
- **DownloadService session 泄漏** — `BaseProcessor` 新增 async context manager 支持（`__aenter__`/`__aexit__`），调用方可用 `async with` 确保资源释放 (`processor.py`)
- **Windows 锁退化** — `LocalStorage` 用 per-name `asyncio.Lock` 替代单一全局锁，config 和 token 保存不再互相阻塞 (`storage.py`)
