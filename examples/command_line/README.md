# dash-annotate-cv command line utility

Dash Annotate CV comes with a command line utility that can be used to annotate images by simply writing a YAML config file.

## Run

```bash
dacv conf.yml
```

Navigate to `http://127.0.0.1:8050/` in your browser to see the app running. The default port is `8050`. You can change it as described in the options below.

## Options

For a complete list of options, run:

```bash
dacv --h
```

Basic options
* `--port 8050`: The port to run the app on. Default is `8050`.
* `--debug`: Run the app in debug mode.