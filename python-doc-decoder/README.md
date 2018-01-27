# Python documentation decoding.

This is a very gross approach, but it is effective nonetheless, even if
it consumes a metric fuck-tonne of resources.

## How was `python-index.json` obtained?

This utilises the `python-index.json` file which holds data outlining
the index for every valid search term on the Python website. This is
a file that is roughly 350,000 lines long when unminified.

This file is obtained by taking the HTML documentation archive that
the Python website provides from here: https://docs.python.org/3.6/download.html

In that archive is a Javascript file called `searchindex.js`. This is a 
single command that loads the entire index for search results in the
Python documentation into memory. This is then searched using an algorithm
on the client-side to get any results for the search. An online version
is found here for reference: https://docs.python.org/3.6/searchindex.js

What I did was install `nodejs` from my package manager, and replace the
start of the file reading `Search.setIndex(` with `JSON.stringify(`) and
then by wrapping that entire statement in `console.log(...);`

I could then output a JSON representation of this index by running 
`nodejs searchindex.js > searchindex.json`.


## I don't want to read 350,000 lines. What is in this file?

This analysis was performed first by parsing the JSON file in Python.

```python
#!/usr/bin/env python3.6

import json

with open('nekocogs/docs/python-index.json') as fp:
    index = json.load(fp)
```

I ran the following code to get the first level names in the root object
of the JSON file.

```python
print(index.keys())
```

This output the following:

```python
dict_keys(['docnames', 'envversion', 'filenames', 'objects', 'objnames',
 'objtypes', 'terms', 'titles', 'titleterms'])
```

The original function that was being passed this large blob of data was called
`Search.setIndex`. After a bit of rooting around in the source code, I found
this is an object called `Search` that is held in `_static/searchtools.js`.

The block-comment at the top of the page explained that an un-min-ified version
of the code was in `_stemmer.js` in the same directory. This was as obfuscated 
as hell and I was not going to try and read it.

### `docnames`

```python
[
    'about', 'bugs', 'c-api/abstract', 'c-api/allocation', 
    'c-api/apiabiversion', 'c-api/arg', 'c-api/bool', 
    'c-api/buffer', 'c-api/bytearray', 'c-api/bytes', 
    'c-api/capsule', 'c-api/cell', 'c-api/code', 
    'c-api/codec', 'c-api/complex', 'c-api/concrete', 
    'c-api/conversion', 'c-api/coro', 'c-api/datetime', 
    'c-api/descriptor', ...
]
```
This clearly maps document names.

### `envversion`

```python
53
```

No idea.

### `filenames`

```python
[
    'about.rst', 'bugs.rst', 'c-api/abstract.rst', 'c-api/allocation.rst', 
    'c-api/apiabiversion.rst', 'c-api/arg.rst', 'c-api/bool.rst', 
    'c-api/buffer.rst', 'c-api/bytearray.rst', 'c-api/bytes.rst', 
    'c-api/capsule.rst', 'c-api/cell.rst', 'c-api/code.rst', 'c-api/codec.rst', 
    'c-api/complex.rst', 'c-api/concrete.rst', 'c-api/conversion.rst', 
    'c-api/coro.rst', 'c-api/datetime.rst', 'c-api/descriptor.rst', ...
]
```
These are the ReStructured Text fragments that were used with Sphinx to generate
the HTML version of the documentation.


### `objects`, `objnames` and `objtypes`

```python
# Keys for `objects`.
[
    '', '_thread.lock', 'abc.ABCMeta', 'aifc.aifc', 'argparse.ArgumentParser', 
    'array.array', 'ast.AST', 'ast.NodeVisitor', 'asynchat.async_chat', 
    'asyncio.AbstractEventLoop', 'asyncio.AbstractEventLoopPolicy', 
    'asyncio.BaseEventLoop', 'asyncio.BaseProtocol', 
    'asyncio.BaseSubprocessTransport', 'asyncio.BaseTransport', 
    'asyncio.Condition', 'asyncio.DatagramProtocol', 
    'asyncio.DatagramTransport', 'asyncio.Event', 'asyncio.Future', 
    'asyncio.Handle', 'asyncio.IncompleteReadError', 
    'asyncio.LimitOverrunError', 'asyncio.Lock', 'asyncio.Protocol', 
    'asyncio.Queue', 'asyncio.ReadTransport', 'asyncio.Semaphore', 
    'asyncio.Server', 'asyncio.StreamReader', 'asyncio.StreamWriter', 
    'asyncio.SubprocessProtocol', 'asyncio.Task', 'asyncio.WriteTransport', 
    'asyncio.asyncio.subprocess', 'asyncio.asyncio.subprocess.Process', 
    'asyncore.dispatcher', 'bdb.Bdb', 'bdb.Breakpoint', 'bz2.BZ2Compressor', 
    'bz2.BZ2Decompressor', 'bz2.BZ2File', 'calendar.Calendar', 
    'calendar.HTMLCalendar', 'calendar.TextCalend...'
]
```
The keys in `objects` seem to relate to specific namespaces. These are mapped to
terms that are contained in the documentation for that namespace and
have some sort of significance.
```python
{
    '': {
        '!': [291, 14, 1, '-'], 
        '--help': [443, 15, 1, 'cmdoption-help'], 
        '--sort-keys': [253, 15, 1, 'cmdoption-sort-keys'], 
        '--version': [443, 15, 1, 'cmdoption-version'], 
        '-?': [443, 15, 1, 'cmdoption'], 
        '-B': [443, 15, 1, 'id1'], 
        '-E': [443, 15, 1, 'cmdoption-e'], 
        '-I': [443, 15, 1, 'id2'], 
        '-J': [443, 15, 1, 'cmdoption-j'], 
        '-O': [443, 15, 1, 'cmdoption-o'], 
        '-OO': [443, 15, 1, 'cmdoption-oo'], 
        '-R': [443, 15, 1, 'cmdoption-r'], 
        '-S': [443, 15, 1, 'id3'], 
        '-V': [443, 15, 1, 'cmdoption-v'], 
        '-W': [443, 15, 1, 'cmdoption-w'], 
        '-X': [443, 15, 1, 'id5'], 
        '-b': [443, 15, 1, 'cmdoption-b'], 
        '-c': [443, 15, 1, 'cmdoption-c'], 
        '-d': [443, 15, 1, 'cmdoption-d'], 
        '-h': [443, 15, 1, 'cmdoption-h'], 
        '-i': [443, 15, 1, 'cmdoption-i'], 
        '-m': [443, 15, 1, 'cmdoption-m'], 
        '-q': [443, 15, 1, 'cmdoption-q'], 
        '-s': [443, 15, 1, 'cmdoption-s'], 
        '-u': [443, 15, 1, 'cmdoption-u'], 
        '-v': [443, 15, 1, 'id4'], 
        '-x': [443, 15, 1, 'cmdoption-x'], 
        'break': [291, 14, 1, '-'], 
        'continue': [291, 14, 1, '-'],
        ...
```
These are mapped to groups of numeric identifiers which are defined in `objtypes`
and have aliases defined in `objnames`. `Objtypes` defines types of term,
whereas `objnames` defines actual terms.

So, I am guessing `objects` maps to groups of keywords. Each keyword is given
a combination of zero or more `objname`s. Each `objname` can have one or more
`objtype`s.

`Objtypes` starts like so:

```python
{
    '0': 'c:var',
    '1': 'c:type', 
    '2': 'c:function', 
    '3': 'c:member', 
    '4': 'c:macro', 
    '5': 'py:exception', 
    '6': 'py:attribute', 
    '7': 'py:method', 
    '8': 'py:data', 
    '9': 'py:module', 
    '10': 'py:function', 
    '11': 'py:class', 
    '12': 'py:classmethod', 
    '13': 'py:staticmethod', '14': 'std:pdbcommand', 
    '15': 'std:cmdoption', 
    '16': 'std:opcode', 
    '17': 'std:envvar', '18': 'std:2to3fixer'}, ...
```

Likewise, `objnames` is defined like so:

```python
{
    '0': ['c', 'var', 'C variable'],
    '1': ['c', 'type', 'C type'], 
    '2': ['c', 'function', 'C function'], 
    '3': ['c', 'member', 'C member'], 
    '4': ['c', 'macro', 'C macro'], 
    '5': ['py', 'exception', 'Python exception'], 
    '6': ['py', 'attribute', 'Python attribute'], 
    '7': ['py', 'method', 'Python method'], 
    '8': ['py', 'data', 'Python data'], 
    '9': ['py', 'module', 'Python module'], 
    '10': ['py', 'function', 'Python function'], 
    '11': ['py', 'class', 'Python class'], 
    '12': ['py', 'classmethod', 'Python class method'], 
    '13': ['py', 'staticmethod', 'Python static method'], ...
```

### `terms`

Not sure what this does. It seems to map a bunch of arbitrary terms to empty
lists. 

### `titles`

These are specific titles used in the documentation, stored in a list.

### `titleterms`

See `terms`, except this appears to work on titles only.

## Going forward

There is a lot of clutter in this file that will slow it down at runtime.

I need to write some sort of algorithm to reformat some of this data into a
clearer manner. 