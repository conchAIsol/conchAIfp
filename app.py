import asyncio
import websockets
import uuid
import os
from aiohttp import web
from characterai import aiocai

class CombinedServer:
    def __init__(self):
        self.user_chats = {}
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_http)
        self.app.router.add_get('/ws', self.handle_websocket)
        static_path = os.path.join(os.path.dirname(__file__), 'static')
        self.app.router.add_static('/static/', static_path)
        
    async def handle_http(self, request):
        # Serve your static files or handle HTTP requests here
        return web.FileResponse('./index.html')  # Adjust path as needed
    
    async def handle_websocket(self, request):
        print('handling')
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        user_sid = str(uuid.uuid4())
        await self.create_chat(user_sid)
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                response = await self.get_message(msg.data, user_sid)
                await ws.send_str(response)
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket connection closed with exception {ws.exception()}')
                
        return ws
    
    async def create_chat(self, user_sid):
        if user_sid not in self.user_chats:
            char = '0yCipW7-xP5kWWT9ptFbvE324QFNbCIZe2gb8AWvlXM'
            client = aiocai.Client('ecf4941c89f3fb09372078ed8cb36b679e6074c9')
            
            me = await client.get_me()
            async with await client.connect() as chat:
                new, answer = await chat.new_chat(char, me.id)
                self.user_chats[user_sid] = new.chat_id
                print('Created new chat:', self.user_chats[user_sid])
                return answer.text
    
    async def get_message(self, user_input, user_sid):
        char = '0yCipW7-xP5kWWT9ptFbvE324QFNbCIZe2gb8AWvlXM'
        client = aiocai.Client('ecf4941c89f3fb09372078ed8cb36b679e6074c9')
        
        if user_sid not in self.user_chats:
            me = await client.get_me()
            async with await client.connect() as chat:
                new, answer = await chat.new_chat(char, me.id)
                self.user_chats[user_sid] = new.chat_id
                return answer.text
        else:
            your_chat = self.user_chats.get(user_sid)
            async with await client.connect() as chat:
                message = await chat.send_message(char, your_chat, user_input)
                return message.text

async def main():
    server = CombinedServer()
    runner = web.AppRunner(server.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    
    print('Server started on port 10000')
    await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
