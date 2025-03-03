import sys
import json
import argparse
from db_operation import DatabaseManager

def register_device(user_id, device_name, device_type, serial_number):
    """注册新设备"""
    db = DatabaseManager()
    if db.connect():
        try:
            # 检查序列号是否已存在
            try:
                cursor = db.connection.cursor(dictionary=True)
                query = "SELECT * FROM devices WHERE serial_number = %s"
                cursor.execute(query, (serial_number,))
                existing_device = cursor.fetchone()
                if existing_device:
                    return {"success": False, "error": "设备序列号已注册"}
            finally:
                cursor.close()
            
            # 注册设备
            device_id = db.register_device(
                user_id=user_id,
                device_name=device_name,
                device_type=device_type,
                serial_number=serial_number
            )
            
            if device_id:
                return {
                    "success": True,
                    "message": "设备注册成功",
                    "device_id": device_id
                }
            else:
                return {"success": False, "error": "设备注册失败"}
        finally:
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

def get_user_devices(user_id):
    """获取用户关联的设备列表"""
    db = DatabaseManager()
    if db.connect():
        try:
            cursor = db.connection.cursor(dictionary=True)
            query = "SELECT * FROM devices WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            devices = cursor.fetchall()
            
            # 处理日期/时间为字符串
            for device in devices:
                for key, value in device.items():
                    if isinstance(value, (bytes, bytearray)):
                        device[key] = value.decode('utf-8')
            
            return {
                "success": True,
                "user_id": int(user_id),
                "devices": devices
            }
        finally:
            cursor.close()
            db.disconnect()
    return {"success": False, "error": "数据库连接失败"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='设备操作工具')
    parser.add_argument('command', help='要执行的命令')
    parser.add_argument('args', nargs='*', help='命令参数')
    
    args = parser.parse_args()
    
    result = {"success": False, "error": "未知命令"}
    
    if args.command == "register_device" and len(args.args) == 4:
        result = register_device(*args.args)
    elif args.command == "get_user_devices" and len(args.args) == 1:
        result = get_user_devices(args.args[0])
    
    print(json.dumps(result))