from db_helper import db
import crud_user
import crud_product


def add_to_cart(user_id, product_id, quantity):
    """加入购物车"""
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

    # 4. 查购物车是否已有该商品
    check_cart = db.execute_query(
        "SELECT * FROM carts WHERE user_id = ? AND product_id = ?",
        (user_id, product_id)
    )

    if check_cart:
        new_quantity = check_cart[0]["quantity"] + quantity
        db.execute_update(
            "UPDATE carts SET quantity = ? WHERE id = ?",
            (new_quantity, check_cart[0]["id"])
        )
        cart_id = check_cart[0]["id"]
        final_quantity = new_quantity
    else:
        cart_id = db.execute_update(
            "INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, quantity)
        )
        final_quantity = quantity

    return {
        "code": 200,
        "msg": "加入购物车成功",
        "data": {
            "cart_id": cart_id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": final_quantity
        }
    }


def get_cart(user_id):
    """查看购物车"""
    rows = db.execute_query(
        "SELECT id, user_id, product_id, quantity FROM carts WHERE user_id = ?",
        (user_id,)
    )
    return {"code": 200, "msg": "查询成功", "data": rows}


def update_cart_quantity(cart_id, quantity):
    """修改购物车数量"""
    rows = db.execute_query("SELECT * FROM carts WHERE id = ?", (cart_id,))
    if not rows:
        return {"code": 404, "msg": "购物车记录不存在"}
    db.execute_update(
        "UPDATE carts SET quantity = ? WHERE id = ?",
        (quantity, cart_id)
    )
    return {"code": 200, "msg": "修改成功", "data": {"cart_id": cart_id, "quantity": quantity}}


def delete_cart_item(cart_id):
    """删除购物车商品"""
    rows = db.execute_query("SELECT * FROM carts WHERE id = ?", (cart_id,))
    if not rows:
        return {"code": 404, "msg": "没有该商品"}
    db.execute_update("DELETE FROM carts WHERE id = ?", (cart_id,))
    return {"code": 200, "msg": "删除成功"}


def clear_cart(user_id):
    """清空购物车"""
    db.execute_update(
        "DELETE FROM carts WHERE user_id = ?",
        (user_id,)
    )
    return {"code": 200, "msg": "清空成功"}