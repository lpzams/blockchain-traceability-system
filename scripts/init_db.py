#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from werkzeug.security import generate_password_hash
from models.database import init_database, create_user, get_db_connection
from models.traceability import register_product, transfer_ownership, add_quality_check, add_logistics
from datetime import datetime, timedelta


def main():
    print("=" * 60)
    print("产品溯源区块链系统 - 数据库初始化")
    print("=" * 60)

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'blockchain.db')

    if os.path.exists(db_path):
        response = input(f"\n数据库文件已存在: {db_path}\n是否删除并重新初始化? (y/n): ")
        if response.lower() == 'y':
            os.remove(db_path)
            print("已删除旧数据库")
        else:
            print("初始化已取消")
            return

    print("\n[1/5] 创建数据库表...")
    init_database()
    print("✓ 数据库表创建成功")

    print("\n[2/5] 创建管理员和测试用户...")

    # 创建管理员账号
    admin_id = create_user(
        username='admin',
        password_hash=generate_password_hash('1'),
        role='admin',
        company_name='系统管理'
    )
    print(f"✓ 管理员账号: admin / 1")

    # 创建生产商
    manufacturer1_id = create_user(
        username='manufacturer1',
        password_hash=generate_password_hash('123456'),
        role='manufacturer',
        company_name='优质茶叶生产公司'
    )
    print(f"✓ 生产商1: manufacturer1 / 123456")

    manufacturer2_id = create_user(
        username='manufacturer2',
        password_hash=generate_password_hash('123456'),
        role='manufacturer',
        company_name='有机食品生产基地'
    )
    print(f"✓ 生产商2: manufacturer2 / 123456")

    # 创建经销商
    distributor1_id = create_user(
        username='distributor1',
        password_hash=generate_password_hash('123456'),
        role='distributor',
        company_name='全国经销商A'
    )
    print(f"✓ 经销商1: distributor1 / 123456")

    distributor2_id = create_user(
        username='distributor2',
        password_hash=generate_password_hash('123456'),
        role='distributor',
        company_name='地区经销商B'
    )
    print(f"✓ 经销商2: distributor2 / 123456")

    distributor3_id = create_user(
        username='distributor3',
        password_hash=generate_password_hash('123456'),
        role='distributor',
        company_name='线上商城C'
    )
    print(f"✓ 经销商3: distributor3 / 123456")

    # 创建消费者
    consumer1_id = create_user(
        username='consumer1',
        password_hash=generate_password_hash('123456'),
        role='consumer',
        company_name='个人消费者'
    )
    print(f"✓ 消费者1: consumer1 / 123456")

    consumer2_id = create_user(
        username='consumer2',
        password_hash=generate_password_hash('123456'),
        role='consumer',
        company_name='个人消费者'
    )
    print(f"✓ 消费者2: consumer2 / 123456")

    consumer3_id = create_user(
        username='consumer3',
        password_hash=generate_password_hash('123456'),
        role='consumer',
        company_name='个人消费者'
    )
    print(f"✓ 消费者3: consumer3 / 123456")

    # 创建监管者
    regulator_id = create_user(
        username='regulator1',
        password_hash=generate_password_hash('123456'),
        role='regulator',
        company_name='质量监管部门'
    )
    print(f"✓ 监管者: regulator1 / 123456")

    print("\n[3/5] 创建演示产品...")

    # 产品1: 西湖龙井茶叶
    product1_id, _ = register_product(
        name='西湖龙井茶叶',
        batch_number='001',
        manufacturer_id=manufacturer1_id,
        production_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )
    print(f"✓ 产品1: 西湖龙井茶叶 (ID: {product1_id[:16]}...)")

    add_quality_check(product1_id, manufacturer1_id, '合格', '符合国家标准，品质优良')
    print("  - 质检记录: 合格")

    transfer_ownership(product1_id, manufacturer1_id, distributor1_id, '杭州仓库')
    print("  - 转移: 生产商 → 经销商A")

    add_logistics(product1_id, distributor1_id, '上海配送中心', '运输中')
    print("  - 物流: 上海配送中心")

    transfer_ownership(product1_id, distributor1_id, distributor2_id, '上海中转站')
    print("  - 转移: 经销商A → 经销商B")

    add_logistics(product1_id, distributor2_id, '北京门店', '已到达')
    print("  - 物流: 已到达北京门店")

    transfer_ownership(product1_id, distributor2_id, consumer1_id, '北京')
    print("  - 转移: 经销商B → 消费者1")

    # 产品2: 有机绿茶
    product2_id, _ = register_product(
        name='有机绿茶',
        batch_number='002',
        manufacturer_id=manufacturer1_id,
        production_date=(datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d')
    )
    print(f"✓ 产品2: 有机绿茶 (ID: {product2_id[:16]}...)")

    add_quality_check(product2_id, manufacturer1_id, '合格', '有机认证，无农药残留')
    print("  - 质检记录: 合格")

    transfer_ownership(product2_id, manufacturer1_id, distributor1_id, '杭州仓库')
    print("  - 转移: 生产商 → 经销商A")

    transfer_ownership(product2_id, distributor1_id, distributor3_id, '线上仓库')
    print("  - 转移: 经销商A → 经销商C")

    transfer_ownership(product2_id, distributor3_id, consumer2_id, '线上')
    print("  - 转移: 经销商C → 消费者2")

    # 产品3: 铁观音
    product3_id, _ = register_product(
        name='铁观音',
        batch_number='003',
        manufacturer_id=manufacturer1_id,
        production_date=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
    )
    print(f"✓ 产品3: 铁观音 (ID: {product3_id[:16]}...)")

    add_quality_check(product3_id, manufacturer1_id, '合格', '传统工艺，品质一流')
    print("  - 质检记录: 合格")

    transfer_ownership(product3_id, manufacturer1_id, distributor2_id, '上海仓库')
    print("  - 转移: 生产商 → 经销商B")

    transfer_ownership(product3_id, distributor2_id, consumer1_id, '北京')
    print("  - 转移: 经销商B → 消费者1")

    # 产品4: 有机大米
    product4_id, _ = register_product(
        name='有机大米',
        batch_number='004',
        manufacturer_id=manufacturer2_id,
        production_date=(datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
    )
    print(f"✓ 产品4: 有机大米 (ID: {product4_id[:16]}...)")

    add_quality_check(product4_id, manufacturer2_id, '合格', '无化肥无农药，纯生态种植')
    print("  - 质检记录: 合格")

    transfer_ownership(product4_id, manufacturer2_id, distributor1_id, '仓库A')
    print("  - 转移: 生产商 → 经销商A")

    add_logistics(product4_id, distributor1_id, '配送中心', '打包中')
    print("  - 物流: 配送中心打包中")

    transfer_ownership(product4_id, distributor1_id, consumer3_id, '配送')
    print("  - 转移: 经销商A → 消费者3")

    # 产品5: 黑芝麻
    product5_id, _ = register_product(
        name='黑芝麻',
        batch_number='005',
        manufacturer_id=manufacturer2_id,
        production_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    )
    print(f"✓ 产品5: 黑芝麻 (ID: {product5_id[:16]}...)")

    add_quality_check(product5_id, manufacturer2_id, '合格', '低温冷压，营养保留完整')
    print("  - 质检记录: 合格")

    transfer_ownership(product5_id, manufacturer2_id, distributor3_id, '线上仓')
    print("  - 转移: 生产商 → 经销商C")

    transfer_ownership(product5_id, distributor3_id, consumer2_id, '线上')
    print("  - 转移: 经销商C → 消费者2")

    print("\n[4/5] 为高级功能创建额外演示产品...")

    # 为高级功能创建几个演示产品
    demo_batch = f'DEMO-{datetime.now().strftime("%Y%m%d")}'
    demo_products = []

    for i in range(1, 4):
        demo_product_id, _ = register_product(
            name=f'高级功能演示产品{i}',
            batch_number=demo_batch,
            manufacturer_id=manufacturer1_id,
            production_date=datetime.now().strftime('%Y-%m-%d')
        )
        demo_products.append(demo_product_id)

        add_quality_check(demo_product_id, manufacturer1_id, '合格', f'演示产品{i}质检通过')
        print(f"  ✓ 演示产品{i}: {demo_product_id[:16]}...")

    # 为演示产品创建事件，确保高级功能能访问
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for demo_id in demo_products:
            # 确保有transfer事件
            cursor.execute('''
                INSERT INTO events (product_id, event_type, from_user_id, to_user_id, location, data, block_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (demo_id, 'transfer', manufacturer1_id, distributor1_id, '仓库', '转移到经销商', 'demo_block_hash'))

    print("\n[5/5] 创建完成！\n")

    print("=" * 60)
    print("系统账号:")
    print("=" * 60)
    print("  管理员:  admin / 1")
    print("\n生产商账号:")
    print("  生产商1: manufacturer1 / 123456")
    print("  生产商2: manufacturer2 / 123456")
    print("\n经销商账号:")
    print("  经销商1: distributor1 / 123456")
    print("  经销商2: distributor2 / 123456")
    print("  经销商3: distributor3 / 123456")
    print("\n消费者账号:")
    print("  消费者1: consumer1 / 123456")
    print("  消费者2: consumer2 / 123456")
    print("  消费者3: consumer3 / 123456")
    print("\n监管者账号:")
    print("  监管者:  regulator1 / 123456")
    print("\n演示产品:")
    print(f"  产品1: {product1_id} (西湖龙井茶叶)")
    print(f"  产品2: {product2_id} (有机绿茶)")
    print(f"  产品3: {product3_id} (铁观音)")
    print(f"  产品4: {product4_id} (有机大米)")
    print(f"  产品5: {product5_id} (黑芝麻)")

    print(f"\n高级功能演示产品 (批次: {demo_batch}):")
    for i, demo_id in enumerate(demo_products, 1):
        print(f"  演示产品{i}: {demo_id}")
        print(f"    - 证书: /features/certificate/{demo_id}")
        print(f"    - 防伪码: /features/anti-counterfeit/{demo_id}")
        print(f"    - 链验证: /features/chain-integrity/{demo_id}")

    print(f"\n  批次管理: /features/batch/{demo_batch}")
    print(f"  功能首页: /features/overview")

    print("=" * 60)
    print("启动系统: python app.py")
    print("访问地址: http://localhost:5000")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()

