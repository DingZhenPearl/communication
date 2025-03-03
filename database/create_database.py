import mysql.connector
from mysql.connector import Error
import os

def create_database():
    try:
        # 首先连接MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='sushiding'  # 请使用您的实际密码
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 读取SQL文件
            script_path = os.path.join(os.path.dirname(__file__), 'create_database.sql')
            with open(script_path, 'r', encoding='utf-8') as sql_file:
                sql_script = sql_file.read()
            
            # 执行SQL脚本（按语句分割执行）
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement + ';')
            
            connection.commit()
            print("数据库和表创建成功！")

    except Error as e:
        print(f"错误: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭。")

if __name__ == "__main__":
    create_database()