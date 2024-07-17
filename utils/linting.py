import os
import subprocess
import ast
from typing import Optional

from lib import logger


class Linter:
    def __init__(self):
        self.python_config = {
            "linter": "pylint",
            "error_codes": {"raise": [1, 2, 4]},
            "venv": "venv_matplotlib",
            "conda_env": None,
        }
        self.js_config = {
            "linter": "jshint",
            "config_file": "linter_configs/jshint.json",
            "error_code": {},
        }

    def lint_file(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = file_path.split(".")[-1]

        try:
            if file_extension == "py":
                return self._lint_python(file_path)
            elif file_extension == "js":
                return self._lint_javascript(file_path)
            elif file_extension == "html":
                return self._lint_html(file_path)
            elif file_extension == "css":
                return self._lint_css(file_path)
            else:
                logger.warning(f"'.{file_extension}' linting is not supported yet.")
        except NotImplementedError as nie:
            logger.warning(nie)

    def _lint_python(self, file_path: str) -> Optional[str]:
        if not file_path.endswith(".py"):
            raise ValueError("File is not a python file")

        if self.python_config.get("venv", None):
            command = f"source {self.python_config['venv']}/bin/activate && {self.python_config['linter']} {file_path}"
        elif self.python_config.get("conda_env", None):
            command = f"conda activate {self.python_config['conda_env']} && conda run {self.python_config['linter']} {file_path}"
        else:
            command = f"{self.python_config['linter']} {file_path}"

        lint_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
        )

        if lint_result:
            error_codes = self.python_config.get("error_codes", {}).get("raise", None)
            if not error_codes or lint_result.returncode in error_codes:
                raise LinterError(
                    return_code=lint_result.returncode,
                    stdout=lint_result.stdout,
                    stderr=lint_result.stderr,
                    file_path=file_path,
                )
            return lint_result.stdout

    def _lint_javascript(self, file_path: str) -> Optional[str]:
        args = [self.js_config["linter"]]
        if self.js_config.get("config_file", None):
            args.extend(["--config", self.js_config["config_file"]])
        args.append(file_path)

        lint_result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )

        if lint_result:
            error_code = self.js_config.get("error_code", {}).get("raise", None)
            if error_code and lint_result.returncode == error_code:
                raise LinterError(
                    return_code=lint_result.returncode,
                    stdout=lint_result.stdout,
                    stderr=lint_result.stderr,
                    file_path=file_path,
                )

            return lint_result.stdout

    def _lint_html(self, file_path: str) -> Optional[str]:
        raise NotImplementedError("HTML linting is not supported yet")

    def _lint_css(self, file_path: str) -> Optional[str]:
        raise NotImplementedError("CSS linting is not supported yet")


class LinterError(Exception):
    """
    Should have the following properties:
    - message: str
    - file_path: str
    - file_extension: str
    """

    def __init__(self, return_code, stdout, stderr, file_path):
        self.return_code = return_code
        self.stdout = stdout.strip()
        if stderr:
            stderr = stderr.strip()
            stderr = None if stderr == "" else stderr
        self.stderr = stderr
        self.message = f"[stdout]:{stdout.strip()}"
        if stderr:
            self.message += f"\n\n[stderr]:{stderr}"
        self.file_path = file_path
        super().__init__(self.message)

    def __str__(self):
        return f"[File: {self.file_path} (Return Code {self.return_code})]\n\n{self.message}"


# Initialize a Linter object
default_linter = Linter()
