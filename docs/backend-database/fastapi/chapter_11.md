---
sidebar_position: 11
---

# FastAPI高级特性与扩展：解锁框架的全部潜力

> 当你已经掌握了FastAPI的基础和中级功能，接下来就是探索它的高级特性和扩展能力的时候了。这些特性将让你的应用从"能用"升级到"卓越"。

## 11.1 自定义路由类：超越标准路由的灵活性

### 为什么需要自定义路由类？

标准的路由器(APIRouter)已经很强大了，但有些场景需要更精细的控制。自定义路由类允许你：

1. 统一添加中间件到特定路由组
2. 自动注入依赖项
3. 实现路由级别的缓存策略
4. 自定义路由匹配逻辑

### 基础自定义路由实现

```python
# app/routing/custom_router.py
from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute
from typing import Callable, List, Optional, Dict, Any
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class LoggingRoute(APIRoute):
    """带有详细日志记录的自定义路由"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Any:
            # 请求前日志
            start_time = time.time()

            logger.info(
                f"开始处理请求: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None
                }
            )

            try:
                # 处理请求
                response = await original_route_handler(request)
                duration = time.time() - start_time

                # 请求后日志
                logger.info(
                    f"请求处理完成: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration": duration
                    }
                )

                # 添加性能头
                response.headers["X-Response-Time"] = f"{duration:.3f}s"

                return response

            except Exception as exc:
                duration = time.time() - start_time
                logger.error(
                    f"请求处理失败: {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "duration": duration,
                        "error": str(exc)
                    },
                    exc_info=True
                )
                raise

        return custom_route_handler

class CacheRoute(APIRoute):
    """支持缓存的自定义路由"""

    def __init__(self, *args, cache_ttl: int = 300, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_ttl = cache_ttl

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def cached_route_handler(request: Request) -> Any:
            from app.core.cache import RedisCache

            # 构建缓存键
            cache_key = self._build_cache_key(request)

            # 尝试从缓存获取
            cache = RedisCache()
            cached_response = await cache.get(cache_key)

            if cached_response is not None:
                # 返回缓存的响应
                from fastapi.responses import Response
                return Response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"],
                    media_type=cached_response["media_type"]
                )

            # 执行原始处理
            response = await original_route_handler(request)

            # 缓存响应
            if 200 <= response.status_code < 300:
                cache_data = {
                    "content": response.body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }
                await cache.set(cache_key, cache_data, self.cache_ttl)

            return response

        return cached_route_handler

    def _build_cache_key(self, request: Request) -> str:
        """构建缓存键"""
        import hashlib
        import json

        key_parts = [
            request.method,
            request.url.path,
            request.url.query,
            json.dumps(dict(request.headers), sort_keys=True)
        ]

        key_string = ":".join(str(p) for p in key_parts)
        return f"route_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
```

### 使用自定义路由类

```python
# app/api/advanced.py
from fastapi import APIRouter, FastAPI
from app.routing.custom_router import LoggingRoute, CacheRoute

# 创建支持日志的路由器
logging_router = APIRouter(route_class=LoggingRoute)

@logging_router.get("/logged")
async def logged_endpoint():
    """这个端点会自动记录详细的日志"""
    return {"message": "This request is logged"}

# 创建支持缓存的路由器
cache_router = APIRouter(route_class=CacheRoute)

@cache_router.get("/cached", cache_ttl=60)
async def cached_endpoint():
    """这个端点会被缓存60秒"""
    import time
    time.sleep(1)  # 模拟耗时操作
    return {"message": f"Cached response at {time.time()}"}

# 高级路由：需要认证的自定义路由
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class AuthenticatedRoute(APIRoute):
    """需要认证的自定义路由"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def authenticated_route_handler(
            request: Request,
            credentials: HTTPAuthorizationCredentials = Security(security)
        ) -> Any:
            # 验证token
            token = credentials.credentials

            # 这里应该是实际的token验证逻辑
            if token != "secret-token":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials"
                )

            # 将用户信息添加到请求状态
            request.state.user = {"id": 1, "username": "admin"}

            return await original_route_handler(request)

        return authenticated_route_handler

# 创建应用并注册路由
app = FastAPI()

# 动态路由注册
def register_routes_with_prefix(router: APIRouter, prefix: str):
    """为路由自动添加前缀的装饰器"""
    for route in router.routes:
        route.path = prefix + route.path
    return router

# 使用示例
v1_router = APIRouter()
v1_router.include_router(logging_router, prefix="/v1")
v1_router.include_router(cache_router, prefix="/v1")

app.include_router(v1_router)
```

## 11.2 响应编码与内容协商

### 内容协商基础

内容协商允许客户端和服务器就响应的格式进行协商。FastAPI原生支持通过`Accept`头进行内容协商。

```python
# app/api/content_negotiation.py
from fastapi import APIRouter, Request
from fastapi.responses import (
    Response,
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    ORJSONResponse,
    UJSONResponse
)
from typing import Optional, Dict, Any
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

router = APIRouter()

# 基础内容协商
@router.get("/negotiate")
async def negotiate_content(request: Request):
    """根据Accept头返回不同格式的响应"""
    accept_header = request.headers.get("Accept", "")

    data = {
        "message": "Hello World",
        "timestamp": "2024-01-15T10:30:00Z",
        "version": "1.0"
    }

    if "application/xml" in accept_header:
        # XML响应
        root = ET.Element("response")
        for key, value in data.items():
            child = ET.SubElement(root, key)
            child.text = str(value)

        xml_str = ET.tostring(root, encoding="unicode")
        return Response(
            content=xml_str,
            media_type="application/xml"
        )

    elif "text/plain" in accept_header:
        # 纯文本响应
        text_content = "\n".join(f"{k}: {v}" for k, v in data.items())
        return PlainTextResponse(content=text_content)

    elif "text/html" in accept_header:
        # HTML响应
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>API Response</title></head>
        <body>
            <h1>API Response</h1>
            <ul>
                <li>Message: {data['message']}</li>
                <li>Timestamp: {data['timestamp']}</li>
                <li>Version: {data['version']}</li>
            </ul>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    else:
        # 默认JSON响应
        return JSONResponse(content=data)

# 自定义响应编码器
class CustomEncoder(json.JSONEncoder):
    """自定义JSON编码器"""

    def default(self, obj):
        import datetime
        from decimal import Decimal
        from uuid import UUID

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__

        return super().default(obj)

# 使用自定义编码器的响应
@router.get("/custom-json")
async def custom_json_response():
    """使用自定义JSON编码器的响应"""
    import datetime
    from decimal import Decimal
    from uuid import uuid4

    data = {
        "id": uuid4(),
        "name": "Product",
        "price": Decimal("99.99"),
        "created_at": datetime.datetime.now(),
        "metadata": {
            "category": "electronics",
            "tags": ["new", "popular"]
        }
    }

    # 手动编码
    json_str = json.dumps(data, cls=CustomEncoder, indent=2)

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"X-Custom-Encoded": "true"}
    )
```

### 高级内容协商策略

```python
# app/negotiation/strategies.py
from typing import List, Tuple, Optional
from fastapi.responses import Response
import json

class ContentNegotiator:
    """智能内容协商器"""

    def __init__(self):
        self.supported_types = [
            ("application/json", 1.0),
            ("application/xml", 0.9),
            ("text/html", 0.8),
            ("text/plain", 0.7),
            ("application/yaml", 0.6)
        ]

    def negotiate(self, accept_header: str) -> str:
        """协商最佳内容类型"""
        if not accept_header:
            return "application/json"

        # 解析Accept头
        client_preferences = self._parse_accept_header(accept_header)

        # 找到最佳匹配
        best_match = None
        best_score = -1.0

        for client_type, client_q in client_preferences:
            for server_type, server_q in self.supported_types:
                if self._type_matches(client_type, server_type):
                    score = client_q * server_q
                    if score > best_score:
                        best_score = score
                        best_match = server_type

        return best_match or "application/json"

    def _parse_accept_header(self, header: str) -> List[Tuple[str, float]]:
        """解析Accept头"""
        result = []

        for part in header.split(","):
            part = part.strip()
            if ";" in part:
                type_part, q_part = part.split(";", 1)
                type_part = type_part.strip()

                # 提取q值
                q_value = 1.0
                for param in q_part.split(";"):
                    param = param.strip()
                    if param.startswith("q="):
                        try:
                            q_value = float(param[2:])
                        except ValueError:
                            q_value = 1.0

                result.append((type_part, q_value))
            else:
                result.append((part.strip(), 1.0))

        # 按q值降序排序
        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def _type_matches(self, client_type: str, server_type: str) -> bool:
        """检查类型是否匹配"""
        if client_type == "*/*" or server_type == "*/*":
            return True

        if "/" in client_type and "/" in server_type:
            c_main, c_sub = client_type.split("/")
            s_main, s_sub = server_type.split("/")

            if c_sub == "*" or s_sub == "*":
                return c_main == s_main
            else:
                return client_type == server_type

        return client_type == server_type

# 使用智能协商器的端点
@router.get("/smart-negotiate")
async def smart_negotiate(request: Request):
    """智能内容协商端点"""
    negotiator = ContentNegotiator()
    best_type = negotiator.negotiate(request.headers.get("Accept", ""))

    data = {
        "message": "Smart content negotiation",
        "negotiated_type": best_type,
        "available_types": [t for t, _ in negotiator.supported_types]
    }

    if best_type == "application/xml":
        # 转换为XML
        import xml.etree.ElementTree as ET
        root = ET.Element("response")
        for key, value in data.items():
            child = ET.SubElement(root, key)
            child.text = str(value)

        xml_str = ET.tostring(root, encoding="unicode")
        return Response(content=xml_str, media_type=best_type)

    elif best_type == "text/yaml":
        # 转换为YAML
        import yaml
        yaml_str = yaml.dump(data, default_flow_style=False)
        return Response(content=yaml_str, media_type=best_type)

    else:
        # 默认JSON
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json"
        )
```

### 流式响应和服务器推送

```python
# app/api/streaming.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator

router = APIRouter()

# SSE (Server-Sent Events) 示例
@router.get("/sse")
async def server_sent_events():
    """服务器推送事件流"""
    async def event_generator():
        for i in range(10):
            # 生成事件数据
            event_data = {
                "id": i,
                "event": "message",
                "data": f"Event {i} at {time.time()}",
                "retry": 3000  # 重连时间
            }

            # SSE格式: "event: {event}\ndata: {data}\n\n"
            yield f"id: {event_data['id']}\n"
            yield f"event: {event_data['event']}\n"
            yield f"data: {json.dumps(event_data['data'])}\n"
            yield f"retry: {event_data['retry']}\n\n"

            await asyncio.sleep(1)  # 每秒发送一个事件

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )

# 大文件流式下载
@router.get("/stream-large-file")
async def stream_large_file():
    """流式下载大文件"""
    async def file_chunk_generator():
        chunk_size = 1024 * 1024  # 1MB chunks

        # 模拟生成大文件
        for i in range(100):  # 100MB文件
            chunk = b"x" * chunk_size
            yield chunk
            await asyncio.sleep(0.01)  # 稍微延迟，模拟I/O

    headers = {
        "Content-Disposition": "attachment; filename=large_file.bin",
        "Content-Length": str(100 * 1024 * 1024)  # 100MB
    }

    return StreamingResponse(
        file_chunk_generator(),
        media_type="application/octet-stream",
        headers=headers
    )

# 实时日志流
@router.get("/logs/stream")
async def stream_logs():
    """实时日志流"""
    import sys
    import io

    class TeeStream(io.StringIO):
        """同时写入到多个流的类"""
        def __init__(self, *streams):
            super().__init__()
            self.streams = streams

        def write(self, text):
            super().write(text)
            for stream in self.streams:
                stream.write(text)
            return len(text)

    # 创建双向流
    async def log_stream():
        import logging

        # 设置日志流
        log_capture_string = io.StringIO()

        # 创建日志处理器
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # 添加到根日志器
        logging.getLogger().addHandler(ch)

        try:
            # 持续读取日志
            while True:
                content = log_capture_string.getvalue()
                if content:
                    yield content
                    log_capture_string.truncate(0)
                    log_capture_string.seek(0)
                await asyncio.sleep(0.1)
        finally:
            # 清理
            logging.getLogger().removeHandler(ch)

    return StreamingResponse(
        log_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff"
        }
    )
```

## 11.3 WebHooks实现：构建事件驱动的API

### WebHooks基础架构

```python
# app/webhooks/core.py
from typing import Dict, List, Optional, Callable, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import asyncio
import hashlib
import hmac
import json
from enum import Enum

class WebhookEvent(str, Enum):
    """Webhook事件类型"""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"

class WebhookSubscription(BaseModel):
    """Webhook订阅模型"""
    id: str
    url: HttpUrl
    events: List[WebhookEvent]
    secret: Optional[str] = None
    enabled: bool = True
    created_at: datetime
    updated_at: datetime
    retry_count: int = 0
    last_delivery: Optional[datetime] = None

class WebhookPayload(BaseModel):
    """Webhook负载"""
    event: WebhookEvent
    data: Dict[str, Any]
    timestamp: datetime
    webhook_id: str

class WebhookManager:
    """Webhook管理器"""

    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.queues: Dict[str, asyncio.Queue] = {}
        self.workers: Dict[str, asyncio.Task] = {}

    async def subscribe(self, subscription: WebhookSubscription):
        """添加订阅"""
        self.subscriptions[subscription.id] = subscription

        # 为每个订阅创建处理队列和工作线程
        if subscription.id not in self.queues:
            self.queues[subscription.id] = asyncio.Queue(maxsize=1000)
            self.workers[subscription.id] = asyncio.create_task(
                self._process_webhook_queue(subscription.id)
            )

    async def unsubscribe(self, webhook_id: str):
        """取消订阅"""
        if webhook_id in self.subscriptions:
            del self.subscriptions[webhook_id]

        # 停止工作线程
        if webhook_id in self.workers:
            self.workers[webhook_id].cancel()
            del self.workers[webhook_id]
            del self.queues[webhook_id]

    async def trigger(self, event: WebhookEvent, data: Dict[str, Any]):
        """触发Webhook事件"""
        payload = WebhookPayload(
            event=event,
            data=data,
            timestamp=datetime.now(),
            webhook_id=self._generate_webhook_id()
        )

        # 找到订阅了此事件的所有Webhook
        for subscription in self.subscriptions.values():
            if event in subscription.events and subscription.enabled:
                await self.queues[subscription.id].put(payload)

    async def _process_webhook_queue(self, webhook_id: str):
        """处理Webhook队列"""
        import httpx

        while True:
            try:
                payload = await self.queues[webhook_id].get()
                subscription = self.subscriptions[webhook_id]

                # 发送Webhook
                success = await self._deliver_webhook(
                    subscription,
                    payload
                )

                if success:
                    # 更新最后发送时间
                    subscription.last_delivery = datetime.now()
                    subscription.retry_count = 0
                else:
                    # 失败重试
                    await self._retry_delivery(subscription, payload)

                self.queues[webhook_id].task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Webhook processing error: {e}")
                await asyncio.sleep(1)

    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload
    ) -> bool:
        """发送Webhook"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 构建请求头
                headers = {
                    "User-Agent": "FastAPI-Webhooks/1.0",
                    "Content-Type": "application/json",
                    "X-Webhook-Event": payload.event,
                    "X-Webhook-ID": payload.webhook_id,
                    "X-Webhook-Timestamp": payload.timestamp.isoformat()
                }

                # 添加签名
                if subscription.secret:
                    signature = self._generate_signature(
                        subscription.secret,
                        payload.json()
                    )
                    headers["X-Webhook-Signature"] = signature

                # 发送请求
                response = await client.post(
                    str(subscription.url),
                    json=payload.dict(),
                    headers=headers
                )

                # 检查响应
                return 200 <= response.status_code < 300

        except Exception as e:
            print(f"Webhook delivery failed: {e}")
            return False

    def _generate_signature(self, secret: str, payload: str) -> str:
        """生成Webhook签名"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def _generate_webhook_id(self) -> str:
        """生成Webhook ID"""
        import uuid
        return str(uuid.uuid4())

    async def _retry_delivery(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload
    ):
        """重试发送"""
        max_retries = 3
        retry_delays = [1, 5, 15]  # 秒

        if subscription.retry_count < max_retries:
            subscription.retry_count += 1
            delay = retry_delays[subscription.retry_count - 1]

            await asyncio.sleep(delay)
            await self.queues[subscription.id].put(payload)
```

### WebHooks API端点

```python
# app/api/webhooks.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import uuid
from datetime import datetime

router = APIRouter()
webhook_manager = WebhookManager()

# Webhook注册端点
@router.post("/webhooks", response_model=WebhookSubscription)
async def create_webhook(
    url: str,
    events: List[WebhookEvent],
    secret: str = None
):
    """注册Webhook"""
    webhook_id = str(uuid.uuid4())

    subscription = WebhookSubscription(
        id=webhook_id,
        url=url,
        events=events,
        secret=secret,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        enabled=True
    )

    await webhook_manager.subscribe(subscription)

    return subscription

@router.get("/webhooks", response_model=List[WebhookSubscription])
async def list_webhooks():
    """列出所有Webhook"""
    return list(webhook_manager.subscriptions.values())

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """删除Webhook"""
    await webhook_manager.unsubscribe(webhook_id)
    return {"message": "Webhook deleted"}

# Webhook测试端点
@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str):
    """测试Webhook"""
    if webhook_id not in webhook_manager.subscriptions:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # 触发测试事件
    await webhook_manager.trigger(
        WebhookEvent.USER_CREATED,
        {
            "user_id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "test": True
        }
    )

    return {"message": "Test webhook triggered"}

# Webhook接收端点（用于接收其他服务的Webhook）
@router.post("/webhooks/receive")
async def receive_webhook(
    background_tasks: BackgroundTasks,
    x_webhook_signature: str = None,
    x_webhook_event: str = None
):
    """接收外部Webhook"""
    from fastapi import Request
    import json

    async def verify_and_process(request: Request):
        body = await request.body()

        # 验证签名（如果有）
        if x_webhook_signature:
            # 这里应该验证签名
            pass

        # 处理Webhook
        data = json.loads(body)

        # 根据事件类型处理
        event_type = x_webhook_event or data.get("event")

        if event_type == "payment.success":
            # 处理支付成功
            pass
        elif event_type == "payment.failed":
            # 处理支付失败
            pass

        return {"received": True}

    # 在后台处理Webhook
    background_tasks.add_task(verify_and_process)

    return {"message": "Webhook received"}
```

## 11.4 GraphQL集成：拥抱现代API查询语言

### 使用Strawberry集成GraphQL

```python
# app/graphql/schema.py
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

# GraphQL类型定义
@strawberry.type
class User:
    id: strawberry.ID
    username: str
    email: str
    created_at: datetime
    is_active: bool = True

    @strawberry.field
    def posts(self, limit: Optional[int] = 10) -> List["Post"]:
        """获取用户的文章"""
        # 这里应该是数据库查询
        from .resolvers import get_user_posts
        return get_user_posts(self.id, limit)

@strawberry.type
class Post:
    id: strawberry.ID
    title: str
    content: str
    author: User
    created_at: datetime
    updated_at: Optional[datetime] = None

    @strawberry.field
    def excerpt(self, length: Optional[int] = 100) -> str:
        """文章摘要"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + "..."

@strawberry.type
class Comment:
    id: strawberry.ID
    content: str
    author: User
    post: Post
    created_at: datetime

# 输入类型（用于Mutation）
@strawberry.input
class UserInput:
    username: str
    email: str
    password: str

@strawberry.input
class PostInput:
    title: str
    content: str
    author_id: strawberry.ID

# 查询类型
@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: strawberry.ID) -> Optional[User]:
        """获取单个用户"""
        from .resolvers import get_user_by_id
        return await get_user_by_id(id)

    @strawberry.field
    async def users(
        self,
        skip: Optional[int] = 0,
        limit: Optional[int] = 10,
        search: Optional[str] = None
    ) -> List[User]:
        """获取用户列表"""
        from .resolvers import get_users
        return await get_users(skip, limit, search)

    @strawberry.field
    async def post(self, id: strawberry.ID) -> Optional[Post]:
        """获取单个文章"""
        from .resolvers import get_post_by_id
        return await get_post_by_id(id)

    @strawberry.field
    async def posts(
        self,
        skip: Optional[int] = 0,
        limit: Optional[int] = 10,
        author_id: Optional[strawberry.ID] = None
    ) -> List[Post]:
        """获取文章列表"""
        from .resolvers import get_posts
        return await get_posts(skip, limit, author_id)

# 变更类型
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(self, user_input: UserInput) -> User:
        """创建用户"""
        from .resolvers import create_user
        return await create_user(user_input)

    @strawberry.mutation
    async def update_user(
        self,
        id: strawberry.ID,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """更新用户"""
        from .resolvers import update_user
        return await update_user(id, username, email)

    @strawberry.mutation
    async def create_post(self, post_input: PostInput) -> Post:
        """创建文章"""
        from .resolvers import create_post
        return await create_post(post_input)

    @strawberry.mutation
    async def delete_post(self, id: strawberry.ID) -> bool:
        """删除文章"""
        from .resolvers import delete_post
        return await delete_post(id)

# 创建Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# 创建GraphQL路由
graphql_router = GraphQLRouter(
    schema,
    graphiql=True,  # 启用GraphiQL界面
    allow_queries_via_get=True  # 允许通过GET请求查询
)

# 解析器实现
# app/graphql/resolvers.py
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid

# 模拟数据库
users_db = {}
posts_db = {}

async def get_user_by_id(id: str) -> Optional[User]:
    """根据ID获取用户"""
    await asyncio.sleep(0.1)  # 模拟数据库延迟
    return users_db.get(id)

async def get_users(skip: int = 0, limit: int = 10, search: str = None) -> List[User]:
    """获取用户列表"""
    await asyncio.sleep(0.1)

    users = list(users_db.values())

    if search:
        users = [u for u in users if search.lower() in u.username.lower()]

    return users[skip:skip+limit]

async def create_user(user_input: UserInput) -> User:
    """创建用户"""
    user_id = str(uuid.uuid4())

    user = User(
        id=user_id,
        username=user_input.username,
        email=user_input.email,
        created_at=datetime.now()
    )

    users_db[user_id] = user
    return user

async def get_post_by_id(id: str) -> Optional[Post]:
    """根据ID获取文章"""
    await asyncio.sleep(0.1)
    return posts_db.get(id)

async def get_posts(skip: int = 0, limit: int = 10, author_id: str = None) -> List[Post]:
    """获取文章列表"""
    await asyncio.sleep(0.1)

    posts = list(posts_db.values())

    if author_id:
        posts = [p for p in posts if p.author.id == author_id]

    return posts[skip:skip+limit]

async def create_post(post_input: PostInput) -> Post:
    """创建文章"""
    post_id = str(uuid.uuid4())
    author = users_db.get(post_input.author_id)

    if not author:
        raise ValueError("Author not found")

    post = Post(
        id=post_id,
        title=post_input.title,
        content=post_input.content,
        author=author,
        created_at=datetime.now()
    )

    posts_db[post_id] = post
    return post
```

### 高级GraphQL特性

```python
# app/graphql/advanced.py
import strawberry
from typing import Optional, Annotated
from strawberry.types import Info
from strawberry.permission import BasePermission
from strawberry.extensions import Extension

# GraphQL权限控制
class IsAuthenticated(BasePermission):
    """认证检查权限"""
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        # 从context中获取用户
        user = info.context.get("user")
        return user is not None

class IsAdmin(BasePermission):
    """管理员权限"""
    message = "User is not admin"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        user = info.context.get("user")
        return user and user.get("role") == "admin"

@strawberry.type
class AdminQuery:
    """管理员查询"""

    @strawberry.field(permission_classes=[IsAdmin])
    async def all_users(self) -> List[User]:
        """获取所有用户（仅管理员）"""
        from .resolvers import get_all_users
        return await get_all_users()

    @strawberry.field(permission_classes=[IsAdmin])
    async def system_stats(self) -> Dict[str, Any]:
        """系统统计（仅管理员）"""
        return {
            "total_users": len(users_db),
            "total_posts": len(posts_db),
            "active_users": sum(1 for u in users_db.values() if u.is_active)
        }

# GraphQL扩展（用于监控、日志等）
class QueryLoggingExtension(Extension):
    """查询日志扩展"""

    def on_operation(self):
        # 操作开始时
        start_time = time.time()
        self.execution_context.context["start_time"] = start_time

        yield

        # 操作结束时
        end_time = time.time()
        duration = end_time - start_time

        # 记录日志
        query = self.execution_context.query
        variables = self.execution_context.variables

        logger.info(
            f"GraphQL query executed in {duration:.3f}s",
            extra={
                "query": query,
                "variables": variables,
                "duration": duration
            }
        )

class RateLimitExtension(Extension):
    """速率限制扩展"""

    def __init__(self, max_operations: int = 100, window_seconds: int = 60):
        self.max_operations = max_operations
        self.window_seconds = window_seconds
        self.operation_counts = {}

    def on_operation(self):
        client_ip = self.execution_context.context.get("client_ip")

        if not client_ip:
            yield
            return

        # 检查速率限制
        current_time = time.time()
        window_start = current_time - self.window_seconds

        # 清理过期的记录
        self.operation_counts[client_ip] = [
            ts for ts in self.operation_counts.get(client_ip, [])
            if ts > window_start
        ]

        # 检查是否超过限制
        if len(self.operation_counts[client_ip]) >= self.max_operations:
            raise Exception("Rate limit exceeded")

        # 记录操作
        self.operation_counts[client_ip].append(current_time)

        yield

# 联合类型和接口
@strawberry.interface
class SearchResult:
    """搜索结果接口"""
    id: strawberry.ID
    title: str
    relevance: float

@strawberry.type
class UserSearchResult(SearchResult):
    """用户搜索结果"""
    username: str
    email: str

@strawberry.type
class PostSearchResult(SearchResult):
    """文章搜索结果"""
    excerpt: str
    author_username: str

@strawberry.type
class SearchQuery:
    """搜索查询"""

    @strawberry.field
    async def search(
        self,
        query: str,
        limit: Optional[int] = 10
    ) -> List[SearchResult]:
        """搜索"""
        results = []

        # 搜索用户
        for user in users_db.values():
            if query.lower() in user.username.lower():
                results.append(
                    UserSearchResult(
                        id=user.id,
                        title=user.username,
                        relevance=0.8,
                        username=user.username,
                        email=user.email
                    )
                )

        # 搜索文章
        for post in posts_db.values():
            if query.lower() in post.title.lower() or query.lower() in post.content.lower():
                results.append(
                    PostSearchResult(
                        id=post.id,
                        title=post.title,
                        relevance=0.6,
                        excerpt=post.content[:100],
                        author_username=post.author.username
                    )
                )

        # 按相关性排序
        results.sort(key=lambda x: x.relevance, reverse=True)

        return results[:limit]

# 创建包含高级特性的Schema
advanced_schema = strawberry.Schema(
    query=strawberry.type(
        "AdvancedQuery",
        (Query, AdminQuery, SearchQuery)
    ),
    mutation=Mutation,
    extensions=[
        QueryLoggingExtension,
        lambda: RateLimitExtension(max_operations=60)
    ],
    types=[User, Post, Comment, UserSearchResult, PostSearchResult]
)
```

## 11.5 自定义OpenAPI文档：打造专属API文档体验

### 自定义文档配置

```python
# app/docs/customization.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from typing import Dict, Any, Optional

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """自定义OpenAPI文档"""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My Awesome API",
        version="2.0.0",
        description="""
        # My Awesome API

        ## 特性

        - 🔥 高性能
        - 🔐 安全认证
        - 📊 实时监控
        - 🔄 Webhook支持

        ## 快速开始

        1. 获取API密钥
        2. 使用Bearer认证
        3. 开始调用API

        [查看完整文档](https://docs.example.com)
        """,
        routes=app.routes,
    )

    # 自定义服务器
    openapi_schema["servers"] = [
        {
            "url": "https://api.example.com",
            "description": "生产环境"
        },
        {
            "url": "https://staging-api.example.com",
            "description": "测试环境"
        },
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        }
    ]

    # 添加安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "输入你的JWT令牌，格式: Bearer <token>"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API密钥认证"
        }
    }

    # 添加标签元数据
    openapi_schema["tags"] = [
        {
            "name": "users",
            "description": "用户管理操作",
            "externalDocs": {
                "description": "了解更多",
                "url": "https://docs.example.com/users"
            }
        },
        {
            "name": "products",
            "description": "商品管理操作",
            "externalDocs": {
                "description": "商品API文档",
                "url": "https://docs.example.com/products"
            }
        },
        {
            "name": "orders",
            "description": "订单管理操作"
        }
    ]

    # 添加扩展
    openapi_schema["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        "backgroundColor": "#FFFFFF",
        "altText": "API Logo"
    }

    openapi_schema["x-tagGroups"] = [
        {
            "name": "核心API",
            "tags": ["users", "products", "orders"]
        },
        {
            "name": "扩展API",
            "tags": ["webhooks", "graphql", "files"]
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 自定义Swagger UI
def get_custom_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> HTMLResponse:
    """自定义Swagger UI界面"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}

        *,
        *:before,
        *:after {{
            box-sizing: inherit;
        }}

        body {{
            margin: 0;
            background: #fafafa;
        }}

        .topbar {{
            background-color: #1e1e1e;
            padding: 10px 0;
            text-align: center;
            color: white;
            font-size: 1.2em;
        }}

        .topbar a {{
            color: #61dafb;
            text-decoration: none;
        }}

        .version {{
            background-color: #61dafb;
            color: #1e1e1e;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
    </style>
    </head>

    <body>
    <div class="topbar">
        <span>{title} <span class="version">v2.0</span></span>
        <span style="margin-left: 20px;">
            <a href="/docs">Swagger UI</a> |
            <a href="/redoc">ReDoc</a> |
            <a href="/graphql">GraphQL</a>
        </span>
    </div>
    <div id="swagger-ui"></div>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
        dom_id: '#swagger-ui',
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true,
        oauth2RedirectUrl: '{oauth2_redirect_url or ''}',
        initOAuth: {json.dumps(init_oauth) if init_oauth else '{}'},
        onComplete: function() {{
            // 自定义完成回调
            console.log("Swagger UI loaded");

            // 添加自定义CSS
            const style = document.createElement('style');
            style.innerHTML = `
                .opblock-tag {{
                    font-size: 16px;
                    margin: 0 0 10px;
                    font-family: sans-serif;
                }}
                .opblock-tag-section {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
            `;
            document.head.appendChild(style);

            // 添加自定义按钮
            const tryOutBtn = document.createElement('button');
            tryOutBtn.innerHTML = '🚀 快速测试';
            tryOutBtn.className = 'btn try-out__btn';
            tryOutBtn.style.marginLeft = '10px';
            tryOutBtn.onclick = function() {{
                // 自动填充示例数据
                const inputs = document.querySelectorAll('input[type="text"]');
                inputs.forEach(input => {{
                    if (input.placeholder.includes('ID')) {{
                        input.value = '123';
                    }} else if (input.placeholder.includes('name')) {{
                        input.value = '示例名称';
                    }} else if (input.placeholder.includes('email')) {{
                        input.value = 'example@test.com';
                    }}
                }});
            }};

            // 找到合适的位置添加按钮
            const executeBtn = document.querySelector('.execute');
            if (executeBtn) {{
                executeBtn.parentNode.insertBefore(tryOutBtn, executeBtn);
            }}
        }}
    }});

    // 自定义主题
    ui.initOAuth({{
        clientId: 'your-client-id',
        clientSecret: 'your-client-secret-if-required',
        realm: 'your-realms',
        appName: 'Swagger UI',
        scopeSeparator: ' ',
        additionalQueryStringParams: {{}},
        useBasicAuthenticationWithAccessCodeGrant: false,
        usePkceWithAuthorizationCodeGrant: false,
    }});
    </script>
    </body>
    </html>
    """

    return HTMLResponse(html)
```

### API文档生成与导出

```python
# app/docs/generator.py
from typing import Dict, Any, List
import json
import yaml
from datetime import datetime
from pathlib import Path

class APIDocumentationGenerator:
    """API文档生成器"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.schema = custom_openapi(app)

    def generate_markdown(self) -> str:
        """生成Markdown格式的文档"""
        md_lines = []

        md_lines.append(f"# {self.schema['info']['title']}")
        md_lines.append(f"\n{self.schema['info']['description']}\n")

        # 服务器信息
        md_lines.append("## 服务器")
        for server in self.schema.get("servers", []):
            md_lines.append(f"- **{server['description']}**: `{server['url']}`")

        # 安全认证
        md_lines.append("\n## 认证")
        if "securitySchemes" in self.schema.get("components", {}):
            for name, scheme in self.schema["components"]["securitySchemes"].items():
                md_lines.append(f"\n### {name}")
                md_lines.append(f"- 类型: {scheme['type']}")
                md_lines.append(f"- 描述: {scheme.get('description', '')}")

        # 标签分组
        md_lines.append("\n## API端点")

        # 按标签分组
        endpoints_by_tag = {}
        for path, methods in self.schema["paths"].items():
            for method, details in methods.items():
                tags = details.get("tags", ["default"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []

                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "details": details
                    })

        # 生成每个标签的文档
        for tag, endpoints in endpoints_by_tag.items():
            md_lines.append(f"\n### {tag}")

            for endpoint in endpoints:
                details = endpoint["details"]

                md_lines.append(f"\n#### {endpoint['method']} {endpoint['path']}")
                md_lines.append(f"\n{details.get('summary', '')}")

                if "description" in details:
                    md_lines.append(f"\n{details['description']}")

                # 参数
                if "parameters" in details:
                    md_lines.append("\n**参数:**")
                    md_lines.append("| 名称 | 位置 | 类型 | 必填 | 描述 |")
                    md_lines.append("|------|------|------|------|------|")

                    for param in details["parameters"]:
                        md_lines.append(
                            f"| {param['name']} | {param['in']} | "
                            f"{param.get('schema', {}).get('type', 'string')} | "
                            f"{'是' if param.get('required', False) else '否'} | "
                            f"{param.get('description', '')} |"
                        )

                # 请求体
                if "requestBody" in details:
                    md_lines.append("\n**请求体:**")
                    content = details["requestBody"]["content"]

                    for media_type, schema_info in content.items():
                        md_lines.append(f"\n*{media_type}*:")

                        schema = schema_info.get("schema", {})
                        if "$ref" in schema:
                            ref_name = schema["$ref"].split("/")[-1]
                            md_lines.append(f"  使用: `{ref_name}`")

                # 响应
                if "responses" in details:
                    md_lines.append("\n**响应:**")

                    for status_code, response_info in details["responses"].items():
                        description = response_info.get("description", "")
                        md_lines.append(f"\n- **{status_code}**: {description}")

        return "\n".join(md_lines)

    def generate_postman_collection(self) -> Dict[str, Any]:
        """生成Postman集合"""
        collection = {
            "info": {
                "name": self.schema["info"]["title"],
                "description": self.schema["info"]["description"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }

        # 按标签分组
        endpoints_by_tag = {}
        for path, methods in self.schema["paths"].items():
            for method, details in methods.items():
                tags = details.get("tags", ["default"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []

                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "details": details
                    })

        # 创建文件夹结构
        for tag, endpoints in endpoints_by_tag.items():
            folder = {
                "name": tag,
                "item": []
            }

            for endpoint in endpoints:
                item = {
                    "name": endpoint["details"].get("summary", endpoint["path"]),
                    "request": {
                        "method": endpoint["method"],
                        "url": {
                            "raw": f"{{{{base_url}}}}{endpoint['path']}",
                            "host": ["{{base_url}}"],
                            "path": endpoint["path"].strip("/").split("/")
                        }
                    }
                }

                # 添加认证
                security = endpoint["details"].get("security", [])
                if security:
                    item["request"]["auth"] = {
                        "type": "bearer",
                        "bearer": [{"key": "token", "value": "{{api_token}}", "type": "string"}]
                    }

                # 添加参数
                if "parameters" in endpoint["details"]:
                    query_params = []
                    path_vars = []

                    for param in endpoint["details"]["parameters"]:
                        if param["in"] == "query":
                            query_params.append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", ""),
                                "disabled": not param.get("required", False)
                            })
                        elif param["in"] == "path":
                            path_vars.append({
                                "key": param["name"],
                                "value": "example",
                                "description": param.get("description", "")
                            })

                    if query_params:
                        item["request"]["url"]["query"] = query_params

                    # 更新路径变量
                    if path_vars:
                        for path_var in path_vars:
                            item["request"]["url"]["path"] = [
                                segment.replace(
                                    f"{{{path_var['key']}}}",
                                    path_var["value"]
                                )
                                for segment in item["request"]["url"]["path"]
                            ]

                folder["item"].append(item)

            collection["item"].append(folder)

        return collection

    def export_all_formats(self, output_dir: str = "./docs"):
        """导出所有格式的文档"""
        Path(output_dir).mkdir(exist_ok=True)

        # 导出OpenAPI JSON
        json_path = Path(output_dir) / "openapi.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.schema, f, indent=2, ensure_ascii=False)

        # 导出OpenAPI YAML
        yaml_path = Path(output_dir) / "openapi.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self.schema, f, allow_unicode=True)

        # 导出Markdown
        md_path = Path(output_dir) / "api_documentation.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.generate_markdown())

        # 导出Postman集合
        postman_path = Path(output_dir) / "postman_collection.json"
        with open(postman_path, "w", encoding="utf-8") as f:
            json.dump(self.generate_postman_collection(), f, indent=2)

        # 导出HTML
        html_path = Path(output_dir) / "api_documentation.html"
        self._generate_html_documentation(html_path)

        return {
            "json": str(json_path),
            "yaml": str(yaml_path),
            "markdown": str(md_path),
            "postman": str(postman_path),
            "html": str(html_path)
        }

    def _generate_html_documentation(self, output_path: Path):
        """生成HTML文档"""
        import markdown
        from markdown.extensions.toc import TocExtension

        md_content = self.generate_markdown()

        # 转换为HTML
        html = markdown.markdown(
            md_content,
            extensions=[
                TocExtension(toc_depth="2-4"),
                'fenced_code',
                'tables',
                'codehilite'
            ],
            output_format='html5'
        )

        # 添加HTML模板
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.schema['info']['title']} - API文档</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
            <script>hljs.highlightAll();</script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: #f6f8fa;
                }}
                .markdown-body {{
                    box-sizing: border-box;
                    min-width: 200px;
                    max-width: 980px;
                    margin: 0 auto;
                    padding: 45px;
                }}
                @media (max-width: 767px) {{
                    .markdown-body {{
                        padding: 15px;
                    }}
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    margin-bottom: 2rem;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5rem;
                }}
                .header .version {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 0.2rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.9rem;
                    margin-left: 1rem;
                }}
                .download-links {{
                    background: white;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .download-links a {{
                    margin-right: 1rem;
                    text-decoration: none;
                    color: #0366d6;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.schema['info']['title']} <span class="version">v{self.schema['info']['version']}</span></h1>
                <p>{self.schema['info'].get('description', '').split('\\n')[0]}</p>
            </div>

            <div class="markdown-body">
                <div class="download-links">
                    <strong>下载格式:</strong>
                    <a href="openapi.json">OpenAPI JSON</a>
                    <a href="openapi.yaml">OpenAPI YAML</a>
                    <a href="api_documentation.md">Markdown</a>
                    <a href="postman_collection.json">Postman</a>
                </div>
                {html}
                <hr>
                <footer style="text-align: center; color: #666; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee;">
                    <p>文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>使用 <a href="https://fastapi.tiangolo.com" target="_blank">FastAPI</a> 生成</p>
                </footer>
            </div>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)
```

## 11.6 插件系统开发：构建可扩展的应用架构

### 插件系统架构

```python
# app/plugins/core.py
from typing import Dict, List, Any, Optional, Callable, Type
from abc import ABC, abstractmethod
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import importlib
import inspect
from pathlib import Path

class PluginConfig(BaseModel):
    """插件配置"""
    name: str
    version: str
    enabled: bool = True
    dependencies: List[str] = []
    settings: Dict[str, Any] = {}

class PluginManifest(BaseModel):
    """插件清单"""
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    dependencies: List[str] = []
    routers: List[str] = []
    middleware: List[str] = []
    events: Dict[str, List[str]] = {}
    commands: Dict[str, str] = {}

class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, app: FastAPI, config: PluginConfig):
        self.app = app
        self.config = config
        self.router = APIRouter(prefix=f"/plugin/{config.name}")

    @abstractmethod
    def setup(self):
        """插件安装"""
        pass

    @abstractmethod
    def teardown(self):
        """插件卸载"""
        pass

    def register_routes(self):
        """注册路由"""
        self.app.include_router(self.router)

    def register_middleware(self, middleware_class: Type):
        """注册中间件"""
        self.app.add_middleware(middleware_class)

    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self.app.add_event_handler(event_type, handler)

class PluginManager:
    """插件管理器"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.plugins: Dict[str, BasePlugin] = {}
        self.loaded_plugins: Dict[str, Any] = {}

        # 插件目录
        self.plugin_dir = Path("plugins")
        self.plugin_dir.mkdir(exist_ok=True)

    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        try:
            # 导入插件模块
            module_name = f"plugins.{plugin_name}"
            plugin_module = importlib.import_module(module_name)

            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(plugin_module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BasePlugin) and
                    obj != BasePlugin):
                    plugin_class = obj
                    break

            if not plugin_class:
                print(f"未找到插件类: {plugin_name}")
                return False

            # 读取配置
            config_path = self.plugin_dir / plugin_name / "config.json"
            if config_path.exists():
                import json
                config_data = json.loads(config_path.read_text())
                config = PluginConfig(**config_data)
            else:
                config = PluginConfig(name=plugin_name, version="1.0.0")

            # 创建插件实例
            plugin_instance = plugin_class(self.app, config)

            # 检查依赖
            for dep in config.dependencies:
                if dep not in self.plugins:
                    print(f"插件 {plugin_name} 缺少依赖: {dep}")
                    return False

            # 安装插件
            plugin_instance.setup()
            plugin_instance.register_routes()

            self.plugins[plugin_name] = plugin_instance
            self.loaded_plugins[plugin_name] = plugin_module

            print(f"插件加载成功: {plugin_name}")
            return True

        except Exception as e:
            print(f"插件加载失败 {plugin_name}: {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_name]
            plugin.teardown()

            del self.plugins[plugin_name]
            del self.loaded_plugins[plugin_name]

            print(f"插件卸载成功: {plugin_name}")
            return True

        except Exception as e:
            print(f"插件卸载失败 {plugin_name}: {e}")
            return False

    def load_all_plugins(self):
        """加载所有插件"""
        for plugin_dir in self.plugin_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                self.load_plugin(plugin_dir.name)

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        result = []
        for name, plugin in self.plugins.items():
            result.append({
                "name": name,
                "version": plugin.config.version,
                "enabled": plugin.config.enabled,
                "dependencies": plugin.config.dependencies
            })
        return result
```

### 插件示例：认证插件

```python
# plugins/auth_plugin/__init__.py
from app.plugins.core import BasePlugin, PluginConfig
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt

class AuthPlugin(BasePlugin):
    """认证插件"""

    def __init__(self, app, config: PluginConfig):
        super().__init__(app, config)
        self.secret_key = config.settings.get("secret_key", "default-secret-key")
        self.security = HTTPBearer()

    def setup(self):
        """安装插件"""
        print(f"安装认证插件: {self.config.name}")

        # 注册路由
        @self.router.post("/login")
        async def login(username: str, password: str):
            # 验证用户
            user = self.authenticate_user(username, password)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # 生成token
            token = self.generate_token(user)
            return {"access_token": token, "token_type": "bearer"}

        @self.router.get("/me")
        async def get_current_user(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            token = credentials.credentials
            user = self.verify_token(token)

            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")

            return user

    def teardown(self):
        """卸载插件"""
        print(f"卸载认证插件: {self.config.name}")

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """验证用户"""
        # 这里应该是数据库查询
        users = {
            "admin": {"id": 1, "username": "admin", "role": "admin"},
            "user": {"id": 2, "username": "user", "role": "user"}
        }

        if username in users and password == "password":
            return users[username]

        return None

    def generate_token(self, user: dict) -> str:
        """生成JWT令牌"""
        import time

        payload = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600  # 1小时过期
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {
                "id": payload["sub"],
                "username": payload["username"],
                "role": payload["role"]
            }
        except jwt.PyJWTError:
            return None

# 插件配置
# plugins/auth_plugin/config.json
{
    "name": "auth",
    "version": "1.0.0",
    "description": "用户认证插件",
    "enabled": true,
    "dependencies": [],
    "settings": {
        "secret_key": "your-secret-key-here",
        "token_expire_hours": 24
    }
}
```

### 插件示例：监控插件

```python
# plugins/monitoring_plugin/__init__.py
from app.plugins.core import BasePlugin, PluginConfig
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import psutil
import os

class MonitoringPlugin(BasePlugin):
    """监控插件"""

    def __init__(self, app, config: PluginConfig):
        super().__init__(app, config)
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0
        }

    def setup(self):
        """安装插件"""
        print(f"安装监控插件: {self.config.name}")

        # 添加监控中间件
        @self.app.middleware("http")
        async def monitor_middleware(request: Request, call_next):
            start_time = time.time()

            try:
                response = await call_next(request)
                duration = time.time() - start_time

                # 更新指标
                self.metrics["request_count"] += 1
                self.metrics["total_response_time"] += duration

                # 添加性能头
                response.headers["X-Response-Time"] = f"{duration:.3f}s"

                return response

            except Exception as e:
                self.metrics["error_count"] += 1
                raise

        # 注册监控端点
        @self.router.get("/metrics")
        async def get_metrics():
            """获取监控指标"""
            process = psutil.Process(os.getpid())

            return {
                "requests": {
                    "total": self.metrics["request_count"],
                    "errors": self.metrics["error_count"],
                    "avg_response_time": (
                        self.metrics["total_response_time"] /
                        max(self.metrics["request_count"], 1)
                    )
                },
                "system": {
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent(),
                    "memory_rss": process.memory_info().rss,
                    "threads": process.num_threads()
                },
                "uptime": time.time() - process.create_time()
            }

        @self.router.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "plugin": self.config.name
            }

    def teardown(self):
        """卸载插件"""
        print(f"卸载监控插件: {self.config.name}")
```

## 11.7 源码阅读与贡献指南

### FastAPI源码结构解析

```
fastapi/
├── __init__.py              # 主要导出
├── applications.py          # FastAPI类定义
├── routing.py              # 路由相关
├── datastructures.py       # 数据结构
├── params.py              # 参数处理
├── dependencies.py        # 依赖注入系统
├── security.py           # 安全相关
├── background.py         # 后台任务
├── responses.py          # 响应类
├── staticfiles.py        # 静态文件
├── templating.py         # 模板渲染
├── middleware            # 中间件目录
│   ├── __init__.py
│   ├── cors.py
│   └── gzip.py
├── exceptions.py         # 异常处理
├── openapi               # OpenAPI相关
│   ├── __init__.py
│   ├── docs.py
│   ├── models.py
│   └── utils.py
└── types.py             # 类型定义
```

### 关键源码阅读

#### 1. FastAPI类核心实现

```python
# fastapi/applications.py (简化版)
class FastAPI(Starlette):
    """FastAPI主类"""

    def __init__(
        self,
        debug: bool = False,
        routes: List[BaseRoute] = None,
        **kwargs
    ):
        super().__init__(debug=debug, routes=routes, **kwargs)

        # 路由相关的属性
        self.router: routing.APIRouter = routing.APIRouter()
        self.openapi_version = "3.0.2"
        self.openapi_schema: Optional[Dict[str, Any]] = None

        # 添加默认文档路由
        self.setup_docs()

    def setup_docs(self):
        """设置文档路由"""
        if self.openapi_url:
            self.add_route(
                self.openapi_url,
                self.openapi,
                include_in_schema=False,
            )

        if self.docs_url:
            self.add_route(
                self.docs_url,
                self.swagger_ui_html,
                include_in_schema=False,
            )

    def get(self, path: str, **kwargs):
        """GET装饰器"""
        return self.router.get(path, **kwargs)

    def post(self, path: str, **kwargs):
        """POST装饰器"""
        return self.router.post(path, **kwargs)

    # ... 其他HTTP方法装饰器

    def include_router(self, router: routing.APIRouter, **kwargs):
        """包含路由器"""
        self.router.include_router(router, **kwargs)
```

#### 2. 依赖注入系统解析

```python
# fastapi/dependencies/utils.py (简化版)
async def solve_dependencies(
    *,
    dependant: Dependant,
    body: Optional[Dict[str, Any]] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    response: Optional[Response] = None,
    dependency_overrides: Optional[Dict[Callable, Callable]] = None,
) -> Tuple[Dict[str, Any], List[ErrorWrapper]]:
    """解决依赖关系"""
    values: Dict[str, Any] = {}
    errors: List[ErrorWrapper] = []

    # 遍历依赖树
    for sub_dependant in dependant.dependencies:
        sub_values, sub_errors = await solve_dependencies(
            dependant=sub_dependant,
            body=body,
            background_tasks=background_tasks,
            response=response,
            dependency_overrides=dependency_overrides,
        )

        if sub_errors:
            errors.extend(sub_errors)
            continue

        # 调用依赖函数
        call = sub_dependant.call
        if dependency_overrides and call in dependency_overrides:
            call = dependency_overrides[call]

        try:
            # 执行依赖函数
            solved = await call(**sub_values)
            values.update({sub_dependant.name: solved})
        except Exception as e:
            errors.append(ErrorWrapper(e, loc=("dependency",)))

    return values, errors
```

### 贡献指南

#### 如何开始贡献

1. **Fork仓库**：

   ```bash
   # 访问 https://github.com/tiangolo/fastapi
   # 点击右上角的 "Fork" 按钮
   ```

2. **克隆你的分支**：

   ```bash
   git clone https://github.com/YOUR_USERNAME/fastapi.git
   cd fastapi
   ```

3. **设置开发环境**：

   ```bash
   # 创建虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows

   # 安装开发依赖
   pip install -e .[dev]
   pip install pytest pytest-cov
   ```

4. **运行测试**：

   ```bash
   # 运行所有测试
   pytest

   # 运行特定测试文件
   pytest tests/test_main.py

   # 带覆盖率报告
   pytest --cov=fastapi tests/
   ```

#### 贡献流程

1. **创建新分支**：

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码并测试**：

   ```python
   # 确保添加测试用例
   # tests/test_your_feature.py

   def test_your_feature():
       from fastapi import FastAPI
       from fastapi.testclient import TestClient

       app = FastAPI()

       @app.get("/")
       async def root():
           return {"message": "Hello World"}

       client = TestClient(app)
       response = client.get("/")
       assert response.status_code == 200
   ```

3. **代码风格检查**：

   ```bash
   # 格式化代码
   black fastapi/ tests/

   # 排序imports
   isort fastapi/ tests/

   # 类型检查
   mypy fastapi/
   ```

4. **提交更改**：

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**：
   - 访问 https://github.com/tiangolo/fastapi
   - 点击 "New Pull Request"
   - 选择你的分支
   - 填写PR描述

#### 贡献规范

1. **提交消息格式**：

   ```
   type(scope): description

   body

   footer
   ```

   类型说明：
   - `feat`: 新功能
   - `fix`: bug修复
   - `docs`: 文档更新
   - `style`: 代码风格调整
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建/工具更新

2. **测试要求**：
   - 新功能必须包含测试
   - 修复bug需要添加回归测试
   - 测试覆盖率不应降低

3. **文档要求**：
   - 新功能需要更新文档
   - 公共API需要类型提示和docstring
   - 复杂功能需要示例代码

#### 学习资源

1. **官方文档**：
   - [贡献指南](https://fastapi.tiangolo.com/contributing/)
   - [开发设置](https://fastapi.tiangolo.com/contributing/#development-installation)
   - [项目结构](https://fastapi.tiangolo.com/contributing/#project-structure)

2. **社区资源**：
   - [GitHub Discussions](https://github.com/tiangolo/fastapi/discussions)
   - [Discord社区](https://discord.gg/VQjSZae)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/fastapi)

3. **相关项目**：
   - [Starlette](https://github.com/encode/starlette): FastAPI的基础
   - [Pydantic](https://github.com/pydantic/pydantic): 数据验证库
   - [Uvicorn](https://github.com/encode/uvicorn): ASGI服务器

### 实战练习：实现一个简单的特性

**任务**：为FastAPI添加一个`@retry`装饰器，当API调用失败时自动重试。

```python
# 实现示例
def retry(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
            return None
        return wrapper
    return decorator

# 使用示例
@app.get("/unstable")
@retry(max_retries=3, delay=0.5)
async def unstable_endpoint():
    import random
    if random.random() < 0.5:
        raise HTTPException(status_code=500, detail="随机失败")
    return {"status": "ok"}
```

---

## 总结

通过本章的学习，你已经深入了解了FastAPI的高级特性和扩展能力。这些高级特性包括：

1. **自定义路由类**：实现更灵活的路由控制
2. **响应编码与内容协商**：支持多种响应格式
3. **WebHooks实现**：构建事件驱动的API系统
4. **GraphQL集成**：提供灵活的查询能力
5. **自定义OpenAPI文档**：打造专业的API文档
6. **插件系统开发**：构建可扩展的应用架构
7. **源码阅读与贡献**：深入理解框架并参与贡献

这些高级特性让FastAPI不仅是一个Web框架，更是一个完整的API开发平台。掌握这些技能后，你将能够：

- 构建更强大、更灵活的API系统
- 提供更好的开发者体验
- 实现更复杂的业务需求
- 为开源社区做出贡献

**记住**：技术只是工具，真正的价值在于用这些工具解决实际问题。不断实践，不断优化，你将成为FastAPI专家。
