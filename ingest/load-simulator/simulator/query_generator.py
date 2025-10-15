import asyncpg
import random
from faker import Faker

fake = Faker()

class QueryGenerator:
    def __init__(self, host, port, database, username, password):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection_pool = None
    
    async def connect(self):
        self.connection_pool = await asyncpg.create_pool(
            host=self.host, port=self.port, user=self.username,
            password=self.password, database=self.database,
            min_size=2, max_size=10
        )
    
    async def disconnect(self):
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def insert_user(self):
        async with self.connection_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (username, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                fake.user_name() + str(random.randint(1000, 9999)), fake.email()
            )
    
    async def simple_select(self):
        async with self.connection_pool.acquire() as conn:
            await conn.fetch("SELECT * FROM users LIMIT 10")
    
    async def join_query(self):
        async with self.connection_pool.acquire() as conn:
            await conn.fetch("""
                SELECT u.username, COUNT(o.id) 
                FROM users u LEFT JOIN orders o ON u.id = o.user_id 
                GROUP BY u.username LIMIT 20
            """)
    
    async def execute_slow_query(self):
        async with self.connection_pool.acquire() as conn:
            await conn.fetchval("SELECT pg_sleep($1)", random.uniform(1.0, 2.0))
