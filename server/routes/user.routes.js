const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');

// 修改用户注册处理函数
router.post('/register', async (req, res) => {
  const { username, password, email, gender, birth_date, height, weight, target_weight, daily_calorie_goal } = req.body;
  
  // 添加详细的请求日志
  console.log('接收到注册请求:', {
    username,
    email,
    gender,
    hasPassword: !!password,
    birth_date: birth_date || '',
    height,
    weight,
    target_weight: target_weight || '',
    daily_calorie_goal
  });

  // 增强输入验证
  if (!username || typeof username !== 'string') {
    return res.status(400).json({ 
      success: false, 
      error: '无效的用户名',
      details: '用户名必须是非空字符串'
    });
  }

  if (!password || typeof password !== 'string' || password.length < 6) {
    return res.status(400).json({
      success: false,
      error: '无效的密码',
      details: '密码必须至少6个字符'
    });
  }

  if (!email || !email.includes('@')) {
    return res.status(400).json({
      success: false,
      error: '无效的邮箱地址',
      details: '请提供有效的电子邮箱'
    });
  }

  try {
    // 确保空值被转换为空字符串
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/user_operations.py'),
      'register_user',
      username,
      password,
      email,
      gender || '',
      birth_date || '',  // 确保提供空字符串
      height ? String(height) : '',
      weight ? String(weight) : '',
      target_weight || '',  // 确保提供空字符串
      daily_calorie_goal ? String(daily_calorie_goal) : ''
    ], {
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    // 改进错误处理
    let outputData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      outputData += data.toString();
      console.log('Python输出:', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      console.error('Python错误:', data.toString());
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python进程异常退出,代码:${code}, 错误信息:${errorData}`);
        return res.status(500).json({
          success: false,
          error: '注册处理失败',
          details: errorData || '未知错误'
        });
      }

      try {
        const result = JSON.parse(outputData);
        res.status(result.success ? 201 : 400).json(result);
      } catch (e) {
        console.error('解析Python输出失败:', e, '原始输出:', outputData);
        res.status(500).json({
          success: false, 
          error: '处理注册响应失败',
          details: e.message,
          rawOutput: outputData
        });
      }
    });

  } catch (error) {
    console.error('执行注册脚本错误:', error);
    res.status(500).json({
      success: false,
      error: '服务器内部错误',
      details: error.message
    });
  }
});

// 修改用户登录处理函数
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../database/user_operations.py'),
      'login_user',
      username,
      password
    ]);
    
    // 收集所有输出
    let outputData = '';
    let errorData = '';
    
    pythonProcess.stdout.on('data', (data) => {
      outputData += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      console.error(`Python错误输出: ${data}`);
    });
    
    // 等待进程结束后再处理结果
    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python进程退出，代码: ${code}，错误: ${errorData}`);
        return res.status(500).json({ success: false, error: '登录处理失败' });
      }
      
      try {
        const result = JSON.parse(outputData);
        if (result.success) {
          res.json(result);
        } else {
          res.status(401).json(result);
        }
      } catch (error) {
        console.error('解析Python输出错误:', error, '原始输出:', outputData);
        res.status(500).json({ success: false, error: '登录处理失败' });
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: '服务器错误' });
  }
});

// 获取用户饮食记录
router.get('/:userId/diet-records', async (req, res) => {
  const { userId } = req.params;
  const { date, startDate, endDate } = req.query;
  
  try {
    const args = [
      path.join(__dirname, '../../database/user_operations.py'),
      'get_user_diet_records',
      userId
    ];
    
    if (date) {
      args.push('--date');
      args.push(date);
    } else if (startDate && endDate) {
      args.push('--start-date');
      args.push(startDate);
      args.push('--end-date');
      args.push(endDate);
    }
    
    const pythonProcess = spawn('python', args);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        res.json(result);
      } catch (error) {
        res.status(500).json({ success: false, error: '获取饮食记录失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ success: false, error: '处理饮食记录错误' });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: '服务器错误' });
  }
});

module.exports = router;