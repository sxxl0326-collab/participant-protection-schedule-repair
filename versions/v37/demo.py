"""Fresh CP-SAT repair/protection query on a supplied synthetic event."""
from pathlib import Path
import argparse, json, sys, time

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME / 'src'))
from engine import Repair
from independent_checker import check

def main(args):
    item = json.loads(Path(args.input).read_text(encoding='utf-8'))
    repair = Repair(item, seconds=args.seconds, seed=41)
    began = time.perf_counter()
    setup = repair.setup()
    result = {'model':item['id'], 'solver_seed':41, 'workers':1, 'setup':setup}
    if setup['status'] == 'OPTIMAL':
        # Command-line labels are one-based W1,W2,...; saved indices are zero-based.
        group = [int(label.upper().removeprefix('W'))-1 for label in args.protect]
        assert all(0 <= worker < item['d']['workers'] for worker in group)
        calls = []
        for dc, dg in [(0,0),(0,1),(1,0),(1,1)]:
            query = repair.query_protect(group, c=repair.cstar+dc, g=repair.gstar+dg)
            witness = query.get('witness')
            if witness:
                check(item, item['outage']['start'], [item['outage']], witness,
                      witness['c'], witness['g'], group)
            calls.append({'delta_C':dc, 'delta_G':dg, 'result':query})
            if witness:
                break
        result.update(request_labels=args.protect, menu_queries=calls)
        if args.map:
            result['protection_map'] = repair.protection_map()
    result['recorded_seconds'] = time.perf_counter()-began
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'setup':setup['status'], 'C':repair.cstar, 'G':repair.gstar,
        'request':args.protect, 'responses':[q['result']['status'] for q in result.get('menu_queries',[])],
        'output':str(args.output)}))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(HOME / 'data/example_set4_1335.json'))
    parser.add_argument('--protect', nargs='+', default=['W8'])
    parser.add_argument('--seconds', type=float, default=4,
                        help='Time limit per solver call, including model construction')
    parser.add_argument('--map', action='store_true')
    parser.add_argument('--output', default='demo_output.json')
    main(parser.parse_args())
