# 电商后端系统 & 接口自动化测试框架

基于 FastAPI + Pytest + Requests + SQLite 搭建的电商后端系统，配套完整的接口自动化测试用例。

## 🛠️ 技术栈

- **后端**：FastAPI + Pydantic + SQLite
- **测试**：Pytest + Requests + Allure
- **数据库校验**：直连 SQLite 做双层验证

## 📂 项目结构
shopping_moudle/
├── main.py # FastAPI 入口，所有 API 路由
├── database.py # 数据库建表脚本
├── db_helper.py # 数据库操作封装
├── crud_user.py # 用户模块 CRUD
├── crud_product.py # 商品模块 CRUD
├── crud_cart.py # 购物车模块 CRUD
├── crud_order.py # 订单模块 CRUD
├── conftest.py # Pytest 全局 Fixture（数据工厂）
├── pytest.ini # Pytest 配置
├── test_user_api.py # 用户模块测试
├── test_products_api.py # 商品模块测试
├── test_cart_api.py # 购物车模块测试
├── test_order_api.py # 订单模块测试
└── requirements.txt # 依赖清单


## 🚀 快速开始

### 1. 安装依赖
pip install -r requirements.txt

### 2. 启动后端服务
uvicorn main:app --reload

### 3. 运行测试
pytest -v

### 4. 生成 Allure 报告（可选）
pytest --alluredir=report/allure-results
allure serve report/allure-results

✅ 测试覆盖
用户模块：注册、登录（成功 + 参数校验 + 业务异常）

商品模块：创建、查询、修改、删除（正向 + 边界 + 异常）

购物车模块：加购、查询、修改数量、删除、清空

订单模块：下单、查询、取消（含库存回滚）

共 60+ 条测试用例，全部通过。

🎯 设计亮点
三层校验：Pydantic 参数校验 -> CRUD 业务校验 -> 数据库落库校验

数据工厂：conftest.py 中用 yield 实现测试数据自动创建与清理

级联删除：购物车表用 ON DELETE CASCADE，订单表保护交易凭证

两种错误处理模式：查询类接口用 None 直抛，业务类接口用字典解析后再抛




