from pathlib import Path
import py_compile
p=Path(__import__('os').environ['OPENWEBUI_PACKAGE_DIR']) / 'utils/middleware.py';s=p.read_text();a=s.index('async def chat_image_generation_handler');b=s.index('\nasync def ',a+10)
part=s[a:b];old='    user_message = get_last_user_message(message_list)\n\n    prompt = user_message'
new='''    user_message = get_last_user_message(message_list)
    # Normalized/new chats can have no user turn in the stored history yet.
    # The submitted payload still carries the current user prompt.
    if not user_message:
        message_list = form_data.get('messages', [])
        user_message = get_last_user_message(message_list)

    prompt = user_message'''
assert part.count(old)==1;p.write_text(s[:a]+part.replace(old,new)+s[b:]);py_compile.compile(str(p),doraise=True)
