import asyncio, os, uuid
from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.environ["BOT_TOKEN"]

FONT_PATH = "BebasNeue-Regular.ttf"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

MAX_SIZE = 120
MIN_SIZE = 24
PAD = 12


def fit_font(draw, text, w, size=MAX_SIZE):
    while size > MIN_SIZE:
        f = ImageFont.truetype(FONT_PATH, size)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= w - 2 * PAD:
            return f
        size -= 2
    return ImageFont.truetype(FONT_PATH, MIN_SIZE)


def wrap(text, draw, font, w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        test = (cur + " " + word).strip()
        b = draw.textbbox((0, 0), test, font=font)
        if b[2] - b[0] <= w - 2 * PAD:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_line(draw, xy, text, font):
    x, y = xy
    s = max(2, font.size // 15)
    for dx in range(-s, s + 1):
        for dy in range(-s, s + 1):
            draw.text((x + dx, y + dy), text, font=font, fill="black", anchor="ma")
    draw.text((x, y), text, font=font, fill="white", anchor="ma")


def make_meme(img_bytes, top, bottom):
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    W, H = img.size
    d = ImageDraw.Draw(img)

    if top:
        f = fit_font(d, top, W)
        y = PAD
        for line in wrap(top, d, f, W):
            draw_line(d, (W // 2, y), line, f)
            b = d.textbbox((0, 0), line, font=f)
            y += (b[3] - b[1]) + 5

    if bottom:
        f = fit_font(d, bottom, W)
        lines = wrap(bottom, d, f, W)
        hs = [d.textbbox((0, 0), ln, font=f)[3] - d.textbbox((0, 0), ln, font=f)[1] + 5 for ln in lines]
        y = H - PAD - sum(hs)
        for line in lines:
            draw_line(d, (W // 2, y), line, f)
            b = d.textbbox((0, 0), line, font=f)
            y += (b[3] - b[1]) + 5

    out = BytesIO()
    img.save(out, "JPEG", quality=92)
    return out.getvalue()


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "Кинь фото с подписью — сделаю мем Impact.\n"
        "Разделитель | делит верх и низ.\n"
        "Пример: когда открыл телеграм | и не закрыл"
    )


@dp.message(F.photo)
async def photo(m: Message):
    if not m.caption:
        await m.answer("Добавь подпись к фото.")
        return
    if "|" in m.caption:
        top, bottom = [p.strip() for p in m.caption.split("|", 1)]
    else:
        top, bottom = m.caption.strip(), ""

    buf = BytesIO()
    await bot.download(m.photo[-1], destination=buf)
    try:
        result = await asyncio.to_thread(make_meme, buf.getvalue(), top, bottom)
        await m.reply_photo(BufferedInputFile(result, filename="meme.jpg"))
    except Exception as e:
        await m.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
