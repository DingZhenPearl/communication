import sys
import json
import datetime
from db_operation import DatabaseManager

def get_user_daily_calories(user_id, date):
    """获取用户指定日期的卡路里摄入总量"""
    db = DatabaseManager()
    if db.connect():
        try:
            total_calories = db.get_user_daily_calories(user_id, date)
            goal_calories = get_user_calorie_goal(db, user_id)
            
            return {
                "success": True,
                "user_id": int(user_id),
                "date": date,
                "total_calories": total_calories,
                "goal_calories": goal_calories,
                "remaining_calories": goal_calories - total_calories if goal_calories else None
            }
        finally:
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

def get_user_calorie_goal(db, user_id):
    """获取用户的目标卡路里摄入量"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        query = "SELECT daily_calorie_goal FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return result['daily_calorie_goal'] if result else None
    except Exception as e:
        db.logger.error(f"Error getting user goal: {e}")
        return None
    finally:
        cursor.close()

def get_exercise_recommendations(user_id, date):
    """根据用户当日卡路里摄入情况，生成运动建议"""
    db = DatabaseManager()
    if db.connect():
        try:
            # 获取用户的卡路里摄入情况
            daily_calories = db.get_user_daily_calories(user_id, date)
            goal_calories = get_user_calorie_goal(db, user_id)
            
            if not goal_calories:
                return {"success": False, "error": "用户未设置卡路里目标"}
            
            # 计算超出或剩余的卡路里
            excess_calories = daily_calories - goal_calories
            
            # 获取用户信息（体重）
            user_info = get_user_info(db, user_id)
            user_weight = user_info.get('weight', 70) if user_info else 70  # 默认70kg
            
            # 根据卡路里情况生成建议
            if excess_calories > 0:
                # 超出卡路里，需要运动消耗
                recommendations = generate_exercise_recommendations(excess_calories, user_weight)
                
                # 保存建议到数据库
                recommendation_id = db.add_exercise_recommendation(
                    user_id=user_id,
                    excess_calories=excess_calories,
                    recommendation_text=json.dumps(recommendations)
                )
                
                return {
                    "success": True,
                    "user_id": int(user_id),
                    "date": date,
                    "excess_calories": excess_calories,
                    "recommendations": recommendations,
                    "recommendation_id": recommendation_id
                }
            else:
                # 未超出卡路里
                return {
                    "success": True,
                    "user_id": int(user_id),
                    "date": date,
                    "remaining_calories": abs(excess_calories),
                    "message": "今日卡路里摄入未超标，可以适当增加食物摄入或保持当前状态。"
                }
        finally:
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

def get_user_info(db, user_id):
    """获取用户信息"""
    try:
        cursor = db.connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
    except Exception as e:
        db.logger.error(f"Error getting user info: {e}")
        return None
    finally:
        cursor.close()

def generate_exercise_recommendations(excess_calories, user_weight):
    """根据超出的卡路里和用户体重生成运动建议"""
    # 常见运动的消耗卡路里（每小时每公斤体重）
    exercises = {
        "步行": 4.0,
        "慢跑": 8.0,
        "跑步": 13.0,
        "游泳": 10.0,
        "骑自行车": 6.0,
        "健身操": 7.5,
        "瑜伽": 4.0,
        "跳绳": 12.0
    }
    
    recommendations = []
    for exercise, calories_per_kg_per_hour in exercises.items():
        # 计算需要的运动时间（分钟）
        calories_per_minute = (calories_per_kg_per_hour * user_weight) / 60
        minutes_needed = round(excess_calories / calories_per_minute)
        
        recommendations.append({
            "exercise_type": exercise,
            "duration_minutes": minutes_needed,
            "calories_burned": excess_calories
        })
    
    # 按运动时间排序，推荐时间较短的运动
    recommendations.sort(key=lambda x: x["duration_minutes"])
    # 只返回前5个建议
    return recommendations[:5]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "缺少参数"}))
        sys.exit(1)
    
    command = sys.argv[1]
    result = {"success": False, "error": "未知命令"}
    
    if command == "get_user_daily_calories" and len(sys.argv) >= 4:
        result = get_user_daily_calories(sys.argv[2], sys.argv[3])
    elif command == "get_exercise_recommendations" and len(sys.argv) >= 4:
        result = get_exercise_recommendations(sys.argv[2], sys.argv[3])
    
    print(json.dumps(result))