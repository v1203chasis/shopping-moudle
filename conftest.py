import pytest
import requests

# 后端的基础地址
BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture
def product_factory():
    """
    这个 fixture 就像一个工厂：
    1. 测试开始前，自动造一个商品（前置）。
    2. 测试结束后，自动把造的商品删掉（后置）。
    """
    created_ids = []  # 记录本次测试创建了哪些商品ID，方便后面清理

    # 定义一个内部函数，供测试用例调用，用来“创建商品”
    def _create_product(name, price, stock=0): # 加上 stock 参数
        response = requests.post(
            f"{BASE_URL}/api/products",
            json={"name": name, "price": price, "stock": stock} # 传给后端
        )
        
        assert response.status_code == 200, "创建商品失败"
        product_id = response.json()["data"]["id"]
        created_ids.append(product_id)  # 记录下来
        return product_id

    # 把创建商品的函数交出去（yield 之前的代码是前置）
    yield _create_product

    # 下面是后置清理（yield 之后的代码）
    # 测试跑完后，把我们造出来的商品都删掉，还数据库一个清净
    for pid in created_ids:
        requests.delete(f"{BASE_URL}/api/products/{pid}")