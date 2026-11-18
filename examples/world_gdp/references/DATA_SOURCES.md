# 数据与素材出处

整理日期：2026-11-18。这里记录来源，不把混合序列称为统一官方历史数据库。

| 本地文件 | 来源与用途 |
|---|---|
| `data/raw/worldbank-gdp.json` | World Bank `NY.GDP.MKTP.CD` 中国及其他经济体1960—2025响应，最后更新字段为2026-11-11；名义现价美元。 |
| `data/raw/worldbank-countries.json` | World Bank经济体元数据，用于排除地区汇总项。 |
| `data/un-historical-gdp.json` | UN National Accounts Main Aggregates Database历史国家摘录，苏联、捷克斯洛伐克、南斯拉夫等；原始文件来源 `https://unstats.un.org/unsd/amaapi/api/file/2`，本目录只保留复现需要的提取结果。 |
| `data/raw/maddison-owid-gdp.csv`、metadata | Maddison Project Database / Our World in Data真实产出代理；仅用于已授权苏联补估比例，不把PPP序列作为现价美元GDP直接排名。 |
| `data/raw/fred-gdpdef-*.csv` | FRED GDPDEF季度价格代理，用于苏联估算，代理不等于苏联实际汇率。 |
| `data/soviet-gdp-1960-1970-method.json` | 1960—1969补估公式、参数、来源与敏感性说明。 |
| `data/soviet-1991-estimate.json` | 1991补估公式、输入哈希；不得去掉估算标签。 |
| `data/all-gdp-source-records-1960-2025.csv` | 已保存的统一来源记录，空值不是零，包含来源/估算状态；原始单位美元。 |
| `references/baseline-rankings.json` | 本次实现回归参考快照，完整候选集/年度Top10/事件信息；不是数据覆盖完整性认证。 |
| `data/raw/*events*` | 公共网页检索结果标题/URL/摘要，排除了内部服务响应元数据。 |
| `references/v4-flag-sources.json`、`sources.json` | 国旗素材及早期参考来源；旗帜年代和国家边界限制保留。 |
| `references/stock-inputs.json` | 本机Mixkit两段免费火焰原视频的下载入口/来源/SHA256。 |
| `references/free-license.html`、`terms.html` | 2026-11-18保存的Mixkit官方页面。视频合成允许的用途和限制应以当前条款为准。 |

Mixkit原始视频存储在Git忽略的 `assets/local-only/`。提交只包含来源/许可/下载器；不把第三方素材原件作为可公开库存包分发。网页快照中的外链仅用于说明，不会自动执行或下载。

本目录不复制所有IMF/UN原始文件、内部搜索接口返回值和多版本成片，以避免不必要体积和隐私风险。此前完整研究档案仍在原项目 `storage/data/world-gdp/`，不随Git提交。
