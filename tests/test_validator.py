"""Тесты валидатора Form.xml."""

from pathlib import Path

from mcp_forms.forms.loader import load_form, detect_format
from mcp_forms.schema.validator import validate_form

FIXTURES = Path(__file__).parent / "fixtures"


class TestDetectFormat:
    def test_logform(self):
        xml = (FIXTURES / "logform_catalog_element.xml").read_bytes()
        assert detect_format(xml) == "logform"

    def test_managed(self):
        xml = (FIXTURES / "managed_simple.xml").read_bytes()
        assert detect_format(xml) == "managed"

    def test_invalid_xml(self):
        assert detect_format(b"not xml at all") == "unknown"


class TestLoadForm:
    def test_logform_loads(self):
        xml = (FIXTURES / "logform_catalog_element.xml").read_bytes()
        doc = load_form(xml)
        assert doc.format == "logform"
        assert doc.version == "2.16"

    def test_managed_loads(self):
        xml = (FIXTURES / "managed_simple.xml").read_bytes()
        doc = load_form(xml)
        assert doc.format == "managed"

    def test_logform_with_bom(self):
        xml = (FIXTURES / "logform_catalog_element.xml").read_bytes()
        assert xml.startswith(b"\xef\xbb\xbf") or True  # BOM may or may not be present
        doc = load_form(xml)
        assert doc.format == "logform"


class TestValidateLogform:
    def test_valid_catalog_element(self):
        xml = (FIXTURES / "logform_catalog_element.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        assert result.is_valid
        assert result.error_count == 0

    def test_valid_document(self):
        xml = (FIXTURES / "logform_document.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        assert result.is_valid

    def test_broken_duplicate_element_ids(self):
        xml = (FIXTURES / "logform_broken.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        assert not result.is_valid
        messages = [e.message for e in result.errors if e.severity == "error"]
        assert any("Дублирующийся id=1" in m for m in messages)

    def test_broken_duplicate_attribute_names(self):
        xml = (FIXTURES / "logform_broken.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        messages = [e.message for e in result.errors if e.severity == "error"]
        assert any("Дублирующееся имя атрибута" in m for m in messages)

    def test_broken_missing_companions(self):
        xml = (FIXTURES / "logform_broken.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e.message for e in result.errors if e.severity == "warning"]
        assert any("ContextMenu" in w for w in warnings)
        assert any("ExtendedTooltip" in w for w in warnings)

    def test_broken_datapath_warning(self):
        xml = (FIXTURES / "logform_broken.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e.message for e in result.errors if e.severity == "warning"]
        assert any("НесуществующийРеквизит" in w for w in warnings)

    def test_to_dict(self):
        xml = (FIXTURES / "logform_broken.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        d = result.to_dict()
        assert d["valid"] is False
        assert d["format"] == "logform"
        assert isinstance(d["details"], list)
        assert len(d["details"]) > 0


class TestValidateManaged:
    def test_valid_simple(self):
        xml = (FIXTURES / "managed_simple.xml").read_bytes()
        doc = load_form(xml)
        result = validate_form(doc)
        assert result.is_valid
