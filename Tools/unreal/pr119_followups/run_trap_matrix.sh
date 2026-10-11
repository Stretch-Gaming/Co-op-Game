#!/bin/bash
# Run test_cave_traps.py on L_Site01 at each player count given, as Play As Client.
cd "$(dirname "$0")"
Q=../../../Saved/PR119
for n in "$@"; do
  python3 request.py pie_stop.py '{"_during_pie":true}' >/dev/null
  for i in 1 2 3 4 5 6; do sleep 3; [ "$(python3 request.py pie_worlds.py '{"_during_pie":true}' | python3 -c "import json,sys; print(json.load(sys.stdin)['result'])")" = "[]" ] && break; done
  LOG="$HOME/Library/Logs/Unreal Engine/CoopGameEditor/CoopGame_2.log"; MARK=$(wc -l < "$LOG" | tr -d " ")
  python3 request.py pie_start.py "{\"map\":\"/Game/Maps/L_Site01\",\"clients\":$n}" >/dev/null
  # Wait until every client has joined; a 4-client PIE launch on one Mac can stall for over a minute.
  for i in $(seq 1 120); do [ "$(tail -n +$MARK "$LOG" | grep -c 'Join succeeded')" -ge "$n" ] && break; sleep 2; done; sleep 4
  rm -f $Q/cave-traps.json; python3 request.py test_cave_traps.py '{"_during_pie":true,"join_wait":60}' >/dev/null
  for i in $(seq 1 90); do [ -f $Q/cave-traps.json ] && break; sleep 2; done
  cp $Q/cave-traps.json $Q/cave-traps-$n.json
  python3 -c "import json; r=json.load(open('$Q/cave-traps-$n.json')); print('$n players:', r['passed'], r['error'] or ''); print(*r['checks'], sep='\n'); print('health after', r['data'].get('server_health_after'))"
done
python3 request.py pie_stop.py '{"_during_pie":true}' >/dev/null
