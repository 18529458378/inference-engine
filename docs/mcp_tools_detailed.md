MCP 工具详细接口（前 30 项）

说明：下面为项目内首 30 个 MCP 工具提供详细的 API contract 模板。每个 contract 包含：用途、输入 JSON Schema、输出 JSON Schema、错误代码、审计字段与示例调用。

1) mcp_query
- 用途：通用事实或检索查询入口，适合低复杂度事实查询或检索器代理。
- 输入 schema (JSON Schema)：
  {
    "type": "object",
    "properties": {
      "query": {"type":"string"},
      "project_namespace": {"type":"string"},
      "top_k": {"type":"integer"}
    },
    "required":["query","project_namespace"]
  }
- 输出 schema：
  {
    "type":"object",
    "properties":{
      "result":{},
      "confidence":{"type":"number","minimum":0,"maximum":1},
      "warnings":{"type":"array","items":{"type":"string"}},
      "meta":{"type":"object"}
    },
    "required":["result","confidence"]
  }
- 错误代码：
  - 400: invalid_input
  - 401: unauthorized (检查 project_namespace 的权限)
  - 503: service_unavailable
- 审计字段：caller, project_namespace, timestamp, request_id
- 示例调用：
  {"query":"Who wrote 'Pride and Prejudice'?","project_namespace":"proj-1","top_k":5}

2) mcp_workflow
- 用途：执行或调度工作流步骤（可组合成复杂任务）。
- 输入 schema：{ step:int, payload:object, project_namespace:str }
- 输出：{ result: any, confidence: float, step_id: str }
- 说明：工作流步骤应记录可回溯日志与事件ID。

3) mcp_validator
- 用途：对先前阶段结果做校验与一致性检查。
- 输入：{ results: [object], project_namespace: string }
- 输出：{ valid: bool, issues: [ {code, message} ], confidence }

4) mcp_collab_analyze
- 用途：分析一个模糊任务并建议分派计划。
- 输入：{ task: string, project_namespace: string, constraints?:object }
- 输出：{ plan: [ {role:string, task:string, estimated_cost: number} ], confidence }

5) mcp_remember
- 用途：把事实写入长期记忆，自动脱敏。
- 输入：{ fact: string, metadata?:object, project_namespace: string }
- 输出：{ id: string, stored: bool, confidence }
- 隐私：实现必须在写入前对 PII 进行脱敏，审计明细保存脱敏前后差异（但不存储脱敏前明文）。

6) mcp_ingest
- 用途：文档入库并建立索引（全文/向量/元数据）。
- 输入：{ document: {title, text, metadata}, project_namespace, ingest_options?: {vectorize:boolean} }
- 输出：{ doc_id, status, indexed: {vector:boolean, text:boolean}, confidence }

7) mcp_anchor_init
- 用途：为任务设置锚点（目标/约束），便于后续 drift 检查。
- 输入：{ task_id:string, anchors: {goal, constraints}, project_namespace }
- 输出：{ ok: bool, anchor_id: string }

8) mcp_anchor_check
- 用途：检查任务与锚点的偏离程度并返回警告。
- 输入：{ task_id, project_namespace }
- 输出：{ drift_score: number (0-1), alerts: [string], confidence }

9) hermes_agent_tool
- 用途：调研/搜索/多源整合；返回聚合结果与摘要。
- 输入：{ task:string, project_namespace, params?:{top_k:int, sources:[str]} }
- 输出：{ result: {sources:[{source,id,score,snippet}], summary}, confidence }

10) deepseek_tool
- 用途：深度检索/跨源聚合检索。
- 输入：{ query:string, project_namespace, index_hint?:string }
- 输出：{ result: {sources:[{source,score,snippet}], summary}, confidence }
- 安全：若需外部 API key，应从环境变量读取（例如 DEEPSEEK_API_KEY），不得写入代码或 repo。

11) pi_agent_tool
- 用途：代码/脚本静态分析与安全执行计划建议。
- 输入：{ task: string, project_namespace, language?:string }
- 输出：{ result:{analysis, suggested_actions}, confidence }

12) toknife_tool
- 用途：Token 压缩工具（JSON/code-aware）。
- 输入：{ data:any, project_namespace }
- 输出：{ result: compressed_repr, confidence }
- 部署：若为脚本包形式，应通过环境变量 TOKNIFE_PY_PATH 指定脚本路径或在 runner 预装。

13) mcp_search_indexer
- 用途：索引文档到检索后端。
- 输入：{ documents:[...], backend:{type, config}, project_namespace }
- 输出：{ indexed_count, index_id, confidence }

14) mcp_retriever
- 用途：从索引检索相关片段。
- 输入：{ query, index_id, top_k, project_namespace }
- 输出：{ hits:[{id,score,text}], confidence }

15) mcp_summarizer
- 用途：对文本进行抽取式/生成式摘要。
- 输入：{ text, mode:'extract'|'abstractive', project_namespace }
- 输出：{ summary, confidence }

16) mcp_passage_ranker
- 用途：对候选 passage 进行排序。
- 输入：{ passages:[{id,text}], query, project_namespace }
- 输出：{ ranked:[{id,score}] , confidence }

17) mcp_qa
- 用途：问答接口，基于检索+生成。
- 输入：{ question, context_passages, project_namespace }
- 输出：{ answer, sources, confidence }

18) mcp_code_validator
- 用途：静态/动态代码校验（lint、类型、单元测试触发）。
- 输入：{ repo_path, file_paths, tests?:bool, project_namespace }
- 输出：{ passed:boolean, report: str, confidence }

19) mcp_security_scan
- 用途：静态安全扫描与依赖漏洞检测。
- 输入：{ repo_path, project_namespace }
- 输出：{ issues:[{id, severity, description}], confidence }

20) mcp_permissions_audit
- 用途：审计资源访问权限与策略。
- 输入：{ resource, project_namespace }
- 输出：{ problems:[...], confidence }

21) mcp_laws_checker
- 用途：法律/合规性初步检查（非法律意见）。
- 输入：{ content, jurisdiction, project_namespace }
- 输出：{ findings:[{issue, severity}], confidence }

22) mcp_philosophy_analysis
- 用途：认知偏差与伦理/辩证分析。
- 输入：{ prompt, project_namespace }
- 输出：{ analysis, confidence }

23) mcp_trend_detector
- 用途：时间序列/日志/大规模数据的趋势洞见。
- 输入：{ series, params, project_namespace }
- 输出：{ trends:[{desc,score}], confidence }

24) mcp_data_cleaner
- 用途：数据清洗/标准化管道。
- 输入：{ dataset, ruleset, project_namespace }
- 输出：{ cleaned_dataset_ref, stats, confidence }

25) mcp_etl_runner
- 用途：执行 ETL 作业并返回运行状态。
- 输入：{ job_spec, project_namespace }
- 输出：{ job_id, status, logs_ref, confidence }

26) mcp_feature_store
- 用途：管理特征存储与快照。
- 输入：{ feature_set, project_namespace }
- 输出：{ status, snapshot_id, confidence }

27) mcp_vectorizer
- 用途：将文本转成向量表示。
- 输入：{ texts:[str], model_name?, project_namespace }
- 输出：{ vectors_ref, dims, confidence }

28) mcp_faiss_index
- 用途：管理 FAISS 索引（构建/查询/持久化）。
- 输入：{ action: 'build'|'query'|'save', payload, project_namespace }
- 输出：{ index_id, results, confidence }

29) mcp_redis_cache
- 用途：短期缓存接口。
- 输入：{ key, value?, ttl?, project_namespace }
- 输出：{ ok, value?, confidence }

30) mcp_sql_writer
- 用途：写入结构化关系型数据。
- 输入：{ table, rows, project_namespace }
- 输出：{ rows_written, transaction_id, confidence }


注：该文件为模板。后续可以将这些 schema 转为 JSON Schema 文件并在 CI 中用 JSON Schema 校验工具自动验证工具实现的响应。
