import pytest
from unittest.mock import patch, mock_open
from app.services.pdf_parser import PVTResult, CROResult

def test_m3_bsw_boundary_pass(client, sp_factory, sample_factory):
    """Verifica que BS&W dentro do limite (1.0) passa."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    # Mock do parser para retornar BS&W = 1.0
    mock_pvt = PVTResult(
        report_type="PVT",
        boletim="PVT-TEST-001",
        density=850.0,
        bsw=1.0 # No limite
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_pvt), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "Approved"
        
        # Verifica se o check de BS&W passou
        bsw_check = next(c for c in data["checks"] if c["parameter"] == "bsw")
        assert bsw_check["status"] == "pass"

def test_m3_bsw_boundary_fail(client, sp_factory, sample_factory):
    """Verifica que BS&W acima do limite (1.0) reprova."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_pvt = PVTResult(
        report_type="PVT",
        boletim="PVT-TEST-002",
        density=850.0,
        bsw=1.1 # Acima do limite
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_pvt), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "Reproved"
        
        bsw_check = next(c for c in data["checks"] if c["parameter"] == "bsw")
        assert bsw_check["status"] == "fail"
        assert "exceeds limit" in bsw_check["detail"]

def test_m3_h2s_boundary_pass(client, sp_factory, sample_factory):
    """Verifica que H2S dentro do limite (10.0) passa."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_cro = CROResult(
        report_type="CRO",
        boletim="CRO-TEST-001",
        h2s=10.0 # No limite
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_cro), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["overall_status"] == "Approved"

def test_m3_h2s_boundary_fail(client, sp_factory, sample_factory):
    """Verifica que H2S acima do limite (10.0) reprova."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_cro = CROResult(
        report_type="CRO",
        boletim="CRO-TEST-002",
        h2s=10.1 # Acima do limite
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_cro), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["overall_status"] == "Reproved"

def test_m3_stress_combined_fail(client, sp_factory, sample_factory):
    """Verifica que qualquer falha (mesmo com outros passando) reprova."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    # O2 passa, mas H2S falha
    mock_cro = CROResult(
        report_type="CRO",
        boletim="CRO-TEST-003",
        o2=0.1,  # Pass (Limit 0.5)
        h2s=15.0 # Fail (Limit 10.0)
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_cro), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        assert res.json()["overall_status"] == "Reproved"
        
        checks = res.json()["checks"]
        assert any(c["parameter"] == "o2" and c["status"] == "pass" for c in checks)
        assert any(c["parameter"] == "h2s" and c["status"] == "fail" for c in checks)
