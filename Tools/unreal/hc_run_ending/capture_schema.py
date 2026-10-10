import rpc,json
r=rpc.rpc('tools/call',{'name':'describe_toolset','arguments':{'toolset_name':'EditorToolset.EditorAppToolset'}})
d=json.loads(r['result']['content'][0]['text'])
print(json.dumps(next(t['inputSchema'] for t in d['tools'] if t['name'].endswith('.CaptureViewport')),indent=2))
