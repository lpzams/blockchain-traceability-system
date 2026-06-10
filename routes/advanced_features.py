"""
新功能API路由 - 智能合约、召回、碳追踪、审计、库存预测
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps

# 导入新功能模块
from services.smart_contract import (
    contract_engine, QualityCheckContract, TransferApprovalContract,
    ContractStatus, RuleType
)
from services.recall_system import recall_system, RecallSeverity, RecallStatus
from services.carbon_tracking import carbon_tracker, EmissionSource
from services.blockchain_audit import audit_system, ExportFormat, AuditLevel
from services.inventory_forecast import inventory_forecast, PredictionModel, StockStatus

# 创建蓝图
advanced_features_bp = Blueprint('advanced_features', __name__, url_prefix='/api/advanced')


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "未登录"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== 智能合约相关 ====================

@advanced_features_bp.route('/contracts', methods=['GET'])
@login_required
def list_contracts():
    """列出所有活跃合约"""
    contracts = contract_engine.list_active_contracts()
    return jsonify({"contracts": contracts})


@advanced_features_bp.route('/contracts/quality-check', methods=['POST'])
@login_required
def create_quality_check_contract():
    """创建质检自动审批合约"""
    data = request.json
    contract_id = data.get('contract_id')
    min_score = data.get('min_score', 80.0)

    contract = QualityCheckContract(contract_id, min_score)
    contract_engine.register_contract(contract)

    return jsonify({
        "message": "质检合约创建成功",
        "contract": contract_engine.get_contract_status(contract_id)
    })


@advanced_features_bp.route('/contracts/transfer-approval', methods=['POST'])
@login_required
def create_transfer_approval_contract():
    """创建转移审批合约"""
    data = request.json
    contract_id = data.get('contract_id')
    allowed_parties = data.get('allowed_parties', [])
    max_value = data.get('max_value')

    contract = TransferApprovalContract(contract_id, allowed_parties, max_value)
    contract_engine.register_contract(contract)

    return jsonify({
        "message": "转移审批合约创建成功",
        "contract": contract_engine.get_contract_status(contract_id)
    })


@advanced_features_bp.route('/contracts/<contract_id>/execute', methods=['POST'])
@login_required
def execute_contract(contract_id):
    """执行合约"""
    context = request.json
    result = contract_engine.execute_contract(contract_id, context)

    return jsonify({"result": result})


# ==================== 产品召回相关 ====================

@advanced_features_bp.route('/recalls', methods=['GET'])
@login_required
def list_recalls():
    """列出所有活跃召回"""
    recalls = recall_system.list_active_recalls()
    return jsonify({"recalls": recalls})


@advanced_features_bp.route('/recalls/initiate', methods=['POST'])
@login_required
def initiate_recall():
    """启动产品召回"""
    data = request.json
    recall_id = data.get('recall_id')
    reason = data.get('reason')
    severity = RecallSeverity(data.get('severity', 'medium'))
    criteria = data.get('criteria', {})

    recall = recall_system.initiate_recall(recall_id, reason, severity, criteria)

    return jsonify({
        "message": "召回已启动",
        "recall": recall.to_dict()
    })


@advanced_features_bp.route('/recalls/<recall_id>', methods=['GET'])
@login_required
def get_recall_status(recall_id):
    """获取召回状态"""
    status = recall_system.get_recall_status(recall_id)

    if status is None:
        return jsonify({"error": "召回不存在"}), 404

    return jsonify(status)


@advanced_features_bp.route('/recalls/<recall_id>/recover', methods=['POST'])
@login_required
def mark_product_recovered(recall_id):
    """标记产品已回收"""
    data = request.json
    product_id = data.get('product_id')

    success = recall_system.mark_product_recovered(recall_id, product_id)

    if success:
        return jsonify({"message": "产品已标记为回收"})
    else:
        return jsonify({"error": "标记失败"}), 400


@advanced_features_bp.route('/recalls/<recall_id>/complete', methods=['POST'])
@login_required
def complete_recall(recall_id):
    """完成召回"""
    success = recall_system.complete_recall(recall_id)

    if success:
        return jsonify({"message": "召回已完成"})
    else:
        return jsonify({"error": "完成失败"}), 400


@advanced_features_bp.route('/recalls/<recall_id>/report', methods=['GET'])
@login_required
def get_recall_report(recall_id):
    """生成召回报告"""
    report = recall_system.generate_recall_report(recall_id)
    return jsonify(report)


@advanced_features_bp.route('/products/<product_id>/trace', methods=['GET'])
@login_required
def trace_product_flow(product_id):
    """追踪产品流转路径"""
    flow = recall_system.trace_product_flow(product_id)
    return jsonify(flow)


# ==================== 碳足迹追踪相关 ====================

@advanced_features_bp.route('/carbon/production', methods=['POST'])
@login_required
def record_production_emission():
    """记录生产环节碳排放"""
    data = request.json
    product_id = data.get('product_id')
    energy_kwh = data.get('energy_kwh')
    materials = data.get('materials', {})

    footprint = carbon_tracker.record_production_emission(product_id, energy_kwh, materials)

    return jsonify({
        "message": "生产碳排放已记录",
        "footprint": footprint.to_dict()
    })


@advanced_features_bp.route('/carbon/transportation', methods=['POST'])
@login_required
def record_transportation_emission():
    """记录运输环节碳排放"""
    data = request.json
    product_id = data.get('product_id')
    distance_km = data.get('distance_km')
    vehicle_type = data.get('vehicle_type', 'truck')
    fuel_liters = data.get('fuel_liters')

    footprint = carbon_tracker.record_transportation_emission(
        product_id, distance_km, vehicle_type, fuel_liters
    )

    return jsonify({
        "message": "运输碳排放已记录",
        "footprint": footprint.to_dict()
    })


@advanced_features_bp.route('/carbon/storage', methods=['POST'])
@login_required
def record_storage_emission():
    """记录仓储环节碳排放"""
    data = request.json
    product_id = data.get('product_id')
    storage_days = data.get('storage_days')
    facility_energy = data.get('facility_energy_kwh_per_day')

    footprint = carbon_tracker.record_storage_emission(product_id, storage_days, facility_energy)

    return jsonify({
        "message": "仓储碳排放已记录",
        "footprint": footprint.to_dict()
    })


@advanced_features_bp.route('/carbon/packaging', methods=['POST'])
@login_required
def record_packaging_emission():
    """记录包装环节碳排放"""
    data = request.json
    product_id = data.get('product_id')
    materials = data.get('materials', {})

    footprint = carbon_tracker.record_packaging_emission(product_id, materials)

    return jsonify({
        "message": "包装碳排放已记录",
        "footprint": footprint.to_dict()
    })


@advanced_features_bp.route('/carbon/products/<product_id>', methods=['GET'])
@login_required
def get_product_carbon_footprint(product_id):
    """获取产品总碳排放"""
    emission_data = carbon_tracker.get_product_total_emission(product_id)
    return jsonify(emission_data)


@advanced_features_bp.route('/carbon/compare', methods=['POST'])
@login_required
def compare_carbon_footprints():
    """比较多个产品的碳足迹"""
    data = request.json
    product_ids = data.get('product_ids', [])

    comparison = carbon_tracker.compare_products(product_ids)
    return jsonify(comparison)


@advanced_features_bp.route('/carbon/report', methods=['GET'])
@login_required
def get_carbon_report():
    """生成碳排放报告"""
    product_id = request.args.get('product_id')
    report = carbon_tracker.generate_carbon_report(product_id)
    return jsonify(report)


@advanced_features_bp.route('/carbon/certificate/<product_id>', methods=['GET'])
@login_required
def get_carbon_certificate(product_id):
    """获取碳足迹证书"""
    certificate = carbon_tracker.get_carbon_certificate(product_id)
    return jsonify(certificate)


# ==================== 区块链审计相关 ====================

@advanced_features_bp.route('/audit/blockchain/verify', methods=['GET'])
@login_required
def verify_blockchain():
    """验证区块链完整性"""
    result = audit_system.verify_blockchain_integrity()
    return jsonify(result)


@advanced_features_bp.route('/audit/products/<product_id>', methods=['GET'])
@login_required
def audit_product(product_id):
    """审计产品历史"""
    level = request.args.get('level', 'standard')
    audit_level = AuditLevel(level)

    result = audit_system.audit_product_history(product_id, audit_level)
    return jsonify(result)


@advanced_features_bp.route('/audit/export', methods=['GET'])
@login_required
def export_blockchain():
    """导出区块链数据"""
    format_str = request.args.get('format', 'json')
    start_block = int(request.args.get('start', 0))
    end_block = request.args.get('end')

    export_format = ExportFormat(format_str)
    data = audit_system.export_blockchain_data(
        export_format,
        start_block,
        int(end_block) if end_block else None
    )

    return data, 200, {'Content-Type': 'application/json' if format_str == 'json' else 'text/plain'}


@advanced_features_bp.route('/audit/certificate', methods=['POST'])
@login_required
def generate_audit_certificate():
    """生成审计证书"""
    audit_results = request.json
    certificate = audit_system.generate_audit_certificate(audit_results)
    return jsonify(certificate)


@advanced_features_bp.route('/audit/compliance', methods=['GET'])
@login_required
def get_compliance_report():
    """生成合规性报告"""
    report = audit_system.generate_compliance_report()
    return jsonify(report)


@advanced_features_bp.route('/audit/history', methods=['GET'])
@login_required
def get_audit_history():
    """获取审计历史"""
    limit = int(request.args.get('limit', 10))
    history = audit_system.get_audit_history(limit)
    return jsonify({"history": history})


# ==================== 库存预测相关 ====================

@advanced_features_bp.route('/inventory/record', methods=['POST'])
@login_required
def record_inventory_change():
    """记录库存变化"""
    data = request.json
    product_id = data.get('product_id')
    change_type = data.get('change_type')  # 'inbound' or 'outbound'
    quantity = data.get('quantity')

    inventory_forecast.record_inventory_change(product_id, change_type, quantity)

    return jsonify({"message": "库存变化已记录"})


@advanced_features_bp.route('/inventory/predict/<product_id>', methods=['GET'])
@login_required
def predict_demand(product_id):
    """预测产品需求"""
    days = int(request.args.get('days', 7))
    model = request.args.get('model', 'moving_average')

    prediction_model = PredictionModel(model)
    prediction = inventory_forecast.predict_demand(product_id, days, prediction_model)

    return jsonify(prediction)


@advanced_features_bp.route('/inventory/reorder-point/<product_id>', methods=['GET'])
@login_required
def calculate_reorder_point(product_id):
    """计算再订货点"""
    lead_time = int(request.args.get('lead_time', 7))
    safety_stock_days = int(request.args.get('safety_stock_days', 3))

    result = inventory_forecast.calculate_reorder_point(product_id, lead_time, safety_stock_days)
    return jsonify(result)


@advanced_features_bp.route('/inventory/optimize/<product_id>', methods=['GET'])
@login_required
def optimize_order_quantity(product_id):
    """优化订货批量"""
    holding_cost = float(request.args.get('holding_cost', 1.0))
    order_cost = float(request.args.get('order_cost', 50.0))

    result = inventory_forecast.optimize_order_quantity(product_id, holding_cost, order_cost)
    return jsonify(result)


@advanced_features_bp.route('/inventory/analyze/<product_id>', methods=['POST'])
@login_required
def analyze_stock(product_id):
    """分析当前库存状态"""
    data = request.json
    current_quantity = data.get('current_quantity')

    analysis = inventory_forecast.analyze_current_stock(product_id, current_quantity)
    return jsonify(analysis)


@advanced_features_bp.route('/inventory/dashboard', methods=['POST'])
@login_required
def get_inventory_dashboard():
    """获取库存仪表板"""
    inventory_levels = request.json  # {"product_id": quantity, ...}

    dashboard = inventory_forecast.get_inventory_dashboard(inventory_levels)
    return jsonify(dashboard)


@advanced_features_bp.route('/inventory/alerts', methods=['POST'])
@login_required
def generate_inventory_alerts():
    """生成库存预警"""
    inventory_levels = request.json

    alerts = inventory_forecast.generate_inventory_alerts(inventory_levels)
    return jsonify({"alerts": alerts})


@advanced_features_bp.route('/inventory/simulate/<product_id>', methods=['POST'])
@login_required
def simulate_inventory(product_id):
    """模拟库存场景"""
    data = request.json
    current_qty = data.get('current_quantity')
    daily_demand = data.get('daily_demand')
    days = data.get('days', 30)

    simulation = inventory_forecast.simulate_inventory_scenario(
        product_id, current_qty, daily_demand, days
    )
    return jsonify(simulation)


# 导出蓝图
__all__ = ['advanced_features_bp']
