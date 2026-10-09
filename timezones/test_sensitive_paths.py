import unittest
from sensitive_paths import is_sensitive_public_path
class SensitivePathTests(unittest.TestCase):
 def test_sensitive_routes(self):
  for p in ['/.env','/config/production.env','/keys/id_rsa','/keys/id_ed25519','/app/.env.production','/assets/.git/config','/nested/LOGS/traffic.log','/%252eenv','/assets%5c.env','/backup/config','/x/key.pem','/db.sqlite3','/x/file.bak','/x/../.env']:
   with self.subTest(p=p):self.assertTrue(is_sensitive_public_path(p))
 def test_normal_routes(self):
  for p in ['/timezone/health','/timezone/about','/docs','/openapi.json','/timezone/location']:
   with self.subTest(p=p):self.assertFalse(is_sensitive_public_path(p))
class MiddlewareResponseTests(unittest.TestCase):
 def test_denial_is404_not500(self):
  import ast
  from pathlib import Path
  from fastapi import FastAPI, Request
  from fastapi.responses import JSONResponse
  from fastapi.testclient import TestClient
  app=FastAPI()
  tree=ast.parse(Path(__file__).with_name('main.py').read_text())
  node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='block_sensitive_public_paths')
  env=dict(app=app,Request=Request,JSONResponse=JSONResponse,is_sensitive_public_path=is_sensitive_public_path)
  exec(compile(ast.Module(body=[node],type_ignores=[]),'middleware-test','exec'),env)
  @app.get('/{path:path}')
  async def fallback(path):return {'ok':True}
  with TestClient(app) as client:
   self.assertEqual(client.get('/assets/.env').status_code,404)
   self.assertEqual(client.get('/%252eenv').status_code,404)
   self.assertEqual(client.get('/timezone/health').status_code,200)

if __name__=='__main__':unittest.main()
