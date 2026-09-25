import pytest
import requests
import yaml
from db_helper import db

# 后端的基础地址
BASE_URL = "http://127.0.0.1:8000"


# ================= 商品工厂 =================

@pytest.fixture
def product_factory():
    created_ids = []

    def _create_product(name="测试商品", price=10.0, stock=100):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": name, "price": price, "stock": stock}
        )
        assert response.status_code == 200, f"创建商品失败: {response.text}"
        product_id = response.json()["data"]["id"]
        created_ids.append(product_id)
        return product_id

    yield _create_product

    # 测试结束后，从数据库直接删除商品
    for pid in created_ids:
        db.execute_update("DELETE FROM products WHERE id = ?", (pid,))


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
            user_id = result["data"]["id"]
        else:
            db_rows = db.execute_query(
                "SELECT id FROM users WHERE username = ?", (username,)
            )
            user_id = db_rows[0]["id"]

        created_ids.append(user_id)
        return user_id

    yield _create_user

    for uid in created_ids:
        db.execute_update("DELETE FROM users WHERE id = ?", (uid,))


# ================= 订单工厂 =================

@pytest.fixture
def order_factory(product_factory, user_factory):
    created_order_ids = []

    def _create_order(product_name="测试商品", price=10.0, stock=100, quantity=1):
        user_id = user_factory(
            username=f"order_user_{len(created_order_ids)}", password="123456"
        )
        product_id = product_factory(name=product_name, price=price, stock=stock)

        response = requests.post(
            f"{BASE_URL}/api/orders",
            json={"user_id": user_id, "product_id": product_id, "quantity": quantity}
        )
        assert response.status_code == 200, f"下单失败: {response.text}"
        order_id = response.json()["data"]["order_id"]
        created_order_ids.append(order_id)

        return {
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": price * quantity,
        }

    yield _create_order

    for order_id in created_order_ids:
        try:
            requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        except Exception:
            pass


# ================= 支付工厂 =================

@pytest.fixture
def payment_factory(order_factory):
    created_order_ids = []

    def _create_payment(product_name="支付测试商品", price=10.0, stock=100, quantity=1):
        order_info = order_factory(
            product_name=product_name, price=price, stock=stock, quantity=quantity
        )
        order_id = order_info["order_id"]

        response = requests.post(f"{BASE_URL}/api/payments/{order_id}")
        assert response.status_code == 200, f"支付失败: {response.text}"

        created_order_ids.append(order_id)

        return {
            "order_id": order_id,
            "user_id": order_info["user_id"],
            "product_id": order_info["product_id"],
            "quantity": quantity,
            "amount": price * quantity,
        }

    yield _create_payment

    for order_id in created_order_ids:
        try:
            requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
            requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        except Exception:
            pass


# ================= Hook 函数 =================

def pytest_collection_modifyitems(config, items):
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")


# ================= YAML 加载工具 =================

def load_yaml(file_path):
    """从 YAML 文件读取测试数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)