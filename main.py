from fastapi import FastAPI
from pydantic import BaseModel,Field
from database import init_db
from db_helper import db  # ✅ 这样才正确
import crud_product 
import crud_user
import crud_cart
import crud_order
from fastapi import HTTPException

# 启动时初始化数据库
init_db()

app = FastAPI()

class ProductCreate(BaseModel):
    name: str=Field(...,min_length=1,max_length=50)
    price: float=Field(...,gt=0)
    stock: int = Field(...,ge=0)

@app.post("/api/products")
def create_product(product: ProductCreate):
    new_id = crud_product.create_product_in_db(product.name, product.price, product.stock)
    return {
        "msg": "商品添加成功！",
        "data": {"id": new_id, "name": product.name, "price": product.price, "stock": product.stock}
    }

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    product = crud_product.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"msg": "获取成功", "data": product}


@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductCreate):
    success = crud_product.update_product_in_db(
        product_id, product.name, product.price, product.stock
    )
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")  # ✅ 抛出真正的 HTTP 404
    return {
        "msg": "商品修改成功！",
        "data": {
            "id": product_id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock
        }
    }


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    success = crud_product.delete_product_from_db(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"msg": "删除成功", "data": {"id": product_id}}

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


@app.post("/api/register")
def register(user: UserCreate):
    existing_user = crud_user.get_user_by_username(user.username)
    if existing_user is not None:
        return {"msg":"用户已存在","code":400}
    new_user_id = crud_user.create_user_in_db(user.username,user.password)
    return {
        "msg":"注册成功！",
        "data":{"id":new_user_id,"username":user.username}
    }


@app.post("/api/login")
def login(user: UserCreate):
    db_user = crud_user.get_user_by_username(user.username)
    if  not db_user or db_user["password"] != user.password:
        return {"msg":"用户名或密码错误","code":401}
    return{
        "msg":"登录成功！",
        "data":{"id":db_user["id"],"username":db_user["username"]}
    }


class CartCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


@app.post("/api/cart")
def add_to_cart(req: CartCreate):
    result = crud_cart.add_to_cart(req.user_id, req.product_id, req.quantity)

    # 把业务码转成 HTTP 状态码
    if result.get("code") != 200:
        raise HTTPException(status_code=result.get("code"), detail=result.get("msg"))

    return result


@app.get("/api/cart")
def get_cart(user_id: int):
    return crud_cart.get_cart(user_id)


from fastapi import HTTPException  # 确保文件顶部有导入这个

@app.put("/api/cart/{cart_id}")
def update_cart(cart_id: int, req: CartUpdate):
    result = crud_cart.update_cart_quantity(cart_id, req.quantity)
    if result.get("code") != 200:
        raise HTTPException(status_code=result.get("code"), detail=result.get("msg"))
    return result


@app.delete("/api/cart/{cart_id}")
def delete_cart(cart_id: int):
    result = crud_cart.delete_cart_item(cart_id)
    if result.get("code") != 200:
        raise HTTPException(status_code=result.get("code"), detail=result.get("msg"))
    return result


@app.delete("/api/cart")
def clear_cart(user_id: int):
    return crud_cart.clear_cart(user_id)


# ==================== 订单模块 ====================

class OrderCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

# ==================== 订单接口 ====================

@app.post("/api/orders")
def create_order_api(req: OrderCreate):
    """创建订单（下单）"""
    result = crud_order.create_order(req.user_id, req.product_id, req.quantity)

    # 模式二：解析后再抛出
    if result["code"] != 200:
        raise HTTPException(status_code=result["code"], detail=result["msg"])
    return result


@app.get("/api/orders/{order_id}")
def get_order_api(order_id: int):
    """查询单个订单"""
    order = crud_order.get_order_by_id(order_id)

    # 模式一：直接抛出
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"msg": "获取成功", "data": order}


@app.get("/api/orders")
def get_user_orders_api(user_id: int):
    """查询某个用户的所有订单"""
    orders = crud_order.get_user_orders(user_id)
    return {"msg": "获取成功", "data": orders}


@app.put("/api/orders/{order_id}/cancel")
def cancel_order_api(order_id: int):
    """取消订单"""
    result = crud_order.cancel_order(order_id)

    # 模式二：解析后再抛出
    if result["code"] != 200:
        raise HTTPException(status_code=result["code"], detail=result["msg"])
    return result


