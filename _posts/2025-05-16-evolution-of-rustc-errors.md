---
layout: "post"
title: "Evolution of Rust compiler errors"
date: "2025-05-16 13:00:00 +0200"
categories: rust rustc
#reddit_link: TODO
---

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/default.min.css">
<link rel="stylesheet" href="/assets/posts/rustc-error-evolution/style.css" />
<script type="text/javascript" src="/assets/posts/rustc-error-evolution/ansi_up.js" defer></script>
<script type="text/javascript" src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@latest/build/highlight.min.js" defer></script>
<script type="text/javascript" src="/assets/posts/rustc-error-evolution/script.js" defer></script>

I recently attended [RustWeek](https://rustweek.org/) (which was totally awesome) and the talks by Alex Crichton (on the history of Rust) and Pietro Albini (on the importance of error messages) inspired me to do a little archaeology into the way Rust compiler messages have evolved over time.

I wrote a script that downloaded all stable Rust releases all the way back to 1.0[^rustup], executed each stable version of the compiler on a set of small programs containing an error and gathered the compiler standard (error) output.

[^rustup]: This is actually possible to do just with `rustup` (at least on x64 Linux), even though some of the oldest releases actually predate rustup. How cool is that?

The widget below visualizes how the error messages evolved over time. You can use the select box to examine different Rust programs to see their error:

<select id="programs">
    <option value="moved_var">Moved variable</option>
    <option value="wrong_field">Wrong field</option>
    <option value="missing_impl">Missing implementation</option>
    <option value="swapped_args">Swapped arguments</option>
    <option value="wrong_type_arg">Wrong argument type</option>
    <option value="borrowck">Borrow check error</option>
    <option value="missing_where_bound">Missing where bound</option>
    <option value="unused_var">Unused variable</option>
</select>
<div id="error-widget"></div>

There are a couple of interesting things to note:

- First and foremost, the error messages are simply *great*. If you have used Rust previously, this probably isn't too surprising. Even Rust `1.0.0` contained pretty solid error reporting, and it got much better over time.
- Rust `1.2.0` introduced numerical [error codes](https://doc.rust-lang.org/error_codes/error-index.html).
- Rust `1.26.0` introduced colorful error messages. It sounds like a small change, but you can see what an improvement it makes! It also added the `rustc --explain <error-code>` hint.
- The error messages sometimes went a bit back and forth in different Rust versions, which is a bit funny. For example, the `error: aborting due to 2 previous errors` has switched to `...previous error(s)` in `1.19.0` and then back to `...2 previous errors` in `1.20.0`, which seems like an unintended change in `1.19.0`. Sometimes the difference is only in a single space, which is not even visible in the visualization above.
- The error spans are also continuously being improved between rustc versions. My favourite example is the `Wrong field` program change in `1.87.0`.

But I think that ultimately, the most interesting thing about this is the evolution process of these messages itself, which demonstrates that a lot of effort has to be put into the messages to make them *really good*. To someone, it might seem like these messages are somehow automatically derived from the compilation process, and we get them "for free", but that couldn't be further from the truth. It is the result of a continuous design, implementation, review and testing effort that has been performed by hundreds of individual contributors over the span of more than ten years. Thank you to everyone who has worked on the Rust compiler and contributed to these awesome error messages!

If you'd like to test this out on more programs than the ones I have shown here,
you can check out my script [here](https://github.com/Kobzol/rustc-error-evolution)[^interactive].

[^interactive]: For a moment I thought about making the widget interactive, so that you could write any Rust code and see the evolution of the compiler errors for it directly in the browser, but that would essentially mean that I would have to reimplement the [Rust Playground](https://play.rust-lang.org/) for almost a hundred different compiler versions, which seemed… too much for a blog post :)

If you have your own favourite example of a Rust compiler error message, share it with others on [Reddit]({{ page.reddit_link }})!
