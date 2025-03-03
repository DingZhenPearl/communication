# 创建一个新文件保存常见食物的营养成分

COMMON_FOODS = {
    # "白米饭": {
    #     "food_category": "谷物",
    #     "calorie_per_100g": 116,
    #     "protein_per_100g": 2.6,
    #     "fat_per_100g": 0.3,
    #     "carbs_per_100g": 25.5,
    #     "fiber_per_100g": 0.4
    # },
    # "馒头": {
    #     "food_category": "谷物",
    #     "calorie_per_100g": 223,
    #     "protein_per_100g": 6.5,
    #     "fat_per_100g": 0.8,
    #     "carbs_per_100g": 47.0,
    #     "fiber_per_100g": 1.3
    # },
    # "苹果": {
    #     "food_category": "水果",
    #     "calorie_per_100g": 52,
    #     "protein_per_100g": 0.3,
    #     "fat_per_100g": 0.2,
    #     "carbs_per_100g": 14.0,
    #     "fiber_per_100g": 2.4
    # },
    # "鸡胸肉": {
    #     "food_category": "肉类",
    #     "calorie_per_100g": 165,
    #     "protein_per_100g": 31.0,
    #     "fat_per_100g": 3.6,
    #     "carbs_per_100g": 0.0,
    #     "fiber_per_100g": 0.0
    # }
    # 可以继续添加更多常见食物
}

def get_food_info(food_name):
    """根据食物名称获取营养成分信息"""
    # 尝试完全匹配
    if food_name in COMMON_FOODS:
        return COMMON_FOODS[food_name]
    
    # 尝试部分匹配
    for name, info in COMMON_FOODS.items():
        if name in food_name or food_name in name:
            return info
    
    # 没有匹配到，返回None
    return None