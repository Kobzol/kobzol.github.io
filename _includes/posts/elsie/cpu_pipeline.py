from elsie import SlideDeck, TextStyle as s
from elsie.boxtree.box import Box
from elsie.render import jupyter


def cpu_pipeline(slides: SlideDeck):
    hash_size = 8

    def table(wrapper: Box, size, dimension, buckets=None, bucket_indices=True):
        htable = wrapper.box(horizontal=True)
        items = []
        for i in range(size):
            cell = htable.box(width=dimension, height=dimension, horizontal=True).rect("black",
                                                                                       stroke_width=2)
            items.append(cell)

        if buckets:
            bucket_width = int((size / buckets) * dimension)
            for i in range(buckets):
                pos = i * bucket_width
                htable.box(x=pos, y=0, width=bucket_width, height=dimension).rect("black",
                                                                                  stroke_width=4)
                if bucket_indices:
                    htable.box(x=pos, y=dimension, width=bucket_width).text(str(i))

        return (htable, items)

    address_colors = ["#B22222", "#007944", "#0018AE"]
    colors = ("#F0134D", "#FF6F5E", "#F0134D")

    slides.update_style("default", s(size=20))
    slides.set_style("tag", s(color=address_colors[0]))
    tag = slides.get_style("tag")
    slides.set_style("index", tag.compose(s(color=address_colors[1])))
    slides.set_style("offset", tag.compose(s(color=address_colors[2])))

    styles = ["tag", "index", "offset"]
    colors = ["#F0134D", "#FF6F5E", "#1F6650", "#40BFC1"]

    def address(cols, content, use_style=True, row=0, step=1, end=None):
        assert end is not None
        for i, col in enumerate(cols):
            show = f"{step + row}-{end}"

            style = "default"
            if use_style:
                if i == 0:
                    style = s(color=colors[row])
                else:
                    style = styles[i - 1]
            col.box(show=show).text(content[i], style=style)

    content = slides.new_slide()

    width = 400
    columns = 4
    row = content.box(horizontal=True)
    cols = [row.box(width=width // columns) for _ in range(columns)]

    address(cols, ("Number", "Tag", "Index", "Offset"), use_style=False, end=4)
    address(cols, ("A", "..100000", "000000", "000000"), end=4)
    address(cols, ("B", "..100000", "000000", "000100"), row=1, end=4)
    address(cols, ("C", "..100000", "000000", "001000"), row=2, end=4)
    address(cols, ("D", "..100000", "000000", "001100"), row=3, end=4)

    hash_dimension = 40
    (htable, hitems) = table(content.box(p_top=20), hash_size, hash_dimension, hash_size // 2)
    for i in range(4):
        hitems[0].box(show="{}-4".format(i + 1), width=hash_dimension // 4,
                      height=hash_dimension).rect(bg_color=colors[i])

    content = content.overlay()

    row = content.box(horizontal=True)
    cols = [row.box(width=width // columns) for _ in range(columns)]

    address(cols, ("Number", "Tag", "Index", "Offset"), use_style=False, step=5, end=8)
    address(cols, ("A", "..100000", "000000", "000000"), step=5, end=8)
    address(cols, ("B", "..100000", "000001", "000000"), row=1, step=5, end=8)
    address(cols, ("C", "..100000", "000010", "000000"), row=2, step=5, end=8)
    address(cols, ("D", "..100000", "000011", "000000"), row=3, step=5, end=8)

    (htable, hitems) = table(content.box(p_top=20), hash_size, hash_dimension, hash_size // 2)
    for i in range(4):
        hitems[i * 2].box(show="{}-8".format(5 + i), width=hash_dimension // 4,
                          height=hash_dimension, x=0).rect(bg_color=colors[i])

    content = content.overlay()

    row = content.box(horizontal=True)
    cols = [row.box(width=width // columns) for _ in range(columns)]

    address(cols, ("Number", "Tag", "Index", "Offset"), use_style=False, step=9, end=12)
    address(cols, ("A", "..100000", "000000", "000000"), step=9, end=12)
    address(cols, ("B", "..100001", "000000", "000000"), row=1, step=9, end=12)
    address(cols, ("C", "..100010", "000000", "000000"), row=2, step=9, end=12)
    address(cols, ("D", "..100011", "000000", "000000"), row=3, step=9, end=12)

    (htable, hitems) = table(content.box(p_top=20), hash_size, hash_dimension, hash_size // 2)
    for i in range(4):
        hitems[i % 2].box(show="{}+".format(9 + i), width=hash_dimension // 4,
                          height=hash_dimension, x=0).rect(bg_color=colors[i])
    return content


slides = SlideDeck(width=400, height=220)
slide = cpu_pipeline(slides)
with open("cpu-pipeline.html", "w") as f:
    f.write(jupyter.render_slide_html(slide.slide, format="png"))
