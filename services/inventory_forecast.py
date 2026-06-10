"""
预测性库存管理系统 - AI辅助的需求预测和库存优化
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from enum import Enum
import math

logger = logging.getLogger(__name__)


class PredictionModel(Enum):
    """预测模型"""
    MOVING_AVERAGE = "moving_average"      # 移动平均
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"  # 指数平滑
    LINEAR_REGRESSION = "linear_regression"  # 线性回归
    SEASONAL = "seasonal"                  # 季节性模型


class StockStatus(Enum):
    """库存状态"""
    SUFFICIENT = "sufficient"    # 充足
    LOW = "low"                 # 偏低
    CRITICAL = "critical"       # 危急
    OVERSTOCK = "overstock"     # 积压


class InventoryForecastSystem:
    """库存预测系统"""

    def __init__(self):
        self.historical_data: Dict[str, List[Dict]] = defaultdict(list)
        self.predictions: Dict[str, Dict] = {}
        self.alerts: List[Dict] = []

    def record_inventory_change(self, product_id: str, change_type: str,
                                quantity: int, timestamp: datetime = None):
        """记录库存变化"""
        if timestamp is None:
            timestamp = datetime.now()

        record = {
            "timestamp": timestamp.isoformat(),
            "change_type": change_type,  # 'inbound' 入库, 'outbound' 出库
            "quantity": quantity
        }

        self.historical_data[product_id].append(record)
        logger.info(f"Inventory change recorded for {product_id}: {change_type} {quantity}")

    def predict_demand(self, product_id: str, days_ahead: int = 7,
                      model: PredictionModel = PredictionModel.MOVING_AVERAGE) -> Dict:
        """预测未来需求"""
        if product_id not in self.historical_data:
            return {
                "error": "No historical data available",
                "product_id": product_id
            }

        history = self.historical_data[product_id]

        if model == PredictionModel.MOVING_AVERAGE:
            prediction = self._moving_average_prediction(history, days_ahead)
        elif model == PredictionModel.EXPONENTIAL_SMOOTHING:
            prediction = self._exponential_smoothing_prediction(history, days_ahead)
        elif model == PredictionModel.LINEAR_REGRESSION:
            prediction = self._linear_regression_prediction(history, days_ahead)
        else:
            prediction = self._moving_average_prediction(history, days_ahead)

        result = {
            "product_id": product_id,
            "model_used": model.value,
            "forecast_days": days_ahead,
            "predicted_demand": prediction,
            "confidence": self._calculate_confidence(history),
            "forecasted_at": datetime.now().isoformat()
        }

        self.predictions[product_id] = result
        return result

    def _moving_average_prediction(self, history: List[Dict], days: int) -> float:
        """移动平均预测"""
        # 计算最近30天的平均日需求
        recent_data = [
            abs(record['quantity']) for record in history[-30:]
            if record['change_type'] == 'outbound'
        ]

        if not recent_data:
            return 0.0

        daily_avg = sum(recent_data) / len(recent_data)
        return round(daily_avg * days, 2)

    def _exponential_smoothing_prediction(self, history: List[Dict], days: int,
                                         alpha: float = 0.3) -> float:
        """指数平滑预测"""
        outbound_data = [
            abs(record['quantity']) for record in history
            if record['change_type'] == 'outbound'
        ]

        if not outbound_data:
            return 0.0

        # 指数平滑
        smoothed = outbound_data[0]
        for value in outbound_data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        return round(smoothed * days, 2)

    def _linear_regression_prediction(self, history: List[Dict], days: int) -> float:
        """简单线性回归预测"""
        outbound_data = [
            (i, abs(record['quantity']))
            for i, record in enumerate(history)
            if record['change_type'] == 'outbound'
        ]

        if len(outbound_data) < 2:
            return 0.0

        # 计算斜率和截距
        n = len(outbound_data)
        sum_x = sum(x for x, _ in outbound_data)
        sum_y = sum(y for _, y in outbound_data)
        sum_xy = sum(x * y for x, y in outbound_data)
        sum_x2 = sum(x * x for x, _ in outbound_data)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n

        # 预测未来值
        future_x = n + days
        prediction = slope * future_x + intercept

        return round(max(0, prediction), 2)

    def _calculate_confidence(self, history: List[Dict]) -> float:
        """计算预测置信度"""
        if len(history) < 5:
            return 0.3

        # 基于数据量和稳定性
        data_score = min(len(history) / 100, 0.5)

        # 计算变异系数
        outbound_data = [
            abs(record['quantity']) for record in history
            if record['change_type'] == 'outbound'
        ]

        if not outbound_data or len(outbound_data) < 2:
            return data_score

        mean = sum(outbound_data) / len(outbound_data)
        variance = sum((x - mean) ** 2 for x in outbound_data) / len(outbound_data)
        std_dev = math.sqrt(variance)

        cv = std_dev / mean if mean != 0 else 1
        stability_score = max(0, 0.5 - cv * 0.1)

        return min(data_score + stability_score, 1.0)

    def calculate_reorder_point(self, product_id: str, lead_time_days: int = 7,
                               safety_stock_days: int = 3) -> Dict:
        """计算再订货点"""
        # 预测需求
        demand_forecast = self.predict_demand(product_id, lead_time_days + safety_stock_days)

        if "error" in demand_forecast:
            return demand_forecast

        predicted_demand = demand_forecast["predicted_demand"]
        daily_demand = predicted_demand / (lead_time_days + safety_stock_days)

        reorder_point = daily_demand * lead_time_days
        safety_stock = daily_demand * safety_stock_days

        return {
            "product_id": product_id,
            "reorder_point": round(reorder_point, 2),
            "safety_stock": round(safety_stock, 2),
            "daily_demand_estimate": round(daily_demand, 2),
            "lead_time_days": lead_time_days,
            "calculated_at": datetime.now().isoformat()
        }

    def optimize_order_quantity(self, product_id: str, holding_cost: float = 1.0,
                               order_cost: float = 50.0) -> Dict:
        """优化订货批量（经济订货量模型 EOQ）"""
        # 预测年需求
        annual_forecast = self.predict_demand(product_id, days_ahead=365)

        if "error" in annual_forecast:
            return annual_forecast

        annual_demand = annual_forecast["predicted_demand"]

        if annual_demand <= 0:
            return {
                "error": "Invalid demand forecast",
                "product_id": product_id
            }

        # EOQ公式: sqrt(2 * D * S / H)
        # D = 年需求, S = 订货成本, H = 持有成本
        eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost)

        # 计算相关指标
        order_frequency = annual_demand / eoq  # 年订货次数
        total_cost = (annual_demand / eoq) * order_cost + (eoq / 2) * holding_cost

        return {
            "product_id": product_id,
            "economic_order_quantity": round(eoq, 2),
            "annual_demand_forecast": round(annual_demand, 2),
            "optimal_order_frequency": round(order_frequency, 2),
            "estimated_annual_cost": round(total_cost, 2),
            "holding_cost_per_unit": holding_cost,
            "order_cost": order_cost,
            "calculated_at": datetime.now().isoformat()
        }

    def analyze_current_stock(self, product_id: str, current_quantity: int) -> Dict:
        """分析当前库存状态"""
        # 计算再订货点
        reorder_info = self.calculate_reorder_point(product_id)

        if "error" in reorder_info:
            return reorder_info

        reorder_point = reorder_info["reorder_point"]
        safety_stock = reorder_info["safety_stock"]

        # 预测7天需求
        forecast = self.predict_demand(product_id, days_ahead=7)
        weekly_demand = forecast.get("predicted_demand", 0)

        # 计算库存天数
        daily_demand = reorder_info["daily_demand_estimate"]
        days_of_stock = current_quantity / daily_demand if daily_demand > 0 else 999

        # 判断状态
        if current_quantity <= safety_stock:
            status = StockStatus.CRITICAL
            recommendation = "立即订货！库存已低于安全库存"
        elif current_quantity <= reorder_point:
            status = StockStatus.LOW
            recommendation = "建议订货，已达到再订货点"
        elif days_of_stock > 60:
            status = StockStatus.OVERSTOCK
            recommendation = "库存积压，建议促销或减少订货"
        else:
            status = StockStatus.SUFFICIENT
            recommendation = "库存正常"

        return {
            "product_id": product_id,
            "current_quantity": current_quantity,
            "status": status.value,
            "days_of_stock": round(days_of_stock, 1),
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "weekly_demand_forecast": weekly_demand,
            "recommendation": recommendation,
            "analyzed_at": datetime.now().isoformat()
        }

    def generate_inventory_alerts(self, inventory_levels: Dict[str, int]) -> List[Dict]:
        """生成库存预警"""
        alerts = []

        for product_id, current_qty in inventory_levels.items():
            analysis = self.analyze_current_stock(product_id, current_qty)

            if "error" in analysis:
                continue

            status = analysis["status"]

            if status == StockStatus.CRITICAL.value:
                alerts.append({
                    "priority": "high",
                    "product_id": product_id,
                    "message": f"危急：{product_id} 库存仅剩 {current_qty}，低于安全库存",
                    "recommendation": analysis["recommendation"],
                    "created_at": datetime.now().isoformat()
                })
            elif status == StockStatus.LOW.value:
                alerts.append({
                    "priority": "medium",
                    "product_id": product_id,
                    "message": f"偏低：{product_id} 库存 {current_qty}，已达再订货点",
                    "recommendation": analysis["recommendation"],
                    "created_at": datetime.now().isoformat()
                })
            elif status == StockStatus.OVERSTOCK.value:
                alerts.append({
                    "priority": "low",
                    "product_id": product_id,
                    "message": f"积压：{product_id} 库存 {current_qty}，可供应 {analysis['days_of_stock']:.1f} 天",
                    "recommendation": analysis["recommendation"],
                    "created_at": datetime.now().isoformat()
                })

        self.alerts = alerts
        return alerts

    def get_inventory_dashboard(self, inventory_levels: Dict[str, int]) -> Dict:
        """生成库存仪表板"""
        dashboard = {
            "total_products": len(inventory_levels),
            "status_summary": {
                "critical": 0,
                "low": 0,
                "sufficient": 0,
                "overstock": 0
            },
            "products": [],
            "alerts": [],
            "generated_at": datetime.now().isoformat()
        }

        for product_id, current_qty in inventory_levels.items():
            analysis = self.analyze_current_stock(product_id, current_qty)

            if "error" not in analysis:
                status = analysis["status"]
                dashboard["status_summary"][status] += 1

                dashboard["products"].append({
                    "product_id": product_id,
                    "current_quantity": current_qty,
                    "status": status,
                    "days_of_stock": analysis["days_of_stock"]
                })

        # 生成预警
        dashboard["alerts"] = self.generate_inventory_alerts(inventory_levels)

        return dashboard

    def simulate_inventory_scenario(self, product_id: str, current_qty: int,
                                   daily_demand: float, days: int = 30) -> Dict:
        """模拟库存场景"""
        simulation = {
            "product_id": product_id,
            "starting_quantity": current_qty,
            "daily_demand": daily_demand,
            "simulation_days": days,
            "daily_levels": [],
            "stockout_day": None,
            "recommendations": []
        }

        qty = current_qty

        for day in range(1, days + 1):
            qty -= daily_demand

            simulation["daily_levels"].append({
                "day": day,
                "quantity": round(qty, 2)
            })

            if qty <= 0 and simulation["stockout_day"] is None:
                simulation["stockout_day"] = day
                simulation["recommendations"].append(
                    f"预计在第 {day} 天发生缺货，建议提前 {day - 7} 天订货"
                )
                break

        if simulation["stockout_day"] is None:
            simulation["recommendations"].append(
                f"库存可支撑 {days} 天以上，状态良好"
            )

        return simulation


# 全局库存预测系统实例
inventory_forecast = InventoryForecastSystem()


__all__ = ['InventoryForecastSystem', 'PredictionModel', 'StockStatus', 'inventory_forecast']
