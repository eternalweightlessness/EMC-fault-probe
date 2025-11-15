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



# 6.进阶任务



[^1]: [简介 - Python教程 - 廖雪峰的官方网站](https://liaoxuefeng.com/books/python/introduction/index.html)
[^2]: [Arduino开发ESP32-CAM模块 & 使用Python-PyQt5编写图传.exe独立程序_auduino图传-CSDN博客](https://blog.csdn.net/Zhuwany/article/details/128989573?spm=1001.2014.3001.5502)
[^3]: [PyQt5 - 教程 - 菜鸟教程](https://www.cainiaoya.com/pyqt5/pyqt5-jiaocheng.html)
[^4]: [30分钟内搞定！在本地电脑上部署属于你自己的大模型 - 知乎](https://zhuanlan.zhihu.com/p/1969812316003493816)
