
import asyncio
import json
import logging
import time
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncTarget(Enum):
    """同步目标"""
    BACKEND = "backend"     # 后端业务服务
    NLP = "nlp"             # NLP算法模块


@dataclass
class SyncTask:
    """同步任务"""
    target: SyncTarget
    endpoint: str
    data: Dict
    retry_count: int = 0
    max_retry: int = 3


class DataSynchronizer:
    """
    数据同步器
    功能：异步批量同步位置数据、失败重试、优先级队列
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000", 
                 nlp_url: str = "http://localhost:8001"):
        self.backend_url = backend_url
        self.nlp_url = nlp_url
        
        # 同步队列
        self.queue: asyncio.Queue = asyncio.Queue()
        self.batch_size = 10      # 批量同步大小
        self.sync_interval = 1.0  # 同步间隔（秒）
        
        # 统计
        self.sync_stats = {
            'success': 0,
            'failed': 0,
            'retried': 0
        }
        
        # 回调函数（用于通知同步结果）
        self.callbacks: List[Callable] = []
        
        # 运行状态
        self.running = False
    
    async def start(self):
        """启动同步服务"""
        self.running = True
        logger.info("数据同步服务启动")
        
        # 启动批量同步任务
        asyncio.create_task(self._batch_sync_loop())
        
        # 启动监控任务
        asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """停止同步服务"""
        self.running = False
        # 等待队列处理完成
        await self.queue.join()
        logger.info("数据同步服务停止")
    
    def add_callback(self, callback: Callable):
        """添加同步完成回调"""
        self.callbacks.append(callback)
    
    async def sync_location(self, user_id: str, location: Dict, 
                           priority: bool = False):
        """
        同步位置数据
        priority: 是否优先同步（如匹配时）
        """
        # 准备数据
        data = {
            'user_id': user_id,
            'location': location,
            'timestamp': time.time(),
            'sync_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 创建任务
        backend_task = SyncTask(
            target=SyncTarget.BACKEND,
            endpoint=f"{self.backend_url}/api/location/update",
            data=data
        )
        
        nlp_task = SyncTask(
            target=SyncTarget.NLP,
            endpoint=f"{self.nlp_url}/api/location/receive",
            data=data
        )
        
        # 加入队列（优先任务放前面）
        if priority:
            # 使用优先级队列或直接处理
            await self._immediate_sync(backend_task)
            await self._immediate_sync(nlp_task)
        else:
            await self.queue.put(backend_task)
            await self.queue.put(nlp_task)
        
        logger.debug(f"位置同步任务已创建: {user_id}")
    
    async def sync_match_result(self, user_id: str, matches: List[Dict]):
        """
        同步匹配结果给后端
        """
        data = {
            'user_id': user_id,
            'matches': matches,
            'match_count': len(matches),
            'timestamp': time.time()
        }
        
        task = SyncTask(
            target=SyncTarget.BACKEND,
            endpoint=f"{self.backend_url}/api/match/result",
            data=data,
            max_retry=5  # 匹配结果更重要，多重试几次
        )
        
        await self.queue.put(task)
        logger.info(f"匹配结果同步任务已创建: {user_id}, 匹配数: {len(matches)}")
    
    async def _immediate_sync(self, task: SyncTask):
        """立即同步（用于高优先级任务）"""
        success = await self._send_request(task)
        if not success:
            # 失败则加入队列稍后重试
            await self.queue.put(task)
    
    async def _batch_sync_loop(self):
        """批量同步循环"""
        while self.running:
            batch = []
            
            # 收集一批任务
            try:
                while len(batch) < self.batch_size:
                    task = self.queue.get_nowait()
                    batch.append(task)
            except asyncio.QueueEmpty:
                pass
            
            if batch:
                await self._process_batch(batch)
            else:
                await asyncio.sleep(0.1)  # 队列为空时短暂休眠
    
    async def _process_batch(self, tasks: List[SyncTask]):
        """处理批量任务"""
        # 按目标分组
        backend_tasks = [t for t in tasks if t.target == SyncTarget.BACKEND]
        nlp_tasks = [t for t in tasks if t.target == SyncTarget.NLP]
        
        # 并发发送
        await asyncio.gather(
            self._send_batch(SyncTarget.BACKEND, backend_tasks),
            self._send_batch(SyncTarget.NLP, nlp_tasks),
            return_exceptions=True
        )
    
    async def _send_batch(self, target: SyncTarget, tasks: List[SyncTask]):
        """批量发送"""
        if not tasks:
            return
        
        # 合并数据
        batch_data = {
            'batch': True,
            'count': len(tasks),
            'items': [t.data for t in tasks],
            'timestamp': time.time()
        }
        
        endpoint = tasks[0].endpoint
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=batch_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        self.sync_stats['success'] += len(tasks)
                        logger.debug(f"批量同步成功: {target.value}, {len(tasks)}条")
                        
                        # 通知回调
                        for task in tasks:
                            self._notify_success(task)
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"批量同步失败: {target.value}, 错误: {e}")
            # 重新加入队列
            for task in tasks:
                await self._retry_task(task)
    
    async def _send_request(self, task: SyncTask) -> bool:
        """发送单个请求"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    task.endpoint,
                    json=task.data,
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return False
    
    async def _retry_task(self, task: SyncTask):
        """重试任务"""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retry:
            self.sync_stats['retried'] += 1
            # 指数退避
            delay = 2 ** task.retry_count
            await asyncio.sleep(delay)
            await self.queue.put(task)
            logger.warning(f"任务重试: {task.target.value}, 第{task.retry_count}次")
        else:
            self.sync_stats['failed'] += 1
            logger.error(f"任务失败（超过重试次数）: {task.target.value}")
            self._notify_failure(task)
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            await asyncio.sleep(60)  # 每分钟输出统计
            logger.info(f"同步统计 - 成功: {self.sync_stats['success']}, "
                       f"失败: {self.sync_stats['failed']}, "
                       f"重试: {self.sync_stats['retried']}, "
                       f"队列: {self.queue.qsize()}")
    
    def _notify_success(self, task: SyncTask):
        """通知成功"""
        for callback in self.callbacks:
            try:
                callback('success', task)
            except:
                pass
    
    def _notify_failure(self, task: SyncTask):
        """通知失败"""
        for callback in self.callbacks:
            try:
                callback('failure', task)
            except:
                pass
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'success': self.sync_stats['success'],
            'failed': self.sync_stats['failed'],
            'retried': self.sync_stats['retried'],
            'pending': self.queue.qsize()
        }


# ========== 模拟后端接口（测试用） ==========
class MockBackendServer:
    """模拟后端服务"""
    
    def __init__(self, port: int):
        self.port = port
        self.received_data = []
    
    async def handle(self, request):
        """处理请求"""
        try:
            data = await request.json()
            self.received_data.append({
                'timestamp': time.time(),
                'data': data
            })
            print(f"[后端:{self.port}] 收到数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
            return aiohttp.web.Response(text='OK')
        except Exception as e:
            print(f"[后端:{self.port}] 错误: {e}")
            return aiohttp.web.Response(status=500)
    
    async def start(self):
        """启动模拟服务器"""
        app = aiohttp.web.Application()
        app.router.add_post('/api/location/update', self.handle)
        app.router.add_post('/api/location/receive', self.handle)
        app.router.add_post('/api/match/result', self.handle)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"模拟后端启动于端口 {self.port}")


# ========== 测试代码 ==========
async def main():
    """测试数据同步"""
    # 启动模拟后端
    backend = MockBackendServer(8000)
    nlp = MockBackendServer(8001)
    await backend.start()
    await nlp.start()
    
    # 创建同步器
    syncer = DataSynchronizer(
        backend_url="http://localhost:8000",
        nlp_url="http://localhost:8001"
    )
    
    # 添加回调
    def on_sync(result, task):
        print(f"同步结果: {result}, 目标: {task.target.value}")
    
    syncer.add_callback(on_sync)
    
    # 启动同步服务
    await syncer.start()
    
    # 模拟位置更新
    print("\n=== 模拟位置同步 ===")
    for i in range(5):
        await syncer.sync_location(
            f"user_{i:03d}",
            {
                'latitude': 39.9 + i * 0.001,
                'longitude': 116.4 + i * 0.001,
                'accuracy': 10
            },
            priority=(i == 0)  # 第一个用户优先同步
        )
        await asyncio.sleep(0.1)
    
    # 模拟匹配结果同步
    print("\n=== 模拟匹配结果同步 ===")
    await syncer.sync_match_result("user_001", [
        {'user_id': 'user_002', 'distance': 50, 'score': 0.85},
        {'user_id': 'user_003', 'distance': 120, 'score': 0.72}
    ])
    
    # 运行一段时间
    await asyncio.sleep(5)
    
    # 输出统计
    print(f"\n同步统计: {syncer.get_stats()}")
    
    # 停止
    await syncer.stop()

if __name__ == "__main__":
    # 安装依赖: pip install aiohttp
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("测试结束")