import sqlite3

# 数据库文件名统一在这里定义
DB_FILE = "shop.db"

def get_connection():
    """获取数据库连接，所有操作数据库的地方都调用这个函数"""
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    """初始化数据库，创建商品表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

