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
        return "耐看点播"

    def init(self, extend=""):
        self.host = "https://nkdvd.me"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        }
        print("============{0}============".format(extend))
        pass

    def get_doc(self, html):
        return pq(html)

    def homeContent(self, filter):
        rsp = self.fetch(self.host, headers=self.headers)
        doc = self.get_doc(rsp.text)

        classes = []
        for a in doc('ul.navbar-items > li > a').items():
            href = a.attr('href')
            if href and 'type' in href:
                type_name = a.find('span').text()
                if not type_name:
                    type_name = a.text()
                type_id_match = re.search(r'(\d+)', href)
                if type_id_match:
                    type_id = type_id_match.group(1)
                    classes.append({'type_name': type_name, 'type_id': type_id})

        videos = []
        for item in doc('a.module-poster-item').items():
            href = item.attr('href')
            name = item.attr('title')
            if not href or not name:
                continue
            vid_match = re.search(r'/video/(\d+)\.html', href)
            if vid_match:
                vid = vid_match.group(1)
                pic = item.find('img').attr('data-original')
                remark = item.find('.module-item-note').text()
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": self.host + pic if pic and not pic.startswith('http') else pic,
                    "vod_remarks": remark
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

        url = f'{self.host}/type/{tid}-{pg}.html'
        if pg == '1':
            url = f'{self.host}/type/{tid}.html'

        rsp = self.fetch(url, headers=self.headers)
        doc = self.get_doc(rsp.text)

        videos = []
        for item in doc('a.module-poster-item').items():
            href = item.attr('href')
            name = item.attr('title')
            if not href or not name:
                continue
            vid_match = re.search(r'/video/(\d+)\.html', href)
            if vid_match:
                vid = vid_match.group(1)
                pic = item.find('img').attr('data-original')
                remark = item.find('.module-item-note').text()
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": self.host + pic if pic and not pic.startswith('http') else pic,
                    "vod_remarks": remark
                })

        result = {
            'page': int(pg),
            'pagecount': 9999,
            'limit': len(videos),
            'total': 999999,
            'list': videos
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def detailContent(self, ids):
        vod_id = ids[0]
        url = f'{self.host}/video/{vod_id}.html'
        rsp = self.fetch(url, headers=self.headers)
        doc = self.get_doc(rsp.text)

        info_main = doc('.module-info-main')
        name = info_main.find('h1').text()
        pic = doc('.module-info-poster .module-item-pic img').attr('data-original')
        pic = self.host + pic if pic and not pic.startswith('http') else pic

        vod_director = ''
        vod_actor = ''
        vod_year = ''
        vod_area = ''
        vod_remarks = ''
        vod_type = ''

        for item in info_main.find('.module-info-item').items():
            title_element = item.find('.module-info-item-title')
            if not title_element:
                continue
            title = title_element.text()
            content_element = item.find('.module-info-item-content')
            if not content_element:
                continue
            content = content_element.text()
            if '导演' in title:
                vod_director = content
            elif '主演' in title:
                vod_actor = content
            elif '备注' in title:
                vod_remarks = content

        tag_links = info_main.find('.module-info-tag-link a')
        if len(tag_links) > 0:
            vod_year = tag_links.eq(0).text()
        if len(tag_links) > 1:
            vod_area = tag_links.eq(1).text()
        if len(tag_links) > 2:
            type_texts = [tag_links.eq(i).text() for i in range(2, len(tag_links))]
            vod_type = '/'.join(type_texts)

        vod_content = doc('.module-info-introduction-content').text()

        vod_play_from = [a.text() for a in doc('.module-tab-item span').items()]

        vod_play_url = []
        for panel in doc('.module-play-list').items():
            episodes = []
            for a in panel.find('a').items():
                episodes.append(f"{a.text()}${a.attr('href')}")
            vod_play_url.append('#'.join(episodes))

        vod = {
            "vod_id": vod_id, "vod_name": name, "vod_pic": pic,
            "vod_type": vod_type, "vod_year": vod_year, "vod_area": vod_area,
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
        url = f'{self.host}/vodsearch/page/{pg}/wd/{encoded_key}.html'

        rsp = self.fetch(url, headers=self.headers)
        doc = self.get_doc(rsp.text)

        videos = []
        for item in doc('.module-card-item').items():
            poster_link = item.find('a.module-card-item-poster')

            href = poster_link.attr('href')
            if not href:
                continue

            vid_match = re.search(r'/video/(\d+)\.html', href)
            if vid_match:
                vid = vid_match.group(1)
                name = item.find('.module-card-item-title a').text()
                pic = poster_link.find('img').attr('data-original')
                remark = poster_link.find('.module-item-note').text()

                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": self.host + pic if pic and not pic.startswith('http') else pic,
                    "vod_remarks": remark
                })

        result = {
            'list': videos
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def playerContent(self, flag, id, vipFlags):
        url = self.host + id
        rsp = self.fetch(url, headers=self.headers)
        html_content = rsp.text

        match = re.search(r'var player_.*?=\s*(.*?)</script>', html_content)
        if not match:
            return {}

        json_str = match.group(1).strip()
        if json_str.endswith(';'):
            json_str = json_str[:-1]

        try:
            player_data = json.loads(json_str)
            video_url = player_data.get('url', '')
            encrypt = player_data.get('encrypt', 0)

            if encrypt == 1:
                self.log(f"AES encrypted URL found for {url}, not supported yet.")
                return {}
            elif video_url:
                video_url = base64.b64decode(video_url).decode('utf-8', errors='ignore')
        except Exception as e:
            self.log(f"Failed to process player data for {url}: {e}")
            return {}

        result = {
            'parse': 0,
            'url': video_url,
            'header': json.dumps({'Referer': url})
        }

        return result

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass
