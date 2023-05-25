---
layout: "post"
title: "Elsie: programmable presentations"
date: "2021-01-07 15:30:00 +0100"
categories: presentations elsie
---
In the [last post]({% post_url 2021-01-07-tools-for-technical-presentations %}), I have written
about existing tools for creating technically-oriented slides and what I dislike about them. TLDR
version:

- WYSIWYG tools (e.g. PowerPoint) require a lot of manual and repetitive work, don't support syntax
  highlighting very well, don't provide proper tools to precisely draw complex visuals and
  animations, and they can't be easily put under source control.
- Declarative tools (e.g. Beamer or reveal.js) are much better, as they have solid support for
  syntax highlighting, they can draw complex visuals and animations (especially Beamer) and they
  and are easily versionable. However, neither of their declarative languages (LaTeX nor HTML)
  provides me with the level of flexibility that I ultimately want for creating complex slides.

*[WYSIWYG]: What You See Is What You Get: software where you edit content in its visual form.

What I'd like to have is a tool that gives me ultimate control of everything on a slide when I need
it, but at the same time provides reasonable defaults for creating simple things for which I don't
need fine-grained control.

Now if only there was a way to tell the computer to do exactly what I want, with the option to
abstract common scenarios into concise commands to avoid verbosity when performing simple tasks?
:thinking: Well, I'm a programmer, and this sure sounds a lot like programming! So why not simply
write a program that will generate the slides for me?

## Programmable slides
You could argue that the declarative tools that I have talked about (Beamer and reveal.js) are
already "sort of" programmable. I don't want to get into an argument whether LaTeX and HTML are
*programming* languages, but for me, there is still quite a large gap between a declarative
language like HTML and an imperative language like, say, Python.

Imagine for a moment that instead of clicking on text boxes in PowerPoint or writing LaTeX/HTML
markup, you would create slides by writing a computer program in an imperative programming
language, ideally using some slide API/library to make your job easier.

It might sound a bit silly at first, but if you think about it, programmers already create programs
that present data to users all the time (think of websites, mobile/desktop apps, etc.). So why
don't we also use programming languages to create slides for presentations?

### Existing tools for programming slides
Now, there are certainly people who thought of this concept before. There is a Python library
called [python-pptx](https://python-pptx.readthedocs.io/en/latest/), which is basically an API for
building PowerPoint presentations. While that's truly great if you like PowerPoint (or if you are
forced to use it), it doesn't solve its
[many issues]({% post_url 2021-01-07-tools-for-technical-presentations %}#powerpoint-like-tools).
Creating complex animations and visuals, having pretty syntax highlighted source code snippets or
rendering math symbols and equations with LaTeX-level quality will still be difficult, even if you
use this library. It is however a step in the right direction and if it wasn't PowerPoint-specific,
and it contained some high-level functionality (such as a layout model or built-in support for
syntax highlighting), I think that it could support most of my use cases.

There is also an API for creating
[Google Slides](https://developers.google.com/slides/reference/rest). Similar limitations as for
PowerPoint apply here, and the slides must be created using a JSON object, which is… less than
ideal for anything complex.

I couldn't find any other tools for creating slides programmatically (other than some other
libraries for creating PowerPoint slides). If you know of any other such tools, please let me know
on [Reddit](https://www.reddit.com/r/Python/comments/l1ypzt/elsie_python_library_for_creating_slides/)!

## Elsie
A few years ago, [one](https://github.com/spirali) of my colleagues was frustrated of having to
deal with the
[existing solutions]({% post_url 2021-01-07-tools-for-technical-presentations %}#existing-tools)
for creating slides with a lot of technical content (code snippets, complex diagrams and
animations, math symbols etc.). She decided to solve this problem by
creating [`Elsie`](https://spirali.github.io/elsie/), a Python library which allows the user to
**create slides programmatically**. It provides basic building blocks (such as text blocks, images,
code snippets, shapes, lists, etc.) that can be combined to create slides. Internally, it
transforms these building blocks to SVG and then renders the SVG slides to PDF.

We have been using it internally for several years, and we find it so useful that lately we have
decided to write a proper documentation for it and share it with others. I won't be explaining
*Elsie* in detail in this post, but just to give you an idea of how it looks, here is a simple
hello world example:

```python
import elsie

# Create a new presentation
slides = elsie.SlideDeck()

# Create a new slide
slide = slides.new_slide()
# Draw some text on the slide
slide.text("Hello world!")

# Render the slides to PDF
slides.render("slides.pdf")
```

You import the library, create some slides and then render them to a PDF file. There is no DSL or
anything like that, it's all just Python. You call functions, use variables, conditions, loops,
etc. to build your slides.

*Elsie* has a lot of useful features, such
as [syntax highlighting](https://spirali.github.io/elsie/userguide/syntax_highlighting/), a
[layout model](https://spirali.github.io/elsie/userguide/layout/), or a
powerful [revealing](https://spirali.github.io/elsie/userguide/revealing/) system. It can also
render [LaTeX](https://spirali.github.io/elsie/userguide/latex/)
or [Markdown](https://spirali.github.io/elsie/userguide/markdown/) and you can use it to create
your slides interactively in [Jupyter](https://spirali.github.io/elsie/userguide/jupyter/). You can
find a guide how to install and use *Elsie* in
its [documentation](https://spirali.github.io/elsie/).

However, for me, the ultimate feature of *Elsie* is simply the fact that it makes slide creation
*programmable*. This is a big paradigm shift that has changed the way I approach creating slides,
as it lets me do things that simply wouldn't be possible (or would be much more difficult) in
other (WYSIWYG or declarative) tools.

I'll now try to present some use-cases to demonstrate why it might be a good idea to create slides
programmatically. I will be showing some Python code snippets using *Elsie*, but they will mostly
serve as pseudocode to demonstrate why slide programmability can be useful. Therefore, if you know
basics of Python, you should be fine even if you don't know the *Elsie* API.

To be clear, I'm not claiming that the following use-cases are impossible in declarative or WYSIWYG
tools. Just try to think about how difficult it would be to achieve them in your favourite slide
making tool.

## Avoiding repetitive tasks
Programming is incredibly useful for making repetitive tasks easier, and this also applies to
making presentations. Here are some examples of situations where programmability can help avoid
doing tasks manually or e.g. copy-pasting things all over your presentation.

### Changing style quickly
Say that you want to quickly change the font (or its size, color, etc.) of all the text boxes in
your presentation, to see what style looks best. Or you might want to change the style of a
specific category of text boxes (e.g. all footnotes or headings). Or worse, right before your
presentation, you realize that the projector's aspect ratio (`4:3`/`16:9`) or the room's lightning
conditions (light/dark) do not match your slides, and you have to change the style ASAP.

Declarative tools can handle these changes relatively easily. WYSIWYG editors too, to a certain
extent, but it requires a lot of discipline by the user to e.g. use shared styles (if the tool
supports them). If you are not disciplined, you will need to resort to going through each slide one
by one and painfully changing the desired style by hand.

With programmable slides, the default font size, color theme, slide dimensions, etc. can simply be
variables, which are then used by the rest of the code that creates the slides. In that case, if
you need to change something, just modify the value of the variable (usually a single line change),
execute your program, and you will get a new version of your slides immediately.

```python
# A shared style is just a variable
color = "black"
...
slide1 = slides.new_slide(bg_color=color)
...
slideX = slides.new_slide(bg_color=color)
```

What if you want to change the font size of only selected (categories of) text boxes? Just create
more variables! For example, you can create a separate text style for each text box category, to be
able to change the style of all the texts with the same category easily.

```python
default = elsie.TextStyle(size=30)
# Changing this style will change the style of all footnotes
footnote = elsie.TextStyle(size=20, italic=True)
...
slide.text("Foo bar[^1]", style=default)
slide.text("1: This is a footnote", style=footnote)
```

TLDR: Variables can be useful for creating slides.

### Avoiding needless copy-paste
I often like to show an outline of my presentation (especially if it's long). However, if you only
show the outline at the beginning, the listener will probably forget its contents after the next
few slides. Therefore, I tend to show the outline repeatedly during the presentation and highlight
the next section that I will be presenting. Something like this:

{% include posts/elsie/outline.html %}

> You can use the buttons to change individual slides (called fragments here). Imagine that I want
> to show the outline, then some content, then the outline again, etc.

This means that I need to render the same slide (outline) several times, but each time with a
slight change (a different section will be highlighted). Now, if only there was a way to perform
one thing repeatedly with different parametrizations, but without copy-pasting it. In programming
languages, this is usually called *calling a function*. :slightly_smiling_face: I can just create a
function that will receive (an empty) slide and a name of the current section, and it will render
the outline on the slide and highlight the selected section. The implementation is not really
important, so I'll just show the function interface and its usage:

```python
def draw_outline(slide, active_section):
    # render outline on the given slide
    # highlight the active section
    ...


draw_outline(slides.new_slide(), "Section A")
draw_section_a(slides)
draw_outline(slides.new_slide(), "Section B")
draw_section_b(slides)
draw_outline(slides.new_slide(), "Section C")
...
```

This is of course a general concept, useful not only for outlines. Everytime you need to draw
something multiple times (perhaps in a slightly different way each time), you can just put it in a
function, parametrize it and call it in multiple slides.

You can also use loops to create e.g. grids or clusters of items on a slide with just a few lines
of code.

TLDR: Functions and loops can be useful for creating slides.

## Automating slide creation
If your slides are generated by a program, you can generate slides based on data from all sorts of
dynamic sources in an automated way, to (again) avoid painful manual work.

Once I was preparing slides for a training, and I wanted to show a slide with several IP addresses
of virtual machines to which the trainees could connect to. Running (cloud-based) virtual machines
can be quite expensive, so I wanted to boot the machines right before the presentation. However,
the IP addresses of the machines were dynamic, so I couldn't just hardcore them into the slides
e.g. the day before the training.

Because my slides were programmable, I created a function which used the API of the cloud provider
to download the IP addresses of currently running machines[^1]. My slide program could then use
this function to get the current IP addresses and draw them on a slide everytime the program was
executed. Then I just executed my program right before the training started and immediately got the
updated slides, without the need to copy the IP addresses to my presentation manually.

[^1]: Now that I think of it, the function could have also outright started the machines! :smile:

More generally, if you can generate slides by a program, you can use it to automate creating
work/performance/publication reports, charts etc. You can e.g. create a whole pipeline that will
run some experiment or benchmark, collect the results, postprocess them into charts and summaries
and directly render them into a nice presentation[^2].

[^2]: And then it can e-mail the PDF to your boss, so that you don't have to do *anything* anymore.

I think that tools like `python-pptx` were created mostly for this purpose. *Elsie* gives you both
automation and useful building blocks for technical presentations (the latter is mostly missing in
PowerPoint).

## Parametrizing slides
By automating slide creation, you can also easily create different versions of your presentation,
for different use-cases. When I was preparing the slides for my
[Meeting C++ talk](https://www.youtube.com/watch?v=ICKIMHCw--Y), I was a bit afraid that my live
demo (presented inside an IDE) wouldn't work for some reason. To stay on the safe side, I decided
to create two versions of my slides. One with additional screenshots of code that I prepared
beforehand (if there were problems with the demo) and another one without the screenshots (if the
demo worked fine).

Because my slides were built by a program, achieving this was fairly trivial. I simply created a
(boolean) variable that controlled which version should be rendered, and inserted the screenshots
into my slides only if the variable was set. My program then rendered two versions of the slides
into two PDF files, once with the flag set and once with the flag unset[^3].

[^3]: My demo has worked fine, but I'd be really glad to have the backup version if it didn't!

## Creating complex visuals and animations
For me, this is probably the biggest benefit of having an imperative language available for
creating slides. Image that you want to put some complex drawing, diagram or an animation into your
slides. Without specifying the context of the following animations[^4] (it's not really important
here), let's say that you want to draw something like this:

[^4]: Can you guess what do these animations demonstrate? :slightly_smiling_face:

{% include posts/elsie/branch-prediction.html %}

or this:

{% include posts/elsie/cpu-pipeline.html %}

These are the sorts of things that truly shine in a technical presentation and can often explain
some concept much better than a single static image. I can't really imagine how would I create
these animations in PowerPoint or reveal.js. They could probably be created in Beamer, but for me,
it's much easier to create them using Python rather than using TikZ.

> If creating such animations with a program is more exhausting for you than simply drawing
> them by hand, *Elsie* also lets you create such animations from manually drawn SVG or ORA images,
> using a [naming convention](https://spirali.github.io/elsie/userguide/images/#embedding-fragments-in-images).

## Conclusion
I hope that these examples have demonstrated to you that it might make sense to create slides
programmatically in certain scenarios. Of course, not even this solution is perfect. There are
use-cases (such as very simple slides), where using a DSL, a declarative language or a WYSIWYG
editor will probably always be quicker and easier than coding. And there is also the elephant in
the room, that you need to have some basic programming skills in order to leverage programmable
slides at all.

As for me, for most of my use-cases nowadays, I will first reach for programmable slides before
WYSIWYG editors or declarative tools. And since *Elsie* is the only practical tool that I know of
to make programmable slides with technical content, it is also my favourite slide making tool :)

So, if you know Python, but you're still creating slides manually, check
out [Elsie](https://spirali.github.io/elsie/) to level-up your slide-fu. And let me know what you
think about programmable presentations on [Reddit](https://www.reddit.com/r/Python/comments/l1ypzt/elsie_python_library_for_creating_slides/).
