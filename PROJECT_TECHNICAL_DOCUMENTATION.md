# 钓鱼网站检测系统 - 详细技术文档

## 项目概述

本项目是一个基于机器学习的钓鱼网站检测系统，通过分析URL的词汇特征、HTTP响应特征、HTML内容特征、国际化域名特征、Cookie安全特征和安全头特征等多个维度，识别恶意钓鱼网站。

## 1. 模型详细信息

### 1.1 模型架构
- **模型类型**: RandomForestClassifier (随机森林分类器)
- **算法**: scikit-learn 实现的随机森林算法
- **版本**: sklearn.ensemble._forest.RandomForestClassifier

### 1.2 模型参数
```python
{
    'bootstrap': True,              # 使用bootstrap采样
    'ccp_alpha': 0.0,               # 复杂度参数
    'class_weight': 'balanced_subsample',  # 类别权重：平衡子采样
    'criterion': 'gini',            # 分裂标准：基尼不纯度
    'max_depth': None,              # 树的最大深度：无限制
    'max_features': 'sqrt',         # 寻找最佳分裂时考虑的特征数量：平方根
    'max_leaf_nodes': None,         # 叶子节点最大数量：无限制
    'max_samples': None,            # bootstrap样本数量：全部
    'min_impurity_decrease': 0.0,   # 分裂所需的最小不纯度减少
    'min_samples_leaf': 1,          # 叶子节点的最小样本数
    'min_samples_split': 2,         # 分裂内部节点的最小样本数
    'min_weight_fraction_leaf': 0.0, # 叶子节点的最小权重分数
    'n_estimators': 500,            # 树的数量：500棵
    'n_jobs': -1,                   # 并行作业数：使用所有CPU核心
    'oob_score': False,             # 是否使用out-of-bag样本评分
    'random_state': 2025,           # 随机种子
    'verbose': 0,                   # 详细输出：关闭
    'warm_start': False             # 热启动：关闭
}
```

### 1.3 模型性能指标
- **训练集性能**: ROC AUC = 1.0, PR AUC = 1.0
- **测试集性能**: ROC AUC = 1.0, PR AUC = 1.0
- **训练样本数**: 28个
- **测试样本数**: 7个
- **分类**: 二分类 (0: 正常网站, 1: 钓鱼网站)

### 1.4 特征重要性排序
前10个重要特征及其重要性分数：
1. `num_special_host` (特殊字符数量): 0.2353
2. `num_digits_host` (数字字符数量): 0.1707
3. `missing_hsts` (缺少HSTS头): 0.0722
4. `has_at_symbol` (包含@符号): 0.0720
5. `cookie_none_without_secure` (Cookie不安全): 0.0620
6. `redirects` (重定向次数): 0.0565
7. `set_cookie_count` (Cookie数量): 0.0555
8. `url_len` (URL长度): 0.0506
9. `host_len` (主机名长度): 0.0371
10. `xcto_nosniff` (X-Content-Type-Options): 0.0365

## 2. 特征工程详解

### 2.1 特征分类系统

#### 2.1.1 URL词汇特征 (10个)
1. **url_len**: URL总长度
2. **host_len**: 主机名长度
3. **path_len**: 路径长度
4. **query_len**: 查询字符串长度
5. **num_subdomains**: 子域名数量
6. **num_digits_host**: 主机名中数字字符数量
7. **num_special_host**: 主机名中特殊字符数量 (-_@%)
8. **has_at_symbol**: 是否包含@符号
9. **suspicious_tld**: 是否使用可疑顶级域名
10. **unusual_port**: 是否使用非标准端口

#### 2.1.2 HTTP响应特征 (7个)
1. **status_code**: HTTP状态码
2. **is_html**: 是否为HTML内容
3. **redirects**: 重定向次数
4. **num_security_headers**: 安全头数量
5. **missing_hsts**: 缺少HSTS头
6. **missing_csp**: 缺少CSP头
7. **missing_xfo**: 缺少X-Frame-Options头

#### 2.1.3 HTML内容特征 (8个)
1. **title_len**: 页面标题长度
2. **forms_count**: 表单数量
3. **inputs_count**: 输入框数量
4. **has_password_input**: 是否包含密码输入框
5. **has_iframe**: 是否包含iframe
6. **meta_refresh**: 是否使用meta刷新
7. **ext_js_ratio**: 外部JavaScript比例
8. **ext_css_ratio**: 外部CSS比例

#### 2.1.4 国际化域名特征 (3个)
1. **is_idn**: 是否为国际化域名
2. **mixed_scripts**: 是否混合脚本
3. **confusable**: 是否包含可混淆字符

#### 2.1.5 Cookie安全特征 (3个)
1. **set_cookie_count**: 设置的Cookie数量
2. **cookie_none_without_secure**: Cookie不安全标志
3. **cookie_no_httponly**: 缺少HttpOnly标志

#### 2.1.6 安全头特征 (2个)
1. **xcto_nosniff**: X-Content-Type-Options头
2. **xfo_strict**: X-Frame-Options严格模式

### 2.2 特征提取逻辑

#### 2.2.1 URL解析与词汇分析
```python
def url_lexical_features(url: str) -> dict:
    # 使用urllib.parse和tldextract解析URL
    # 提取域名、子域名、路径、查询参数等组件
    # 计算各组件长度、特殊字符数量等统计特征
```

#### 2.2.2 可疑顶级域名检测
系统监控的可疑TLD包括：
- `.zip`, `.mov`, `.top`, `.xyz`, `.gq`, `.loan`, `.click`
- `.country`, `.stream`, `.download`, `.work`, `.men`
- `.info`, `.science`, `.tk`, `.ml`, `.cf`

#### 2.2.3 安全头分析
系统检查的安全头包括：
- **HSTS (HTTP Strict Transport Security)**
- **CSP (Content Security Policy)**
- **X-Frame-Options**
- **X-Content-Type-Options**

## 3. 训练数据分析

### 3.1 数据集组成
- **总样本数**: 35个URL
- **正常网站**: 20个 (57.1%)
- **钓鱼网站**: 15个 (42.9%)
- **特征维度**: 33个

### 3.2 数据来源

#### 3.2.1 正常网站来源
主要来自知名合法网站：
- 搜索引擎: Google, Baidu
- 社交媒体: Facebook, Twitter, Instagram, LinkedIn, Weibo
- 电商平台: Amazon, Taobao, Tmall, JD
- 科技公司: Microsoft, Apple, GitHub
- 其他: Wikipedia, YouTube, Stack Overflow, Zhihu, Douban

#### 3.2.2 钓鱼网站特征
- **可疑顶级域名**: .ga, .tk, .ml, .cf, .top, .xyz, .click, .download
- **钓鱼关键词分布**:
  - login: 2个
  - secure: 2个
  - verify: 1个
  - account: 2个
  - security: 2个
  - support: 2个

### 3.3 数据特征差异

#### 3.3.1 关键特征对比
| 特征 | 正常网站平均 | 钓鱼网站平均 | 差异 |
|------|-------------|-------------|------|
| URL长度 | 22.45 | 25.73 | 钓鱼网站URL更长 |
| 子域名数 | 1.00 | 0.00 | 正常网站更多子域名 |
| 可疑TLD | 0.00 | 0.80 | 钓鱼网站使用可疑TLD |
| 安全头数 | 2.40 | 0.13 | 正常网站安全配置更好 |

#### 3.3.2 模式识别
- **钓鱼网站倾向使用**：
  - 较长的URL
  - 可疑顶级域名
  - 包含安全相关关键词
  - 缺少安全配置

- **正常网站特征**：
  - 较短的URL
  - 多层子域名结构
  - 完善的安全头配置
  - 知名域名

## 4. 检测算法原理

### 4.1 随机森林算法原理
- **集成学习**: 使用500棵决策树进行投票
- **特征随机性**: 每棵树使用√n个随机特征
- **样本随机性**: Bootstrap采样构建训练集
- **类别平衡**: 使用balanced_subsample处理类别不平衡

### 4.2 决策流程
1. **特征提取**: 从URL和HTTP响应中提取33个特征
2. **特征标准化**: 模型内部处理特征缩放
3. **森林投票**: 500棵决策树分别投票
4. **概率输出**: 计算钓鱼网站的概率
5. **阈值判定**: 默认阈值0.5进行分类

### 4.3 关键检测机制

#### 4.3.1 多维度检测
- **词汇层面**: 检测URL中的可疑字符和模式
- **结构层面**: 分析域名结构和路径复杂性
- **内容层面**: 检查HTML表单和外部资源
- **安全层面**: 评估安全头和Cookie配置
- **国际化**: 检测IDN和字符混淆

#### 4.3.2 规则增强
虽然主要依赖机器学习，但系统也融合了启发式规则：
- 可疑TLD黑名单
- 安全头完整性检查
- 特殊字符模式识别
- 重定向链分析

## 5. 系统部署架构

### 5.1 技术栈
- **后端框架**: Flask
- **机器学习**: scikit-learn
- **数据处理**: pandas, numpy
- **网络爬虫**: requests, BeautifulSoup
- **HTML渲染**: Selenium/Playwright (可选)
- **URL解析**: urllib.parse, tldextract

### 5.2 部署信息
- **服务器地址**: 192.168.0.76:5001
- **公网访问**: 121.17.216.90:5001
- **部署方式**: systemd服务 + Flask应用
- **依赖管理**: requirements.txt

### 5.3 API接口
```
GET  /               - 主页面
GET  /health        - 健康检查
POST /analyze       - URL分析接口
```

## 6. 性能优化与扩展

### 6.1 性能特点
- **训练数据量**: 小规模 (35个样本)
- **模型复杂度**: 中等 (500棵树)
- **特征维度**: 33维
- **推理速度**: 快速 (毫秒级)

### 6.2 扩展建议
1. **数据扩充**: 增加更多真实的钓鱼网站样本
2. **特征工程**: 添加更多行为特征和时间序列特征
3. **模型升级**: 尝试深度学习模型 (LSTM, Transformer)
4. **实时检测**: 集成浏览器插件进行实时提醒
5. **威胁情报**: 结合实时威胁情报源

### 6.3 局限性
- **数据偏差**: 训练数据较少，可能存在偏差
- **特征覆盖**: 主要基于静态特征，缺少动态行为分析
- **对抗性**: 可能被精心设计的钓鱼网站绕过
- **时效性**: 需要定期更新以应对新的钓鱼手法

## 7. 安全与隐私

### 7.1 数据安全
- **URL存储**: 分析结果不存储完整URL
- **匿名化**: 移除用户标识信息
- **访问控制**: API接口需要认证

### 7.2 模型安全
- **模型保护**: 模型文件加密存储
- **输入验证**: 严格的URL格式验证
- **输出过滤**: 防止信息泄露

### 7.3 隐私保护
- **无跟踪**: 不跟踪用户浏览历史
- **本地处理**: 尽可能在本地完成分析
- **最小权限**: 只请求必要的权限

## 8. 维护与监控

### 8.1 日志系统
- **访问日志**: 记录API调用情况
- **错误日志**: 记录异常和错误
- **性能日志**: 监控响应时间和准确率

### 8.2 监控指标
- **准确率**: 分类准确率统计
- **响应时间**: API响应时间监控
- **系统资源**: CPU、内存使用情况
- **错误率**: 错误和异常统计

### 8.3 更新机制
- **模型重训练**: 定期使用新数据重训练
- **特征更新**: 根据新的钓鱼手法更新特征
- **系统更新**: 定期更新依赖库和安全补丁

---

*文档版本: 1.0*
*创建时间: 2025-09-18*
*最后更新: 2025-09-18*