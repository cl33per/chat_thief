from chat_thief.models.user import User

BOTS_AND_CREATORS = {
    "aquafunkalisticbootywhap": "aquafunkbot",
    "ravonus": "r4vb0t",
    "beginbot": "beginbotbot",
    "bopojoe_": "cykablondesbot",
    "isidentical": "stallmansbot",
    "disk1of5": "disk_bot",
    "jr_boss": "jr_bots",
    "cachesking": "distributedcache",
    "whatsinmyopsec": "opsecbot",
    "zanuss": "zanussbot",
    "baldclap": "cheb0t",
    "nomorequity": "nomoreb0t",
    "r_u_ri_ui": "hal9thou",
}


def register_them_bots():
    for creator, bot in BOTS_AND_CREATORS.items():
        print(f"Registering: {bot} to it's Creator: {creator}")
        User.register_bot(bot, creator)


if __name__ == "__main__":
    register_them_bots()
