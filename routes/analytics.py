from flask import Blueprint, render_template, jsonify, request
from models.advanced_analytics import ProductTraceAnalytics, PredictionEngine
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
def index():
    """高级分析首页"""
    return render_template('analytics/index.html')


@analytics_bp.route('/risk-assessment')
def risk_assessment():
    """产品风险评估仪表板"""
    try:
        assessments = ProductTraceAnalytics.get_risk_assessment()
        return render_template('analytics/risk_assessment.html', assessments=assessments)
    except Exception as e:
        logger.error(f"风险评估错误: {e}")
        return render_template('analytics/risk_assessment.html', assessments=[], error=str(e))


@analytics_bp.route('/api/risk-assessment')
def api_risk_assessment():
    """风险评估API"""
    try:
        product_id = request.args.get('product_id')
        assessments = ProductTraceAnalytics.get_risk_assessment(product_id)
        return jsonify({'success': True, 'data': assessments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/supply-chain-network')
def supply_chain_network():
    """供应链网络分析"""
    try:
        network = ProductTraceAnalytics.get_supply_chain_network()
        return render_template('analytics/supply_chain_network.html', network=network)
    except Exception as e:
        logger.error(f"网络分析错误: {e}")
        return render_template('analytics/supply_chain_network.html', network={}, error=str(e))


@analytics_bp.route('/api/supply-chain-network')
def api_supply_chain_network():
    """供应链网络API"""
    try:
        network = ProductTraceAnalytics.get_supply_chain_network()
        return jsonify(network)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/carbon-footprint')
def carbon_footprint():
    """碳足迹分析"""
    try:
        analysis = ProductTraceAnalytics.get_carbon_footprint_analysis()
        return render_template('analytics/carbon_footprint.html', analysis=analysis)
    except Exception as e:
        logger.error(f"碳足迹分析错误: {e}")
        return render_template('analytics/carbon_footprint.html', analysis={}, error=str(e))


@analytics_bp.route('/api/carbon-footprint')
def api_carbon_footprint():
    """碳足迹API"""
    try:
        analysis = ProductTraceAnalytics.get_carbon_footprint_analysis()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/quality-heatmap')
def quality_heatmap():
    """质量追溯热力图"""
    try:
        heatmap = ProductTraceAnalytics.get_quality_heatmap()
        return render_template('analytics/quality_heatmap.html', heatmap=heatmap)
    except Exception as e:
        logger.error(f"热力图错误: {e}")
        return render_template('analytics/quality_heatmap.html', heatmap=[], error=str(e))


@analytics_bp.route('/recommendations')
def recommendations():
    """智能推荐系统"""
    try:
        recommendations = ProductTraceAnalytics.get_intelligent_recommendations()
        predictions = PredictionEngine.predict_quality_issues()
        return render_template('analytics/recommendations.html',
                             recommendations=recommendations,
                             predictions=predictions)
    except Exception as e:
        logger.error(f"推荐系统错误: {e}")
        return render_template('analytics/recommendations.html',
                             recommendations=[],
                             predictions=[],
                             error=str(e))


@analytics_bp.route('/api/predictions/<product_id>')
def api_predictions(product_id):
    """产品交付预测API"""
    try:
        delivery_prediction = PredictionEngine.predict_delivery_time(product_id)
        return jsonify({'success': True, 'data': delivery_prediction})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
