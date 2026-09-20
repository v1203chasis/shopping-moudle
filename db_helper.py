# db_helper.py
import sqlite3

class DBHelper:
    """
    一个数据库管理助手（模仿连接池的简单版）
    负责统一管理数据库连接和释放
    """
    def __init__(self, db_file="shop.db"):
        self.db_file = db_file

    def get_connection(self):
        """获取连接，这是我们所有操作的入口"""
        conn = sqlite3.connect(self.db_file)
        # 让查询结果变成字典形式（很重要，方便后续处理）
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, sql, params=None):
        """执行查询语句（SELECT），返回结果列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]  # 转成字典列表
        conn.close()
        return result

    def execute_update(self, sql, params=None):
        """执行增删改语句（INSERT/UPDATE/DELETE）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

# 实例化一个全局的 DBHelper 对象，后面所有地方都用它！
db = DBHelper()