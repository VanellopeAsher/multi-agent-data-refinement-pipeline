# 多智能体科学知识图谱修复系统

基于论文OmniScientist: Toward a Co-evolving Ecosystem of Human and AI Scientists实现的多智能体知识图谱精炼系统。

## 系统架构

系统分为三个阶段：

1. **阶段 0 - 数据收集**：从顶级 AI 会议收集论文、参考文献和 PDF 全文
2. **阶段 1 - 初始图谱构建**：将 OpenAlex 元数据映射到 Neo4j 图谱
3. **阶段 2 - 多智能体修复**：使用 5 个智能体协作精炼图谱

### 智能体流程

1. **DiagnoseAgent** - 检测图谱问题（缺失信息、不一致等）
2. **SearchAgent** - 使用 Tavily API 检索外部证据
3. **NormalizationAgent** - 标准化实体和关系
4. **CodingAgent** - 生成图谱更新操作
5. **ReviewAgent** - 验证和过滤更新

## 快速开始

### 环境要求

- Python 3.8+
- Neo4j 5.0+
- API 密钥：OpenAI/SiliconFlow（LLM）、Tavily（搜索）

### 安装步骤

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**

   创建 `.env` 文件：
   ```env
   # LLM 配置
   MODEL_NAME=your-model-name
   PLATFORM=openai  # 或 'siliconflow'
   OPENAI_API_KEY=your-key
   OPENAI_BASE_URL=your-url  # Azure OpenAI 需要
   SILICONFLOW_API_KEY=your-key  # 使用 SiliconFlow 时需要
   SILICONFLOW_BASE_URL=your-url
   
   # 搜索 API
   TAVILY_API_KEY=your-key
   
   # Neo4j 配置
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   NEO4J_DATABASE=neo4j
   ```

3. **验证安装**
   ```bash
   python quick_start.py
   ```

## 使用流程

### 步骤 1：准备数据
```bash
python -m src.scripts.prepare_data
```
从顶级 AI 会议收集论文并下载 PDF，结果保存到 `data/raw/papers.json`

### 步骤 2：构建初始图谱
```bash
python -m src.scripts.ingest_to_neo4j
```
在 Neo4j 中创建论文、作者、概念、机构等节点和关系

### 步骤 3：运行精炼流程
```bash
# 运行第一轮精炼
python -m src.scripts.run_refinement_pipeline --round 1

# 继续后续轮次
python -m src.scripts.run_refinement_pipeline --round 2

# 从检查点恢复
python -m src.scripts.run_refinement_pipeline --round 1 --resume
```

### 步骤 4：评估图谱质量（可选）
```bash
python -m src.evaluation.run_evaluation
```
比较精炼后的图谱与原始 OpenAlex 数据，评估完整性、覆盖率等指标

### 步骤 5：查看使用统计（可选）
```bash
python -m src.scripts.summarize_logs
```

## 项目结构

```
├── data/              # 数据目录（raw, pdfs, intermediate, refined）
├── logs/              # 日志目录
├── src/
│   ├── agents/       # 5 个智能体
│   ├── data_collection/  # 数据收集模块
│   ├── evaluation/   # 图谱评估模块
│   ├── graph_store/  # 图谱存储接口
│   ├── ingestion/    # 图谱构建
│   ├── pipeline/     # 流程编排
│   └── scripts/      # 入口脚本
├── tests/            # 单元测试
└── quick_start.py    # 环境验证脚本
```

## 常见问题

- **Neo4j 连接失败**：确保 Neo4j 运行中，检查 `.env` 中的连接配置
- **API 密钥错误**：验证所有必需的 API 密钥已正确配置
- **中断恢复**：使用 `--resume` 参数从检查点继续，检查点保存在 `data/intermediate/checkpoints/`

## 文档

- `PAPERS_JSON_STRUCTURE.md` - papers.json 数据结构说明
- `GRAPH_DATABASE_STRUCTURE.md` - Neo4j 图谱结构说明
