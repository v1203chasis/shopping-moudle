# schemas.py

# 订单 Schema
ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "product_id": {"type": "integer"},
        "quantity": {"type": "integer", "minimum": 1},
        "total_price": {"type": "number", "minimum": 0},
        "status": {
            "type": "string",
            "enum": ["created", "paid", "cancelled", "refunded"]
        }
    },
    "required": ["id", "user_id", "product_id", "quantity", "total_price", "status"]
}

# 商品 Schema
PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "price": {"type": "number", "minimum": 0},
        "stock": {"type": "integer", "minimum": 0}
    },
    "required": ["id", "name", "price", "stock"]
}

# 支付记录 Schema
PAYMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "order_id": {"type": "integer"},
        "amount": {"type": "number", "minimum": 0},
        "status": {
            "type": "string",
            "enum": ["pending", "success", "refunded"]
        }
    },
    "required": ["id", "order_id", "amount", "status"]
}

# 支付接口的响应 Schema（简单版）
PAY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {"type": "integer"},
        "status": {"type": "string", "enum": ["paid"]}
    },
    "required": ["order_id", "status"]
}