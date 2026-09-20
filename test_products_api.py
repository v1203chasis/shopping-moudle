
import pytest
import requests
import allure  # 新增：引入 allure
from db_helper import db

BASE_URL = "http://127.0.0.1:8000"

# 定义测试的大分类
@allure.epic("电商后端系统")
@allure.feature("商品管理模块")
class TestProductAPI:

    @allure.story("添加并查询商品")
    @allure.title("测试添加商品：{name}，价格：{price}")
    @pytest.mark.parametrize("name, price,stock", [
        ("猪猪玩偶", 12.99,50),
        ("deepseek周边", 29.9,100),
        ("测试0库存商品", 9.9, 0)
    ])
    def test_create_product_and_verify_db(self,product_factory,name,price,stock):
        """
        测试用例：创建商品 -> 通过接口查 -> 直接查数据库，三重验证！
        """
    # 1. 创建
        product_id = product_factory(name=name, price=price, stock=stock)
    
    # 2. 通过接口查（GET）
        response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert response.status_code == 200
        api_data = response.json()["data"]

    
        
        assert api_data is not None, "GET 接口查不到刚创建的商品！"
        assert api_data["name"] == name

    # 3. 【超关键一步】直接查数据库，看看“身份证”在不在档案里
        db_rows = db.execute_query(
             "SELECT id, name, price, stock FROM products WHERE id = ?", 
        (product_id,)
    )
    
    # 4. 断言数据库里的数据
        
        assert len(db_rows) == 1, "数据库里找不到这条记录！"
        assert db_rows[0]["name"] == name
        assert db_rows[0]["price"] == price
        assert db_rows[0]["stock"] == stock
    
        print(f"\n✅ 全链路验证通过！ID={product_id} 在 API 和 DB 中均正确。")

    @allure.story("修改商品信息")
    @allure.title("测试修改商品：{name}")
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
                json={"name":new_name, "price": new_price, "stock": new_stock}
                 )
        assert response.status_code == 200, "修改接口返回失败"
        
        # 3. 通过接口查，验证修改后数据是否生效
        get_response = requests.get(f"{BASE_URL}/api/products")
        api_data = get_response.json()["data"]
        target_from_api = next((p for p in api_data if p["id"] == product_id), None)
        
        assert target_from_api["name"] == new_name
        assert target_from_api["price"] == new_price
        assert target_from_api["stock"] == new_stock
        
        # 4. 【超关键一步】直接查数据库，确认修改已落库
        db_rows = db.execute_query(
                "SELECT name, price, stock FROM products WHERE id = ?",
                (product_id,)
            )
        assert db_rows[0]["name"] == new_name
        assert db_rows[0]["price"] == new_price
        assert db_rows[0]["stock"] == new_stock
        
        print(f"\n✅ 商品 {product_id} 修改验证通过！")