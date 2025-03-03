const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');

// 注册设备
router.post('/register', async (req, res) => {
  const { userId, deviceName, deviceType, serialNumber } = req.body;
  
  if (!userId || !deviceName || !deviceType || !serialNumber) {
    return res.status(400).json({ success: false, error: '缺少必要的设备信息' });
  }
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/device_operations.py'),
      'register_device',
      userId,
      deviceName,
      deviceType,
      serialNumber
    ]);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        if (result.success) {
          res.status(201).json(result);
        } else {
          res.status(400).json(result);
        }
      } catch (error) {
        res.status(500).json({ success: false, error: '设备注册失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ success: false, error: '设备注册处理错误' });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: '服务器错误' });
  }
});

// 获取用户的设备列表
router.get('/user/:userId', async (req, res) => {
  const { userId } = req.params;
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/device_operations.py'),
      'get_user_devices',
      userId
    ]);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        res.json(result);
      } catch (error) {
        res.status(500).json({ success: false, error: '获取设备列表失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ success: false, error: '处理设备列表错误' });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: '服务器错误' });
  }
});

module.exports = router;