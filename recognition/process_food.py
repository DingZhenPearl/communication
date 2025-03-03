import argparse
import json
import time
import os
import sys
from pathlib import Path

# 添加父级目录到路径，以便能够导入数据库操作模块
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.db_operation import DatabaseManager

# 导入智谱AI
try:
    from zhipuai import ZhipuAI
except ImportError:
    print("正在安装zhipuai依赖...")
    os.system("pip install zhipuai")
    from zhipuai import ZhipuAI

# 在开头导入
from food_database import get_food_info

def recognize_food_image(image_path, weight_g):
    """
    使用智谱AI识别食物图像并计算卡路里
    """
    start_time = time.time()
    
    # 初始化智谱AI客户端
    try:
        client = ZhipuAI(api_key="b161ab74893310f851cf1773d822657d.iVHlt3Ymx27C1Iax")  # 这里请使用自己的API密钥
        
        # 读取图片作为base64
        with open(image_path, "rb") as image_file:
            import base64
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 调用智谱AI API进行识别
        response = client.chat.completions.create(
            model="glm-4v-flash",
            messages=[
                {
                  "role": "user", 
                  "content": [
                    {
                      "type": "image_url",
                      "image_url": {
                        "url" : f"data:image/jpeg;base64,{image_base64}"
                      }
                    },
                    {
                      "type": "text",
                      "text": f"""请识别图片中的食物，并以严格的JSON格式返回以下信息：
1. food_name: 食物名称
2. food_category: 食物种类(谷物、蔬菜、水果、肉类、海鲜、乳制品等)
3. calorie_per_100g: 每100克的卡路里含量(必须是数字)
4. protein_per_100g: 每100克的蛋白质含量(必须是数字)
5. fat_per_100g: 每100克的脂肪含量(必须是数字)
6. carbs_per_100g: 每100克的碳水化合物含量(必须是数字)
7. fiber_per_100g: 每100克的纤维含量(必须是数字)

食物重量为{weight_g}g，请也计算出总卡路里。
必须返回JSON格式数据，所有数值必须是数字而非字符串，且不要为0。请查阅标准食物营养成分表提供准确数据。"""
                    }
                  ]
                },
            ],
            stream=False
        )
        
        # 获取响应内容
        response_content = response.choices[0].message.content
        import sys
        print(f"原始响应内容: {response_content}", file=sys.stderr)  # 调试信息输出到stderr
        print(f"智谱AI原始响应: {response_content}", file=sys.stderr)
        
        # 提取JSON部分代码加强处理
        import re

        # 获取响应内容
        response_content = response.choices[0].message.content
        print(f"智谱AI原始响应: {response_content}", file=sys.stderr)

        # 多种方式尝试提取JSON
        json_str = None
        # 尝试方法1: 提取```json```之间的内容
        json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            print(f"方法1提取结果: {json_str}", file=sys.stderr)
        # 尝试方法2: 提取{}之间的内容
        if not json_str:
            json_match = re.search(r'(\{.*\})', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                print(f"方法2提取结果: {json_str}", file=sys.stderr)
        # 尝试方法3: 直接使用原始响应
        if not json_str:
            json_str = response_content

        # 尝试解析JSON
        try:
            food_info = json.loads(json_str)
            print(f"成功解析JSON: {food_info}", file=sys.stderr)
            
            # 验证关键字段是否存在且不为0
            if not food_info.get('calorie_per_100g') or food_info.get('calorie_per_100g') == 0:
                # 尝试从本地数据库获取食物信息
                local_food_info = get_food_info(food_info.get('food_name', ''))
                if local_food_info:
                    food_info.update(local_food_info)
                else:
                    # 设置默认值
                    food_info['calorie_per_100g'] = food_info.get('calorie_per_100g') or 100
                    food_info['protein_per_100g'] = food_info.get('protein_per_100g') or 5
                    food_info['fat_per_100g'] = food_info.get('fat_per_100g') or 3
                    food_info['carbs_per_100g'] = food_info.get('carbs_per_100g') or 10
                    food_info['fiber_per_100g'] = food_info.get('fiber_per_100g') or 2
            
        except Exception as e:
            print(f"JSON解析错误: {e}", file=sys.stderr)
            # 如果解析失败，尝试寻找{}包围的部分
            json_match = re.search(r'{.*}', json_str, re.DOTALL)
            if json_match:
                try:
                    food_info = json.loads(json_match.group(0))
                except:
                    # 如果还是解析失败，创建一个基本的食物信息对象
                    food_info = {
                        "food_name": "未识别食物",
                        "food_category": "其他",
                        "calorie_per_100g": 100,
                        "protein_per_100g": 5,
                        "fat_per_100g": 3,
                        "carbs_per_100g": 10,
                        "fiber_per_100g": 2
                    }
            else:
                return {
                    "success": False,
                    "error": "无法解析识别结果",
                    "processing_time": time.time() - start_time
                }
        
        # 在process_food.py中添加调试信息
        print(f"解析后的食物信息: {food_info}", file=sys.stderr)
        
        # 保存食物信息到数据库
        db = DatabaseManager()
        if db.connect():
            try:
                # 检查食物是否已存在
                cursor = db.connection.cursor(dictionary=True)
                query = "SELECT * FROM foods WHERE food_name = %s"
                cursor.execute(query, (food_info.get('food_name', '未知食物'),))
                existing_food = cursor.fetchone()
                
                if existing_food:
                    food_id = existing_food['food_id']
                else:
                    # 添加新食物
                    food_id = db.add_food(
                        food_name=food_info.get('food_name', '未知食物'),
                        category=food_info.get('food_category', '其他'),
                        calorie_per_100g=food_info.get('calorie_per_100g', 0),
                        protein=food_info.get('protein_per_100g', 0),
                        fat=food_info.get('fat_per_100g', 0),
                        carbs=food_info.get('carbs_per_100g', 0),
                        fiber=food_info.get('fiber_per_100g', 0),
                        image_url=None
                    )
                
                # 计算总卡路里
                weight = float(weight_g)
                calories_per_100g = float(food_info.get('calorie_per_100g', 0))
                total_calories = (calories_per_100g * weight) / 100
                
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "food_id": food_id,
                    "food_name": food_info.get('food_name', '未知食物'),
                    "food_category": food_info.get('food_category', '其他'),
                    "weight_g": weight,
                    "calorie_per_100g": calories_per_100g,
                    "total_calories": total_calories,
                    "nutrition": {
                        "protein": food_info.get('protein_per_100g', 0),
                        "fat": food_info.get('fat_per_100g', 0),
                        "carbs": food_info.get('carbs_per_100g', 0),
                        "fiber": food_info.get('fiber_per_100g', 0)
                    },
                    "confidence_score": 0.85,  # 假设的置信度
                    "processing_time": processing_time
                }
            finally:
                cursor.close()
                db.disconnect()
    except Exception as e:
        return {
            "success": False,
            "error": f"识别过程出错: {str(e)}",
            "processing_time": time.time() - start_time
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='食物图像识别工具')
    parser.add_argument('--image', required=True, help='图像文件路径')
    parser.add_argument('--weight', required=True, help='食物重量(g)')
    
    args = parser.parse_args()
    
    try:
        result = recognize_food_image(args.image, args.weight)
        # 只输出JSON结果到stdout
        print(json.dumps(result))
    except Exception as e:
        # 错误信息输出到stderr
        print(f"主函数错误: {e}", file=sys.stderr)
        # 返回错误的JSON到stdout
        print(json.dumps({
            "success": False,
            "error": f"处理过程出错: {str(e)}"
        }))