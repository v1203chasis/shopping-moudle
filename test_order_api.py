import pytest
import requests
import allure
from db_helper import db

BASE_URL = "http://127.0.0.1:8000"


@allure.epic("电商后端系统")
@allure.feature("订单管理模块")
@pytest.mark.order
class TestOrderAPI:

    # ==================== 1. 下单成功 + 三重验证 ====================
    @allure.story("创建订单")
    @allure.title("测试下单成功，并验证库存扣减和订单落库")
    @pytest.mark.smoke
    def test_create_order(self, order_factory):
        """下单 -> 查接口 -> 查数据库 -> 验证库存扣减"""
        # 1. 准备数据（工厂会自动下单）
        order_info = order_factory(product_name="下单测试商品", price=25.0, stock=100, quantity=2)
        order_id = order_info["order_id"]
        product_id = order_info["product_id"]

        # 2. 通过接口查订单详情
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}")
        assert response.status_code == 200
        api_data = response.json()["data"]
        assert api_data["quantity"] == 2
        assert api_data["total_price"] == 50.0   # 25.0 * 2
        assert api_data["status"] == "created"

        # 3. 直接查数据库，确认订单落库
        db_orders = db.execute_query(
            "SELECT id, user_id, product_id, quantity, total_price, status FROM orders WHERE id = ?",
            (order_id,)
        )
        assert len(db_orders) == 1, "数据库里找不到这条订单！"
        assert db_orders[0]["total_price"] == 50.0
        assert db_orders[0]["status"] == "created"

        # 4. 验证库存是否扣减（100 - 2 = 98）
        db_product = db.execute_query(
            "SELECT stock FROM products WHERE id = ?",
            (product_id,)
        )
        assert db_product[0]["stock"] == 98, f"库存扣减错误，期望 98，实际 {db_product[0]['stock']}"

        print(f"\n✅ 下单全链路验证通过！订单ID={order_id}，库存已从100扣减到98。")

    # ==================== 2. 查询订单（单个 + 列表） ====================
    @allure.story("查询订单")
    @allure.title("测试查询单个订单")
    @pytest.mark.smoke
    def test_get_order_by_id(self, order_factory):
        """查单个订单，验证返回数据"""
        order_info = order_factory(product_name="查询测试商品", price=15.0, quantity=3)
        order_id = order_info["order_id"]

        response = requests.get(f"{BASE_URL}/api/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == order_id
        assert data["quantity"] == 3
        assert data["total_price"] == 45.0   # 15.0 * 3

    @allure.story("查询订单")
    @allure.title("测试查询某个用户的所有订单")
    @pytest.mark.smoke
    def test_get_user_orders(self, order_factory):
        """查用户订单列表，验证列表里有刚下的订单"""
        order_info = order_factory(product_name="列表测试商品", price=10.0, quantity=1)
        user_id = order_info["user_id"]
        order_id = order_info["order_id"]

        response = requests.get(f"{BASE_URL}/api/orders?user_id={user_id}")
        assert response.status_code == 200
        orders = response.json()["data"]
        assert len(orders) == 1, "该用户应该有 1 条订单"
        assert orders[0]["id"] == order_id

    # ==================== 3. 取消订单 ====================
    @allure.story("取消订单")
    @allure.title("测试取消订单，并验证库存回滚")
    @pytest.mark.smoke
    def test_cancel_order(self, order_factory):
        """取消订单 -> 状态变 cancelled -> 库存回滚"""
        order_info = order_factory(product_name="取消测试商品", price=20.0, stock=50, quantity=5)
        order_id = order_info["order_id"]
        product_id = order_info["product_id"]

        # 1. 取消前，库存应该是 45（50 - 5）
        stock_before = db.execute_query("SELECT stock FROM products WHERE id = ?", (product_id,))[0]["stock"]
        assert stock_before == 45

        # 2. 调用取消接口
        response = requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "cancelled"

        # 3. 数据库确认状态
        db_order = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
        assert db_order[0]["status"] == "cancelled"

        # 4. 验证库存回滚（应该回到 50）
        stock_after = db.execute_query("SELECT stock FROM products WHERE id = ?", (product_id,))[0]["stock"]
        assert stock_after == 50, f"库存回滚错误，期望 50，实际 {stock_after}"

        print(f"\n✅ 取消订单验证通过！库存已从 45 回滚到 50。")

    # ==================== 4. 参数校验（Pydantic 拦截，参数化） ====================
    @allure.story("订单管理")
    @allure.title("测试下单失败（参数非法）：{case_name}")
    @pytest.mark.parametrize("case_name, payload", [
        ("数量为0",       {"user_id": 1, "product_id": 1, "quantity": 0}),
        ("数量为负",       {"user_id": 1, "product_id": 1, "quantity": -1}),
        ("user_id为负",    {"user_id": -1, "product_id": 1, "quantity": 1}),
        ("商品id为负",     {"user_id": 1, "product_id": -1, "quantity": 1}),
        ("缺少数量字段",     {"user_id": 1, "product_id": 1}),
    ])
    def test_create_order_invalid_params(self, case_name, payload):
        """参数校验：Pydantic 直接拦截，返回 422，不查数据库"""
        response = requests.post(f"{BASE_URL}/api/orders", json=payload)
        assert response.status_code == 422, f"[{case_name}] 期望422，实际{response.status_code}"

    # ==================== 5. 业务逻辑异常 ====================
    @allure.story("订单管理")
    @allure.title("测试下单失败（用户不存在）")
    def test_create_order_user_not_exists(self, product_factory):
        # 只造商品，不造用户，用一个不存在的 user_id
        product_id = product_factory(name="库存测试商品", price=10, stock=100)
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json={"user_id": 99999, "product_id": product_id, "quantity": 1}
        )
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    @allure.story("订单管理")
    @allure.title("测试下单失败（商品不存在）")
    def test_create_order_product_not_exists(self, user_factory):
        # 只造用户，不造商品，用一个不存在的 product_id
        user_id = user_factory(username="no_product_user", password="123456")
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json={"user_id": user_id, "product_id": 99999, "quantity": 1}
        )
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    @allure.story("订单管理")
    @allure.title("测试下单失败（库存不足）")
    def test_create_order_stock_insufficient(self, user_factory, product_factory):
        # 造一个库存只有 5 的商品，试图买 10 个
        user_id = user_factory(username="stock_test_user", password="123456")
        product_id = product_factory(name="库存不足商品", price=10, stock=5)

        response = requests.post(
            f"{BASE_URL}/api/orders",
            json={"user_id": user_id, "product_id": product_id, "quantity": 10}
        )
        assert response.status_code == 400, f"期望400，实际{response.status_code}"

    # ==================== 6. 状态异常 ====================
    @allure.story("订单管理")
    @allure.title("测试取消订单失败（订单不存在）")
    def test_cancel_order_not_exists(self):
        response = requests.put(f"{BASE_URL}/api/orders/99999/cancel")
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    @allure.story("订单管理")
    @allure.title("测试取消订单失败（订单已取消）")
    def test_cancel_order_already_cancelled(self, order_factory):
        order_info = order_factory(product_name="重复取消商品", price=10, quantity=1)
        order_id = order_info["order_id"]

        # 第一次取消，应该成功
        response1 = requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        assert response1.status_code == 200

        # 第二次取消，应该失败（400）
        response2 = requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")
        assert response2.status_code == 400, f"期望400，实际{response2.status_code}"