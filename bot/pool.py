"""Connection Pool — مدیریت اتصال SQLite."""
# NOTE: This module is currently unused (not imported anywhere). Kept for potential future use.
import asyncio
import logging
import aiosqlite

log = logging.getLogger("kaysan.pool")


class ConnectionPool:
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=max_connections)
        self._size = 0

    async def acquire(self) -> aiosqlite.Connection:
        try:
            return self._pool.get_nowait()
        except asyncio.QueueEmpty:
            if self._size < self.max_connections:
                self._size += 1
                return await aiosqlite.connect(self.db_path)
            return await self._pool.get()

    async def release(self, conn: aiosqlite.Connection):
        try:
            self._pool.put_nowait(conn)
        except asyncio.QueueFull:
            await conn.close()
            self._size -= 1

    async def close(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                await conn.close()
            except (asyncio.QueueEmpty, Exception):
                break
        self._size = 0

    class _ConnectionContextManager:
        def __init__(self, pool):
            self.pool = pool
            self.conn = None

        async def __aenter__(self):
            self.conn = await self.pool.acquire()
            return self.conn

        async def __aexit__(self, *args):
            await self.pool.release(self.conn)

    def connection(self):
        return self._ConnectionContextManager(self)


_pool: ConnectionPool | None = None


def get_pool(db_path: str = "", max_connections: int = 5) -> ConnectionPool:
    global _pool
    if _pool is None and db_path:
        _pool = ConnectionPool(db_path, max_connections)
    return _pool


async def init_pool(db_path: str, max_connections: int = 5):
    global _pool
    _pool = ConnectionPool(db_path, max_connections)
    log.info("connection pool initialized: max_connections=%d", max_connections)
