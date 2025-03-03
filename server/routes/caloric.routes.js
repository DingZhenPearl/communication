const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');

// 获取用户当日卡路里摄入
router.get('/daily/:userId', async (req, res) => {
  const { userId } = req.params;
  const date = req.query.date || new Date().toISOString().split('T')[0]; // 默认今天
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/caloric_operations.py'),
      'get_user_daily_calories',
      userId,
      date
    ]);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: '解析数据失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ error: '获取卡路里数据失败' });
    });
  } catch (error) {
    res.status(500).json({ error: '获取卡路里数据失败' });
  }
});

// 获取运动建议
router.get('/exercise-recommendations/:userId', async (req, res) => {
  const { userId } = req.params;
  const date = req.query.date || new Date().toISOString().split('T')[0]; // 默认今天
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/caloric_operations.py'),
      'get_exercise_recommendations',
      userId,
      date
    ]);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: '解析数据失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ error: '获取运动建议失败' });
    });
  } catch (error) {
    res.status(500).json({ error: '获取运动建议失败' });
  }
});

module.exports = router;