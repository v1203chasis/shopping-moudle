from db_helper import db

def create_user_in_db(username,password):
    """在数据库中创建新用户，返回新生成的id"""
    new_user_id = db.execute_update("INSERT INTO users (username,password) VALUES (?,?)",(username,password))
    return new_user_id

def get_all_users():
    """查询所有用户，返回字典列表"""
    return db.execute_query("SELECT id, username FROM users")


def get_user_by_username(usernsme):
    """根据 ID 查询单个用户，返回字典或 None"""
    rows = db.execute_query(
         "SELECT id, username,password FROM users WHERE username = ?",
         (usernsme,))
#如果查到了，返回第一条数据；如果没查到，返回 None
    return rows[0] if rows else None


def delete_user_from_db(user_id):
    """删除用户，返回 True 表示成功，False表示不存在"""
    #先查是否存在
    rows = db.execute_query("SELECT id FROM users WHERE id = ?",(user_id,))
    if not rows:
        return False#不存在，直接返回 False
    #存在，执行删除
    db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
    return True

def update_user_in_db(user_id, username, password):
    """更新用户信息，返回 True表示成功，False 表示商品不存在"""
    # 1. 先检查用户是否存在
    rows = db.execute_query("SELECT id FROM users WHERE id = ?",(user_id,))
    if not rows:
        return False #用户不存在，直接返回 False
    # 2. 执行更新
    db. execute_update(
        "UPDATE users SET username = ?, password = ? WHERE id = ?",(username,password,user_id))
    return True