from .rules import LayerDependencies
from pants.engine.target import Target, COMMON_TARGET_FIELDS, Dependencies


class PythonLambdaLayerTarget(Target):
    alias = "python_lambda_layer"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        LayerDependencies,
    )
    help = "The `python_lambda_layer` target will take a set of dependencies and package them in a zip file to be deployed as a lambda layer."
