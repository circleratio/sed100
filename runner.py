"""Run sed against input text and report the result."""
import shlex
import subprocess

SED_TIMEOUT_SECONDS = 5


class SedError(Exception):
    """Raised when sed itself fails (bad syntax, missing binary, timeout)."""


def run_sed(script_str: str, input_text: str) -> str:
    """Execute `sed <script_str>` with input_text on stdin, return stdout.

    script_str is exactly what a user would type after "sed " on a real
    command line (may include -n/-e/-E flags and quoted scripts).
    """
    try:
        args = shlex.split(script_str)
    except ValueError as exc:
        raise SedError(f"引数の解析に失敗しました: {exc}") from exc

    try:
        proc = subprocess.run(
            ["sed", *args],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=SED_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise SedError("sed コマンドが見つかりません。PATH を確認してください。") from exc
    except subprocess.TimeoutExpired as exc:
        raise SedError("sed の実行がタイムアウトしました。") from exc

    if proc.returncode != 0:
        message = proc.stderr.strip() or f"sed がエラー終了しました (code={proc.returncode})"
        raise SedError(message)

    return proc.stdout
