# This registers all of the plugin hooks that action our sources/dependencies
from .target_types import (
    PythonLambdaLayerTarget,
)

from .rules import rules as lambda_layer_rules


def rules():
    return [*lambda_layer_rules()]


def target_types():
    return [PythonLambdaLayerTarget]
