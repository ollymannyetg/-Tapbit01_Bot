from telegram.ext import ChatMemberHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from db import conn, cursor
import time
from telegram.ext import MessageHandler, filters

import os
import re
import requests
from telegram.constants import ChatMemberStatus

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    if not data:
        cursor.execute("""
        INSERT INTO users (user_id, username, points, kyc_status, last_redeem, last_daily, streak)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username or "no_username",
            0,
            "normal",
            0,
            0,
            0
        ))
    else:
        cursor.execute("""
        UPDATE users SET username=? WHERE user_id=?
        """, (user.username or "no_username", user.id))

    conn.commit()

    await update.message.reply_text(
        "🚀 Welcome to Tapbit Rewards!\n\nUse /daily and /points",
    )
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute("SELECT points FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    if data:
        await update.message.reply_text(f"⭐ Your points: {data[0]}")
    else:
        await update.message.reply_text("Use /start first")
async def addpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 7356560699

    # ✅ Only admin allowed
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Not allowed")
        return

    try:
        # ✅ Check arguments
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addpoint @username 50")
            return

        username = context.args[0].replace("@", "")
        amount = int(context.args[1])

        # ✅ Get current points
        cursor.execute("SELECT points FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            await update.message.reply_text("❌ User not found. Ask them to /start")
            return

        old_points = user[0]

        # ✅ Update points
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE username=?",
            (amount, username)
        )
        conn.commit()

        new_points = old_points + amount

        # ✅ CLEAR RESPONSE
        await update.message.reply_text(
            f"✅ @{username}\n\n"
            f"Old Points: {old_points}\n"
            f"Added: +{amount}\n"
            f"New Points: {new_points}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # 🔒 Admin IDs (won’t appear)
        admin_ids = (7356560699,)  # add more if needed

        # 🧠 Handle query safely
        if admin_ids:
            placeholders = ",".join(["?"] * len(admin_ids))
            query = f"""
                SELECT username, points
                FROM users
                WHERE user_id NOT IN ({placeholders})
                ORDER BY points DESC
                LIMIT 15
            """
            cursor.execute(query, admin_ids)
        else:
            cursor.execute("""
                SELECT username, points
                FROM users
                ORDER BY points DESC
                LIMIT 15
            """)

        users = cursor.fetchall()

        # 🧾 Build message (NO Markdown = NO ERRORS)
        message = "🏆 Leaderboard\n\n"

        if not users:
            message += "No users yet."
        else:
            for i, user in enumerate(users, 1):
                name = user[0] if user[0] else "unknown"
                points = user[1]

                # 🥇 Top 3 styling
                if i == 1:
                    prefix = "🥇"
                elif i == 2:
                    prefix = "🥈"
                elif i == 3:
                    prefix = "🥉"
                else:
                    prefix = f"{i}."

                message += f"{prefix} @{name} — {points} pts\n"

        # ✅ SEND WITHOUT MARKDOWN
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ Leaderboard error:\n{e}")
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admin_id = 7356560699

    if context.args and user.id == admin_id:
        username = context.args[0].replace("@", "")
        cursor.execute("""
            SELECT username, points, exchange_uid, twitter_username, kyc_status 
            FROM users WHERE username=?
        """, (username,))
    else:
        cursor.execute("""
            SELECT username, points, exchange_uid, twitter_username, kyc_status 
            FROM users WHERE user_id=?
        """, (user.id,))

    data = cursor.fetchone()

    if not data:
        await update.message.reply_text("User not found")
        return

    username = data[0] or "no_username"
    uid = data[2] or "Not set"
    twitter = data[3] or "Not set"

    msg = f"""
👤 Profile

Username: @{username}
Points: {data[1]}
Tapbit UID: {uid}
Twitter: @{twitter}
Status: {data[4]}
"""

    await update.message.reply_text(msg)
async def verifykyc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 7356560699

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Not allowed")
        return

    if not context.args:
        await update.message.reply_text("Usage: /verifykyc @username")
        return

    username = context.args[0].replace("@", "")

    cursor.execute("""
        UPDATE users 
        SET kyc_status = 'verified', points = points + 50
        WHERE username = ?
    """, (username,))

    conn.commit()

    await update.message.reply_text(f"✅ @{username} KYC verified +50 points")
async def verifydeposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 7356560699

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Not allowed")
        return

    try:
        username = context.args[0].replace("@", "")

        cursor.execute("""
            UPDATE users 
            SET points = points + 100 
            WHERE username = ?
        """, (username,))
        conn.commit()

        await update.message.reply_text(f"💰 @{username} deposit verified +100 points")

    except:
        await update.message.reply_text("Usage: /verifydeposit @username")
async def verifytrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 7356560699

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Not allowed")
        return

    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])

        cursor.execute("""
            UPDATE users 
            SET points = points + ? 
            WHERE username = ?
        """, (amount, username))
        conn.commit()

        await update.message.reply_text(f"📈 @{username} trade verified +{amount} points")

    except:
        await update.message.reply_text("Usage: /verifytrade @username 30")
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not context.args:
        await update.message.reply_text("Usage: /redeem fee | vip | airdrop")
        return

    reward = context.args[0].lower()

    rewards = {
        "fee": 50,
        "vip": 200,
        "airdrop": 150
    }

    if reward not in rewards:
        await update.message.reply_text("❌ Invalid reward")
        return

    cost = rewards[reward]

    cursor.execute("SELECT points, last_redeem FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    if not data:
        await update.message.reply_text("Use /start first")
        return

    points, last_redeem = data
    now = int(time.time())

    if now - last_redeem < 3600:
        await update.message.reply_text("⏳ Wait before redeeming again")
        return

    if points < cost:
        await update.message.reply_text(f"❌ Not enough points. You need {cost}")
        return

    cursor.execute("""
        UPDATE users 
        SET points = points - ?, last_redeem = ?
        WHERE user_id = ?
    """, (cost, now, user.id))

    conn.commit()

    await update.message.reply_text(f"🎁 You redeemed {reward} successfully!")
async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
📋 DAILY TASKS

• /start → +10 points  
• /daily → bonus reward  
• Send messages → engagement  
• Participate in events → +10 points  

🔥 Complete tasks daily to earn more!
"""
    )
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        now = int(time.time())

        cursor.execute(
            "SELECT last_daily, streak, points FROM users WHERE user_id=?",
            (user.id,)
        )
        data = cursor.fetchone()

        # AUTO REGISTER if user not found
        if not data:
            cursor.execute("""
                INSERT INTO users 
                (user_id, username, points, kyc_status, last_redeem, last_daily, streak)
                VALUES (?, ?, 0, 'normal', 0, 0, 0)
            """, (user.id, user.username or "no_username"))
            conn.commit()

            last_daily, streak, points = 0, 0, 0
        else:
            last_daily, streak, points = data

        last_daily = last_daily or 0
        streak = streak or 0

        # already claimed
        if now - last_daily < 86400:
            await update.message.reply_text("⏳ Already claimed today")
            return

        # streak logic
        if last_daily != 0 and now - last_daily < 172800:
            streak += 1
        else:
            streak = 1

        reward = 20 + (streak * 2)

        cursor.execute("""
            UPDATE users 
            SET points = points + ?, last_daily = ?, streak = ?
            WHERE user_id = ?
        """, (reward, now, streak, user.id))

        conn.commit()

        await update.message.reply_text(
            f"🎁 Daily Reward: +{reward}\n🔥 Streak: {streak}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error in /daily:\n{e}")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    if update.effective_chat.type == "private":
        return

    user = update.effective_user
    message = update.message
    text = message.text

    if not text or text.startswith("/"):
        return
        
    # 📰 Any news
    if "any news" in text.lower():
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": "bitcoin,ethereum,solana",
                    "price_change_percentage": "24h"
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            message = "📰 <b>MARKET UPDATE</b>\n\n"

            for market in data:
                coin = market["symbol"].upper()
                price = market["current_price"]
                change = market["price_change_percentage_24h"]

                icon = "🟢" if change >= 0 else "🔴"

                message += (
                    f"💰 <b>{coin}/USDT</b>\n"
                    f"💵 Price: ${price:,.2f}\n"
                    f"{icon} 24H Change: {change:+.2f}%\n\n"
                )

            message += "⚡ <i>Market data powered by Tapbit</i>"

            await update.message.reply_text(
                message,
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"News/market error: {e}")
            await update.message.reply_text(
                "❌ Couldn't get the market update right now."
            )

        return
        
    # 🚀 Auto crypto price detection
    clean_text = text.upper().strip()

    clean_text = re.sub(r"[/\-]", " ", clean_text)
    clean_text = re.sub(r"\b(PRICE|VALUE|RATE|USDT)\b", "", clean_text)
    clean_text = re.sub(r"[^A-Z0-9]", "", clean_text)

    coin = clean_text

    coin_ids = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "PEPE": "pepe",
        "ZEC": "zcash",
        "ETC": "ethereum-classic",
        "ADA": "cardano",
        "TRX": "tron",
        "AVAX": "avalanche-2",
        "DOT": "polkadot",
        "LINK": "chainlink",
        "LTC": "litecoin",
        "BCH": "bitcoin-cash",
        "ATOM": "cosmos",
        "UNI": "uniswap",
        "AAVE": "aave",
        "NEAR": "near",
        "APT": "aptos",
        "ARB": "arbitrum",
        "OP": "optimism",
        "POL": "polygon-ecosystem-token"
    }

    stock_symbols = {
        "AAPL": "Apple",
        "TSLA": "Tesla",
        "NVDA": "NVIDIA",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "GOOGL": "Alphabet",
        "META": "Meta",
        "NFLX": "Netflix",
        "AMD": "AMD",
        "COIN": "Coinbase"
    }

    if coin in stock_symbols:
        print("🔥 STOCK CODE REACHED:", coin)
        try:
            api_key = os.getenv("ALPHA_VANTAGE_KEY")

            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": coin,
                    "apikey": api_key
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()
            print("ALPHA VANTAGE RESPONSE:", data)

            quote = data.get("Global Quote", {})

            if not quote:
                raise ValueError("No stock data returned")

            price = float(quote["05. price"])
            change = float(quote["09. change"])
            change_percent = quote["10. change percent"]

            icon = "🟢" if change >= 0 else "🔴"

            await update.message.reply_text(
                f"🏢 <b>{stock_symbols[coin]} ({coin})</b>\n\n"
                f"💵 <b>Price:</b> ${price:,.2f}\n"
                f"{icon} <b>Change:</b> {change:+,.2f} ({change_percent})\n\n"
                f"📈 <i>US Stock Market</i>",
                parse_mode="HTML"
            )

        except Exception as e:
            print("STOCK ERROR:", repr(e))
            await update.message.reply_text(
                f"❌ Couldn't get {coin} stock data right now."
            )

        return
    
    if coin in coin_ids:
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": coin_ids[coin],
                    "price_change_percentage": "24h"
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()
            market = data[0]

            price = market["current_price"]
            high_24h = market["high_24h"]
            low_24h = market["low_24h"]
            volume_24h = market["total_volume"]
            change_24h = market["price_change_percentage_24h"]

            # Smart price formatting
            def format_price(value):
                if value >= 1:
                    return f"${value:,.2f}"
                elif value >= 0.01:
                    return f"${value:,.4f}"
                elif value >= 0.0001:
                    return f"${value:,.6f}"
                else:
                    return f"${value:,.10f}"

            price_display = format_price(price)
            high_display = format_price(high_24h)
            low_display = format_price(low_24h)

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"🚀 Trade {coin} on Tapbit",
                        url="https://www.tapbit.com"
                    )
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            if change_24h >= 0:
                change_icon = "🟢"
            else:
                change_icon = "🔴"

            await update.message.reply_text(
                f"💰 <b>{coin}/USDT</b>\n\n"
                f"💵 <b>Price:</b> {price_display}\n"
                f"📈 <b>24H High:</b> {high_display}\n"
                f"📉 <b>24H Low:</b> {low_display}\n"
                f"📊 <b>24H Volume:</b> ${volume_24h:,.0f}\n"
                f"{change_icon} <b>24H Change:</b> {change_24h:+.2f}%\n\n"
                f"⚡ <i>Market data powered by Tapbit</i>",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        except Exception as e:
            print(f"Price error: {e}")
            await update.message.reply_text(
                f"❌ Couldn't get the {coin}/USDT market data right now."
            )

        return

    # Detect links
    link_pattern = re.compile(
        r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
        re.IGNORECASE
    )

    # Check if user is an admin
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user.id
    )

    is_admin = member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    )

    # Delete links from non-admins
    if link_pattern.search(text) and not is_admin:
        try:
            await message.delete()
            print(f"🚫 Deleted link from @{user.username}")
        except Exception as e:
            print(f"❌ Could not delete link: {e}")
        return

    # Normal message = +1 point
    now = int(time.time())

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, points, kyc_status, last_redeem, last_daily, streak, last_message)
        VALUES (?, ?, 0, 'normal', 0, 0, 0, 0)
    """, (user.id, user.username or "no_username"))

    cursor.execute("""
        UPDATE users
        SET points = points + 1,
            last_message = ?
        WHERE user_id = ?
    """, (now, user.id))

    conn.commit()
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
📌 *Tapbit Commands*

/start - Register  
/daily - Claim reward  
/points - Check balance  
/leaderboard - Top users  
/profile - Your info
/setuid [ENTER YOUR UID] -For uid registration
/settwitter [ENTER YOUR TWITTER HANDLE] -For X registration  

🔥 Stay active & earn more!
""",
        parse_mode="Markdown"
    )
async def welcome_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"""
🎉 Welcome {member.first_name}!

🚀 Type /start to join Tapbit Rewards  
💰 Start earning points instantly  
🏆 Compete on leaderboard
""",
            parse_mode="Markdown"
        )
async def setuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not context.args:
        await update.message.reply_text("Usage: /setuid YOUR_EXCHANGE_UID")
        return

    uid = context.args[0]

    cursor.execute("""
        UPDATE users SET exchange_uid=? WHERE user_id=?
    """, (uid, user.id))

    conn.commit()


    await update.message.reply_text(f"✅ Exchange UID saved: {uid}")
async def settwitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not context.args:
        await update.message.reply_text("Usage: /settwitter your_username")
        return

    twitter = context.args[0].replace("@", "")

    if len(twitter) < 3 or len(twitter) > 15:
        await update.message.reply_text("❌ Invalid username length (3–15 chars)")
        return

    if not twitter.replace("_", "").isalnum():
        await update.message.reply_text("❌ Only letters, numbers, underscores allowed")
        return

    cursor.execute("""
        UPDATE users SET twitter_username=? WHERE user_id=?
    """, (twitter, user.id))

    conn.commit()

    # ✅ THIS WAS MISSING
    await update.message.reply_text(f"✅ Twitter username saved: @{twitter}")
async def removepoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 7356560699

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Not allowed")
        return

    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])

        cursor.execute("SELECT points FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            await update.message.reply_text("User not found")
            return

        old_points = user[0]

        cursor.execute(
            "UPDATE users SET points = points - ? WHERE username=?",
            (amount, username)
        )
        conn.commit()

        new_points = old_points - amount

        await update.message.reply_text(
            f"❌ @{username}\n\n"
            f"Old Points: {old_points}\n"
            f"Removed: -{amount}\n"
            f"New Points: {new_points}"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


    await update.message.reply_text(f"✅ Twitter username saved: @{twitter}")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("points", points))
app.add_handler(CommandHandler("addpoint", addpoint))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("verifykyc", verifykyc))
app.add_handler(CommandHandler("verifydeposit", verifydeposit))
app.add_handler(CommandHandler("verifytrade", verifytrade))
app.add_handler(CommandHandler("redeem", redeem))
app.add_handler(CommandHandler("tasks", tasks))
app.add_handler(CommandHandler("daily", daily))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new))
app.add_handler(CommandHandler("setuid", setuid))
app.add_handler(CommandHandler("settwitter", settwitter))
app.add_handler(CommandHandler("removepoint", removepoint))

import asyncio

async def main():
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        print("✅ BOT STARTED SUCCESSFULLY")

        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("🔥 CRASH ERROR:", e)
