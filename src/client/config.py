# Для поиска сервера в локальной сети: установить server_ip в None, server_port игнорируется
# Для подключения к конкретному серверу (локальная/глобальная сеть): задать server_ip и server_port
server_ip = None
server_port = 10330

beacon_port = 10331

keycodes_to_hide_show_console = 165, 163, 161, 13  # RAlt, RCtrl, RShift, Enter  (необходимо зажать все)
start_hidden = False  # скрывать консоль при запуске?