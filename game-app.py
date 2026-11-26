import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VocabSnap — English Vocabulary Guess Game",
    page_icon="🖼️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .word-card {
        background-color: #f8f9fa;
        border-left: 5px solid #4CAF50;
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        color: #1f2937;
    }
    .hint-box {
        background-color: #fffbeb;
        border: 1px solid #fcd34d;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        color: #78350f;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Vocabulary Dataset
# -----------------------------------------------------------------------------
VOCAB_DATA = [
    {
        "word": "apple",
        "difficulty": "Easy",
        "category": "Nature",
        "pos": "noun",
        "definition": "A round fruit with crisp flesh and red, yellow, or green skin.",
        "example": "She packed a crisp red apple in her lunchbox.",
    },
    {
        "word": "umbrella",
        "difficulty": "Easy",
        "category": "Objects",
        "pos": "noun",
        "definition": "A folding canopy supported by ribs, used for protection against rain or sun.",
        "example": "Don't forget your umbrella; dark clouds are gathering.",
    },
    {
        "word": "cactus",
        "difficulty": "Easy",
        "category": "Nature",
        "pos": "noun",
        "definition": "A desert plant with thick, fleshy stems and sharp spines instead of leaves.",
        "example": "The green cactus thrived on the sunny windowsill with very little water.",
    },
    {
        "word": "bridge",
        "difficulty": "Easy",
        "category": "Objects",
        "pos": "noun",
        "definition": "A structure built to span a physical obstacle such as a river, valley, or road.",
        "example": "We walked across the wooden bridge to reach the other side of the stream.",
    },
    {
        "word": "volcano",
        "difficulty": "Medium",
        "category": "Nature",
        "pos": "noun",
        "definition": "A mountain or hill with a crater through which lava, rock, and gas erupt.",
        "example": "Thick plumes of ash rose from the active volcano.",
    },
    {
        "word": "compass",
        "difficulty": "Medium",
        "category": "Objects",
        "pos": "noun",
        "definition": "An instrument containing a magnetized pointer that shows the direction of magnetic north.",
        "example": "Hikers rely on a map and compass when navigating dense forests.",
    },
    {
        "word": "violin",
        "difficulty": "Medium",
        "category": "Objects",
        "pos": "noun",
        "definition": "A wooden string instrument with four strings played with a horsehair bow.",
        "example": "The solo violin melody echoed beautifully through the concert hall.",
    },
    {
        "word": "lighthouse",
        "difficulty": "Medium",
        "category": "Objects",
        "pos": "noun",
        "definition": "A tall tower with a bright light at the top to warn or guide ships at sea.",
        "example": "The coastal lighthouse flashed its beam every ten seconds through the fog.",
    },
    {
        "word": "telescope",
        "difficulty": "Hard",
        "category": "Objects",
        "pos": "noun",
        "definition": "An optical instrument designed to make distant celestial objects appear nearer.",
        "example": "Through the backyard telescope, Saturn's rings were clearly visible.",
    },
    {
        "word": "hourglass",
        "difficulty": "Hard",
        "category": "Objects",
        "pos": "noun",
        "definition": "A device with two connected glass bulbs containing sand that takes an hour to fall.",
        "example": "She flipped the hourglass over to time the board game round.",
    },
    {
        "word": "eclipse",
        "difficulty": "Hard",
        "category": "Nature",
        "pos": "noun",
        "definition": "An astronomical event where one celestial body moves into the shadow of another.",
        "example": "Thousands gathered to watch the total solar eclipse darken the afternoon sky.",
    },
    {
        "word": "anchor",
        "difficulty": "Hard",
        "category": "Objects",
        "pos": "noun",
        "definition": "A heavy metal device dropped to the seabed to prevent a vessel from drifting.",
        "example": "The captain ordered the crew to drop anchor in the sheltered bay.",
    },
]


# -----------------------------------------------------------------------------
# Image Generation (Local File Support + Custom PIL Procedural Art Fallback)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_word_image(word: str) -> bytes:
    """Loads a local image from images/<word>.* if available, otherwise draws a clean PIL illustration."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        local_path = os.path.join("images", f"{word.lower()}.{ext}")
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()

    # Generate high-resolution 600x400 PIL illustration
    w, h = 600, 400
    img = Image.new("RGB", (w, h), "#eef6ff")
    draw = ImageDraw.Draw(img)

    # Subtle decorative border
    draw.rectangle([12, 12, w - 12, h - 12], outline="#cbd5e1", width=4)

    cx, cy = w // 2, h // 2
    word_key = word.lower()

    if word_key == "apple":
        # Sky/table background
        draw.rectangle([16, 290, w - 16, h - 16], fill="#fde68a")
        # Stem & Leaf
        draw.line([(cx, cy - 75), (cx + 12, cy - 115)], fill="#78350f", width=10)
        draw.ellipse([cx + 8, cy - 115, cx + 65, cy - 80], fill="#22c55e", outline="#15803d", width=3)
        # Apple body (two overlapping circles)
        draw.ellipse([cx - 95, cy - 75, cx + 25, cy + 85], fill="#ef4444")
        draw.ellipse([cx - 25, cy - 75, cx + 95, cy + 85], fill="#dc2626")
        # Highlight
        draw.arc([cx - 72, cy - 50, cx - 20, cy + 20], start=130, end=240, fill="#fca5a5", width=8)

    elif word_key == "umbrella":
        # Raindrops
        for rx, ry in [(130, 90), (470, 100), (160, 260), (440, 250), (110, 180), (490, 180)]:
            draw.line([(rx, ry), (rx - 8, ry + 22)], fill="#3b82f6", width=4)
        # Handle
        draw.line([(cx, cy - 95), (cx, cy + 95)], fill="#78350f", width=8)
        draw.arc([cx - 40, cy + 65, cx, cy + 115], start=0, end=180, fill="#78350f", width=8)
        # Canopy
        draw.pieslice([cx - 140, cy - 100, cx + 140, cy + 120], start=180, end=360, fill="#8b5cf6", outline="#5b21b6", width=4)
        draw.pieslice([cx - 60, cy - 100, cx + 60, cy + 120], start=180, end=360, fill="#a78bfa")

    elif word_key == "cactus":
        # Desert ground & sun
        draw.ellipse([440, 45, 520, 125], fill="#facc15")
        draw.rectangle([16, 300, w - 16, h - 16], fill="#f59e0b")
        # Main stem
        draw.rounded_rectangle([cx - 30, cy - 110, cx + 30, cy + 110], radius=30, fill="#16a34a", outline="#14532d", width=4)
        # Left arm
        draw.rounded_rectangle([cx - 95, cy - 45, cx - 30, cy + 15], radius=18, fill="#16a34a", outline="#14532d", width=4)
        draw.rounded_rectangle([cx - 95, cy - 85, cx - 60, cy + 15], radius=18, fill="#16a34a", outline="#14532d", width=4)
        # Right arm
        draw.rounded_rectangle([cx + 30, cy - 20, cx + 95, cy + 35], radius=18, fill="#16a34a", outline="#14532d", width=4)
        draw.rounded_rectangle([cx + 60, cy - 65, cx + 95, cy + 35], radius=18, fill="#16a34a", outline="#14532d", width=4)
        # Spines
        for sy in range(cy - 80, cy + 80, 35):
            draw.line([(cx - 42, sy), (cx - 28, sy)], fill="#fef08a", width=3)
            draw.line([(cx + 28, sy), (cx + 42, sy)], fill="#fef08a", width=3)

    elif word_key == "bridge":
        # Water
        draw.rectangle([16, 260, w - 16, h - 16], fill="#38bdf8")
        # Towers
        draw.rectangle([165, 95, 190, 290], fill="#dc2626")
        draw.rectangle([410, 95, 435, 290], fill="#dc2626")
        # Suspension cables
        draw.arc([178, 50, 422, 220], start=0, end=180, fill="#b91c1c", width=5)
        draw.arc([40, 50, 178, 220], start=0, end=90, fill="#b91c1c", width=5)
        draw.arc([422, 50, 560, 220], start=90, end=180, fill="#b91c1c", width=5)
        # Vertical suspender ropes
        for vx in range(205, 405, 28):
            draw.line([(vx, 165), (vx, 220)], fill="#991b1b", width=2)
        # Road deck
        draw.rectangle([40, 215, 560, 232], fill="#334155")

    elif word_key == "volcano":
        # Ash cloud
        for ox, oy, r in [(cx - 35, 75, 32), (cx + 15, 65, 38), (cx + 55, 80, 28), (cx - 5, 95, 30)]:
            draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill="#94a3b8")
        # Mountain cone
        draw.polygon([(120, 340), (260, 135), (340, 135), (480, 340)], fill="#57534e", outline="#292524")
        # Lava crater & flows
        draw.polygon([(260, 135), (340, 135), (325, 195), (300, 170), (275, 215)], fill="#f97316")
        draw.ellipse([260, 125, 340, 145], fill="#ef4444")

    elif word_key == "compass":
        # Outer metallic case
        draw.ellipse([cx - 125, cy - 125, cx + 125, cy + 125], fill="#d97706", outline="#78350f", width=8)
        draw.ellipse([cx - 102, cy - 102, cx + 102, cy + 102], fill="#ffffff", outline="#94a3b8", width=4)
        # Cardinal ticks
        draw.line([(cx, cy - 95), (cx, cy - 75)], fill="#1e293b", width=5)
        draw.line([(cx, cy + 75), (cx, cy + 95)], fill="#1e293b", width=5)
        draw.line([(cx - 95, cy), (cx - 75, cy)], fill="#1e293b", width=5)
        draw.line([(cx + 75, cy), (cx + 95, cy)], fill="#1e293b", width=5)
        # Angled needle (North = Red, South = Blue)
        draw.polygon([(cx - 16, cy - 16), (cx + 16, cy + 16), (cx + 68, cy - 68)], fill="#ef4444")
        draw.polygon([(cx - 16, cy - 16), (cx + 16, cy + 16), (cx - 68, cy + 68)], fill="#3b82f6")
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill="#facc15", outline="#78350f", width=3)

    elif word_key == "violin":
        # Neck & Scroll
        draw.rectangle([cx - 10, 45, cx + 10, 175], fill="#78350f")
        draw.ellipse([cx - 16, 35, cx + 16, 60], fill="#92400e")
        # Body (upper and lower bouts)
        draw.ellipse([cx - 55, 145, cx + 55, 245], fill="#d97706", outline="#78350f", width=4)
        draw.ellipse([cx - 72, 215, cx + 72, 345], fill="#d97706", outline="#78350f", width=4)
        # Bridge & Strings
        draw.rectangle([cx - 22, 255, cx + 22, 263], fill="#fef3c7")
        for sx in [-6, -2, 2, 6]:
            draw.line([(cx + sx, 60), (cx + sx, 315)], fill="#f8fafc", width=2)
        # Bow
        draw.line([(cx + 95, 65), (cx + 95, 335)], fill="#78350f", width=5)
        draw.line([(cx + 88, 70), (cx + 88, 330)], fill="#e2e8f0", width=2)

    elif word_key == "lighthouse":
        # Night sky & sea
        draw.rectangle([16, 16, w - 16, 310], fill="#1e293b")
        draw.rectangle([16, 310, w - 16, h - 16], fill="#0284c7")
        # Light beams
        draw.polygon([(cx, 105), (40, 55), (40, 160)], fill="#fef08a")
        draw.polygon([(cx, 105), (560, 55), (560, 160)], fill="#fef08a")
        # Striped tower
        draw.polygon([(cx - 45, 310), (cx - 28, 130), (cx + 28, 130), (cx + 45, 310)], fill="#ffffff")
        draw.polygon([(cx - 40, 265), (cx - 36, 220), (cx + 36, 220), (cx + 40, 265)], fill="#ef4444")
        draw.polygon([(cx - 32, 175), (cx - 29, 135), (cx + 29, 135), (cx + 32, 175)], fill="#ef4444")
        # Lantern room & dome
        draw.rectangle([cx - 24, 92, cx + 24, 130], fill="#facc15", outline="#ef4444", width=3)
        draw.pieslice([cx - 28, 65, cx + 28, 115], start=180, end=360, fill="#ef4444")

    elif word_key == "telescope":
        # Night sky & stars
        draw.rectangle([16, 16, w - 16, h - 16], fill="#0f172a")
        for sx, sy in [(90, 70), (150, 130), (480, 65), (510, 140), (390, 55), (120, 220)]:
            draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill="#fef08a")
        # Tripod legs
        draw.line([(cx, cy + 15), (cx - 95, 355)], fill="#94a3b8", width=8)
        draw.line([(cx, cy + 15), (cx + 95, 355)], fill="#94a3b8", width=8)
        draw.line([(cx, cy + 15), (cx, 360)], fill="#64748b", width=8)
        # Optical tube
        draw.polygon([(cx - 110, cy + 55), (cx + 105, cy - 65), (cx + 125, cy - 25), (cx - 95, cy + 80)], fill="#38bdf8", outline="#ffffff")
        draw.ellipse([cx + 100, cy - 68, cx + 132, cy - 22], fill="#e0f2fe", outline="#0284c7", width=4)

    elif word_key == "hourglass":
        # Top & bottom wooden frames
        draw.rounded_rectangle([cx - 95, 55, cx + 95, 78], radius=8, fill="#92400e")
        draw.rounded_rectangle([cx - 95, 322, cx + 95, 345], radius=8, fill="#92400e")
        # Glass bulbs
        draw.polygon([(cx - 75, 78), (cx + 75, 78), (cx + 10, cy), (cx - 10, cy)], fill="#e0f2fe", outline="#0284c7")
        draw.polygon([(cx - 10, cy), (cx + 10, cy), (cx + 75, 322), (cx - 75, 322)], fill="#e0f2fe", outline="#0284c7")
        # Sand (top, falling stream, bottom)
        draw.polygon([(cx - 42, 135), (cx + 42, 135), (cx + 8, cy), (cx - 8, cy)], fill="#f59e0b")
        draw.line([(cx, cy), (cx, 320)], fill="#f59e0b", width=4)
        draw.polygon([(cx, 260), (cx + 68, 320), (cx - 68, 320)], fill="#f59e0b")

    elif word_key == "eclipse":
        # Deep space
        draw.rectangle([16, 16, w - 16, h - 16], fill="#090d16")
        # Corona glow
        for r, col in [(135, "#312e81"), (118, "#f59e0b"), (106, "#fef08a")]:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        # Moon disc blocking the sun
        draw.ellipse([cx - 98, cy - 98, cx + 98, cy + 98], fill="#090d16")
        # Diamond ring sparkle
        draw.ellipse([cx + 76, cy - 76, cx + 102, cy - 50], fill="#ffffff")

    elif word_key == "anchor":
        # Ocean backdrop
        draw.rectangle([16, 16, w - 16, h - 16], fill="#dbeafe")
        col = "#1e3a8a"
        # Top ring
        draw.ellipse([cx - 24, 55, cx + 24, 103], outline=col, width=10)
        # Vertical shank & crossbar
        draw.line([(cx, 103), (cx, 315)], fill=col, width=14)
        draw.line([(cx - 65, 145), (cx + 65, 145)], fill=col, width=12)
        # Curved arms & flukes
        draw.arc([cx - 105, 165, cx + 105, 320], start=15, end=165, fill=col, width=14)
        draw.polygon([(cx - 115, 245), (cx - 85, 225), (cx - 92, 268)], fill=col)
        draw.polygon([(cx + 115, 245), (cx + 85, 225), (cx + 92, 268)], fill=col)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# -----------------------------------------------------------------------------
# Session State Management
# -----------------------------------------------------------------------------
def filter_words(difficulty: str, category: str) -> list[dict]:
    words = [
        item
        for item in VOCAB_DATA
        if (difficulty == "All" or item["difficulty"] == difficulty)
        and (category == "All" or item["category"] == category)
    ]
    return words if words else VOCAB_DATA.copy()


def init_game(difficulty: str = "All", category: str = "All"):
    deck = filter_words(difficulty, category)
    random.shuffle(deck)
    st.session_state.deck = deck
    st.session_state.round_idx = 0
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.best_streak = 0
    st.session_state.hints_used = 0
    st.session_state.round_over = False
    st.session_state.round_status = None  # "correct" | "skipped" | None
    st.session_state.feedback_msg = ""
    st.session_state.guess_input = ""
    st.session_state.selected_difficulty = difficulty
    st.session_state.selected_category = category


if "deck" not in st.session_state:
    init_game()


# -----------------------------------------------------------------------------
# Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Game Settings")

    difficulty = st.selectbox(
        "Difficulty Level",
        options=["All", "Easy", "Medium", "Hard"],
        index=["All", "Easy", "Medium", "Hard"].index(st.session_state.selected_difficulty),
    )

    category = st.selectbox(
        "Category",
        options=["All", "Nature", "Objects"],
        index=["All", "Nature", "Objects"].index(st.session_state.selected_category),
    )

    if (
        difficulty != st.session_state.selected_difficulty
        or category != st.session_state.selected_category
    ):
        init_game(difficulty, category)
        st.rerun()

    if st.button("🔄 Restart Game", use_container_width=True):
        init_game(difficulty, category)
        st.rerun()

    st.divider()
    st.subheader("📏 Scoring Rules")
    st.markdown(
        """
        - **Base Points:** `100 pts`
        - **No-Hint Bonus:** `+25 pts`
        - **Streak Bonus:** `+10 pts × streak`
        - **Hint Penalty:** `-25 pts` per hint (up to 3 hints)
        """
    )


# -----------------------------------------------------------------------------
# Main Gameplay UI
# -----------------------------------------------------------------------------
st.title("🖼️ English Vocabulary Guess Game")
st.caption("Look at the illustration, use hints if needed, and guess the English word!")

total_words = len(st.session_state.deck)
round_idx = st.session_state.round_idx

# Top Scoreboard
col1, col2, col3, col4 = st.columns(4)
col1.metric("Round", f"{min(round_idx + 1, total_words)} / {total_words}")
col2.metric("Score", f"{st.session_state.score} pts")
col3.metric("Streak 🔥", st.session_state.streak)
col4.metric("Best Streak 🏆", st.session_state.best_streak)

st.progress(min(round_idx / total_words, 1.0))

# Game Completed View
if round_idx >= total_words:
    st.balloons()
    st.success("🎉 **Congratulations! You completed all words in this deck!**")
    st.markdown(
        f"""
        - **Final Score:** `{st.session_state.score}` points
        - **Best Streak:** `{st.session_state.best_streak}` in a row
        - **Words Played:** `{total_words}`
        """
    )
    if st.button("Play Again", type="primary", use_container_width=True):
        init_game(difficulty, category)
        st.rerun()
    st.stop()

# Active Round Data
current_item = st.session_state.deck[round_idx]
target_word = current_item["word"]

# Display Illustration
img_bytes = get_word_image(target_word)
st.image(img_bytes, use_container_width=True)

# Badge Metadata
st.markdown(
    f"**Category:** `{current_item['category']}` &nbsp;|&nbsp; **Difficulty:** `{current_item['difficulty']}`"
)

# Hints Section
hints_list = [
    f"**Hint 1 (Length & First Letter):** `{len(target_word)}` letters, starts with **`{target_word[0].upper()}`**",
    f"**Hint 2 (Part of Speech):** *`{current_item['pos']}`*",
    f"**Hint 3 (Definition):** {current_item['definition']}",
]

if not st.session_state.round_over:
    hint_col1, hint_col2 = st.columns([1, 2])
    with hint_col1:
        if st.button(
            f"💡 Get Hint ({st.session_state.hints_used}/3)",
            disabled=st.session_state.hints_used >= 3,
            use_container_width=True,
        ):
            st.session_state.hints_used += 1
            st.rerun()
    with hint_col2:
        if st.session_state.hints_used == 0:
            st.caption("✨ Solve with 0 hints for a **+25 pt** bonus!")
        else:
            st.caption(f"Hints used: {st.session_state.hints_used} (-{st.session_state.hints_used * 25} pts)")

for i in range(st.session_state.hints_used):
    st.markdown(f"<div class='hint-box'>{hints_list[i]}</div>", unsafe_allow_html=True)

# Guess Submission Form (Active Round)
if not st.session_state.round_over:
    with st.form(key=f"guess_form_{round_idx}", clear_on_submit=False):
        user_guess = st.text_input(
            "Your Guess:",
            placeholder="Type the English vocabulary word here...",
            key=f"input_{round_idx}",
        )
        btn_col1, btn_col2 = st.columns(2)
        submitted = btn_col1.form_submit_button("✅ Submit Guess", type="primary", use_container_width=True)
        skipped = btn_col2.form_submit_button("⏭️ Skip / Reveal Word", use_container_width=True)

    if submitted:
        cleaned_guess = user_guess.strip().lower()
        if not cleaned_guess:
            st.warning("Please enter a word before submitting!")
        elif cleaned_guess == target_word.lower():
            # Calculate points
            base_pts = 100
            hint_penalty = st.session_state.hints_used * 25
            no_hint_bonus = 25 if st.session_state.hints_used == 0 else 0
            streak_bonus = st.session_state.streak * 10
            earned = max(25, base_pts - hint_penalty + no_hint_bonus + streak_bonus)

            st.session_state.score += earned
            st.session_state.streak += 1
            st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
            st.session_state.round_over = True
            st.session_state.round_status = "correct"
            st.session_state.feedback_msg = (
                f"🎉 Correct! You earned **+{earned} pts** "
                f"(Base: {base_pts}, Hints: -{hint_penalty}, No-Hint Bonus: +{no_hint_bonus}, Streak: +{streak_bonus})."
            )
            st.rerun()
        else:
            st.session_state.streak = 0
            st.error(f"❌ **'{user_guess.strip()}'** isn't quite right. Try again or use a hint!")

    if skipped:
        st.session_state.streak = 0
        st.session_state.round_over = True
        st.session_state.round_status = "skipped"
        st.session_state.feedback_msg = f"⏭️ Word skipped! The answer was **{target_word.capitalize()}**."
        st.rerun()

# Post-Round Reveal & Next Word Button
if st.session_state.round_over:
    if st.session_state.round_status == "correct":
        st.success(st.session_state.feedback_msg)
    else:
        st.info(st.session_state.feedback_msg)

    st.markdown(
        f"""
        <div class="word-card">
            <h3 style="margin-top:0;">📖 {target_word.capitalize()} <small style="font-weight:normal; color:#4b5563;">({current_item['pos']})</small></h3>
            <p><strong>Meaning:</strong> {current_item['definition']}</p>
            <p style="margin-bottom:0;"><strong>Example:</strong> <em>"{current_item['example']}"</em></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    next_label = "➡️ Next Word" if round_idx + 1 < total_words else "🏁 See Final Results"
    if st.button(next_label, type="primary", use_container_width=True):
        st.session_state.round_idx += 1
        st.session_state.hints_used = 0
        st.session_state.round_over = False
        st.session_state.round_status = None
        st.session_state.feedback_msg = ""
        st.rerun()
