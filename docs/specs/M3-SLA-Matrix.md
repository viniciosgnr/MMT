# M3 Periodic Analyses SLA Matrix

Esta matriz representa a "Lei" de prazos para amostragens periódicas, guiando as datas previstas (`due_date`) e os tetos (SLAs) para alertas.

| Classification | Type | Local | Intervalo | Disembark | Laboratory | Report | Validação | FC (Flow Computer) | Obs. |
|---|---|---|---|---|---|---|---|---|---|
| Fiscal | Chromatography | Onshore | 30 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Aprovado | 3 dias úteis após a emissão | |
| Fiscal | Chromatography | Onshore | 30 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Reprovado | NA | A data de coleta tem que ser 3 dias úteis após a emissão do relatório devidamente reprovado ou a data prevista mantém se menor |
| Fiscal | Chromatography | Offshore | 30 dias | NA | NA | 25 dias após a coleta | Aprovado | 3 dias úteis após a emissão | |
| Fiscal | Chromatography | Offshore | 30 dias | NA | NA | 25 dias após a coleta | Reprovado | NA | Mesma regra de reprovação acima |
| Apropriation | Chromatography | Onshore | 90 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Aprovado | 3 dias úteis após a emissão | |
| Apropriation | Chromatography | Onshore | 90 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Reprovado | NA | Mesma regra de reprovação acima |
| Apropriation | Chromatography | Offshore | 90 dias | NA | NA | 25 dias após a coleta | Aprovado | 3 dias úteis após a emissão | |
| Apropriation | Chromatography | Offshore | 90 dias | NA | NA | 25 dias após a coleta | Reprovado | NA | Mesma regra de reprovação acima |
| Operational | Chromatography | Onshore | 180 dias | 10 dias após a coleta | 20 dias após a coleta | 45 dias após a coleta | Aprovado | 10 dias úteis após a emissão | |
| Operational | Chromatography | Onshore | 180 dias | 10 dias após a coleta | 20 dias após a coleta | 45 dias após a coleta | Reprovado | NA | |
| Operational | Chromatography | Offshore | 180 dias | NA | NA | 45 dias após a coleta | Aprovado | 10 dias úteis após a emissão | |
| Operational | Chromatography | Offshore | 180 dias | NA | NA | 45 dias após a coleta | Reprovado | NA | |
| Apropriation | PVT | Onshore | 90 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Aprovado | NA | |
| Apropriation | PVT | Onshore | 90 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | Reprovado | NA | |
| Apropriation | PVT | Offshore | 90 dias | NA | NA | 25 dias após a coleta | Aprovado | NA | |
| Apropriation | PVT | Offshore | 90 dias | NA | NA | 25 dias após a coleta | Reprovado | NA | |
| Fiscal | Enxofre | Onshore | 365 dias | 10 dias após a coleta | 20 dias após a coleta | 25 dias após a coleta | NA | NA | |
| Fiscal | Enxofre | Offshore | 365 dias | NA | NA | 25 dias após a coleta | NA | NA | |
| Fiscal | Viscosity | Onshore | 365 dias | 10 dias após a coleta | 20 dias após a coleta | 45 dias após a coleta | NA | NA | |
| Fiscal | Viscosity | Offshore | 365 dias | NA | NA | 45 dias após a coleta | NA | NA | |
| Custody Transfer | Viscosity | Onshore | 365 dias | 10 dias após a coleta | 20 dias após a coleta | 45 dias após a coleta | NA | NA | |
| Custody Transfer | Viscosity | Offshore | 365 dias | NA | NA | 45 dias após a coleta | NA | NA | |

*Nota sobre a Reprovação:* 
Independentemente se o Status Final for "Validação: Reprovado" para Cromatografia T0 On/Off, o Flow Computer não é atualizado (`NA`), e aciona-se compulsoriamente a emergência de reagendamento para 3 dias úteis a menos que o intervalo natural vença antes.
