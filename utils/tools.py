BUY = {
    'type': 'function',
    'function': {
        'name': 'buy',
        'description': 'Buy a specific quantity of a cryptocurrency',
        'parameters': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string'},
                'quantity': {'type': 'number'}
            },
            'required': ['symbol', 'quantity']
        }
    }
}
SELL = {
    'type': 'function',
    'function': {
        'name': 'sell',
        'description': 'Sell a specific quantity of a cryptocurrency',
        'parameters': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string'},
                'quantity': {'type': 'number'}
            },
            'required': ['symbol', 'quantity']
        }
    }
}