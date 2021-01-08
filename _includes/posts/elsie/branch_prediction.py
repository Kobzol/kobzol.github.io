from elsie import SlideDeck, TextStyle as s
from elsie.boxtree.box import Box
from elsie.render import jupyter

COLOR_NOTE = "orange"


def branch_prediction(slides: SlideDeck):
    content = slides.new_slide()

    row = content.box(horizontal=True)
    box_dimension = 50

    def array(numbers, predictions, start=1, needle=6):
        stroke_width = 2
        size = 36
        for i in range(len(numbers)):
            box = row.box(width=box_dimension, height=box_dimension).rect(color="black",
                                                                          stroke_width=stroke_width)
            number = str(numbers[i])
            box.text(number, s(bold=True, size=size))

            predicted_correctly = (predictions[i] and numbers[i] < needle) or (
                    not predictions[i] and numbers[i] >= needle)
            prediction = "green" if predicted_correctly else "red"
            show_overlay = "{}+".format(start + i * 2 + 1)
            overlay = box.overlay(show=show_overlay).rect(color="black", bg_color=prediction,
                                                          stroke_width=stroke_width)
            overlay.text(number, s(color="white", bold=True, size=size))
            show_text = start + i * 2
            row.box(x=i * box_dimension, y=box_dimension, width=box_dimension,
                    show="{}-{}".format(show_text, show_text + 1)).text(
                "{} < {}?".format(number, needle))

    values = [6, 2, 1, 7, 4, 8, 3, 9]
    text_style = s(align="left", size=30)
    width = 400

    def predict_sequence(wrapper: Box, values, start=1):
        for i in range(len(values)):
            value = "Taken" if values[i] else "Not taken"
            show_start = start + i * 2
            wrapper.overlay(show="{}-{}".format(show_start, show_start + 1)).rect(
                bg_color="white").text("Prediction: {}".format(value), style=text_style)

    def predict_value(index):
        if index == 0:
            return False
        return values[index - 1] < 6

    predictions = [predict_value(i) for i in range(len(values))]

    array(values, predictions, start=2)
    prediction_wrapper = content.box(p_top=60, width=width).text("Prediction: Not taken",
                                                                 style=text_style)
    predict_sequence(prediction_wrapper, predictions, start=1)
    return content


slides = SlideDeck(width=500, height=200)
slides.update_style("code", s(size=32))
slides.set_style("bold", s(bold=True))
slides.set_style("notice", s(color=COLOR_NOTE, bold=True))
slide = branch_prediction(slides)
svgs = slides.render(return_units=True)
with open("branch-prediction.html", "w") as f:
    f.write(jupyter.render_slide_html(slide.slide, format = "png"))
