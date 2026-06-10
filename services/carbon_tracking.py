"""
碳足迹追踪系统 - 记录和分析供应链各环节的碳排放
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class EmissionSource(Enum):
    """碳排放来源"""
    PRODUCTION = "production"        # 生产制造
    TRANSPORTATION = "transportation"  # 运输物流
    STORAGE = "storage"              # 仓储存储
    PACKAGING = "packaging"          # 包装材料
    ENERGY = "energy"                # 能源消耗


class CarbonFootprint:
    """碳足迹记录"""

    def __init__(self, record_id: str, product_id: str, source: EmissionSource,
                 emission_kg: float, details: Dict):
        self.record_id = record_id
        self.product_id = product_id
        self.source = source
        self.emission_kg = emission_kg  # 碳排放量（千克CO2当量）
        self.details = details
        self.recorded_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "record_id": self.record_id,
            "product_id": self.product_id,
            "source": self.source.value,
            "emission_kg": self.emission_kg,
            "details": self.details,
            "recorded_at": self.recorded_at.isoformat()
        }


class CarbonTrackingSystem:
    """碳足迹追踪系统"""

    # 标准碳排放系数（kg CO2/单位）
    EMISSION_FACTORS = {
        "electricity_kwh": 0.5,      # 每度电
        "diesel_liter": 2.7,         # 每升柴油
        "gasoline_liter": 2.3,       # 每升汽油
        "natural_gas_m3": 2.0,       # 每立方米天然气
        "paper_kg": 0.9,             # 每千克纸张
        "plastic_kg": 6.0,           # 每千克塑料
        "transport_km": 0.15         # 每公里运输（货车）
    }

    def __init__(self):
        self.footprint_records: Dict[str, List[CarbonFootprint]] = defaultdict(list)

    def record_production_emission(self, product_id: str, energy_kwh: float,
                                   materials: Dict[str, float]) -> CarbonFootprint:
        """记录生产环节的碳排放"""
        emission = 0.0
        details = {"energy_kwh": energy_kwh, "materials": materials}

        # 能源消耗
        emission += energy_kwh * self.EMISSION_FACTORS["electricity_kwh"]

        # 材料消耗
        for material, amount_kg in materials.items():
            factor_key = f"{material}_kg"
            if factor_key in self.EMISSION_FACTORS:
                emission += amount_kg * self.EMISSION_FACTORS[factor_key]

        record_id = f"prod_{product_id}_{int(datetime.now().timestamp())}"
        footprint = CarbonFootprint(
            record_id, product_id, EmissionSource.PRODUCTION, emission, details
        )

        self.footprint_records[product_id].append(footprint)
        logger.info(f"Production emission recorded: {emission:.2f} kg CO2 for {product_id}")

        return footprint

    def record_transportation_emission(self, product_id: str, distance_km: float,
                                      vehicle_type: str = "truck", fuel_liters: float = None) -> CarbonFootprint:
        """记录运输环节的碳排放"""
        details = {"distance_km": distance_km, "vehicle_type": vehicle_type}

        if fuel_liters:
            # 基于实际燃料消耗
            factor = self.EMISSION_FACTORS.get(f"{vehicle_type}_liter", 2.5)
            emission = fuel_liters * factor
            details["fuel_liters"] = fuel_liters
        else:
            # 基于距离估算
            emission = distance_km * self.EMISSION_FACTORS["transport_km"]

        record_id = f"trans_{product_id}_{int(datetime.now().timestamp())}"
        footprint = CarbonFootprint(
            record_id, product_id, EmissionSource.TRANSPORTATION, emission, details
        )

        self.footprint_records[product_id].append(footprint)
        logger.info(f"Transportation emission recorded: {emission:.2f} kg CO2 for {product_id}")

        return footprint

    def record_storage_emission(self, product_id: str, storage_days: int,
                               facility_energy_kwh_per_day: float) -> CarbonFootprint:
        """记录仓储环节的碳排放"""
        emission = storage_days * facility_energy_kwh_per_day * self.EMISSION_FACTORS["electricity_kwh"]

        details = {
            "storage_days": storage_days,
            "facility_energy_kwh_per_day": facility_energy_kwh_per_day
        }

        record_id = f"stor_{product_id}_{int(datetime.now().timestamp())}"
        footprint = CarbonFootprint(
            record_id, product_id, EmissionSource.STORAGE, emission, details
        )

        self.footprint_records[product_id].append(footprint)
        logger.info(f"Storage emission recorded: {emission:.2f} kg CO2 for {product_id}")

        return footprint

    def record_packaging_emission(self, product_id: str, packaging_materials: Dict[str, float]) -> CarbonFootprint:
        """记录包装环节的碳排放"""
        emission = 0.0
        details = {"materials": packaging_materials}

        for material, amount_kg in packaging_materials.items():
            factor_key = f"{material}_kg"
            if factor_key in self.EMISSION_FACTORS:
                emission += amount_kg * self.EMISSION_FACTORS[factor_key]

        record_id = f"pack_{product_id}_{int(datetime.now().timestamp())}"
        footprint = CarbonFootprint(
            record_id, product_id, EmissionSource.PACKAGING, emission, details
        )

        self.footprint_records[product_id].append(footprint)
        logger.info(f"Packaging emission recorded: {emission:.2f} kg CO2 for {product_id}")

        return footprint

    def get_product_total_emission(self, product_id: str) -> Dict:
        """获取产品的总碳排放"""
        if product_id not in self.footprint_records:
            return {
                "product_id": product_id,
                "total_emission_kg": 0.0,
                "breakdown": {},
                "records": []
            }

        records = self.footprint_records[product_id]
        total = sum(r.emission_kg for r in records)

        # 按来源分类统计
        breakdown = defaultdict(float)
        for record in records:
            breakdown[record.source.value] += record.emission_kg

        return {
            "product_id": product_id,
            "total_emission_kg": round(total, 2),
            "breakdown": dict(breakdown),
            "records": [r.to_dict() for r in records],
            "record_count": len(records)
        }

    def compare_products(self, product_ids: List[str]) -> Dict:
        """比较多个产品的碳足迹"""
        comparison = []

        for product_id in product_ids:
            emission_data = self.get_product_total_emission(product_id)
            comparison.append({
                "product_id": product_id,
                "total_emission": emission_data["total_emission_kg"],
                "breakdown": emission_data["breakdown"]
            })

        # 排序（从高到低）
        comparison.sort(key=lambda x: x["total_emission"], reverse=True)

        avg_emission = sum(p["total_emission"] for p in comparison) / len(comparison) if comparison else 0

        return {
            "products": comparison,
            "average_emission": round(avg_emission, 2),
            "highest_emitter": comparison[0]["product_id"] if comparison else None,
            "lowest_emitter": comparison[-1]["product_id"] if comparison else None
        }

    def get_emission_by_source(self, source: EmissionSource = None) -> Dict:
        """按排放源统计"""
        stats = defaultdict(lambda: {"total_emission": 0.0, "record_count": 0})

        for product_id, records in self.footprint_records.items():
            for record in records:
                if source is None or record.source == source:
                    key = record.source.value
                    stats[key]["total_emission"] += record.emission_kg
                    stats[key]["record_count"] += 1

        return dict(stats)

    def generate_carbon_report(self, product_id: str = None) -> Dict:
        """生成碳排放报告"""
        if product_id:
            # 单个产品报告
            emission_data = self.get_product_total_emission(product_id)
            recommendations = self._generate_reduction_recommendations(emission_data)

            return {
                "report_type": "product",
                "product_id": product_id,
                "emission_data": emission_data,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat()
            }
        else:
            # 全局报告
            all_products = list(self.footprint_records.keys())
            total_emission = sum(
                sum(r.emission_kg for r in records)
                for records in self.footprint_records.values()
            )

            by_source = self.get_emission_by_source()

            return {
                "report_type": "global",
                "total_products": len(all_products),
                "total_emission_kg": round(total_emission, 2),
                "emission_by_source": by_source,
                "average_per_product": round(total_emission / len(all_products), 2) if all_products else 0,
                "generated_at": datetime.now().isoformat()
            }

    def _generate_reduction_recommendations(self, emission_data: Dict) -> List[str]:
        """生成减排建议"""
        recommendations = []
        breakdown = emission_data.get("breakdown", {})

        # 针对最大排放源给出建议
        if breakdown:
            max_source = max(breakdown.items(), key=lambda x: x[1])
            source_name, source_emission = max_source

            if source_name == "production":
                recommendations.append("生产环节排放最高，建议采用节能设备或可再生能源")
            elif source_name == "transportation":
                recommendations.append("运输环节排放最高，建议优化物流路线或使用低碳运输方式")
            elif source_name == "packaging":
                recommendations.append("包装环节排放最高，建议使用可降解或可回收材料")
            elif source_name == "storage":
                recommendations.append("仓储环节排放最高，建议优化温控系统或改善建筑保温")

        total = emission_data.get("total_emission_kg", 0)
        if total > 100:
            recommendations.append("总体碳排放较高，建议考虑购买碳抵消或实施碳中和计划")

        return recommendations

    def get_carbon_certificate(self, product_id: str) -> Dict:
        """生成碳足迹证书"""
        emission_data = self.get_product_total_emission(product_id)

        # 评级（基于总排放量）
        total = emission_data["total_emission_kg"]
        if total < 10:
            rating = "A+"
            label = "极低碳"
        elif total < 30:
            rating = "A"
            label = "低碳"
        elif total < 50:
            rating = "B"
            label = "中等碳排放"
        elif total < 100:
            rating = "C"
            label = "较高碳排放"
        else:
            rating = "D"
            label = "高碳排放"

        return {
            "product_id": product_id,
            "total_emission_kg": emission_data["total_emission_kg"],
            "rating": rating,
            "label": label,
            "breakdown": emission_data["breakdown"],
            "certificate_id": f"CARBON_{product_id}_{int(datetime.now().timestamp())}",
            "issued_at": datetime.now().isoformat()
        }


# 全局碳追踪系统实例
carbon_tracker = CarbonTrackingSystem()


__all__ = ['CarbonTrackingSystem', 'CarbonFootprint', 'EmissionSource', 'carbon_tracker']
