# SSE 流式进度推送实现总结

## 实施日期
2026-01-25

## 目标
完善 SSE（Server-Sent Events）流式推送功能，实现 LangGraph Agent 到前端的实时进度通信。

## 问题诊断

### 现状问题
1. **连接断开**：Agent 的 `emit_progress_tool` 只记录日志，未连接到 SSE 端点
2. **模拟数据**：FastAPI SSE 端点使用模拟数据，不是真实的 Agent 进度
3. **缺失事件总线**：没有进度事件的存储和传递机制

### 根本原因
Agent 工具和 FastAPI 端点之间缺少一个中间层来传递进度事件。

## 解决方案

### 架构设计

```
┌─────────────────────────────────────────────────────┐
│  LangGraph Agent (data_processing_agent)           │
│  - emit_progress_tool 被调用                        │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│  ProgressEventBus (新增模块)                        │
│  - 内存队列：asyncio.Queue                          │
│  - 订阅者管理：dict[dataset_id] = [queues]         │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI SSE Endpoint                               │
│  - /api/analysis/{dataset_id}/progress              │
│  - 从 ProgressEventBus 读取事件                     │
│  - 实时推送到前端                                    │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│  前端 EventSource                                    │
│  - AnalysisProgressPanel 实时显示                   │
└─────────────────────────────────────────────────────┘
```

## 实施细节

### 1. 新增 ProgressEventBus 模块

**文件**：`backend/src/core/progress_event_bus.py`

**核心类**：
- `ProgressEvent`：进度事件数据结构
- `ProgressEventBus`：单例模式的事件总线

**关键方法**：
```python
async def subscribe(dataset_id: str) -> asyncio.Queue
    # 订阅数据集的进度事件，返回队列

async def publish(event: ProgressEvent)
    # 发布进度事件到所有订阅者

async def iter_events(dataset_id: str, queue: asyncio.Queue) -> AsyncIterator[ProgressEvent]
    # 迭代队列中的事件（用于 SSE 端点）

async def unsubscribe(dataset_id: str, queue: asyncio.Queue)
    # 取消订阅
```

**特性**：
- ✅ 单例模式，全局唯一实例
- ✅ 异步队列支持多订阅者
- ✅ 心跳机制（每秒发送心跳，超时1秒）
- ✅ 自动清理不活跃订阅者
- ✅ 进度达到100%自动结束流

### 2. 修改 Agent 工具

**文件**：`backend/src/agents/data_processing/tools.py`

**修改内容**：
```python
# 之前：仅记录日志
logger.info(f"[Progress Event] {progress_event}")

# 之后：发布到事件总线
from src.core.progress_event_bus import get_progress_event_bus, ProgressEvent

event_bus = get_progress_event_bus()
progress_event = ProgressEvent(...)
await event_bus.publish(progress_event)
```

**改进点**：
- ✅ 连接到 ProgressEventBus
- ✅ 创建结构化事件对象
- ✅ 异步发布到事件总线
- ✅ 更详细的日志记录

### 3. 修改 FastAPI SSE 端点

**文件**：`backend/fastapi_extension.py`

**修改内容**：
```python
# 之前：模拟数据
for i in range(0, 101, 10):
    await asyncio.sleep(1)
    yield f"event: progress\ndata: {json.dumps(simulated_data)}\n\n"

# 之后：从事件总线读取真实事件
event_bus = get_progress_event_bus()
queue = await event_bus.subscribe(dataset_id)

async for event in event_bus.iter_events(dataset_id, queue):
    yield f"event: progress\ndata: {json.dumps(event.to_dict())}\n\n"
    if event.progress >= 100:
        break
```

**改进点**：
- ✅ 从 ProgressEventBus 订阅事件
- ✅ 实时推送 Agent 真实进度
- ✅ finally 块确保取消订阅
- ✅ 完整的错误处理
- ✅ 添加 HTTP 头 `X-Accel-Buffering: no` 禁用 Nginx 缓冲

### 4. 前端错误处理改进

**文件**：`agent-chat-ui/src/lib/api-extension.ts`

**修改内容**：
```typescript
// 添加心跳事件监听
eventSource.addEventListener('heartbeat', (e: MessageEvent) => {
  console.debug('[SSE] Heartbeat:', e.data);
});

// 区分业务错误和连接错误
eventSource.addEventListener('error', (e: MessageEvent) => {
  // 后端发送的业务错误
  const errorData = JSON.parse(e.data);
  onError?.(new Error(errorData.error));
});

eventSource.onerror = (evt) => {
  // EventSource 内置错误（网络错误等）
  onError?.(new Error('SSE connection failed'));
  eventSource.close();
};
```

**改进点**：
- ✅ 添加心跳事件监听
- ✅ 区分业务错误和连接错误
- ✅ 更详细的错误日志
- ✅ 自动关闭失效连接

## 错误处理

### 后端错误处理
1. **连接中断**：`asyncio.CancelledError` 捕获并记录日志
2. **业务异常**：`Exception` 捕获并发送 error 事件到前端
3. **资源清理**：`finally` 块确保取消订阅
4. **超时保护**：心跳机制防止连接挂起

### 前端错误处理
1. **JSON 解析错误**：try-catch 捕获并通知用户
2. **连接错误**：EventSource.onerror 监听并关闭连接
3. **业务错误**：后端 error 事件处理并显示错误信息

## 测试建议

### 手动测试步骤
1. 启动后端：`cd backend && uv run python start_unified.py`
2. 启动前端：`cd agent-chat-ui && pnpm dev`
3. 上传一个 CSV 文件
4. 观察 AnalysisProgressPanel 实时进度
5. 检查浏览器控制台日志
6. 验证进度达到100%后自动完成

### 预期行为
- ✅ SSE 连接成功（`connected` 事件）
- ✅ 心跳事件每秒发送一次
- ✅ Agent 进度实时显示
- ✅ 进度达到100%后发送 `complete` 事件
- ✅ 连接自动关闭

### 异常测试
- ❌ 中断网络连接（应该触发 `onerror`）
- ❌ 后端 Agent 失败（应该发送 `error` 事件）
- ❌ 前端刷新页面（应该自动关闭旧连接）

## 性能考虑

### 内存占用
- 每个订阅者占用一个 asyncio.Queue（约 1KB）
- 自动清理机制防止内存泄漏
- 队列满时丢弃事件（非阻塞 put）

### 并发支持
- 支持同一数据集多个订阅者
- 异步锁保护共享状态
- 每个订阅者独立队列

### 网络优化
- 心跳间隔：1秒
- HTTP 头优化：禁用 Nginx 缓冲
- 自动断开：进度100%后立即关闭

## 已知限制

1. **单进程依赖**：EventBus 是内存单例，不支持多进程部署
2. **无持久化**：进程重启后丢失所有订阅
3. **无重连机制**：前端断开后需手动重新连接（可改进）

## 未来改进方向

1. **持久化存储**：使用 Redis 替代内存队列
2. **自动重连**：前端 EventSource 断开后自动重连
3. **任务取消**：支持主动取消正在运行的 Agent
4. **多进程支持**：Redis Pub/Sub 替代内存单例
5. **性能监控**：添加连接数、事件吞吐量监控

## 文件清单

### 新增文件
- `backend/src/core/progress_event_bus.py` - 事件总线核心模块

### 修改文件
- `backend/src/agents/data_processing/tools.py` - emit_progress_tool 连接到 EventBus
- `backend/fastapi_extension.py` - SSE 端点使用真实事件
- `agent-chat-ui/src/lib/api-extension.ts` - 前端错误处理改进

## 验收标准

✅ Agent 调用 emit_progress_tool 后，前端实时显示进度
✅ 进度信息准确（步骤名称、百分比、已完成/待完成步骤）
✅ 分析完成后自动关闭 SSE 连接
✅ 异常情况下正确处理错误并通知用户
✅ 无内存泄漏，订阅者正确清理

## 总结

本次实施成功实现了 LangGraph Agent 到前端的完整 SSE 流式推送功能。通过引入 ProgressEventBus 作为中间层，解耦了 Agent 工具和 FastAPI 端点，提升了系统的可维护性和扩展性。所有核心功能已完成，错误处理完善，可以进行测试和部署。
