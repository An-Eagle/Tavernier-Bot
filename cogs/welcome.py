from discord import Bot, Cog, Member, Embed, Guild, Color

guild_id = 807743905121566720
welcome_channel_id = 807900462794932236
roles_channel_id = 915562589193392138


class Welcome(Cog):
    """Message de bienvenue"""

    def __init__(self, bot):
        self.bot: Bot = bot


    @Cog.listener()
    async def on_member_join(self, member: Member):
        guild: Guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(welcome_channel_id)

        if member.guild != guild:
            return

        if not member.bot:
            embed = Embed(
                title = f"Bienvenue à {member}",
                description = f"{member.mention} viens d'arriver dans la Taverne !",
                color = Color.blurple()
            )
        else:
            embed = Embed(
                title = f"Nouveau bot 🤖 {member}",
                description = f"{member.mention} viens d'être ajouté dans la Taverne !",
                color = Color.blurple()
            )

        embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Welcome(bot))
    print(" - Welcome")
