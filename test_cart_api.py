import pytest
import requests
import allure
from db_helper import db
from jsonpath_ng import parse
import jsonschema

BASE_URL = "http://127.0.0.1:8000"


@allure.epic("电商后端系统")
@allure.feature("购物车管理模块")
class TestCartAPI:

    # ==================== 1. 加入购物车 ====================
    @allure.story("加入购物车")
    @allure.title("测试加入购物车：用户{user_id}-商品{product_id}-数量{quantity}")
    @pytest.mark.parametrize("user_id, product_id, quantity, expected", [
        (1, 1, 2, 200),        # 成功
        (9999, 1, 2, 404),     # 用户不存在
        (1, 9999, 2, 404),     # 商品不存在
        (1, 1, 99999, 400),    # 库存不足
        (1, 1, 0, 422),        # 数量为 0
        (1, 1, -1, 422),       # 数量为负
    ])
    def test_add_to_cart(self, user_factory, product_factory, user_id, product_id, quantity, expected):
        """测试加入购物车"""
        # 1. 准备数据：如果是“正常 id”，就用 factory 创建真实数据
        if user_id != 9999:
            user_id = user_factory(username=f"cart_user_{user_id}", password="123456")
        if product_id != 9999:
            product_id = product_factory(name=f"cart_product_{product_id}", price=10, stock=100)

        # 2. 发请求
        response = requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": quantity}
        )

        # 3. 断言状态码
        assert response.status_code == expected, f"期望{expected}，实际{response.status_code}"

        # 4. 如果成功，双重断言：接口 + 数据库
        if expected == 200:
            result = response.json()
            assert result["data"]["user_id"] == user_id
            assert result["data"]["product_id"] == product_id
            assert result["data"]["quantity"] == quantity

            rows = db.execute_query(
                "SELECT user_id, product_id, quantity FROM carts WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
            assert len(rows) == 1, "数据库里没有找到刚加入购物车的记录"
            assert rows[0]["user_id"] == user_id
            assert rows[0]["product_id"] == product_id
            assert rows[0]["quantity"] == quantity

    # ==================== 2. 查询购物车 ====================
    @allure.story("查询购物车")
    @allure.title("测试查询购物车")
    def test_get_cart(self, user_factory, product_factory):
        """测试查询购物车"""
        # 1. 准备数据
        user_id = user_factory(username="cart_query_user", password="123456")
        product_id = product_factory(name="查询商品", price=20, stock=100)

        # 2. 先加入购物车
        cart_test = requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": 2}
        )
        cart_id = cart_test.json()["data"]["cart_id"]

        # 3. 再查询购物车
        response = requests.get(f"{BASE_URL}/api/cart?user_id={user_id}")

        # 4. 断言
        res = response.json()
        assert response.status_code == 200, "查询失败"
        assert len(res["data"]) == 1, "购物车列表为空"
        assert res["data"][0]["product_id"] == product_id

        # 5. 数据库校验
        result = db.execute_query(
            "SELECT user_id, product_id, quantity FROM carts WHERE id = ?",
            (cart_id,)
        )
        assert result[0]["user_id"] == user_id
        assert result[0]["product_id"] == product_id
        assert result[0]["quantity"] == 2

    # ==================== 3. 修改购物车数量 ====================
    @allure.story("修改购物车数量")
    @allure.title("测试修改购物车数量")
    def test_update_cart_quantity(self, user_factory, product_factory):
        """测试修改购物车数量"""
        # 1. 准备数据
        user_id = user_factory(username="cart_update_user", password="123456")
        product_id = product_factory(name="修改商品", price=10, stock=100)

        # 2. 加购，拿到 cart_id
        add_res = requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": 2}
        )
        cart_id = add_res.json()["data"]["cart_id"]

        # 3. 修改数量
        response = requests.put(
            f"{BASE_URL}/api/cart/{cart_id}",
            json={"quantity": 5}
        )

        # 4. 断言
        assert response.status_code == 200
        assert response.json()["data"]["quantity"] == 5

        # 5. 数据库校验
        rows = db.execute_query("SELECT quantity FROM carts WHERE id = ?", (cart_id,))
        assert rows[0]["quantity"] == 5

    @allure.story("修改购物车数量")
    @allure.title("测试修改不存在的购物车记录")
    def test_update_cart_not_exists(self):
        """测试修改不存在的购物车记录"""
        response = requests.put(
            f"{BASE_URL}/api/cart/9999",
            json={"quantity": 5}
        )
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    # ==================== 4. 删除购物车商品 ====================
    @allure.story("删除购物车商品")
    @allure.title("测试删除购物车商品")
    def test_delete_cart_item(self, user_factory, product_factory):
        """测试删除购物车商品"""
        # 1. 准备数据
        user_id = user_factory(username="cart_delete_user", password="123456")
        product_id = product_factory(name="删除商品", price=10, stock=100)

        # 2. 加购，拿到 cart_id
        add_res = requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": 2}
        )
        cart_id = add_res.json()["data"]["cart_id"]

        # 3. 删除
        response = requests.delete(f"{BASE_URL}/api/cart/{cart_id}")
        assert response.status_code == 200

        # 4. 数据库校验：购物车记录应该没了
        rows = db.execute_query("SELECT * FROM carts WHERE id = ?", (cart_id,))
        assert len(rows) == 0, "购物车记录没有被删除"

    @allure.story("删除购物车商品")
    @allure.title("测试删除不存在的购物车商品")
    def test_delete_cart_not_exists(self):
        """测试删除不存在的购物车商品"""
        response = requests.delete(f"{BASE_URL}/api/cart/9999")
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    # ==================== 5. 清空购物车 ====================
    @allure.story("清空购物车")
    @allure.title("测试清空购物车")
    def test_clear_cart(self, user_factory, product_factory):
        """测试清空购物车"""
        # 1. 准备数据
        user_id = user_factory(username="cart_clear_user", password="123456")
        product_id = product_factory(name="清空商品", price=10, stock=100)

        # 2. 加购两次
        requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": 2}
        )
        requests.post(
            f"{BASE_URL}/api/cart",
            json={"user_id": user_id, "product_id": product_id, "quantity": 3}
        )

        # 3. 清空
        response = requests.delete(f"{BASE_URL}/api/cart?user_id={user_id}")
        assert response.status_code == 200

        # 4. 再查，应该是空的
        check_res = requests.get(f"{BASE_URL}/api/cart?user_id={user_id}")
        assert check_res.json()["data"] == []