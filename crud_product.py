from db_helper import db  # 导入我们封装好的 DBHelper 实例

def create_product_in_db(name, price, stock):
    """在数据库中创建商品，返回新生成的 ID"""
    new_id = db.execute_update(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        (name, price, stock)
    )
    return new_id

def get_all_products():
    """查询所有商品，返回字典列表"""
    return db.execute_query("SELECT id, name, price, stock FROM products")

def get_product_by_id(product_id):
    """根据 ID 查询单个商品，返回字典或 None"""
    rows = db.execute_query(
        "SELECT id, name, price, stock FROM products WHERE id = ?", 
        (product_id,)
    )
    # 如果查到了，返回第一条数据；如果没查到，返回 None
    return rows[0] if rows else None


def delete_product_from_db(product_id):
    """删除商品，返回 True 表示成功，False 表示不存在"""
    # 先查是否存在
    rows = db.execute_query("SELECT id FROM products WHERE id = ?", (product_id,))
    if not rows:
        return False  # 不存在，直接返回 False
    # 存在，执行删除
    db.execute_update("DELETE FROM products WHERE id = ?", (product_id,))
    return True

def update_product_in_db(product_id, name, price, stock):
    """更新商品信息，返回 True 表示成功，False 表示商品不存在"""
    # 1. 先检查商品是否存在
    rows = db.execute_query("SELECT id FROM products WHERE id = ?", (product_id,))
    if not rows:
        return False  # 商品不存在，直接返回 False
    
    # 2. 执行更新
    db.execute_update(
        "UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?",
        (name, price, stock, product_id)
    )
    return True