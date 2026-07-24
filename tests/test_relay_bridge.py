import unittest
from unittest.mock import Mock, patch

import config
from relay.bridge import RelayBridge
from utils.constants import CHAIN_MAP, ZERO_ADDRESS


class RelayBridgeTests(unittest.TestCase):
    def make_bridge(self):
        bridge = RelayBridge.__new__(RelayBridge)
        bridge._chain_from = 'ARBITRUM'
        bridge._chain_to = 'BNB'
        bridge.url = 'https://relay.link/'
        bridge.api_url = 'https://api.relay.link/'
        bridge.chain_map = CHAIN_MAP
        bridge.address = '0x1111111111111111111111111111111111111111'
        bridge.proxy = None
        return bridge

    def test_quote_uses_v2_slippage_refund_and_keeps_request_id(self):
        bridge = self.make_bridge()
        response = Mock(status_code=200)
        response.json.return_value = {
            'steps': [{
                'kind': 'transaction',
                'requestId': 'request-123',
                'items': [{'data': {'to': '0x2222222222222222222222222222222222222222', 'value': '1'}}],
            }]
        }

        with patch('relay.bridge.requests.post', return_value=response) as post:
            quote = bridge._quote_tx_data(123, bridge.address)

        self.assertEqual(quote.get('request_id'), 'request-123')
        self.assertEqual(quote.get('tx', {}).get('value'), '1')
        self.assertTrue(post.call_args.args[0].endswith('/quote/v2'))
        body = post.call_args.kwargs['json']
        self.assertNotIn('slippageTolerance', body)
        self.assertEqual(body['refundTo'], bridge.address)
        self.assertEqual(body['destinationCurrency'], ZERO_ADDRESS)

    def test_quote_uses_manual_slippage_when_configured(self):
        bridge = self.make_bridge()
        response = Mock(status_code=200)
        response.json.return_value = {
            'steps': [{
                'kind': 'transaction',
                'requestId': 'request-123',
                'items': [{'data': {'to': '0x2222222222222222222222222222222222222222', 'value': '1'}}],
            }]
        }

        with patch.object(config, 'SLIPPAGE_TOLERANCE_BPS', 600, create=True), \
                patch('relay.bridge.requests.post', return_value=response) as post:
            bridge._quote_tx_data(123, bridge.address)

        self.assertEqual(post.call_args.kwargs['json'].get('slippageTolerance'), '600')

    def test_wait_for_relay_returns_false_when_fill_is_refunded(self):
        bridge = self.make_bridge()
        pending = Mock(status_code=200)
        pending.json.return_value = {'status': 'pending'}
        refunded = Mock(status_code=200)
        refunded.json.return_value = {'status': 'refund', 'details': 'market price shifted'}

        self.assertTrue(hasattr(bridge, '_wait_for_relay'))
        if not hasattr(bridge, '_wait_for_relay'):
            return

        with patch('relay.bridge.requests.get', side_effect=[pending, refunded]) as get, \
                patch('time.sleep'):
            result = bridge._wait_for_relay('request-123')

        self.assertFalse(result)
        self.assertEqual(get.call_count, 2)
        self.assertTrue(get.call_args.args[0].endswith('/intents/status/v3'))
        self.assertEqual(get.call_args.kwargs['params'], {'requestId': 'request-123'})

    def test_wait_for_relay_returns_true_when_fill_succeeds(self):
        bridge = self.make_bridge()
        response = Mock(status_code=200)
        response.json.return_value = {'status': 'success', 'txHashes': ['0xdestination']}

        with patch('relay.bridge.requests.get', return_value=response) as get:
            result = bridge._wait_for_relay('request-123')

        self.assertTrue(result)
        self.assertEqual(get.call_count, 1)

    def test_bridge_is_not_successful_until_relay_confirms_fill(self):
        bridge = self.make_bridge()
        tx = {'to': '0x2222222222222222222222222222222222222222', 'value': '1'}

        with patch.object(bridge, '_quote_tx_data', return_value={'tx': tx, 'request_id': 'request-123'}), \
                patch.object(bridge, 'send_tx', return_value='0xorigin') as send_tx, \
                patch.object(bridge, '_wait_for_relay', return_value=False, create=True):
            result = bridge.bridge_to_recipient(123, bridge.address)

        self.assertEqual(result, 0)
        send_tx.assert_called_once_with(tx, return_hash=True)


if __name__ == '__main__':
    unittest.main()
