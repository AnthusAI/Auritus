"""Lambda layer carrying Cognito operator token verification.

The layer holds PyJWT, cryptography, and ``auritus_operator_auth``. Both the
API authorizer and the router import it. Bundling runs ``pip`` locally for
the Lambda platform (manylinux x86_64, CPython 3.11) so synth does not need
Docker; it falls back to the CDK Python bundling image when local pip fails.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import jsii
from aws_cdk import BundlingOptions, ILocalBundling
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

OPERATOR_AUTH_LAYER_ROOT = (
    Path(__file__).resolve().parents[1] / "lambdas" / "operator_auth_layer"
)
LAMBDA_PYTHON_VERSION = "3.11"
LAMBDA_PIP_PLATFORM = "manylinux2014_x86_64"


@jsii.implements(ILocalBundling)
class LocalPipLayerBundler:
    """Build the layer's ``python/`` directory with the host's pip."""

    def try_bundle(self, output_dir: str, _options: BundlingOptions) -> bool:
        """Install pinned wheels for the Lambda platform and copy the module.

        :param output_dir: CDK asset output directory.
        :param _options: The asset's bundling options (unused).
        :returns: ``True`` when the layer was built, ``False`` to fall back to
            Docker bundling.
        """
        target = Path(output_dir) / "python"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--disable-pip-version-check",
                "--requirement",
                str(OPERATOR_AUTH_LAYER_ROOT / "requirements.txt"),
                "--target",
                str(target),
                "--platform",
                LAMBDA_PIP_PLATFORM,
                "--implementation",
                "cp",
                "--python-version",
                LAMBDA_PYTHON_VERSION,
                "--only-binary=:all:",
            ],
            check=False,
        )
        if result.returncode != 0:
            return False
        for module_path in (OPERATOR_AUTH_LAYER_ROOT / "python").glob("*.py"):
            shutil.copy2(module_path, target / module_path.name)
        return True


def build_operator_auth_layer(scope: Construct) -> lambda_.LayerVersion:
    """Create the operator auth Lambda layer.

    :param scope: The construct scope, normally the backend stack.
    :returns: The layer version to attach to the authorizer and router.
    """
    runtime = lambda_.Runtime.PYTHON_3_11
    return lambda_.LayerVersion(
        scope,
        "OperatorAuthLayer",
        description="PyJWT, cryptography, and Auritus operator token verification",
        compatible_runtimes=[runtime],
        compatible_architectures=[lambda_.Architecture.X86_64],
        code=lambda_.Code.from_asset(
            str(OPERATOR_AUTH_LAYER_ROOT),
            bundling=BundlingOptions(
                image=runtime.bundling_image,
                local=LocalPipLayerBundler(),
                command=[
                    "bash",
                    "-c",
                    "pip install --requirement requirements.txt "
                    "--target /asset-output/python "
                    "&& cp python/*.py /asset-output/python/",
                ],
            ),
        ),
    )
