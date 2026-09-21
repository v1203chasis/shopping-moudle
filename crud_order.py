from db_helper import db
import crud_user
import crud_product


def create_order(user_id, product_id, quantity):
    """创建订单"""
    # 1. 检查用户是否存在
    check_user = crud_user.get_user_by_id(user_id)
    if not check_user:
        return {"code": 404, "msg": "用户不存在"}

    # 2. 检查商品是否存在
    check_product = crud_product.get_product_by_id(product_id)
    if not check_product:
        return {"code": 404, "msg": "商品不存在"}

    # 3. 检查库存是否足够
    if check_product["stock"] < quantity:
        return {"code": 400, "msg": "库存不足"}

    # 4. 计算总价
    total_price = check_product["price"] * quantity

    # 5. 扣减库存
    db.execute_update(
        "UPDATE products SET stock = stock - ? WHERE id = ?",
        (quantity, product_id)
    )

    # 6. 生成订单记录
    new_order_id = db.execute_update(
        "INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, product_id, quantity, total_price, "created")
    )

    # 7. 返回订单结果
    return {
        "code": 200,
        "msg": "下单成功",
        "data": {
            "order_id": new_order_id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price,
            "status": "created"
        }
    }

def get_order_by_id(order_id):
    """根据 ID 查询单个订单"""
    rows = db.execute_query(
        "SELECT id, user_id, product_id, quantity, total_price, status, created_at FROM orders WHERE id = ?",
        (order_id,)
    )
    # 查到了返回第一条，没查到返回 None
    return rows[0] if rows else None

def get_user_orders(user_id):
    """查询某个用户的所有订单（按时间倒序排列）"""
    rows = db.execute_query(
        "SELECT id, user_id, product_id, quantity, total_price, status, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    return rows


def cancel_order(order_id):
    """取消订单（含库存回滚）"""
    # 1. 查询订单是否存在
    order = get_order_by_id(order_id)
    if not order:
        return {"code": 404, "msg": "订单不存在"}

    # 2. 检查订单状态（只有 'created' 状态才允许取消）
    if order["status"] != "created":
        return {"code": 400, "msg": "该订单状态不允许取消"}

    # 3. 回滚库存（把下单时扣掉的库存加回去）
    db.execute_update(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (order["quantity"], order["product_id"])
    )

    # 4. 修改订单状态为已取消
    db.execute_update(
        "UPDATE orders SET status = 'cancelled' WHERE id = ?",
        (order_id,)
    )

    return {
        "code": 200, 
        "msg": "取消成功", 
        "data": {"order_id": order_id, "status": "cancelled"}}

