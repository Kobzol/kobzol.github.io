---
layout: "post"
title: "Why doesn't Rust care more about compiler performance?"
date: "2025-05-29 13:00:00 +0200"
categories: rust
#reddit_link: https://www.reddit.com/r/programming/comments/1kg37vm/git_stash_driven_refactoring
---

One thing that I hear all the time about Rust 

- hear this question often
- disclaimer
- wg-perf member
- it's hard, low-hanging fruit has been picked, large refactorings needed
- lot of other things to do (perf. improvements vs miscompilation)
- we're not a company

## Conclusion

If you want to try the new flag on your projects, you can try to build them using
`cargo +nightly build -Zno-embed-metadata`. I would be interested in seeing the results, i.e. how
much disk space it was able to save. You can let me know about your results
on [Reddit]({{ page.reddit_link }}).
