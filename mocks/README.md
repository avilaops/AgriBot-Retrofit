# CONTRATO: AgriBot-Retrofit

## ✅ CONTRATO DEFINIDO E TESTADO

### 🎯 O que este projeto RECEBE

**De:** Precision-Agriculture-Platform

**Via:** GeoJSON export (ou Shapefile convertido)

**Formato:** JSON com geometrias de zonas + prescrições VRA

**Frequência:** Sob demanda (quando prescrição é aprovada no dashboard)

### Input Structure (GeoJSON):

```json
{
  "prescription_id": "VRA-20260220-001",
  "field_id": "F001-UsinaGuarani-Piracicaba",
  "prescription_type": "variable_rate_reform",
  "zones": [
    {
      "zone_id": "Z001",
      "area_ha": 50.2,
      "action": "reform",
      "priority": "high",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-47.6234, -22.7123], ...]]
      }
    },
    {
      "zone_id": "Z002",
      "action": "maintain",
      "product_rate_kg_ha": 150,
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-47.6198, -22.7123], ...]]
      }
    }
  ]
}
```

---

### 🎯 O que este projeto PRODUZ

**Para:** CanaSwarm-MicroBot (robôs em campo)

**Processa:**
1.  Importa prescrições de aplicação variável (VRA)
2. Converte polígonos de zonas em waypoints de navegação
3. Gera padrão Boustrophedon (linhas paralelas vai-e-vem)
4. Calcula cobertura e duração estimada
5. Define taxas de aplicação por zona

**Output:**

```json
{
  "mission_id": "AGR-20260220-150000",
  "prescription_id": "VRA-20260220-001",
  "zone_missions": [
    {
      "zone_id": "Z001",
      "zone_area_ha": 50.2,
      "action": "reform",
      "priority": "high",
      "waypoints": [
        {
          "lat": -22.7089,
          "lon": -47.6234,
          "velocity_m_s": 1.5,
          "action": "start_line",
          "line_number": 0
        },
        ...
      ],
      "stats": {
        "num_waypoints": 40,
        "num_lines": 20,
        "coverage_ha": 50.1,
        "estimated_duration_min": 80
      }
    }
  ],
  "metadata": {
    "total_zones": 2,
    "total_waypoints": 80,
    "total_area_ha": 130,
    "estimated_total_duration_min": 160
  }
}
```

---

## ✅ INTEGRAÇÃO TESTADA

**Data:** 20/02/2026

**Resultado:** ✅ AgriBot importou prescrição do Precision, converteu polígonos em waypoints, gerou missão completa

**Evidência:**
- Mock implementado: `AgriBot-Retrofit/mocks/`
- Importador: `shapefile_importer_mock.py`
- Conversor: `waypoint_converter_mock.py`
- Gerador: `mission_generator_mock.py`
- Dados teste: `example_prescription.json` (baseado no output do Precision)

**Como testar:**
```bash
cd AgriBot-Retrofit/mocks

# Teste 1: Importar prescrição
python shapefile_importer_mock.py

# Teste 2: Converter waypoints
python waypoint_converter_mock.py

# Teste 3: Gerar missão completa
python mission_generator_mock.py
```

**Output esperado:**
```
🤖 AgriBot-Retrofit - Gerador de Missões Mock

🎯 TESTANDO INTEGRAÇÃO PRECISION → AGRIBOT

📥 PASSO 1: Importando prescrição...
✅ Prescrição carregada: VRA-20260220-001
   Field: F001-UsinaGuarani-Piracicaba
   Zonas: 2
   Área total: 130 ha

📊 PASSO 2: Processando zonas...
✅ Prescrição válida

🗺️  PASSO 3: Gerando waypoints...
   Processando ZONA Z001...
      ✅ 40 waypoints
      ✅ 20 linhas
      ✅ ~80 min

   Processando ZONA Z002...
      ✅ 40 waypoints
      ✅ 20 linhas
      ✅ ~80 min

📋 RESUMO DA MISSÃO GERADA
🆔 Mission ID: AGR-20260220-150808
   Status: READY

📊 ESTATÍSTICAS:
   Zonas: 2
   Waypoints: 80
   Área total: 130 ha
   Duração estimada: 160 minutos (2.7 horas)

🎉 INTEGRAÇÃO PRECISION → AGRIBOT: SUCESSO

✅ Prescrição do Precision importada
✅ Polígonos convertidos em waypoints
✅ Missão de navegação gerada
✅ Pronta para envio aos robôs em campo
```

---

## 📋 Critério de Sucesso

- [x] Contrato de entrada definido (GeoJSON)
- [x] Importador de prescrições implementado (`shapefile_importer_mock.py`)
- [x] Conversor de polígonos para waypoints (`waypoint_converter_mock.py`)
- [x] Algoritmo Boustrophedon (linhas paralelas)
- [x] Gerador de missões completas (`mission_generator_mock.py`)
- [x] Dados de teste com prescrição do Precision
- [x] Missão salva em JSON

---

## 🔗 Referências

- [Mock Files](https://github.com/avilaops/AgriBot-Retrofit/tree/main/mocks)
- [DEPENDENCY-CONTROL.md](https://github.com/avilaops/agro-tech-ecosystem/blob/main/DEPENDENCY-CONTROL.md)
- [Precision-Platform Integration](https://github.com/avilaops/Precision-Agriculture-Platform/tree/main/mocks)

**Status:** ✅ CONTRATO VALIDADO — Pipeline Precision → AgriBot FUNCIONA

---

## 🚀 Próximos Passos

1. Substituir mock por código real (shapely para geometrias, rospy para ROS)
2. Implementar interface ROS para comunicação com MicroBots
3. Adicionar validação de geometrias (polígonos inválidos, auto-interseção)
4. Otimizar geração de waypoints (evitar áreas já cobertas)
5. Implementar telemetria em tempo real (área coberta, produto aplicado)
