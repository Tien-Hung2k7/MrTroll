import os
import io
import discord
import requests
from PIL import Image, ImageDraw, ImageFont

# ==================== CONFIGURATION ====================
# Thay vì dán token trực tiếp, hãy dùng os.getenv
BOT_TOKEN = os.getenv("BOT_TOKEN") 

# Nếu bot không tìm thấy token, hãy cho nó báo lỗi rõ ràng
if not BOT_TOKEN:
    print("❌ Lỗi: Chưa thiết lập biến môi trường BOT_TOKEN!")
    exit()

# 2. Điền link Webhook kênh Welcome vào đây
WEBHOOK_URL = "https://discord.com/api/webhooks/1514142940925267978/VKUo-ZJiqATFrzCHT0PyWg2RBSCtlsyglDDZTL0ppM3ieCgMpHS_p-F-D3sJZDVl2YQt"

BACKGROUND_IMAGE = "welcome.png"     # File ảnh thiết kế PowerPoint của bạn
FONT_PATH = "times.ttf"              # File font chữ (Times New Roman)

# --- TỌA ĐỘ VÀ KÍCH THƯỚC KHỚP VỚI BACKGROUND MỚI CỦA BẠN ---
AVATAR_CENTER_X = 678   # Vị trí tâm trục X của ô tròn xanh lá bên trái
AVATAR_CENTER_Y = 996   # Vị trí tâm trục Y của ô tròn xanh lá bên trái
AVATAR_SIZE = 890       # Kích thước avatar (hơi nhỏ hơn ô xanh một chút để lộ viền)

TEXT_CENTER_X = 2000     # Tâm trục X của khoảng trống bên phải (để căn giữa chữ)
TEXT_Y = 940            # Vị trí đặt chữ (ngay dưới dòng To Hung Server)
# =======================================================
intents = discord.Intents.default()
intents.members = True          # Bắt buộc để nhận sự kiện người mới vào
intents.message_content = True  # Bắt buộc để bot đọc được lệnh !welcome
bot = discord.Client(intents=intents)

def tao_anh_welcome(username, avatar_url):
    try:
        # Mở ảnh nền PowerPoint của bạn
        base_img = Image.open(BACKGROUND_IMAGE).convert("RGBA")
        W, H = base_img.size
        
        # Tải Avatar thành viên mới
        response = requests.get(avatar_url)
        avatar_raw = Image.open(io.BytesIO(response.content)).convert("RGBA")
        avatar_raw = avatar_raw.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
        
        # Cắt tròn Avatar bằng Mask mượt mà
        mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        
        avatar_round = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (0, 0, 0, 0))
        avatar_round.paste(avatar_raw, (0, 0), mask=mask)
        
        # Tính toán vị trí dán dựa trên tâm ô tròn xanh lá của bạn
        paste_x = AVATAR_CENTER_X - (AVATAR_SIZE // 2)
        paste_y = AVATAR_CENTER_Y - (AVATAR_SIZE // 2)
        base_img.paste(avatar_round, (paste_x, paste_y), avatar_round)
        
        # Viết tên thành viên mới vào khoảng trống bên phải
        draw_text = ImageDraw.Draw(base_img)
        font = ImageFont.truetype(FONT_PATH, 140) # Cỡ chữ 140 to rõ ràng
        
        welcome_text = f"{username}"
        text_box = draw_text.textbbox((0, 0), welcome_text, font=font)
        text_w = text_box[2] - text_box[0]
        
        # Căn chữ nằm chính giữa không gian trống bên phải
        text_x = TEXT_CENTER_X - (text_w // 2)
        
        # Vẽ chữ với màu trắng bạc đổ bóng nhẹ cho sang bọc với style PowerPoint
        draw_text.text((text_x + 2, TEXT_Y + 2), welcome_text, font=font, fill=(0, 0, 0, 150)) # Bóng đổ đen
        draw_text.text((text_x, TEXT_Y), welcome_text, font=font, fill=(241, 196, 15, 255))   # Chữ màu vàng Gold nổi bật
        
        output_path = "welcome_final.png"
        base_img.save(output_path)
        return output_path
    except Exception as e:
        print(f"❌ Lỗi xử lý đồ họa: {e}")
        return None

@bot.event
async def on_ready():
    print(f"🚀 Bot Welcome đã sẵn sàng hoạt động với tên: {bot.user}")

@bot.event
async def on_member_join(member):
    print(f"🔔 Thành viên mới gia nhập: {member.name}")
    
    avatar_url = member.display_avatar.url
    username = member.name
    
    file_anh = tao_anh_welcome(username, avatar_url)
    
    if file_anh:
        payload = {"content": f"🎉 Chào mừng **{member.mention}** đã đặt chân đến server của chúng mình!"}
        files = {"file": (file_anh, open(file_anh, "rb"), "image/png")}
        
        res = requests.post(WEBHOOK_URL, data=payload, files=files)
        if res.status_code in [200, 204]:
            print(f"✅ Đã bắn ảnh Welcome của {member.name} lên Discord thành công!")
        else:
            print(f"❌ Lỗi bắn Webhook: {res.status_code}")

# .... các đoạn code xử lý on_member_join và tao_anh_welcome ở phía trên giữ nguyên ....

# CHUYỂN HÀM ON_MESSAGE LÊN TRÊN (Sát lề trái, không thụt lề dòng @bot.event)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Chỉ nhận lệnh !welcome
    if message.content.strip() == "!welcome":
        await message.channel.send("🔄 Đang tạo ảnh test, đợi tí nhé thầy Hưng...")
        try:
            # Tạo ảnh
            file_anh = tao_anh_welcome(message.author.name, message.author.display_avatar.url)
            
            if file_anh and os.path.exists(file_anh):
                # Gửi file
                with open(file_anh, "rb") as f:
                    await message.channel.send(file=discord.File(f, "welcome_test.png"))
            else:
                await message.channel.send("❌ Không tìm thấy file ảnh.")
        except Exception as e:
            await message.channel.send(f"❌ Lỗi gửi ảnh: {e}")

# LUÔN ĐỂ DÒNG CHẠY BOT NÀY Ở DƯỚI CÙNG CỦA FILE
if __name__ == "__main__":
    bot.run(BOT_TOKEN)