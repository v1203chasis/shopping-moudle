import sqlite3

DB_FILE = "shop.db"

def init_db():
    """初始化数据库，创建商品表和用户表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. 创建商品表（你之前写好的）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    # 2. 创建用户表（今天新增的）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
