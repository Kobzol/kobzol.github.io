---
layout: "post"
title: "Async Rust is about concurrency, not (just) performance"
alternative_title: In defense of async (Rust)
date: "2025-01-15 12:00:00 +0100"
categories: rust
#reddit_link: TODO
---

> **TLDR**: I think that the primary benefit of `async/await` is that it lets us concisely express complex concurrency; any (potential) performance improvements are just a second-order effect. We should thus judge async primarily based on how it simplifies our code, not how (or if) it makes the code faster.

While teaching a [Rust course]({% post_url 2024-12-18-rust-exercises %}) at my university, I showed my students various ways to implement networking applications, from blocking I/O with threads, non-blocking I/O with manual state machines and ultimately `async/await`. When I was explaining the motivation for async Rust, I was reminded of a pet peeve of mine related to the way it is sometimes being discussed online, where performance is being used as the main motivation when async Rust is being promoted, which in turn provokes critical responses that claim that the performance effect is probably not worth the problems associated with async. 
I think that this view is incomplete; to me, the primary motivation to use async is almost never performance (alone), but rather the ability to elegantly express and compose concurrent processes, which I consider to be the true killer feature of the `async/await` mechanism. I repeatedly tried to express this sentiment in comments on Reddit and Twitter, so I thought that I should finally write it down so that I can refer to it in the future.

In this post, I'll try to explore different motivations for using async, show a few examples where I appreciate the benefits that async gives us, and examine some proposed alternatives and why I don't think that they are viable for the use-cases that I usually need to solve. This is all interspersed by an assorted collection of my opinions on async, which is why it is a bit rambly -- you have been warned :)

## Why do we even need async?
There are many angles to this question, but why not start with a bit of history -- why did Rust originally implement support for `async/await`? boats does a great job of explaining its history in [this blog post](https://without.boats/blog/why-async-rust/), which mentions that async Rust was introduced to enable ergonomic *user-space concurrency* that achieves high performance. The user-space part is important; boats contrasts it to using concurrency using OS primitives (threads), which tends to be associated with higher overhead and worse performance.
I think that many people took away the message that reduced overhead and higher performance is *the* reason why async is useful; it seems to me that it is the dominant topic when async Rust is mentioned online[^c10k]. Interestingly, the performance aspects are being emphasized both by fans of async Rust ("use async to get BlAZinGLy fast performance") and its critics ("you don't need the performance offered by async Rust unless you're 
FAANG", "the performance gains are not worth the problems caused by it" or "threads would be as fast or faster").

[^c10k]: I wonder if the popularity of the [C10k](https://en.wikipedia.org/wiki/C10k_problem) problem has something to do with it. It seems to me that some people still think that you need non-blocking I/O or asynchronous processing to handle 10 thousand clients on a single machine in this day and age.

As I already suggested at the beginning of this post, I actually kind of agree with the framing of async critics here. I also think that many applications using async Rust do not achieve (or even need to achieve in the first place!) significant performance gains when compared to using threads and blocking I/O. The notion of "just add `.await` to your code and it will suddenly become X times faster", which seems to be (at least in my view) sometimes written between the lines when async Rust is being promoted, is not very realistic.

It is important to clarify one thing here; any potential performance gains should come from using non-blocking I/O and interruptible functions (state machines), which can help overlap execution and thus achieve better concurrency. `async/await` is simply a mechanism for leveraging these concepts in an ergonomic way. So there is no reason why introducing async to code that has no potential for concurrent execution should improve performance. In fact, on its own, async actually introduces (usually relatively small) overhead.

Despite the fact that I have been using async Rust heavily in [various](https://github.com/it4innovations/rsds) [distributed](https://github.com/it4innovations/hyperqueue) systems in the context of supercomputers and HPC, which is known for, you know, *high performance*, the actual performance implications of async were never the primary reason why I wanted to use it. For me, the main reason is the *user-space concurrency* part of the original motivation. I often want to express complex concurrent scenarios in my applications, be it in distributed systems, web services or even CLI tools. Performing two actions concurrently and seeing which one completes first. Reading messages from two data streams, while sending responses to another data stream, and also periodically doing something completely different at the same time. Implementing a timeout or a heartbeat mechanism. Starting several operations at once, so that they can progress concurrently, and periodically observe their progress. These sorts of things.

*[CLI]: Command-line Interface
*[HPC]: High-Performance Computing

While some of these use-cases are related to performance, and can potentially even make my programs faster, I primarily want to be able to express them in the first place. Such concurrent logic is usually quite difficult to achieve with blocking operations (I/O), so I need to use non-blocking operations (I/O) instead. And async allows me to do that without manually writing state machines and event loops, which is incredibly error-prone. In particular, it gives me the ability to easily manage, express and most importantly compose concurrent processes using "sequentially looking" code that is relatively easy to understand and maintain. **So it's not that I worry that my concurrent code would be too slow without async, it's more that I often don't even know how I would reasonably express it without async!**

## Expressing concurrency with async
I'll show what I like about async on the usage of a timeout for a potentially long-running operation. Even though it is one of the most basic use-cases useful in concurrent programs, it makes use of the most important aspects of async code. Here is how it can be expressed with async Rust and `tokio`:

```rust
let future = do_something();
let result = tokio::time::timeout(
  Duration::from_secs(10),
  future
).await;
```

This code is seemingly as simple as it gets. It can be so simple because of the contract of `Future`s in Rust. Each future can be cancelled by dropping it (i.e. it can be stopped without cooperation from the future itself) and its progress has to be driven from the outside by polling it (i.e. it cannot make progress on its own). Both of these properties are useful for timeouts.

The fact that I can pause *any* future by simply not polling it anymore gives me a lot of control. I can compose a single [timeout](https://docs.rs/tokio/1.43.0/tokio/time/fn.timeout.html) implementation with any kind of future, without having to know how it works, and crucially without the future itself having to know that it is being timeouted. I could replace `do_something` with any other future, and it would work the same. This allows loose coupling of concurrent operations (mostly) without exposing their implementation details[^but].

[^but]: Yes, I know that you might be thinking "But what about...", I'll discuss the issues later in the post :)

The fact that we can cancel any future by (synchronously) dropping it (and thus never polling it again) without knowing its implementation details lets us make sure that after the timeout has elapsed, the future won't continue and unexpectedly make progress anymore, which we usually want to avoid.

Another huge advantage of async is that `.await`s form very explicit suspend points. Especially if I use the single-threaded runtime (which I prefer), I can be sure that no other code will run in-between them, which makes it easier to think about potential race conditions and make sure that invariants will be upheld. 

Of course, if you have interacted with async Rust before, you know that the benefits described above also bring a lot of trade-offs. I'll talk about these later [below](#why-not-use-async), but first I want to show two more real-world use-cases of async that come from [HyperQueue](http://github.com/it4innovations/hyperqueue) (HQ), a distributed HPC task scheduler that I work on.

*[HQ]: HyperQueue

### Perform a periodic activity while waiting for something
In HQ's TUI [dashboard](https://it4innovations.github.io/hyperqueue/stable/cli/dashboard/), we need to read new events (e.g. that a task finished its execution) from a TCP/IP socket, and periodically send a batch of fetched events to another part of the application that then displays them in a terminal user interface. A simplified version (ignoring error handling and unrelated concepts) of that looks something like this:
```rust
let client = create_socket();
let mut events = vec![];
let mut tick = tokio::time::interval(Duration::from_millis(500));

loop {
  select! {
    _ = tick.tick() => {
      channel.send(std::mem::take(&mut events)).await;
    }
    event = client.recv() => {
      events.push(event);
    }
  }
}
```

> This way of using `select` in a loop could potentially cause [issues](https://blog.yoshuawuyts.com/futures-concurrency-3/) regarding cancellation of futures (although in this case it's fine). It can be implemented in a better way, but I didn't want to complicate the example.

Here I need the ability to perform a periodic action (send a batch of events) even though I might be currently waiting for the next event to be received -- I don't want to be stuck on receiving the next event before I can publish the current batch of events to the TUI.

*[TUI]: Terminal User Interface

Performing a periodic operation while waiting for a set of other operations to complete is a very common pattern that I use all the time, and with async, it's quite simple to achieve.

### Temporarily pausing a future
Sometimes we need to be sure that some code will *not* be executing during a given period of time. In the HyperQueue server, there is an event streaming system that writes events to a binary file on disk. When a client connects to the server, it should receive a replay of all events that have happened so far. Because the server does not hold all events in memory, it first has to replay all the previous events from the file on disk. Only then it starts streaming new events directly to the client. However, there is a potential race condition; if new events are generated before the file is fully replayed and the client streaming starts, the client might miss them. Furthermore, we should not write to the event file while we are also reading from it. Therefore, we need to pause the writing of events to the file before the replay is completed. In a simplified form, that can look something like this:

```rust
loop {
  tokio::select! {
    event = events.recv() => {
      write_event_to_file(event).await;
    }
    client = receive_new_client() => {
      // Here we are sure that the first branch of select! won't be executing
      // before the replay is completed, because we simply don't poll it.
      replay_events(&mut client).await;
    }
  }
}
```

> In the [real implementation](https://github.com/it4innovations/hyperqueue/blob/16a786150117d96631aa8b65240388509992721c/crates/hyperqueue/src/server/event/journal/stream.rs#L74), this is combined with periodic flushing of a buffer of events to the file, which corresponds to the previous "periodic activity" use-case. With async, that means just another branch in the `select!` expression.

The fact that `Future`s have to be explicitly polled is very useful here - if I don't poll a future, I can be sure that it won't be making progress if I don't want it to. If the file writing future would run on a separate thread (or even a separate async task spawned e.g. with [tokio::spawn](https://docs.rs/tokio/latest/tokio/task/fn.spawn.html)), I could not exert control over its behavior in such a way.

A lot of use-cases where I express some concurrency patterns (i.e. where it isn't just "normal blocking-like code + `.await`") are built on a combination of these standard primitives, like select (race), join, perform a periodic activity, a timeout or something similar. Async makes it easy to express such concurrent behavior.

## Why *not* use async?

Now comes the time to discuss when *not* to use async. It's not hard to find reasons for not using async Rust online, as there is a certain trend of negativity towards it. There are many blog posts and articles that give both async Rust and the `async/await` concept in general a bad rep (like [1](https://web.archive.org/web/20240205152633/https://blog.hugpoint.tech/avoid_async_rust.html), [2](https://bitbashing.io/async-rust.html), [3](https://hirrolot.github.io/posts/rust-is-hard-or-the-misery-of-mainstream-programming.html), [4](https://eta.st/2021/03/08/async-rust-2.html), [5](https://n8s.site/async-rust-isnt-bad-you-are), [6](https://corrode.dev/blog/async/), [7](https://lucumr.pocoo.org/2024/11/18/threads-beat-async-await/) or [8](https://trouble.mataroa.blog/blog/asyncawait-is-real-and-can-hurt-you/), and also the venerable [function colouring post](https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/)). These posts usually claim that async has a lot of issues, brings unnecessary complexity and the performance that we gain from it is not worth the hassle.

As I already stated before, I also think that motivating async by magical performance gains alone is probably not the right fit for many use-cases. If performance was supposed to be the main benefit of async Rust, I would probably also remain a skeptic, because it does indeed bring a lot of issues! `Future` implementations must be written in a way that avoids [blocking](https://ryhl.io/blog/async-what-is-blocking/). Implementation details of futures can in fact leak -- for example, if the future needs to spawn an async task or perform some time-based operations, it will have to be polled in the context of a specific runtime (usually `tokio`). And if it does indeed spawn an async task, we lose precise control over the execution of that task, and potentially also of its cancellation (depending on how well is structured concurrency handled by the future that spawned it).
Furthermore, the fact that we can cancel futures by dropping them, without letting them perform asynchronous cleanup, can be a footgun, so sometimes we must care about [cancellation safety](https://blog.yoshuawuyts.com/async-cancellation-1/). Pin is confusing and hard to use. The `select!` macro is quite messy.

Async Rust also currently has many missing pieces, and I am often annoyed by them. I would *love* to use async iterators, and to a slightly lesser extent async closures[^async-closures] and async Drop[^async-drop]. I'd like to stop thinking about cancellation safety and have a half-decent way of debugging async stacktraces and managing structured concurrency. Some of these issues are very difficult to resolve without making [backwards-incompatible changes](https://without.boats/blog/pin/), but others haven't been resolved yet simply because no one had the time yet to drive them to completion[^zulip]. And while some of these issues are in fact shared with `async/await` in other languages, they can *feel* especially painful in Rust, both because of its unique design constraints and also because "normal" (sync) Rust is known for having a relatively low amount of footguns, so going from sync Rust to async Rust can present a sharp increase in complexity and annoyance.

[^async-closures]: Coming to a stable Rust near you [soon](https://github.com/rust-lang/rust/pull/132706).
[^async-drop]: Currently being implemented as an [experiment](https://github.com/rust-lang/rust/pull/123948).
[^zulip]: If you'd like to help, drop by our [Zulip](https://rust-lang.zulipchat.com/)!

That being said, I personally don't find all the aspects of async Rust that are often hated to be equally problematic, and I think that we can get rid of some of the mentioned issues if we change the way how we use it. Specifically, I usually don't care about the `Send + Sync` issue, because I almost exclusively use single-threaded executors (and I share the opinion that they should be the [default](https://maciej.codes/2022-06-09-local-async.html)). They don't require using multithreaded locking, which is generally good performance-wise, they don't require caring about `Send` and `Sync`, and most importantly they make the resulting system *much easier* to reason about, and thus make it easier to avoid race conditions in heavily concurrent code.
On another note, I think that function coloring was the right choice for Rust and I appreciate it, although I do find it less appealing in languages with a GC, which could afford to make async programming more magical and thus potentially avoid the coloring. I also think that the "runtime (e.g. `tokio`) vendor lock-in" is not such a big issue, it's just too much of an ask to avoid that. 

Taking all of the above into account, that's a lot of issues and limitations, which can be at times very annoying! So it's easy to see why async Rust is often being criticised. But I think that it is important to also acknowledge the benefits that async brings when discussing it, so that we can properly acknowledge its trade-offs. Even though I am `Pin`fully[^pun-intended] aware of the issues of async, I still use it a lot and find it invaluable, because it gives me the ability to easily implement and compose concurrent operations. It is definitely not perfect, it currently lacks the ability to cleanly express certain patterns, and it comes at the cost of having to think about various aspects that might not be always checkable by the compiler, but I cannot imagine writing concurrent applications without it anymore.

[^pun-intended]: ~~Pin~~ Pun intended.

> Note that a corollary of what I wrote above is that if you don't need to express complex concurrent patterns, then using async might be pure overhead (both in terms of code complexity and actual performance). Of course, if crates or dependencies that you want to use are async, then you might not have much choice -- but that is a topic for another blog post :)

So, if I were to stop using async (which is a suggestion made by several of the mentioned blog posts), I would need to use some alternative instead. And that's the problem -- I just don't see any viable alternative (in Rust), and don't understand how are the alternatives mentioned in the linked blog posts supposed to provide me with the same ability to express concurrency in a maintainable way.

## Alternatives
Let's go through some alternatives that are usually suggested by posts that critique async Rust:

- Use non-blocking I/O with a manual event loop ([1](https://web.archive.org/web/20240205152633/https://blog.hugpoint.tech/avoid_async_rust.html), [2](https://n8s.site/async-rust-isnt-bad-you-are)). Indeed, non-blocking I/O is what I want, and if I would write my own event loop and my own state machines, I could sidestep most of the complexity associated with `async/await`. This approach also has the benefit of avoiding the pervasive use of reference counting, as it enables to pass good ol' references to the functions that perform non-blocking I/O. However, writing code like that is both verbose and incredibly error-prone! While it would most likely not cause undefined behaviour and memory errors in Rust, unlike in e.g. *C* or *C++*, I cannot really imagine writing all the asynchronous applications that I have created over the years using this low-level approach. `async/await` was created precisely so that we would not have to deal with this, and avoid state-machine related bugs that 
  are so easy to make!

  To me, suggesting to write state machines and event loops manually to avoid the complexity and issues of async is like saying that I should use `malloc` and `free` to avoid the rough edges of RAII, or use *C* to avoid the complexity of Rust. Yes, `nginx` uses non-blocking I/O, and it was [written without await](https://trouble.mataroa.blog/blog/asyncawait-is-real-and-can-hurt-you/#asyncawait-is-almost-never-faster), but does that mean that I want to write every asynchronous application in the style of `nginx`? No, absolutely not, thank you. There are people that consider Rust to be a strictly [low-level](https://n8s.site/async-rust-isnt-bad-you-are) system programming language where writing code like this should be the norm, but I think that Rust can offer us much more, and actually combine low-level control with high-level affordances. So this is not a viable alternative *to me*.

- Use separated processes that communicate through message passing, otherwise known as [CSP](https://en.wikipedia.org/wiki/Communicating_sequential_processes). This is a good advice, and I do indeed use CSP-like actors a lot in my code. But that doesn't mean that I don't need to express other forms of communication or concurrency! In fact, I often implement actors as individual async tasks that communicate through channels, but they then also perform various concurrent actions inside them, and I use async to express these concurrency patterns. So I don't see CSP as an alternative to `async/await`, but rather as a complementary way of designing the structure of complex concurrent programs.

- Use another language. Well, this is of course *an alternative*, but not very relevant if I want (or need) to use Rust because of other reasons (like the fact that it is performant by default, allows me to easily write sound and often-insta-correct code, has incredible tooling, yada yada). We should also not forget that there are certain trade-offs here. Async Rust tries to achieve something incredibly difficult -- combine the dynamic nature of coroutines and non-blocking I/O that can be interrupted and "jump" to a completely different execution context in the middle of execution, with a rigid static analysis system for determining the lifetime and ownership of data that is checked at compile-time based on the (mostly lexical) scope of variables. And furthermore, it does that while not requiring a runtime or a GC, supporting embedded systems, providing low overhead and presenting a very high-level and relatively ergonomic interface (I'm talking about `async fn`, not `Pin`, of
  course.[^pin-ergonomics]).

  I think that async Rust does a pretty great job in this area, despite its shortcomings, and while it might not get all the way there, it is impressive what it can achieve in many diverse use-cases. Yes, using Go or e.g. Java's [Project Loom](https://openjdk.org/projects/loom/) does not require you to think about function coloring and seemingly makes handling concurrency simpler, but it also comes at the cost of a GC and more painful FFI due to not using the native (*C*) stack. And it also does not give you the same level of control over *how* exactly is the concurrency performed (such as when your runtime automatically starts futures in the background as e.g. JavaScript does).

[^pin-ergonomics]: Althought we might get there [one day](https://github.com/rust-lang/rust/issues/130494).

*[GC]: Garbage collector
*[FFI]: Foreign-Function Interface

And that brings me to the last (and probably most commonly mentioned) alternative to async Rust -- "just use threads". More precisely, I always assumed this to mean "threads in combination with blocking I/O", because using non-blocking I/O is essentially the "manual epoll/state-machines" alternative mentioned above. I have to admit that I find this advice baffling. Either the things that I want to express with async Rust are unusually complex or I'm missing some obvious way how to use threads and blocking I/O for such use-cases in a way that does not make me lose sanity. I cannot really imagine writing the concurrent logic that I showed earlier in this way.

To clarify, the main problem that I have with this alternative is not using threads *per-se* (as they are fairly ergonomic and uniquely safe to use in Rust), but rather using blocking I/O instead of non-blocking I/O (or, more generally, using uninterruptible operations instead of interruptible operations). Blocking I/O inhibits concurrency *by design*, so using threads then becomes a necessity in order to achieve any concurrency at all, but expressing the various concurrency primitives with threads is more difficult than with coroutines, at least in my experience.

Below, I'll try to implement the timeout example with blocking I/O and threads, using two different approaches.

### Using I/O operations that support timeout
If you have a specific I/O operation that allows expressing timeouts, such as a [read operation](https://doc.rust-lang.org/std/net/struct.TcpStream.html#method.set_read_timeout) on a TCP/IP stream from the standard library, you can set the timeout directly and then perform the blocking operation:
```rust
let stream = TcpStream::connect("addr")?;
stream.set_read_timeout(Some(Duration::from_secs(10)))?;
let data = stream.read(...)?;
```

It looks simple for this three line piece of code, but unlike the async solution, it does not scale much further. A real implementation of socket communication would do more things -- connect to a remote host, perform a number of `read` calls to get a full (e.g. a line-delimited) message from it, and then return that message to the caller. If I wanted to time out this whole combined process, I would need to use a different [method](https://doc.rust-lang.org/std/net/struct.TcpStream.html#method.connect_timeout) for connecting and (since multiple `read` calls could be needed to download a whole message) I would also need to call `set_read_timeout` before each `read` call and dynamically recalculate the remaining time before a timeout should occur[^syscall].

[^syscall]: Each such call is a separate syscall, so I imagine it would not be great for performance either.

But the implementation complexity is not the worst thing here. The main issue in my view is simply that I have to add the knowledge of timeouts directly within the implementation of my I/O operation. I cannot simply add it "from the outside", as I could with async. To support timeouts anywhere, I would need to do that in all my concurrent operations. And even then, it would only be usable for timeouts; it would not allow me to specify other concurrent patterns out of the box, such as waiting until the first of several such operations completes its execution or cancellation. When I design the structure of concurrent applications, I want to be able to quickly experiment with various ways of composing the individual asynchronous processes and actors. Having to implement support for concurrency primitives into each such process would be cumbersome and slow.

This approach is also not great from the point of actually using such a concurrent process from the outside. If I wanted to put the message reading logic behind any sort of abstraction (function/struct/enum/trait) so that I could (re)use it in various places of my app, then I could not directly set the timeout "from the outside", without knowing which specific operation is used inside the abstraction. Instead, I would need to add the capability of exposing the timeout to that abstraction. While that's not the end of the world, it does complicate the interface, and would need to be done for all kinds of concurrency primitives that I would want to support.

The last problematic aspect of this approach is that even with the timeout, the I/O operation still blocks the current thread, although that is already implied by using blocking I/O and thus avoiding writing the complex state machines by hand. This is not such an issue, as a coarse level of concurrency can be regained by simply running multiple threads, where each one performs a specific asynchronous operation. But it does require spawning separate execution contexts to gain *any* concurrency at all, which limits the amount of control I have over these asynchronous operations (this behavior is shared with using APIs like [`tokio::spawn`](https://docs.rs/tokio/latest/tokio/task/fn.spawn.html), by the way).

Using this approach of course requires that you use an (I/O) operation that "natively" supports timeouts in the first place. For example, the [`TcpListener::accept`](https://doc.rust-lang.org/std/net/struct.TcpListener.html#method.accept) method in the standard library does not allow expressing a timeout[^socket-fiddling]. If you use it, it will block the current thread until a client connects. I even gave an assignment to my students to try to figure out how to get around this problem :smile:. When this happens, you will have to use a different approach, such as the one described below.

[^socket-fiddling]: Without fiddling with the socket file descriptor in OS-specific ways.

### Channels
The composability problem with the approach above can be somewhat remedied via channels. A common way to add a timeout to an "arbitrary" blocking operation is to run it inside a thread, create a channel, send the `sender` half to the thread, and let it publish a result into the channel once it finishes. Then we can use the `receiver` half to read the result from a different thread using the convenient [`recv_timeout`](https://doc.rust-lang.org/std/sync/mpsc/struct.Receiver.html#method.recv_timeout) method, which allows expressing a timeout:
```rust
let (tx, rx) = std::sync::mpsc::sync_channel(1);
let t1 = std::thread::spawn(move || {
    let result = do_something();
    tx.send(result).unwrap();
});
let result = rx.recv_timeout(Duration::from_secs(10))?;
t1.join().unwrap();
```
This actually works quite well. We could even wrap it in a `timeout` helper method to achieve a very similar interface to what we had with `tokio`. However, apart from the less-than-great fact that we have to spawn (or at least acquire from a threadpool) a thread and allocate a channel just to perform a simple timeout, the bigger problem is with the last line, `t1.join().unwrap()`. Because even if we time out while waiting for the result, the operation itself will still continue forward, unless we cancel it somehow.

Therefore, to gain the desired functionality (actually stop the operation after it timed out), we would need to implement the concurrent operation in a way so that it would explicitly know when it needs to be stopped, and design some mechanism for communicating that information. This could perhaps be done by using something like the [CancellationToken](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken) from the .NET ecosystem, but that would need to be used pervasively in the Rust ecosystem, so that the all primitives that we commonly use can actually be cancelled. And it would also add complexity to the implementation of (nearly all) asynchronous operations, which would need to take the token into account, and at least propagate it to nested asynchronous operations. Also, there are some operations that simply cannot be canceled; there is no cancellation token that can be passed to the `read` syscall on Linux.

To be fair, you can get quite far with channels backed by threads, but it's far from being as simple as with async, and you lose the precise control over the execution of futures. It is of course possible to implement any concurrency patterns that can be done with async also using threads (Turing completeness and all), but at least for me, it's often just too cumbersome in practice. Thus, I'd rather deal with the limitation of async than implement complex concurrency scenarios using threads alone.

## Conclusion
It seems to me that we sometimes want too much from async Rust. We want it to be extremely fast and completely zero-cost, to be usable anywhere from microcontrollers to supercomputers, to be simple to understand and use, to not contain any footguns and to be usable with any kind of runtime. But even though it sometimes might seem like Rust can perform miracles, there are certain limits to everything; we should not expect a given feature to be the best in all possible axes. I think that despite its issues, async Rust provides a lot of tangible benefits that should not be ignored when we discuss it. I personally like to use async and wouldn't want to go back to dealing with concurrency in a crude way using threads if I don't have to.

Anyway, that was enough of my rambling. This is a very complex topic, and I have omitted many aspects in this post, e.g. by reducing throughput and latency optimizations (both relevant to concurrency and non-blocking I/O) to just "performance" and not dealing with other use-cases like embedded (where I'd say async is even more useful though), but hopefully I got the gist of my idea across.

I'm interested in whether you have a suggestion on how to easily implement concurrent patterns without async. Let me know on [Reddit]({{ page.reddit_link }}) if you have any suggestions or comments!
