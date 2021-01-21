---
layout: "post"
title: "Tools for technical presentations"
date: "2021-01-07 15:26:00 +0100"
categories: presentations elsie
---
Programmers sometimes need to make presentations about projects that they work on, their favourite
library or algorithms, or about a shiny new programming language. Slides for such
technically-oriented presentations will probably need to contain specific content, such as code
snippets with syntax highlighting, complex diagrams, step-by-step animations, math symbols and
equations, etc. Here are some examples of slides that I have created which demonstrate what kind of
presentations I'm talking about:

- [Rust](https://github.com/Kobzol/elsie-gallery/raw/main/rust/slides.pdf)
- [CPU microarchitecture effects](https://github.com/Kobzol/elsie-gallery/raw/main/cpu-arch/slides.pdf)

What software would you use to create slides for such a technical presentation? It may sound like a
simple task that should be handled by any decent tool for creating slides. Yet from my experience,
the available solutions (that I know of) are somewhat lacking for this use-case, in several
regards.

In this post, I'll describe what properties I would like to have in a "perfect" tool for creating
technically-focused slides and what things I like or dislike about the current available solutions.

In the [next post]({% post_url 2021-01-07-elsie-programmable-presentations %}), I'll try to make an
argument for taking a **different approach to creating slides**, by creating slides
programmatically using the [Elsie](https://spirali.github.io/elsie/)
framework.

> Please note that this whole post is focused on presentations and slides with technical/computer
> science content that are exportable to PDF. It might not apply to presentations/slides in
> general. Also, I am quite a perfectionist when it comes to creating slides. :sweat_smile:

## Requirements
Here is a list of properties that I'd like to have in a (hypothetical) ideal slide-making tool
designed for technical presentations.

- `Syntax highlighting` Pretty syntax highlighting with support for common programming and
  configuration languages is an absolute must. I use code snippets in my presentations very often,
  so I want them to look good, and I also want to experiment with them interactively. Capturing
  screenshots from an IDE or copying highlighted snippets manually from
  e.g. [carbon](https://carbon.now.sh) is something that I'd really like to avoid.
- `Fragments and animations` It should support revealing selected contents of a slide gradually and
  changing its properties (e.g. size/color/position of a piece of text or an image)
  in individual steps (sometimes called fragments). This should be integrated with code snippets,
  by allowing the user to e.g. reveal code line by line or to highlight a single line at a time.

  It should also allow the user to easily create step-by-step animations by
  translating/scaling/rotating shapes, text or images, so that this doesn't have to be performed
  manually in e.g. Inkscape. As an example, I want to be able to animate e.g. several moves of a
  chess game, or a packet traveling through a set of connected network devices.

  What I don't really need so much are continuous animations (e.g. `GIF` or a video), since I want
  the slides to be exportable to PDF.
- `Level of control` I want the tool to support both high-level and low-level control of slide
  creation. More specifically:
    - `Simple things should be simple…` It shouldn't be too difficult to just slap a piece of text
      on a slide and call it a day. In most cases, I don't care about specifying the exact location
      of some item on a slide, I just want it to be placed and aligned reasonably. I especially
      don't want to be forced to align things manually (using the mouse) over and over again.

      The tool should thus have a layout model which places and aligns content on a slide
      automatically, and it should also have the most common slide items built in.
    - `…and complex things should be possible`[^1] On the other hand, sometimes I do want to place
      items *exactly 30 pixels* from the left border, overlay several items on top of each other or
      create an arrow that will point from the *center* of an image to the *end of the third line*
      of a specific text box.

      The tool should thus offer low-level, pixel-perfect control of everything that resides on a
      slide and let the user build complex visuals when the situation requires it.
- `Math symbols and equations` I don't need to render equations or math symbols in presentations
  that often, but it's certainly a nice feature to have, especially if your slides are math-heavy.
- `Source control` The slides should be easily versionable using e.g. `git`. This allows the user
  to go back to previous versions of the slides, make modifications without the fear of losing data
  and to rebuild the slide deck from its source code at any time.
- `Export to PDF` PDF is (probably?) the best format for distributing presentations. This feature
  is supported quite well by most tools, so it shouldn't be a problem.

[^1]: Quoting [Alan Kay] and also [Larry Wall].

[Alan Kay]: https://en.wikiquote.org/wiki/Alan_Kay

[Larry Wall]: https://en.wikiquote.org/wiki/Larry_wall

The tool should also be free to use (or even better, it should be open-source).

Is it too much to ask? Maybe. :man_shrugging: In any case, I wasn't aware of any existing tool that
would fully satisfy these properties. Now I'll describe some tools that I have been using so far
and what I perceive as their strengths and weaknesses.

## Existing tools
There is obviously a myriad of tools for creating slides and presentations, but I'm mainly
interested in those that can be used for creating technical presentations that I have described
above. I'll enumerate solutions that I have personally used for creating slides for such
presentations.

Note that the list of strengths and weakness is quite opinionated and biased :)
It is also possible that I have missed some popular alternatives, so if you know of any other
software tools for creating (technically-oriented) slides, please let me know on [Reddit](https://www.reddit.com/r/Python/comments/l1ypzt/elsie_python_library_for_creating_slides/)!

### PowerPoint-like tools
I'm putting tools such as PowerPoint, Google Slides, Impress, Prezi,… into a single category,
because they all represent the (probably most common) slide creation archetype, which uses a
WYSIWYG editor for creating slides. These tools are fine if you need to make a bunch of very simple
slides quickly, but using them gets pretty annoying if you need anything more complex.

*[WYSIWYG]: What You See Is What You Get: software where you edit content in its visual form.

My biggest gripe with these tools is that using them is a very manual and laborous process, because
you mostly need to place and align items on a slide manually using the mouse. Sure, you get the
occasional "grid-snapping" functionality to help you, but that is a small band-aid and sometimes it
can become pretty annoying if it doesn't snap in the way you want.

Furthermore, if you want to experiment with some property/detail that occurs on multiple slides
(for example: change the font or size of all text), you often need to go through all the slides to
modify them one by one, which is exhausting.

- `Syntax highlighting` :thumbsdown: Support for code snippets is pretty weak. You basically have
  to resort to importing code as an image which has been highlighted by another tool (an
  IDE, `carbon.sh`, `pygments`, etc.). It's not that bad if you do it once. But after you are
  editing the same code snippet on a slide for the twentieth time, or you decide that you want to
  change the highlight theme of all the code snippets in your presentation, it quickly becomes
  annoying.
- `Fragments and animations` :thumbsdown: You can reveal parts of your slide, for example items of
  a list or parts of a paragraph, but the options are somewhat discrete and limited. I haven't
  found a simple way in PowerPoint to e.g. show some text, then hide it, then show some other text
  at the same time as an image and then show the original text again. It may sound like a
  convoluted example, but I want to display similar visuals in my slides fairly often, and these
  kinds of tools don't allow me to express them easily.

  PowerPoint can actually create pretty nice continous/moving animations, but that is not very
  useful when you want to export to PDF.
- `High-level control` :thumbsup: PowerPoint has a lot of features to create lists, tables, charts,
  and it also has advanced formatting, editing and spellchecking features, so you get a lot of
  things built-in. Yet placement and alignment is not automated as well as I would like.
- `Low-level control` :thumbsdown: While you can place things pretty much where you want, you need
  to do it manually ba hand, and creating complex animated diagrams is very time-consuming.
- `Math symbols and equations` :man_shrugging: PowerPoint has support for rendering equations, but
  it's a bit cumbersome and not really on the level of TeX.
- `Source control` :thumbsdown: Not really possible using `git`. These tools support various forms
  of history, but it's very crude compared to proper source control.

### Beamer
[(La)TeX](https://www.latex-project.org/) is a typesetting system popular within the scientific
community, which uses a declarative language to typeset and render documents. There is a LaTeX
template named [Beamer](https://www.overleaf.com/learn/latex/beamer), which is designed for
creating presentations[^2].

- `Syntax highlighting` :thumbsup: Code highlighting in Beamer is pretty good, thanks to
  the [minted](https://www.overleaf.com/learn/latex/Code_Highlighting_with_minted) package. It
  supports theming, line numbers and overall it is pretty solid.
- `Fragments and animations` :man_shrugging: Beamer has support for basic fragments and revealing,
  but it's not so easy to support more advanced use-cases. You can create complex animations using
  the very powerful [TikZ](https://www.overleaf.com/learn/latex/TikZ_package)
  package, but it has (at least in my opinion) a pretty steep learning curve, and it can get
  somewhat verbose because of it declarative nature. For me, this is probably the biggest annoyance
  of Beamer (followed by its very unhelpful error messages :) ).
- `High-level control` :thumbsup: LaTeX has pretty good support for lists, tables, etc. While a
  declarative solution will probably never match the simplicity of WYSIWYG editing for creating
  really simple items, I don't feel that Beamer is too verbose even for basic slides.
- `Low-level control` :thumbsup: LaTeX allows you to place things with a low of control, so in this
  regard it gives you a lot of flexibility. Complex visuals are possible to do with TikZ, but
  again, it often feels a bit too complicated to me.
- `Math symbols and equations` :thumbsup: LaTeX obviously shines here, since it was designed
  exactly for this use-case. You probably won't find a better tool if you need to render a lot of
  equations, math symbols, proofs, etc.
- `Source control` :thumbsup: It is easy to version LaTeX, since it's just text-based source code.

LaTeX is notable for producing fine-looking text and has very good typesetting. If you can make
sense of LaTeX errors, you don't mind its syntax and you can speak `TikZ`, I think that Beamer is
actually a pretty good choice.

[^2]: It is often used for technical presentations especially in academic environments.

### [Reveal.js](https://revealjs.com)
This is a great tool for making HTML presentations. Its presentations look nice, they can work in
both interactive (in a browser) or presentation
(exported to PDF) modes and its familiar HTML/CSS syntax is more approachable than (sometimes quite
ugly) LaTeX code. However, it shares some disadvantages of LaTeX/Beamer, which stems from the fact
that it is also declarative.

- `Syntax highlighting` :thumbsup: Code highlighting is quite good. It also supports theming and
  line numbers, and it even has support for highlighting parts of the source code gradually out of
  the box.
- `Fragments and animations` :man_shrugging: Again, this is a point of contention for me. The tool
  supports basic [fragments](https://revealjs.com/fragments/) and also some advanced scenarios, but
  you cannot really express complex animations or build complex diagrams easily using HTML. You can
  actually use JavaScript to create these things, but it's not integrated, the library does not
  offer you API to make it easier, so it's pretty cumbersome.
- `High-level control` :thumbsup: Reveal.js uses HTML and CSS, so it allows you to build a lot of
  UI elements very simply, and you can use a myriad of layout models (e.g. flexbox) to lay them out
  on the slide.
- `Low-level control` :thumbsup: Using CSS, you can achieve pixel-perfect placement. Yet creating
  complex visuals (without the use of JavaScript) is only possible to a certain extent.
- `Math symbols and equations` :thumbsup: The tool supports [MathJax](https://www.mathjax.org/)
  , which is basically LaTeX rendered in the browser. Support for rendering math is thus quite
  good.
- `Source control` :thumbsup: Again, the source is just text, so it is easy to put it under source
  control. Reveal.js presentations are distributed as directories with quite a few files, but it's
  not really a big problem for `git`.

### Markdown-based tools
There are also quite a few tools that can render Markdown into a set of slides (for
example [Marp](https://marp.app/)). Markdown is a great tool for creating nicely-looking content
quickly, and if it matches your use-case, you should definitely use it. However, I cannot imagine
creating complex visuals, diagrams or animations using Markdown syntax, since it is highly
declarative and also quite limited in what it can do (which is actually its goal and a benefit in
many situations).

Therefore, I consider Markdown-based solutions to have very similar properties to `reveal.js`, just
with a different markup language (HTML vs Markdown).

## Conclusion
In general, these tools can be divided into two categories - tools with WYSIWYG editing (such as
PowerPoint) and tools with declarative source code (such as Beamer or `reveal.js`).

- *WYSIWYG editing tools* require a lot of manual labor to create beautiful slides, which usually
  leads to one of two things - you either spend way too much time making your slides look pretty,
  or you gloss over it to save time and then end up with mediocre slides.

- *Declarative tools* are quite useful for creating technical slides and can get you quickly to 90%
  of the desired result. As you might have noticed from the list above, I basically like the
  existing declarative tools, and I have used them many times for creating presentations. However,
  too often achieving the final 10% of the desired result gets exponentially harder to achieve
  using declarative tools.

So, this is the end of my rant :) In the [next post]({% post_url
2021-01-07-elsie-programmable-presentations %}), I'll show you that slides can also be created
differently, by taking the useful features of existing declarative tools and combining them with
the power of an imperative programming language.
