from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest
from linebot.v3.exceptions import InvalidSignatureError
import pandas as pd
import os
from dotenv import load_dotenv  # 新增

# 加載 .env 文件
load_dotenv()  # 新增

app = Flask(__name__)

# 用你自己的 Channel access token 和 secret 替换下方字串
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "default_access_token")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "default_secret")

if LINE_CHANNEL_ACCESS_TOKEN == "default_access_token" or LINE_CHANNEL_SECRET == "default_secret":
    print("警告：未設置環境變數 'LINE_CHANNEL_ACCESS_TOKEN' 或 'LINE_CHANNEL_SECRET'，使用默認值。")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise EnvironmentError(
        "請確保已設置環境變數 'LINE_CHANNEL_ACCESS_TOKEN' 和 'LINE_CHANNEL_SECRET'"
    )

print(f"LINE_CHANNEL_ACCESS_TOKEN: {LINE_CHANNEL_ACCESS_TOKEN}")
print(f"LINE_CHANNEL_SECRET: {LINE_CHANNEL_SECRET}")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 確認資料檔案是否存在

df = None

def load_data():
    global df
    if df is None:
        DATA_FILE = "cleaned_qian_data.csv"
        if not os.path.exists(DATA_FILE):
            raise FileNotFoundError(f"資料檔案 {DATA_FILE} 不存在，請確認檔案位置。")

        # 读取 cleaned_qian_data.csv（只讀取一次）
        print("正在讀取資料檔案...")
        df = pd.read_csv(DATA_FILE)
        print(f"資料檔案 {DATA_FILE} 已成功讀取，共 {len(df)} 筆資料。")


@app.route("/callback", methods=["POST"])
def callback():
    print(f"Request body: {123}")
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessage):
        user_msg = event.message.text

        # 从资料库随机选一首签
        selected = df.sample(n=1).iloc[0]
        original = selected["原文"]
        modern = selected["現代化解籤"]

        reply = f"你抽到：\n\n「{original}」\n\n現代解讀：\n{modern}"

        line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=event.reply_token,
                                messages=[TextMessage(text=reply)]))


if __name__ == "__main__":

    print("啟動伺服器...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  # 設定 debug=False 以避免重啟伺服器
    # 增加 waitress 執行緒數量
    # serve(app, host="0.0.0.0", port=5000,)
