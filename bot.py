from telegram.ext import ChatMemberHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import conn, cursor
import time
from telegram.ext import MessageHandler, filters

import os
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

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not allowed")
        return

    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            await update.message.reply_text("❌ User not found. Ask them to /start first")
            return

        cursor.execute(
            "UPDATE users SET points = points + ? WHERE username = ?",
            (amount, username)
        )
        conn.commit()

        await update.message.reply_text(f"✅ Added {amount} points to @{username}")

    except:
        await update.message.reply_text("Usage: /addpoint @username 10")
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 15")
    users = cursor.fetchall()

    message = "🏆 Leaderboard\n\n"

    for i, user in enumerate(users, 1):
        name = user[0] if user[0] else "unknown"
        message += f"{i}. @{name} - {user[1]} pts\n"

    await update.message.reply_text(message)
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
Exchange UID: {uid}
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

    user = update.effective_user
    text = update.message.text

    if not text or text.startswith("/"):
        return

    now = int(time.time())

    # AUTO REGISTER
    cursor.execute("""
        INSERT OR IGNORE INTO users 
        (user_id, username, points, kyc_status, last_redeem, last_daily, streak, last_message)
        VALUES (?, ?, 0, 'normal', 0, 0, 0, 0)
    """, (user.id, user.username or "no_username"))

    # CHECK COOLDOWN
    cursor.execute("SELECT last_message FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    if data and data[0] and now - data[0] < 10:
        return  # ⛔ ignore spam (10 sec cooldown)

    # GIVE POINT
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
/Leaderboard - Top users  
/profile - Your info
/setuid [ENTER YOUR UID] -For uid registration  

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

    # ✅ BASIC VALIDATION
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

import asyncio

if __name__ == "__main__":
    asyncio.run(app.run_polling())