#!/usr/bin/env python3
"""Generate the Ghost of Radio PDF guide using reportlab."""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import Color
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import os

# Page dimensions
PAGE_W, PAGE_H = LETTER

# Colors
BG = Color(10/255, 10/255, 10/255)
GOLD = Color(201/255, 168/255, 76/255)
CREAM = Color(232/255, 224/255, 208/255)
DIM = Color(168/255, 158/255, 140/255)
CARD_BG = Color(26/255, 26/255, 26/255)
BORDER = Color(42/255, 37/255, 32/255)

# Margins
LEFT = 1.0 * inch
RIGHT = PAGE_W - 1.0 * inch
TOP = PAGE_H - 0.85 * inch
BOTTOM = 1.0 * inch
TEXT_W = RIGHT - LEFT

OUTPUT_DIR = "/Users/mac1/Projects/ghostofradio/downloads"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "ghost-of-radio-guide.pdf")


class PDFGuide:
    def __init__(self):
        self.c = canvas.Canvas(OUTPUT_PATH, pagesize=LETTER)
        self.c.setTitle("The Golden Age of Radio - Your Essential Guide")
        self.c.setAuthor("Ghost of Radio")
        self.page_num = 0
        self.y = TOP

    def _draw_bg(self):
        self.c.setFillColor(BG)
        self.c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def _draw_footer(self):
        self.c.setFillColor(GOLD)
        self.c.setFont("Helvetica", 8)
        self.c.drawCentredString(PAGE_W / 2, 0.5 * inch, f"- {self.page_num} -")
        self.c.setFillColor(DIM)
        self.c.setFont("Helvetica", 7)
        self.c.drawCentredString(PAGE_W / 2, 0.35 * inch, "ghostofradio.com")

    def new_page(self):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self._draw_bg()
        self.y = TOP

    def gold_rule(self, y=None, width=None, thickness=0.5):
        if y is None:
            y = self.y
        w = width or TEXT_W
        x = LEFT + (TEXT_W - w) / 2
        self.c.setStrokeColor(GOLD)
        self.c.setLineWidth(thickness)
        self.c.line(x, y, x + w, y)
        self.y = y - 12

    def draw_heading(self, text, size=20, spacing_after=16):
        self.c.setFillColor(GOLD)
        self.c.setFont("Helvetica-Bold", size)
        self.c.drawString(LEFT, self.y, text.upper())
        self.y -= spacing_after

    def draw_centered_text(self, text, font, size, color, y=None):
        if y is not None:
            self.y = y
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        self.c.drawCentredString(PAGE_W / 2, self.y, text)
        self.y -= size + 4

    def draw_body(self, text, color=None, font="Times-Roman", size=10.5,
                  leading=15, indent=0, max_width=None):
        if color is None:
            color = CREAM
        w = max_width or (TEXT_W - indent)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        lines = simpleSplit(text, font, size, w)
        for line in lines:
            if self.y < BOTTOM + 10:
                self._draw_footer()
                self.new_page()
            self.c.drawString(LEFT + indent, self.y, line)
            self.y -= leading
        self.y -= 4  # paragraph spacing

    def draw_card(self, title, body, title_size=11):
        """Draw a card-style block with gold title and cream body."""
        # Estimate height needed
        lines_body = simpleSplit(body, "Times-Roman", 10, TEXT_W - 24)
        needed = title_size + 8 + len(lines_body) * 14 + 20
        if self.y - needed < BOTTOM:
            self._draw_footer()
            self.new_page()

        card_top = self.y + 8
        card_bottom = self.y - needed + 12

        # Card background
        self.c.setFillColor(CARD_BG)
        self.c.setStrokeColor(BORDER)
        self.c.setLineWidth(0.5)
        self.c.roundRect(LEFT - 6, card_bottom, TEXT_W + 12,
                         card_top - card_bottom, 4, fill=1, stroke=1)

        # Title
        self.c.setFillColor(GOLD)
        self.c.setFont("Helvetica-Bold", title_size)
        self.c.drawString(LEFT + 6, self.y, title.upper())
        self.y -= title_size + 6

        # Body
        self.c.setFillColor(CREAM)
        self.c.setFont("Times-Roman", 10)
        for line in lines_body:
            self.c.drawString(LEFT + 6, self.y, line)
            self.y -= 14

        self.y -= 10

    def save(self):
        self._draw_footer()
        self.c.save()

    # ---- PAGE BUILDERS ----

    def page_cover(self):
        self.new_page()
        # No page number on cover, we'll override footer
        y = PAGE_H * 0.65
        self.draw_centered_text("THE GOLDEN AGE", "Helvetica-Bold", 42, GOLD, y)
        self.draw_centered_text("OF RADIO", "Helvetica-Bold", 42, GOLD)
        self.y -= 20
        self.gold_rule(self.y, width=3 * inch, thickness=1.0)
        self.y -= 20
        self.draw_centered_text("Your Essential Guide to Classic Old Time Radio",
                                "Times-Roman", 14, CREAM)
        self.y -= 60
        self.draw_centered_text("Ghost of Radio  |  ghostofradio.com",
                                "Helvetica", 10, DIM)

    def page_introduction(self):
        self.new_page()
        self.draw_heading("WHY OLD TIME RADIO STILL MATTERS", 18)
        self.y -= 4
        self.gold_rule(thickness=0.5)
        self.y -= 8

        paras = [
            "Before television colonized American living rooms, before streaming algorithms decided what you\u2019d watch next, there was radio. Just a voice in the dark, a few sound effects, and your imagination doing all the heavy lifting. For three remarkable decades \u2014 roughly 1930 to 1960 \u2014 radio drama wasn\u2019t just entertainment. It was the shared heartbeat of a nation. Families gathered around glowing dials in darkened parlors, and for thirty minutes at a time, the whole world disappeared.",
            "What made those broadcasts extraordinary wasn\u2019t technical sophistication \u2014 it was intimacy. A whispered confession, the creak of a door, footsteps on wet pavement. Radio forced listeners to build the scene in their own minds, and that collaboration between storyteller and audience created something no visual medium has ever matched. The theater of the mind doesn\u2019t age. It doesn\u2019t need CGI upgrades or HD remasters. A great radio drama recorded in 1948 can still pin you to your chair today.",
            "This guide is your entry point into that world. Whether you\u2019re a curious newcomer or a longtime listener looking for your next obsession, we\u2019ve curated the essential shows, episodes, and history you need. The Golden Age may be over, but its ghosts are still broadcasting \u2014 if you know where to tune in."
        ]
        for p in paras:
            self.draw_body(p, size=11, leading=16)
            self.y -= 6

    def page_top10_shows(self):
        shows = [
            ("SUSPENSE (CBS, 1942\u20131962)",
             "The master of tension. For twenty years, Suspense delivered weekly doses of psychological terror that left listeners white-knuckled and breathless. From Agnes Moorehead\u2019s legendary one-woman performance in \u2018Sorry, Wrong Number\u2019 to tales of paranoia, murder, and impossible choices, this is where radio drama reached its apex."),
            ("THE SHADOW (Mutual Broadcasting, 1937\u20131954)",
             "\u2018Who knows what evil lurks in the hearts of men?\u2019 Orson Welles first spoke those words, and they still echo. Lamont Cranston\u2019s ability to cloud men\u2019s minds made him radio\u2019s first superhero \u2014 a vigilante of the airwaves who fought crime with hypnotic powers and a chilling laugh that defined an era."),
            ("YOURS TRULY, JOHNNY DOLLAR (CBS, 1949\u20131962)",
             "The last great radio drama. Johnny Dollar was an insurance investigator with an expense account and a talent for stumbling into murder. The show\u2019s legendary five-part serial format turned each case into a week-long addiction, with Bob Bailey\u2019s definitive portrayal making Dollar the most human detective on the dial."),
            ("DRAGNET (NBC, 1949\u20131957)",
             "Just the facts. Jack Webb\u2019s revolutionary procedural stripped crime drama down to documentary realism. Based on actual LAPD cases, Dragnet\u2019s clipped dialogue and methodical pacing invented a genre that still dominates television seventy years later. The radio version remains the purest expression of Webb\u2019s obsessive vision."),
            ("THE WHISTLER (CBS, 1942\u20131955)",
             "\u2018I am the Whistler, and I know many things...\u2019 This West Coast noir gem specialized in ironic twist endings worthy of O. Henry. Each episode followed an ordinary person making one fatal mistake, narrated by the mysterious Whistler whose eerie theme still haunts anyone who\u2019s heard it."),
            ("SAM SPADE (NBC/CBS, 1946\u20131951)",
             "Howard Duff brought Dashiell Hammett\u2019s iconic detective to crackling life in this witty, hard-boiled series. Spade\u2019s sardonic narration and the show\u2019s clever blend of genuine mystery with sharp humor made it the gold standard for detective radio. Every PI show since owes Sam Spade a drink."),
            ("INNER SANCTUM (NBC/CBS, 1941\u20131952)",
             "That creaking door. The host\u2019s terrible puns. Then thirty minutes of genuine horror that pushed the boundaries of what broadcasting would allow. Inner Sanctum Mysteries understood that what you imagine is always worse than what you see \u2014 and its writers were masters of making you imagine terrible things."),
            ("GUNSMOKE (CBS, 1952\u20131961)",
             "The adult Western that changed everything. William Conrad\u2019s Marshal Matt Dillon inhabited a Dodge City where violence had consequences, morality was ambiguous, and the frontier was as psychologically complex as any noir cityscape. The radio Gunsmoke is darker, deeper, and arguably better than the TV show it spawned."),
            ("ESCAPE (CBS, 1947\u20131954)",
             "\u2018Tired of the everyday grind? Ever dream of a life of romantic adventure?\u2019 Escape delivered exactly what it promised \u2014 high-octane tales of survival, exploration, and danger drawn from the finest adventure literature. From Jack London to Roald Dahl, this anthology series was a weekly passport to somewhere extraordinary."),
            ("SHERLOCK HOLMES (NBC/Various, 1939\u20131950)",
             "Basil Rathbone and Nigel Bruce brought Holmes and Watson from the silver screen to the airwaves, and the result was magic. The foggy streets of Victorian London were made for radio, and these adaptations of Conan Doyle\u2019s mysteries remain among the most atmospheric detective shows ever produced."),
        ]

        # Page 3: shows 1-5
        self.new_page()
        self.draw_heading("THE 10 SHOWS YOU MUST HEAR FIRST", 17)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 6

        for i, (title, desc) in enumerate(shows[:5]):
            num_title = f"{i+1}. {title}"
            self.draw_card(num_title, desc, title_size=10)

        # Page 4: shows 6-10
        self._draw_footer()
        self.new_page()
        self.draw_heading("THE 10 SHOWS YOU MUST HEAR FIRST (CONTINUED)", 14)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 6

        for i, (title, desc) in enumerate(shows[5:], start=6):
            num_title = f"{i}. {title}"
            self.draw_card(num_title, desc, title_size=10)

    def page_timeline(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("THE GOLDEN AGE TIMELINE", 18)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 8

        entries = [
            ("1920s: THE BIRTH",
             "Commercial radio explodes across America. By 1930, over 12 million households own a radio set. The medium is new, raw, and searching for its voice."),
            ("1930s: THE GOLDEN AGE BEGINS",
             "Networks form. Sponsors pour in. Shows like The Shadow, The Lone Ranger, and Orson Welles\u2019 Mercury Theatre emerge. On October 30, 1938, Welles\u2019 War of the Worlds broadcast triggers nationwide panic \u2014 and proves radio\u2019s staggering power over the American imagination."),
            ("1940s: THE PEAK",
             "World War II makes radio essential. Families huddle around sets for war news, then stay for Suspense, Inner Sanctum, and The Whistler. This is radio drama\u2019s finest decade \u2014 the writing is sharp, the actors are Hollywood-caliber, and the audiences number in the tens of millions."),
            ("1950s: THE LAST STAND",
             "Television arrives and the exodus begins. But radio drama doesn\u2019t go quietly. Shows like Gunsmoke, Yours Truly Johnny Dollar, and X Minus One push the art form to new creative heights even as audiences shrink. Johnny Dollar\u2019s final broadcast on September 30, 1962, marks the end of an era."),
            ("1960s\u20132000s: THE WILDERNESS",
             "Old time radio survives in syndication, collector circles, and late-night AM broadcasts. A devoted community keeps the recordings alive, trading tapes and cataloging thousands of surviving episodes."),
            ("2000s\u2013PRESENT: THE REVIVAL",
             "The internet changes everything. Thousands of episodes become freely available. Podcasting creates a new generation of audio drama fans. Old time radio finds its largest audience in decades \u2014 proof that great storytelling never expires."),
        ]
        for era, desc in entries:
            self.c.setFillColor(GOLD)
            self.c.setFont("Helvetica-Bold", 11)
            self.c.drawString(LEFT, self.y, era.upper())
            self.y -= 16
            self.draw_body(desc, size=10.5, leading=15, indent=0)
            self.y -= 4

    def page_genre_guide(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("GENRE GUIDE", 18)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 6

        genres = [
            ("NOIR & DETECTIVE",
             "The beating heart of OTR. Start with Sam Spade for wit, Philip Marlowe for atmosphere, Johnny Dollar for serial storytelling, and Richard Diamond for charm. Broadway Is My Beat delivers the most poetic crime narration ever broadcast."),
            ("HORROR & THRILLER",
             "Suspense is the undisputed king, but Inner Sanctum brings gleeful camp horror, The Whistler offers ironic noir twists, and Lights Out pioneered visceral sound-effects horror that still disturbs. Quiet, Please is the literary dark horse \u2014 genuinely unsettling."),
            ("WESTERN",
             "Gunsmoke towers above all, with writing that rivals any prestige drama. The Lone Ranger is pure adventure serial joy. Have Gun Will Travel brings sophisticated moral complexity to the frontier."),
            ("SCIENCE FICTION",
             "X Minus One adapted the finest sci-fi literature of the 1950s \u2014 Bradbury, Asimov, Heinlein \u2014 with stunning production values. Dimension X was its predecessor and nearly as good. For cosmic horror, try Quiet, Please."),
            ("COMEDY",
             "Jack Benny perfected the sitcom decades before television. The Great Gildersleeve invented the spin-off. Burns and Allen were surrealist geniuses. Fred Allen\u2019s intellectual wit made him the thinking person\u2019s comedian."),
            ("ADVENTURE",
             "Escape is the gateway \u2014 pure pulp adventure adapted from great literature. Bold Venture pairs Bogart and Bacall in Caribbean intrigue. The Green Hornet delivers vigilante justice with a jazz soundtrack."),
        ]
        for title, desc in genres:
            self.draw_card(title, desc, title_size=11)

    def page_how_to_listen(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("HOW TO LISTEN", 18)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 8

        sections = [
            ("STREAM FREE AT GHOSTOFRADIO.COM",
             "Our growing library features thousands of episodes with curated descriptions, and a custom vintage radio player. No account needed. Just pick a show, press play, and let the static wash over you."),
            ("BEST STARTING EPISODES BY GENRE",
             "Detective: Sam Spade, \u2018The Calcutta Trunk Caper\u2019 | Horror: Suspense, \u2018Sorry, Wrong Number\u2019 | Western: Gunsmoke, \u2018Billy the Kid\u2019 | Sci-Fi: X Minus One, \u2018A Logic Named Joe\u2019 | Comedy: Jack Benny, any episode"),
            ("TIPS FOR IMMERSIVE LISTENING",
             "Use headphones. Turn the lights off. Give it your full attention \u2014 no multitasking. The first five minutes might feel strange if you\u2019re not used to the pacing. Push through. By the halfway mark, you\u2019ll be hooked. These shows were designed for focused listening in a dark room. Honor that."),
            ("THE GHOST OF RADIO YOUTUBE CHANNEL",
             "Full episodes with vintage artwork and enhanced audio. Subscribe for new uploads and curated playlists organized by show, genre, and mood."),
        ]
        for title, desc in sections:
            self.c.setFillColor(GOLD)
            self.c.setFont("Helvetica-Bold", 12)
            self.c.drawString(LEFT, self.y, title)
            self.y -= 18
            self.draw_body(desc, size=10.5, leading=15)
            self.y -= 8

    def page_5_episodes(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("5 EPISODES THAT WILL HOOK YOU FOREVER", 16)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 6

        episodes = [
            ("SAM SPADE: \u2018The Calcutta Trunk Caper\u2019",
             "A locked trunk arrives from India. Inside: a body. Sam Spade unravels a mystery that spans continents, with Howard Duff\u2019s narration at its sardonic best. The plot twists are genuinely surprising, and the final revelation is a masterclass in radio storytelling economy."),
            ("SUSPENSE: \u2018Sorry, Wrong Number\u2019",
             "A bedridden woman overhears a murder plot on a crossed telephone line \u2014 her own murder. Agnes Moorehead delivers a tour-de-force solo performance that\u2019s as harrowing today as it was in 1943. This single episode defined what radio drama could achieve and was performed seven times by popular demand."),
            ("THE SHADOW: \u2018Death House Rescue\u2019",
             "Lamont Cranston must save an innocent man from the electric chair with only hours to spare. The Shadow uses every trick in his arsenal \u2014 invisibility, deduction, sheer nerve \u2014 in a race against the clock that showcases everything great about the series: atmosphere, tension, and Cranston\u2019s ruthless sense of justice."),
            ("INNER SANCTUM: \u2018The Man from Yesterday\u2019",
             "A soldier returns from the dead \u2014 or does he? This psychological thriller blurs the line between supernatural horror and human cruelty, with a twist ending that rewards a second listen. Inner Sanctum at its most genuinely disturbing, beneath the host\u2019s cheerful puns."),
            ("GUNSMOKE: \u2018Billy the Kid\u2019",
             "A young gunfighter rides into Dodge City looking for Marshal Dillon. The writing is Hemingway-spare, the confrontation is inevitable, and the ending hits like a gut punch. This episode demonstrates why the radio Gunsmoke was a genuine work of American literature."),
        ]
        for title, desc in episodes:
            self.draw_card(title, desc, title_size=10)

    def page_behind_mic(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("BEHIND THE MICROPHONE", 18)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 6

        facts = [
            ("THE PANIC BROADCAST",
             "On Halloween Eve 1938, Orson Welles and the Mercury Theatre performed a radio adaptation of H.G. Wells\u2019 War of the Worlds as a series of fake news bulletins. Listeners who tuned in late believed Martians had actually invaded New Jersey. Police switchboards lit up across the country. Newspapers ran outraged headlines for weeks. It remains the most famous single broadcast in radio history \u2014 and launched Welles straight to Hollywood and Citizen Kane."),
            ("THE ART OF SOUND",
             "Radio sound effects were handmade art. Coconut shells on gravel for horse hooves. Cellophane crackling for fire. A leather glove slapped on a table for a punch. Berry Kroeger could make listeners see a rainstorm with nothing but a sheet of metal and a watering can. The sound effects artists were radio\u2019s unsung geniuses."),
            ("HOLLYWOOD AT THE MICROPHONE",
             "Radio paid well and rehearsals were short, which meant the biggest movie stars moonlighted behind the microphone. Humphrey Bogart, Lauren Bacall, James Stewart, Orson Welles, Agnes Moorehead, Vincent Price \u2014 they all did extensive radio work, often delivering performances more raw and intimate than anything they did on film."),
            ("LIVE AND DANGEROUS",
             "Most Golden Age shows were performed live, mistakes and all. Actors sometimes flubbed lines, sound effects misfired, and pages got dropped. The best performers turned disasters into moments of genuine spontaneity. There are surviving recordings where you can hear actors stifle laughter, improvise around errors, and somehow make it all work."),
            ("CREATIVITY FROM CONSTRAINT",
             "No visuals meant no budget for sets, costumes, or locations. A story could leap from a Manhattan penthouse to a submarine to the surface of Mars in seconds \u2014 all it cost was a few words and a sound effect. These constraints didn\u2019t limit creativity. They supercharged it."),
        ]
        for title, desc in facts:
            self.c.setFillColor(GOLD)
            self.c.setFont("Helvetica-Bold", 10.5)
            self.c.drawString(LEFT, self.y, title)
            self.y -= 15
            self.draw_body(desc, size=10, leading=14, indent=0)
            self.y -= 4

    def page_next_steps(self):
        self._draw_footer()
        self.new_page()
        self.draw_heading("YOUR NEXT STEPS", 18)
        self.y -= 2
        self.gold_rule(thickness=0.5)
        self.y -= 10

        sections = [
            ("START LISTENING NOW",
             "Visit ghostofradio.com and pick any show that caught your eye in this guide. Every episode is free to stream. No account required. Just press play."),
            ("SUBSCRIBE ON YOUTUBE",
             "The Ghost of Radio YouTube channel features full episodes with vintage artwork and enhanced audio. New episodes uploaded regularly. Subscribe and never miss a broadcast from the past."),
            ("JOIN THE COMMUNITY",
             "Sign up for our newsletter at ghostofradio.com for weekly episode recommendations, behind-the-scenes history, and updates on new shows added to the archive."),
            ("SPREAD THE SIGNAL",
             "Know someone who\u2019d love old time radio? Share this guide. The Golden Age deserves new listeners, and every shared episode keeps these broadcasts alive for another generation."),
        ]
        for title, desc in sections:
            self.c.setFillColor(GOLD)
            self.c.setFont("Helvetica-Bold", 13)
            self.c.drawString(LEFT, self.y, title)
            self.y -= 20
            self.draw_body(desc, size=11, leading=16)
            self.y -= 16

        # Final tagline
        self.y -= 20
        self.gold_rule(width=2.5 * inch, thickness=0.75)
        self.y -= 16
        self.c.setFillColor(GOLD)
        self.c.setFont("Times-Roman", 12)
        self.c.drawCentredString(
            PAGE_W / 2, self.y,
            "The Golden Age ended. The ghosts are still broadcasting. \u2014 Ghost of Radio"
        )

    def generate(self):
        self.page_cover()
        self.page_introduction()
        self.page_top10_shows()
        self.page_timeline()
        self.page_genre_guide()
        self.page_how_to_listen()
        self.page_5_episodes()
        self.page_behind_mic()
        self.page_next_steps()
        self._draw_footer()
        self.save()
        print(f"PDF generated: {OUTPUT_PATH}")
        print(f"Total pages: {self.page_num}")


if __name__ == "__main__":
    guide = PDFGuide()
    guide.generate()
