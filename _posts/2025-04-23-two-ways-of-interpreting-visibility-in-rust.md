---
layout: "post"
title: "Two ways of interpreting visibility in Rust"
date: "2025-04-23 13:00:00 +0200"
categories: rust
#reddit_link: TODO
---
Last year, while I was browsing through Rust compiler [pull requests](https://github.com/rust-lang/rust/pulls), I noticed [#126013](https://github.com/rust-lang/rust/pull/126013), which added the [`unreachable_pub`](https://doc.rust-lang.org/stable/nightly-rustc/rustc_lint/builtin/static.UNREACHABLE_PUB.html) lint to several crates of the compiler. This piqued my interest, because I did not know that lint at the time. But when I examined its description, I was quite surprised, become the lint made absolutely no sense to me! After I discussed this with the author of the PR[^nnethercote], I realized that the way I think about visibility in Rust is perhaps a bit strange, or at least different from the "way it was designed to be used".

[^nnethercote]: None other than the illustrious [Nicholas Nethercote](https://nnethercote.github.io/).

This topic seemed interesting enough to me to write this blog post, in which I'll briefly explain how visibility works in Rust, and describe two quite different ways of using it. If you know how Rust visibility works, you can skip ahead to the [main topic](#global-visibility). Note that this post is mostly a braindump of various thoughts on visibility, so don't expect any grand revelations :)

## Visibility in Rust
Each *item* in Rust (such as a function, struct, enum, etc.) has some *visibility*, which affects what other code is allowed to use that item. By default, it is *private*, which means that the item is only accessible within the module where it was defined, plus in any (grand)children modules. However, it cannot be accessed "higher" in the module hierarchy, in parent and sibling modules.

```rust
mod a {
  // Private struct
  struct Foo;

  mod c {
    // `Foo` is accessible here (e.g. through `super::Foo`)
  }
  // `Foo` is accessible here
}
mod b {
  // `Foo` is NOT accessible here
}
// `Foo` is NOT accessible here
```

You can override the default private visibility using the `pub` keyword, which can be optionally [extended](https://doc.rust-lang.org/reference/visibility-and-privacy.html?highlight=pub#pubin-path-pubcrate-pubsuper-and-pubself) with a path that limits the scope of the visibility, such as `pub(crate)` or `pub(in super::super)`.

Crucially, using `pub` actually does two separate things:
- It exports the item, so that in addition to the current and child modules, it can be also accessed from a set of **ancestor** modules[^pub-self]. However, in order for that item to actually be accessible through a use path, all modules in that path have to also be accessible: 
  ```rust
  mod a {
    mod b {
      mod c {
        // Make `Foo` accessible to `b` and `a`
        pub(in super::super) struct Foo;      
      }
  
      fn foo(_: c::Foo) {} // OK
  
      pub(super) use c::Foo;
    }
    // Error, `Foo` is not accessible through `c`, which is still private
    fn bar(_: b::c::Foo) {}
    
    // OK, `Foo` is accessible through the re-export from `b`
    fn baz(_: b::Foo) {}
  }
  ```
- It limits the scope in which the item can be further re-exported.
  This is only relevant when you use `pub` in combination with some path, because using `pub` alone enables the item to be re-exported arbitrarily, even outside the current crate. For example:

  ```rust
  mod a {
    mod b {
      pub(super) mod c {
        // Make `Foo` accessible to `b` and `a`
        pub(in super::super) struct Foo;
      }

      pub(super) use c::Foo; // OK, re-export to `a`, where `Foo` is accessible
    }

    fn foo(_: b::c::Foo) {} // OK

    pub(super) use b::c::Foo; // Error, `Foo` cannot be re-exported further
  }
  ```
  This feature is most commonly used through `pub(crate)`, to only allow an item to be used within the crate, but not re-exported further outside the crate.

[^pub-self]: With `pub(self)`, which is essentially the same as private visibility, that set will be empty, but that's usually not very useful.

It seems to me that these two different properties of visibility in Rust create a sort of tension, as they cannot be configured separately (I'll examine this further in this post). Now that we have a basic understanding of visibility in Rust, I'll discuss two different approaches to its usage that I have encountered. I will first very shortly describe both of them and then compare their trade-offs.

## Global visibility
I will start with what I suspect is the "default" way of using visibility in Rust. With this approach, you specify the "final" visibility that you *want* an item to have directly on that item. So if you want to export an item from its crate, you mark it with `pub`. If you only want to make it accessible within the crate, you mark it with `pub(crate)`.

I call this approach *global*, because conceptually, you make the decision where an item should be accessible globally across the whole crate (or even the whole crate graph) directly on that item. In other words, when you write `fn <Foo>`, you are (in theory) supposed to think about all the possible places where `Foo` will be accessible. Of course, if you have been paying attention earlier, you already know that it is not so simple; this will be discussed later below.

## Local visibility
The second approach is how I personally use visibility in Rust. I don't really use `pub(crate)`, `pub(super)` or `pub(in ...)`[^consistency], and only use `pub` as a *binary modifier* that decides whether an item is private or exported to its parent module. I essentially use `pub` as an `export` keyword. This is much closer to how visibility is handled in other mainstream languages, e.g. `export` in JavaScript/TypeScript, `public` in C#/Java or `static` in *C*[^c-static].

[^consistency]: Unless the codebase is already using these visibility modifiers, then I always try to stay consistent with the existing style, if possible.

[^c-static]: Of course, in *C* the default is the opposite: everything is public and the `static` keyword on non-local variables and functions makes it private to the translation unit. Also, *C* doesn't really have a module system. And there are linkage modes. And `static` does something else entirely for variables with automatic storage duration. But you get the point.

I call this approach *local*, because the item itself only determines its local visibility, i.e. if it is exported to its parent module or not. It is then the responsibility of its ancestor module(s) to decide how the item will be visible to the rest of the crate and whether it will be re-exported from the crate to the outside world.

Essentially what I'm trying to achieve is to use `pub(super)` for the "access" part of visibility and `pub` for the "re-export" part of visibility. In other words, allow the parent to access the item, and then let it (arbitrarily) decide how and where it wants to re-export it. But since you cannot really disentangle these two concepts in Rust (AFAIK), I just use `pub` to keep the code shorter.

Below you can see an example of using the local visibility approach:

```rust
mod service {
  mod scheduler {
    // Useful elsewhere, let the parent decide where to re-export/use it
    pub struct Scheduler;

    fn estimate_cost() {
      // use utility function provided by the parent module
      super::utils::calculate_graph_cost();
    }
  }

  // Only available in this module, not re-exported further
  mod utils {
    // Useful to the outside, let parent decide where to re-export/use it
    pub fn calculate_graph_cost() {}
  }

  // Re-exported up the hierarchy
  pub use scheduler::Scheduler;
}
```
Note how `calculate_graph_cost` is marked with `pub`, even though I definitely do not intend to export it outside the current crate, as it's just a utility function. Arguably, if I wanted to make 100% sure that items from the `utils` module won't ever be used up the module hierarchy, I could mark them with `pub(super)`, but I don't see a large benefit in that, as it would complicate my rather simple heuristic (`pub` - export to parent, no `pub` - private). It's up to the parent to decide whether to re-export these items elsewhere.

## Comparison
At first glance, these two approches might look almost identical[^laziness], and indeed, they can produce quite similar code. From my point of view, the important aspect is the way I think about assigning visibility to individual items, because it also affects how I structure code, and it has a few interesting effects and trade-offs that I'll try to describe below.

[^laziness]: Also, you might think that I'm just being too lazy to properly spell out the proper `pub(<path>)` modifiers, but I promise that there is a bit more to it, which I try to describe in the rest of the article.

Of course, it should be noted that there can be other approaches or patterns of using visibility in Rust, and it is also possible to combine multiple approaches. But for the sake of comparison, I will try to compare the trade-offs of these two specific approaches that I described above, and also describe how they can be combined with various code-structuring approaches that play well to their strengths.

### Simplicity
By "simplicity", I mean how difficult it is for me to figure out what should be the visibility of a given item. With the local visibility approach, an individual item only cares about the fact if it is private (usually because it needs to uphold some inner invariants or because it simply doesn't make sense to use it elsewhere) or if its functionality can be exposed to (any) other module. This makes the decision binary and quite simple, because I do not have to consider much else, which I like. This also plays well with keeping everything private by default, and then only making things `pub` on-demand (which I usually do with an IDE quick-fix) when I need to use it elsewhere in the crate.

With the global visibility approach, I feel like I am supposed to think about the (visibility) relation of items with respect to the whole crate. If I used `pub(crate)`, I would have to make a conscious decision for each non-private item (even one that is five nested modules deep)
whether it should be available outside the current crate or not. That doesn't make a lot of sense to me; it should not be the responsibility of that item to figure that out, its module ancestors should decide that.

Of course, in practice, people likely do not spend a lot of time thinking about the global visibility for each item that they implement, but I still consider making a binary decision to be the simpler approach.

### Composability
Another nice thing about local visibility is that it makes the individual visibility decisions composable. Each item decides whether it is exported or not, and its parent module then recursively applies the same local decision -- is the given item (or module) only useful locally, or should it be exported up the module hierarchy? The final visibility is then the result of composing all decisions of the item's ancestor modules.

The local aspect of this approach also means that I can move a set of modules to a different location within a crate, or even across crates, and their visibility modifiers should still remain valid in the context of the moved modules, regardless of other code in the crate.

Conversely, modifiers like `pub(crate)` (or `pub` when you interpret it as "being available outside the current crate") kind of "break through" the boundaries of parent modules, which feels weird to me. The compiler still applies a hierarchy when handling visibilities, so if the parent module of a `pub(crate)` item does not re-export it, then the effective visibility of that item is not `pub(crate)` after all, which I find misleading (although there are lints to detect this situation, which leads us to the next section).

### Lints
Above I showed that using `pub(crate)` or `pub` under the global visibility approach can be problematic if the parent modules do not properly re-export the given item. To detect these situations, you can leverage two lints:
- With the [`unreachable_pub`](https://doc.rust-lang.org/stable/nightly-rustc/rustc_lint/builtin/static.UNREACHABLE_PUB.html) (compiler) lint, you have a guarantee that each `pub` item will be in fact visible outside its crate.
- With the [`redundant_pub_crate`](https://rust-lang.github.io/rust-clippy/master/index.html#redundant_pub_crate) (Clippy) lint, you have a guarantee that each `pub(crate)` item will be in fact visible *across* the whole crate.

The existence of these lints suggests that "global visibility" is indeed the default approach for interpreting visibility in Rust. But it also shows that this approach has some gaps, as it needs lints to ensure that the visibilities stay consistent. 

With local visibility, the `unreachable_pub` lint doesn't really make sense, because even items that are only visible e.g. in their parent module or within the crate will be marked as `pub`. That is why the lint has confused me at first.

Lint support is in general a big disadvantage of the local visibility approach, because I haven't yet found tooling that could work with it. Notably, after some refactoring, it can happen that some items that are exported are no longer used anywhere outside their module, so their visibility could be "downgraded" to private. It would be nice if there was a lint that would detect such cases. I don't think that such lint [currently exists](https://github.com/rust-lang/rust-clippy/issues/3907#issuecomment-1879264618); perhaps it would require a global analysis that Clippy does not currently support (?), but maybe no one has just tried to implement it yet.

That being said, having `pub` on some extra items doesn't really concern me much, because if you use a particular style of designing your public interface, which I will describe later below, it should not be possible for these items to unexpectedly leak outside the crate (which would be concerning).

### Figuring out the external visibility
One argument that I heard against local visibility is that it doesn't allow us to immediately see the "external visibility" of an item. In other words, you cannot figure out if a given item is exported from a crate or not just by looking at its declaration, as you only see if the item is exported to its parent.

This is indeed a benefit of the global visibility approach, because with it you can look at an item in isolation and immediately see if it is accessible outside the current crate or not (although this only holds if you use the lints mentioned above, otherwise the visibility might be inaccurate!).

That being said, I personally do not often have the need to ask this question, but that's likely because I don't work on libraries that often. I think that this is a functionality that should be implemented by IDEs (such as RustRover or Rust Analyzer), which should tell you things like "is this item available outside the current crate?" when you hover on top of it.

### Designing the public interface of a crate
One of the most interesting aspects that go hand-in-hand with the used visibility approach is the method used to determine the public interface of a crate. There are likely many ways of designing that interface, but here I want to describe specific aspects of building public APIs that are related to the used visibility approach.

If you use global visibility, each item already decides if it should be exported from the current crate or not. You can thus get away with making your intermediate modules `pub` or using glob re-exports (`pub use foo::*;`), propagate the visibility of all nested items all the way to the crate root and then make even the root modules public:

```rust
pub mod foo {
  pub mod bar {
    pub struct A;
    struct B;
  }
}

// External crates can access foo::bar::A, but not foo::bar::B
```

The advantage of this approach is that if you have a lot of items that should be exported, you don't need to manually list them in the crate root in order to export them. This essentially means that you are "glob-reexporting" all modules and children that contain at least a single `pub` item from the crate.

This approach is convenient, but it also has some disadvantages. The items that you export in this way will be automatically available under the module structure used in your crate, so if you want to export them under different paths, you will need to use a different approach. Your public interface is also scattered throughout the whole crate, so you cannot easily see it at one place directly in the source code. To achieve that, you must reach for tools like [`cargo-public-api`](https://crates.io/crates/cargo-public-api) that can display your public interface by inspecting your crate. Same as with figuring out the external visibility of individual items, I think that this is something that should ideally be displayed by your IDE.

With local visibility, I usually use a similar approach, although I cannot also make the root modules `pub`, because then I could inadvertedly also export nested `pub` items that are not supposed to be exported. Instead, a more natural choice here is to export selected items that will form your public API individually, like this:

```rust
// src/lib.rs
// These modules are kept private, no "pub mod" here.
mod comm;
mod gateway;
mod program;

// Here I build the public API of the library,
// so that I have complete control over it.
pub use comm::Foo;
pub use gateway::Bar;
```

With this manual approach, I have complete control over the public interface. I can even build a "virtual" exported module structure that might not correspond to the module structure of my crate at all:

```rust
mod comm;
mod gateway;
mod program;

pub mod client {
  pub use program::Baz;

  pub mod api {
    pub use gateway::Bar;
  }
}
```

A nice benefit of this is that the whole external interface of your crate is visible at a single place, without the need of any additional tools.

Of course, the disadvantage is that if the API surface is large, the root of the library might also become quite large. In that case you might want to delegate the decision on whether to export something or not from the root module to some of the child modules, and then re-export everything from them.

## Conclusion
Anyway, that's all I got; as I wrote at the beginning, this post is an assorted set of thoughts that I wanted to write down, without some sort of grand conclusion :) Ultimately, the way you interpret visibility in Rust comes down to the style that you prefer. I personally prefer the local visibility style, as I find it simpler to think about. But maybe I simply don't work on use-cases that would be much easier to achieve with the other approach?

Which approach do you use? Do you know other approaches to interpreting visibility in Rust? If you have any comments, let me know on [Reddit]({{ page.reddit_link }}).
