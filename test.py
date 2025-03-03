from zhipuai import ZhipuAI
client = ZhipuAI(api_key="b161ab74893310f851cf1773d822657d.iVHlt3Ymx27C1Iax")

response = client.chat.completions.create(
    model="glm-4v-flash",
    messages=[
        {
          "role": "user", 
          "content": [
            {
              "type": "image_url",
              "image_url": {
                "url" : "https://picb5.photophoto.cn/13/021/13021675_1.jpg"
              }
            },
            {
              "type": "text",
              "text": "估计图片内食物的卡路里"
            }
          ]
        },
    ],
    stream=True,
)

# 方法1: 直接打印，不分段
print("回复内容:")
for chunk in response:
    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n")

# 方法2: 收集所有内容后一次性输出
"""
full_response = ""
for chunk in response:
    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
        full_response += chunk.choices[0].delta.content

print(f"\n完整回复:\n{full_response}")
"""