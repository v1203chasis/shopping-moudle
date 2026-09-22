# 电商后端系统 - 测试用例文档

## 文档信息
| 项目 | 内容 |
| :--- | :--- |
| **项目名称** | 电商后端系统 |
| **测试模块** | 用户 / 商品 / 购物车 / 订单 |
| **测试类型** | 接口自动化测试 |
| **测试框架** | Pytest + Requests |
| **编写日期** | 2026-09-21 |
| **用例总数** | 52 条 |

---

## 一、订单模块测试用例（TC-ORDER）

| 用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **TC-ORDER-001** | 下单成功，验证订单落库和库存扣减 | P0 | 用户存在、商品库存=100 | 1. POST /api/orders {user_id, product_id, quantity=2}<br>2. GET /api/orders/{order_id}<br>3. 查数据库 orders 表<br>4. 查数据库 products 表 | 1. 状态码 200，返回 order_id<br>2. 状态码 200，quantity=2，total_price=50.0<br>3. 订单记录存在，status='created'<br>4. 库存从 100 变成 98 |
| **TC-ORDER-002** | 查询单个订单详情 | P1 | 订单已存在 | 1. GET /api/orders/{order_id} | 状态码 200，返回订单详情，字段与创建时一致 |
| **TC-ORDER-003** | 查询用户的所有订单 | P1 | 用户有 1 条订单 | 1. GET /api/orders?user_id={user_id} | 状态码 200，列表长度=1，包含目标 order_id |
| **TC-ORDER-004** | 取消订单，验证状态变更和库存回滚 | P0 | 订单已创建，商品库存=45 | 1. PUT /api/orders/{order_id}/cancel<br>2. 查数据库 orders 表<br>3. 查数据库 products 表 | 1. 状态码 200，status='cancelled'<br>2. 订单 status='cancelled'<br>3. 库存从 45 回滚到 50 |
| **TC-ORDER-005** | 下单失败：数量为 0 | P1 | 无 | 1. POST /api/orders {quantity=0} | 状态码 422（Pydantic 拦截），不查数据库 |
| **TC-ORDER-006** | 下单失败：数量为负数 | P1 | 无 | 1. POST /api/orders {quantity=-1} | 状态码 422 |
| **TC-ORDER-007** | 下单失败：user_id 为负数 | P2 | 无 | 1. POST /api/orders {user_id=-1} | 状态码 422 |
| **TC-ORDER-008** | 下单失败：商品 ID 为负数 | P2 | 无 | 1. POST /api/orders {product_id=-1} | 状态码 422 |
| **TC-ORDER-009** | 下单失败：缺少数量字段 | P2 | 无 | 1. POST /api/orders {user_id, product_id} | 状态码 422 |
| **TC-ORDER-010** | 下单失败：用户不存在 | P0 | 商品存在，user_id=99999 | 1. POST /api/orders | 状态码 404，msg="用户不存在" |
| **TC-ORDER-011** | 下单失败：商品不存在 | P0 | 用户存在，product_id=99999 | 1. POST /api/orders | 状态码 404，msg="商品不存在" |
| **TC-ORDER-012** | 下单失败：库存不足 | P0 | 用户存在，商品库存=5，quantity=10 | 1. POST /api/orders | 状态码 400，msg="库存不足" |
| **TC-ORDER-013** | 取消订单失败：订单不存在 | P1 | 无 | 1. PUT /api/orders/99999/cancel | 状态码 404，msg="订单不存在" |
| **TC-ORDER-014** | 取消订单失败：订单已取消 | P1 | 订单已取消 | 1. 再次 PUT /api/orders/{order_id}/cancel | 状态码 400，msg="该订单状态不允许取消" |

---

## 二、用户模块测试用例（TC-USER）

| 用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **TC-USER-001** | 注册新用户成功 | P0 | 用户名未被占用 | 1. POST /api/register<br>2. 查数据库 users 表 | 1. 状态码 200，返回 user_id<br>2. 用户记录存在 |
| **TC-USER-002** | 重复注册失败 | P1 | 用户名已存在 | 1. POST /api/register（同名） | 状态码 400，msg="用户已存在" |
| **TC-USER-003** | 登录成功 | P0 | 用户已注册 | 1. POST /api/login（正确账号密码） | 状态码 200，返回 username 和 token |
| **TC-USER-004** | 登录失败：用户名为空 | P1 | 无 | 1. POST /api/login {username=""} | 状态码 422 |
| **TC-USER-005** | 登录失败：密码为空 | P1 | 无 | 1. POST /api/login {password=""} | 状态码 422 |
| **TC-USER-006** | 登录失败：用户名超长（51字符） | P2 | 无 | 1. POST /api/login {username="a"*51} | 状态码 422 |
| **TC-USER-007** | 登录失败：密码超长（101字符） | P2 | 无 | 1. POST /api/login {password="a"*101} | 状态码 422 |

---

## 三、商品模块测试用例（TC-PRODUCT）

| 用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **TC-PRODUCT-001** | 创建商品成功，三重验证 | P0 | 无 | 1. 创建商品<br>2. 查接口<br>3. 查数据库 | 1. 状态码 200<br>2. 数据一致<br>3. 数据库有记录 |
| **TC-PRODUCT-002** | 修改商品成功 | P1 | 商品已存在 | 1. PUT 修改<br>2. 查接口<br>3. 查数据库 | 数据被正确更新 |
| **TC-PRODUCT-003** | 创建失败：价格为 0 | P1 | 无 | 1. POST {price=0} | 状态码 422 |
| **TC-PRODUCT-004** | 创建失败：价格为负数 | P1 | 无 | 1. POST {price=-1} | 状态码 422 |
| **TC-PRODUCT-005** | 创建成功：价格最小值 0.01 | P2 | 无 | 1. POST {price=0.01} | 状态码 200 |
| **TC-PRODUCT-006** | 创建失败：库存为负数 | P1 | 无 | 1. POST {stock=-1} | 状态码 422 |
| **TC-PRODUCT-007** | 创建失败：名称为空 | P1 | 无 | 1. POST {name=""} | 状态码 422 |
| **TC-PRODUCT-008** | 查询失败：商品不存在 | P1 | 无 | 1. GET /api/products/99999 | 状态码 404 |
| **TC-PRODUCT-009** | 修改失败：商品不存在 | P1 | 无 | 1. PUT /api/products/99999 | 状态码 404 |
| **TC-PRODUCT-010** | 删除失败：商品不存在 | P1 | 无 | 1. DELETE /api/products/99999 | 状态码 404 |

---

## 四、购物车模块测试用例（TC-CART）

| 用例编号 | 用例标题 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **TC-CART-001** | 加入购物车成功，双重验证 | P0 | 用户和商品存在 | 1. POST /api/cart<br>2. 查接口<br>3. 查数据库 | 1. 状态码 200<br>2. 数据一致<br>3. carts 表有记录 |
| **TC-CART-002** | 查询购物车 | P1 | 购物车有商品 | 1. GET /api/cart?user_id=1 | 状态码 200，返回购物车列表 |
| **TC-CART-003** | 修改购物车数量 | P1 | 购物车有商品 | 1. PUT /api/cart/{id} {quantity=5} | 状态码 200，数量更新 |
| **TC-CART-004** | 删除购物车商品 | P1 | 购物车有商品 | 1. DELETE /api/cart/{id} | 状态码 200，数据库记录删除 |
| **TC-CART-005** | 清空购物车 | P1 | 购物车有多个商品 | 1. DELETE /api/cart?user_id=1 | 状态码 200，购物车为空 |
| **TC-CART-006** | 加购失败：库存不足 | P0 | 商品库存=10，quantity=99999 | 1. POST /api/cart | 状态码 400 |
| **TC-CART-007** | 加购失败：用户不存在 | P1 | user_id=99999 | 1. POST /api/cart | 状态码 404 |
| **TC-CART-008** | 加购失败：商品不存在 | P1 | product_id=99999 | 1. POST /api/cart | 状态码 404 |
| **TC-CART-009** | 加购失败：数量为0 | P2 | 无 | 1. POST {quantity=0} | 状态码 422 |
| **TC-CART-010** | 加购失败：数量为负 | P2 | 无 | 1. POST {quantity=-1} | 状态码 422 |

---

## 📊 测试用例统计

| 模块 | 用例数 | P0 | P1 | P2 |
| :--- | :---: | :---: | :---: | :---: |
| 订单模块 | 14 | 5 | 6 | 3 |
| 用户模块 | 7 | 2 | 3 | 2 |
| 商品模块 | 10 | 1 | 6 | 3 |
| 购物车模块 | 10 | 2 | 5 | 3 |
| **总计** | **41** | **10** | **20** | **11** |