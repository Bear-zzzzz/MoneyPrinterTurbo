import csv
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from historical_events import load_events
from paths import DATA, OUTPUT


ROOT = OUTPUT
SOVIET_REPUBLICS = {'RUS', 'UKR', 'BLR', 'MDA', 'EST', 'LVA', 'LTU', 'ARM', 'AZE', 'GEO', 'KAZ', 'KGZ', 'TJK', 'TKM', 'UZB'}
YUGOSLAV_REPUBLICS = {'SVN', 'HRV', 'BIH', 'MKD', 'SRB', 'MNE', 'XKX'}
STYLES = {
    'USA': ('美国', '#59A8FF', 'us'), 'SUN': ('苏联', '#F56268', 'SUN'),
    'CHN': ('中国', '#E88745', 'cn'), 'JPN': ('日本', '#F0A0BD', 'jp'),
    'DEU': ('德国', '#E5BE68', 'de'), 'FRA': ('法国', '#9A8AE8', 'fr'),
    'GBR': ('英国', '#5DD6CE', 'gb'), 'ITA': ('意大利', '#72C692', 'it'),
    'CAN': ('加拿大', '#E8ABCD', 'ca'), 'IND': ('印度', '#C6CD70', 'in'),
    'BRA': ('巴西', '#69D998', 'br'), 'AUS': ('澳大利亚', '#58B8D1', 'au'),
    'ARG': ('阿根廷', '#91C6E4', 'ar'), 'MEX': ('墨西哥', '#55B385', 'mx'),
    'NLD': ('荷兰', '#F0AA63', 'nl'), 'ESP': ('西班牙', '#E4C546', 'es'),
    'KOR': ('韩国', '#BCB2F5', 'kr'), 'RUS': ('俄罗斯', '#CC778C', 'ru'),
    'CSK': ('捷克斯洛伐克', '#73BCE8', 'CSK'), 'YUG': ('南斯拉夫', '#C978E7', 'YUG'),
}
V4_EVENT_HEADLINES = {
    1960: '石油输出国组织成立', 1961: '加加林完成首次载人航天飞行',
    1962: '古巴导弹危机', 1963: '部分禁止核试验条约签署',
    1964: '东京奥运会举行', 1965: '联合国开发计划署成立',
    1966: '联合国通过两项国际人权公约', 1967: '外层空间条约生效',
    1968: '不扩散核武器条约开放签署', 1969: '阿波罗11号登月',
    1970: '不扩散核武器条约生效', 1971: '联合国大会通过第2758号决议',
    1972: '斯德哥尔摩人类环境会议', 1973: '石油禁运与能源危机',
    1974: '罗马世界粮食会议', 1975: '赫尔辛基最后文件签署',
    1976: '蒙特利尔奥运会举行', 1977: '旅行者1号与2号发射',
    1978: '戴维营协议签署', 1979: '第二次石油危机',
    1980: '莫斯科奥运会举行', 1981: '航天飞机完成首次飞行',
    1982: '联合国海洋法公约开放签署', 1983: 'ARPANET切换到TCP/IP协议',
    1984: '洛杉矶奥运会举行', 1985: '保护臭氧层维也纳公约通过',
    1986: '切尔诺贝利核事故', 1987: '蒙特利尔议定书通过',
    1988: '汉城奥运会举行', 1989: '柏林墙开放',
    1990: '德国统一', 1991: '苏联解体', 1992: '里约地球峰会举行',
    1993: '欧洲联盟正式成立', 1994: '马拉喀什协定签署',
    1995: '世界贸易组织成立', 1996: '全面禁止核试验条约开放签署',
    1997: '京都议定书通过', 1998: '国际空间站开始在轨组装',
    1999: '欧元正式启动', 2000: '联合国千年首脑会议举行',
    2001: '美国发生九一一袭击', 2002: '欧元纸币与硬币开始流通',
    2003: 'SARS疫情引发国际公共卫生应对', 2004: '印度洋地震与海啸',
    2005: '京都议定书生效', 2006: '联合国人权理事会成立',
    2007: 'IPCC发布第四次评估报告', 2008: '全球金融危机加剧',
    2009: '甲型H1N1流感大流行', 2010: '海地发生强烈地震',
    2011: '日本大地震与福岛核事故', 2012: 'CERN宣布发现新玻色子',
    2013: '一带一路倡议提出', 2014: '西非埃博拉疫情',
    2015: '巴黎协定通过', 2016: '英国举行脱欧公投',
    2017: '双中子星并合多信使观测公布', 2018: '中美贸易摩擦升级',
    2019: '首张黑洞图像公布', 2020: '新冠疫情被宣布为大流行',
    2021: 'COVAX启动全球疫苗交付', 2022: '俄乌战争全面升级',
    2023: 'WHO结束新冠国际紧急状态', 2024: '巴黎奥运会举行',
    2025: '巴西贝伦举行COP30气候大会',
}
V4_EVENT_SOURCES = {
    1960: 'https://www.opec.org/brief-history.html',
    1961: 'https://www.nasa.gov/history/60-years-ago-yuri-gagarin-becomes-the-first-human-in-space/',
    1962: 'https://history.state.gov/milestones/1961-1968/cuban-missile-crisis',
    1963: 'https://history.state.gov/milestones/1961-1968/limited-ban',
    1965: 'https://www.undp.org/about-us',
    1966: 'https://www.ohchr.org/en/what-are-human-rights/international-bill-human-rights',
    1967: 'https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/introouterspacetreaty.html',
    1968: 'https://www.armscontrol.org/factsheets/timeline-nuclear-nonproliferation-treaty-npt',
    1969: 'https://www.nasa.gov/mission/apollo-11/',
    1970: 'https://www.armscontrol.org/factsheets/timeline-nuclear-nonproliferation-treaty-npt',
    1971: 'https://digitallibrary.un.org/record/192054/files/A_RES_2758%28XXVI%29-EN.pdf',
    1972: 'https://www.un.org/en/conferences/environment/stockholm1972',
    1973: 'https://history.state.gov/milestones/1969-1976/oil-embargo',
    1974: 'https://history.state.gov/historicaldocuments/frus1969-76ve14p1/d153',
    1975: 'https://history.state.gov/milestones/1969-1976/helsinki',
    1977: 'https://science.nasa.gov/mission/voyager/',
    1978: 'https://history.state.gov/milestones/1977-1980/camp-david',
    1979: 'https://www.federalreservehistory.org/essays/oil-shock-of-1978-79',
    1981: 'https://www.nasa.gov/mission/sts-1/',
    1982: 'https://www.un.org/depts/los/convention_agreements/convention_historical_perspective.htm',
    1983: 'https://www.internetsociety.org/internet/history-internet/brief-history-internet/',
    1985: 'https://ozone.unep.org/treaties/vienna-convention',
    1986: 'https://www.iaea.org/topics/chornobyl',
    1987: 'https://ozone.unep.org/treaties/montreal-protocol',
    1989: 'https://history.state.gov/milestones/1989-1992/fall-of-communism',
    1990: 'https://history.state.gov/milestones/1989-1992/german-reunification',
    1991: 'https://history.state.gov/milestones/1989-1992/collapse-soviet-union',
    1992: 'https://www.un.org/en/conferences/environment/rio1992',
    1993: 'https://www.consilium.europa.eu/en/maastricht-treaty/',
    1994: 'https://www.wto.org/english/docs_e/legal_e/04-wto_e.htm',
    1995: 'https://www.wto.org/english/thewto_e/25y_e/25ytimeline_e.htm',
    1996: 'https://www.ctbto.org/our-mission/the-treaty',
    1997: 'https://unfccc.int/kyoto_protocol',
    1998: 'https://www.nasa.gov/international-space-station/',
    1999: 'https://www.ecb.europa.eu/euro/intro/html/index.en.html',
    2000: 'https://www.un.org/en/conferences/environment/newyork2000',
    2001: 'https://www.911memorial.org/learn',
    2002: 'https://www.ecb.europa.eu/euro/intro/html/index.en.html',
    2003: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7106085/',
    2004: 'https://www.un.org/en/observances/tsunami-awareness-day',
    2005: 'https://unfccc.int/kyoto_protocol',
    2006: 'https://www.ohchr.org/en/hr-bodies/hrc/about-council',
    2007: 'https://www.ipcc.ch/assessment-report/ar4/',
    2008: 'https://www.imf.org/external/pubs/ft/wp/2010/wp1044.pdf',
    2009: 'https://www.cdc.gov/orr/responses/h1n1-influenza-pandemic.html',
    2010: 'https://www.un.org/en/observances/haiti-earthquake-remembrance-day',
    2011: 'https://www.iaea.org/topics/response/fukushima-daiichi-nuclear-accident',
    2012: 'https://home.cern/science/physics/higgs-boson',
    2013: 'https://greenfdc.org/belt-and-road-initiative-about/',
    2014: 'https://archive.cdc.gov/www_cdc_gov/media/releases/2016/p0707-history-ebola-response.html',
    2015: 'https://unfccc.int/process-and-meetings/the-paris-agreement',
    2016: 'https://www.electoralcommission.org.uk/research-reports-and-data/our-reports-and-data-past-elections-and-referendums',
    2017: 'https://www.ligo.caltech.edu/page/press-release-gw170817',
    2018: 'https://ustr.gov/issue-areas/enforcement/section-301-investigations/tariff-actions',
    2019: 'https://eventhorizontelescope.org/press-release-april-10-2019-astronomers-capture-first-image-black-hole',
    2020: 'https://www.who.int/director-general/speeches/detail/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020',
    2021: 'https://www.who.int/initiatives/act-accelerator/covax',
    2022: 'https://research.un.org/en/docs/ga/quick/emergency',
    2023: 'https://www.who.int/news/item/05-05-2023-statement-on-the-fifteenth-meeting-of-the-international-health-regulations-(2005)-emergency-committee-regarding-the-coronavirus-disease-(covid-19)-pandemic',
    2025: 'https://unfccc.int/cop30',
}
for olympic_year, city in ((1964, 'tokyo'), (1976, 'montreal'), (1980, 'moscow'),
                           (1984, 'los-angeles'), (1988, 'seoul'), (2024, 'paris')):
    V4_EVENT_SOURCES[olympic_year] = f'https://olympics.com/en/olympic-games/{city}-{olympic_year}'


def excluded_successors(year):
    excluded = set()
    if year <= 1991:
        excluded.update(SOVIET_REPUBLICS)
    if year <= 1992:
        excluded.update({'CZE', 'SVK'})
    if year <= 1991:
        excluded.update(YUGOSLAV_REPUBLICS)
    return excluded


def load_growth_and_prices():
    growth = {}
    with (DATA / 'raw/maddison-owid-gdp.csv').open() as source:
        for row in csv.DictReader(source):
            if row['Entity'] in ('USSR', 'Czechoslovakia', 'Yugoslavia'):
                growth.setdefault(row['Entity'], {})[int(row['Year'])] = float(row['GDP'])
    quarterly = {}
    with (DATA / 'raw/fred-gdpdef-1960-1992.csv').open() as source:
        for row in csv.DictReader(source):
            value = float(row['GDPDEF'])
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Invalid price input')
            quarterly.setdefault(int(row['observation_date'][:4]), []).append(value)
    if any(len(values) != 4 for values in quarterly.values()):
        raise ValueError('Four quarterly values required for every year')
    return growth, {year: sum(values) / 4 for year, values in quarterly.items()}


@lru_cache(maxsize=1)
def build_dataset():
    events = load_events()
    wb = json.loads((DATA / 'raw/worldbank-gdp.json').read_text())
    country_meta = json.loads((DATA / 'raw/worldbank-countries.json').read_text())[1]
    eligible = {row['id'] for row in country_meta if row['region']['id'] != 'NA'}
    by_year = {year: [] for year in range(1960, 2026)}
    for row in wb[1]:
        year = int(row['date'])
        code = row['countryiso3code']
        if code in eligible - excluded_successors(year) and row['value'] is not None and row['value'] > 0:
            by_year[year].append({'code': code, 'value_usd': row['value'],
                                  'status': 'provider_reported', 'source': 'World Bank'})
    historical = json.loads((DATA / 'un-historical-gdp.json').read_text())['records']
    mapping = {'USSR (Former)': ('SUN', 1991), 'Czechoslovakia (Former)': ('CSK', 1992),
               'Yugoslavia (Former)': ('YUG', 1991)}
    for country in historical:
        if country['country'] not in mapping:
            continue
        code, last_year = mapping[country['country']]
        for year, value in country['values_usd'].items():
            if 1960 <= int(year) <= last_year:
                by_year[int(year)].append({'code': code, 'value_usd': value,
                                           'status': 'provider_reported', 'source': 'UN National Accounts'})
    with (DATA / 'soviet-gdp-1960-1970-estimates.csv').open() as source:
        for row in csv.DictReader(source):
            if row['status'] == 'estimated':
                by_year[int(row['year'])].append({'code': 'SUN', 'value_usd': float(row['value_usd']),
                    'status': 'estimated', 'source': 'UN-1970 anchored real-output and dollar-price proxy'})
    growth, prices = load_growth_and_prices()
    soviet = next(row for row in historical if row['country'] == 'USSR (Former)')
    anchor = soviet['values_usd']['1990']
    estimate = anchor * growth['USSR'][1991] / growth['USSR'][1990] * prices[1991] / prices[1990]
    by_year[1991].append({'code': 'SUN', 'value_usd': estimate, 'status': 'estimated',
                         'source': 'UN-1990 anchor × USSR real-output ratio × BEA/FRED price ratio'})
    years = []
    for year, candidates in sorted(by_year.items()):
        candidates.sort(key=lambda row: (-row['value_usd'], row['code']))
        top = candidates[:10]
        if len(top) != 10 or len({row['code'] for row in top}) != 10:
            raise ValueError(f'Invalid top ten for {year}')
        for row in top:
            if row['code'] not in STYLES:
                raise ValueError(f'Missing style: {row["code"]}')
        years.append({'year': year, 'top10': top, 'candidates': candidates,
                      'event': events[year],
                      'missing_eligible_codes': sorted(eligible - excluded_successors(year) - {row['code'] for row in candidates}),
                      'complete_global_historical_ranking_certified': False})
    return {'metric': 'Nominal GDP, current USD', 'retrieved_on': '2026-11-17',
            'wb_lastupdated': wb[0]['lastupdated'], 'years': years,
            'estimated_soviet_1991': {'value_usd': estimate, 'anchor_1990_usd': anchor,
                'real_ratio': growth['USSR'][1991] / growth['USSR'][1990],
                'price_ratio': prices[1991] / prices[1990]},
            'limitations': ['Cross-source full-period picture draft, not a certified complete historical world ranking.',
                'USSR 1960–1969 and 1991 are model estimates, not observed dollar GDP.',
                'Former Czechoslovakia and Yugoslavia participate where UN data exists (1970–1990); their missing years remain missing.',
                'East Germany is not falsely replaced with West Germany; East German separate nominal series remains unresolved and is not ranked.',
                'Germany before 1990 is displayed as West Germany; pre-unification territorial coverage is a documented limitation.',
                'Historical identity cutoffs use annual display conventions; successor republic overlaps are excluded.',
                'Use caution about early close rankings and missing historical states.',
                'Flag-era changes require individual review; current assets are not guaranteed contemporaneous for every year.',
                'Events are historical background, never asserted as sole causes of GDP changes.',
                'Source/estimation information is retained here despite removing explanatory on-screen text.']}


def save_dataset():
    dataset = build_dataset()
    (ROOT / 'v9-full-rankings.json').write_text(json.dumps(dataset, ensure_ascii=False, indent=2))
    with (ROOT / 'world-gdp-top10-1960-2025-draft.csv').open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['year', 'rank', 'code', 'value_usd', 'status', 'source'])
        writer.writeheader()
        for year in dataset['years']:
            for index, record in enumerate(year['top10']):
                writer.writerow({'year': year['year'], 'rank': index + 1, **record})
    events = [{**year['event'], 'year': year['year']} for year in dataset['years']]
    (ROOT / 'world-history-events-1960-2025-v9.json').write_text(json.dumps(events, ensure_ascii=False, indent=2))
    (ROOT / 'soviet-1991-estimate.json').write_text(json.dumps({
        **dataset['estimated_soviet_1991'], 'status': 'estimated', 'year': 1991,
        'formula': 'UN1990_USD × USSR_real1991/real1990 × mean_GDPDEF1991/mean_GDPDEF1990',
        'limits': 'Model approximation; dollar-price proxy not actual Soviet exchange rate.',
        'input_sha256': {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in
                         ('un-historical-gdp.json', 'raw/maddison-owid-gdp.csv', 'raw/fred-gdpdef-1960-1992.csv')},
    }, ensure_ascii=False, indent=2))
    print('Saved 66 years / 660 top-ten entries /', sum(bool(event['headline']) for event in events), 'selected event years.')
    print('Soviet 1991 estimate USD billions:', dataset['estimated_soviet_1991']['value_usd'] / 1e9)
    print('Entrants:', sorted({row['code'] for year in dataset['years'] for row in year['top10']}))
    return dataset


if __name__ == '__main__':
    save_dataset()
