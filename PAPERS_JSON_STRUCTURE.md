# papers.json 数据结构总结

## 概述

`papers.json` 是一个 JSON 数组，包含从 OpenAlex API 获取的论文元数据，以及通过 `prepare_data.py` 处理后的 PDF 路径和全文内容。

- **总论文数**: 133 篇
- **数据来源**: OpenAlex API + PDF 下载和解析
- **格式**: JSON 数组，每个元素是一篇论文的完整元数据

---

## 顶层字段结构

### 1. 基本信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | OpenAlex 论文 ID，格式：`https://openalex.org/W{数字}` |
| `doi` | string | DOI 标识符 |
| `title` | string | 论文标题 |
| `display_name` | string | 显示名称（通常与 title 相同） |
| `publication_year` | int | 发表年份 |
| `publication_date` | string | 发表日期（ISO 格式，如 "2022-06-07"） |
| `type` | string | 论文类型（如 "article", "preprint"） |
| `language` | string | 语言代码（如 "en"） |

### 2. 标识符字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ids` | dict | 包含各种标识符：<br>- `openalex`: OpenAlex ID<br>- `doi`: DOI<br>- `mag`: MAG ID（如果有）<br>- `arxiv`: arXiv ID（如果有） |

### 3. 位置和来源字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `primary_location` | dict | 主要发表位置，包含：<br>- `id`: 位置 ID<br>- `is_oa`: 是否开放获取<br>- `landing_page_url`: 落地页 URL<br>- `pdf_url`: PDF 下载 URL<br>- `source`: 来源信息（期刊/会议等）<br>- `license`: 许可证<br>- `version`: 版本信息 |
| `best_oa_location` | dict | 最佳开放获取位置（结构同 primary_location） |
| `locations` | list | 所有位置列表 |
| `open_access` | dict | 开放获取信息：<br>- `is_oa`: 是否开放获取<br>- `oa_status`: OA 状态<br>- `oa_url`: OA URL |

### 4. 作者信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `authorships` | list | 作者列表，每个元素包含：<br>- `author_position`: 作者位置（"first", "middle", "last"）<br>- `author`: 作者信息（id, display_name, orcid）<br>- `institutions`: 机构列表<br>- `countries`: 国家代码列表<br>- `is_corresponding`: 是否通讯作者<br>- `raw_author_name`: 原始作者名<br>- `raw_affiliation_strings`: 原始单位字符串<br>- `affiliations`: 单位详细信息 |
| `corresponding_author_ids` | list | 通讯作者 ID 列表 |
| `corresponding_institution_ids` | list | 通讯作者机构 ID 列表 |
| `institutions` | list | 所有机构列表 |
| `institutions_distinct_count` | int | 不同机构数量 |
| `countries_distinct_count` | int | 不同国家数量 |

### 5. 概念和主题字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `concepts` | list | 概念列表，每个元素包含：<br>- `id`: 概念 ID<br>- `wikidata`: Wikidata ID<br>- `display_name`: 概念名称<br>- `level`: 概念层级（0-5）<br>- `score`: 相关性分数 |
| `primary_topic` | dict | 主要主题，包含：<br>- `id`: 主题 ID<br>- `display_name`: 主题名称<br>- `score`: 分数<br>- `subfield`: 子领域<br>- `field`: 领域<br>- `domain`: 域 |
| `keywords` | list | 关键词列表 |
| `topics` | list | 主题列表 |

### 6. 引用关系字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `referenced_works` | list | 引用的论文 ID 列表（OpenAlex ID） |
| `referenced_works_count` | int | 引用论文数量 |
| `related_works` | list | 相关论文 ID 列表 |
| `cited_by_count` | int | 被引用次数 |
| `citation_normalized_percentile` | dict | 标准化引用百分位：<br>- `value`: 百分位值<br>- `is_in_top_1_percent`: 是否前 1%<br>- `is_in_top_10_percent`: 是否前 10% |
| `cited_by_percentile_year` | dict | 年度引用百分位 |
| `counts_by_year` | list | 按年份的引用统计 |

### 7. PDF 和全文字段（由 prepare_data.py 添加）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `local_pdf_path` | string | 本地 PDF 文件路径（绝对路径） |
| `full_text` | string | PDF 解析提取的全文内容 |

### 8. 其他字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `abstract_inverted_index` | dict | 摘要倒排索引（用于搜索） |
| `biblio` | dict | 书目信息（卷、期、页码等） |
| `indexed_in` | list | 索引来源列表（如 "crossref", "arxiv"） |
| `is_retracted` | bool | 是否已撤回 |
| `is_paratext` | bool | 是否为副文本 |
| `is_xpac` | bool | 是否为 XPAC |
| `fwci` | float | Field-Weighted Citation Impact |
| `apc_list` | dict | APC（文章处理费）列表 |
| `apc_paid` | dict | 已支付的 APC |
| `funders` | list | 资助者列表 |
| `grants` | list | 资助项目列表 |
| `awards` | list | 奖项列表 |
| `mesh` | list | MeSH 术语列表 |
| `sustainable_development_goals` | list | 可持续发展目标 |
| `has_content` | dict | 内容可用性信息 |
| `created_date` | string | 创建日期 |
| `updated_date` | string | 更新日期 |

---

## 数据流程

1. **数据获取**: 从 OpenAlex API 获取种子论文和引用论文的元数据
2. **PDF 下载**: 根据元数据中的 PDF URL（优先 arXiv）下载 PDF 文件
3. **PDF 解析**: 使用 PyPDF2 提取 PDF 全文
4. **数据增强**: 添加 `local_pdf_path` 和 `full_text` 字段到元数据中
5. **保存**: 将所有增强后的元数据保存到 `papers.json`

---

## 使用示例

```python
import json

# 读取 papers.json
with open('data/raw/papers.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

# 获取第一篇论文
paper = papers[0]

# 访问基本信息
print(f"Title: {paper['title']}")
print(f"Year: {paper['publication_year']}")
print(f"DOI: {paper['doi']}")

# 访问作者信息
for authorship in paper['authorships']:
    author = authorship['author']
    print(f"Author: {author['display_name']}")
    if authorship['institutions']:
        inst = authorship['institutions'][0]
        print(f"  Institution: {inst['display_name']}")

# 访问概念
for concept in paper['concepts']:
    print(f"Concept: {concept['display_name']} (level {concept['level']}, score {concept['score']:.2f})")

# 访问引用关系
print(f"Cited by: {paper['cited_by_count']} papers")
print(f"References: {paper['referenced_works_count']} papers")

# 访问 PDF 和全文（如果已处理）
if 'local_pdf_path' in paper:
    print(f"PDF path: {paper['local_pdf_path']}")
if 'full_text' in paper:
    print(f"Full text length: {len(paper['full_text'])} characters")
```

---

## 注意事项

1. **不是所有论文都有 PDF**: 只有成功下载并解析的论文才包含 `local_pdf_path` 和 `full_text` 字段
2. **PDF 来源优先级**: arXiv > best_oa_pdf > best_oa_url > oa_url > primary_landing
3. **全文提取可能失败**: 如果 PDF 解析失败，论文仍会保留在列表中，但不会有 `full_text` 字段
4. **引用关系**: `referenced_works` 包含的是 OpenAlex ID 字符串，需要进一步查询获取完整信息

