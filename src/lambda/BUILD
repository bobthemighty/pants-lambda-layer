python_sources(

)

pex_binary (
    name="main",
    layout="zipapp",
    dependencies=[
        "src/lambda/handler.py",
        "!!3rdparty/python:numpy",
    ]
)
