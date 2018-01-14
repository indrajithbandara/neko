"""
Tag implementation using PostgreSQL backend for storage and management.
"""
import neko

# Creates the tables we need.
_create_tables = '''
    CREATE TABLE IF NOT EXISTS local_tags (
      -- Tag names must be unique, so might as well
      -- use this for the PK.
      tag_name     VARCHAR(30)    PRIMARY KEY
                                  CONSTRAINT not_whitespace_name CHECK (
                                    TRIM(tag_name) <> ''
                                  ),
      -- Snowflake
      tag_author   BIGINT         NOT NULL,
    
      -- Snowflake
      tag_guild    BIGINT         NOT NULL,
      
      -- Tag content. Allow up to 1800 characters.
      tag_content  VARCHAR(1800)  CONSTRAINT not_whitespace_cont CHECK (
                                    TRIM(tag_content) <> ''
                                  )
    );
    
    CREATE TABLE IF NOT EXISTS global_tags (
      -- Tag names must be unique, so might as well
      -- use this for the PK.
      tag_name     VARCHAR(30)    PRIMARY KEY
                                  CONSTRAINT not_whitespace_name CHECK (
                                    TRIM(tag_name) <> ''
                                  ),
      -- Snowflake
      tag_author   BIGINT         NOT NULL,
    
      -- Tag content. Allow up to 1800 characters.
      tag_content  VARCHAR(1800)  CONSTRAINT not_whitespace_cont CHECK (
                                    TRIM(tag_content) <> ''
                                  )
);'''


@neko.inject_setup
class TagCog(neko.Cog):
    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

    async def on_connect(self):
        """Ensures the tables actually exist."""

        self.logger.info('Ensuring tables exist')
        async with self.bot.postgres_pool as pool:
            async with pool.acquire() as conn:
                await conn.execute(_create_tables)
        self.logger.info('Tables should now exist if they didn\'t already.')

    @neko.group(
        name='tag',
        brief='Text tags that can be defined and retrieved later',
        invoke_without_command=True
    )
    async def tag_group(self, ctx):
        page = neko.Page(title='Available tag commands')

        description = []

        for command in self.tag_group.commands:
            if await command.can_run(ctx):
                description.append(f'`{command.name}` - {command.brief}')

        page.description = '\n'.join(sorted(description))

        await ctx.send(embed=page)

    @tag_group.command(
        name='add',
        brief='Add a local tag for this server')
    async def tag_add(self, ctx, name, *, content):
        async with self.bot.postgres_pool as pool:
            async with pool.acquire():
                pass
