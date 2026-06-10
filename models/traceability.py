import uuid
import json
from datetime import datetime
from models.blockchain import Blockchain
from models.database import (
    save_block_to_db, create_product, update_product_owner,
    create_event, get_product_by_id, get_product_events, get_user_by_id
)


blockchain = Blockchain()


def register_product(name, batch_number, manufacturer_id, production_date):
    product_id = str(uuid.uuid4())

    data = {
        "type": "register",
        "product_id": product_id,
        "name": name,
        "batch_number": batch_number,
        "manufacturer_id": manufacturer_id,
        "production_date": production_date,
        "timestamp": datetime.now().isoformat()
    }

    block = blockchain.add_block(data)
    save_block_to_db(block)

    create_product(product_id, name, batch_number, manufacturer_id, production_date, block.hash)

    create_event(
        product_id=product_id,
        event_type='register',
        block_hash=block.hash,
        to_user_id=manufacturer_id,
        data=json.dumps({"name": name, "batch": batch_number})
    )

    return product_id, block.hash


def transfer_ownership(product_id, from_user_id, to_user_id, location=None):
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("Product not found")

    if product['current_owner_id'] != from_user_id:
        raise ValueError("You are not the current owner of this product")

    data = {
        "type": "transfer",
        "product_id": product_id,
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "location": location,
        "timestamp": datetime.now().isoformat()
    }

    block = blockchain.add_block(data)
    save_block_to_db(block)

    update_product_owner(product_id, to_user_id)

    create_event(
        product_id=product_id,
        event_type='transfer',
        block_hash=block.hash,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        location=location
    )

    return block.hash


def add_quality_check(product_id, inspector_id, result, notes):
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("Product not found")

    data = {
        "type": "quality_check",
        "product_id": product_id,
        "inspector_id": inspector_id,
        "result": result,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    }

    block = blockchain.add_block(data)
    save_block_to_db(block)

    create_event(
        product_id=product_id,
        event_type='quality_check',
        block_hash=block.hash,
        from_user_id=inspector_id,
        data=json.dumps({"result": result, "notes": notes})
    )

    return block.hash


def add_logistics(product_id, user_id, location, status):
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("Product not found")

    data = {
        "type": "logistics",
        "product_id": product_id,
        "user_id": user_id,
        "location": location,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    block = blockchain.add_block(data)
    save_block_to_db(block)

    create_event(
        product_id=product_id,
        event_type='logistics',
        block_hash=block.hash,
        from_user_id=user_id,
        location=location,
        data=json.dumps({"status": status})
    )

    return block.hash


def get_product_history(product_id):
    import json

    product = get_product_by_id(product_id)
    if not product:
        return None

    events = get_product_events(product_id)

    # 格式化事件
    formatted_events = []
    for event in events:
        event_info = {
            'type': event['event_type'],
            'timestamp': event['created_at'],
            'location': event['location']
        }

        if event['event_type'] == 'register':
            event_info['title'] = '产品注册'
            to_username = event['to_username'] if 'to_username' in event.keys() else '未知'
            event_info['details'] = f"由 {to_username} 注册"
        elif event['event_type'] == 'transfer':
            event_info['title'] = '所有权转移'
            from_username = event['from_username'] if 'from_username' in event.keys() else '未知'
            to_username = event['to_username'] if 'to_username' in event.keys() else '未知'
            event_info['details'] = f"从 {from_username} 转移到 {to_username}"
        elif event['event_type'] == 'quality_check':
            data_str = event['data'] if event['data'] else None
            data = json.loads(data_str) if data_str else {}
            event_info['title'] = '质检'
            event_info['details'] = f"质检结果: {data.get('result', 'unknown')}"
        elif event['event_type'] == 'logistics':
            data_str = event['data'] if event['data'] else None
            data = json.loads(data_str) if data_str else {}
            event_info['title'] = '物流更新'
            event_info['details'] = f"状态: {data.get('status', 'unknown')}"
        else:
            event_info['title'] = event['event_type']
            event_info['details'] = event['data'] if event['data'] else '无详细信息'

        formatted_events.append(event_info)

    history = {
        "product": dict(product),
        "events": formatted_events
    }

    return history


def verify_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return False, "Product not found"

    is_valid, message = blockchain.is_chain_valid()

    if is_valid:
        return True, "Product is authentic and blockchain is valid"
    else:
        return False, f"Blockchain validation failed: {message}"


def get_blockchain_status():
    is_valid, message = blockchain.is_chain_valid()
    return {
        "valid": is_valid,
        "message": message,
        "total_blocks": len(blockchain.chain),
        "latest_block": blockchain.get_latest_block().to_dict()
    }
