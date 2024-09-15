import sys

import modal
app = modal.App("example-get-started")


datascience_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("pandas==2.2.0", "numpy")
)


@app.function(image=datascience_image)
def my_function():
    import pandas as pd
    import numpy as np

    df = pd.DataFrame()



@app.function(gpu="A10G")
def function_two():
    pass
