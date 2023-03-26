from dataclasses import dataclass

import os

from pants.backend.python.util_rules.pex_cli import PexPEX
from pants.backend.python.util_rules.pex import (
    Pex,
    PexEnvironment,
    VenvPex,
)
from pants.backend.python.util_rules.pex_from_targets import PexFromTargetsRequest
from pants.core.goals.package import BuiltPackage, PackageFieldSet
from pants.engine.fs import (
    AddPrefix,
    CreateDigest,
    Digest,
    DigestSubset,
    MergeDigests,
    PathGlobs,
    RemovePrefix,
    Snapshot,
)
from pants.engine.process import Process, ProcessResult
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Dependencies, DependenciesRequest, Targets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from pants.core.goals.package import (
    BuiltPackageArtifact,
    BuiltPackage,
    PackageFieldSet,
)
from pants.core.util_rules.archive import CreateArchive, ArchiveFormat
import logging

logger = logging.getLogger(__name__)


class LayerDependencies(Dependencies):
    pass


@dataclass(frozen=True)
class PythonLambdaLayerFieldSet(PackageFieldSet):
    required_fields = (LayerDependencies,)

    dependencies: LayerDependencies


@rule(level=LogLevel.DEBUG)
async def do_it(
    field_set: PythonLambdaLayerFieldSet,
    pex_env: PexEnvironment,
    pex_pex: PexPEX,
) -> BuiltPackage:

    targets = await Get(Targets, DependenciesRequest(field_set.dependencies))

    requirements_pex = await Get(
        VenvPex,
        PexFromTargetsRequest(
            output_filename="requirements.pex",
            addresses=[tgt.address for tgt in targets],
            internal_only=True,
            include_source_files=False,
            additional_args=["--include-tools"],
        ),
    )

    complete_pex_env = pex_env.in_sandbox(working_directory=None)
    merged_digest = await Get(
        Digest, MergeDigests([pex_pex.digest, requirements_pex.digest])
    )

    argv = complete_pex_env.create_argv(
        "requirements.pex",
        *[
            "venv",
            "--collisions-ok",
            "--scope=deps",
            "./venv",
        ],
    )
    env = {
        **complete_pex_env.environment_dict(python_configured=requirements_pex.python),
        "PEX_TOOLS": "1",
    }

    venv = await Get(
        ProcessResult,
        Process(
            argv=argv,
            env=env,
            description="Create the venv",
            input_digest=merged_digest,
            output_directories=["venv/lib/python3.9/site-packages/*"],
        ),
    )

    strip_venv = await Get(
        Digest,
        RemovePrefix(venv.output_digest, "venv/lib/python3.9/site-packages"),
    )

    python_directory = await Get(Digest, AddPrefix(strip_venv, "python"))
    snapshot = await Get(Snapshot, Digest, python_directory)

    zip = await Get(
        Digest,
        CreateArchive(
            snapshot=snapshot, format=ArchiveFormat.ZIP, output_filename="layer.zip"
        ),
    )

    return BuiltPackage(
        digest=zip,
        artifacts=(BuiltPackageArtifact("layer.zip"),),
    )


def rules():
    return [*collect_rules(), UnionRule(PackageFieldSet, PythonLambdaLayerFieldSet)]
