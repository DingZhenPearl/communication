import React, { useState, useEffect } from 'react';
import { 
  View, Text, TextInput, Button, FlatList, 
  StyleSheet, SafeAreaView, StatusBar 
} from 'react-native';
import io from 'socket.io-client';

// 配置信息
const DEVICE_ID = 'device_app'; // 要连接的硬件设备ID
const APP_ID = `app_for_${DEVICE_ID}`; // APP的ID格式
const SERVER_URL = 'http://192.168.1.100:3000'; // 使用实际服务器IP

const App = () => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [deviceStatus, setDeviceStatus] = useState('未知');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);

  // 建立Socket连接
  useEffect(() => {
    const newSocket = io(SERVER_URL);
    
    newSocket.on('connect', () => {
      console.log('已连接到服务器');
      setConnected(true);
      
      // 注册为APP
      newSocket.emit('register', {
        type: 'app',
        deviceId: APP_ID
      });
    });
    
    newSocket.on('device_status', (data) => {
      console.log('设备状态更新:', data);
      setDeviceStatus(data.status === 'online' ? '在线' : '离线');
    });
    
    newSocket.on('message', (data) => {
      console.log('收到消息:', data);
      setMessages(prevMessages => [
        {
          id: Date.now().toString(),
          ...data,
          isIncoming: true
        },
        ...prevMessages
      ]);
    });
    
    newSocket.on('error', (error) => {
      console.error('通信错误:', error);
      alert(`通信错误: ${error.message}`);
    });
    
    newSocket.on('disconnect', () => {
      console.log('与服务器断开连接');
      setConnected(false);
      setDeviceStatus('未知');
    });
    
    setSocket(newSocket);
    
    // 清理函数
    return () => {
      newSocket.disconnect();
    };
  }, []);

  // 发送消息
  const sendMessage = () => {
    if (!message.trim() || !socket || !connected) return;
    
    // 构建消息对象
    const messageObj = {
      to: DEVICE_ID,
      message: message.trim(),
      metadata: {
        appVersion: '1.0.0',
        platform: Platform.OS
      }
    };
    
    socket.emit('message', messageObj);
    
    // 添加到本地消息列表
    setMessages(prevMessages => [
      {
        id: Date.now().toString(),
        from: APP_ID,
        message: message.trim(),
        timestamp: new Date().toISOString(),
        isIncoming: false
      },
      ...prevMessages
    ]);
    
    // 清空输入框
    setMessage('');
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <Text style={styles.title}>设备通信</Text>
        <View style={styles.statusContainer}>
          <View style={[
            styles.statusIndicator, 
            {backgroundColor: deviceStatus === '在线' ? '#4CAF50' : '#F44336'}
          ]} />
          <Text style={styles.statusText}>
            设备状态: {deviceStatus}
          </Text>
        </View>
      </View>
      
      <FlatList
        data={messages}
        keyExtractor={item => item.id}
        style={styles.messagesList}
        inverted
        renderItem={({ item }) => (
          <View style={[
            styles.messageContainer,
            item.isIncoming ? styles.incomingMessage : styles.outgoingMessage
          ]}>
            <Text style={styles.messageText}>{item.message}</Text>
            <Text style={styles.messageTime}>
              {new Date(item.timestamp).toLocaleTimeString()}
            </Text>
          </View>
        )}
      />
      
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={message}
          onChangeText={setMessage}
          placeholder="输入消息..."
          placeholderTextColor="#999"
        />
        <Button
          title="发送"
          onPress={sendMessage}
          disabled={!connected || deviceStatus !== '在线'}
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 6,
  },
  statusText: {
    fontSize: 14,
    color: '#616161',
  },
  messagesList: {
    flex: 1,
    padding: 16,
  },
  messageContainer: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  incomingMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  outgoingMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#E3F2FD',
  },
  messageText: {
    fontSize: 16,
  },
  messageTime: {
    fontSize: 11,
    color: '#9E9E9E',
    alignSelf: 'flex-end',
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  input: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 4,
    paddingHorizontal: 12,
    marginRight: 12,
  },
});

export default App;