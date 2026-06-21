---
layout: "post"
title: "Optimizing #[sqlx::test] rebuild time"
date: "2026-06-21 18:00:00 +0200"
categories: rust
#reddit_link: TODO
---

> You might find this post especially useful if you have a project with many `#[sqlx::test]` tests.

One of the upstream Rust projects that I worked on during the past few years was the rewrite of [`bors`][bors],
the merge queue bot we use to merge all [`rust-lang/rust`][rust-lang/rust] PRs. If you are interested in learning more about this bot, check out my [talk][bors-talk] from RustWeek 2026.

I'm quite proud of the integration test suite of `bors`, which I spent a lot of effort on, and thanks
to which the bot has been working pretty much flawlessly since we deployed it to production in January 2026
(despite GitHub lately often having… troubles).

One thing that I'm not very happy about though is the incremental rebuild time of `bors`, and in particular its
test suite. It takes a long time (~8-10s) to rebuild the tests after each change on my laptop,
which is quite bad for productivity.

Recently I finally found some time to profile[^samply] its build time, and learned that it is caused by a
combination of several factors:
- Generation of debug information takes a long time. This is a [known issue]({% post_url 2025-05-20-disable-debuginfo-to-improve-rust-compile-times %}), but in
  this case I didn't want to give up debug info, because I actually debug and step through `bors` tests
  quite often.
- `rustc` takes a long time to load and persist the incremental session. I plan to take a look into this.
- Probably because of all the debuginfo (the final binary has like 220 MiB), it takes `lld` a whole second (!)
  to link the tests. With [`wild`][wild], it's just ~200ms.
- The `sqlx::test`s that I am using heavily in `bors` take a long time to compile. This is what I will focus on
  in this post.

[^samply]: Using just `samply record`, nothing fancy this time.

## Slow compilation of sqlx tests

As a frame of reference, for my benchmark I was using `touch <test-file> && time cargo test --no-run`.
Even after a no-op change, it took ~7.5 seconds to recompile the tests, which is super slow.

Of course, it is very well known that [`sqlx`][sqlx]'s proc macros can slow down compilation times,
because of all the ~~crimes~~ interesting things that they do[^sqlx-db]. However, the case that I encountered
might not be so obvious. In my case, `sqlx` did not actually even connect to a database! Because I'm compiling with `SQLX_OFFLINE=1`, unless I work directly on SQL queries. And *yes*, I am setting
`opt-level = 3` for the `sqlx-macros` crate, as [recommended][docs-opt-level] by the `sqlx` documentation.

[^sqlx-db]: Such as connecting to a running database *during compilation*. I always get blank stares when I explain this to people new to Rust when I do Rust trainings.

So what is happening here? To find out, it is important to understand what is happening when you
have a test like this:

```rust
#[sqlx::test]
async fn test_foo(pool: sqlx::PgPool) {}
```

The `#[sqlx::test]` attribute is super useful, because it creates a new database before the execution
of the test, runs migrations on it, and then gives you a database connection pool, so that you can
run your tests against an actual database, and not against a mocked HashMap[^testing].

[^testing]: I have a talk and a WIP blog post about similar situations… testing is fun (for some definition of "fun").

Wait, did I say migrations? Hmm, where does it find them? Well, from disk, of course! Each usage of
`#[sqlx::test]` will gather all migrations from a directory on disk, and then read, parse, validate
and hash each migration. Perhaps counter-intuitively, this part is not that slow! Turns
out that Rust is actually quite fast (who knew, right??), and if you do not have gigabytes of migrations, I/O is probably also not a problem[^windows].

[^windows]: At least if you're not on Windows and have an SSD.

*[SSD]: Solid-state drive

What is worse is the generated output of those macros. For each such test, the macro will generate a
complete list of migrations, including their text content and a checksum in the form of a byte array,
in the Rust source code as a constant. So if you expand the macro, before each test you'll find something
like this:

```rust
args.migrator(&::sqlx::migrate::Migrator {
   migrations: ::std::borrow::Cow::Borrowed(&[
      ::sqlx::migrate::Migration {
        version: 20240517094752i64,
        description: ::std::borrow::Cow::Borrowed("create build"),
        migration_type: ::sqlx::migrate::MigrationType::ReversibleUp,
        sql: ::std::borrow::Cow::Borrowed("CREATE TABLE <skipped>)"),
        no_tx: false,
        checksum: ::std::borrow::Cow::Borrowed(&[193u8, 202u8, <skipped>]),
      },
      ::sqlx::migrate::Migration {
        <skipped>
      },
      <skipped>
   ]),
   <skipped>
});
```

The example above is shortened, and it skips a lot of stuff. The actual generated code will be much longer, and of course it scales with the number (and content) of your migrations.

Now, if you have something like this in your source code once, that's not so bad. However, in `bors`, there are ~350 `sqlx` tests and 30 migrations. And at that point, it starts to add up rather quickly.

To test my hypothesis that migrations might be causing some of the build slowness, I tested what would happen
if I had only one migration by deleting the rest of them. And sure enough, the rebuild time immediately went from ~7.5s to ~5s! What is perhaps even more telling is that the size of the output of `cargo expand --lib --tests` went from 32 MiB (!) with 30 migrations to "only" 6 MiB with a single migration. Compiling an additional 26 MiB of Rust code sure isn't for free.

It wasn't just about the compilation time of the generated code though. In the profiles, it looked like converting all the migration description data to tokens using the `quote` crate during the proc macro execution also takes a non-trivial amount of time.

This behavior can be pretty inconspicious, because at the start of the project, the rebuilds were fast
(or at least, *faster*). But then, with each added test, and each added migration, the rebuild time
slowly increases, so it creeps up on you.

I tried if the experimental [proc macro caching](https://github.com/rust-lang/rust/pull/145354) feature that I landed in the compiler last year might help, but it didn't. Probably the time needed to compile the generated code dwarfs the time to run the proc macro itself, so it does not help if the proc macro itself is cached.

## What can be done about it

First, I started thinking about reducing the size of the generated code, e.g. by representing the checksum byte array in a more compact form. While this would likely help, I realized that as long as we generate code for all migrations next to each test, there will still be too much code.

Then I tried to patch `sqlx` to move the loading of the migrations to (test) runtime from compilation
time, to get rid of all the inlined migrations. This actually had the desired effect! The rebuild time went down to ~5s, and (at least in the case of `bors`), the `cargo expand` output was reduced to ~6 MiB, all while the execution time of the tests wasn't affected in a measurable way. The change wasn't even very complicated, all that's needed is to generate code that will call the function to load migrations at runtime, rather than calling that function in the proc macro and then embedding the description of all migrations in the generated source code.

So essentially, you go from this (pseudo-code):
```rust
fn sqlx_proc_macro() -> TokenStream {
  let migrations = generate_migrations();
  quote! {
    Migrator {
        migrations: #migrations
    }
  }
}
```

to this:

```rust
fn sqlx_proc_macro() -> TokenStream {
  quote! {
    Migrator {
        migrations: ::sqlx::generate_migrations()
    }
  }
}
```

However, loading the migrations at runtime might have some disadvantages, e.g. the tests would no
longer be self-contained.

I went to the [sqlx Discord][sqlx-discord] server and asked if people have any suggestions. My proposal was that `sqlx` could either load the migrations at runtime (which I described above), or that there could be a shared variable with the migrations that all the tests would reference, to avoid the generated code bloat. Funnily enough, one person responded and told me that the second solution is already implemented (well, sort of). You can actually specify a path to a variable containing the migrations to apply in `#[sqlx::test]`:

```rust
// The macro generates the migrations, we store it in a single variable.
const MIGRATOR: sqlx::migrate::Migrator = sqlx::migrate!();

// Each test just references the variable, instead of inlining all the
// migrations next to the test's source code.
#[sqlx::test(migrator = "crate::MIGRATOR")]
async fn test_1(pool: sqlx::PgPool) {}

#[sqlx::test(migrator = "crate::MIGRATOR")]
async fn test_2(pool: sqlx::PgPool) {}
```

> I wasn't sure if `const` or `static` would be better here, and I didn't measure any rebuild time differences. But `static` makes more sense to me, to ensure that the data exists just once in the final binary.

This solution worked great for `bors`! After [adding][bors-pr] the `migrator` argument to all `#[sqlx::test]` instances with a bit of `Find + Replace` magic, the rebuild time went down to ~5s.

While this works, what I don't like about it is the annoying `migrator = "crate::MIGRATOR"` attribute
that I have to remember to add to all my tests to avoid the migration code bloat problem. I think that
it would be quite elegant to specify a default value for the `migrator` argument in the `sqlx.toml` configuration
file added in the `0.9` release of `sqlx`, so that the shared variable would be used by default, without having
to think about it.

I opened an [issue][sqlx-issue] that proposes this feature. Let's see what do `sqlx` maintainers think,
although I would understand if they had some concerns about a feature like this.

In any case, even this manual solution was quite helpful, and it made my test rebuild times a bit faster.
There is still a lot of space for improvements, as 5s is still slow, though.

Maybe it would be useful to mention this "footgun" in the `#[sqlx::test]` [documentation](https://docs.rs/sqlx/latest/sqlx/attr.test.html). I suggested that [here][sqlx-pr].

## Conclusion

I think that this post offers two main takeaways:
- If you have a project with many `#[sqlx::test]` tests, and you suffer from long rebuild times,
  try to use the `migrator = "..."` trick to see if that helps.
- If you have proc macros that generate a lot of code, measuring the *byte size* of your code using `cargo expand` can be a relatively good predictor of compilation time :)

If you have further suggestions on how to optimize rebuild times when using `sqlx`, let me know on [Reddit]({{ page.reddit_link }}).

[bors]: https://github.com/rust-lang/bors
[bors-pr]: https://github.com/rust-lang/bors/pull/771
[bors-talk]: https://www.youtube.com/watch?v=NhTwLwznok8
[docs-opt-level]: https://github.com/transact-rs/sqlx#compile-time-verification
[rust-lang/rust]: https://github.com/rust-lang/rust
[sqlx]: https://github.com/transact-rs/sqlx
[sqlx-discord]: https://github.com/transact-rs/sqlx/blob/main/CONTRIBUTING.md
[sqlx-issue]: https://github.com/transact-rs/sqlx/issues/4318
[sqlx-pr]: https://github.com/transact-rs/sqlx/pull/4320
[wild]: https://github.com/wild-linker/wild
