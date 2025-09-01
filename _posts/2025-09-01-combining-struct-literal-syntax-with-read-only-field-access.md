---
layout: "post"
title: "Combining struct literal syntax with read-only field access"
date: "2025-09-01 13:00:00 +0200"
categories: rust
#reddit_link: TODO
---

Recently, I found myself struggling with a small annoyance related to struct field visibility
and struct initialization in Rust. It's no rocket science, but I thought about it long enough that
I might as well turn it into a blog post.

In [HyperQueue](https://github.com/it4innovations/hyperqueue), we have a struct describing
parameters of a queue (for the purpose of this post, it doesn't really matter what a queue is),
which contains a bunch of fields. Something like this:

```rust
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct QueueParameters {
    pub manager: ManagerType,
    pub max_workers_per_alloc: u32,
    pub backlog: u32,
    pub timelimit: Duration,
    pub name: Option<String>,
    pub max_worker_count: Option<u32>,
    pub min_utilization: Option<f32>,
    pub additional_args: Vec<String>,
    // ... more fields
}
```

This struct is just (Plain Old) data, a bag of fields that can be (de)serialized, sent over the
network, etc. However, at some point in the program, I want to store these parameters in a way
that would prevent other parts of the codebase from modifying them. Of course, I could do that easily
by making its fields private, but that would prevent me from using the struct literal syntax for
creating values of this struct outside the module (and its children) that defines it.

In short, I want to be able to both:
- Initialize the struct using the struct literal syntax (`QueueParameters { manager: ..., backlog: ... }`)
  anywhere in the codebase, so that I can see which fields are initialized with what values (as we
  don't have named parameters in Rust).
- Make it impossible to modify the values of the struct fields (outside the module of the struct) after initialization.

It would be nice to have something like "init-only" fields, but as far as I know, Rust doesn't really
have anything like that today. So I had to use some workaround. A common approach to sort of emulate
named parameters in Rust is to use the builder pattern, but that seemed like overkill to me in this use-case,
and its syntax would be more verbose than the normal struct literal syntax anyway. I also didn't
want to complicate the matter with any kind of macro magic.

My original "solution" to avoid the field mutation was to introduce a separate struct that has the
same fields as `QueueParameters` (let's call it `ReadOnlyQueueParameters`),
just with the fields being private, so that they cannot be modified from the outside after initialization.
Because the fields were private, I also had to create a constructor function `ReadOnlyQueueParameters::new`,
which received values for all the fields. Of course, this meant that I couldn't use the nice struct
literal syntax anymore, which made the initialization quite awkward, as there are a lot of fields:

```rust
let params = ReadOnlyQueueParameters::new(
    ManagerType::Slurm,
    1,
    4,
    Duration::from_secs(3600),
    None,
    Some(10),
    None,
    ...
);
```

This code was bothering me for a long time, because everytime I had to add a new field to the
parameters, I would have to extend this `new` function with yet another parameter, and the call-sites
would become ever more confusing. This is how such a change would typically look as a diff:

```diff
...
-   None,
-   None
- )
...
+   None,
+   None,
+   None,
+ )
```

Yeah, not great.

## The solution

After a few years of working with the annoying read-only wrapper, I finally lost my patience with
it and decided to refactor it. I quickly realized that the behavior I want can be achieved in a
very straightforward and elegant way by not duplicating the fields, but simply storing the mutable
struct directly as a field inside a read-only struct. The read-only struct would then expose the
fields of the mutable struct in a read-only way:

```rust
struct ReadOnlyQueueParameters(QueueParameters);

impl ReadOnlyQueueParameters {
    pub fn new(params: QueueParameters) -> Self {
        Self(params)
    }

    pub fn backlog(&self) -> u32 {
        self.0.backlog
    }
}
```

With this approach, I can construct the parameters using the struct literal syntax:
```rust
let queue = ReadOnlyQueueParameters::new(QueueParameters {
    manager: ...,
    backlog: ...,
    ...
});
```

But at the same time, I cannot modify the fields from the outside after construction anymore.
I could even remove the accessor methods by implementing the
[`Deref`](https://doc.rust-lang.org/std/ops/trait.Deref.html) trait for the wrapper, but
here I decided to keep the code more explicit. 

This is, of course, yet another instance of the [newtype pattern](https://rust-unofficial.github.io/patterns/patterns/behavioural/newtype.html), which I use all the time, and even [teach](https://github.com/Kobzol/rust-course-fei) it to my students! And the solution is really quite trivial in hindsight. So it was a bit
embarrassing to me that it took me so long to realize that it can be used to solve this annoyance.
Although frankly, the main issue was to find the motivation to spend five minutes to refactor code
that was bothering me for years :)

> For these simple newtype wrappers, it would be nice to be able to simply implement the `From`
> trait, to go from the inner field to a value of the newtype. More about that [soon](https://github.com/rust-lang/rfcs/pull/3809).

## Conclusion

Anyway, that's all. The newtype pattern just keeps on giving! Do you have other useful use-cases for
it? Let me know on [Reddit]({{ page.reddit_link }}).
