---
name: travel-research-maps
description: Research travel destinations with Firecrawl-backed multi-platform social and travel evidence, score worthwhile attractions and restaurants, and prepare auditable Chinese venue lists without day-by-day itineraries; only after explicit approval, save uniquely matched places into a chosen Google Maps list. Automatically use when the user asks to travel somewhere, make a travel plan, see a place's tourist attractions, find travel food recommendations, or curate travel places into Google Maps, including Chinese requests such as “去哪里旅游”“做个旅游计划”“看一下哪里的旅游景点”.
---

# 旅行研究与地图收藏

为给定目的地制作可审核的旅行地点清单。默认输出中文，不使用固定旅行偏好。

## 必需输入

先确认或从请求中提取：目的地、旅行日期或时间范围。可选输入为语言、指定来源和已有 Google Maps 列表名。

若用户未提供日期，使用“计划前往日期未知”，仍研究研究日向前 365 天内的内容；将季节性、临时闭馆和预约信息标为需要在出行前复核。

## 工作流

1. 阅读 `references/scoring-rubric.md`，按其规则收集和标注证据。
2. 使用 Firecrawl MCP 作为主研究路径，收集研究日向前 365 天内公开可访问的旅行内容。优先使用 `mcp__firecrawl.firecrawl_search` 发现候选 URL，再对有价值页面使用 `mcp__firecrawl.firecrawl_scrape` 或 `mcp__firecrawl.firecrawl_extract` 抽取正文和结构化证据；当站内 URL 难定位时，少量使用 `mcp__firecrawl.firecrawl_map`；只有搜索、抓取和 map 都无法完成复杂跨站研究时，才将 `mcp__firecrawl.firecrawl_agent` 作为最后 fallback。
   - 每次使用 `mcp__firecrawl.firecrawl_search` 并处理结果后，立即调用 `mcp__firecrawl.firecrawl_search_feedback`，标注有价值来源或缺失内容。
   - 若 Firecrawl MCP 不可用，报告阻塞原因；不得把内置 web search 当作等价替代。
   - 中国大陆目的地以小红书和 Bilibili 为主，其他社交或旅行来源作为补充；港澳台或跨境目的地按实际可访问平台混合处理。
   - 中国大陆之外目的地以小红书、YouTube、Instagram 和公开旅行内容为主；Bilibili、X 和其他平台作为补充。Google Maps 只用于地址、营业状态、关闭风险和地点匹配核验。
   - 不绕过登录墙、验证码、付费墙、地区限制或反爬机制；不可公开抓取、缺日期、缺作者或缺明确推荐立场的内容不得计分，只记录覆盖缺口。
   - 将“浏览一篇内容”限定为：读取正文或可核验页面内容，并识别作者或频道、发布日期和推荐立场；仅看到搜索结果摘要、转载聚合页或无法打开的链接均不计入浏览量。
   - 景点与餐厅分别满足硬性覆盖门槛后，才可进入评分：景点至少浏览 10 篇相关内容并形成至少 10 个不同景点的候选清单；餐厅至少浏览 10 篇相关内容并形成至少 5 家不同餐厅的候选清单。两类内容和候选数量不得相互抵扣。
   - 在审计数据中分别记录景点/餐厅的已浏览内容数、每篇 URL、来源平台、作者或频道、日期及最终候选数。任一门槛未满足时，停止后续评分、事实核验、审核清单和地图写入；只报告覆盖不足与具体缺口，不得输出部分地点清单。
3. 为每个候选记录名称、类别、链接、来源平台、作者或频道、日期、推荐档位、是否营销、内容指纹和一句摘要。排除广告、赞助、商业合作、探店邀约、店方/品牌账号、优惠码、返佣链接或导购内容。
4. 确认上述景点与餐厅覆盖门槛均已满足后，将候选证据写成 JSON，运行：

   ```bash
   python scripts/score_candidates.py --input evidence.json --output scored.json --as-of YYYY-MM-DD --min-positive-platforms-for-priority 2
   ```

   在当前日期不等于出行日期时，`--as-of` 使用研究当天日期。脚本只做去重、计分和分层；Firecrawl 研究、Google Maps 核验和事实核验由本工作流完成。
5. 对“优先去”和“备选”地点核验事实。门票、预约、营业/闭馆信息优先使用官方来源；官网缺失时才使用预约平台、场馆官方社媒、Google 商家页或近期旅行平台，并标记为“非官方核验”。Google Maps 评论不直接计入推荐分，但可产生 `hard_risks`，例如永久关闭、地点不匹配或多来源一致的重大服务问题。
6. 先输出审核清单，禁止在此阶段写入 Google Maps。只输出“景点”和“餐厅”两组地点，不提供按天、按时段或路线式行程。每项使用以下固定格式：

   ```markdown
   **地点名称**｜开放/营业：时间或“未确认”｜预约：需要/建议/不需要/未确认
   一句话介绍。
   附加：景点写门票、最后入场、闭馆日、官网与多平台证据；餐厅写菜系、招牌、预算、地址/街区、官网或订位渠道与多平台证据。标注净分、独立正向来源数、正向平台、信息可信度和待确认事项。
   ```

   按评分层级排序，但不要另行生成“第几天去哪里”的建议。对无有效社媒或旅行证据的地点标为“待确认”，不得因评分不足暗示其不值得前往。
7. 明确请求人工批准。默认全选“优先去”，用户可回复“加入全部，排除 A、B；使用列表 X”或要求新建“目的地·日期”列表。未得到批准时，结束于地点审核清单。
8. 获得批准后，使用已登录的 Google Maps 浏览器会话。对每项搜索“名称 + 目的地”，核验名称和地址/城市一致后保存到用户指定或新建的列表。结果不唯一、关闭或无法匹配时不保存，并报告原因。
9. 核对列表内已保存的数量，报告已保存、跳过、待确认项目。保留该列表页面作为交付页。

## 审核与安全边界

- 不得把未核验的搜索摘要当作内容证据；无法打开或识别内容时降低覆盖度并说明缺口。
- 同一作者、转载或相同素材只算一个独立来源。优先项目不代表保证可订位或实时营业。
- 出现永久关闭、食品安全、地点不匹配或多来源一致的重大服务问题时，标为排除，不进入默认地图写入范围。
- Google Maps 写入是外部副作用：仅在用户明确批准审核清单及目标列表后执行。不要读取 Cookie、密码或其他浏览器会话数据。
- 无法使用 Google Maps 或用户未登录时，保留审核清单并说明阻塞原因；不要尝试替代账号或上传私人数据。

## 资源

- `references/scoring-rubric.md`：推荐档位、独立性、广告、风险、多平台可信度和事实核验规则。
- `scripts/score_candidates.py`：确定性评分器及 JSON 输入输出约定。
- `scripts/test_score_candidates.py`：评分器的回归测试。
