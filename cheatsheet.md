# JS → Python cheatsheet

A quick-reference for JS/frontend devs picking up Python for backend work.

## Variables & types

| JS | Python |
| --- | --- |
| `let x = 5;` | `x = 5` |
| `const x = 5;` | `x = 5` (Python has no real constants; `X = 5` + ALL_CAPS is the convention) |
| `null` / `undefined` | `None` |
| `true` / `false` | `True` / `False` |
| `typeof x` | `type(x)` |
| `x === null \|\| x === undefined` | `x is None` |
| `x ?? defaultVal` | `x if x is not None else defaultVal` |
| `x?.prop?.sub` | `getattr(x, 'prop', None)` or just try/except |

## Functions

| JS | Python |
| --- | --- |
| `function add(a, b) { return a + b; }` | `def add(a, b): return a + b` |
| `const add = (a, b) => a + b;` | `add = lambda a, b: a + b` |
| `function greet(name = "world") {}` | `def greet(name="world"):` |
| `function sum(...args) {}` | `def sum(*args):` |
| `function f({a, b}) {}` (destructure) | `def f(a, b):` (or `**kwargs` for object-style) |
| `f.apply(null, args)` | `f(*args)` |

## Collections

| JS | Python |
| --- | --- |
| `[1, 2, 3]` | `[1, 2, 3]` |
| `{a: 1, b: 2}` | `{'a': 1, 'b': 2}` |
| `new Set([1, 2])` | `{1, 2}` |
| `arr.push(x)` | `arr.append(x)` |
| `arr.pop()` | `arr.pop()` |
| `arr.shift()` | `arr.pop(0)` |
| `arr.unshift(x)` | `arr.insert(0, x)` |
| `arr.length` | `len(arr)` |
| `arr.includes(x)` | `x in arr` |
| `arr.slice(1, 3)` | `arr[1:3]` |
| `arr.slice(-2)` | `arr[-2:]` |
| `[...arr1, ...arr2]` | `[*arr1, *arr2]` or `arr1 + arr2` |
| `Object.keys(obj)` | `obj.keys()` |
| `Object.values(obj)` | `obj.values()` |
| `Object.entries(obj)` | `obj.items()` |
| `'key' in obj` | `'key' in obj` (same!) |
| `delete obj.key` | `del obj['key']` |
| `Array.from({length: 5}, (_, i) => i)` | `list(range(5))` |

## Comprehensions & functional patterns

| JS | Python |
| --- | --- |
| `items.map(x => x * 2)` | `[x * 2 for x in items]` |
| `items.filter(x => x > 0)` | `[x for x in items if x > 0]` |
| `items.map(x => x*2).filter(x => x>0)` | `[x*2 for x in items if x*2 > 0]` |
| `items.some(x => cond)` | `any(cond for x in items)` |
| `items.every(x => cond)` | `all(cond for x in items)` |
| `items.reduce((a, x) => a + x, 0)` | `sum(items)` (or `functools.reduce`) |
| `items.find(x => cond)` | `next((x for x in items if cond), None)` |
| `Object.fromEntries(pairs)` | `dict(pairs)` or `{k: v for k, v in pairs}` |
| `items.forEach((x, i) => {})` | `for i, x in enumerate(items):` |
| `items.sort((a, b) => a - b)` | `items.sort()` / `sorted(items)` |
| `items.sort((a,b) => a.age - b.age)` | `items.sort(key=lambda x: x.age)` |

## Control flow

| JS | Python |
| --- | --- |
| `if (cond) {} else {}` | `if cond: ... else: ...` |
| `cond ? a : b` | `a if cond else b` |
| `for (let i=0; i<n; i++) {}` | `for i in range(n):` |
| `for (const x of arr) {}` | `for x in arr:` |
| `for (const k in obj) {}` | `for k in obj:` (iterates keys, same as JS) |
| `while (cond) {}` | `while cond:` |
| `switch (x) { case 1: ... }` | `match x: case 1: ...` (3.10+), or if/elif chain |
| `try {} catch (e) {} finally {}` | `try: ... except Exception as e: ... finally:` |
| `throw new Error("msg")` | `raise Exception("msg")` |

## Strings

| JS | Python |
| --- | --- |
| `` `Hello, ${name}!` `` | `f"Hello, {name}!"` |
| `str.split(',')` | `str.split(',')` |
| `str.trim()` | `str.strip()` |
| `str.toLowerCase()` | `str.lower()` |
| `str.includes(sub)` | `sub in str` |
| `str.padStart(5, '0')` | `str.rjust(5, '0')` or `str.zfill(5)` |
| `arr.join(', ')` | `', '.join(arr)` |
| `str.replace(a, b)` | `str.replace(a, b)` |

## Classes

| JS | Python |
| --- | --- |
| `class Foo { constructor(x) { this.x = x; } }` | `class Foo:\n def __init__(self, x):\n self.x = x` |
| `this.x` | `self.x` (explicit `self` param on every method) |
| `class Bar extends Foo {}` | `class Bar(Foo):` |
| `super(x)` | `super().__init__(x)` |
| `static method() {}` | `@staticmethod` decorator |
| `get prop() {}` | `@property` decorator |
| `#privateField` | `_privateField` (convention only — not enforced) |

## Async

| JS | Python |
| --- | --- |
| `async function f() {}` | `async def f():` |
| `await promise` | `await coroutine` |
| `Promise.all([p1, p2])` | `await asyncio.gather(c1, c2)` |
| `new Promise((resolve) => {})` | `asyncio.Future()` (rarely needed directly) |
| `setTimeout(fn, 1000)` | `await asyncio.sleep(1)` then call `fn()` |
| top-level `await` (modules) | needs an event loop — `asyncio.run(main())` |

## Modules & packages

| JS | Python |
| --- | --- |
| `import { x } from './mod'` | `from mod import x` |
| `import * as mod from './mod'` | `import mod` |
| `export default function() {}` | no direct equivalent — just define/import by name |
| `module.exports = {...}` | everything at module scope is importable |
| `npm install pkg` | `pip install pkg` |
| `package.json` | `requirements.txt` or `pyproject.toml` |
| `node_modules/` | virtual env (`venv/`, `.venv/`) |
| `npm run script` | often a `Makefile` or `poetry run` |

## Resource handling & misc

| JS | Python |
| --- | --- |
| `try { ... } finally { close() }` | `with open(...) as f:` (context manager auto-closes) |
| `JSON.stringify(obj)` | `json.dumps(obj)` |
| `JSON.parse(str)` | `json.loads(str)` |
| `console.log(x)` | `print(x)` |
| `undefined` (missing key) | `KeyError` raised, or `dict.get(k, default)` |
| `NaN` | `float('nan')` (rare in practice) |
| `Array.isArray(x)` | `isinstance(x, list)` |
| `x instanceof Foo` | `isinstance(x, Foo)` |
| `===` (strict equality) | `==` (Python has no loose/strict distinction) |
| `Object.freeze(obj)` | no true equivalent — use `namedtuple`, `dataclass(frozen=True)`, or a tuple |

## Gotchas worth knowing up front

- **Indentation is syntax.** No braces — a wrong indent level is a runtime bug, not a style nit.
- **No hoisting.** A function or variable must be defined before it's used in the code's execution order.
- **`self` is explicit everywhere** in instance methods — Python won't infer it like JS's `this`.
- **Mutable default args are a trap**: `def f(items=[]):` reuses the *same* list across every call with no argument. Use `def f(items=None): items = items or []`.
- **Integer division**: `5 / 2` is `2.5` (float division). Use `5 // 2` for the JS-style `Math.floor(5/2)`.
- **`is` vs `==`**: `is` checks identity (same object in memory), `==` checks value equality — `is` is only for `None`/`True`/`False` checks, not general comparisons.