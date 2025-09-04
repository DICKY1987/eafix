from unittest.mock import patch

from eafix.apps.desktop.main import launch_mt4


def test_launch_mt4_uses_env_path(monkeypatch):
    fake_path = "/fake/terminal.exe"
    monkeypatch.setenv("MT4_PATH", fake_path)

    with patch("eafix.apps.desktop.main.Path.is_file", return_value=True), \
            patch("eafix.apps.desktop.main.subprocess.Popen") as popen:
        launch_mt4()
        popen.assert_called_once_with([fake_path])

