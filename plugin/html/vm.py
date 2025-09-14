# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
from base.spider import Spider
import json
import re
import base64
from pyquery import PyQuery as pq
from urllib.parse import quote

class Spider(Spider):
    def getName(self):
        return "4KVM"

    def init(self, extend=""):
        self.host = "https://www.4kvm.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        }
        print("============{0}============".format(extend))
        pass

    def get_doc(self, html):
        return pq(html)

    def homeContent(self, filter):
        doc = self.get_doc(self.fetch(self.host, headers=self.headers).text)

        classes = []
        for li in doc('#main_header > li.menu-item').items():
            a = li.find('a')
            href = a.attr('href')
            if href and ('/movies' in href or '/tvshows' in href or '/classify' in href):
                type_id = href.split('/')[-1]
                if not type_id:
                    type_id = href.split('/')[-2]

                type_name = a.text()
                if not li.find('ul.sub-menu'):
                    classes.append({'type_id': type_id, 'type_name': type_name})
                for sub_a in li.find('ul.sub-menu li a').items():
                    sub_href = sub_a.attr('href')
                    sub_type_id = sub_href.split('/')[-1]
                    if not sub_type_id:
                        sub_type_id = sub_href.split('/')[-2]
                    classes.append({'type_id': sub_type_id, 'type_name': sub_a.text()})

        videos = []
        for item in doc('article.item').items():
            link = item.find('div.poster > a')
            href = link.attr('href')
            if not href:
                continue

            parts = [p for p in href.split('/') if p]
            vod_type = parts[-2]
            vod_slug = parts[-1]

            vod_id = f'{vod_type}/{vod_slug}'

            title = item.find('.data h3 a').text()
            pic = item.find('.poster img').attr('src')
            remarks = item.find('.poster .rating').text().strip()

            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remarks
            })

        result = {
            'class': classes,
            'list': videos
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def homeVideoContent(self):
        result = {}
        return result

    def categoryContent(self, tid, pg, filter, extend):
        if not pg:
            pg = '1'

        url_path = f'/{tid}/page/{pg}'
        if tid not in ['movies', 'tvshows', 'imdb', 'trending']:
             url_path = f'/classify/{tid}/page/{pg}'

        url = self.host + url_path
        doc = self.get_doc(self.fetch(url, headers=self.headers).text)

        videos = []
        for item in doc('#archive-content article.item').items():
            link = item.find('div.poster > a')
            href = link.attr('href')
            if not href:
                continue

            parts = [p for p in href.split('/') if p]
            vod_type = parts[-2]
            vod_slug = parts[-1]
            vod_id = f'{vod_type}/{vod_slug}'

            title = item.find('.data h3 a').text()
            pic = item.find('.poster img').attr('src')
            remarks = item.find('.poster .rating').text().strip()

            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remarks
            })

        page_count = 0
        page_text = doc('.pagination span').eq(0).text()
        if page_text:
            match = re.search(r'Page \d+ of (\d+)', page_text)
            if match:
                page_count = int(match.group(1))

        result = {
            'page': int(pg),
            'pagecount': page_count if page_count > 0 else int(pg) + 1,
            'limit': len(videos),
            'total': 999999,
            'list': videos
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def detailContent(self, ids):
        slug = ids[0]
        vod_type, vod_slug = slug.split('/')

        url = f'{self.host}/{vod_type}/{vod_slug}'
        doc = self.get_doc(self.fetch(url, headers=self.headers).text)

        title = doc('.sheader h1').text()
        pic = doc('.sheader .poster img').attr('src')

        vod_director = ''
        vod_actor = ''
        vod_year = ''
        vod_area = ''
        vod_remarks = ''
        vod_type_name = ''

        for item in doc('.sbox .data .extra span').items():
            text = item.text()
            if re.match(r'^\d{4}$', text):
                vod_year = text
            elif '分钟' in text:
                pass
            else:
                vod_area = text

        imdb_rating = doc('.sheader .data .starstruck-rating .dt_rating_vgs').text()
        if imdb_rating:
            vod_remarks = f"IMDb: {imdb_rating}"

        sgeneros = [a.text() for a in doc('.sheader .sgeneros a').items()]
        vod_type_name = '/'.join(sgeneros)

        vod_content = doc('#info .wp-content').text()

        directors = [a.text() for a in doc('#cast .persons').eq(0).find('.name a').items()]
        vod_director = ','.join(directors)

        actors = [a.text() for a in doc('#cast .persons').eq(1).find('.name a').items()]
        vod_actor = ','.join(actors)

        post_id_str = doc('body').attr('class')
        post_id_match = re.search(r'postid-(\d+)', post_id_str)
        if not post_id_match:
            return {}
        post_id = post_id_match.group(1)

        ajax_url = self.host + '/wp-admin/admin-ajax.php'

        vod_play_from = []
        vod_play_url = []

        player_options = doc('#playeroptionsul li')
        for li in player_options.items():
            source_name = li.find('span.title').text()
            nume = li.attr('data-nume')

            params = { 'action': 'dooplay_player_ajax', 'post': post_id, 'nume': nume, 'type': vod_type }
            player_rsp = self.post(ajax_url, data=params, headers=self.headers)
            player_data = player_rsp.json()

            embed_url = ''
            if isinstance(player_data, dict):
                embed_url = player_data.get('embed_url', '')

            vod_play_from.append(source_name)
            vod_play_url.append(f"播放${embed_url}")

        vod = {
            "vod_id": slug, "vod_name": title, "vod_pic": pic,
            "vod_type": vod_type_name, "vod_year": vod_year, "vod_area": vod_area,
            "vod_remarks": vod_remarks, "vod_actor": vod_actor,
            "vod_director": vod_director, "vod_content": vod_content,
            "vod_play_from": "$$$".join(vod_play_from),
            "vod_play_url": "$$$".join(vod_play_url)
        }

        result = {'list': [vod]}
        return json.loads(json.dumps(result, ensure_ascii=False))

    def searchContent(self, key, quick, pg='1'):
        if not pg:
            pg = '1'

        encoded_key = quote(key)
        url = f'{self.host}/xssearch?s={encoded_key}&p={pg}'
        doc = self.get_doc(self.fetch(url, headers=self.headers).text)

        videos = []
        for item in doc('div.search-page .result-item').items():
            article = item.find('article')
            if not article:
                continue

            link = article.find('.image .thumbnail a')
            href = link.attr('href')
            if not href:
                continue

            parts = [p for p in href.split('/') if p]
            if len(parts) < 2:
                continue
            vod_type = parts[-2]
            vod_slug = parts[-1]
            vod_id = f'{vod_type}/{vod_slug}'

            title = article.find('.details .title a').text()
            pic = article.find('.image img').attr('src')
            remarks = article.find('.details .meta .rating').text().strip()

            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remarks
            })

        result = {
            'list': videos
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def playerContent(self, flag, id, vipFlags):
        result = {
            'parse': 1,
            'url': id,
        }
        return result
