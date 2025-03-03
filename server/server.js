const express = require('express');
const http = require('http');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const { Server } = require('socket.io');
require('dotenv').config();

// 初始化 Express 应用
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件配置
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../client/build')));

// 导入路由模块
const userRoutes = require('./routes/user.routes');
const deviceRoutes = require('./routes/device.routes');
const recognitionRoutes = require('./routes/recognition.routes');
const caloricRoutes = require('./routes/caloric.routes');

// 注册API路由
app.use('/api/users', userRoutes);
app.use('/api/devices', deviceRoutes);
app.use('/api/recognition', recognitionRoutes);
app.use('/api/caloric', caloricRoutes);

// 基本路由
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: '服务器正常运行' });
});

// API 路由示例
app.post('/api/message', (req, res) => {
  const { message } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: '消息不能为空' });
  }
  
  // 这里可以添加消息处理逻辑
  console.log('收到消息:', message);
  
  res.json({ 
    success: true,
    message: '消息已接收',
    timestamp: new Date().toISOString() 
  });
});

// 在现有路由定义后添加

// 测试API端点
app.get('/api/test', (req, res) => {
  res.json({
    status: 'success',
    message: '测试API正常工作',
    time: new Date().toISOString()
  });
});

// 简单的测试用户注册端点
app.post('/api/test-register', (req, res) => {
  const testUser = {
    username: `test_${Date.now()}`,
    password: "password123",
    email: `test${Date.now()}@example.com`
  };
  
  console.log('创建测试用户:', testUser);
  
  // 内部调用Python脚本注册用户
  const { spawn } = require('child_process');
  const pythonProcess = spawn('python', [
    path.join(__dirname, '../database/user_operations.py'),
    'register_user',
    testUser.username,
    testUser.password,
    testUser.email
  ], {
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });
  
  let output = '';
  pythonProcess.stdout.on('data', (data) => {
    output += data.toString('utf-8');
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.log('Python输出:', data.toString('utf-8'));
  });
  
  pythonProcess.on('close', (code) => {
    try {
      const result = JSON.parse(output);
      res.json({
        testUser,
        result,
        pythonExitCode: code
      });
    } catch (error) {
      res.status(500).json({
        error: '测试用户创建失败',
        pythonOutput: output,
        pythonExitCode: code
      });
    }
  });
});

// 捕获所有其他请求并返回前端应用
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/web/cal.html'));
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error('服务器错误:', err);
  res.status(500).json({ error: '服务器内部错误' });
});

// 创建 HTTP 服务器
const server = http.createServer(app);

// 创建 Socket.IO 实例
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// 设备连接管理
const connectedDevices = new Map();
const connectedApps = new Map();

// Socket.IO 连接处理
io.on('connection', (socket) => {
  console.log('新客户端连接:', socket.id);

  // 客户端类型识别
  socket.on('register', (data) => {
    const { type, deviceId } = data;
    
    if (type === 'hardware') {
      connectedDevices.set(deviceId, socket.id);
      socket.deviceId = deviceId;
      socket.deviceType = 'hardware';
      console.log(`硬件设备11 ${deviceId} 已连接`);
      
      // 通知相关APP设备已上线
      for (const [appId, socketId] of connectedApps.entries()) {
        if (appId.startsWith(`app_for_${deviceId}`)) {
          io.to(socketId).emit('device_status', { deviceId, status: 'online' });
        }
      }
    } 
    else if (type === 'app') {
      connectedApps.set(deviceId, socket.id);
      socket.deviceId = deviceId;
      socket.deviceType = 'app';
      console.log(`APP客户端 ${deviceId} 已连接`);
      
      // 检查相关硬件是否在线
      const hardwareId = deviceId.replace('app_for_', '');
      if (connectedDevices.has(hardwareId)) {
        socket.emit('device_status', { deviceId: hardwareId, status: 'online' });
      } else {
        socket.emit('device_status', { deviceId: hardwareId, status: 'offline' });
      }
    }
  });

  // 消息转发
  socket.on('message', (data) => {
    const { to, message, metadata } = data;
    console.log(`收到来自 ${socket.deviceId} 的消息，发送至 ${to}`);
    
    // 确定目标Socket ID
    let targetSocketId = null;
    if (socket.deviceType === 'hardware') {
      // 从硬件发往APP
      targetSocketId = connectedApps.get(`app_for_${socket.deviceId}`);
    } else if (socket.deviceType === 'app') {
      // 从APP发往硬件
      const hardwareId = socket.deviceId.replace('app_for_', '');
      targetSocketId = connectedDevices.get(hardwareId);
    }
    
    // 发送消息
    if (targetSocketId) {
      io.to(targetSocketId).emit('message', {
        from: socket.deviceId,
        message,
        metadata,
        timestamp: new Date().toISOString()
      });
    } else {
      // 目标设备离线，发送错误通知
      socket.emit('error', { 
        code: 'DEVICE_OFFLINE',
        message: '目标设备当前离线' 
      });
    }
  });

  // 添加特定于食物识别的数据处理
  socket.on('food_data', async (data) => {
    try {
      const { weight_g, image_data, deviceId } = data;
      console.log(`收到来自设备 ${deviceId} 的食物数据，重量: ${weight_g}g`);
      
      // 保存图像数据到临时文件
      const imagePath = await saveImageToFile(image_data, deviceId);
      
      // 调用Python进行食物识别
      const { spawn } = require('child_process');
      const pythonProcess = spawn('python', [
        path.join(__dirname, '../recognition/process_food.py'),
        '--image', imagePath,
        '--weight', weight_g
      ]);
      
      // 修改为:
      let stdoutData = '';
      pythonProcess.stdout.on('data', (data) => {
        stdoutData += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        console.log('Python调试输出:', data.toString());
      });
      
      pythonProcess.on('close', (code) => {
        try {
          if (code === 0 && stdoutData) {
            const recognitionResult = JSON.parse(stdoutData);
            console.log('食物识别结果:', recognitionResult);
            
            // 如果识别成功，通知相关APP
            if (recognitionResult.success) {
              const appSocketId = connectedApps.get(`app_for_${deviceId}`);
              if (appSocketId) {
                io.to(appSocketId).emit('food_recognition', {
                  from: deviceId,
                  result: recognitionResult,
                  timestamp: new Date().toISOString()
                });
              }
              
              // 向当前连接的客户端也发送
              socket.emit('food_recognition_result', recognitionResult);
            }
          } else {
            console.error('Python进程错误或无数据:', code);
            socket.emit('error', {
              code: 'RECOGNITION_FAILED',
              message: '食物识别失败'
            });
          }
        } catch (err) {
          console.error('处理识别结果错误:', err, '原始数据:', stdoutData);
          socket.emit('error', {
            code: 'PROCESSING_ERROR',
            message: '处理识别结果时出错'
          });
        }
      });
    } catch (err) {
      console.error('处理食物数据错误:', err);
      socket.emit('error', {
        code: 'PROCESSING_ERROR',
        message: '处理食物数据时出错'
      });
    }
  });

  // 断开连接处理
  socket.on('disconnect', () => {
    console.log(`客户端断开连接: ${socket.id}`);
    
    if (socket.deviceType === 'hardware') {
      connectedDevices.delete(socket.deviceId);
      
      // 通知相关APP设备已下线
      for (const [appId, socketId] of connectedApps.entries()) {
        if (appId.startsWith(`app_for_${socket.deviceId}`)) {
          io.to(socketId).emit('device_status', { deviceId: socket.deviceId, status: 'offline' });
        }
      }
    } 
    else if (socket.deviceType === 'app') {
      connectedApps.delete(socket.deviceId);
    }
  });
});

// 保存图像数据到文件的辅助函数
async function saveImageToFile(imageData, deviceId) {
  const fs = require('fs').promises;
  const path = require('path');
  
  // 确保目录存在
  const uploadDir = path.join(__dirname, '../uploads');
  try {
    await fs.mkdir(uploadDir, { recursive: true });
  } catch (err) {
    // 目录已存在，忽略错误
  }
  
  // 生成唯一文件名
  const fileName = `${deviceId}_${Date.now()}.jpg`;
  const filePath = path.join(uploadDir, fileName);
  
  // 保存图片数据
  // 如果imageData是base64编码的字符串
  const base64Data = imageData.replace(/^data:image\/\w+;base64,/, '');
  await fs.writeFile(filePath, base64Data, { encoding: 'base64' });
  
  return filePath;
}

server.listen(PORT, () => {
  console.log(`服务器在http://localhost:${PORT} 上运行`);
  console.log(`WebSocket服务已启动`);
});

module.exports = { app, server, io };