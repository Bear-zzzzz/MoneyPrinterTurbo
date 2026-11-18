from full_data import STYLES
from render_full import FPS, YEAR_SECONDS, frame_state


START_SECONDS = (2001-1960)*YEAR_SECONDS
DURATION = round(12*YEAR_SECONDS,1)


def fade_envelope(elapsed, duration, fade):
    if elapsed <= 0 or elapsed >= duration:
        return 0
    fraction=min(1,elapsed/fade,(duration-elapsed)/fade)
    return fraction*fraction*(3-2*fraction)


def build_storyboard(dataset):
    period=[year for year in dataset['years'] if 2001 <= year['year'] <= 2012]
    eligible={row['code'] for row in period[-1]['top10']}
    records=[]
    for code in sorted(eligible):
        values=[next((row for row in year['candidates'] if row['code']==code),None) for year in period]
        if any(row is None or row['status']!='provider_reported' for row in values):
            continue
        first,last=values[0]['value_usd'],values[-1]['value_usd']
        records.append({'code':code,'first_usd':first,'last_usd':last,'increase_usd':last-first,'ratio':last/first})
    absolute=max(records,key=lambda row:row['increase_usd'])
    relative=max(records,key=lambda row:row['ratio'])
    crossing=None
    for index in range(round(DURATION*FPS)):
        state=frame_state(START_SECONDS+index/FPS,dataset)
        values={row['code']:row['value_usd'] for row in state['render_rows']}
        if values['CHN']>=values['JPN']:
            crossing=index/FPS
            break
    if crossing is None:
        raise ValueError('No CHN/JPN crossing in selected demo period')
    return {
        'period':[2001,2012],'start_global_seconds':START_SECONDS,'duration_seconds':DURATION,
        'comparison_scope':'2012 Top10 with complete provider-reported annual records from2001 through2012',
        'focus_candidates':records,'absolute_focus':absolute,'relative_focus':relative,
        'crossing_seconds':crossing,'crossing_note':'Interpolated animation crossing, not a historical calendar date',
        'scenes':[
            {'kind':'era','start':0,'end':2,'codes':[],'title':'2001—2012 · 全球化与危机'},
            {'kind':'absolute','start':2,'end':6,'codes':[absolute['code']],
             'title':f'{STYLES[absolute["code"]][0]} · 阶段增量约{absolute["increase_usd"]/1e8:,.0f}亿美元'},
            {'kind':'relative','start':6.5,'end':9,'codes':[relative['code']],
             'title':f'{STYLES[relative["code"]][0]} · 总量约为期初{relative["ratio"]:.2f}倍'},
            {'kind':'crisis','start':11.2,'end':12.8,'codes':[],'title':'2008 · 全球金融危机'},
            {'kind':'crossing','start':crossing-0.9,'end':crossing+1.3,'codes':['CHN','JPN'],'title':'中日GDP位次交替'},
            {'kind':'summary','start':17,'end':18.6,'codes':[absolute['code']],
             'title':f'{STYLES[absolute["code"]][0]} · 回看阶段总量增量'},
        ],
        'metrics_note':'Nominal current-USD endpoint change among eligible final-year Top10, not real growth or certified worldwide champion',
    }


def presentation_at(seconds, story):
    local_frame=round(seconds*FPS)%round(YEAR_SECONDS*FPS)
    result={'header_opacity':fade_envelope(local_frame/FPS,YEAR_SECONDS-1/FPS,0.2),
            'scene_opacity':0,'strength':0,'codes':[],'caption':'','kind':'main'}
    for scene in story['scenes']:
        if scene['start'] <= seconds < scene['end']:
            opacity=fade_envelope(seconds-scene['start'],scene['end']-scene['start'],0.3)
            result.update({'kind':scene['kind'],'codes':scene['codes'],'caption':scene['title'],
                           'scene_opacity':opacity,'strength':opacity})
            break
    return result
