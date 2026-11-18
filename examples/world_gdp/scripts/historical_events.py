import json
from functools import lru_cache
from pathlib import Path
from paths import DATA


REFORM = 'https://www.12371.cn/2018/12/17/ARTI1545002856640593.shtml'
FED_CRISIS = 'https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath'
RETURNS = 'https://www.dswxyjy.org.cn/n1/2022/0408/c244516-32394271.html'
RECORDS = {
    1960: (['石油输出国组织成立'], ['https://history.state.gov/historicaldocuments/frus1958-60v04/d314']),
    1961: (['柏林墙修建，冷战分裂加深'], ['https://history.state.gov/milestones/1953-1960/berlin-crises']),
    1962: (['古巴导弹危机'], ['https://history.state.gov/milestones/1961-1968/cuban-missile-crisis']),
    1967: (['第三次中东战争'], ['https://history.state.gov/milestones/1961-1968/arab-israeli-war-1967']),
    1969: (['阿波罗11号，人类首次登月'], ['https://www.nasa.gov/mission/apollo-11/']),
    1971: (['美元停止兑换黄金'], ['https://www.federalreservehistory.org/essays/gold-convertibility-ends']),
    1973: (['第一次石油危机'], ['https://www.federalreservehistory.org/essays/oil-shock-of-1973-74']),
    1978: (['改革开放开启，工作重心转向经济建设'], [REFORM]),
    1979: (['第二次石油危机'], ['https://www.federalreservehistory.org/essays/oil-shock-of-1978-79']),
    1980: (['深圳等经济特区设立'], [REFORM]),
    1984: (['开放14个沿海港口城市'], [REFORM]),
    1985: (['广场协议签署'], ['https://www.nber.org/system/files/working_papers/w21813/w21813.pdf']),
    1987: (['黑色星期一，全球股市暴跌'], ['https://www.federalreservehistory.org/essays/stock-market-crash-of-1987']),
    1989: (['柏林墙开放，东西方格局转折'], ['https://history.state.gov/milestones/1989-1992/fall-of-communism']),
    1990: (['德国统一'], ['https://history.state.gov/milestones/1989-1992/german-reunification']),
    1991: (['中国加入亚太经合组织', '海湾战争 · 苏联解体'], ['https://www.apec.org/Meeting-Papers/Annual-Ministerial-Meetings/1991/1991_amm', 'https://history.state.gov/milestones/1989-1992/gulf-war', 'https://history.state.gov/milestones/1989-1992/collapse-soviet-union']),
    1995: (['世界贸易组织成立'], ['https://www.wto.org/english/thewto_e/history_e/history_e.htm']),
    1997: (['香港回归祖国'], [RETURNS]),
    1999: (['澳门回归祖国'], [RETURNS]),
    2001: (['中国加入世界贸易组织'], ['https://www.wto.org/english/thewto_e/countries_e/china_e.htm']),
    2007: (['次贷危机，金融风险开始蔓延'], [FED_CRISIS]),
    2008: (['全球金融危机全面爆发'], [FED_CRISIS]),
    2010: (['中国成为世界第二大经济体'], ['https://www.stats.gov.cn/sj/zxfb/202303/t20230301_1919243.html']),
    2011: (['日本大地震与福岛核事故'], ['https://www.iaea.org/topics/response/fukushima-daiichi-nuclear-accident']),
    2015: (['供给侧结构性改革提出'], ['https://www.gov.cn/xinwen/2015-11/10/content_5006868.htm']),
    2016: (['英国脱欧公投'], ['https://commonslibrary.parliament.uk/research-briefings/cbp-7639/']),
    2018: (['中美关税摩擦升级'], ['https://ustr.gov/about-us/policy-offices/press-office/press-releases/2018/june/ustr-issues-tariffs-chinese-products']),
    2020: (['新冠疫情冲击生产与消费'], ['https://www.stats.gov.cn/xxgk/jd/sjjd2020/202101/t20210119_1812635.html']),
    2022: (['俄乌战争全面升级'], ['https://news.un.org/en/story/2022/02/1112592']),
    2025: (['美国推出“对等关税”政策'], ['https://unctad.org/publication/global-trade-update-april-2025-escalating-tariffs-impact-small-and-vulnerable-economies']),
}


@lru_cache(maxsize=1)
def load_events():
    snapshots = {}
    for path in sorted((DATA / 'raw').rglob('*.json')):
        try:
            response = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(response, dict):
            continue
        for result in response.get('results', []):
            if result.get('url') and result.get('snippet'):
                snapshots.setdefault(result['url'], set()).add(str(path.relative_to(DATA)))
    events = {}
    for year in range(1960, 2026):
        lines, sources = RECORDS.get(year, ([], []))
        evidence_files = sorted({path for source in sources for path in snapshots.get(source, [])})
        source_records = [{'url': source, 'review_status': 'search_snapshot_only' if source in snapshots else 'needs_page_verification',
                           'evidence_files': sorted(snapshots.get(source, []))} for source in sources]
        status = 'not_selected' if not lines else ('search_snapshot_only' if all(source in snapshots for source in sources) else 'needs_page_verification')
        events[year] = {
            'headline': '\n'.join(lines), 'lines': lines, 'selected': bool(lines),
            'source_url': sources[0] if sources else '', 'sources': source_records,
            'evidence_files': evidence_files, 'review_status': status,
            'evidence_summary': 'User-approved representative history selection; source review status is recorded separately.' if lines else '',
            'selection': 'User-approved list; other years intentionally blank',
            'asserted_gdp_cause': False,
            'review_note': 'Historical context, not a causal explanation of annual GDP or rank. Search snippets do not equal full-page verification.',
        }
    return events
