import gc,types,pathlib,time
rows=[]
for obj in gc.get_objects():
 if isinstance(obj,types.FunctionType) and obj.__name__=='tick' and obj.__code__.co_filename.endswith('test_clients.py'):
  env=obj.__globals__;rows.append({'stage':env['state'],'focus':env.get('focus_targets'),'last_steps':len(env['steps']),'checks':env['report']['checks'],'time':time.monotonic()})
RESULT=rows
