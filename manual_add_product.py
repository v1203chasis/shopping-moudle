import requests

# 1. 让商家自己输入信息
print("====== 商家商品添加系统 ======")
user_input_name = input("请输入商品名称：")
user_input_price = input("请输入商品价格：")  # 注意：input() 默认接收的是字符串

# 2. 组装数据（注意要把价格转成浮点数，否则后端会报 422 错误）
payload = {
    "name": user_input_name,
    "price": float(user_input_price)
}

# 3. 发送请求
url = "http://127.0.0.1:8000/api/products"
response = requests.post(url, json=payload)

# 4. 打印结果
print("\n====== 添加结果 ======")
print("状态码:", response.status_code)
print("返回数据:", response.json())