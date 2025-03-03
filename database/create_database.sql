-- 创建数据库
CREATE DATABASE IF NOT EXISTS calorie_monitoring;
USE calorie_monitoring;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    gender ENUM('male', 'female', 'other'),
    birth_date DATE,
    height DECIMAL(5,2),
    weight DECIMAL(5,2),
    target_weight DECIMAL(5,2),
    daily_calorie_goal INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建食物表
CREATE TABLE IF NOT EXISTS foods (
    food_id INT PRIMARY KEY AUTO_INCREMENT,
    food_name VARCHAR(100) NOT NULL,
    food_category VARCHAR(50),
    calorie_per_100g DECIMAL(6,2) NOT NULL,
    protein_per_100g DECIMAL(5,2),
    fat_per_100g DECIMAL(5,2),
    carbs_per_100g DECIMAL(5,2),
    fiber_per_100g DECIMAL(5,2),
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建饮食记录表
CREATE TABLE IF NOT EXISTS diet_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    food_id INT NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') NOT NULL,
    weight_g DECIMAL(6,2) NOT NULL,
    calories DECIMAL(6,2) NOT NULL,
    image_path VARCHAR(255),
    record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (food_id) REFERENCES foods(food_id)
);

-- 创建设备表
CREATE TABLE IF NOT EXISTS devices (
    device_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 创建测量数据表
CREATE TABLE IF NOT EXISTS measurements (
    measurement_id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    weight_g DECIMAL(6,2) NOT NULL,
    image_path VARCHAR(255),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- 创建运动建议表
CREATE TABLE IF NOT EXISTS exercise_recommendations (
    recommendation_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    excess_calories INT NOT NULL,
    recommendation_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 创建识别记录表
CREATE TABLE IF NOT EXISTS recognition_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    measurement_id INT NOT NULL,
    recognized_food_id INT NOT NULL,
    confidence_score DECIMAL(4,3) NOT NULL,
    processing_time DECIMAL(8,3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (measurement_id) REFERENCES measurements(measurement_id),
    FOREIGN KEY (recognized_food_id) REFERENCES foods(food_id)
);