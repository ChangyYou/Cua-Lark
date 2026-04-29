import os
import glob
import yaml
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--test-suites-dir", action="store", default="test_suites", help="Directory containing test suite YAML files"
    )

def pytest_generate_tests(metafunc):
    """
    Dynamically generate pytest items from YAML files in the test suites directory.
    """
    if "test_case" in metafunc.fixturenames:
        # Resolve path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        suites_dir = os.path.join(project_root, metafunc.config.getoption("test_suites_dir"))
        yaml_files = glob.glob(os.path.join(suites_dir, "*.yaml"))
        
        test_cases = []
        case_ids = []
        
        for yaml_file in yaml_files:
            with open(yaml_file, "r", encoding="utf-8") as f:
                suite = yaml.safe_load(f)
                suite_name = suite.get("test_suite", os.path.basename(yaml_file))
                
                for case in suite.get("cases", []):
                    test_cases.append({
                        "suite_name": suite_name,
                        "case": case
                    })
                    case_ids.append(f"{suite_name}::{case['id']}")
                    
        metafunc.parametrize("test_case", test_cases, ids=case_ids)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, 'extra', [])

    if report.when == 'call' and pytest_html is not None:
        # Add screenshot and assertion reason to the HTML report if they exist
        if hasattr(pytest, 'last_assert_image'):
            # pytest-html needs a relative path or absolute path, we'll use the absolute path
            abs_img_path = os.path.abspath(pytest.last_assert_image)
            extra.append(pytest_html.extras.image(abs_img_path))
            
        if hasattr(pytest, 'last_assert_reason'):
            extra.append(pytest_html.extras.html(f"<div><strong>Assertion Reason:</strong> {pytest.last_assert_reason}</div>"))
            
        # Clean up so they don't leak to next test
        if hasattr(pytest, 'last_assert_image'):
            delattr(pytest, 'last_assert_image')
        if hasattr(pytest, 'last_assert_reason'):
            delattr(pytest, 'last_assert_reason')

        report.extra = extra
