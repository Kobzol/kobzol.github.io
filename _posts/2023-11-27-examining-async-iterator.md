---
layout: "post"
title: "Examining Rust async iterator approaches"
date: "2023-11-27 21:16:00 +0100"
categories: rust
---

I'm an avid user of async Rust, and I have used it to implement various kinds of
distributed systems and networking applications. Even though async Rust is very helpful in expressing
concurrent processes, synchronization patterns, timeouts etc., it is not a secret that there are still
a lot of papercuts and missing features in it. One of these is an interface for asynchronous iterators.

A [recent post](https://without.boats/blog/poll-next) by boats about different approaches of
implementing asynchronous iterators in Rust reminded me of this topic again. In this post, boats
argues that an `AsyncIterator` trait with `poll_next` method (which is a "low-level" approach,
conceptually similar to `Future`'s `poll`):

```rust
trait AsyncIterator {
    type Item;
    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<Option<Self::Item>>;
}
```

is superior in pretty much all aspects to a more "high-level" approach using the `async fn` syntax:

```rust
trait AsyncIterator {
    type Item;
    async fn next(&mut self) -> Option<Self::Item>;
}
```

I saw a lot of discussion of these two approaches, but I haven't seen actual implementations of
non-toy asynchronous iterators using them. Of course, such implementations do exist *somewhere*, but
I felt that I wanted to get a feeling of these approaches myself, so that I could evaluate which approach
I like better. Now, I'm no language designer, and I have no idea of all the repercussions of choosing
a specific approach for Rust in this case, but after trying these two out, I definitely have a
favourite :) I'll write about which approach I liked more at the end of the post.

To evaluate these approaches, I decided to implement a simple (but not a completely *toy*) iterator,
that would be doing something useful, to see how does `poll_next` and `async fn next` rank in terms
of ergonomics and performance. I'll describe my experience in this post. The code is available
in [this repository](https://github.com/kobzol/async-iterator-examples).

# Use-case description
I'll implement a very simple async iterator. It will read data delimited by newlines from an async
(tokio) TCP socket, and parse each line as a JSON message using `serde_json`. While simple, it does
use nested `async` calls (for reading from the socket), isn't completely trivial and represents an
actually useful use-case. I won't go through the implementations step-by-step, as this was meant as
a quick post.

> Disclaimer: I implemented these versions in ~30 minutes total and tested them in only a very basic
> way. It's possible that they contain serious errors :) I also haven't examined their properties
> w.r.t. cancellation safety and other aspects. So take them with a grain of salt.

# The `poll_next` approach
As a reminder, this is how the `poll_next`-based `AsyncIterator` looks like:
```rust
trait AsyncIterator {
    type Item;
    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<Option<Self::Item>>;
}
```

A sight for sore eyes indeed :laughing: Here is how I have implemented the aforementioned iterator
logic using this interface. Keep in mind that I'm no expert in terms of how pinning works and I almost
exclusively use `async fns` when using async Rust, so it's quite possible that this code is terrible
and can be written in a better way.

```rust
// Structure used for implementing the iterator
pin_project! {
    struct MessageReaderPollNext {
        #[pin]
        stream: TcpStream,
        #[pin]
        buffer: [u8; 1024],
        // How much valid data is in `self.buffer`
        read_amount: usize
    }
}

impl AsyncIteratorPollNext for MessageReaderPollNext {
    type Item = Message;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)
            -> Poll<Option<Self::Item>> {
        let read_amount = self.read_amount;
        let mut this = self.project();

        loop {
            // Try to read from the socket
            let mut read_buf = ReadBuf::new(&mut this.buffer[read_amount..]);
            match this.stream.as_mut().poll_read(cx, &mut read_buf) {
                Poll::Ready(read) => read.unwrap(),
                Poll::Pending => {
                    return Poll::Pending;
                }
            };
            // If nothing was read, client has disconnected, end iteration
            let read = read_buf.filled().len();
            if read == 0 {
                return Poll::Ready(None);
            }
            *this.read_amount += read;
            // If we found a newline
            if let Some(newline_index) = this.buffer
                .iter()
                .position(|&c| c == b'\n') {
                let line = &this.buffer[..newline_index];
                // Parse a message out of it
                let msg: Message = serde_json::from_slice(&line).unwrap();
                // And remove the data (including the newline) from the buffer
                this.buffer.copy_within(newline_index + 1.., 0);
                *this.read_amount -= newline_index + 1;
                return Poll::Ready(Some(msg));
            }
        }
    }
}
```
So, how well did the implementation go? Well, approximately the same as implementing `Future::poll` manually
back in the day. So terrible, of course :laughing: I had to remember that something like
`pin-project-lite` exists, and I had to accept many hints from `rustc` before I could even compile the
code (the pinning error messages were quite good though!). I had a very "<I have no idea what I'm doing
meme>" feeling when I wrote this code. Just finding out which `poll_` function from `tokio::net::TcpStream`
should I call was an adventure. It's possible (even probable) that this could be implemented in a much
simpler/better way, but I expect that most Rust users that are not `Pin` experts would struggle with the
implementation in a similar way as I did.

Here is how iteration could look like:
```rust
// `client` is a `tokio::net::TcpStream`
let mut reader = MessageReaderPollNext {
    stream: client,
    buffer: [0; 1024],
    read_amount: 0,
};

// Pin the iterator
let mut iter = pin!(reader);
// Convert from `poll_next` a `Future`
while let Some(msg) = poll_fn(|cx| iter.as_mut().poll_next(cx)).await {
    // Handle `msg`
}
```

# Async generator
This version uses an async generator using the [`async_gen`](https://docs.rs/async-gen/latest/async_gen/)
crate. I was worrying that it would be too painful to combine this crate with the `poll_next` method,
but it turned out to be trivial to turn a generator into an iterator using the
[`AsyncIter`](https://docs.rs/async-gen/latest/async_gen/struct.AsyncIter.html) struct offered by
the crate. It took me a moment to realize that when I use a generator, I don't actually need to
implement a trait for some struct, but the state of the struct will be stored as local variables
inside the generator (d'uh). Here is how it looks like:
```rust
let iter = AsyncIter::from(async_gen::gen! {
    let mut buffer = [0; 1024];
    let mut read_amount = 0;
    loop {
        // No data? Then end iteration.
        let read = client.read(&mut buffer[read_amount..]).await.unwrap();
        if read == 0 {
            return;
        }
        read_amount += read;
        // Find newline, parse message out of the line.
        if let Some(newline_index) = buffer.iter().position(|&c| c == b'\n') {
            let line = &buffer[..newline_index];
            let msg: Message = serde_json::from_slice(&line).unwrap();
            buffer.copy_within(newline_index + 1.., 0);
            read_amount -= newline_index + 1;
            yield msg;
        }
    }
});
```
Iterating through this generator looks exactly the same as before with the `poll_next` method:
```rust
let mut iter = pin!(iter);
while let Some(msg) = poll_fn(|cx| iter.as_mut().poll_next(cx)).await {}
```

The `async_gen` crate is really awesome! I would love to use it in my own code. The main thing that's
missing for better support of that is the stabilization of the `AsyncIterator` trait :) (And eventually
also async generators, of course, which would make this crate obsolete).

# The `async fn next` approach
This implementation was quite straightforward, and I pretty much got it right on the first try. Since
I work with `async` functions often, it was pleasantly easy to implement an async iterator using the
same approach.

As a reminder, this is how the `async fn next`-based `AsyncIterator` looks like:
```rust
trait AsyncIteratorAsyncNext {
    type Item;
    async fn next(&mut self) -> Option<Self::Item>;
}
```

And this is how I ended up implementing the JSON line parsing iterator using it:
```rust
struct MessageReaderAsyncNext {
    stream: TcpStream,
    buffer: [u8; 1024],
    read_amount: usize,
}

impl AsyncIteratorAsyncNext for MessageReaderAsyncNext {
    type Item = Message;

    async fn next(&mut self) -> Option<Self::Item> {
        loop {
            let read = self.stream.read(&mut self.buffer[self.read_amount..])
                .await.unwrap();
            if read == 0 {
                return None;
            }
            self.read_amount += read;
            if let Some(newline_index) = self.buffer
                .iter()
                .position(|&c| c == b'\n') {
                let line = &self.buffer[..newline_index];
                let msg: Message = serde_json::from_slice(&line).unwrap();
                self.buffer.copy_within(newline_index + 1.., 0);
                self.read_amount -= newline_index + 1;
                return Some(msg);
            }
        }
    }
}
```

# So which approach did I like the most?
The `poll_next` version was (expectedly) quite painful to implement by hand. I definitely wouldn't
like to write such implementations manually in my programs. However, what I realized during this
experiment is that this wouldn't really be needed thanks to async generators, same as it's not needed
to implement the `Future` trait by hand in most cases, thanks to `async fn`!

I think that it is great that low-level interfaces like `poll` (or `poll_next`) exist, and that it
even is *possible* to implement such an interface as performantly as possible, which is often not the
case in other languages. I'm a big fan of zero-cost abstractions, and I think that they are a good fit
for Rust. In fact, I personally consider Rust's property of "great performance out of the box, but you
can get stellar performance if you really dive deep" to be one of the reasons why it became so successful.

But what about ergonomics? Wouldn't `async fn next` be simpler to implement? Well, it is definitely
simpler to implement than `poll_next`, that's for sure. But remember, we're not expecting to write
`poll_next` by hand! We will probably be writing most async iterators with `async` generators, same
as we write most futures with `async` fns.[^library]
**Crucially, note that the async generator version is ergonomically
even better than the trait with `async fn next`!** And that's even though it had to be implemented
using a third-party crate and doesn't have any language support or syntax sugar at the moment.

[^library]: Library authors will probably need to go for the more low-level
    interface, but in that case I think that `poll_next` makes more sense, as it gives them more control.

The point is that I would definitely prefer writing `async gen` blocks/functions, rather than
implementing an `AsyncIterator` trait (be it `async fn next` or `poll_next` version) explicitly. But
since for me, the "implementation ergonomics" was pretty much the only argument going for
`async fn next`, my opinion is that the `poll_next` approach is the right way forward, combined with
support for `async` generators, as this would give us both low-level control and high-level ergonomics.

Note that I'm ignoring a lot of other design elements of async iterators, like cancellation safety,
two state machines, pinning and other things mentioned in the blog post written by boats. But thankfully,
as I already said, I'm not a language designer :laughing: So based on my blissful ignorance, and my
very brief experience from this experiment, I make this bold claim:

Let's stabilize `poll_next` to provide a low-level building block for library authors, and then (ideally
as soon as possible) stabilize `async` generators, to also enable Rust application programmers to easily
author async iterators on top of the `poll_next` method.

# Performance
Originally, I actually mainly wanted to evaluate the performance of these approaches, but later I realized
that the ergonomics of the implementation was even more interesting to me. But to not ignore performance
completely, I benchmarked these three approaches using a very simple TCP/IP client (included in the
repo). All three had pretty much identical performance, running at ~320k requests/s on my AMD Zen 3
laptop. I haven't examined the assembly in detail, but if anyone wants to have a go at this, I'd be
very interested in what you could find :)

# Conclusion
Anyway, I wrote this post in a haste (it took ~1.5 hours to read boats' blog, implement the code and
write this post :laughing:), and it was just a fun experiment, so don't take it too seriously :)

If you have any comments or questions, please let me know on [Reddit](TODO).
