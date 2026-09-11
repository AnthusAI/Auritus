"""auritus deploy command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from auritus.config import global_config_path, load_config, save_config

app = typer.Typer(help="Deploy the Auritus CDK stack and write outputs to config.")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[4]


@app.callback(invoke_without_command=True)
def deploy(
    stack: str = typer.Option("AuritusBackend", help="CDK stack name"),
    require_approval: str = typer.Option(
        "never", "--require-approval", help="CDK require-approval setting"
    ),
) -> None:
    """Run cdk deploy and merge stack outputs into ~/.auritus/config."""
    cdk_dir = _repo_root() / "cdk"
    if not cdk_dir.exists():
        typer.secho(
            f"CDK directory not found: {cdk_dir}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)

    outputs_file = cdk_dir / "cdk-outputs.json"
    cmd = [
        "cdk",
        "deploy",
        stack,
        "--outputs-file",
        str(outputs_file),
        "--require-approval",
        require_approval,
    ]
    typer.echo(f"Running: {' '.join(cmd)} (cwd={cdk_dir})")
    result = subprocess.run(cmd, cwd=cdk_dir, check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

    if not outputs_file.exists():
        typer.secho(
            "Deploy succeeded but no outputs file was written.", fg=typer.colors.YELLOW
        )
        return

    raw = json.loads(outputs_file.read_text(encoding="utf-8"))
    stack_outputs = raw.get(stack) or next(iter(raw.values()), {})
    cfg = load_config()
    mapping = {
        "ApiEndpoint": "api_endpoint",
        "CognitoClientId": "cognito_client_id",
        "UserPoolId": "user_pool_id",
        "CognitoDomain": "cognito_domain",
        "BatchQueue": "batch_queue",
        "AudioBucket": "s3_bucket",
        "CloudFrontDomain": "cloudfront_domain",
        "Region": "region",
    }
    for output_key, config_key in mapping.items():
        if output_key in stack_outputs:
            cfg[config_key] = stack_outputs[output_key]
    path = save_config(cfg, path=global_config_path())
    typer.secho(f"Wrote stack outputs to {path}", fg=typer.colors.GREEN)
