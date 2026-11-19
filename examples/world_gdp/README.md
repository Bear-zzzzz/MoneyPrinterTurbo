# 世界 GDP 动态榜与四幕分镜

本目录将此前位于 Git 忽略的 `storage/` 中的实现整理为可提交示例。无需模型 API；使用 Python/Pillow 绘图、FFmpeg 编码。

## 目录

- `scripts/`：数据构建、连续位次/数字轨迹、全片及分镜渲染、音乐合成、素材获取与文件校验。
- `tests/`：数据、动画、文字、火焰遮罩与分镜回归测试。
- `data/`：1960—2025 世界银行原始响应、联合国历史国家摘录、苏联估算输入/方法及统一来源 CSV。`value_usd` 始终为美元，视频显示为亿美元。
- `assets/flags/`：国旗及历史旗帜素材，出处在 `references/`。
- `references/`：固定排名快照、素材来源/许可及 SHA256 清单；公共事件检索摘录保存在 `data/raw/`。
- `assets/local-only/`：Mixkit 原始视频。本机已经放入；**Git 忽略**，不是可公开再分发的素材包。
- `output/`：成片、预览和新导出数据，Git 忽略，避免提交所有历史版本。
- `deliverables/`：随提交附带的最新v16火焰预览（5秒）与v9完整时间轴成片（105.6秒），两者均无音轨；详细区别见该目录README。

## 安装与测试

从项目根目录执行；需要 `ffmpeg`、`ffprobe` 位于 PATH。使用 Python 3.11+。

```bash
python -m pip install -r examples/world_gdp/requirements.txt
python examples/world_gdp/scripts/check_bundle.py
python examples/world_gdp/tests/run_tests.py
```

字体复用项目已有 `resource/fonts/STHeitiMedium.ttc`，不重复拷贝53MB字体。所有路径按文件位置解析，不依赖开发者主目录或原 `storage/`。

## 生成视频

```bash
# 1960—2025 全片，105.6秒，连续计数/位次，Top1长度固定
python examples/world_gdp/scripts/render_full.py

# 四幕30秒，无火焰、底部留空（推荐主版本）
python examples/world_gdp/scripts/render_four_acts.py --clean

# 淡入淡出＋国家聚焦19.2秒样片
python examples/world_gdp/scripts/render_storyboard.py

# 现成火焰5秒合成预览（本机素材已就绪）
python examples/world_gdp/scripts/render_stock_fire.py

# 校验实际生成的视频（全量解码）
python examples/world_gdp/scripts/verify_render.py examples/world_gdp/output/world-gdp-stock-fire-v16-preview.mp4 --duration 5
```

如新检出项目没有火焰输入，审阅官方许可和条款后获取：

```bash
python examples/world_gdp/scripts/fetch_stock_fire.py --accept-license
```

下载器仅处理已记录的一个免费条目，验证当前页面许可和下载 SHA256；不会购买、登录、绕过校验或去除水印。素材版本/许可变化时拒绝下载，需重新核对。

现成火焰来自 Mixkit 3759，原始文件是黑底 RGB 视频，不是原生透明视频；用黑底 matte 提取透明层，等比裁片、平铺羽化、随柱长裁剪、数字置顶遮罩。52302 是本地备用素材，不是正式预览输入。原始文件不随 Git 或分享压缩包分发，项目内保留许可和下载清单。

曾试过的手绘火焰脚本为回归/历史方案保留：`--bar-flame`、`--side-fire`、`--power-aura`，不作为推荐效果。较早 `render_demo.py` 的数字翻滚仅是历史实验；新 `render_full.py` 不采用数字翻滚。

## 计划使用的 BGM

按以下顺序播放，用于营造激情、紧张的氛围：

1. **CHASHKAKEFIRA — BARRETE!**
2. **CHASHKAKEFIRA — COLLAR!**
3. **Lunak — PASSO FUNK**

当前仅记录歌曲名称，实际音频文件与使用授权尚未提供；提交随附的视频仍无音轨，不表示音乐已合成。提供文件后可执行：

```bash
python examples/world_gdp/scripts/mix_bgm.py --music /path/BARRETE.mp3 /path/COLLAR.mp3 /path/PASSO_FUNK.mp3
```

## 数据与许可限制

- 跨来源试排，不是已认证的完整历史全球 Top10。东德及部分历史国家缺年仍未解决，当前国旗也未全部逐年核验。
- 苏联1960—1969、1991是用户授权模型估算，原状态与方法保留；苏联身份退出不等于 GDP 归零，不用俄罗斯替代。
- 美元名义GDP受汇率/价格/修订影响，不是实际经济增速。年度之间数字/位次是动画插值，不是观察到的月度值。
- 年度终值与源数据精确一致；事件仅为时代背景，不是GDP变化的因果解释。
- `data/raw/*events*` 仅保留公共来源标题、URL和摘要，未复制内部检索接口元数据；完整页面核验状态在记录中说明。
- 第三方数据、旗帜、字体和视频遵循各自许可，来源清单不等于统一授权；发布前检查目标用途的许可。不要把火焰原视频当独立素材库公开分发。

## 提交

```bash
git status --short -- examples/world_gdp .gitignore
git add .gitignore examples/world_gdp
```

本次整理不自动暂存或提交。不要用 `git add -f` 强行加入 `assets/local-only/` 或 `output/`。

修改示例文件后可运行 `python examples/world_gdp/scripts/refresh_manifest.py` 更新清单；新清单不能替代数据审校。`check_bundle.py` 只校验文件完整性，不认证数据历史覆盖完整。
