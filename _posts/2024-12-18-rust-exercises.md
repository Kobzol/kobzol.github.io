---
layout: "post"
title: "Rust exercises from my university course"
date: "2024-12-18 20:00:00 +0100"
categories: teaching
---

I'm still recovering from the most [hectic semester]({% post_url 2024-11-12-phd-postmortem %}) of my life[^so-far],
so I wasn't yet able to push out the several blog posts that I have in the pipeline. So this is just
a short post in which I wanted to share a bunch of Rust exercises that I created during the first run
of a [Rust university course](https://edison.sso.vsb.cz/cz.vsb.edison.edu.study.prepare.web/SubjectVersion.faces?version=460-4157/01&subjectBlockAssignmentId=539402&studyFormId=1&studyPlanId=25878&locale=en&back=true) that I was teaching at my [university](https://www.vsb.cz/en) this semester.

[^so-far]: Most hectic semester [so far](https://www.youtube.com/watch?v=bfpPArfDTGw)…

You can find the exercises [here](https://github.com/Kobzol/rust-course-fei/tree/main/lessons). The repository also contains a link to a [YouTube playlist](https://www.youtube.com/playlist?list=PLgoUJJFtqE9C8Ar_JgDBHQYrG-hHMlVyU) containing recordings of my lessons, but they are in the Czech 🇨🇿 language, so they are mostly only useful to people from my country :)

Each exercise has a short description, sometimes a piece of bootstrap code, and also a set of unit tests that should test the correctness of the solution. Creating the exercises took an extreme amount of time, easily more than one hundred hours total. It takes some time to think of a good/interesting topic, write a reference implementation, write a set of unit tests, think about various approaches that students could use and add more tests e.g. to make sure that a naïve solution won't work, make sure to guide the students to avoid pitfalls, etc. But it's also a lot of fun :) …when you don't have to do it 10 weeks in a row on a just-in-time basis. Yeah, that part was *not* ideal.

One of the exercises, called [Memory map](https://github.com/Kobzol/rust-course-fei/blob/main/lessons/06/exercises/assignments/tests/04_memory_map.rs), was based on a real-world data structure that I implemented for a [cool project](https://marketplace.visualstudio.com/items?itemName=jakub-beranek.memviz) that I somehow squeezed into my very busy schedule this autumn. I'm planning to write a (hopefully interesting) blog post about it in the (near-ish) future, so stay tuned :)

Anyway, that's all I wanted to share. If you have any feedback regarding the exercises or want to suggest any improvements or fixes, feel free to open an [issue](https://github.com/Kobzol/rust-course-fei/issues/new) or send a PR on GitHub.
