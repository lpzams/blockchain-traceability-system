"""
产品增强功能服务 - 评价、收藏、关注等
"""

import logging
from typing import Dict, List, Optional
from models.database import (
    add_product_rating, get_product_ratings, get_product_average_rating,
    get_user_rating_for_product, add_product_favorite, remove_product_favorite,
    get_user_favorites, is_product_favorited, add_product_watch,
    remove_product_watch, get_user_watches, get_product_watchers,
    is_product_watched, get_product_by_id
)

logger = logging.getLogger(__name__)


class ProductRatingService:
    """产品评价服务"""

    @staticmethod
    def add_rating(product_id: str, user_id: int, rating: int, comment: Optional[str] = None) -> Dict:
        """添加或更新产品评价"""
        # 验证评分范围
        if rating < 1 or rating > 5:
            raise ValueError("评分必须在1-5之间")

        # 验证产品是否存在
        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("产品不存在")

        try:
            rating_id = add_product_rating(product_id, user_id, rating, comment)
            logger.info(f"User {user_id} rated product {product_id}: {rating}/5")

            return {
                'success': True,
                'rating_id': rating_id,
                'message': '评价成功'
            }
        except Exception as e:
            logger.error(f"Failed to add rating: {str(e)}")
            raise

    @staticmethod
    def get_product_ratings(product_id: str) -> List[Dict]:
        """获取产品的所有评价"""
        ratings = get_product_ratings(product_id)
        return [dict(rating) for rating in ratings]

    @staticmethod
    def get_product_rating_summary(product_id: str) -> Dict:
        """获取产品评分摘要"""
        avg_rating = get_product_average_rating(product_id)
        ratings = get_product_ratings(product_id)

        # 统计各星级数量
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            rating_distribution[rating['rating']] += 1

        return {
            'average_rating': avg_rating['average'],
            'total_ratings': avg_rating['count'],
            'distribution': rating_distribution,
            'recent_ratings': [dict(r) for r in ratings[:5]]  # 最近5条评价
        }

    @staticmethod
    def get_user_rating(product_id: str, user_id: int) -> Optional[Dict]:
        """获取用户对产品的评价"""
        rating = get_user_rating_for_product(product_id, user_id)
        return dict(rating) if rating else None


class ProductFavoriteService:
    """产品收藏服务"""

    @staticmethod
    def add_favorite(product_id: str, user_id: int) -> Dict:
        """添加收藏"""
        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("产品不存在")

        try:
            favorite_id = add_product_favorite(product_id, user_id)
            logger.info(f"User {user_id} favorited product {product_id}")

            return {
                'success': True,
                'favorite_id': favorite_id,
                'message': '收藏成功'
            }
        except Exception as e:
            logger.error(f"Failed to add favorite: {str(e)}")
            raise

    @staticmethod
    def remove_favorite(product_id: str, user_id: int) -> Dict:
        """取消收藏"""
        try:
            count = remove_product_favorite(product_id, user_id)
            logger.info(f"User {user_id} unfavorited product {product_id}")

            return {
                'success': True,
                'removed': count > 0,
                'message': '已取消收藏' if count > 0 else '未找到收藏记录'
            }
        except Exception as e:
            logger.error(f"Failed to remove favorite: {str(e)}")
            raise

    @staticmethod
    def get_user_favorites(user_id: int) -> List[Dict]:
        """获取用户的收藏列表"""
        favorites = get_user_favorites(user_id)
        return [dict(fav) for fav in favorites]

    @staticmethod
    def is_favorited(product_id: str, user_id: int) -> bool:
        """检查是否已收藏"""
        return is_product_favorited(product_id, user_id)


class ProductWatchService:
    """产品关注服务"""

    @staticmethod
    def add_watch(product_id: str, user_id: int,
                  notify_on_transfer: bool = True,
                  notify_on_quality_check: bool = True) -> Dict:
        """添加关注"""
        product = get_product_by_id(product_id)
        if not product:
            raise ValueError("产品不存在")

        try:
            watch_id = add_product_watch(
                product_id, user_id,
                notify_on_transfer, notify_on_quality_check
            )
            logger.info(f"User {user_id} started watching product {product_id}")

            return {
                'success': True,
                'watch_id': watch_id,
                'message': '关注成功'
            }
        except Exception as e:
            logger.error(f"Failed to add watch: {str(e)}")
            raise

    @staticmethod
    def remove_watch(product_id: str, user_id: int) -> Dict:
        """取消关注"""
        try:
            count = remove_product_watch(product_id, user_id)
            logger.info(f"User {user_id} stopped watching product {product_id}")

            return {
                'success': True,
                'removed': count > 0,
                'message': '已取消关注' if count > 0 else '未找到关注记录'
            }
        except Exception as e:
            logger.error(f"Failed to remove watch: {str(e)}")
            raise

    @staticmethod
    def get_user_watches(user_id: int) -> List[Dict]:
        """获取用户关注的产品列表"""
        watches = get_user_watches(user_id)
        return [dict(watch) for watch in watches]

    @staticmethod
    def is_watched(product_id: str, user_id: int) -> bool:
        """检查是否已关注"""
        return is_product_watched(product_id, user_id)

    @staticmethod
    def notify_watchers(product_id: str, event_type: str, event_data: Dict):
        """通知关注者"""
        watchers = get_product_watchers(product_id, event_type)

        notifications = []
        for watcher in watchers:
            notifications.append({
                'user_id': watcher['id'],
                'username': watcher['username'],
                'product_id': product_id,
                'event_type': event_type,
                'event_data': event_data
            })

        logger.info(f"Notified {len(notifications)} watchers for product {product_id}")
        return notifications


class ProductComparisonService:
    """产品对比服务"""

    @staticmethod
    def compare_products(product_ids: List[str]) -> Dict:
        """对比多个产品"""
        if len(product_ids) < 2:
            raise ValueError("至少需要2个产品进行对比")

        if len(product_ids) > 5:
            raise ValueError("最多只能对比5个产品")

        products_data = []
        from models.database import get_all_products

        # 先获取所有产品用于批次号查询
        all_products = get_all_products()

        for product_id_or_batch in product_ids:
            # 先尝试用UUID查询
            product = get_product_by_id(product_id_or_batch)

            # 如果没找到，尝试用批次号查询
            if not product:
                product = next((p for p in all_products if p['batch_number'] == product_id_or_batch), None)

            if not product:
                raise ValueError(f"产品 {product_id_or_batch} 不存在")

            actual_product_id = product['product_id']

            # 获取评分信息
            rating_summary = ProductRatingService.get_product_rating_summary(actual_product_id)

            # 获取事件统计
            from models.database import get_product_events
            events = get_product_events(actual_product_id)

            event_stats = {
                'total_events': len(events),
                'transfers': sum(1 for e in events if e['event_type'] == 'transfer'),
                'quality_checks': sum(1 for e in events if e['event_type'] == 'quality_check'),
                'logistics_updates': sum(1 for e in events if e['event_type'] == 'logistics')
            }

            products_data.append({
                'product': dict(product),
                'rating_summary': rating_summary,
                'event_stats': event_stats
            })

        return {
            'products': products_data,
            'comparison_count': len(products_data)
        }


# 导出
__all__ = [
    'ProductRatingService',
    'ProductFavoriteService',
    'ProductWatchService',
    'ProductComparisonService'
]
