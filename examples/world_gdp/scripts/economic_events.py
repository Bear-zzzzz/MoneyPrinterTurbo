import json
from functools import lru_cache
from pathlib import Path
from paths import DATA


IMF_HISTORY = 'https://www.imf.org/external/pubs/ft/survey/sup0998/14.htm'
FED_RECESSION = 'https://www.federalreservehistory.org/essays/recession-of-1981-82'
FED_CRISIS = 'https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath'
EURO = 'https://www.ecb.europa.eu/euro/intro/html/index.en.html'
OMT = 'https://www.ecb.europa.eu/press/pr/date/2012/html/pr120906_1.en.html'
WTO_HISTORY = 'https://www.wto.org/english/thewto_e/history_e/history_e.htm'
SILENT_REVOLUTION = 'https://www.imf.org/external/pubs/ft/silent/index.htm'

RECORDS = [
    (1960, 'OPEC成立，协调石油政策', 'energy', '国际石油市场', '产油国协调供给和石油政策，关系能源成本与出口收入。', 'https://history.state.gov/historicaldocuments/frus1958-60v04/d314'),
    (1961, '经合组织成立，推进经济合作', 'economic_policy', '成员经济体与国际政策合作', '建立经济政策比较与合作机制，不等同于当年全球需求冲击。', 'https://www.oecd.org/en/about/history.html'),
    (1962, '欧洲共同农业政策启动', 'economic_policy', '欧洲农业与国际农产品贸易', '农业补贴、价格支持和贸易安排影响农产品供给及财政支出。', 'https://agriculture.ec.europa.eu/common-agricultural-policy/cap-overview/cap-glance_en'),
    (1963, 'IMF设立出口补偿融资机制', 'finance', '出口收入受冲击的成员经济体', '针对出口收入短缺提供国际收支融资支持。', IMF_HISTORY),
    (1964, '肯尼迪回合启动关税谈判', 'trade', 'GATT参与经济体', '多边谈判以关税削减及贸易规则为重点，影响跨境交易成本。', WTO_HISTORY),
    (1965, '美加汽车协定促进产业整合', 'trade', '北美汽车产业链', '取消多数双边汽车及零部件关税，推动跨境分工。', 'https://www.chicagofed.org/publications/economic-perspectives/1978/jul-aug-part4-hervey'),
    (1966, '美国信贷紧缩冲击融资', 'finance', '美国信贷与金融市场', '货币紧缩和金融机构融资压力影响信贷供给及投资。', 'https://www.richmondfed.org/-/media/richmondfedorg/publications/research/working_papers/1993/pdf/wp93-2.pdf'),
    (1967, '英镑贬值冲击固定汇率体系', 'monetary', '英国与国际货币市场', '英镑平价调整影响贸易计价和固定汇率体系信心。', 'https://history.blog.gov.uk/2017/11/17/whats-the-context-18-november-1967-devaluation-of-sterling/'),
    (1968, '黄金总库瓦解，金价双轨化', 'monetary', '国际黄金与储备体系', '黄金干预合作瓦解，官方与私人市场价格分离。', 'https://www.elibrary.imf.org/display/book/9781451971477/ch020.xml'),
    (1969, '特别提款权制度正式确立', 'monetary', 'IMF成员与国际储备体系', '第一次协定修订确立SDR机制，为国际储备提供补充工具。', IMF_HISTORY),
    (1970, '首批特别提款权开始分配', 'monetary', '国际储备体系', '首批SDR分配增加参与经济体的国际储备资产。', IMF_HISTORY),
    (1971, '美元停止兑换黄金', 'monetary', '全球货币与汇率体系', '美元黄金兑换窗口关闭，改变战后货币体系运行基础。', IMF_HISTORY),
    (1972, '国际货币体系改革谈判启动', 'monetary', '国际货币体系', '二十国委员会成立，讨论固定汇率体系危机后的制度改革。', IMF_HISTORY),
    (1973, '石油禁运引发能源危机', 'energy', '全球能源、价格与生产', '石油供应冲击推高进口成本并影响通胀与经济活动。', 'https://www.federalreservehistory.org/essays/oil-shock-of-1973-74'),
    (1974, 'IMF石油融资机制应对冲击', 'finance', '受油价冲击的进口经济体', '石油融资机制缓解能源涨价造成的国际收支压力。', IMF_HISTORY),
    (1975, '石油融资补贴支持低收入国', 'finance', '低收入石油进口经济体', '设立补贴账户，降低符合条件成员的石油融资成本。', IMF_HISTORY),
    (1976, '牙买加协议重塑货币体系', 'monetary', '国际货币与储备体系', '货币改革协议为汇率安排与黄金地位的改变提供框架。', IMF_HISTORY),
    (1977, 'IMF设立补充融资机制', 'finance', '面临国际收支困难的成员', '建立补充融资工具，增加国际收支援助能力；并非当年即生效。', IMF_HISTORY),
    (1978, 'IMF修约承认多元汇率安排', 'monetary', '国际汇率制度', '第二次协定修订生效，成员可选择不同汇率安排。', IMF_HISTORY),
    (1979, '第二次石油冲击推高成本', 'energy', '全球能源与通胀', '石油供给与价格冲击增加进口负担，推动通胀压力。', 'https://www.federalreservehistory.org/essays/oil-shock-of-1978-79'),
    (1980, '美国经济衰退，紧缩承压', 'recession', '美国及其贸易金融伙伴', '高通胀与反通胀政策背景下，需求、就业和信贷承压。', FED_RECESSION),
    (1981, '沃尔克紧缩，衰退再度开始', 'monetary', '美国与美元融资市场', '高利率抑制通胀，同时增加借款成本并压低经济活动。', FED_RECESSION),
    (1982, '拉美债务危机爆发', 'debt', '拉美借款国与国际银行', '外债偿付困难冲击国际银行、资本流动和地区投资。', 'https://www.federalreservehistory.org/essays/latin-american-debt-crisis'),
    (1983, 'IMF增资扩大危机融资能力', 'finance', '国际金融安全网', '份额增加与借款安排扩大，提高债务危机时期的融资能力。', IMF_HISTORY),
    (1984, '美元走强，加剧贸易失衡', 'monetary', '美元市场与主要贸易经济体', '美元升值改变出口竞争力及美元计价债务负担。', SILENT_REVOLUTION),
    (1985, '广场协议协调汇率调整', 'monetary', '主要工业国与全球外汇市场', '主要经济体协调政策，推动美元汇率调整。', 'https://www.nber.org/system/files/working_papers/w21813/w21813.pdf'),
    (1986, 'IMF结构调整融资机制设立', 'finance', '低收入发展中经济体', '优惠融资应对国际收支困难，并与经济结构调整相联系。', IMF_HISTORY),
    (1987, '黑色星期一冲击全球股市', 'finance', '国际股票与流动性市场', '股市急跌考验市场流动性和金融稳定。', 'https://www.federalreservehistory.org/essays/stock-market-crash-of-1987'),
    (1988, '巴塞尔协议确立银行资本标准', 'finance', '国际银行监管', '统一银行资本充足率框架，影响风险管理及跨境银行竞争。', 'https://www.bis.org/publications/198807-standards-international-convergence-capital-measurement-and-capital-standards'),
    (1989, '布雷迪计划推动外债减免', 'debt', '高负债新兴经济体与债权银行', '债务减免与债务工具重组缓解外债负担。', IMF_HISTORY),
    (1990, '欧洲货币联盟第一阶段启动', 'monetary', '欧洲资本与货币市场', '成员间资本流动限制原则上取消，推进经济货币一体化。', 'https://www.ecb.europa.eu/ecb/history-arts-culture/history/emu/html/index.en.html'),
    (1991, '苏联解体，统一经济体系分裂', 'economic_policy', '前苏联地区及贸易伙伴', '国家解体改变货币、财政和供应网络；不把年度GDP变化全归于此。', 'https://www.imf.org/external/region/bal/rr/2014/25_years_of_transition.pdf'),
    (1992, '欧洲汇率机制遭遇危机', 'monetary', '欧洲外汇与资本市场', '汇率压力与投机冲击迫使部分货币退出或调整汇率安排。', 'https://ies.princeton.edu/pdf/S84.pdf'),
    (1993, '欧洲单一市场正式运行', 'trade', '欧洲及其贸易伙伴', '商品、服务、资本和人员流动的一体化改变交易成本与市场准入。', 'https://ec-europa-eu.libguides.com/SingleMarket/achievements/eu'),
    (1994, '马拉喀什协定重塑贸易规则', 'trade', '多边贸易体系', '签署建立WTO的协定，扩展多边贸易规则覆盖范围。', 'https://www.wto.org/english/docs_e/legal_e/legal_e.htm'),
    (1995, '世界贸易组织正式成立', 'trade', '多边贸易体系', 'WTO开始运行，形成贸易谈判、规则与争端解决机制。', 'https://www.wto.org/english/docs_e/legal_e/legal_e.htm'),
    (1996, '重债穷国减债倡议获认可', 'debt', '重债低收入经济体与国际债权人', 'IMF与世界银行联合减债倡议获得委员会认可。', IMF_HISTORY),
    (1997, '亚洲金融危机爆发', 'finance', '亚洲与国际资本市场', '汇率和资本流动逆转引发债务、银行及经济活动压力。', 'https://www.federalreservehistory.org/essays/asian-financial-crisis'),
    (1998, '俄罗斯违约冲击国际金融', 'debt', '俄罗斯与全球投资市场', '政府债务与汇率危机造成资产重估和风险传染。', 'https://unctad.org/system/files/official-document/poirrsd002.en.pdf'),
    (1999, '欧元启动，汇率正式锁定', 'monetary', '欧元区及国际外汇市场', '参与国实行共同货币和统一货币政策，减少区内汇率风险。', EURO),
    (2000, '互联网泡沫破裂，科技股下跌', 'finance', '美国科技股与国际资本市场', '科技资产估值回调冲击融资和投资，非所有国家同步衰退。', 'https://guides.loc.gov/business-booms-busts/dot-com-real-estate'),
    (2001, '中国加入世界贸易组织', 'trade', '中国与全球贸易网络', '市场准入和贸易规则承诺推动中国进一步融入全球贸易体系。', 'https://www.wto.org/english/thewto_e/countries_e/china_e.htm'),
    (2002, '欧元现金开始流通', 'monetary', '欧元区支付与商品市场', '共同纸币和硬币替换国家现金，改变支付和价格比较方式。', EURO),
    (2003, '坎昆贸易谈判未达成共识', 'trade', 'WTO成员与多边贸易谈判', '部长级谈判受阻，影响多哈议程及贸易开放进程。', 'https://www.wto.org/english/forums_e/public_forum12_e/art_pf12_e/art10.htm'),
    (2004, '欧盟扩大，单一市场扩容', 'trade', '欧洲与跨境产业链', '新成员加入扩大单一市场覆盖，改变贸易、投资和劳动力流动。', 'https://ec-europa-eu.libguides.com/SingleMarket/achievements/eu'),
    (2005, '人民币汇率形成机制改革', 'monetary', '中国与国际贸易外汇市场', '人民币转向参考一篮子货币的有管理浮动，改变汇率运行机制。', 'https://www.frbsf.org/research-and-insights/publications/economic-letter/2005/09/a-look-at-china-new-exchange-rate-regime/'),
    (2006, '美国房价见顶，楼市转弱', 'finance', '美国住房信贷与金融市场', '住房价格转折削弱抵押贷款资产质量，为后续金融压力提供背景。', 'https://guides.loc.gov/business-booms-busts/dot-com-real-estate'),
    (2007, '次贷危机引发信贷市场动荡', 'finance', '美国与国际信贷市场', '房贷违约和证券化资产压力传入资金市场。', FED_CRISIS),
    (2008, '雷曼破产，金融危机加剧', 'finance', '全球金融与实体经济', '大型金融机构失败加剧流动性危机和全球风险收缩。', FED_CRISIS),
    (2009, '全球衰退，政策救助展开', 'recession', '全球主要经济体', '金融危机后的经济收缩推动财政、货币及金融救助。', FED_CRISIS),
    (2010, '欧债危机，主权融资承压', 'debt', '欧元区与国际债券市场', '主权偿付风险、银行资产敞口和融资成本相互传导。', 'https://www.ecb.europa.eu/pub/pdf/annrep/ar2012en.pdf'),
    (2011, '欧债危机蔓延，融资收紧', 'debt', '欧元区银行与主权债券市场', '主权风险与银行融资压力强化，影响信贷和投资。', 'https://www.ecb.europa.eu/pub/pdf/annrep/ar2012en.pdf'),
    (2012, '欧债危机下，ECB公布OMT', 'debt', '欧元区债券与货币政策传导', '公布有条件的二级市场国债交易框架，并非当年实际启动购债。', OMT),
    (2013, '缩减恐慌冲击新兴市场', 'monetary', '美国与新兴经济体资本市场', '宽松退出预期推高收益率，扰动汇率与跨境资本流动。', 'https://www.federalreserve.gov/econres/notes/feds-notes/u-s-interest-rates-and-emerging-market-currencies-taking-stock-10-years-after-the-taper-tantrum-20231004.html'),
    (2014, '国际油价大跌，能源收入受压', 'energy', '全球能源及进出口经济体', '油价下跌改变能源贸易收入、进口成本与能源投资。', 'https://www.imf.org/external/pubs/ft/fandd/2015/12/baffes.htm'),
    (2015, '欧洲央行扩大资产购买', 'monetary', '欧元区及国际金融市场', '扩大资产购买压低融资成本，应对低通胀压力。', 'https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1956.en.pdf'),
    (2016, '脱欧公投增加贸易投资不确定性', 'trade', '英国、欧洲与国际投资者', '未来市场准入安排不确定，影响汇率、投资和贸易预期。', 'https://www.ecb.europa.eu/press/economic-bulletin/html/eb201606.en.html'),
    (2017, 'WTO贸易便利化协定生效', 'trade', 'WTO成员与跨境物流', '海关流程与规则改革旨在减少贸易摩擦和通关成本。', 'https://www.wto.org/english/tratop_e/tradfa_e/tradfa_agreement_e.htm'),
    (2018, '中美关税争端升级', 'trade', '中美与全球供应链', '关税提高跨境贸易成本并影响产业链布局和投资预期。', 'https://ustr.gov/issue-areas/enforcement/section-301-investigations/tariff-actions'),
    (2019, '全球贸易放缓，外需承压', 'trade', '国际商品贸易与主要出口经济体', '贸易疲弱反映外部需求和贸易摩擦压力，非单一日期事件。', 'https://media.un.org/unifeed/en/asset/d237/d2375114'),
    (2020, '疫情冲击全球生产与贸易', 'recession', '全球供应链与需求', '防疫限制和需求变化冲击生产及跨境贸易；不采用当时预测跌幅作最终数据。', 'https://www.wto.org/english/news_e/pres20_e/pr855_e.htm'),
    (2021, '贸易反弹，供应链瓶颈加剧', 'trade', '全球贸易与物流网络', '贸易需求恢复伴随运输和供应瓶颈，增加成本压力。', 'https://www.wto.org/english/res_e/booksp_e/wtsr_2022_c3_e.pdf'),
    (2022, '能源冲击叠加通胀压力', 'energy', '全球能源、物价与贸易', '战争引发能源与商品市场扰动，加剧通胀和购买力压力。', 'https://www.wto.org/english/res_e/booksp_e/wtsr_2022_c3_e.pdf'),
    (2023, '硅谷银行倒闭，银行风险升温', 'finance', '美国银行与国际金融市场', '银行倒闭引发存款、流动性和金融稳定担忧。', 'https://www.federalreserve.gov/publications/review-of-the-federal-reserves-supervision-and-regulation-of-silicon-valley-bank.htm'),
    (2024, '欧洲央行降息25个基点', 'monetary', '欧元区与国际利率市场', '6月降息调整货币限制程度，影响借贷成本和金融条件。', 'https://www.ecb.europa.eu/press/economic-bulletin/html/eb202404.en.html'),
    (2025, '美国对等关税政策冲击贸易', 'trade', '美国贸易伙伴与全球供应链', '关税政策改变市场准入成本，增加贸易和供应链不确定性；不推断全年GDP因果。', 'https://unctad.org/publication/global-trade-update-april-2025-escalating-tariffs-impact-small-and-vulnerable-economies'),
]


@lru_cache(maxsize=1)
def load_events():
    snapshots = {}
    for path in sorted((DATA / 'raw/economic-events').glob('*.json')):
        try:
            response = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        for result in response.get('results', []):
            url = result.get('url', '')
            if url and result.get('snippet'):
                snapshots.setdefault(url, []).append(str(path.relative_to(DATA)))
    events = {}
    for year, headline, category, scope, economic_link, source in RECORDS:
        evidence_files = sorted(set(snapshots.get(source, [])))
        status = 'search_snapshot_only' if evidence_files else 'needs_page_verification'
        if source == IMF_HISTORY:
            evidence_files.append('raw/economic-events/imf-chronology.txt')
            status = 'primary_page_fetched'
        events[year] = {
            'headline': headline, 'category': category, 'scope': scope,
            'economic_link': economic_link, 'source_url': source,
            'evidence_summary': economic_link,
            'evidence_files': evidence_files, 'review_status': status,
            'asserted_gdp_cause': False,
            'review_note': 'Editorial economic context; saved search snippets do not equal full-page fact checking.',
        }
    if sorted(events) != list(range(1960, 2026)) or len(RECORDS) != 66:
        raise ValueError('Exactly one economic event per year from 1960 through 2025 is required')
    return events
