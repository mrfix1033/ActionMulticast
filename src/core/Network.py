# import ssl
from pathlib import Path

import requests

from src.core.protocol.BasePacket import BasePacket


def get_client_session():
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # ssl_context.load_default_certs()

    # connector =aiohttp.TCPConnector(
    #     ssl=ssl_context,
    #     limit=100,
    #     force_close=True,
    #     enable_cleanup_closed=True
    # )

    session = requests.session()
    session.trust_env = True
    return session


def download_file(download_url: str, save_path: str):
    with get_client_session() as session:
        with session.get(download_url) as response:
            if response.status_code == 200:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                    return None
    return response.status_code


def serialize_packet(packet: BasePacket):
    packet_bytes = packet.serialize()
    packet_data = f"{packet.get_id()} {len(packet_bytes)} ".encode() + packet_bytes
    return packet_data
