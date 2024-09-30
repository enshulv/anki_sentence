## 配置

在 `config.json` 文件中设置以下参数：

- COLLECTION_PATH: Anki数据库文件的路径（默认为%APPDATA%\Anki2\你的账户名字\collection.anki2）
- DECK_NAME: 要处理的牌组名称
- FIELD_NAME: 包含单词的字段名称
- NUM_CARDS: 要处理的卡片数量
- NUM_SENTENCES: 每个单词生成的句子数量
- API_KEY: LLM API密钥
- BASE_URL: LLM API的基础URL
- TIMEOUT: API调用超时时间（秒）
- MAX_RETRIES: 最大重试次数
- RETRY_DELAY: 重试间隔（秒）
- SYSTEM_PROMPT: 给LLM的系统提示词
- USER_PROMPT: 给LLM的用户提示词模板

注意：USER_PROMPT 中可以使用 {num_sentences} 和 {word} 作为占位符，它们会被实际的句子数量和单词替换。
