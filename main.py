from fastapi import FastAPI
from pydantic import BaseModel,Field
from database import init_db
from db_helper import db  # ✅ 这样才正确
import crud_product 
import crud_user

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

@app.get("/api/products")
def get_products():
    return {"msg": "获取成功", "data": crud_product.get_all_products()}

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    # 👇 改成调用专门查单个商品的函数
    product = crud_product.get_product_by_id(product_id)
    if not product:
        return {"msg": "商品不存在", "code": 404}
    return {"msg": "获取成功", "data": product}


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    success = crud_product.delete_product_from_db(product_id)
    if not success:
        return {"msg": "商品不存在", "code": 404}
    return {"msg": "删除成功", "data": {"id": product_id}}


@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductCreate):
    # 调用 crud_product 的更新逻辑
    success = crud_product.update_product_in_db(
        product_id, product.name, product.price, product.stock
    )
    
    if not success:
        return {"msg": "商品不存在", "code": 404}
    
    return {
        "msg": "商品修改成功！",
        "data": {
            "id": product_id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock
        }
    }

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

