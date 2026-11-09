from app.services.package_manager import PackageManager


def test_unconfigured_install_cannot_report_success_or_create_fake_metadata(tmp_path):
    manager = PackageManager(packages_dir=tmp_path)
    result = manager.install_package('example')
    assert result.success is False
    assert manager.list_packages() == []
    assert not (tmp_path / 'installed.json').exists()
