"""
Run once to populate quests, World Cup matches, and starter Flash Cards.
Usage:  python -m app.seed_goat
"""
from datetime import datetime
from .database import SessionLocal, engine
from . import models_goat  # ensure tables are registered
from .database import Base
from .models_goat import Quest, WorldCupMatch, FlashCard

Base.metadata.create_all(bind=engine)

QUESTS = [
    # easy
    dict(title="First Touch",        description="Send a voice message to someone you haven't spoken to in a while.",                     xp_reward=30,  token_reward=5,  category="social",    difficulty="easy",      football_theme=False),
    dict(title="Opening Whistle",    description="Write down your #1 goal for this week. Be specific.",                                  xp_reward=30,  token_reward=5,  category="personal",  difficulty="easy",      football_theme=False),
    dict(title="Warm Up",            description="Do 15 minutes of something physical right now. No excuses.",                            xp_reward=30,  token_reward=5,  category="personal",  difficulty="easy",      football_theme=False),
    dict(title="Match Day Energy",   description="Wake up, cold shower, set your intention before checking your phone.",                  xp_reward=40,  token_reward=8,  category="personal",  difficulty="easy",      football_theme=True),
    # normal
    dict(title="The Assist",         description="Help someone today without being asked or expecting anything in return.",               xp_reward=50,  token_reward=10, category="social",    difficulty="normal",    football_theme=False),
    dict(title="Man Marking",        description="Spend 2 hours completely phone-free. Be present.",                                      xp_reward=50,  token_reward=10, category="personal",  difficulty="normal",    football_theme=True),
    dict(title="Through Ball",       description="Give someone an honest compliment they wouldn't expect. Mean it.",                     xp_reward=50,  token_reward=10, category="social",    difficulty="normal",    football_theme=False),
    dict(title="Set Piece",          description="Plan something spontaneous and execute it today. No overthinking.",                     xp_reward=60,  token_reward=12, category="creative",  difficulty="normal",    football_theme=False),
    dict(title="Captain's Armband",  description="Lead by example today — let your actions do the talking.",                              xp_reward=60,  token_reward=12, category="career",    difficulty="normal",    football_theme=True),
    dict(title="Pressing Game",      description="Tackle one task you've been avoiding for more than a week.",                            xp_reward=70,  token_reward=15, category="career",    difficulty="normal",    football_theme=True),
    # hard
    dict(title="Hat Trick",          description="Complete 3 tasks you've been procrastinating on. All 3. Today.",                        xp_reward=100, token_reward=25, category="personal",  difficulty="hard",      football_theme=True),
    dict(title="Counter Press",      description="Cold approach — start a genuine conversation with a complete stranger.",                xp_reward=120, token_reward=30, category="social",    difficulty="hard",      football_theme=False),
    dict(title="Golden Boot",        description="Share something you created with the world. Post it. Publish it. Ship it.",             xp_reward=150, token_reward=35, category="creative",  difficulty="hard",      football_theme=True),
    dict(title="Extra Time",         description="Stay 2 hours extra focused on your most important project. No distractions.",           xp_reward=100, token_reward=25, category="career",    difficulty="hard",      football_theme=True),
    # legendary
    dict(title="GOAT Move",          description="Do one thing today that scares you but you know you need to do. No safety net.",        xp_reward=250, token_reward=75, category="personal",  difficulty="legendary", football_theme=True),
    dict(title="World Cup Final",    description="Write your legacy — in 200 words, what do you want to be remembered for?",              xp_reward=300, token_reward=100,category="personal",  difficulty="legendary", football_theme=True),
    dict(title="Penalty Shootout",   description="Have the hard conversation you've been avoiding. Be honest, be kind, be brave.",        xp_reward=200, token_reward=60, category="social",    difficulty="legendary", football_theme=True),
]

# FIFA World Cup 2026 — key matches (update with official schedule as needed)
# Host countries: USA, Canada, Mexico | Start date: June 11, 2026
WC_MATCHES = [
    # Opening match
    dict(match_number=1,  team_home="Mexico",      team_away="Ecuador",    flag_home="🇲🇽", flag_away="🇪🇨", match_date=datetime(2026, 6, 11, 20, 0), stadium="Estadio Azteca",         city="Mexico City",  country="Mexico",  stage="group", group_name="A"),
    dict(match_number=2,  team_home="USA",          team_away="Bolivia",    flag_home="🇺🇸", flag_away="🇧🇴", match_date=datetime(2026, 6, 12, 18, 0), stadium="SoFi Stadium",           city="Los Angeles",  country="USA",     stage="group", group_name="B"),
    dict(match_number=3,  team_home="Canada",       team_away="Morocco",    flag_home="🇨🇦", flag_away="🇲🇦", match_date=datetime(2026, 6, 12, 21, 0), stadium="BMO Field",              city="Toronto",      country="Canada",  stage="group", group_name="C"),
    dict(match_number=4,  team_home="Brazil",       team_away="Germany",    flag_home="🇧🇷", flag_away="🇩🇪", match_date=datetime(2026, 6, 13, 18, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="group", group_name="D"),
    dict(match_number=5,  team_home="Argentina",    team_away="Nigeria",    flag_home="🇦🇷", flag_away="🇳🇬", match_date=datetime(2026, 6, 13, 21, 0), stadium="AT&T Stadium",          city="Dallas",       country="USA",     stage="group", group_name="E"),
    dict(match_number=6,  team_home="France",       team_away="Portugal",   flag_home="🇫🇷", flag_away="🇵🇹", match_date=datetime(2026, 6, 14, 18, 0), stadium="Mercedes-Benz Stadium", city="Atlanta",      country="USA",     stage="group", group_name="F"),
    dict(match_number=7,  team_home="Spain",        team_away="Japan",      flag_home="🇪🇸", flag_away="🇯🇵", match_date=datetime(2026, 6, 14, 21, 0), stadium="Levi's Stadium",        city="San Francisco",country="USA",     stage="group", group_name="G"),
    dict(match_number=8,  team_home="England",      team_away="Senegal",    flag_home="🏴󠁧󠁢󠁥󠁮󠁧󠁿", flag_away="🇸🇳", match_date=datetime(2026, 6, 15, 18, 0), stadium="BC Place",              city="Vancouver",    country="Canada",  stage="group", group_name="H"),
    dict(match_number=9,  team_home="Netherlands",  team_away="Colombia",   flag_home="🇳🇱", flag_away="🇨🇴", match_date=datetime(2026, 6, 15, 21, 0), stadium="Estadio Akron",         city="Guadalajara",  country="Mexico",  stage="group", group_name="I"),
    dict(match_number=10, team_home="Italy",        team_away="Uruguay",    flag_home="🇮🇹", flag_away="🇺🇾", match_date=datetime(2026, 6, 16, 18, 0), stadium="Estadio BBVA",          city="Monterrey",    country="Mexico",  stage="group", group_name="J"),
    dict(match_number=11, team_home="Portugal",     team_away="USA",        flag_home="🇵🇹", flag_away="🇺🇸", match_date=datetime(2026, 6, 22, 18, 0), stadium="Arrowhead Stadium",     city="Kansas City",  country="USA",     stage="group", group_name="F"),
    dict(match_number=12, team_home="Argentina",    team_away="Brazil",     flag_home="🇦🇷", flag_away="🇧🇷", match_date=datetime(2026, 6, 28, 21, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="group", group_name="E"),
    # Knockout placeholders (teams TBD after group stage)
    dict(match_number=49, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 4,  18, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="r32",   group_name=None),
    dict(match_number=57, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 10, 18, 0), stadium="AT&T Stadium",          city="Dallas",       country="USA",     stage="r16",   group_name=None),
    dict(match_number=61, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 14, 18, 0), stadium="SoFi Stadium",          city="Los Angeles",  country="USA",     stage="qf",    group_name=None),
    dict(match_number=63, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 18, 18, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="sf",    group_name=None),
    dict(match_number=64, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 19, 15, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="sf",    group_name=None),
    dict(match_number=65, team_home="TBD",          team_away="TBD",        flag_home="🏳", flag_away="🏳",  match_date=datetime(2026, 7, 26, 16, 0), stadium="MetLife Stadium",        city="New York",     country="USA",     stage="final", group_name=None),
]

FLASH_CARDS = [
    dict(name="Lionel Messi - GOAT Edition",   description="The greatest of all time. 2022 Champion.",
         rarity="legendary", card_type="player",  token_price=500, supply=100,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Lionel_Messi_20180626.jpg/300px-Lionel_Messi_20180626.jpg",
         card_metadata={"nation": "Argentina", "wc_wins": 1}),
    dict(name="Cristiano Ronaldo - Legacy",    description="Legacy card for the all-time top scorer.",
         rarity="legendary", card_type="player",  token_price=500, supply=100,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Cristiano_Ronaldo_2018.jpg/300px-Cristiano_Ronaldo_2018.jpg",
         card_metadata={"nation": "Portugal",  "goals": 900}),
    dict(name="Vinicius Jr - Villain Arc",     description="Activated his villain arc and never looked back.",
         rarity="epic",      card_type="player",  token_price=200, supply=500,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Vinicius_Jr_2021.jpg/300px-Vinicius_Jr_2021.jpg",
         card_metadata={"nation": "Brazil",    "position": "LW"}),
    dict(name="Jude Bellingham - Era",         description="He defined a generation. His era is now.",
         rarity="epic",      card_type="player",  token_price=200, supply=500,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jude_Bellingham_England_2022.jpg/300px-Jude_Bellingham_England_2022.jpg",
         card_metadata={"nation": "England",   "position": "CM"}),
    dict(name="Kylian Mbappé - Speed Run",     description="Fastest man in football. Legendary pace card.",
         rarity="epic",      card_type="player",  token_price=200, supply=500,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Kylian_Mbapp%C3%A9_2018.jpg/300px-Kylian_Mbapp%C3%A9_2018.jpg",
         card_metadata={"nation": "France",    "position": "ST"}),
    dict(name="Estadio Azteca - Opening Night",description="The legendary venue where WC 2026 kicks off.",
         rarity="rare",      card_type="stadium", token_price=75,  supply=2000,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Estadio_Azteca_-_Vista_lateral.jpg/300px-Estadio_Azteca_-_Vista_lateral.jpg",
         card_metadata={"city": "Mexico City", "capacity": 83000}),
    dict(name="MetLife Stadium - The Final",   description="Where legends become GOATs. WC 2026 Final venue.",
         rarity="rare",      card_type="stadium", token_price=75,  supply=2000,
         image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/MetLife_Stadium.jpg/300px-MetLife_Stadium.jpg",
         card_metadata={"city": "New York",    "capacity": 82500}),
    dict(name="Total Press - Tactic Card",     description="High press, no mercy. Villain Arc approved.",
         rarity="rare",      card_type="tactic",  token_price=50,  supply=None, card_metadata={"style": "high-press"}),
    dict(name="Tiki-Taka - Tactic Card",       description="Control the game. Control your life.",
         rarity="common",    card_type="tactic",  token_price=25,  supply=None, card_metadata={"style": "possession"}),
    dict(name="Counter-Attack - Tactic Card",  description="Let them come. Strike when it matters.",
         rarity="common",    card_type="tactic",  token_price=25,  supply=None, card_metadata={"style": "counter"}),
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Quest).count() == 0:
            for q in QUESTS:
                db.add(Quest(**q))
            print(f"Seeded {len(QUESTS)} quests")

        if db.query(WorldCupMatch).count() == 0:
            for m in WC_MATCHES:
                db.add(WorldCupMatch(**m))
            print(f"Seeded {len(WC_MATCHES)} World Cup matches")

        if db.query(FlashCard).count() == 0:
            for c in FLASH_CARDS:
                db.add(FlashCard(**c))
            print(f"Seeded {len(FLASH_CARDS)} Flash Cards")
        else:
            # Always sync image_url from seed data (fixes wrong/outdated URLs)
            updated = 0
            for card_data in FLASH_CARDS:
                if not card_data.get("image_url"):
                    continue
                card = db.query(FlashCard).filter(FlashCard.name == card_data["name"]).first()
                if card and card.image_url != card_data["image_url"]:
                    card.image_url = card_data["image_url"]
                    updated += 1
            if updated:
                print(f"Updated image_url for {updated} Flash Cards")

        db.commit()
        print("Seed complete ✅")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
