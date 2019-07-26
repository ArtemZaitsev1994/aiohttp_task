from aiohttp.test_utils import TestClient, TestServer, loop_context
from aiohttp import web
import json
from datetime import datetime
import collections


def read_file(name):
    name: str

    with open(name, 'r', encoding='utf-8') as f:
        result = json.load(f)
    return result


async def all_news(request):
    news = read_file('news_for_test.json')
    comments = read_file('comments_for_test.json')

    sorted_news = sorted(news['news'], key=lambda x: datetime.strptime(x["date"], "%Y-%m-%dT%H:%M:%S"))
    sorted_news = (x for x in sorted_news)
    comments = (x for x in comments['comments'])

    comments_counts = collections.defaultdict(int)
    for com in comments:
        comments_counts[com['news_id']] += 1

    news = [
        {**n, "comments_count": comments_counts.get(n['id'], None)}
        for n in sorted_news
        if datetime.strptime(n["date"], "%Y-%m-%dT%H:%M:%S") <= datetime.now() and n['deleted'] != 'true'
    ]
    result = {'news': news, 'news_count': len(news)}

    return web.Response(text=json.dumps(result))


async def news_by_id(request):
    news_id = request.match_info.get('news_id', 1)
    try:
        news_id = int(news_id)
    except ValueError:
        raise web.HTTPNotFound()

    news = read_file('news_for_test.json')

    current_news = next((x for x in news['news'] if x['id'] == news_id), None)
    if current_news is None:
        raise web.HTTPNotFound()
    elif datetime.strptime(current_news["date"], "%Y-%m-%dT%H:%M:%S") > datetime.now():
        raise web.HTTPNotFound()
    elif current_news['deleted'] == 'true':
        raise web.HTTPNotFound()

    comments = read_file('comments_for_test.json')
    news_comments = [com for com in comments['comments'] if com['news_id'] == news_id]
    news_comments = sorted(news_comments, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%dT%H:%M:%S"))

    result = current_news
    result['comments'] = news_comments
    result['comments_count'] = len(news_comments)

    return web.Response(text=json.dumps(result))


with loop_context() as loop:
    app = web.Application()
    app.add_routes([
        web.get('/', all_news),
        web.get('/news/{news_id}', news_by_id)
    ])
    client = TestClient(TestServer(app), loop=loop)
    loop.run_until_complete(client.start_server())
    root = "http://127.0.0.1:8080"

    async def test_all_news():
        resp = await client.get("/")
        assert resp.status == 200
        news = await resp.json(content_type='text/plain')
        # news = json.loads(text)
        # id новостей, 3-я новость с датой выше текущей, 5-ая новость удалена
        checkup_list = [1, 2, 4]
        # количество комментариев к каждой новости
        comments_counts = [5, 2, 1]
        got_news = []
        got_comments = []
        for x in news['news']:
            got_news.append(x['id'])
            got_comments.append(x['comments_count'])
        assert len(got_news) <= len(checkup_list), 'Got more news than needed'
        assert len(got_news) >= len(checkup_list), 'Got not all the news'
        assert got_news == checkup_list, 'News are not in right order'
        assert got_comments == comments_counts, 'Not right comments'
        print('All the test are passed for "all_news"')

    async def test_news_by_id():
        resp = await client.get("/news/2")
        assert resp.status == 200
        news = await resp.json(content_type='text/plain')
        # id коментариев
        checkup_list = [2, 4]
        got_comments = [x['id'] for x in news['comments']]

        assert news['id'] == 2, 'Got not right news'
        assert len(news['comments']) <= len(checkup_list), 'Got more comments than needed'
        assert len(news['comments']) >= len(checkup_list), 'Got not all the comments'
        assert got_comments == checkup_list, 'Comments are not in right order'
        print('All the test are passed for "news_by_id"')

    loop.run_until_complete(test_all_news())
    loop.run_until_complete(test_news_by_id())
    loop.run_until_complete(client.close())
