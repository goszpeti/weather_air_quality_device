from waqd.assets.assets import get_asset_file, Logger


def test_get_with_file_type(base_fixture):
    # Positive test for format with common filetype in toc
    rsc_folder = base_fixture.testdata_path / "assets" / "with_filetype"
    dummy1 = get_asset_file(rsc_folder, "dummy1")
    dummy2 = get_asset_file(rsc_folder, "dummy2")
    assert dummy1 == rsc_folder / "dummy1_value.png"
    assert dummy2 == rsc_folder / "dummy2_value.png"


def test_get_withou_file_type(base_fixture):
    # Positive test for format with no common filetype in toc
    rsc_folder = base_fixture.testdata_path / "assets" / "without_filetype"
    dummy1 = get_asset_file(rsc_folder, "dummy1")
    dummy2 = get_asset_file(rsc_folder, "dummy2")
    assert dummy1 == rsc_folder / "dummy1_value.png"
    assert dummy2 == rsc_folder / "dummy2_value.gif"


def test_no_file_toc(base_fixture, capsys):
    # Test, that a file without ToC works too (ONLY if no ToC is present)
    rsc_folder = base_fixture.testdata_path / "assets"
    dummy1 = get_asset_file(rsc_folder, "dummy1_value.png")
    assert dummy1 == rsc_folder / "dummy1_value.png"


def test_no_toc_entry(base_fixture, capsys):
    Logger()
    rsc_folder = base_fixture.testdata_path / "assets" / "without_filetype"
    non_existant_rsc = get_asset_file(rsc_folder, "non_existant_rsc")
    captured = capsys.readouterr()
    assert not non_existant_rsc.exists()
    assert "ERROR" in captured.out
    assert "Cannot find resource id" in captured.out


def test_no_rsc_file(base_fixture, capsys):
    rsc_folder = base_fixture.testdata_path / "assets" / "without_filetype"
    dummy3 = get_asset_file(rsc_folder, "dummy3")
    captured = capsys.readouterr()
    assert not dummy3.exists()
    assert "ERROR" in captured.out
    assert "Cannot find resource file" in captured.out

# TODO, test if every asset file exists


def test_if_assets_exists():
    pass
