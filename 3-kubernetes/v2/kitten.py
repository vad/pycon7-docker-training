from aiohttp import web


async def kitten(request):
    return web.Response(body=b'ROAAAAR')


def main():
    app = web.Application()
    app.router.add_route('GET', '/', kitten)
    web.run_app(app, port=6000)


if __name__ == "__main__":
    main()
