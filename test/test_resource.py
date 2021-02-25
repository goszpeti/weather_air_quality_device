from piweather.resources.resources import get_rsc_file, Logger
from piweather.config import PROG_NAME
import piweather.config


def testGetWithFileType(base_fixture):
    # Positive test for format with common filetype in toc
    rsc_folder = base_fixture.testdata_path / "resources" / "with_filetype"
    dummy1 = get_rsc_file(rsc_folder, "dummy1")
    dummy2 = get_rsc_file(rsc_folder, "dummy2")
    assert dummy1 == rsc_folder / "dummy1_value.png"
    assert dummy2 == rsc_folder / "dummy2_value.png"


def testGetWithouFileType(base_fixture):
    # Positive test for format with no common filetype in toc
    rsc_folder = base_fixture.testdata_path / "resources" / "without_filetype"
    dummy1 = get_rsc_file(rsc_folder, "dummy1")
    dummy2 = get_rsc_file(rsc_folder, "dummy2")
    assert dummy1 == rsc_folder / "dummy1_value.png"
    assert dummy2 == rsc_folder / "dummy2_value.gif"


def testNoFileToc(base_fixture, capsys):
    rsc_folder = base_fixture.testdata_path / "resources"
    dummy1 = get_rsc_file(rsc_folder, "dummy1")
    captured = capsys.readouterr()
    assert dummy1 is None
    assert "ERROR" in captured.out
    assert "Cannot find catalog" in captured.out


def testNoTocEntry(base_fixture, capsys):
    Logger()
    rsc_folder = base_fixture.testdata_path / "resources" / "without_filetype"
    non_existant_rsc = get_rsc_file(rsc_folder, "non_existant_rsc")
    captured = capsys.readouterr()
    assert non_existant_rsc is None
    assert "ERROR" in captured.out
    assert "Cannot find resource id" in captured.out


def testNoRscFile(base_fixture, capsys):
    rsc_folder = base_fixture.testdata_path / "resources" / "without_filetype"
    dummy3 = get_rsc_file(rsc_folder, "dummy3")
    captured = capsys.readouterr()
    assert dummy3 is None
    assert "ERROR" in captured.out
    assert "Cannot find resource file" in captured.out
