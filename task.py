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
    news = read_file('news.json')
    comments = read_file('comments.json')

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

    news = read_file('news.json')
    comments = read_file('comments.json')

    current_news = next((x for x in news['news'] if x['id'] == news_id), None)
    if current_news is None:
        raise web.HTTPNotFound()
    elif datetime.strptime(current_news["date"], "%Y-%m-%dT%H:%M:%S") > datetime.now():
        raise web.HTTPNotFound()
    elif current_news['deleted'] == 'true':
        raise web.HTTPNotFound()

    news_comments = [com for com in comments['comments'] if com['news_id'] == news_id]
    news_comments = sorted(news_comments, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%dT%H:%M:%S"))

    result = current_news
    result['comments'] = news_comments
    result['comments_count'] = len(news_comments)

    return web.Response(text=json.dumps(result))


app = web.Application()
app.add_routes([
    web.get('/', all_news),
    web.get('/news/{news_id}', news_by_id)
])

if __name__ == '__main__':
    web.run_app(app)
