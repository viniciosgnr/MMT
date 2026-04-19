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

def test_m3_bsw_boundary_warn(client, sp_factory, sample_factory):
    """Verifica que BS&W acima do limite (1.0) gera Alerta (Warning) mas Aprova."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_pvt = PVTResult(
        report_type="PVT",
        boletim="PVT-TEST-002",
        density=850.0,
        bsw=1.5 # Bem acima do limite
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
        assert data["overall_status"] == "Approved" # Informative only
        
        bsw_check = next(c for c in data["checks"] if c["parameter"] == "bsw")
        assert bsw_check["status"] == "warning"
        assert "exceeds limit" in bsw_check["detail"]
        assert "Informative" in bsw_check["detail"]

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

def test_m3_h2s_boundary_warn(client, sp_factory, sample_factory):
    """Verifica que H2S acima do limite (10.0) gera Alerta (Warning) mas Aprova."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_cro = CROResult(
        report_type="CRO",
        boletim="CRO-TEST-002",
        h2s=15.0 # Acima do limite
    )
    
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_cro), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        res = client.post(
            f"/api/chemical/samples/{sample['id']}/validate-report",
            files={"file": ("test.pdf", b"dummy content", "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "Approved" # Informative only
        
        h2s_check = next(c for c in data["checks"] if c["parameter"] == "h2s")
        assert h2s_check["status"] == "warning"

def test_m3_o2_boundary_fail(client, sp_factory, sample_factory):
    """Verifica que O2 acima do limite (0.5) CONTINUA reprovando."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")
    
    mock_cro = CROResult(
        report_type="CRO",
        boletim="CRO-TEST-O2-FAIL",
        o2=0.6,  # Fail (Limit 0.5)
        h2s=5.0  # Pass
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
        o2_check = next(c for c in checks if c["parameter"] == "o2")
        assert o2_check["status"] == "fail"
        assert any(c["parameter"] == "h2s" and c["status"] == "pass" for c in checks)
