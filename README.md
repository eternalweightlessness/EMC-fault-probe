<h1 align = "center">EMC Principle Group Project</h1>

<h1 align = "center">电磁兼容故障库（中文资料）</h1>
<h3 align="right">——项目过程与细节记录</h3>
<p align="right">第20组-大作业<br>小组成员：朱宛瑜 皇甫依扬 刘子晗<br>Date from: 2025.11.15</p>

<center>用于EMC小组大作业版本管理</center>

<div style="page-break-after: always;"></div>

# 1.历史故障数据收集清单

## 1.1 期刊论文、行业报告等文献

以下中文文献均使用**GB/T 7714-2015**格式参考列出。

[1]彭宇,张莉,梁培. 基于机器学习的电磁兼容故障诊断综述[J]. 电力电子技术,2025,59(1):30-36. DOI:10.3969/j.issn.1000-100X.2025.01.008.

[2]宋健,贺庚贤,葛欣宏. 空间光学有效载荷电磁兼容故障诊断[J]. 现代电子技术,2018,41(6):74-78. DOI:10.16652/j.issn.1004-373x.2018.06.018.



## 1.2 网页资料链接

[1]:[设备电磁兼容性故障的诊断和一般性处理意见.PDF 全文免费](https://max.book118.com/html/2019/0513/7166026100002025.shtm)



## 1.3 LLM（Deepseek & ChatGPT etc.）



# 2.数据预处理

我们需要对从不同途径收集来的故障信息进行清洗。主要的工作如下：

1. 去除无关符号、空白、重复内容；
2. 将不同格式（PDF、Word、网页）的资料转为统一格式（如 TXT 或 JSON）；
3. 利用LLM合并“同义不同述”的故障记录。

> [!NOTE]
>
> 问题1：如何将PDF、Word、HTML等格式的资料转化为JSON格式？
>
> 方案1：使用ConvertTool等在线工具转换。需要试一次，看下转换结果。
>
> 方案结果：将PDF格式的论文转化为JSON格式的示例如下：
>
> ```json
> {
>   "metadata": {
>     "filename": "空间光学有效载荷电磁兼容故障诊断.pdf",
>     "pageCount": 5,
>     "convertedAt": "2025-11-15T14:22:23.464Z"
>   },
>   "pages": [
>     {
>       "pageNumber": 1,
>       "text": "现代电子技术···",
>       "stats": {
>         "charCount": 2582,
>         "wordCount": 240
>       }
>     },
>     {
>       "pageNumber": 2,
>       "text": "第 6 期 宋 健，等：···",
>       "stats": {
>         "charCount": 1244,
>         "wordCount": 89
>       }
>     },
>     {
>       "pageNumber": 3,
>       "text": "现代电子技术 ···",
>       "stats": {
>         "charCount": 1229,
>         "wordCount": 153
>       }
>     },
>     {
>       "pageNumber": 4,
>       "text": "第 6 期 宋 健，等：···",
>       "stats": {
>         "charCount": 2154,
>         "wordCount": 347
>       }
>     },
>     {
>       "pageNumber": 5,
>       "text": "现代电子技术 ···",
>       "stats": {
>         "charCount": 3620,
>         "wordCount": 331
>       }
>     }
>   ]
> }
> ```
>
> 这种方法是可行的，转换得到的.json文件格式基本包含了PDF当中的文字信息。
>
> ConvertTool链接：[转换大师：免费在线 PDF、图片与媒体转换器 – MP3 MP4 JPG - ConvertTool](https://converttool.org/zh-cn/)



# 3.利用LLM提取结构化信息

## 3.1 结构化字段

让LLM从非结构化的故障描述中提取结构化字段，例如：

|  字段头  |          字段内容          |
| :------: | :------------------------: |
| 故障对象 |   如“电机A”、“通信模块”    |
| 故障现象 |  如“通信中断”、“辐射超标”  |
| 故障原因 | 如“接地不良”、“滤波器失效” |
| 解决方案 | 如“重新接地”、“更换滤波器” |
| 故障等级 |      如“严重”、“一般”      |
| 发生频率 |      如“高频”、“偶发”      |

## 3.2 Prompt及提取效果



# 4.构建故障库

利用第3节中所讲述的思路提取出结构化信息后，利用这些信息来构建故障库，主要涉及故障库的存储形式以及数据结构的设计：

1. 将提取的结构化数据存入数据库（如 MySQL 或 MongoDB）；
2. 建立“故障-原因-解决方案”之间的关联关系，并使用故障码来表示不同类型的故障。



# 5.故障库应用功能设计

我们对任务描述中==技术路径一==的应用设计（即实现用户使用中文查询故障即解决方案）的思路如下：

1. 将前述步骤所建立的数据库存储为某种格式的数据文件，如MySQL、JSON格式等；
2. 使用Python[^1]编写脚本，测试不同的用户输入（例如用户输入”辐射发射超标“）能否准确地匹配到故障库中相应的故障词条，并返回故障码和解决方案；
3. 步骤2测试完成，准确度达到要求后，使用PyQt5设计用户交互界面[^2][^3]；
4. 可以尝试在程序中嵌入LLM[^4]，利用LLM进行模糊或近义语义匹配，优化用户体验。

## 5.1 存储数据库



## 5.2 Python脚本测试



## 5.3 嵌入LLM

在这一节，我们将详细讲述如何在本地部署LLM，并将其嵌入到基于Python的用户交互程序中，实现用户输入的语义模糊匹配。

### 5.3.1 本地部署LLM

这一步，我们参考网页资料[^5][^6]，使用Ollama平台进行本地部署。部署的测试模型参数为`Deepseek-r1 8b`，表示模型参数有80亿个。后续可以安装调试GPT、cursor等其他不同的大模型。

本地部署的指令如下：

```cmd
ollama run deepseek-r1:8b
```

安装好Ollama后，将上述指令放在命令行当中运行。成功安装会显示如下结果：

```cmd
D:\Ollama>ollama run deepseek-r1:8b
pulling manifest
pulling e6a7edc1a4d7: 100% 5.2 GB
pulling c5ad996bda6e: 100% 556 B
pulling 6e4c38e1172f: 100% 1.1 KB
pulling ed8474dc73db: 100% 179 B
pulling f64cd5418e4b: 100% 487 B
verifying sha256 digest
writing manifest
success
```

一些常用的命令：

```cmd
ollama run deepseek-r1:8b 运行本地大模型
ollama rm deepseek-r1:8b 删除本地大模型
ollama serve 启动Ollama服务
ollama stop 停止Ollama服务
ollama restart 重启Ollama服务
ollama --help 查看帮助及可用命令
ollama update 更新Ollama版本
ollama clean 清理缓存

/bye 或者ctrl+d 退出交互模式
```

Ollama教程链接：[Ollama 教程 | 菜鸟教程](https://www.runoob.com/ollama/ollama-tutorial.html)

初始安装后，对模型进行问候，回复效果如下图所示。

<img src="./README.assets/image-20251116141145385.png" alt="image-20251116141145385" style="zoom: 33%;" />

### 5.3.2 Python脚本调用本地大模型解析文件

我们使用Ollama工具部署的本地大语言模型，因此基于Ollama来进行文件的读取和解析。

通过询问Deepseek，他向我们提供了如下方案：

```python
import requests

url = "http://localhost:11434/api/generate"
headers = {"Content-Type": "application/json"}
data = {
    "model": "your-model-name",  # 你拉取到的模型名称
    "prompt": "你的完整提示，包括文件内容",
    "stream": False,  # 设置为 False 获取一次性响应
    "max_tokens": 256,
    "temperature": 0.7
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result['response'])
```

接下来需要测试这一方案是否可行。先尝试将大模型的响应通过python控制台打印出来。

### 5.3.3 调试本地大模型[^7]



## 5.4 用户交互界面设计



# 6.进阶任务



[^1]: [简介 - Python教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/python/introduction/index.html)
[^2]: [Arduino开发ESP32-CAM模块 & 使用Python-PyQt5编写图传.exe独立程序_auduino图传-CSDN博客](https://blog.csdn.net/Zhuwany/article/details/128989573?spm=1001.2014.3001.5502)
[^3]: [PyQt5 - 教程 - 菜鸟教程](https://www.cainiaoya.com/pyqt5/pyqt5-jiaocheng.html)
[^4]: [30分钟内搞定！在本地电脑上部署属于你自己的大模型 - 知乎](https://zhuanlan.zhihu.com/p/1969812316003493816)
[^5]:[本地部署大模型：Ollama安装（指定路径）和DeepSeek下载 - 知乎](https://zhuanlan.zhihu.com/p/24889002428)
[^6]:[本地部署大模型：修改Ollama模型文件存储路径 - 知乎](https://zhuanlan.zhihu.com/p/27286614924#:~:text=本文会讲解如何修改Ollama模型文件的默认下载路径（以安装到D盘为例），前期已下载的模型文件直接剪切到这个路径下也可以实现自动调用。,第一步：右键“我的电脑”，并选择“属性”，点击“高级系统设置”，选择“环境变量”。 第二步：双击系统变量中Path那一行，点击“新建”，输入“D%3AOllama”，点击“确定”。)
[^7]:[如何给本地部署的DeepSeek投喂数据，让他更懂你 - 知乎](https://zhuanlan.zhihu.com/p/24142666586)
