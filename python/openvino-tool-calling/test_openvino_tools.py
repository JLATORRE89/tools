import unittest,json
from openvino_tool_protocol import parse_tool_calls, tool_generation_options
T=[{'type':'function','function':{'name':'render','parameters':{'type':'object','properties':{'prompt':{'type':'string'},'steps':{'type':'integer'}},'required':['prompt']}}}]
class ProtocolTests(unittest.TestCase):
 def test_tool_stop_keeps_closing_delimiter(self):
  self.assertEqual(tool_generation_options(T,'auto'),{'stop_strings':{'</tool_call>'},'include_stop_str_in_output':True})
  self.assertEqual(tool_generation_options(T,'none'),{})
  self.assertEqual(tool_generation_options([],'auto'),{})
 def test_xml_typed_args(self):
  m,f=parse_tool_calls('<tool_call><function=render><parameter=prompt>123</parameter><parameter=steps>20</parameter></function></tool_call>',T)
  self.assertEqual(f,'tool_calls');self.assertEqual(json.loads(m['tool_calls'][0]['function']['arguments']),{'prompt':'123','steps':20})
 def test_json(self):self.assertEqual(parse_tool_calls('<tool_call>{"name":"render","arguments":{"prompt":"house"}}</tool_call>',T)[1],'tool_calls')
 def test_plain_text(self):self.assertEqual(parse_tool_calls('Hello',T)[1],'stop')
 def test_bad_calls(self):
  for s in ['<tool_call>','<tool_call>{"name":"other","arguments":{}}</tool_call>','<tool_call>{"name":"render","arguments":{}}</tool_call>']:
   with self.subTest(s=s),self.assertRaises(ValueError):parse_tool_calls(s,T)
if __name__=='__main__':unittest.main()
