#!/usr/bin/env python3
"""
AgriBot-Retrofit - Mission Generator Mock

Gera missões completas de navegação para robôs em campo
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from shapefile_importer_mock import PrescriptionImporter
from waypoint_converter_mock import WaypointConverter


class MissionGenerator:
    """Gera missões de navegação completas para AgriBot"""
    
    def __init__(self):
        self.importer = PrescriptionImporter()
        self.converter = WaypointConverter(swath_width_m=5.0)
    
    def generate_mission(self, prescription_file: str) -> Dict:
        """
        Gera missão completa a partir de arquivo de prescrição
        
        Args:
            prescription_file: Caminho para arquivo GeoJSON de prescrição
        
        Returns:
            Dicionário com missão completa
        """
        # 1. Importar prescrição
        print("📥 PASSO 1: Importando prescrição...")
        prescription = self.importer.load_from_file(prescription_file)
        
        if not self.importer.validate_prescription():
            raise ValueError("Prescrição inválida")
        
        # 2. Obter zonas
        print("\n📊 PASSO 2: Processando zonas...")
        zones = self.importer.get_zones_summary()
        
        # 3. Converter cada zona em waypoints
        print("\n🗺️  PASSO 3: Gerando waypoints...")
        zone_missions = []
        
        for zone in zones:
            print(f"\n   Processando ZONA {zone['zone_id']}...")
            
            polygon_coords = zone['geometry']['coordinates'][0]
            waypoints = self.converter.polygon_to_boustrophedon(polygon_coords)
            coverage_ha = self.converter.calculate_coverage_area(waypoints)
            
            zone_mission = {
                'zone_id': zone['zone_id'],
                'zone_area_ha': zone['area_ha'],
                'action': zone['action'],
                'priority': zone['priority'],
                'product_rate_kg_ha': zone.get('product_rate_kg_ha', 0),
                'waypoints': waypoints,
                'stats': {
                    'num_waypoints': len(waypoints),
                    'num_lines': max(wp['line_number'] for wp in waypoints) + 1,
                    'coverage_ha': round(coverage_ha, 2),
                    'estimated_duration_min': len(waypoints) * 2  # 2 min por waypoint
                }
            }
            
            zone_missions.append(zone_mission)
            
            print(f"      ✅ {len(waypoints)} waypoints")
            print(f"      ✅ {zone_mission['stats']['num_lines']} linhas")
            print(f"      ✅ ~{zone_mission['stats']['estimated_duration_min']} min")
        
        # 4. Montar missão completa
        mission = {
            'mission_id': f"AGR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'prescription_id': prescription['prescription_id'],
            'field_id': prescription['field_id'],
            'generated_at': datetime.now().isoformat(),
            'status': 'ready',
            'zone_missions': zone_missions,
            'metadata': {
                'total_zones': len(zone_missions),
                'total_waypoints': sum(len(zm['waypoints']) for zm in zone_missions),
                'total_area_ha': sum(zm['zone_area_ha'] for zm in zone_missions),
                'estimated_total_duration_min': sum(zm['stats']['estimated_duration_min'] for zm in zone_missions)
            }
        }
        
        return mission
    
    def save_mission(self, mission: Dict, output_file: str):
        """Salva missão em arquivo JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mission, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Missão salva em: {output_file}")
    
    def print_mission_summary(self, mission: Dict):
        """Exibe resumo da missão gerada"""
        print("\n" + "="*60)
        print("📋 RESUMO DA MISSÃO GERADA")
        print("="*60)
        
        print(f"\n🆔 Mission ID: {mission['mission_id']}")
        print(f"   Prescription: {mission['prescription_id']}")
        print(f"   Field: {mission['field_id']}")
        print(f"   Status: {mission['status'].upper()}")
        
        print(f"\n📊 ESTATÍSTICAS:")
        meta = mission['metadata']
        print(f"   Zonas: {meta['total_zones']}")
        print(f"   Waypoints: {meta['total_waypoints']}")
        print(f"   Área total: {meta['total_area_ha']} ha")
        print(f"   Duração estimada: {meta['estimated_total_duration_min']} minutos "
              f"({meta['estimated_total_duration_min']/60:.1f} horas)")
        
        print(f"\n🗺️  ZONAS:")
        for zm in mission['zone_missions']:
            print(f"\n   ZONA {zm['zone_id']} ({zm['action'].upper()}, prioridade {zm['priority']})")
            print(f"      Área: {zm['zone_area_ha']} ha")
            print(f"      Waypoints: {zm['stats']['num_waypoints']}")
            print(f"      Linhas: {zm['stats']['num_lines']}")
            print(f"      Duração: ~{zm['stats']['estimated_duration_min']} min")
            
            if zm['product_rate_kg_ha'] > 0:
                total_product_kg = zm['zone_area_ha'] * zm['product_rate_kg_ha']
                print(f"      Produto: {total_product_kg:.1f} kg ({zm['product_rate_kg_ha']} kg/ha)")


if __name__ == "__main__":
    print("🤖 AgriBot-Retrofit - Gerador de Missões Mock\n")
    print("="*60)
    print("\n🎯 TESTANDO INTEGRAÇÃO PRECISION → AGRIBOT\n")
    
    # Gera missão a partir da prescrição do Precision
    generator = MissionGenerator()
    
    prescription_file = Path(__file__).parent / "example_prescription.json"
    
    try:
        mission = generator.generate_mission(str(prescription_file))
        
        # Exibe resumo
        generator.print_mission_summary(mission)
        
        # Salva missão
        output_file = Path(__file__).parent / f"mission_{mission['mission_id']}.json"
        generator.save_mission(mission, str(output_file))
        
        print("\n" + "="*60)
        print("🎉 INTEGRAÇÃO PRECISION → AGRIBOT: SUCESSO")
        print("="*60)
        print("\n✅ Prescrição do Precision importada")
        print("✅ Polígonos convertidos em waypoints")
        print("✅ Missão de navegação gerada")
        print("✅ Pronta para envio aos robôs em campo")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
