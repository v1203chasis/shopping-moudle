# 测试用例设计实战指南（基于电商后端系统）

> 本文档基于 `shopping-moudle` 项目的实战经验，系统总结六大测试用例设计方法，并配以真实代码案例。

## 🎯 设计方法总览

| 方法 | 核心思想 | 在本项目中的应用 |
| :--- | :--- | :--- |
| **等价类划分** | 输入数据分“有效/无效”两组，各取代表值 | 商品价格、用户ID |
| **边界值分析** | 测试数据的最小值、最大值、临界值 | 价格 0.01、库存 0、用户名超长 |
| **场景法** | 模拟用户真实操作流程 | 下单 -> 查订单 -> 查库存 |
| **错误推测法** | 凭经验和直觉预测可能出错的地方 | 空名称、重复取消订单 |
| **状态迁移法** | 测试对象在多状态间切换是否正确 | 订单状态：created -> cancelled |
| **判定表法** | 多输入条件组合决定结果的场景 | 下单接口的三层校验 |

---

### 从 Pydantic 规则推导测试用例

设计测试用例时，先看 Pydantic 的规则，再推导等价类和边界值：

| Pydantic 规则 | 等价类划分 | 边界值选取 |
| :--- | :--- | :--- |
| `price > 0` | 正数 / 零 / 负数 | 0.01, 0, -1 |
| `stock >= 0` | 非负 / 负数 | 0, -1 |
| `username.min_length = 1` | 非空 / 空 | "a", "" |
| `username.max_length = 50` | 合法 / 超长 | "a"*50, "a"*51 |


## 📘 一、等价类划分

### 理论定义
把输入数据的范围划分为若干个“等价类”，从每个类中选一个代表数据作为测试用例。因为同一个类中的数据，测试结果应该是一致的。

### 项目实战：商品价格校验

**有效等价类**：`price > 0`，代表值 `12.99`，期望 200。
**无效等价类**：`price <= 0`，代表值 `0` 和 `-1`，期望 422。

```python
@pytest.mark.parametrize("name, price, stock", [
    ("猪猪玩偶", 12.99, 50),      # 有效等价类
    ("测试0库存商品", 9.9, 0),     # 边界有效
])
def test_create_product_and_verify_db(self, product_factory, name, price, stock):
    ...

def test_create_product_price_zero(self):      # 无效等价类
    ...

def test_create_product_price_negative(self):  # 无效等价类
    ...

## 📘 二、边界值分析
理论定义
大量 Bug 发生在输入范围的边界上。要专门测试“最小值、最大值、刚好越过边界的值”。

项目实战：价格与库存
场景	边界值	期望	对应测试用例
价格最小值	0.01	200	test_create_product_price_min
价格非法边界	0	422	test_create_product_price_zero
库存最小值	0	200	test_create_product_stock_zero
库存非法边界	-1	422	test_create_product_stock_negative
用户名最大长度	50 字符	200	（正常注册）
用户名越界	51 字符	422	test_login_username_too_long

📘 三、场景法
理论定义
模拟用户真实操作的一连串流程，验证端到端的正确性。

项目实战：下单全链路
用户视角的场景：浏览商品 -> 加购 -> 下单 -> 查看订单 -> 取消订单。

对应测试用例：test_create_order 模拟了“下单 -> 查订单 -> 查数据库 -> 验证库存扣减”的完整链路。

python
def test_create_order(self, order_factory):
    # 1. 准备数据（下单）
    order_info = order_factory(product_name="下单测试商品", price=25.0, stock=100, quantity=2)
    
    # 2. 查订单详情
    response = requests.get(f"{BASE_URL}/api/orders/{order_info['order_id']}")
    
    # 3. 查数据库，验证落库
    db_orders = db.execute_query("SELECT ... FROM orders WHERE id = ?", (order_id,))
    
    # 4. 验证库存扣减
    db_product = db.execute_query("SELECT stock FROM products WHERE id = ?", (product_id,))
    assert db_product[0]["stock"] == 98
📘 四、错误推测法
理论定义
基于测试经验，推测程序可能在哪里出错，然后有针对性地设计测试用例。

项目实战：常见异常场景
错误推测	测试用例
用户会传空名称吗？	test_create_product_name_empty
用户会重复取消订单吗？	test_cancel_order_already_cancelled
订单不存在时会怎样？	test_cancel_order_not_exists
数量会传 0 或负数吗？	test_create_order_quantity_zero / test_create_order_quantity_negative
库存为0时能下单吗？	test_create_order_stock_insufficient
📘 五、状态迁移法
理论定义
当被测对象有多个状态时，要测试状态之间的合法切换和非法切换。

项目实战：订单状态
订单状态：created（已创建）-> cancelled（已取消）。

合法迁移：created -> cancelled（测试用例：test_cancel_order）

非法迁移：cancelled -> cancelled（测试用例：test_cancel_order_already_cancelled）

python
def test_cancel_order_already_cancelled(self, order_factory):
    order_info = order_factory(...)
    # 第一次取消，成功（合法迁移）
    response1 = requests.put(f"{BASE_URL}/api/orders/{order_info['order_id']}/cancel")
    assert response1.status_code == 200
    
    # 第二次取消，失败（非法迁移）
    response2 = requests.put(f"{BASE_URL}/api/orders/{order_info['order_id']}/cancel")
    assert response2.status_code == 400
📘 六、判定表法
理论定义
当多个输入条件组合决定结果时，用表格列出所有组合，确保每种组合都被覆盖。

项目实战：下单接口的三层校验
用户存在？	商品存在？	库存足够？	结果	对应测试用例
✅	✅	✅	200	test_create_order
✅	✅	❌	400	test_create_order_stock_insufficient
✅	❌	-	404	test_create_order_product_not_exists
❌	-	-	404	test_create_order_user_not_exists
注意：表中的 - 表示“该条件不需要校验”，因为前一个条件已经失败，后端会直接返回。

🎯 总结：参数化与变量隔离
判断“能否参数化”的标准
条件	能否参数化
逻辑完全相同，只是输入数据不同	✅ 可以（如参数校验）
前置条件完全相同，比对对象相同	✅ 可以（如登录失败场景）
前置条件不同（造用户 vs 造商品）	❌ 不可以（如业务逻辑异常）
需要加 if/else 区分场景	❌ 不可以（本质不同）
变量隔离原则
一个测试只让一个条件失败。 这样当测试 FAILED 时，能精确定位是哪里出了问题。

例如：

测“用户不存在”时，造商品但不造用户，让 404 只可能来自用户。

测“商品不存在”时，造用户但不造商品，让 404 只可能来自商品。

📚 附录：知识关联
本文档与 test_order_api.py、test_products_api.py、test_user_api.py 中的用例一一对应。

建议搭配阅读：附录10：FastAPI 异常处理与分层设计指南。

text

---

### 🛠️ 第三步：保存并推送到 GitHub

文档写好后，在终端执行：

git add .
git commit -m "docs: 添加测试用例设计实战指南"
git push
