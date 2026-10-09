from pathlib import Path
import py_compile
p=Path(__import__('os').environ['OPENWEBUI_PACKAGE_DIR']) / 'utils/middleware.py';s=p.read_text();old="    extra_params['__features__'] = features\n    if features:"
new="""    extra_params['__features__'] = features
    # The explicit Image control is an execution request, not an optional
    # native tool suggestion. Route it through the configured image engine
    # even when the selected text model cannot emit native tool calls.
    if features.get('image_generation'):
        metadata.setdefault('params', {})['function_calling'] = 'legacy'
    if features:"""
assert s.count(old)==1;p.write_text(s.replace(old,new));py_compile.compile(str(p),doraise=True)
