"""PIE check for the rebaked maze (Play As Client on L_Maze): players stand on the new geometry, and every
station from the scene file has collision under it on the server and on every client. Writes Saved/PR119/maze-pie.json."""
import gzip, json
import unreal as ue
CHARACTER = ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
scene = json.loads(gzip.decompress((ROOT / 'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes()))
worlds = list(ue.EditorLevelLibrary.get_pie_worlds(True))
server = next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
report = {'worlds': len(worlds), 'players': [], 'stations': {}, 'failures': []}
for p in ue.GameplayStatics.get_all_actors_of_class(server, CHARACTER):
    m = p.get_component_by_class(ue.CharacterMovementComponent)
    l = p.get_actor_location()
    hit = ue.SystemLibrary.line_trace_single(server, l, l - ue.Vector(0, 0, 400), ue.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p], ue.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    floor = t[9].get_actor_label() if t and t[0] and t[9] else None
    report['players'].append({'loc': [round(l.x), round(l.y), round(l.z)], 'on_ground': m.is_moving_on_ground(), 'floor': floor})
    if not m.is_moving_on_ground():
        report['failures'].append(('player not on ground', report['players'][-1]))
for st in scene['stations']:
    x, y, z = st['location']
    row = {}
    for w in worlds:
        hit = ue.SystemLibrary.line_trace_single(w, ue.Vector(x, y, z + 150), ue.Vector(x, y, z - 600), ue.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], ue.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        ok = bool(t and t[0])
        row['server' if w == server else 'client%d' % worlds.index(w)] = [round(t[4].z), t[9].get_actor_label() if t[9] else None] if ok else None
        if not ok:
            report['failures'].append(('no floor', st['name'], w.get_name()))
    report['stations'][st['name']] = row
(QUEUE / 'maze-pie.json').write_text(json.dumps(report, indent=2))
RESULT = {'failures': report['failures'], 'players': report['players'], 'stations_checked': len(report['stations']), 'worlds': len(worlds)}
