const { io } = require('socket.io-client');
const readline = require('readline');

// 设备信息
const HARDWARE_ID = 'device_hard'; // 根据实际情况修改设备ID
const SERVER_URL = 'http://localhost:3000'; // 服务器地址

// 创建Socket连接
const socket = io(SERVER_URL);

// 创建命令行接口
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// 连接事件处理
socket.on('connect', () => {
  console.log('已连接到服务器');
  
  // 注册为硬件设备
  socket.emit('register', {
    type: 'hardware',
    deviceId: HARDWARE_ID
  });
  
  console.log(`硬件设备 ${HARDWARE_ID} 已注册`);
});

// 接收消息
socket.on('message', (data) => {
  console.log('\n收到消息:');
  console.log(`- 来源: ${data.from}`);
  console.log(`- 内容: ${data.message}`);
  console.log(`- 时间: ${data.timestamp}`);
  if (data.metadata) {
    console.log(`- 元数据: ${JSON.stringify(data.metadata)}`);
  }
});

// 错误处理
socket.on('error', (error) => {
  console.error('通信错误:', error);
});

// 断线处理
socket.on('disconnect', () => {
  console.log('与服务器断开连接');
});

// 命令行交互
function promptMessage() {
  rl.question('输入要发送的消息 (输入exit退出): ', (message) => {
    if (message.toLowerCase() === 'exit') {
      socket.disconnect();
      rl.close();
      process.exit(0);
    }
    
    // 发送消息到配对的APP
    socket.emit('message', {
      to: `app_for_${HARDWARE_ID}`,
      message,
      metadata: {
        deviceStatus: 'normal',
        batteryLevel: Math.floor(Math.random() * 100)
      }
    });
    
    promptMessage();
  });
}

// 启动交互
console.log('硬件端启动, 准备发送消息...');
promptMessage();