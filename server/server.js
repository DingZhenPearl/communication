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

// 捕获所有其他请求并返回前端应用
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/web/index.html'));
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

server.listen(PORT, () => {
  console.log(`服务器在http://localhost:${PORT} 上运行`);
  console.log(`WebSocket服务已启动`);
});

module.exports = { app, server, io };