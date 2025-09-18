# -*- coding: utf-8 -*-

'''
    OathScrapers module
'''



import re

from six import ensure_text
from six.moves import zip

from blackscrapers import parse_qs, urljoin, urlencode, quote_plus
from blackscrapers.modules import cleantitle, client, source_utils, log_utils

from blackscrapers import custom_base_link
custom_base = custom_base_link(__name__)


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['dl.myvideolinks.net', 'myvideolinks.net', 'go.myvid.one']
        self.base_link = custom_base or 'https://go.myvid.one'
        self.search_link = '/?s=%s'
        self.aliases = []


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        try:
            self.aliases.extend(aliases)
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urlencode(url)
            return url
        except Exception:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            self.aliases.extend(aliases)
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urlencode(url)
            return url
        except Exception:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return
            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urlencode(url)
            return url
        except Exception:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:

            if url is None:
                return sources

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']

            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

            query = '%s S%02dE%02d' % (
                title,
                int(data['season']),
                int(data['episode'])) if 'tvshowtitle' in data else '%s %s' % (
                title,
                data['year'])
            query = re.sub(r'(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
            query = self.search_link % quote_plus(query)

            # r = client.request(self.base_link)
            # search_base = client.parseDOM(r, 'form', ret='action')[0]
            # log_utils.log(search_base)

            #r, self.base_link = client.list_request(self.base_link or self.domains, query)
            #log_utils.log('MYVIDEOLINK r: ' + r)

            url = urljoin(self.base_link, query)
            r = client.request(url)
            results = client.parseDOM(r, 'article', attrs={'id': 'post-\d+'})
            if not 'tvshowtitle' in data: results = [i for i in results if data['imdb'] in i]
            p = client.parseDOM(results, 'h2')
            z = zip(client.parseDOM(p, 'a', ret='href'), client.parseDOM(p, 'a'))
            posts = [(i[1], i[0]) for i in z]

            check = hdlr if not 'tvshowtitle' in data else 'S%02d' % int(data['season'])
            check2 = hdlr if not 'tvshowtitle' in data else 'Season %s' % data['season']

            host_dict = hostprDict + hostDict

            items = []

            for post in posts:
                try:
                    if (not source_utils.is_match(post[0], title, check, self.aliases)) and (not source_utils.is_match(post[0], title, check2, self.aliases)):
                        continue
                    r = client.request(post[1])
                    r = ensure_text(r, errors='replace')
                    r = client.parseDOM(r, 'div', attrs={'class': 'entry-content.*?'})[0]

                    if 'tvshowtitle' in data:
                        z1 = zip(re.findall(r'<p><b>(.+?)</b>', r, re.S), re.findall(r'<ul>(.+?)</ul>', r, re.S))
                        z2 = zip(re.findall(r'<h2>(.+?)</h2>', r, re.I|re.S), re.findall(r'<ul>(.+?)</ul>', r, re.S))
                        for z in (z1, z2):
                            for f in z:
                                u = re.findall("'(http.+?)'", f[1]) + re.findall('"(http.+?)"', f[1])
                                u = [i for i in u if '/embed/' not in i]
                                t = f[0]
                                try: s = re.findall(r'((?:\d+\.\d+|\d+\,\d+|\d+|\d+\,\d+\.\d+)\s*(?:GB|GiB|MB|MiB))', t)[0]
                                except: s = '0'
                                items += [(t, i, s) for i in u]

                    else:
                        t = ensure_text(post[0], errors='replace')
                        u = re.findall("'(http.+?)'", r) + re.findall('"(http.+?)"', r)
                        u = [i for i in u if '/embed/' not in i]
                        try: s = re.findall(r'((?:\d+\.\d+|\d+\,\d+|\d+|\d+\,\d+\.\d+)\s*(?:GB|GiB|MB|MiB))', r)[0]
                        except: s = '0'
                        items += [(t, i, s) for i in u]

                except:
                    log_utils.log('MYVIDEOLINK ERROR', 1)
                    pass

            for item in items:
                try:
                    url = ensure_text(item[1])
                    url = client.replaceHTMLCodes(url)

                    void = ('.rar', '.zip', '.iso', '.part', '.png', '.jpg', '.bmp', '.gif', 'sub', 'srt')
                    if url.endswith(void):
                        continue

                    name = ensure_text(item[0], errors='replace')
                    name = cleantitle.get_title(name)
                    if not hdlr.lower() in name.lower():
                        continue

                    # t = re.sub(r'(\.|\(|\[|\s)(\d{4}|S\d*E\d*|S\d*|3D)(\.|\)|\]|\s|)(.+|)', '', name, re.I)
                    # if not cleantitle.get(t) == cleantitle.get(title):
                        # continue
                    # y = re.findall(r'[\.|\(|\[|\s](\d{4}|S\d*E\d*|S\d*)[\.|\)|\]|\s]', name)[-1].upper()
                    # if not y == hdlr:
                        # continue

                    valid, host = source_utils.is_host_valid(url, host_dict)
                    if not valid:
                        continue
                    host = client.replaceHTMLCodes(host)

                    quality, info = source_utils.get_release_quality(name, url)

                    try:
                        dsize, isize = source_utils._size(item[2])
                    except:
                        dsize, isize = 0.0, ''
                    info.insert(0, isize)

                    info = ' | '.join(info)

                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info,
                                    'direct': False, 'debridonly': False, 'size': dsize, 'name': name})
                except:
                    log_utils.log('MYVIDEOLINK ERROR', 1)
                    pass

            return sources
        except:
            log_utils.log('MYVIDEOLINK ERROR', 1)
            return sources


    def resolve(self, url):
        return url
