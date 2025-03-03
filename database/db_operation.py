import mysql.connector
from mysql.connector import Error
from datetime import datetime
import logging
import sys

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'sushiding',  # 替换为你的数据库密码
            'database': 'calorie_monitoring'
        }
        self.connection = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='database.log'
        )
        self.logger = logging.getLogger(__name__)

    def connect(self):
        try:
            # 明确设置字符集和排序规则
            self.config['charset'] = 'utf8mb4'
            self.config['collation'] = 'utf8mb4_unicode_ci'
            self.config['use_unicode'] = True
            
            print(f"尝试连接到数据库: {self.config['host']}/{self.config['database']}", file=sys.stderr)
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                # 确保连接也使用正确的字符集
                cursor = self.connection.cursor()
                cursor.execute('SET NAMES utf8mb4')
                cursor.execute('SET CHARACTER SET utf8mb4')
                cursor.execute('SET character_set_connection=utf8mb4')
                cursor.close()
                
                db_info = self.connection.get_server_info()
                print(f"已连接到MySQL服务器版本 {db_info}", file=sys.stderr)
                self.logger.info(f"Successfully connected to MySQL database version {db_info}")
                return True
        except Error as e:
            error_msg = f"Error connecting to MySQL: {e}"
            print(error_msg, file=sys.stderr)
            self.logger.error(error_msg)
            # 如果是"数据库不存在"错误，则创建数据库
            if e.errno == 1049:  # 未知数据库
                try:
                    print("尝试创建数据库...", file=sys.stderr)
                    conn = mysql.connector.connect(
                        host=self.config['host'],
                        user=self.config['user'],
                        password=self.config['password']
                    )
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    conn.close()
                    print(f"数据库 {self.config['database']} 已创建，请再次尝试连接", file=sys.stderr)
                except Error as create_err:
                    print(f"创建数据库失败: {create_err}", file=sys.stderr)
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("Database connection closed")

    # 用户相关操作
    def add_user(self, username, password, email, gender=None, birth_date=None, 
                 height=None, weight=None, target_weight=None, daily_calorie_goal=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO users (username, password, email, gender, birth_date, 
                                 height, weight, target_weight, daily_calorie_goal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (username, password, email, gender, birth_date, 
                     height, weight, target_weight, daily_calorie_goal)
            cursor.execute(query, values)
            self.connection.commit()
            self.logger.info(f"User {username} added successfully")
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error adding user: {e}")
            return None
        finally:
            cursor.close()

    def get_user_by_username(self, username):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            return cursor.fetchone()
        except Error as e:
            self.logger.error(f"Error retrieving user: {e}")
            return None
        finally:
            cursor.close()

    # 食物相关操作
    def add_food(self, food_name, category, calorie_per_100g, protein=None, 
                fat=None, carbs=None, fiber=None, image_url=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO foods (food_name, food_category, calorie_per_100g,
                                 protein_per_100g, fat_per_100g, carbs_per_100g,
                                 fiber_per_100g, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (food_name, category, calorie_per_100g, protein, 
                     fat, carbs, fiber, image_url)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error adding food: {e}")
            return None
        finally:
            cursor.close()

    # 饮食记录相关操作
    def add_diet_record(self, user_id, food_id, meal_type, weight_g, 
                       calories, image_path=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO diet_records (user_id, food_id, meal_type, weight_g,
                                        calories, image_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (user_id, food_id, meal_type, weight_g, calories, image_path)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error adding diet record: {e}")
            return None
        finally:
            cursor.close()

    def get_user_daily_calories(self, user_id, date):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT SUM(calories) as total_calories
                FROM diet_records
                WHERE user_id = %s AND DATE(record_time) = %s
            """
            cursor.execute(query, (user_id, date))
            result = cursor.fetchone()
            return result['total_calories'] if result['total_calories'] else 0
        except Error as e:
            self.logger.error(f"Error getting daily calories: {e}")
            return 0
        finally:
            cursor.close()

    # 设备相关操作
    def register_device(self, user_id, device_name, device_type, serial_number):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO devices (user_id, device_name, device_type, serial_number)
                VALUES (%s, %s, %s, %s)
            """
            values = (user_id, device_name, device_type, serial_number)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error registering device: {e}")
            return None
        finally:
            cursor.close()

    # 测量数据相关操作
    def add_measurement(self, device_id, weight_g, image_path=None):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO measurements (device_id, weight_g, image_path)
                VALUES (%s, %s, %s)
            """
            values = (device_id, weight_g, image_path)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error adding measurement: {e}")
            return None
        finally:
            cursor.close()

    # 运动建议相关操作
    def add_exercise_recommendation(self, user_id, excess_calories, recommendation_text):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO exercise_recommendations 
                (user_id, date, excess_calories, recommendation_text)
                VALUES (%s, CURDATE(), %s, %s)
            """
            values = (user_id, excess_calories, recommendation_text)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error adding exercise recommendation: {e}")
            return None
        finally:
            cursor.close()

    # 识别记录相关操作
    def log_recognition(self, measurement_id, recognized_food_id, 
                       confidence_score, processing_time):
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO recognition_logs 
                (measurement_id, recognized_food_id, confidence_score, processing_time)
                VALUES (%s, %s, %s, %s)
            """
            values = (measurement_id, recognized_food_id, confidence_score, processing_time)
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.logger.error(f"Error logging recognition: {e}")
            return None
        finally:
            cursor.close()

# 使用示例
if __name__ == "__main__":
    db = DatabaseManager()
    if db.connect():
        try:
            # 添加测试用户
            user_id = db.add_user(
                username="test_user",
                password="hashed_password",
                email="test@example.com",
                gender="male",
                daily_calorie_goal=2000
            )

            # 添加测试食物
            food_id = db.add_food(
                food_name="Apple",
                category="Fruit",
                calorie_per_100g=52,
                protein=0.3,
                fat=0.2,
                carbs=14,
                fiber=2.4
            )

            # 添加测试饮食记录
            if user_id and food_id:
                db.add_diet_record(
                    user_id=user_id,
                    food_id=food_id,
                    meal_type="snack",
                    weight_g=100,
                    calories=52
                )

            print("Test data added successfully")
        finally:
            db.disconnect()