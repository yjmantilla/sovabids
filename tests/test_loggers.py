import logging
import os
import pytest
from sovabids.loggers import setup_logging


@pytest.fixture(autouse=True)
def clean_root_handlers():
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers[:] = original_handlers
    root.setLevel(original_level)


def test_setup_logging_adds_stderr_streamhandler(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(log_file)
    root = logging.getLogger()
    stream_handlers = [h for h in root.handlers if h.name == 'streamhandler']
    assert len(stream_handlers) == 1
    assert stream_handlers[0].level == logging.WARNING


def test_setup_logging_stderr_handler_not_duplicated(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(log_file)
    setup_logging(log_file)
    root = logging.getLogger()
    stream_handlers = [h for h in root.handlers if h.name == 'streamhandler']
    assert len(stream_handlers) == 1


def test_setup_logging_creates_error_file(tmp_path):
    log_file = str(tmp_path / "sovabids.log")
    setup_logging(log_file)
    error_file = log_file + ".errors"
    assert os.path.exists(error_file)


def test_warnings_written_to_error_file(tmp_path):
    log_file = str(tmp_path / "sovabids.log")
    setup_logging(log_file)
    logging.getLogger("sovabids.test").warning("test warning message")
    error_file = log_file + ".errors"
    content = open(error_file).read()
    assert "test warning message" in content


def test_info_not_written_to_error_file(tmp_path):
    log_file = str(tmp_path / "sovabids.log")
    setup_logging(log_file)
    logging.getLogger("sovabids.test").info("test info message")
    error_file = log_file + ".errors"
    content = open(error_file).read()
    assert "test info message" not in content


def test_warnings_printed_to_stderr(tmp_path, capsys):
    log_file = str(tmp_path / "sovabids.log")
    setup_logging(log_file)
    logging.getLogger("sovabids.test").warning("console warning check")
    err = capsys.readouterr().err
    assert "console warning check" in err


def test_warnings_printed_to_stderr_with_preexisting_handler(tmp_path, capsys):
    log_file = str(tmp_path / "sovabids.log")
    root = logging.getLogger()
    # Add a dummy stream handler that doesn't write to stderr
    import io
    dummy_stream = io.StringIO()
    dummy_handler = logging.StreamHandler(dummy_stream)
    root.addHandler(dummy_handler)
    
    setup_logging(log_file)
    logging.getLogger("sovabids.test").warning("console warning check")
    err = capsys.readouterr().err
    # If setup_logging didn't add its own stderr handler, this will fail
    assert "console warning check" in err


def test_setup_logging_no_logfile_returns_logger():
    logger = setup_logging(log_file=None)
    assert logger is not None
    assert isinstance(logger, logging.Logger)
