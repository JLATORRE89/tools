import ast, asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
p=Path(__import__('os').environ['OPENWEBUI_PACKAGE_DIR']) / 'utils/middleware.py'
f=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='chat_image_generation_handler')
class Generated(BaseException):pass
async def check(saved,stored,submitted,expected):
 async def generate(**kw):
  assert kw['form_data']['prompt']==expected,kw
  raise Generated()
 def last(msgs):return next((m['content'] for m in reversed(msgs) if m['role']=='user'),None)
 env={'Request':object,'Config':SimpleNamespace(get=AsyncMock(return_value=True)), 'Chats':SimpleNamespace(get_chat_by_id_and_user_id=AsyncMock(return_value=SimpleNamespace(chat={'history':{'messages':stored,'currentId':'x'}}))), 'is_saved_chat_id':lambda _:saved,'get_message_list':lambda m,i:m,'get_last_user_message':last,'get_images_from_messages':lambda m:[], 'CreateImageForm':lambda **k:k,'image_generations':generate}
 # Disable prompt rewriting and editing, enable image generation.
 async def config(k):return k=='image_generation.enable'
 env['Config'].get=config
 exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),'exec'),env)
 try:await env[f.name](None,{'messages':submitted},{'__metadata__':{'chat_id':'test'},'__event_emitter__':AsyncMock()},SimpleNamespace(id='test'))
 except Generated:return
 raise AssertionError('Generation not reached')
async def main():
 u=lambda x:[{'role':'user','content':x}]
 await check(True,[],u('house with trees'),'house with trees')
 await check(True,u('stored prompt'),u('submitted prompt'),'stored prompt')
 await check(False,[],u('new prompt'),'new prompt')
 print('3 chat image prompt regression cases passed')
asyncio.run(main())
