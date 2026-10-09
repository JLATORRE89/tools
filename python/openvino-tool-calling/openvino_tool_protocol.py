"""Translate Qwen tool-call output to OpenAI chat-completion messages."""
import json
import re
import uuid


def tool_generation_options(tools, tool_choice):
    """Stop after a complete tool call instead of generating an ungrounded answer."""
    if tools and tool_choice != 'none':
        return {'stop_strings': {'</tool_call>'}, 'include_stop_str_in_output': True}
    return {}


def parse_tool_calls(text, tools):
    allowed = {t['function']['name']: t['function'].get('parameters', {}) for t in tools}
    calls = []
    blocks = list(re.finditer(r'<tool_call>\s*(.*?)\s*</tool_call>', text, re.S))
    if '<tool_call>' in text and not blocks:
        raise ValueError('Incomplete model tool call')
    for block in blocks:
        raw = block.group(1)
        if raw.startswith('{'):
            value = json.loads(raw); name = value['name']; args = value.get('arguments', {})
            if isinstance(args, str): args = json.loads(args)
        else:
            match = re.fullmatch(r'<function=([^>]+)>\s*(.*?)\s*</function>', raw, re.S)
            if not match: raise ValueError('Malformed model tool call')
            name, body = match.groups(); args = {}
            properties = allowed.get(name, {}).get('properties', {})
            matches = list(re.finditer(r'<parameter=([^>]+)>\s*(.*?)\s*</parameter>', body, re.S))
            if re.sub(r'<parameter=([^>]+)>\s*(.*?)\s*</parameter>', '', body, flags=re.S).strip():
                raise ValueError('Malformed model tool parameters')
            for param in matches:
                key, value = param.groups()
                if key in args: raise ValueError('Duplicate tool argument')
                if properties.get(key, {}).get('type') != 'string':
                    try: value = json.loads(value)
                    except json.JSONDecodeError: pass
                args[key] = value
        if name not in allowed or not isinstance(args, dict):
            raise ValueError('Unknown tool or invalid arguments')
        if not set(allowed[name].get('required', [])).issubset(args):
            raise ValueError('Missing required tool arguments')
        calls.append({'id': 'call_' + uuid.uuid4().hex[:24], 'type': 'function',
                      'function': {'name': name, 'arguments': json.dumps(args)}})
    if not calls:return {'role': 'assistant', 'content': text}, 'stop'
    content = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.S).strip()
    return {'role': 'assistant', 'content': content or None, 'tool_calls': calls}, 'tool_calls'


def history_messages(messages):
    result = []
    for message in messages:
        value = message.model_dump(exclude_none=True)
        value['content'] = value.get('content') or ''
        if value['role'] == 'developer': value['role'] = 'system'
        for call in value.get('tool_calls', []):
            function = call['function']
            if isinstance(function.get('arguments'), str):
                function['arguments'] = json.loads(function['arguments'])
        result.append(value)
    return result
