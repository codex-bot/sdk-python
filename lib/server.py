import aiohttp.web


def http_response(function):
    async def wrapper(self, request):
        text = await request.text()
        headers = request.headers
        params = request.match_info
        query = request.query
        
        try:
            post = await request.post()
        except Exception as e:
            post = {}

        try:
            json = await request.json()
        except Exception as e:
            json = {}

        try:
            result = await function(self, {
                'text': text,
                'post': post,
                'json': json,
                'params': params,
                'headers': headers,
                'query': query
            })
        except Exception as e:
            self.sdk.hawk.catch()
            return aiohttp.web.HTTPInternalServerError()

        response_text = result.get('text', '')
        response_status = result.get('status', 200)
        response_content_type = result.get('content-type')

        if response_status != 404:
            return aiohttp.web.Response(text=response_text, content_type=response_content_type, headers={
                'Access-Control-Allow-Origin': '*'
            })
        else:
            return aiohttp.web.HTTPNotFound(text=response_text, content_type=response_content_type)

    return wrapper


class Server:

    def __init__(self, event_loop, host='127.0.0.1', port=1339):
        self.event_loop = event_loop
        self.host, self.port = host, port
        self.web_server = aiohttp.web.Application(loop=self.event_loop)

    def set_routes(self, routes):
        """
        TODO: Check if route is already defined.
        :param routes:
        :return:
        """
        for route in routes:
            self.web_server.router.add_route(*route)

    def add_static(self, route, path):
        self.web_server.router.add_static(route, path)

    def start(self):
        aiohttp.web.run_app(self.web_server, host=self.host, port=self.port)

    def redirect(self, redirect_uri):
        return aiohttp.web.HTTPFound(redirect_uri)