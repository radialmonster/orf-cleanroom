"""Synthetic-only conditional ordering reducer checks."""
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from unittest import mock
from pathlib import Path
spec = importlib.util.spec_from_file_location('reducer', Path(__file__).with_name('suffix_conditional_order.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def case(low, high, returned=None):
    table = [low + high] + [[0] * 8 for _ in range(3)]
    n = sum(low) + sum(high)
    return {'joint_h_rows_l_columns': table, 'retained_tokens': n,
            'requested_tokens': n, 'returned_tokens': n if returned is None else returned,
            'start_token': 0, 'escape_tokens': 0}

a = module.reduce_window(case([9, 8, 7, 6], [1, 2, 3, 4]))
assert a['fractions'] == ['1/10', '1/5', '3/10', '2/5']
assert a['adjacent'] == ['<', '<', '<'] and a['strictly_increasing'] and a['nondecreasing']
a = module.reduce_window(case([9, 8, 8, 6], [1, 2, 2, 4]))
assert a['adjacent'] == ['<', '=', '<'] and not a['strictly_increasing'] and a['nondecreasing']
a = module.reduce_window(case([9, 6, 8, 6], [1, 4, 2, 4]))
assert a['adjacent'] == ['<', '>', '<'] and not a['nondecreasing']
a = module.reduce_window(case([9, 0, 8, 6], [1, 0, 2, 4]))
assert a['fractions'][1] is None and a['adjacent'][:2] == [None, None] and a['strictly_increasing'] is None
a = module.reduce_window(case([9, 8, 7, 6], [1, 2, 3, 4], returned=39))
assert a['counts'] is None and a['strictly_increasing'] is None
a = module.reduce_window(case([0] * 4, [0] * 4))
assert a['counts'] is None and a['adjacent'] is None
w = case([9, 8, 7, 6], [1, 2, 3, 4])
expected = module.reduce_window(w)
w['joint_h_rows_l_columns'] = [[0] * 8, [3, 2, 2, 2, 0, 1, 1, 1], [3, 3, 2, 2, 0, 0, 1, 1], [3, 3, 3, 2, 1, 1, 1, 2]]
assert module.reduce_window(w) == expected
w['joint_h_rows_l_columns'].reverse()
assert module.reduce_window(w) == expected
big = 2 ** 54
a = module.reduce_window(case([big, big, big, big], [big, big + 1, big + 1, big + 2]))
assert a['adjacent'] == ['<', '=', '<'] and a['nondecreasing'] and not a['strictly_increasing']
fixture = {'mode': 'discovery', 'sample': {'pixls_id': '123', 'pixls_name': 'sample.orf',
           'sha256': 'a' * 64, 'windows': [case([9, 8, 7, 6], [1, 2, 3, 4])]}}
raw = json.dumps(fixture).encode('utf-8')
real_open = open
def mock_open(path, *args, **kwargs):
    return io.BytesIO(raw) if path == 'synthetic-report' else real_open(path, *args, **kwargs)
out = io.StringIO()
with mock.patch.object(sys, 'argv', ['reducer', 'synthetic-report']), \
     mock.patch('builtins.open', side_effect=mock_open), contextlib.redirect_stdout(out):
    module.main()
report = json.loads(out.getvalue())
assert (report['mode'], report['pixls_id'], report['pixls_name'], report['sample_sha256']) == ('discovery', '123', 'sample.orf', 'a' * 64)
assert report['input_report_sha256'] == hashlib.sha256(raw).hexdigest()
assert report['tool_sha256'] == hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
assert {k: report['windows'][0][k] for k in ('start_token', 'requested_tokens', 'returned_tokens', 'retained_tokens', 'escape_tokens')} == {'start_token': 0, 'requested_tokens': 40, 'returned_tokens': 40, 'retained_tokens': 40, 'escape_tokens': 0}
print('synthetic conditional ordering checks passed')
