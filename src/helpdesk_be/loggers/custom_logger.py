import logging

logger = logging.getLogger("CustomLogger")
logger.setLevel(logging.INFO)

# フォーマットの設定
# レベル、メッセージ設定
log_format = "%(levelname)s : %(message)s"

# handlerにフォーマットを設定
# handlersフォルダはapi側の物なので、自身のPCのターミナルに出すログ用のhandlerはここに書く
st_handler = logging.StreamHandler()
st_handler.setLevel(logging.INFO)
st_handler.setFormatter(logging.Formatter(log_format))

# loggerにhandlerを伝える
logger.addHandler(st_handler)
