from elsie import SlideDeck, TextStyle as s
from elsie.render import jupyter


def outline(slides: SlideDeck):
    def make_outline(box, start, active_section):
        box = box.overlay(show=f"{start}")
        box.box(p_bottom=20).text("Outline")
        sections = ["A", "B", "C"]

        for section in sections:
            style = s(bold=True) if section == active_section else s()
            box.box().text(f"Section {section}", style=style)

    slide = slides.new_slide()
    make_outline(slide, 1, "A")
    slide.overlay(show="2").text("<section A>")
    make_outline(slide, 3, "B")
    slide.overlay(show="4").text("<section B>")
    make_outline(slide, 5, "C")
    return slide


slides = SlideDeck(width=400, height=220)
slide = outline(slides)
with open("outline.html", "w") as f:
    f.write(jupyter.render_slide_html(slide.slide, format = "png"))
