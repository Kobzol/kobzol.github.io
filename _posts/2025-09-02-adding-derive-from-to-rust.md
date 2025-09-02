---
layout: "post"
title: "Adding #[derive(From)] to Rust"
date: "2025-09-02 13:00:00 +0200"
categories: rust
reddit_link: https://www.reddit.com/r/rust/comments/1n6kxgf/adding_derivefrom_to_rust
---

**TL;DR**: `#[derive(From)]` can be used in nightly now. See [here](#how-to-use-it) on how to use it.
You can follow [this tracking issue](https://github.com/rust-lang/rust/issues/144889) for more updates.

I use the newtype pattern in Rust [a lot]({% post_url 2025-09-01-combining-struct-literal-syntax-with-read-only-field-access %}),
and I would like to make certain use-cases around it (even) simpler to express. A typical thing to
do with newtypes is that you implement a bunch of standard traits for them, which will delegate
to the inner field. The easiest way of achieveing that is of course with a `#[derive(...)]`:

```rust
#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
struct WorkerId(u32);
```

However, this approach cannot be currently used with all "built-in" traits from the standard library.
One of those traits is the [`From`](https://doc.rust-lang.org/std/convert/trait.From.html) trait,
which is used to convert between values of two types. Even though sometimes it might not be a good idea
to implement `From` when using a newtype (more on that later), in other cases it's quite useful,
as it makes it easier to go from a value of the inner field to a value of the newtype (especially
in generic contexts). A manual implementation of the trait will usually look something like this:

```rust
impl From<u32> for WorkerId {
    fn from(value: u32) -> Self {
        Self(value)
    }
}
```

This code is trivial to implement, of course, and there's not much space for bugs here, but it's also
pure boilerplate, and especially if you have a lot of newtypes in your crate, it just seems wasteful,
as it's clear that the compiler should be able to generate this implementation easily.

In fact, writing this impl over and over again usually annoys me enough that I end up writing a
macro to generate newtypes, so that I don't have to copy this (and other similar) code all over the
place. But writing and using such macros has trade-offs (same as using third-party crates for
this, such as [derive_more](https://docs.rs/derive_more/latest/derive_more/derive.From.html)), and
I thought that rustc should just give me the option to `#[derive(From)]`.

## Writing an RFC

After running into this missing feature yet again, I realized that… I could just add it to Rust :laughing:
Making language changes can be daunting, but this specific change seemed quite simple, mostly because
the behavior of the feature seems *obvious*. And so I decided to
try it and write an [RFC](https://github.com/rust-lang/rfcs). To test the waters, I first
drafted a ["Pre-RFC"](https://internals.rust-lang.org/t/pre-rfc-derive-from-for-newtypes/22567) on
the [IRLO](https://internals.rust-lang.org/) forum. It received a relatively positive response,
even from a member of the Language team, which made me confident enough to turn it into an actual RFC,
which I did a few weeks [later](https://github.com/rust-lang/rfcs/pull/3809).

*[RFC]: Request For Comments

I have to say that I was quite pleasantly surprised by the positive response to my RFC. I'm used to
reading big controversial RFCs that generate hundreds of comments and many arguments, but here the
response was mostly "yep, this sounds like a good idea" (with a few exceptions that I will discuss later).
I even received a few suggestions on how this feature could be improved in a future RFC.

The PR [itself](https://github.com/rust-lang/rfcs/pull/3809) also received a lot of positive emojis!
At the time of writing of this blog post, it has over one hundred emoji reactions, which actually
makes it into the top ~60 most "liked" RFCs in the repository, even though it's very recent. Emojis
are of course not a good way to decide which RFCs should be accepted, but it is a signal that many people seem to share the same annoyance of lacking an easy way to derive `From` impls.

I think that one of the strengths of this RFC is that it is arguably not even a *new feature*, per se.
It is one of those things that "just" fill a gap in Rust; it allows combining two features that were working
separately before (the `From` trait and deriving standard library traits), but couldn't be used together.

One thing that was a bit unclear with the RFC though was determining which Rust team(s) should actually
be responsible for deciding its fate. The first decision process (FCP) was [started](https://github.com/rust-lang/rfcs/pull/3809#issuecomment-2917056764) for the Language team. Then it was [suggested](https://github.com/rust-lang/rfcs/pull/3809#issuecomment-2963675737) that it should actually be handled solely by the
Libs API team. And in the end we did a dual Language + Libs API [FCP](https://github.com/rust-lang/rfcs/pull/3809#issuecomment-2964594802). This is actually a recurrent problem in the
Rust Project (and I'm sure in many/most other organizational structures), where we are relatively
often unsure *who* should actually be responsible for deciding (or doing) something, which can sometimes block
progress.

Luckily, that didn't happen here, and I can happily announce that after a few minor road bumps,
the FCP has been finished, and my first ever Rust RFC was accepted :tada:.

*[FCP]: Final Comment Period

## Design of the feature

Now that I have spoiled the outcome of the RFC, I should probably talk about the actual design of
the feature. Even though it sounds simple, there are a few things to consider.

First, let's make it clear what is the goal of `#[derive(From)]`. When applied on an ADT, i.e. a struct
or an enum[^unions], it should generate an implementation of the `From` trait for it. Let's start
with structs -- when you apply `#[derive(From)]` to a struct, you should get a `From` impl for the
struct that creates it from a value of its field, like this:

```rust
#[derive(From)]
struct Foo(u32);

// generates:
impl From<u32> for Foo {
    fn from(value: u32) -> Self {
        Self(value)
    }
}
```

*[ADT]: Algebraic Data Type

[^unions]: I'm purposefully omitting `union`s here, as I mostly want to ignore those :laughing:

If you look at the example above, an obvious problem presents itself: what to do if there is not exactly
one field in the struct?

```rust
struct Foo(u32, bool);
```

There are three solutions that come to mind:
1. Generate a `From` impl from all the values at once, i.e. `From<(u32, bool)>`
2. Force the user to specify which field should be used for the `From` impl
3. Forbid using `#[derive(From)]` in this case

I think that option 1) would be quite unintuitive, and it would run into an issue for the most common
use-case where you have a single field - should we generate `From<FieldType>`, and thus break consistency
with other field counts, or `From<(FieldType,)>` (i.e. generate the struct from a tuple
of size one), which is quite unergonomic and uncommon? This approach also wouldn't really work for
structs with named fields.

I left option 2) as a future possibility. One of the suggestions that were proposed was that we could
annotate a single field with an attribute (e.g. `#[from]`), and then create the rest of the fields
using their `Default` impl:

```rust
#[derive(From)]
struct Foo(#[from] u32, bool);

impl From<u32> for Foo {
    fn from(value: u32) -> Self {
        Self(value, Default::default())
    }
}
```

I like this option a lot, and I think that we should explore it in the future. A similar
approach is also being used for selecting the default enum variant using the `#[default]` attribute
when deriving `Default`, so there is a precedent for doing something like this. However, since I wanted
to keep this RFC minimal in order to improve its chances of being accepted without falling into
deep "design holes", I didn't include it in the RFC and left it as a "future improvement".

And thus I chose to go with option 3), which means that you can currently only use `#[derive(From)]` on
structs that have exactly one field. I don't think that it's a big limitation though, because I expect
that in most cases this derive will be used for newtypes (which typically store exactly one field).
In general, the `From` trait is most commonly used for converting a single value of one type into a
single value of another type, so it makes sense to have this limitation in the initial design.

In terms of enums, the situation is more complicated. In theory, we could allow the macro to be used
on enums that have exactly one variant with exactly one field, but that doesn't sound like a very
useful scenario. For simplicity, I thus also decided to forbid using `#[derive(From)]` on enums,
at least for now.

Apart from this main design question, some concerns were expressed by several people on the RFC.

### Is the "direction" for the From impl the right one?

One noted concern was whether `#[derive(From)] struct Foo(u32);` should generate `From<u32> for Foo`,
`From<Foo> for u32`, or both. To me, the answer is obvious (it should be `From<u32> for Foo`),
because that is how all the other derive macros work; they always generate an impl for the type on
which the derive macro is applied. I think that this behavior is the most intuitive one, and we should
keep consistency with the previous `derive`able macros. This direction also makes the newtype use-case
work, and I consider that to be the most important driving use-case for this feature.

However, it is actually interesting to also consider how we could support the second direction, because
it can also be useful to go from a value of the struct back into the inner field, of course. I omitted
this functionality from my RFC, but one of the proposed solutions was to add something like `#[derive(Into)]`,
which would generate `From<StructType> for FieldType`. Of course, this naming could be quite confusing,
because we would not *actually* generate an impl of the `Into` trait, because that is generated
automatically by a [blanket impl](https://doc.rust-lang.org/src/core/convert/mod.rs.html#756) in the
standard library. But that is a discussion for another RFC.

### Are we closing the door on other solutions?

This is the usual worry with any (Rust) RFC that adds a new feature -- are we sure that we got the right
design for it, that it will be extensible in the future, and won't close doors to a better solution for
the same problem?

Since I kept my RFC minimal, this is a valid concern. Maybe we should first figure out how to support
the `From` impl in the other direction? Or flesh out the `#[from]` extensions? Some reviewers wanted
to see the "grand picture" of this feature before it will be stabilized (or even before the RFC would
get accepted).

I sympathize with those views, as I am myself also often worried about accepting a feature *too soon*,
when we don't know all the details yet. However, in this specific case, I am quite confident that the
feature that I proposed will be perfectly compatible with any relevant extension, and thus we should
land it as soon as possible, without waiting on the more complicated discussions about the possible
extensions, to achieve incremental progress.

My confidence comes from the fact that (at least to me), the behavior of `#[derive(From)]`
is simply *obvious*, and there is no other way how it could reasonably behave.
If `rustc` generated anything else than the following for `#[derive(From)] struct Foo(u32)`:

```rust
impl From<u32> for Foo {
    fn from(value: u32) -> Self {
        Self(value)
    }
}
```

Then I think that the feature would be wrong. It might have some other extensions or configuration
points, but this core functionality is in my opinion set in stone, and there is no other way how it
could work. And thus I wanted to get my minimalistic RFC out the door,
so that we can start testing the feature in the wild, and mainly so that it can start providing
value to Rust users.

It should be possible to lift the limitations (such as allowing it on structs with multiple fields
and implementing the `#[from]` attribute), or add related functionality (such as `#[derive(Into)]`)
to this feature in the future in a backwards-compatible way[^famous-last-words].

[^famous-last-words]: Famous last words…? :laughing:

### Is using `From` on newtypes even a good idea?

One additional, a more philosophical, concern discussed on my RFC was whether implementing
`From` for newtypes is even a good idea in the first place, and thus whether we should teach `rustc`
to do it.

There are two angles to this discussion. The first one is whether newtypes should implement the
`From` trait or not. To answer that question, I'll try to examine the various motivations
for using newtypes in a bit more detail.

> I stress motivations here so much because newtype is a *pattern*, and the motivation for using a pattern is one of the things that defines it. You can have two identical pieces of code, where one upholds a certain pattern, and the other doesn't, which can happen if those pieces of code were created because of a different motivation. That is why there are some patterns in [Gang of Four](https://en.wikipedia.org/wiki/Design_Patterns) that can have pretty much the same source code representation, but they still form different patterns because they have a different motivation.

The primary motivation for using a newtype, one that is upheld by *every* usage of a newtype, is to
create a new type in the type system (d'uh). This allows us distinguish between e.g. `WorkerId` and
`TaskId`, so that it is harder to accidentally combine values of different domain types, even if they
are backed by the same "in-memory" data type (e.g. an integer). I'll call this the "avoid type confusion"
motivation.

Another very common motivation (which is a subset of the first motivation!) is to ensure that values
of the newtype will uphold some invariant, which is not necessarily true for all values of the type
inside the newtype. A typical example is something like `struct Email(String)`. An `Email` is backed
by a `String`, but not all values of strings are valid e-mails! I'll call this the "ensure invariants"
motivation.

For avoiding type confusion, it is perfectly valid to implement the `From` trait for the newtype, as it
gives you a standardized way of initializing the newtype from the wrapped value.

For ensuring invariants, implementing `From` is of course not the right thing to do! `From` should
always be infallible, and should be able to convert *all* values of a type into some value of another
type. But in the case of e.g. `Email`, that of course won't work. It might make sense to implement
`TryFrom` in this case, but that is not something that we can easily `derive` anyway.

It seemed to me that people who expressed concerns about whether we should make implementing
`From` easier were mostly using newtypes to ensure invariants. In that case I can understand why
they think that implementing `From` is a bad idea! However, I personally use newtypes more often
for avoiding type confusion (my estimate is that the ratio between the two use-cases in my code is
something like 75:25 in favour of avoiding type confusion). So for most of my newtype use-cases,
implementing `From` is genuinely useful (which is why I wanted to add this feature to Rust in the
first place :) ).

The second angle to this discussion is more general and unrelated to newtypes.
I personally think that Rust should not dictate what is and what isn't "good program design",
of course as long as makes sure that it is *sound* (in the sense of memory/data race/etc. safety).
Obviously, Rust already makes some strong decisions about program design, for example it does not
allow you to use inheritance, and the borrow checker also makes
expressing certain ownership patterns (like the famous "soup of pointers") annoying. But in this specific case,
you can already implement `From` by hand, so forbidding users from deriving this trait, even
though it is technically possible, just to make sure that they don't do something that might be considered
bad practice, would seem to be a bit silly to me.

## Implementing the feature in rustc

Normally, after an RFC is accepted, we have to wait until *someone* actually implements it (which is
not a given, we shouldn't forget that!). But luckily, since I'm a [compiler contributor](https://www.rust-lang.org/governance/teams/compiler), I was able to help myself here :sweat_smile: And after some trial and error, I
managed to [implement](https://github.com/rust-lang/rust/pull/144922) the feature. It was a pretty
fun exercise, because the `From` trait is different enough from all the previous traits that
were `derive`able, so I also had to make some small changes to the `derive` infrastructure to make it work.
It was also a chance to work with [Nick Nethercote](http://github.com/nnethercote) again, which is always awesome.
He even made some [improvements](https://github.com/rust-lang/rust/pull/145550) to the feature
after my initial PR was merged. Thanks Nick!

While implementing this feature, I understood how the derive macros are actually wired between
the compiler and the standard library, which is actually pretty interesting. The compiler [defines](https://github.com/rust-lang/rust/blob/62227334ae04429f4b1196c8f852d666ae56204b/compiler/rustc_builtin_macros/src/lib.rs#L128)
the traits that are deriveable, along with the actual logic to generate the derived code. However,
when I added a new `From` macro derive implementation to this list, `#[derive(From)]` still didn't work.

After digging and tracing of the compiler's behavior on small Rust programs, and asking the
[Foremost Rust Name Resolution Expert™](https://github.com/petrochenkov) for help, I finally realized
that the answer is *name resolution*. When the compiler sees something like `#[derive(Trait)]`, it uses
name resolution to understand what `Trait` is. One option is that the trait is resolved to a
(derive) proc macro, in which case rustc will call it[^derive-proc-macro-cache] to generate the expanded code.
However, another option is that it will resolve the trait to a macro in the standard library marked
with the `#[rustc_builtin_macro]` [attribute](https://github.com/rust-lang/rust/pull/144922/files#diff-7fdf8ef3b0e02b28e3caa4cc144046f9510df7c8a1f524124f4921601a3d7456R1779).
And that is the piece of magic that ties the name `From` to the code that actually generates the right
derive logic. So after I added this:

[^derive-proc-macro-cache]: And hopefully also [cache](https://github.com/rust-lang/rust/pull/145354) it one day…

```rust
#[rustc_builtin_macro]
#[unstable(feature = "derive_from", issue = "144889")]
pub macro From($item: item) {
    /* compiler built-in */
}
```

to the standard library, `#[derive(From)]` finally started working :tada:

However, name resolution (in Rust, but also in general) is a VERY gnarly beast, and my joy from defeating
it did not last long. The very next day after my PR was merged, someone created an [issue](https://github.com/rust-lang/rust/issues/145524) that my PR broke their code in nightly because of name resolution
errors. Exactly the thing you want to see when you wake up :laughing:

The issue was (as usually) with glob imports. To make `#[derive(From)]` work "out of the box", I added
the `From` macro to the standard library prelude, so that it can be implicitly resolved, and users
thus wouldn't have to import anything to use the new `derive`. This is what makes e.g. `#[derive(Hash)]`
work even if you don't have the `std::hash::Hash` trait imported.

However, adding new things to the prelude is always tricky. Consider this code:

```rust
mod foo {
    pub use derive_more::From;
}

use foo::*;

#[derive(From)] // ERROR: `From` is ambiguous
struct S(u32);
```

The code uses a glob import to import a macro named `From` from the `foo` module. After my PR landed,
this module also received another macro named `From` (the one from the standard library), which was
imported with a glob import from the std prelude, which caused an ambiguity. In other words, my change
broke existing (stable) code, even without people using the new feature. That is obviously Very Bad.

To [fix](https://github.com/rust-lang/rust/pull/145563) this, I had to remove the `From` macro
from the standard library prelude, and thus for now, it will have to be imported explicitly. I added
the macro to the `std::from` module; it had to be added to a *new* module, because no previously
stable Rust code could have had a previous import from a module that did not exist, and thus this
should not break anyone. It is a bit confusing though that the `From` macro is in `std::from`, while
the `From` trait is in [`std::convert`](https://doc.rust-lang.org/std/convert/trait.From.html).

To be honest, I don't know if there is a way to resolve the import ambiguity without an edition bump,
so maybe this feature will have to wait until the next edition before it can be used ergonomically.
Maybe [#139493](https://github.com/rust-lang/rust/pull/139493) might help with issues like this in the future.

It is interesting to note that if the code looked like this instead:

```rust
pub use derive_more::From;

#[derive(From)] // Uses `From` from `derive_more`
struct S(u32);
```

Then there would be no ambiguity, because the explicit import from `derive_more` would be prioritized
before the `From` glob import from the std prelude. But having two macros imported *both* with a
glob import (with one coming from the prelude) causes a problem.

## How to use it

To experiment with this feature, update to a recent nightly release of the compiler, and use `#[derive(From)]`
on a struct of your choice. Note that it will only work on structs with
exactly a single field, as mentioned before! You will also have to import the macro explicitly,
because of the ambiguity problem described above.

```rust
#![feature(derive_from)]

use std::from::From;

#[derive(From)]
struct Foo(u32);

fn main() {
    let f: Foo = 1u32.into();
}
```

You can try the feature and let me know if it works fine for you! Note that I don't expect that
many things could break here, provided that there won't be any further name resolution errors…

## Future improvements

As I already discussed above, there are various improvements and extensions that we could do with
`#[derive(From)]`. But even more generally, I think that we should make it possible to `derive`
as many standard library traits as possible. It should be easily possible to generate impls of
`AsRef`, `Deref` or even traits like `Iterator`, as long as you do it on structs with a single field.

If/once `#[derive(From)]` becomes stabilized, I might try to write RFCs to also support these other
traits, to reduce even more boilerplate.

## Conclusion

I hope you enjoyed my adventures with writing an RFC and designing and implementing a Rust feature!
You can let me know what you think about `#[derive(From)]`, and which other traits would you like to
`#[derive]`, on [Reddit]({{ page.reddit_link }}).
