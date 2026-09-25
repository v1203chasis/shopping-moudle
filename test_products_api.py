import pytest
import requests
import allure
import jsonschema
from schemas import PRODUCT_SCHEMA
from db_helper import db


BASE_URL = "http://127.0.0.1:8000"


@allure.epic("电商后端系统")
@allure.feature("商品管理模块")
@pytest.mark.product
class TestProductAPI:

    # ==================== 1. 创建 + 查接口 + 查数据库 ====================
    @allure.story("添加并查询商品")
    @allure.title("测试添加商品：{name}，价格：{price}")
    @pytest.mark.smoke
    @pytest.mark.parametrize("name, price, stock", [
        ("猪猪玩偶", 12.99, 50),
        ("deepseek周边", 29.9, 100),
        ("测试0库存商品", 9.9, 0),
    ])
    def test_create_product_and_verify_db(self, product_factory, name, price, stock):
        """测试用例：创建商品 -> 通过接口查 -> 直接查数据库，三重验证！"""
        # 1. 创建商品
        product_id = product_factory(name=name, price=price, stock=stock)

        # 2. 通过接口查（GET）
        response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert response.status_code == 200
        api_data = response.json()["data"]

        # 结构校验
        jsonschema.validate(api_data, PRODUCT_SCHEMA)
        
        assert api_data is not None, "GET 接口查不到刚创建的商品！"
        assert api_data["name"] == name

        # 3. 直接查数据库
        db_rows = db.execute_query(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,)
        )
        assert len(db_rows) == 1, "数据库里找不到这条记录！"
        assert db_rows[0]["name"] == name
        assert db_rows[0]["price"] == price
        assert db_rows[0]["stock"] == stock

        print(f"\n✅ 全链路验证通过！ID={product_id} 在 API 和 DB 中均正确。")

    # ==================== 2. 修改商品（成功场景） ====================
    @allure.story("修改商品信息")
    @allure.title("测试修改商品：{new_name}")
    @pytest.mark.smoke
    @pytest.mark.parametrize("old_name, new_name, new_price, new_stock", [
        ("原始猪猪", "修改后的猪猪", 99.9, 50),
        ("原始小深", "修改后的小深", 199.9, 100),
    ])
    def test_update_product(self, product_factory, old_name, new_name, new_price, new_stock):
        # 1. 用旧数据创建一个商品
        product_id = product_factory(name=old_name, price=10.0, stock=5)

        # 2. 调用 PUT 接口，修改这个商品
        response = requests.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"name": new_name, "price": new_price, "stock": new_stock}
        )
        assert response.status_code == 200, f"修改接口返回失败，实际{response.status_code}"

        # 3. 通过接口查，验证修改后数据是否生效
        # 3. 通过接口查，验证修改后数据是否生效（直接查单个商品）
        get_response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert get_response.status_code == 200, "查询商品详情失败"
        api_data = get_response.json()["data"]  # ✅ 现在这里有 data 了

        # 4. 验证数据
        assert api_data["name"] == new_name
        assert api_data["price"] == new_price
        assert api_data["stock"] == new_stock

        # 4. 直接查数据库，确认修改已落库
        db_rows = db.execute_query(
            "SELECT name, price, stock FROM products WHERE id = ?",
            (product_id,)
        )
        assert db_rows[0]["name"] == new_name
        assert db_rows[0]["price"] == new_price
        assert db_rows[0]["stock"] == new_stock

        print(f"\n✅ 商品 {product_id} 修改验证通过！")

    # ==================== 3. 创建商品：异常 & 边界 ====================
    @allure.story("商品管理")
    @allure.title("测试新增商品失败（价格为0）")
    def test_create_product_price_zero(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "测试商品", "price": 0, "stock": 10}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试新增商品失败（价格为负数）")
    def test_create_product_price_negative(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "测试商品", "price": -1, "stock": 10}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试新增商品成功（价格=0.01，最小值）")
    def test_create_product_price_min(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "测试商品", "price": 0.01, "stock": 10}
        )
        assert response.status_code == 200, f"期望200，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试新增商品成功（库存=0）")
    def test_create_product_stock_zero(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "无库存商品", "price": 10, "stock": 0}
        )
        assert response.status_code == 200, f"期望200，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试新增商品失败（库存为负数）")
    def test_create_product_stock_negative(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "测试商品", "price": 10, "stock": -1}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试新增商品失败（名称为空）")
    def test_create_product_name_empty(self):
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": "", "price": 10, "stock": 10}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    # ==================== 4. 查、改、删：异常场景 ====================
    @allure.story("商品管理")
    @allure.title("测试查询单个商品失败（商品不存在）")
    def test_get_product_not_exists(self):
        response = requests.get(f"{BASE_URL}/api/products/9999")
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试修改商品失败（商品不存在）")
    def test_update_product_not_exists(self):
        response = requests.put(
            f"{BASE_URL}/api/products/9999",
            json={"name": "不存在", "price": 10, "stock": 10}
        )
        assert response.status_code == 404, f"期望404，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试修改商品失败（价格改为0）")
    def test_update_product_price_zero(self, product_factory):
        product_id = product_factory(name="测试", price=10, stock=100)
        response = requests.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"name": "测试", "price": 0, "stock": 100}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试修改商品失败（价格改为负数）")
    def test_update_product_price_negative(self, product_factory):
        product_id = product_factory(name="测试", price=10, stock=100)
        response = requests.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"name": "测试", "price": -1, "stock": 100}
        )
        assert response.status_code == 422, f"期望422，实际{response.status_code}"

    @allure.story("商品管理")
    @allure.title("测试删除商品失败（商品不存在）")
    def test_delete_product_not_exists(self):
        response = requests.delete(f"{BASE_URL}/api/products/9999")
        assert response.status_code == 404, f"期望404，实际{response.status_code}"