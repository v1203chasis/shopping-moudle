
import pytest
import requests
import allure
import jsonschema
from schemas import PAYMENT_SCHEMA, PAY_RESPONSE_SCHEMA
from db_helper import db


BASE_URL = "http://127.0.0.1:8000"


@allure.epic("电商后端系统")
@allure.feature("支付管理模块")
@pytest.mark.payment
class TestPaymentAPI:

    # ==================== 1. 支付成功 ====================
    @allure.story("支付订单")
    @allure.title("支付成功，验证订单状态和支付记录")
    @pytest.mark.smoke
    def test_pay_order(self, order_factory):
        """支付 -> 验证订单状态变 paid -> 验证支付记录落库"""
        # 1. 造一个订单
        order_info = order_factory(product_name="支付测试商品", price=20.0, quantity=3)
        order_id = order_info["order_id"]

        # 2. 调用支付接口
        response = requests.post(f"{BASE_URL}/api/payments/{order_id}")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "paid"

        #结构校验
        api_data = response.json()["data"]
        jsonschema.validate(api_data, PAY_RESPONSE_SCHEMA)
        # 3. 查数据库，验证订单状态
        db_order = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
        assert db_order[0]["status"] == "paid"

        # 4. 查数据库，验证支付记录
        db_payment = db.execute_query(
            "SELECT amount, status FROM payments WHERE order_id = ?",
            (order_id,)
        )
        assert len(db_payment) == 1
        assert db_payment[0]["amount"] == 60.0   # 20.0 * 3
        assert db_payment[0]["status"] == "success"

        print(f"\n✅ 支付成功！订单 {order_id} 状态变为 paid，支付金额 60.0 已落库。")

    # ==================== 2. 查询支付记录 ====================
    @allure.story("查询支付")
    @allure.title("查询订单的支付记录")
    @pytest.mark.smoke
    def test_get_payment(self, payment_factory):
        """查支付记录，验证返回数据"""
        payment_info = payment_factory(product_name="查询支付商品", price=15.0, quantity=2)
        order_id = payment_info["order_id"]

        response = requests.get(f"{BASE_URL}/api/payments/{order_id}")
        #结构校验
        api_data = response.json()["data"]
        jsonschema.validate(api_data, PAYMENT_SCHEMA)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["order_id"] == order_id
        assert data["amount"] == 30.0   # 15.0 * 2
        assert data["status"] =="success"

    # ==================== 3. 退款成功 ====================
    @allure.story("退款")
    @allure.title("退款成功，验证订单状态和支付记录变更")
    @pytest.mark.smoke
    def test_refund_order(self, payment_factory):
        """退款 -> 订单状态变 refunded -> 支付记录状态变 refunded"""
        payment_info = payment_factory(product_name="退款测试商品", price=10.0, quantity=1)
        order_id = payment_info["order_id"]

        # 1. 调用退款接口
        response = requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "refunded"

        # 2. 查数据库，验证订单状态
        db_order = db.execute_query("SELECT status FROM orders WHERE id = ?", (order_id,))
        assert db_order[0]["status"] == "refunded"

        # 3. 查数据库，验证支付记录状态
        db_payment = db.execute_query("SELECT status FROM payments WHERE order_id = ?", (order_id,))
        assert db_payment[0]["status"] == "refunded"

        print(f"\n✅ 退款成功！订单 {order_id} 状态变为 refunded。")

    # ==================== 4. 业务异常 ====================
    @allure.story("支付管理")
    @allure.title("支付失败：订单不存在")
    def test_pay_order_not_exists(self):
        response = requests.post(f"{BASE_URL}/api/payments/99999")
        assert response.status_code == 404

    @allure.story("支付管理")
    @allure.title("支付失败：订单已支付")
    def test_pay_order_already_paid(self, payment_factory):
        payment_info = payment_factory(product_name="重复支付商品", price=10.0, quantity=1)
        order_id = payment_info["order_id"]

        # 再次支付同一个订单
        response = requests.post(f"{BASE_URL}/api/payments/{order_id}")
        assert response.status_code == 400, f"期望400，实际{response.status_code}"

    @allure.story("支付管理")
    @allure.title("支付失败：订单已取消")
    def test_pay_order_cancelled(self, order_factory):
        order_info = order_factory(product_name="取消后支付商品", price=10.0, quantity=1)
        order_id = order_info["order_id"]

        # 先取消订单
        requests.put(f"{BASE_URL}/api/orders/{order_id}/cancel")

        # 再尝试支付
        response = requests.post(f"{BASE_URL}/api/payments/{order_id}")
        assert response.status_code == 400

    @allure.story("支付管理")
    @allure.title("退款失败：订单未支付")
    def test_refund_order_not_paid(self, order_factory):
        # 造一个订单，但不支付
        order_info = order_factory(product_name="未支付退款商品", price=10.0, quantity=1)
        order_id = order_info["order_id"]

        # 尝试退款
        response = requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
        assert response.status_code == 400, f"期望400，实际{response.status_code}"

    @allure.story("支付管理")
    @allure.title("退款失败：订单不存在")
    def test_refund_order_not_exists(self):
        response = requests.put(f"{BASE_URL}/api/payments/99999/refund")
        assert response.status_code == 404

    @allure.story("支付管理")
    @allure.title("退款失败：重复退款")
    def test_refund_order_already_refunded(self, payment_factory):
        payment_info = payment_factory(product_name="重复退款商品", price=10.0, quantity=1)
        order_id = payment_info["order_id"]

        # 第一次退款，应该成功
        response1 = requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
        assert response1.status_code == 200

        # 第二次退款，应该失败
        response2 = requests.put(f"{BASE_URL}/api/payments/{order_id}/refund")
        assert response2.status_code == 400
