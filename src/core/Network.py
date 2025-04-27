import ssl
from pathlib import Path

import requests


def get_client_session():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_default_certs()

    # connector =aiohttp.TCPConnector(
    #     ssl=ssl_context,
    #     limit=100,
    #     force_close=True,
    #     enable_cleanup_closed=True
    # )

    session = requests.session()
    session.trust_env = True
    return session


async def download_file(download_url: str, save_path: str):
    async with get_client_session() as session:
        async with session.get(download_url) as response:
            if response.status == 200:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
    return response.status