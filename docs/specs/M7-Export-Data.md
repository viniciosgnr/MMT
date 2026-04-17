# M7 — Export Data

> **Fonte:** PRD §12.8 — Export Data
> **Normas:** Ofício ANP/NFP nº 906/2021 (Offloading XML), ISO 10012
> **Módulos Relacionados:** M11 (configuração), M1 (equipamentos), M2 (certificados), M3 (laudos)

---

## Descrição

Exporta dados estruturados para auditorias ANP, incluindo geração de ZIP archives com estrutura de pastas regulatória e exportação para Excel/PDF.

---

## Requisitos Funcionais (PRD §12.8)

### REQ-M7-01: Export para Excel e PDF
O sistema DEVE exportar views filtradas de módulos (ex: listas de equipamentos, certificados, atividades) para formatos Excel (.xlsx) e PDF. **[MVP]**

### REQ-M7-02: ZIP Archive para ANP
O sistema DEVE gerar um arquivo ZIP estruturado para auditorias ANP, seguindo rigorosamente a estrutura de pastas:
```
FPSO → Categoria → Tag → Data_EventCode
```

### REQ-M7-03: Empacotamento Dinâmico
O sistema DEVE empacotar dinamicamente todos os metadados associados, arquivos XML externos e certificados PDF nos ZIP archives gerados.

---

## Regras MMT Aplicáveis
- **Rule 03:** Exports devem ser assíncronos (background task com progress bar)
- **Rule 05:** Formato bilíngue (EN/PT) para documentos gerados

## Subagents Responsáveis
- **Backend Specialist:** Engine de geração de ZIP, background tasks
- **Metrology Specialist:** Validação de estrutura de pastas ANP
- **CICD Specialist:** Limites de memória para exports grandes (OOM)
