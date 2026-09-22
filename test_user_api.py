import pytest
import requests
import allure
from db_helper import db
from jsonpath_ng import parse
import jsonschema

BASE_URL = "http://127.0.0.1:8000"

@allure.epic("电商后端系统")
@allure.feature("用户管理模块")
@pytest.mark.user
class TestUserAPI:

    @allure.story("用户注册")
    @allure.title("测试注册新用户：{username}")
    @pytest.mark.smoke
    @pytest.mark.parametrize("username, password", [
        ("小猪", "pass123"),
        ("小深", "pass456"),
        ])
    def test_register(self, user_factory, username, password):
        user_id = user_factory(username=username, password=password)

        db_rows = db.execute_query(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,)
        )
        assert len(db_rows) == 1, "数据库里没有找到刚刚注册的用户！"
        assert db_rows[0]["username"] == username
        
        print(f"\n✅ 用户 {username} 注册验证通过！")



    @allure.story("用户注册")
    @allure.title("测试重复注册（用户名已存在）")
    @pytest.mark.smoke
    def test_register_duplicate(self, user_factory):
        # 1. 先注册一个用户
        user_factory(username="duplicate_user", password="123456")
        
        # 2. 用同样的用户名再注册一次
        response = requests.post(
            f"{BASE_URL}/api/register",
            json={"username": "duplicate_user", "password": "123456"}
        )
        
        # 3. 断言后端返回了“用户已存在”和 400 状态码
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 400
        assert result["msg"] == "用户已存在"
        
        print(f"\n✅ 重复注册被正确拦截了！")

    @allure.story("用户登录")
    @allure.title("测试登录成功：{username}")
    @pytest.mark.smoke
    @pytest.mark.parametrize("username, password", [
        ("login_user_a", "pass_a"),
        ("login_user_b", "pass_b"),
    ])
    def test_login_success(self, user_factory, username, password):
        # 1. 先注册一个用户（通过 factory 自动注册）
        user_factory(username=username, password=password)
        
        # 2. 用正确的用户名和密码去登录
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": username, "password": password}
        )
        
        # 3. 断言登录成功
        assert response.status_code == 200
        result = response.json()
        assert result["msg"] == "登录成功！"
    
        jsonpath_expr = parse("$.data.username")
        match = jsonpath_expr.find(result)
        assert match[0].value == username, "用户名不匹配"
        print(f"\n✅ 用户 {username} 登录成功！")


    @allure.story("用户登录")
    @allure.title("测试登录失败（用户名为空）")
    def test_login_empty_username(self):
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "", "password": "123456"}
        )
        assert response.status_code == 422


    @allure.story("用户登录")
    @allure.title("测试登录失败（密码为空）")
    def test_login_empty_password(self):
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "tom", "password": ""}
        )
        assert response.status_code == 422


    @allure.story("用户登录")
    @allure.title("测试登录失败（用户名超长）")
    def test_login_username_too_long(self):
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "a" * 51, "password": "123456"}
        )
        assert response.status_code == 422


    @allure.story("用户登录")
    @allure.title("测试登录失败（密码超长）")
    def test_login_password_too_long(self):
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "tom", "password": "a" * 101}
        )
        assert response.status_code == 422