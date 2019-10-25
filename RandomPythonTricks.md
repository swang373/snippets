I found a notepad where I had collected what appeared to be a random assorted of Python "tricks". I didn't have a source documented, but I'm sure these things are floating around the internet. If I encountered your trick by browsing your blog post or Stack Overflow answer, thanks!

#### Debugging

```python
import pdb; pdb.set_trace()
python -i foo.py; import pdb; pdb.pm()
```

#### Profiling

```python
python -m cProfile my_script.py
```

#### Safer Evals

```python
expr = '[1, 2, 3]'

# Don't do
my_list = eval(expr)

# Rather do
import ast
my_list = ast.literal_eval(expr)
```

#### Sorting custom objects

```python
users.sort(attrgetter("username"))
```

#### Boolean Values as dict Keys

```python
a = {True: 0, False: 1}
```

#### List Tricks

```python

# Reversing a list
mylist[::-1]

# The built-in reversed is faster and returns an iterator
# because the above is a shallow copy of mylist

# Resetting a list
l[:] = [1, 2, 3]

# Copying a list
y = x[:]
```

#### Pro-tip: the built-in enumerate takes a starting index parameter!

#### Cute Fizz Buzz

```python
['Fizz'*(not i%3) + 'Buzz'*(not i%5) or i for i in range(1, 100)]
```

#### Cute Factorial

```python
from operator import mul

factorial = lambda x: reduce(mul, xrange(2, x+1), 1)
```

#### Pro-tip: verbose regex can be broken over multiple lines or use string concatentation.

#### Other useful things

- Descriptors
- Metaclasses
- namedtuples
