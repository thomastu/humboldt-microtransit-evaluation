import os
import click

from subprocess import call
from pathlib import Path
from hcme.settings import BEAM_DIR, JAVA_EXEC_PATH


CMD = """
java -Dorg.gradle.appname=gradlew -classpath /home/ttu/thesis/beam-quickstart/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :run -PappArgs=['--config', 'test/input/sf-light/sf-light.conf'] -PmaxRAM=$MAX_RAM
"""


def build_cmd(conf, maxram=2):
    """Format the command for running a BEAM iteration.
    """

    cmd = (
        f"{JAVA_EXEC_PATH} -Dorg.gradle.appname={BEAM_DIR}gradlew -classpath {BEAM_DIR}gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :run "
        f"""-PappArgs="['--config', '{conf}']" -PmaxRAM={maxram}"""
    )
    print(cmd)
    return cmd


def _format_cmd(beam_path, conf):
    c = str(Path(BEAM_DIR).absolute() / "gradlew")
    args = f":run -PappArgs=\"['--config', {conf}]\""
    return [c, args]


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("-c", "--conf", type=click.Path(exists=True))
@click.option("-r", "--max-ram", type=click.INT, help="Max ram to use in GB", default=2)
def main(ctx, conf, max_ram):
    """Wrapper for running BEAM.
    """
    if ctx.invoked_subcommand is None:
        call(build_cmd(conf, max_ram), cwd=str(BEAM_DIR), shell=True)


@main.command()
@click.option("-c", "--conf", type=click.Path(exists=True))
@click.option("-r", "--max-ram", type=click.INT, help="Max ram to use in GB", default=2)
def info(conf, max_ram):
    """Print gradlew path and BEAM directory.
    """
    cmd = build_cmd(conf or "<path-to-config.conf>", max_ram)
    click.echo(f"Beam Command: {cmd}")


if __name__ == "__main__":
    main()
