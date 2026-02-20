#!/usr/bin/env python3
"""
AgriBot-Retrofit - Waypoint Converter Mock

Converte polígonos de zonas em waypoints para navegação
"""

import json
import math
from typing import List, Dict, Tuple


class WaypointConverter:
    """Converte polígonos em waypoints de navegação"""
    
    def __init__(self, swath_width_m: float = 5.0):
        """
        Args:
            swath_width_m: Largura da faixa de trabalho em metros (default: 5m)
        """
        self.swath_width_m = swath_width_m
    
    def polygon_to_boustrophedon(self, polygon_coords: List[List[float]]) -> List[Dict]:
        """
        Converte polígono em padrão boustrophedon (vai-e-vem paralelo)
        
        Args:
            polygon_coords: Lista de coordenadas [lon, lat]
        
        Returns:
            Lista de waypoints com [lon, lat, velocidade_m_s]
        """
        # Calcula bounding box do polígono
        lons = [coord[0] for coord in polygon_coords]
        lats = [coord[1] for coord in polygon_coords]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Converte swath_width de metros para graus (aproximado)
        # 1 grau lat ≈ 111km, 1 grau lon ≈ 111km * cos(lat)
        avg_lat = (min_lat + max_lat) / 2
        swath_deg_lat = self.swath_width_m / 111000
        
        # Gera linhas paralelas no eixo lat
        waypoints = []
        current_lat = min_lat + swath_deg_lat / 2
        direction = 1  # 1 = esquerda->direita, -1 = direita->esquerda
        line_num = 0
        
        while current_lat < max_lat:
            if direction == 1:
                # Esquerda para direita
                start_lon, end_lon = min_lon, max_lon
            else:
                # Direita para esquerda
                start_lon, end_lon = max_lon, min_lon
            
            waypoints.append({
                'lat': current_lat,
                'lon': start_lon,
                'velocity_m_s': 1.5,  # Velocidade de trabalho
                'action': 'start_line',
                'line_number': line_num
            })
            
            waypoints.append({
                'lat': current_lat,
                'lon': end_lon,
                'velocity_m_s': 1.5,
                'action': 'end_line',
                'line_number': line_num
            })
            
            current_lat += swath_deg_lat
            direction *= -1
            line_num += 1
        
        return waypoints
    
    def calculate_coverage_area(self, waypoints: List[Dict]) -> float:
        """Calcula área coberta pelos waypoints em hectares"""
        if len(waypoints) < 4:
            return 0.0
        
        # Número de linhas
        num_lines = max(wp['line_number'] for wp in waypoints) + 1
        
        # Comprimento médio das linhas
        line_lengths_m = []
        for i in range(0, len(waypoints), 2):
            if i + 1 < len(waypoints):
                wp1, wp2 = waypoints[i], waypoints[i + 1]
                dist_m = self._haversine_distance(
                    wp1['lat'], wp1['lon'],
                    wp2['lat'], wp2['lon']
                )
                line_lengths_m.append(dist_m)
        
        avg_length_m = sum(line_lengths_m) / len(line_lengths_m) if line_lengths_m else 0
        
        # Área = número de linhas * largura da faixa * comprimento médio
        area_m2 = num_lines * self.swath_width_m * avg_length_m
        area_ha = area_m2 / 10000
        
        return area_ha
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos em metros (Haversine)"""
        R = 6371000  # Raio da Terra em metros
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


if __name__ == "__main__":
    print("🤖 AgriBot-Retrofit - Conversor de Waypoints Mock\n")
    print("="*60)
    
    # Carrega prescrição
    from shapefile_importer_mock import PrescriptionImporter
    from pathlib import Path
    
    importer = PrescriptionImporter()
    prescription_file = Path(__file__).parent / "example_prescription.json"
    prescription = importer.load_from_file(str(prescription_file))
    
    zones = importer.get_zones_summary()
    
    # Converte cada zona em waypoints
    converter = WaypointConverter(swath_width_m=5.0)
    
    all_missions = []
    
    for zone in zones:
        print(f"\n🗺️  Convertendo ZONA {zone['zone_id']}...")
        print(f"   Ação: {zone['action'].upper()}")
        
        polygon_coords = zone['geometry']['coordinates'][0]
        waypoints = converter.polygon_to_boustrophedon(polygon_coords)
        
        # Calcula estatísticas
        coverage_ha = converter.calculate_coverage_area(waypoints)
        num_lines = max(wp['line_number'] for wp in waypoints) + 1
        
        print(f"   ✅ {len(waypoints)} waypoints gerados")
        print(f"   ✅ {num_lines} linhas paralelas")
        print(f"   ✅ Cobertura estimada: {coverage_ha:.2f} ha")
        
        mission = {
            'zone_id': zone['zone_id'],
            'zone_area_ha': zone['area_ha'],
            'action': zone['action'],
            'priority': zone['priority'],
            'waypoints': waypoints,
            'stats': {
                'num_waypoints': len(waypoints),
                'num_lines': num_lines,
                'coverage_ha': round(coverage_ha, 2),
                'swath_width_m': converter.swath_width_m
            }
        }
        
        all_missions.append(mission)
    
    print(f"\n✅ CONVERSÃO CONCLUÍDA")
    print(f"   {len(all_missions)} missões prontas para execução")
    print(f"   Total de waypoints: {sum(len(m['waypoints']) for m in all_missions)}")
