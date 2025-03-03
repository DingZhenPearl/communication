const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const multer = require('multer');

// 配置文件上传
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../uploads');
    try {
      await fs.mkdir(uploadDir, { recursive: true });
    } catch (error) {
      // 忽略目录已存在错误
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});
const upload = multer({ storage });

// 处理图像食物识别请求
router.post('/process', upload.single('image'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ success: false, error: '未提供图像文件' });
  }
  
  const { weight } = req.body;
  
  if (!weight) {
    return res.status(400).json({ success: false, error: '未提供重量数据' });
  }
  
  try {
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../recognition/process_food.py'),
      '--image', req.file.path,
      '--weight', weight
    ]);
    
    pythonProcess.stdout.on('data', (data) => {
      try {
        const result = JSON.parse(data.toString());
        res.json(result);
      } catch (error) {
        console.error('解析Python输出错误:', error);
        res.status(500).json({ success: false, error: '食物识别处理失败' });
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python错误: ${data}`);
      res.status(500).json({ success: false, error: '食物识别处理错误' });
    });
  } catch (error) {
    console.error('执行Python脚本错误:', error);
    res.status(500).json({ success: false, error: '服务器错误' });
  }
});

module.exports = router;