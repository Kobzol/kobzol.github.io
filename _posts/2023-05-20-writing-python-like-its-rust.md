---
layout: "post"
title: "Writing Python like it's Rust"
date: "2023-05-20 16:42:00 +0200"
categories: rust python
---

I started programming in Rust several years ago, and it has gradually changed the way I design
programs in other programming languages, most notably in Python. Before I started using Rust, I was
usually writing Python code in a very dynamic and type-loose way, without type hints, passing and
returning dictionaries everywhere, and occasionally falling back
to ["stringly-typed"](https://wiki.c2.com/?StringlyTyped) interfaces. However, after
experiencing the strictness of the Rust type system, and noticing all the problems that it
prevents "by construction", I suddenly became quite anxious whenever I got back to Python and
wasn't provided with the same guarantees.

To be clear, by "guarantees" I don't mean memory safety here (Python is reasonably memory safe
as-is), but rather "soundness" -- the concept of designing APIs that are very hard or outright impossible
to misuse and thus prevent undefined behaviour and various bugs. In Rust, an incorrectly used
interface will usually cause a compilation error. In Python, you can still execute such incorrect
program, but if you use a type checker (like [`pyright`](https://github.com/microsoft/pyright)) or
an IDE with a type analyzer (like PyCharm), you can still get a similar level of quick feedback about a
possible problem.

Eventually, I started adopting some concepts from Rust in my Python programs.
It basically boils down to two things - using type hints as much as possible, and upholding
the good ol'
[making illegal states unrepresentable](https://ybogomolov.me/making-illegal-states-unrepresentable)
principle. I try to do this both for programs that will be maintained for a while, but also for oneshot
utility scripts. Mostly because in my experience, the latter quite often turn into the former :) In
my experience, this approach leads to programs that are easier to understand and change.

In this post I'll show a few examples of such patterns applied to Python
programs. It's no rocket science, but I still felt like it might be useful to document them.

> Note: this post contains a lot of opinions about writing Python code. I don't want to add
> "IMHO" to every sentence, so take everything in this post as simply my opinions on the matter,
> rather than attempts to promote some universal truths :) Also, I'm not claiming that the
> presented ideas were all invented in Rust, they are also used in other languages, of course.

# Type hints
The first and foremost thing is using type hints where possible, particularly in function
signatures and class attributes. When I read a function signature looking like this:

```python
def find_item(records, check):
```

I have no idea what is going on from the signature itself. Is `records` a list, a dict or a
database connection? Is `check` a boolean, or a function? What does this
function return? What happens if it fails, does it raise an exception, or return `None`? To find
answers to these questions, I either have to go read the function body (and often recursively
the bodies of other functions it calls -- this is quite annoying), or read its documentation (if there is any).
While the documentation might contain useful information about what the function does, it shouldn't be
necessary to also use it for documenting answers to the previous questions. A lot of them can be
answered by a built-in mechanism -- type hints.

```python
def find_item(
  records: List[Item],
  check: Callable[[Item], bool]
) -> Optional[Item]:
```

Did it take me more time to write the signature? Yes. Is that a problem? No, unless my coding
is bottlenecked by the number of characters I write per minute, and that doesn't really happen.
Writing out the types explicitly *forces me to think* about what will be the actual interface provided
by the function, and how can I make it as strict as possible, to make it hard for its callers to
use it in a wrong way. With the signature above, I can get a pretty good idea how can I use the
function, what to pass it as arguments, and what can I expect to be returned from it. Furthermore,
unlike a doc comment, which can get easily out of date when the code changes, when I change the types
and don't update the callers of the function, the typechecker will yell at me[^1]. And if I'm interested
in what is `Item`, I can just use `Go to definition` and immediately see how does that type look like. 

[^1]: To be fair, this might also be true for descriptions of parameter types in doc comments if you use
    some structured format (like reStructuredText). In that case the typechecker might be able to use that and warn
    you if the types do not match. But if you use a typechecker anyway, it seems better to me to
    leverage the "native" mechanism for specifying types -- type hints.

Now, I'm not a ~~sith~~ absolutist in this regard, and if it takes five nested type hints to
describe a single parameter, I will usually just give up and give it a simpler, albeit imprecise
type. In my experience, this situation does not happen that often. And if it does happen, it can
actually signal a problem with the code -- if your function parameter can be a number, a tuple of
strings or a dictionary mapping strings to integers, it can be a sign that you might want to
refactor and simplify it.

# Dataclasses instead of tuples or dictionaries
Using type hints is one thing, but that merely describes what is the interface of your functions.
The second step is actually making these interfaces as exact and "locked down" as possible. A typical
example is returning multiple values (or a single complex value) from a function. The lazy and
quick approach is to return a tuple:

```python
def find_person(...) -> Tuple[str, str, int]:
```

Great, we know that we're returning three values. What are they? Is the first string the first name
of the person? The second string the surname? What's the number? Is it age? Position in some list?
Social security number? This kind of typing is opaque and unless you look into the function body,
you don't know what happens here.

The next step to "improve" this could be to return a dictionary:

```python
def find_person(...) -> Dict[str, Any]:
    ...
    return {
        "name": ...,
        "city": ...,
        "age": ...
    }
```

Now we actually have an idea what are the individual returned attributes, but we again have to
inspect the function body to find out. In a sense, the type got even worse, because now
we don't even know the count and the types of the individual attributes. Furthermore, when this
function changes and the keys in the returned dictionary are renamed or removed, there's no easy way to find
out with a typechecker, and thus its callers usually have to be changed with a very manual and
annoying *run-crash-modify code* cycle.

The proper solution is to return a strongly typed object with named parameters that have an
attached type. In Python, this means we have to create a class. I suspect that tuples and dicts
are used so often in these situations because it's just so much easier than to define a class (and think of
a name for it), create a constructor with parameters, store the parameters into fields etc.
Since Python 3.7 (and sooner with a package polyfill), there is a much faster solution - `dataclasses`.

```python
@dataclasses.dataclass
class City:
    name: str
    zip_code: int


@dataclasses.dataclass
class Person:
    name: str
    city: City
    age: int


def find_person(...) -> Person:
```

You still have to think of a [name](https://twitter.com/secretGeek/status/7269997868) for the created class,
but other than that, it's pretty much as concise as it can get, and you get type annotations for all attributes.

With this dataclass, I have an explicit description of what the function returns. When I call
this function and work with the returned value, IDE autocompletion will show me what are the
names and types of its attributes. This might sound trivial, but for me it is a large productivity benefit.
Furthermore, when the code is refactored, and the attributes change, my IDE and the
typechecker will yell at me and show me all locations that have to be changed, without me having
to execute the program at all. For some simple refactorings (e.g. attribute rename), the IDE can even make
these changes for me. In addition, with explicitly named types, I can build a vocabulary of terms (`Person`, `City`)
that I can then share with other functions and classes.

# Algebraic data types
The one thing from Rust that I probably lack the most in most mainstream languages are algebraic data
types (ADTs)[^2]. It is an incredibly powerful tool to explicitly describe the shapes of data
my code is working with. For example, when I'm working with packets in Rust, I can explicitly
enumerate all the various kinds of packets that can be received, and assign different data (fields) to each
of them:

[^2]: a.k.a. discriminated/tagged unions, sum types, sealed classes, etc.

```rust
enum Packet {
  Header {
    protocol: Protocol,
    size: usize
  },
  Payload {
    data: Vec<u8>
  },
  Trailer {
    data: Vec<u8>,
    checksum: usize
  }
}
```

And with pattern matching, I can then react to the individual variants, and the compiler checks that I don't miss
any cases:

```rust
fn handle_packet(packet: Packet) {
  match packet {
    Packet::Header { protocol, size } => ...,
    Packet::Payload { data } |
    Packet::Trailer { data, ...} => println!("{data:?}")
  }
}
```

This is invaluable for making sure that invalid states are not representable and thus avoiding many runtime errors.
ADTs are especially useful in statically typed languages,
where if you want to work with a set of types in an unified manner, you need a shared "name" with which
you will refer to them. Without ADTs, this is typically done using OOP interfaces and/or inheritance.
Interfaces and virtual methods have their place when the set of used types is open-ended, however when the set
of types is closed, and you want to make sure that you handle all the possible variants, ADTs and pattern
matching is a much better fit.

In a dynamically typed language, such as Python, there's not really a need to have a shared name for a set of types,
mainly because you don't even have to name the types used in the program in the first place. However, it can still be
useful to use something akin to ADTs, by creating a union type:

```python
@dataclass
class Header:
  protocol: Protocol
  size: int

@dataclass
class Payload:
  data: str

@dataclass
class Trailer:
  data: str
  checksum: int

Packet = typing.Union[Header, Payload, Trailer]
# or `Packet = Header | Payload | Trailer` since Python 3.10
```

`Packet` here defines a new type, which can be either a header, a payload or a trailer packet. I can now use
this type (name) in the rest of my program when I want to make sure that only these three classes will be valid.
Note that there is no explicit "tag" attached to the classes, so when we want to distinguish them, we have to use
e.g. `instanceof` or pattern matching:

```python
def handle_is_instance(packet: Packet):
    if isinstance(packet, Header):
        print("header {packet.protocol} {packet.size}")
    elif isinstance(packet, Payload):
        print("payload {packet.data}")
    elif isinstance(packet, Trailer):
        print("trailer {packet.checksum} {packet.data}")
    else:
        assert False

def handle_pattern_matching(packet: Packet):
    match packet:
        case Header(protocol, size): print(f"header {protocol} {size}")
        case Payload(data): print("payload {data}")
        case Trailer(data, checksum): print(f"trailer {checksum} {data}")
        case _: assert False
```

Sadly, here we have to (or rather, should) include the annoying `assert False` branches so that the function crashes
when it receives unexpected data. In Rust, this would be a compile-time error instead.

> Note: Several people on Reddit have reminded me that `assert False` is actually optimized away completely
> in optimized build (`python -O ...`). Thus it would be safer to raise an exception directly.
> There is also [`typing.assert_never`](https://docs.python.org/3/library/typing.html#typing.assert_never)
> from Python 3.11, which explicitly tells a type checker that falling to this branch should be a "compile-time"
> error.

A nice property of the union type is that it is defined outside the class that is part of the union.
The class therefore does not know that it is being included in the union, which reduces coupling in code.
And you can even create multiple different unions using the same type:

```python
Packet = Header | Payload | Trailer
PacketWithData = Payload | Trailer
```

Union types are also quite useful for automatic (de)serialization. Recently I found an awesome serialization
library called [pyserde](https://github.com/yukinarit/pyserde), which is based on the venerable Rust
[serde](https://serde.rs/) serialization framework. Amongst many other cool features, it is able to
leverage typing annotations to serialize and deserialize union types without any additional code:

```python
import serde

...
Packet = Header | Payload | Trailer

@dataclass
class Data:
    packet: Packet

serialized = serde.to_dict(Data(packet=Trailer(data="foo", checksum=42)))
# {'packet': {'Trailer': {'data': 'foo', 'checksum': 42}}}

deserialized = serde.from_dict(Data, serialized)
# Data(packet=Trailer(data='foo', checksum=42))
```

You can even [choose](https://yukinarit.github.io/pyserde/guide/features/union.html) how will the union tag be
serialized, same as with `serde`. I was searching for similar functionality for a long time, because it's
quite useful to (de)serialize union types. However, it was quite annoying to implement it in most
other serialization libraries that I tried (e.g. `dataclasses_json` or `dacite`).

As an example, when working with machine learning models, I'm using unions to store various types
of neural networks (e.g. a classification or a segmentation CNN models) inside a single config file format.
I have also found it useful to version different formats of data (in my case configuration files), like this:

```python
Config = ConfigV1 | ConfigV2 | ConfigV3
```

By deserializing `Config`, I'm able to read all previous versions of the config format, and thus keep backwards
compatibility.

# Using newtypes
In Rust, it is quite common to define data types that do not add any new behavior, but serve
simply to specify the domain and intended usage of some other, otherwise quite general data type
-- for example integers. This pattern is called a "newtype" [^3] and it can be also used in Python.
Here is a motivating example:

[^3]: Yes, newtypes also have other use-cases than the one described here, stop yelling at me.

```python
class Database:
  def get_car_id(self, brand: str) -> int:
  def get_driver_id(self, name: str) -> int:
  def get_ride_info(self, car_id: int, driver_id: int) -> RideInfo:

db = Database()
car_id = db.get_car_id("Mazda")
driver_id = db.get_driver_id("Stig")
info = db.get_ride_info(driver_id, car_id)
```

Spot the error?

...

...

The arguments for `get_ride_info` are swapped. There is no type error, because both car IDs
and driver IDs are simply integers, therefore the types are correct, even though semantically
the function call is wrong.

We can solve this problem by defining separate types for different kinds of IDs with a "NewType":

```python
from typing import NewType

# Define a new type called "CarId", which is internally an `int`
CarId = NewType("CarId", int)
# Ditto for "DriverId"
DriverId = NewType("DriverId", int)

class Database:
  def get_car_id(self, brand: str) -> CarId:
  def get_driver_id(self, name: str) -> DriverId:
  def get_ride_info(self, car_id: CarId, driver_id: DriverId) -> RideInfo:


db = Database()
car_id = db.get_car_id("Mazda")
driver_id = db.get_driver_id("Stig")
# Type error here -> DriverId used instead of CarId and vice-versa
info = db.get_ride_info(<error>driver_id</error>, <error>car_id</error>)
```

This is a very simple pattern that can help catch errors that are otherwise hard to spot. It is
especially useful e.g. if you're dealing with a lot of different kinds of IDs (`CarId` vs `DriverId`)
or with some metrics (`Speed` vs `Length` vs `Temperature` etc.) that should not be mixed together.

# Using construction functions
One thing that I quite like about Rust is that it doesn't have constructors *per se*. Instead, 
people tend to use normal functions to create (ideally properly initialized) instances of 
structs. In Python, there is no constructor overloading, therefore if you need to construct an object
in multiple ways, someone this leads to an `__init__` method that has a lot of parameters which serve
for initialization in different ways, and which cannot really be used together.

Instead, I like to create "construction" functions with an explicit name that makes it obvious how to
construct the object and from which data:

```python
class Rectangle:
    @staticmethod
    def from_x1x2y1y2(x1: float, ...) -> "Rectangle":
    
    @staticmethod
    def from_tl_and_size(top: float, left: float, width: float, height: float) -> "Rectangle":
```

This makes it much cleaner to construct the object, and doesn't allow users of the class to pass invalid
data when constructing the object (e.g. by combining `y1` and `width`).

# Encoding invariants using types
Using the type system itself to encode invariants that would otherwise be only tracked at runtime is a very
general and powerful concept. In Python (but also other mainstream languages), I often see classes
that are big hairy balls of mutable state. One of the sources of this mess is code that tries to track
the object's invariants at runtime. It has to consider many situations 
that can happen in theory, because they were not made impossible by the type system ("what if the
client has been asked to disconnect, and now someone tries to send a message to it, but the socket
is still connected" etc.).

#### Client
Here is a typical example:
```python
class Client:
  """
  Rules:
  - Do not call `send_message` before calling `connect` and then `authenticate`.
  - Do not call `connect` or `authenticate` multiple times.
  - Do not call `close` without calling `connect`.
  - Do not call any method after calling `close`.
  """
  def __init__(self, address: str):

  def connect(self):
  def authenticate(self, password: str):
  def send_message(self, msg: str):
  def close(self):
```
…easy, right? You just have to carefully read the documentation, and make sure that you never 
break the mentioned rules (lest you invoke either undefined behaviour or a crash). An alternative is to
fill the class with various asserts that check all the mentioned rules at runtime, which leads to messy code, 
missed edge cases and slower feedback when something is wrong (compile-time vs run-time).
The core of the problem is that the client can exist in various (mutually exclusive) states, but instead
of modelling these states separately, they are all merged in a single type.

Let's see if we can improve this by splitting the various states into separate types [^4].

[^4]: This is known as the [typestate pattern](http://cliffle.com/blog/rust-typestate/).

- First of all, does it even make sense to have a `Client` which isn't connected to anything? 
  Doesn't seem like so. Such an unconnected client can't do anything until you call `connect` 
  anyway. So why allow this state to exist at all? We can create a construction function called 
  `connect` that will return a connected client:

```python
def connect(address: str) -> Optional[ConnectedClient]:
  pass

class ConnectedClient:
  def authenticate(...):
  def send_message(...):
  def close(...):
```
If the function succeeds, it will return a client that upholds the "is connected" invariant, and on which
you cannot call `connect` again to mess things up. If the connection fails, the function can raise an exception
or return `None` or some explicit error.

- A similar approach can be used for the `authenticated` state. We can introduce another type, 
  which holds the invariant that the client is both connected and authenticated:

```python
class ConnectedClient:
  def authenticate(...) -> Optional["AuthenticatedClient"]:

class AuthenticatedClient:
  def send_message(...):
  def close(...):
```
Only once we actually have an instance of an `AuthenticatedClient`, then we can actually start sending messages.

- The final problem is with the `close` method. In Rust (thanks to
[destructive move semantics](https://www.thecodedmessage.com/posts/cpp-move/)), we are able to express the fact
that when the `close` method is called, you cannot use the client anymore. This is not really possible in Python,
so we have to use some workaround. One solution could be to fall back to runtime tracking, introduce a boolean
attribute in the client, and assert in `close` and `send_message` that it hasn't been closed already.
Another approach could be to remove the `close` method completely and just use the client as a context manager:

```python
with connect(...) as client:
    client.send_message("foo")
# Here the client is closed
```

With no `close` method available, you cannot close the client twice by accident[^5].

[^5]: Unless you try hard and e.g. call the magic `__exit__` method manually.

#### Strongly-typed bounding boxes
Object detection is a computer vision task that I sometimes work on, where a program has to detect a set of bounding boxes
in an image. Bounding boxes are basically glorified rectangles with some attached data, and when you implement object
detection, they are all over the place. One annoying thing about them is that sometimes they are normalized (the coordinates and sizes of the rectangle are
in the interval `[0.0, 1.0]`), but sometimes they are denormalized (the coordinates and sizes are bounded by the dimensions
of the image they are attached to). When you send a bounding box through many functions that handle e.g. data
preprocessing or postprocessing, it is easy to mess this up, and e.g. normalize a bounding box twice, which leads to
errors that are quite annoying to debug.

This has happened to me a few times, so one time I decided to solve this for good by splitting these two types
of bboxes into two separate types:

```python
@dataclass
class NormalizedBBox:
  left: float
  top: float
  width: float
  height: float


@dataclass
class DenormalizedBBox:
  left: float
  top: float
  width: float
  height: float
```

With this separation, normalized and denormalized bounding boxes cannot be easily mixed together anymore, which
mostly solves the problem. However, there are some improvements that we can make to make the code more ergonomic:

- Reduce duplication, either by composition or inheritance:

```python
@dataclass
class BBoxBase:
  left: float
  top: float
  width: float
  height: float

# Composition
class NormalizedBBox:
  bbox: BBoxBase

class DenormalizedBBox:
  bbox: BBoxBase

Bbox = Union[NormalizedBBox, DenormalizedBBox]

# Inheritance
class NormalizedBBox(BBoxBase):
class DenormalizedBBox(BBoxBase):
```
- Add a runtime check to make sure that the normalized bounding box is actually normalized:

```python
class NormalizedBBox(BboxBase):
  def __post_init__(self):
    assert 0.0 <= self.left <= 1.0
    ...
```
- Add a way of converting between the two representations. In some places, we might want to know the explicit
representation, but in others, we want to work with a generic interface ("any type of BBox"). In that case we should
be able to convert "any BBox" to one of the two representations:

```python
class BBoxBase:
  def as_normalized(self, size: Size) -> "NormalizeBBox":
  def as_denormalized(self, size: Size) -> "DenormalizedBBox":

class NormalizedBBox(BBoxBase):
  def as_normalized(self, size: Size) -> "NormalizedBBox":
    return self
  def as_denormalized(self, size: Size) -> "DenormalizedBBox":
    return self.denormalize(size)

class DenormalizedBBox(BBoxBase):
  def as_normalized(self, size: Size) -> "NormalizedBBox":
    return self.normalize(size)
  def as_denormalized(self, size: Size) -> "DenormalizedBBox":
    return self
```
With this interface, I can have the best of both worlds -- separated types for correctness, and a unified interface
for ergonomics.

Note: If you want to add some shared methods to the parent/base class that return an instance of the corresponding class,
you can use `typing.Self` from Python 3.11:

```python
class BBoxBase:
  def move(self, x: float, y: float) -> typing.Self: ...

class NormalizedBBox(BBoxBase):
  ...

bbox = NormalizedBBox(...)
# The type of `bbox2` is `NormalizedBBox`, not just `BBoxBase`
bbox2 = bbox.move(1, 2)
```

#### Safer mutexes
Mutexes and locks in Rust are usually provided behind a very nice interface with two benefits:

- When you lock the mutex, you get back
  a [guard](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html)
  object, which unlocks the mutex automatically when it is destroyed, leveraging the venerable
  [RAII](https://en.wikipedia.org/wiki/Resource_acquisition_is_initialization) mechanism:
```rust
{
    let guard = mutex.lock(); // locked here
    ...
} // automatically unlocked here
```
This means that you cannot accidentally forget to unlock the mutex. A very similar mechanism is
also commonly used in C++, although the explicit `lock`/`unlock` interface without a guard object
is also available for [`std::mutex`](https://en.cppreference.com/w/cpp/thread/mutex), which means that
they can still be used incorrectly.

- The data protected by the mutex is stored directly in the mutex (struct). With this design, it is
  [impossible](https://doc.rust-lang.org/std/sync/struct.Mutex.html#method.lock) to access the
  protected data without actually locking the mutex. You have to lock the mutex first to get the
  guard, and then you access the data using the guard itself:
```rust
let lock = Mutex::new(41); // Create a mutex that stores the data inside
let guard = lock.lock().unwrap(); // Acquire guard
*guard += 1; // Modify the data using the guard
```

This is in stark contrast to the usual mutex APIs found in mainstream languages (including
Python), where the mutex and the data it protects are separated, and therefore you can
easily forget to actually lock the mutex before accessing the data:

```python
mutex = Lock()

def thread_fn(data):
    # Acquire mutex. There is no link to the protected variable.
    mutex.acquire()
    data.append(1)
    mutex.release()

data = []
t = Thread(target=thread_fn, args=(data,))
t.start()

# Here we can access the data without locking the mutex.
data.append(2)  # Oops
```

While we cannot get the exact same benefits in Python as we get in Rust, not all is lost. Python locks implement the
context manager interface, which means that you can use them in a `with` block to make sure that they are automatically
unlocked at the end of the scope. And with a little bit of effort, we can go even further:

```python
import contextlib
from threading import Lock
from typing import ContextManager, Generic, TypeVar

T = TypeVar("T")

# Make the Mutex generic over the value it stores.
# In this way we can get proper typing from the `lock` method.
class Mutex(Generic[T]):
  # Store the protected value inside the mutex 
  def __init__(self, value: T):
    # Name it with two underscores to make it a bit harder to accidentally
    # access the value from the outside.
    self.__value = value
    self.__lock = Lock()

  # Provide a context manager `lock` method, which locks the mutex,
  # provides the protected value, and then unlocks the mutex when the
  # context manager ends.
  @contextlib.contextmanager
  def lock(self) -> ContextManager[T]:
    self.__lock.acquire()
    try:
        yield self.__value
    finally:
        self.__lock.release()

# Create a mutex wrapping the data
mutex = Mutex([])

# Lock the mutex for the scope of the `with` block
with mutex.lock() as value:
  # value is typed as `list` here
  value.append(1)
```

With this design, you can only get access to the protected data after
you actually lock the mutex. Obviously, this is still Python, so you
can still break the invariants - e.g. by storing another pointer to the protected data outside of the mutex.
But unless you're behaving adversarially, this makes the mutex interface in Python much safer to
use.

Anyway, I'm sure that there are more "soundness patterns" that I use in my Python code, but that's all I can think
of at the moment. If you have some examples of similar ideas or any other comments, let me know on
[Reddit](https://www.reddit.com/r/rust/comments/13mxu2r/writing_python_like_its_rust/).
