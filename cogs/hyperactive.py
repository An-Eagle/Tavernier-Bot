from discord import Cog, Bot, Member, VoiceState
from data.config import STREAK_SAVE_FILE, STREAK_DATA, STREAK_WEEK_DAY, STREAK_HYPERACTIVE, HYPERACTIVE_ROLE, STREAK_TIME_MIN, REDIRECT_VOICE_CHANNEL
from my_utils import log
from typing import Union
import datetime as dt
import json


def read_data(member: Member = None, *, field: str = None) -> Union[dict, int, float]:
    """Get either the entire data, a member's data, or only a field"""

    with open(STREAK_SAVE_FILE, 'r') as file:
        data: dict = json.load(file)
    
    value = data.copy()
    
    if member:
        value = data.get(str(member.id), None)
        
        if value is None: # Handling member not already known
            update_data(member, STREAK_DATA)
            value = STREAK_DATA
        
        if field:
            value = value.get(field, None)
    
    return value


def update_data(member: Member, member_data, *, field: str = None):
    """Update either the data, or only a field, of a member"""

    data = read_data()
    
    if field:
        assert type(member_data) in (int, float)
        data[str(member.id)][field] = member_data
    else:
        assert type(member_data) is dict
        data[str(member.id)] = member_data
    
    with open(STREAK_SAVE_FILE, 'w') as file:
        json.dump(data, file)


async def reset_progress(member: Member):
    """Reset the streak of a member, and remove the hyperactive role from him if needed"""

    role = member.guild.get_role(HYPERACTIVE_ROLE)
    streak = read_data(member, field="streak")
    
    await member.remove_roles(role, reason=f"Lost a streak of {streak}")
    log(member, "lost a streak of", streak)
    
    update_data(member, 0, field="streak")


def update_last(member: Member):
    timestamp = dt.datetime.utcnow().timestamp()
    update_data(member, timestamp, field="last")


def check_expired(member: Member) -> bool:
    """Check if a member has exceeded the time limit to increase his streak. Return False if the member is new"""

    if (timestamp := read_data(member, field="last")) == 0:
        return False
    
    last_update = dt.datetime.fromtimestamp(timestamp)
    return streak_day() >= last_update


def check_reached(member: Member) -> bool:
    """Check if a member has reached the time needed to aquire the hyperactive role"""

    time = dt.timedelta(hours=read_data(member, field="time"))
    return time >= STREAK_TIME_MIN


async def update_time(member: Member):
    """Add the time spent between now and the connection of a member to his progress"""

    member_data = read_data(member)
    last = dt.datetime.fromtimestamp(member_data.get("last"))
    now = dt.datetime.utcnow()
    
    session = (now - last) / dt.timedelta(hours=1)  # Convert into hours
    time = member_data.get("time", 0) + session
    update_data(member, time, field="time")
    
    if check_reached(member):
        await increase_streak(member)


def add_time(member: Member, value: Union[float, dt.timedelta]):
    """Add a specific value (number of hours, or timedelta) to a member's time"""

    time: float = read_data(member, field="time")
    
    if type(value) is float:
        time += value
    elif type(value) is dt.timedelta:
        time += value / dt.timedelta(hours=1)
    
    update_data(member, time, field="time")


async def increase_streak(member: Member):
    """Increase the streak of a member and give him the hyperactive role if needed"""

    streak = read_data(member, field="streak")
    update_data(member, streak + 1, field="streak")
    
    if streak < STREAK_HYPERACTIVE <= streak + 1:
        role = member.guild.get_role(HYPERACTIVE_ROLE)
        await member.add_roles(role)
        log(member, "got the hyperactive role")


def streak_day() -> dt.datetime:
    """Return a datetime object for the last day where streaks have been updated"""

    now = dt.datetime.utcnow()
    return now + dt.timedelta(days=STREAK_WEEK_DAY - now.weekday())


async def handle_midnight(member):
    """Handle the case where a member connected before and left after midnight on reset day"""

    now = dt.datetime.utcnow()
    last = dt.datetime.fromtimestamp(read_data(member, field="last"))
    add_time(member, streak_day() - last)
    
    if check_reached(member):
        await increase_streak(member)
    else:
        await reset_progress(member)
    
    update_data(member, now - streak_day(), "time")



class Hyperactive(Cog):
    """Rôle Hyperactif automatique"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot or (before.channel and before.channel.id == REDIRECT_VOICE_CHANNEL):
            return
        
        # When a channel is left
        if before.channel:
            if after.channel and before.channel == after.channel:
                return
            
            if check_expired(member):
                await handle_midnight(member)
            else:
                await update_time(member)
        
        update_last(member)
        


def setup(bot: Bot):
    bot.add_cog(Hyperactive(bot))
    print(" - Hyperactive")