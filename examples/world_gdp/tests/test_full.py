import unittest
import json
from pathlib import Path

from full_data import build_dataset, excluded_successors
from render_full import YEAR_SECONDS, frame_state, SCREEN_COPY, split_headline, numeric_tile, render_frame, base_image
from economic_events import load_events as load_economic_events
from mix_bgm import build_filter
from paths import DATA, REFERENCES


class FullRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = build_dataset()

    def test_all_years_and_numeric_top10(self):
        self.assertEqual([row['year'] for row in self.dataset['years']], list(range(1960, 2026)))
        for year in self.dataset['years']:
            self.assertEqual(len(year['top10']), 10)
            self.assertEqual(len({row['code'] for row in year['top10']}), 10)
            self.assertTrue(all(row['value_usd'] > 0 for row in year['top10']))
            self.assertIn('headline', year['event'])

    def test_historical_countries_do_not_overlap_successors(self):
        for year in self.dataset['years']:
            codes = {row['code'] for row in year['candidates']}
            self.assertFalse(codes & excluded_successors(year['year']))
            if year['year'] <= 1991:
                self.assertIn('SUN', codes)
            else:
                self.assertNotIn('SUN', codes)

    def test_estimates_keep_status_and_exact_sources(self):
        years = {row['year']: row for row in self.dataset['years']}
        self.assertEqual(next(row for row in years[1960]['candidates'] if row['code'] == 'SUN')['status'], 'estimated')
        self.assertEqual(next(row for row in years[1991]['candidates'] if row['code'] == 'SUN')['status'], 'estimated')
        self.assertEqual(next(row for row in years[1970]['candidates'] if row['code'] == 'SUN')['status'], 'provider_reported')

    def test_speed_and_minimal_screen_copy(self):
        self.assertEqual(YEAR_SECONDS, 1.6)
        self.assertNotIn('排名', SCREEN_COPY)
        self.assertNotIn('估算', SCREEN_COPY)
        self.assertNotIn('来源', SCREEN_COPY)

    def test_last_frame_has_exact_source_numbers(self):
        for index, year in enumerate(self.dataset['years']):
            with self.subTest(year=year['year']):
                state = frame_state((index + 1) * YEAR_SECONDS - 1 / 30, self.dataset)
                expected = year['top10']
                self.assertEqual([row['code'] for row in state['rows']], [row['code'] for row in expected])
                self.assertEqual([row['value_usd'] for row in state['rows']], [row['value_usd'] for row in expected])

    def test_music_filter_requires_three_tracks_and_normal_tempo(self):
        graph = build_filter(105.6)
        self.assertEqual(graph.count('loudnorm='), 3)
        self.assertEqual(graph.count('acrossfade='), 2)
        self.assertIn('atrim=duration=105.600', graph)
        self.assertNotIn('atempo', graph)

    def test_every_event_is_economically_relevant(self):
        allowed = {'trade', 'monetary', 'finance', 'energy', 'economic_policy', 'debt', 'recession'}
        unrelated = ('奥运', '登月', '航天', '空间站', '玻色子', '黑洞', '核试验', '人权理事会', 'COP30')
        for year, event in load_economic_events().items():
            with self.subTest(year=year):
                self.assertIn(event.get('category'), allowed)
                self.assertTrue(event.get('economic_link'))
                self.assertTrue(event.get('scope'))
                self.assertTrue(event.get('source_url', '').startswith('https://'))
                self.assertFalse(any(word in event['headline'] for word in unrelated))

    def test_selected_replacements_are_economic_not_ceremonial(self):
        events = {year: event['headline'] for year, event in load_economic_events().items()}
        self.assertIn('欧债', events[2012])
        self.assertIn('银行', events[2023])
        self.assertIn('关税', events[2025])

    def test_economic_event_revision_preserves_all_gdp_records(self):
        previous = json.loads((REFERENCES / 'baseline-rankings.json').read_text())
        for old, new in zip(previous['years'], self.dataset['years']):
            self.assertEqual(old['year'], new['year'])
            self.assertEqual(old['top10'], new['top10'])
            self.assertEqual(old['candidates'], new['candidates'])
            self.assertEqual(old['missing_eligible_codes'], new['missing_eligible_codes'])

    def test_event_evidence_is_saved_and_honestly_labelled(self):
        for year in self.dataset['years']:
            with self.subTest(year=year['year']):
                event = year['event']
                if not event['headline']:
                    self.assertEqual(event.get('review_status'), 'not_selected')
                    continue
                self.assertTrue(event.get('evidence_summary'))
                self.assertIn(event.get('review_status'), {'primary_page_fetched', 'search_snapshot_only', 'needs_page_verification'})
                self.assertFalse(event.get('asserted_gdp_cause', True))
                for path in event.get('evidence_files', []):
                    self.assertTrue((DATA / path).is_file())

    def test_approved_sparse_history_and_1991_layout(self):
        events = {year['year']: year['event'] for year in self.dataset['years']}
        selected = {1960,1961,1962,1967,1969,1971,1973,1978,1979,1980,1984,1985,1987,1989,1990,1991,1995,1997,1999,2001,2007,2008,2010,2011,2015,2016,2018,2020,2022,2025}
        self.assertEqual({year for year,event in events.items() if event['headline']}, selected)
        for year,word in {1978:'改革开放',1980:'经济特区',1984:'14',1991:'亚太',1997:'香港回归',1999:'澳门回归',2001:'世界贸易组织',2008:'金融危机',2010:'第二大',2015:'供给侧',2018:'关税',2020:'疫情'}.items():
            self.assertIn(word, events[year]['headline'])
        self.assertEqual(events[1991]['lines'], ['中国加入亚太经合组织', '海湾战争 · 苏联解体'])
        self.assertEqual(split_headline(''), [])

    def test_leading_bar_length_is_constant_and_scale_continuous(self):
        previous_state = None
        for frame_index in range(3168):
            state = frame_state(frame_index/30, self.dataset)
            self.assertAlmostEqual(state['rows'][0]['value_usd']/state['axis_max_usd'], 1/1.08)
            self.assertLessEqual(state['rows'][0]['value_usd'], state['axis_max_usd'])
            previous_state = state
        first = frame_state(1.6-1/30, self.dataset)
        second = frame_state(3.2-1/30, self.dataset)
        self.assertGreater(second['axis_max_usd'], first['axis_max_usd'])

    def test_axis_tracks_actual_leader_during_swap_and_decline(self):
        dataset = {'years': [
            {'year': 2000, 'candidates': [{'code':'USA','value_usd':100,'status':'test'}, {'code':'CHN','value_usd':80,'status':'test'}], 'top10':[{'code':'USA','value_usd':100}], 'event':{}},
            {'year': 2001, 'candidates': [{'code':'USA','value_usd':70,'status':'test'}, {'code':'CHN','value_usd':110,'status':'test'}], 'top10':[{'code':'CHN','value_usd':110}], 'event':{}},
        ]}
        states = [frame_state(frame_index/30, dataset) for frame_index in range(48,96)]
        self.assertEqual(states[0]['rows'][0]['code'], 'USA')
        self.assertEqual(states[-1]['rows'][0]['code'], 'CHN')
        self.assertLess(min(state['axis_max_usd'] for state in states), states[0]['axis_max_usd'])
        for state in states:
            self.assertAlmostEqual(state['axis_max_usd'], max(row['value_usd'] for row in state['rows'])*1.08)

    def test_v7_preserves_v6_gdp_and_history(self):
        previous = json.loads((REFERENCES / 'baseline-rankings.json').read_text())
        self.assertEqual(previous, self.dataset)

    def test_event_text_is_right_of_year_not_at_bottom(self):
        for year in (1978, 1991, 1992):
            image = render_frame((year-1960+1)*YEAR_SECONDS-1/30, self.dataset, base_image())
            gold = lambda pixel: pixel[0] > 150 and pixel[1] > 120 and pixel[2] < 160
            top = image.crop((430, 95, 1010, 225))
            bottom = image.crop((60, 1630, 1020, 1840))
            self.assertEqual(any(gold(pixel) for pixel in top.get_flattened_data()), year != 1992)
            self.assertFalse(any(gold(pixel) for pixel in bottom.get_flattened_data()))
        events = self.dataset['years'][31]['event']
        self.assertEqual(split_headline(events['headline'], 11), events['lines'])
        self.assertTrue(all(len(line) > 3 for line in split_headline(self.dataset['years'][18]['event']['headline'], 11)))

    def test_numbers_follow_bar_tail_with_small_gap_and_fit(self):
        from render_full import bar_geometry, BAR_LEFT, BAR_RIGHT, DISPLAY_DIVISOR, WIDTH
        state = frame_state(105.6-1/30, self.dataset)
        positions = []
        for row in state['rows']:
            geometry = bar_geometry(row, state)
            expected_end = BAR_LEFT+(BAR_RIGHT-BAR_LEFT)*row['value_usd']/state['axis_max_usd']
            self.assertAlmostEqual(geometry['bar_end'], expected_end)
            self.assertLessEqual(abs(geometry['number_x']-expected_end-12), 1)
            self.assertEqual(geometry['number_y'], 50)
            tile = numeric_tile(round(row['value_usd']/DISPLAY_DIVISOR,1),'#FFFFFF')
            self.assertLessEqual(geometry['number_x']+tile.width, WIDTH-30)
            positions.append(geometry['number_x'])
        self.assertGreater(len(set(positions)), 1)

    def test_prominent_header_titles_fit_two_lines(self):
        from render_full import EVENT_FONT_SIZE, EVENT_LINE_CHARACTERS, font
        self.assertGreaterEqual(EVENT_FONT_SIZE, 44)
        for year in self.dataset['years']:
            lines = split_headline(year['event']['headline'], EVENT_LINE_CHARACTERS)
            self.assertLessEqual(len(lines), 2)
            for line in lines:
                self.assertLessEqual(font(EVENT_FONT_SIZE).getlength(line), 565)
        self.assertEqual(split_headline('美国推出“对等关税”政策', 11), ['美国推出', '“对等关税”政策'])
        self.assertEqual(split_headline('改革开放开启，工作重心转向经济建设', 11), ['改革开放开启', '工作重心转向经济建设'])

    def test_hundred_million_usd_unit_and_number_width(self):
        self.assertEqual(SCREEN_COPY, 'GDP · 亿美元')
        state = frame_state(105.6-1/30, self.dataset)
        self.assertAlmostEqual(state['rows'][0]['value_usd']/1e8, 307697, delta=1)
        tile = numeric_tile(round(state['rows'][0]['value_usd']/1e8, 1), '#FFFFFF')
        self.assertLessEqual(tile.width, 211)
        self.assertEqual(tile.height, 50)
        self.assertLess(tile.getbbox()[2], tile.width)

    def test_same_trend_numbers_do_not_pause_at_year_boundary(self):
        for year in (1984, 1991, 2025):
            boundary = (year-1960)*48
            amounts = [next(row['value_usd'] for row in frame_state(index/30,self.dataset)['rows'] if row['code']=='USA') for index in range(boundary-3,boundary+3)]
            increments = [new-old for old,new in zip(amounts,amounts[1:])]
            self.assertTrue(all(increment > 0 for increment in increments))
            self.assertLess(max(increments)/min(increments), 1.3)

    def test_rank_trajectories_have_no_frame_sized_snap(self):
        previous = {}
        for index in range(3168):
            state = frame_state(index/30,self.dataset)
            now = {row['code']:row for row in state['rows']}
            for code in now.keys() & previous.keys():
                self.assertLess(abs(now[code]['position']-previous[code]['position'])*110, 20)
            previous = now

    def test_render_rows_include_smooth_entries_and_exits(self):
        state = frame_state(1551/30,self.dataset)
        self.assertIn('render_rows', state)
        self.assertGreater(len(state['render_rows']), 10)
        self.assertTrue(all(0 <= row['position'] <= 10.5 for row in state['render_rows']))

    def test_subpixel_counter_gap_is_exact(self):
        from render_full import bar_geometry
        state = frame_state(17/30,self.dataset)
        geometry = bar_geometry(state['rows'][4],state)
        self.assertAlmostEqual(geometry['number_x']-geometry['bar_end'],12,places=10)


if __name__ == '__main__':
    unittest.main()
