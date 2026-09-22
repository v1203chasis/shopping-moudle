import pytest
import requests
from db_helper import db

# 后端的基础地址
BASE_URL = "http://127.0.0.1:8000"


# ================= 商品工厂 =================


@pytest.fixture
def product_factory():
    created_ids = []
    def _create_product(name, price, stock=0):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": name, "price": price, "stock": stock}
        )
        assert response.status_code == 200, "创建商品失败"
        product_id = response.json()["data"]["id"]
        created_ids.append(product_id)
        return product_id
    yield _create_product
    for pid in created_ids:
        requests.delete(f"{BASE_URL}/api/products/{pid}")


# ================= 用户工厂 =================

@pytest.fixture
def user_factory():
    created_ids = []

    def _create_user(username, password):
        response = requests.post(
            f"{BASE_URL}/api/register",
            json={"username": username, "password": password}
        )
        assert response.status_code == 200, "注册接口请求失败"
        
        result = response.json()
        if "data" in result:
            # 注册成功，从 data 里取 id
            user_id = result["data"]["id"]
        else:
            # 用户已存在，去数据库里查出来
            db_rows = db.execute_query(
                "SELECT id FROM users WHERE username = ?", (username,)
            )
            user_id = db_rows[0]["id"]
        
        created_ids.append(user_id)
        return user_id

    yield _create_user

    # 测试结束后，直接从数据库清理用户，不调接口
    for uid in created_ids:
        db.execute_update("DELETE FROM users WHERE id = ?", (uid,))


# ================= 订单工厂 =================

@pytest.fixture
def order_factory(product_factory, user_factory):
    """
    订单工厂 Fixture
    动态创建订单，测试结束后通过取消订单接口清理数据（顺便回滚库存）
    """
    created_order_ids = []

    def _create_order(product_name="测试商品", price=10.0, stock=100, quantity=1):
        # 1. 先造一个用户和商品（复用已有的工厂）
        user_id = user_factory(username=f"order_user_{len(created_order_ids)}", password="123456")
        product_id = product_factory(name=product_name, price=price, stock=stock)

        # 2. 调用下单接口
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json={"user_id": user_id, "product_id": product_id, "quantity": quantity}
        )
        assert response.status_code == 200, f"下单失败: {response.text}"
        order_id = response.json()["data"]["order_id"]
        created_order_ids.append(order_id)

        # 3. 返回订单 ID 和相关信息（方便测试用例使用）
        return {
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": price * quantity,
        }

    yield _create_order

    # ===== 测试结束后的清理工作 =====
    for order_id in created_order_ids:
        try:
            # 调用取消订单接口，顺便回滚库存
            requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        except Exception:
            pass


 # ================= 支付工厂 =================

@pytest.fixture
def payment_factory(order_factory):
    """
    支付工厂 Fixture
    创建一个订单并支付，测试结束后自动清理数据
    """
    created_order_ids = []

    def _create_payment(product_name="支付测试商品", price=10.0, stock=100, quantity=1):
        # 1. 先用 order_factory 创建一个订单
        order_info = order_factory(product_name=product_name, price=price, stock=stock, quantity=quantity)
        order_id = order_info["order_id"]

        # 2. 调用支付接口
        response = requests.post(f"{BASE_URL}/api/payments/{order_id}")
        assert response.status_code == 200, f"支付失败: {response.text}"

        created_order_ids.append(order_id)

        # 3. 返回订单 ID 和支付信息
        return {
            "order_id": order_id,
            "user_id": order_info["user_id"],
            "product_id": order_info["product_id"],
            "quantity": quantity,
            "amount": price * quantity,
        }

    yield _create_payment

    # ===== 测试结束后的清理工作 =====
    for order_id in created_order_ids:
        try:
            # 1. 先尝试退款（把订单状态从 paid 变回 refunded）
            requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
            # 2. 再取消订单（回滚库存）
            requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        except Exception:
            pass   