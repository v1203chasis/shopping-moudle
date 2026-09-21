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