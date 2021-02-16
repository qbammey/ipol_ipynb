import io
from pathlib import Path

import imageio
import ipywidgets as widgets
from PIL import Image


class IPOLLauncher:
    def __init__(self, launch_params, in_widgets):
        self.w_run = widgets.ToggleButton(value=False,
                                          description='run',
                                          icon='cog')
        launch_params['run_flag'] = self.w_run
        self.w_out = widgets.interactive_output(self._launch, launch_params)
        self.all_widgets = widgets.VBox(in_widgets + [self.w_run, self.w_out])

    def display(self):
        display(self.all_widgets)

    def register(self, **kwargs):
        """
        TBD.
        Calls IPOL backend and registers arbitrary kwargs
        (same as saving .npz files, the name of the parameter is the name to use.)
        """
        return

    def _launch(self, run_flag, *args, **kwargs):
        if not run_flag:
            return
        self.w_run.value = False
        self.launch(*args, **kwargs)

    def launch(self, *args, **kwargs):
        raise NotImplementedError

    def display_results(self, *args, **kwargs):
        raise NotImplementedError

    def run_code(self, *args, **kwargs):
        raise NotImplementedError


class ImageInput(widgets.VBox):
    def __init__(self,
                 description='Input image',
                 example_paths=None,
                 example_labels=None,
                 enable_upload=True,
                 enable_crop=True):
        assert example_paths is not None or enable_upload
        if example_paths is not None:
            example_paths = list(map(Path, example_paths))
            if example_labels is not None:
                assert len(example_paths) == len(example_labels)
            else:
                example_labels = [path.stem for path in example_paths]
        self.example_paths = example_paths
        self.example_labels = example_labels
        self.have_choice = example_paths is not None
        self.enable_upload = enable_upload
        self.enable_crop = enable_crop

        self.w_label = widgets.Label(value=description)

        if enable_upload:
            self.w_upload = widgets.FileUpload(accept='image/*',
                                               description='Upload an image')
        else:
            self.w_upload = None

        if example_paths is not None:
            self.ws_ex_images = [
                widgets.Image(width=150,
                              height=150,
                              value=open(path, 'rb').read())
                for path in example_paths
            ]
            self.t0 = self.ws_ex_images
            self.ws_ex_buttons = [
                widgets.Button(description=label, button_style='')
                for label in example_labels
            ]
            ws_stack_img_button = [
                widgets.VBox([i, b])
                for i, b in zip(self.ws_ex_images, self.ws_ex_buttons)
            ]
            self.w_img_choice = widgets.GridBox(
                ws_stack_img_button,
                layout=widgets.Layout(
                    grid_template_columns="repeat(5, 200px)"))
        else:
            self.ws_ex_images = None
            self.ws_ex_buttons = None
            self.w_img_choice = None

        self.w_show_img = widgets.Image(width=300, height=300)

        if enable_crop:
            self.w_choose_crop = widgets.Checkbox(value=False,
                                                  description="Crop image?")
            self.w_crop_slider_x = widgets.IntRangeSlider(min=0,
                                                          max=0,
                                                          value=(0, 0),
                                                          step=1,
                                                          description='X Crop')
            self.w_crop_slider_y = widgets.IntRangeSlider(min=0,
                                                          max=0,
                                                          value=(0, 0),
                                                          step=1,
                                                          description='Y Crop')
            self.w_crop_slider_x.layout.visibility = 'hidden'
            self.w_crop_slider_y.layout.visibility = 'hidden'
            self.w_crop = widgets.HBox([
                self.w_choose_crop, self.w_crop_slider_x, self.w_crop_slider_y
            ])
        else:
            self.w_choose_crop = None
            self.w_crop_slider_x = None
            self.w_crop_slider_y = None
            self.w_crop = None

        all_widgets = [
            self.w_label, self.w_upload, self.w_img_choice, self.w_show_img,
            self.w_crop
        ]
        all_widgets = [w for w in all_widgets if w is not None]
        self.value = None
        self.stored = None
        if self.have_choice:
            for i in range(len(self.ws_ex_buttons)):
                self.ws_ex_buttons[i].id = i
                self.ws_ex_buttons[i].on_click(self.observe_choice)
            self.observe_choice(self.ws_ex_buttons[0])
        if self.enable_upload:
            self.w_upload.observe(self.observe_upload)
        if self.enable_crop:
            self.w_choose_crop.observe(self.observe_choose_crop)
            self.w_crop_slider_y.observe(self.observe_crop)
            self.w_crop_slider_x.observe(self.observe_crop)
        super().__init__(all_widgets)

    def set_new_image(self, new_img):
        self.update_value(new_img)
        self.stored = new_img
        if self.enable_crop:
            Y, X = imageio.imread(new_img).shape[:2]
            self.w_crop_slider_x.max = X
            self.w_crop_slider_y.max = Y
            self.w_crop_slider_x.value = (0, X)
            self.w_crop_slider_y.value = (0, Y)
            self.w_choose_crop.value = False

    def observe_upload(self, change):
        self.set_new_image(change.new[0])

    def observe_choice(self, b):
        self.set_new_image(self.ws_ex_images[b.id].value)

    def observe_choose_crop(self, _):
        if self.w_choose_crop.value:
            self.w_crop_slider_y.layout.visibility = 'visible'
            self.w_crop_slider_x.layout.visibility = 'visible'
        else:
            self.w_crop_slider_y.layout.visibility = 'hidden'
            self.w_crop_slider_x.layout.visibility = 'hidden'
            self.value = self.stored
        self.w_crop_slider_y.value = (0, self.w_crop_slider_y.max)
        self.w_crop_slider_x.value = (0, self.w_crop_slider_x.max)

    def observe_crop(self, _):
        left, right = self.w_crop_slider_x.value
        top, bottom = self.w_crop_slider_y.value
        img = Image.open(io.BytesIO(self.stored))
        img = img.crop((left, top, right, bottom))
        out = io.BytesIO()
        img.save(out, format='png')
        out.seek(0)
        self.update_value(out.read())

    def update_value(self, value):
        self.value = value
        self.w_show_img.value = self.value


class RangeTextSlider(widgets.HBox):
    def __init__(self,
                 value_min,
                 value_max,
                 default_values=None,
                 value_type='float',
                 description_left='',
                 description_right='',
                 text_kwargs={},
                 **kwargs):
        if value_type == 'float':
            Slider = widgets.FloatRangeSlider
            Text = widgets.FloatText
        elif value_type == 'int':
            Slider = widgets.IntRangeSlider
            Text = widgets.IntText
        else:
            raise ValueError(value_type)
        if default_values is None:
            default_values = (value_min, value_max)
        self.slider = Slider(min=value_min,
                             max=value_max,
                             value=default_values,
                             **kwargs)
        self.text_left = Text(description=description_left,
                              value=self.slider.value[0])
        self.text_right = Text(description=description_right,
                               value=self.slider.value[1])
        self.text_left.observe(self.observe_text_left)
        self.text_right.observe(self.observe_text_right)
        self.slider.observe(self.observe_slider)
        super().__init__([self.text_left, self.slider, self.text_right])

    def observe_text_left(self, _):
        old_left, right = self.slider.value
        new_left = min(right, max(self.slider.min, self.text_left.value))
        self.text_left.value = new_left
        self.slider.value = new_left, right

    def observe_text_right(self, _):
        left, old_right = self.slider.value
        new_right = min(self.slider.max, max(left, self.text_right.value))
        self.text_right.value = new_right
        self.slider.value = left, new_right

    def observe_slider(self, _):
        left, right = self.slider.value
        self.text_left.value = left
        self.text_right.value = right

    @property
    def value(self):
        return self.slider.value
