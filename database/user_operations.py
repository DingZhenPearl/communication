import sys
import json
import argparse
from db_operation import DatabaseManager
import hashlib
import mysql.connector

def register_user(username, password, email, gender=None, birth_date=None, 
                 height=None, weight=None, target_weight=None, daily_calorie_goal=None):
    """注册新用户"""
    
    print(f"Python收到注册参数: username={username}, email={email}, gender={gender}, birth_date={birth_date}, height={height}, target_weight={target_weight}", file=sys.stderr)
    
    # 验证必填字段
    if not username or not password or not email:
        return {"success": False, "error": "用户名、密码和邮箱为必填项"}
    
    # 处理空字符串参数
    if gender == '':
        gender = None
        
    if birth_date == '':
        birth_date = None
    else:
        # 尝试验证日期格式
        try:
            if birth_date:
                import datetime
                datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError as e:
            return {"success": False, "error": f"出生日期格式错误: {str(e)}"}
    
    if target_weight == '':
        target_weight = None
    
    # 安全转换数值类型
    try:
        height_float = None
        if height and height != '':
            height_float = float(height)
            
        weight_float = None
        if weight and weight != '':
            weight_float = float(weight)
            
        target_weight_float = None
        if target_weight and target_weight != '':
            target_weight_float = float(target_weight)
            
        calorie_goal_int = None
        if daily_calorie_goal and daily_calorie_goal != '':
            calorie_goal_int = int(daily_calorie_goal)
            
        print(f"转换后的值: height_float={height_float}, weight_float={weight_float}, target_weight_float={target_weight_float}, goal={calorie_goal_int}", file=sys.stderr)
    except ValueError as e:
        print(f"值转换错误: {str(e)}", file=sys.stderr)
        return {"success": False, "error": f"数值转换错误: {str(e)}"}
    
    # 简单加密密码
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    db = DatabaseManager()
    if db.connect():
        try:
            # 检查用户名是否已存在
            existing_user = db.get_user_by_username(username)
            if existing_user:
                return {"success": False, "error": "用户名已存在"}
            
            # 检查邮箱是否已存在
            cursor = db.connection.cursor(dictionary=True)
            try:
                query = "SELECT * FROM users WHERE email = %s"
                cursor.execute(query, (email,))
                existing_email = cursor.fetchone()
                if existing_email:
                    return {"success": False, "error": "邮箱已被注册"}
            finally:
                cursor.close()
            
            # 添加用户
            try:
                user_id = db.add_user(
                    username=username,
                    password=hashed_password,
                    email=email,
                    gender=gender,
                    birth_date=birth_date,
                    height=height_float,
                    weight=weight_float,
                    target_weight=target_weight_float,
                    daily_calorie_goal=calorie_goal_int
                )
                
                if user_id:
                    print(f"用户添加成功，ID: {user_id}", file=sys.stderr)
                    return {
                        "success": True,
                        "message": "用户注册成功",
                        "user_id": user_id
                    }
                else:
                    print("添加用户失败", file=sys.stderr)
                    return {"success": False, "error": "用户注册失败"}
            except mysql.connector.Error as sql_err:
                print(f"SQL错误: {str(sql_err)}", file=sys.stderr)
                if sql_err.errno == 1062:  # 重复键值错误
                    return {"success": False, "error": "用户名或邮箱已被注册"}
                else:
                    return {"success": False, "error": f"数据库错误: {str(sql_err)}"}
        except Exception as e:
            print(f"注册异常: {str(e)}", file=sys.stderr)
            return {"success": False, "error": f"注册处理错误: {str(e)}"}
        finally:
            db.disconnect()
    
    return {"success": False, "error": "数据库连接失败"}

def login_user(username, password):
    """用户登录"""
    # 简单加密密码
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    db = DatabaseManager()
    if db.connect():
        try:
            # 获取用户信息
            user = db.get_user_by_username(username)
            
            if not user:
                return {"success": False, "error": "用户不存在"}
            
            if user['password'] != hashed_password:
                return {"success": False, "error": "密码不正确"}
            
            # 登录成功，返回用户信息(不包含密码)
            user_info = {k: v for k, v in user.items() if k != 'password'}
            
            return {
                "success": True,
                "message": "登录成功",
                "user": user_info
            }
        finally:
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

def get_user_diet_records(user_id, date=None, start_date=None, end_date=None):
    """获取用户饮食记录"""
    db = DatabaseManager()
    if db.connect():
        try:
            cursor = db.connection.cursor(dictionary=True)
            
            if date:
                # 获取特定日期的记录
                query = """
                    SELECT dr.*, f.food_name, f.food_category, f.calorie_per_100g
                    FROM diet_records dr
                    JOIN foods f ON dr.food_id = f.food_id
                    WHERE dr.user_id = %s AND DATE(dr.record_time) = %s
                    ORDER BY dr.record_time DESC
                """
                cursor.execute(query, (user_id, date))
            elif start_date and end_date:
                # 获取日期范围的记录
                query = """
                    SELECT dr.*, f.food_name, f.food_category, f.calorie_per_100g
                    FROM diet_records dr
                    JOIN foods f ON dr.food_id = f.food_id
                    WHERE dr.user_id = %s AND DATE(dr.record_time) BETWEEN %s AND %s
                    ORDER BY dr.record_time DESC
                """
                cursor.execute(query, (user_id, start_date, end_date))
            else:
                # 获取所有记录
                query = """
                    SELECT dr.*, f.food_name, f.food_category, f.calorie_per_100g
                    FROM diet_records dr
                    JOIN foods f ON dr.food_id = f.food_id
                    WHERE dr.user_id = %s
                    ORDER BY dr.record_time DESC
                """
                cursor.execute(query, (user_id,))
                
            records = cursor.fetchall()
            
            # 处理日期/时间为字符串
            for record in records:
                for key, value in record.items():
                    if isinstance(value, (bytes, bytearray)):
                        record[key] = value.decode('utf-8')
            
            return {
                "success": True,
                "user_id": int(user_id),
                "records": records
            }
        except Exception as e:
            return {"success": False, "error": f"获取饮食记录失败: {str(e)}"}
        finally:
            cursor.close()
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='用户操作工具')
    parser.add_argument('command', help='要执行的命令')
    parser.add_argument('args', nargs='*', help='命令参数')
    parser.add_argument('--date', help='指定日期')
    parser.add_argument('--start-date', help='开始日期')
    parser.add_argument('--end-date', help='结束日期')
    
    args = parser.parse_args()
    
    result = {"success": False, "error": "未知命令"}
    
    if args.command == "register_user" and len(args.args) >= 3:
        result = register_user(*args.args)
    elif args.command == "login_user" and len(args.args) == 2:
        result = login_user(*args.args)
    elif args.command == "get_user_diet_records" and len(args.args) == 1:
        result = get_user_diet_records(args.args[0], args.date, args.start_date, args.end_date)
    
    print(json.dumps(result))