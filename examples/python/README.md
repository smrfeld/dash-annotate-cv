# Examples of Python usage

The app can be launched by writing a short Python script, which lets you use the annotation components in a flexible way in your own Dash app. Alternatively, a simple command line utility lets you just get up and running.

* Annotating single image labels (whole label per image):
    ```bash
    python example_single.json
    ```

* Annotating multiple image labels (multiple labels per image):
    ```bash
    python example_multiple.json
    ```

* Annotating bounding boxes:
    ```bash
    python example_bboxs.json
    ```

Navigate to the default address `http://127.0.0.1:8050/` in your browser to use the app.

The outputs of the labeling are written to the JSON files in this directory. Some examples are provided for guidance. 

The format of the JSONs follows the `ImageAnnotations` dataclass defined in [dash_annotate_cv/image_annotations.py](../../dash_annotate_cv/image_annotations.py) for the format of the JSON files.