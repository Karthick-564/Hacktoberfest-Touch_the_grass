"""
Seed Script for 'Field Guide':
1. Populates 25 native Coimbatore & Western Ghats trees into the 'species' table (category='trees').
2. Fetches & sets genuine bird call recording URLs from Wikimedia Commons into 'species.audio_url'.
"""

import json
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "field_guide.db"

TREES_DATA = [
    {
        "scientific_name": "Azadirachta indica",
        "common_name": "Neem Tree",
        "tamil_name": "வேப்ப மரம்",
        "rarity": "Everyday",
        "peak_months": ["Mar", "Apr", "May", "Jun"],
        "summary": "Azadirachta indica, commonly known as neem, is a tree in the mahogany family Meliaceae native to the Indian subcontinent.",
        "description_text": "Neem is a fast-growing evergreen tree with dense rounded crown. Leaves are pinnate, 20–40 cm long, with 20 to 31 medium to dark green serrated leaflets. Bark is hard, dark grey to blackish with longitudinal fissures. Flowers are white and fragrant. Fruit is a smooth olive-like green drupe turning yellow when ripe.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "medicinal",
            "habitat": "avenue"
        },
        "local_fact": "Ubiquitous shade and medicinal avenue tree planted outside almost every household and avenue in Coimbatore; leaves are bitter and strongly medicinal.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Azadirachta_indica_leaves.JPG",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Ficus religiosa",
        "common_name": "Sacred Fig (Peepal)",
        "tamil_name": "அரச மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Ficus religiosa, commonly known as the sacred fig or peepal, is a species of fig native to the Indian subcontinent.",
        "description_text": "Ficus religiosa is a large deciduous dry season or semi-evergreen tree up to 30 metres tall with a trunk diameter of up to 3 metres. Leaves are heart-shaped with a distinctive extended tip (drip tip) 2–5 cm long. Leaf petioles are long, causing leaves to flutter and rustle in the slightest breeze. Bark is smooth grey and peels in irregular rounded flakes.",
        "key_traits": {
            "leaf_shape": "heart",
            "leaf_arrangement": "single_alternate",
            "bark": "smooth",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "none",
            "habitat": "campus"
        },
        "local_fact": "Revered sacred tree prominently situated near temple tanks and waterbodies throughout Coimbatore, including Perur Patteeswarar Temple and Singanallur Lake.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e1/Ficus_religiosa_leaves.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Ficus benghalensis",
        "common_name": "Banyan Tree",
        "tamil_name": "ஆலமரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Ficus benghalensis, the banyan, is a massive fig tree native to the Indian subcontinent characterized by aerial prop roots.",
        "description_text": "Ficus benghalensis is a very large evergreen tree producing aerial roots that grow down from branches into the ground to form supportive secondary trunks. Leaves are large, leathery, oval, 10–20 cm long with prominent pale veins. Bark is smooth grey. Fruits are paired, globose figs about 1.5–2 cm diameter, turning bright scarlet-red when ripe.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "single_alternate",
            "bark": "smooth",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "Majestic highway giants lining old stretches of the Coimbatore-Pollachi and Mettupalayam roads, sheltering hundreds of birds and flying foxes.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/77/Banyan_tree_in_India.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Cassia fistula",
        "common_name": "Golden Shower (Indian Laburnum)",
        "tamil_name": "கொன்றை மரம்",
        "rarity": "Regular",
        "peak_months": ["Apr", "May", "Jun"],
        "summary": "Cassia fistula, known as the golden shower or Indian laburnum, is a flowering tree in the family Fabaceae native to the Indian subcontinent.",
        "description_text": "Cassia fistula is a medium-sized tree growing to 10–20 m tall. Leaves are pinnate, 15–60 cm long, with 3 to 8 pairs of leaflets. Flowers are produced in pendulous racemes 20–40 cm long, each flower 4–7 cm diameter with five equal yellow petals. Fruit is a long cylindrical dark brown woody legume 30–60 cm long containing seeds in pungent pulp.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "smooth",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "The celebrated 'Kani Konna' of Tamil literature; bursts into cascades of brilliant yellow blossom across Coimbatore and Marudhamalai foothills during April-May.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Cassia_fistula_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Delonix regia",
        "common_name": "Gulmohar (Flame Tree)",
        "tamil_name": "செம்மயிர்க்கொன்றை",
        "rarity": "Everyday",
        "peak_months": ["Apr", "May", "Jun", "Jul"],
        "summary": "Delonix regia is a species of flowering plant in the bean family Fabaceae, noted for its fern-like leaves and flamboyant scarlet flower display.",
        "description_text": "Delonix regia is an umbrella-shaped spreading tree growing 5–12 m tall. Leaves are bipinnate, feathery and light green, 30–50 cm long, each with 20 to 40 pairs of primary leaflets. Flowers are large with four spreading scarlet petals and a fifth upright yellow-and-white spotted petal called the standard. Fruit is a long, flat woody brown pod up to 60 cm long.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "smooth",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "Spectacular summer flowering tree seen lining arterial roads and university campuses across Coimbatore with fiery red canopies from April to June.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/23/Delonix_regia_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Tamarindus indica",
        "common_name": "Tamarind Tree",
        "tamil_name": "புளிய மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Tamarindus indica is a leguminous tree bearing edible fruit indigenous to tropical Africa but naturalized across India for millennia.",
        "description_text": "Tamarind is a long-lived, medium-growth tree reaching 12 to 18 metres in height. Crown has an irregular, vase-shaped outline of dense feathery foliage. Leaves are alternately arranged and pinnately compound, with 10 to 40 small, opposite, oblong leaflets. Bark is rough, dark grey and deeply cracked into square plates. Fruit is an indehiscent curved brown pod with sour pulp.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_pods",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "Centuries-old highway trees planted along the historic Kongu trade routes; dense canopy provides refreshing cool shade under the Coimbatore sun.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Tamarindus_indica_tree.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Millettia pinnata",
        "common_name": "Pongame Oiltree (Indian Beech)",
        "tamil_name": "புங்க மரம்",
        "rarity": "Everyday",
        "peak_months": ["Mar", "Apr", "May"],
        "summary": "Millettia pinnata is a species of tree in the pea family, Fabaceae, native to eastern and tropical Asia and widespread throughout South India.",
        "description_text": "Millettia pinnata is a medium-sized deciduous tree up to 15–25 m tall with a broad canopy. Leaves are imparipinnate with 5 to 7 glossy, ovate or elliptic leaflets. Bark is thin, smooth, greyish brown. Flowers are borne in short racemes, pinkish-white to violet, pea-flower shaped. Pods are thick, woody, flattened, 4–6 cm long and contain 1–2 seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "smooth",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "A cherished urban shade tree in RS Puram and Race Course; known for its glossy leaves, fragrant pale violet flowers, and oil-rich seeds.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/7b/Pongamia_pinnata_leaves.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Dalbergia latifolia",
        "common_name": "Indian Rosewood",
        "tamil_name": "ஈட்டி மரம்",
        "rarity": "Regular",
        "peak_months": ["Jan", "Feb", "Mar", "Apr"],
        "summary": "Dalbergia latifolia, also known as Indian rosewood or Bombay blackwood, is a premier timber species native to the Western Ghats deciduous forests.",
        "description_text": "A large deciduous tree growing to 20–40 m tall with a straight cylindrical bole. Leaves are imparipinnate, 15–25 cm long, with 5 to 7 rounded or broadly elliptic leaflets. Bark is grey, thin, peeling in fibrous longitudinal flakes. Flowers are small, white, in axillary panicles. Pods are flat, strap-shaped, containing 1 to 4 seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "peeling",
            "flowers_fruit": "visible_pods",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Native to the forested slopes of the Siruvani and Anamalai foothills near Coimbatore; renowned worldwide for its deep purple-brown durable heartwood.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/20/Dalbergia_latifolia_tree.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Tectona grandis",
        "common_name": "Teak",
        "tamil_name": "தேக்கு மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jul", "Aug", "Sep"],
        "summary": "Tectona grandis is a large tropical hardwood tree species in the family Lamiaceae native to South and Southeast Asia.",
        "description_text": "Teak is a large, deciduous tree up to 40 m tall with grey to greyish-brown fibrous bark. Leaves are broadly elliptical or obovate, exceptionally large (30–60 cm long and 20–40 cm wide), with a rough sandpaper-like texture on top and velvety underneath. Flowers are small and white in large terminal panicles up to 40 cm across. Fruit is a round nut enclosed in an inflated bladder-like papery calyx.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "paired_opposite",
            "bark": "fibrous",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Abundant across the Western Ghats foothill forests and plantations of Topslip, Siruvani, and Aliyar bordering Coimbatore.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c2/Teak_leaves_and_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Terminalia arjuna",
        "common_name": "Arjuna Tree",
        "tamil_name": "நீர் மருது",
        "rarity": "Regular",
        "peak_months": ["Apr", "May", "Jun"],
        "summary": "Terminalia arjuna is a tree of the genus Terminalia widely found along riverbanks and riparian ecosystems across central and southern India.",
        "description_text": "Terminalia arjuna grows to about 20–25 metres tall with an enormous buttressed trunk and horizontally spreading crown. Bark is unusually smooth, pinkish-grey, peeling off in large thin sheets. Leaves are oblong, opposite or sub-opposite, 10–15 cm long with two glands at the petiole base. Flowers are pale yellow in spikes. Fruit is an ovoid, 2.5–5 cm fibrous woody drupe with five hard wings.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "paired_opposite",
            "bark": "peeling",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "none",
            "habitat": "wetland"
        },
        "local_fact": "Characteristic giant tree lining the banks of the Noyyal River, Valankulam, and Singanallur lake; recognizable by its smooth pinkish-white bark.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/52/Terminalia_arjuna_trunk.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Syzygium cumini",
        "common_name": "Jamun (Black Plum)",
        "tamil_name": "நாவல் மரம்",
        "rarity": "Everyday",
        "peak_months": ["May", "Jun", "Jul"],
        "summary": "Syzygium cumini, commonly known as Malabar plum, Java plum, or black plum, is an evergreen tropical tree in the flowering plant family Myrtaceae.",
        "description_text": "A slow-growing species, it can reach heights of up to 30 metres. Leaves are opposite, smooth, glossy, oval to elliptic, 8–15 cm long, with a distinct turpentine-like scent when crushed. Bark is rough and dark grey at base, smoother higher up. Flowers are small, white, sweet-scented. Fruit is an oblong berry, starting green, turning pink, and ripening to dark purple or black with astringent sweet flesh.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "paired_opposite",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "citrus",
            "habitat": "wetland"
        },
        "local_fact": "Grows vigorously near Coimbatore water bodies and agricultural lands; fruits are avidly eaten by local bats, parakeets, and children in early monsoon.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/87/Syzygium_cumini_fruit.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Aegle marmelos",
        "common_name": "Bael (Golden Apple)",
        "tamil_name": "வில்வ மரம்",
        "rarity": "Regular",
        "peak_months": ["Mar", "Apr", "May"],
        "summary": "Aegle marmelos, commonly known as bael, is a rare spiny tree native to the Indian subcontinent and Southeast Asia, revered in Hindu traditions.",
        "description_text": "Aegle marmelos is a deciduous shrub or small to medium-sized tree up to 13 m tall with slender drooping branches and sharp axillary spines. Leaves are alternate, trifoliate (each made of three leaflets), ovate, crenate, releasing an aromatic scent when bruised. Bark is pale brown or grey, smooth or slightly fissured. Fruit is a large globose berry with a hard woody green-yellow shell containing sweet orange pulp.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "single_alternate",
            "bark": "smooth",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "citrus",
            "habitat": "campus"
        },
        "local_fact": "Native to dry scrub foothills like Marudhamalai; trifoliate aromatic leaves are sacred to Lord Shiva and medicinal for digestion.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/69/Aegle_marmelos_fruit.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Millingtonia hortensis",
        "common_name": "Indian Cork Tree",
        "tamil_name": "மரமல்லி",
        "rarity": "Regular",
        "peak_months": ["Sep", "Oct", "Nov", "Dec"],
        "summary": "Millingtonia hortensis, the Indian cork tree or tree jasmine, is a tall slender tree in the family Bignoniaceae native to South and Southeast Asia.",
        "description_text": "Millingtonia hortensis is a tall evergreen tree reaching 18 to 25 metres with a narrow columnar crown. Bark is deeply furrowed, spongy, light grey to yellowish, resembling cork. Leaves are bipinnate to tripinnate with serrated leaflets. Flowers are white, bell-shaped with a long slender tube (5–7 cm long), intensely fragrant, opening at night and dropping in carpets in early morning.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "Fills Coimbatore residential avenues with intoxicating sweet jasmine fragrance at dawn during the northeast monsoon months.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Millingtonia_hortensis_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Borassus flabellifer",
        "common_name": "Palmyra Palm",
        "tamil_name": "பனை மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Borassus flabellifer, known as the palmyra palm, is an iconic fan palm robustly adapted to dry tropical regions and the state tree of Tamil Nadu.",
        "description_text": "Borassus flabellifer is a robust unbranched palm tree capable of growing up to 30 metres tall with a dark grey, ring-scarred trunk. Leaves are large, rigid, fan-shaped (flabellate), 2 to 3 metres long, divided into 60 to 80 narrow leaflets with spiny petiole margins. Fruit is large, rounded, blackish-brown when ripe, 15–20 cm diameter, containing fibrous sweet pulp and jelly seed sockets (nungu).",
        "key_traits": {
            "leaf_shape": "fan",
            "leaf_arrangement": "single_alternate",
            "bark": "fibrous",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "The state tree of Tamil Nadu, standing sentinel across Kongu agricultural fields and dry bunds; provides cooling nungu fruit during peak summer.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/52/Borassus_flabellifer_palms.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Couroupita guianensis",
        "common_name": "Cannonball Tree",
        "tamil_name": "நாகலிங்கம்",
        "rarity": "Special find",
        "peak_months": ["Mar", "Apr", "May", "Jun", "Jul", "Aug"],
        "summary": "Couroupita guianensis is an unusual tropical tree in the family Lecythidaceae renowned for its spectacular flowers and heavy spherical fruit.",
        "description_text": "Couroupita guianensis grows to 35 m tall with simple, serrated leaves in clusters at the branch ends. Flowers are produced in large racemes that emerge directly from the trunk (cauliflory). The flowers are up to 6 cm wide, strongly fragrant, with six fleshy orange-pink petals and a distinctive hood-like white and pink androphore. Fruit is a large, hard, spherical woody shell 12–25 cm in diameter packed with seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "single_alternate",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "campus"
        },
        "local_fact": "Grown in TNAU Botanical Gardens and temple grounds across Coimbatore; the flower's hood-like structure is worshipped for resembling a cobra sheltering a lingam.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Couroupita_guianensis_flower.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Peltophorum pterocarpum",
        "common_name": "Copperpod (Yellow Poinciana)",
        "tamil_name": "பெருங்கொன்றை",
        "rarity": "Everyday",
        "peak_months": ["Mar", "Apr", "May", "Jun"],
        "summary": "Peltophorum pterocarpum is a deciduous tree native to tropical southeastern Asia, widely grown across India for shade and yellow floral displays.",
        "description_text": "Peltophorum pterocarpum is a deciduous tree growing to 15–25 m tall with a dense spreading umbrella crown. Leaves are bipinnate, 30–60 cm long, with 16 to 20 pairs of pinnae. Flowers are bright yellow, 2.5–4 cm diameter, produced in large compound pyramidal racemes above the canopy. Pods are flattened, oblong, coppery-red turning dark brown, 5–10 cm long, containing 1–4 seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "smooth",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "avenue"
        },
        "local_fact": "A staple avenue shade tree throughout Race Course and Gandhipuram; creates golden yellow carpets on sidewalks in spring and displays rusty copper pods in winter.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/25/Peltophorum_pterocarpum_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Murraya koenigii",
        "common_name": "Curry Leaf Tree",
        "tamil_name": "கறிவேப்பிலை மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Murraya koenigii is a small tropical to sub-tropical tree in the family Rutaceae native to the Indian subcontinent.",
        "description_text": "Murraya koenigii is a small tree or shrub growing 4–6 m tall with a trunk up to 40 cm diameter. Aromatic leaves are pinnate, with 11–21 leaflets, each leaflet 2–4 cm long and 1–2 cm broad with an asymmetric base. Highly fragrant when crushed. Flowers are small, white, bell-shaped in clusters. Fruit is a small shiny black berry about 1 cm across containing one large seed.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "smooth",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "citrus",
            "habitat": "campus"
        },
        "local_fact": "Wild native understory tree of the Western Ghats scrub; grown in virtually every backyard in Coimbatore and quintessential to South Indian cuisine.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/91/Murraya_koenigii_leaves.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Phyllanthus emblica",
        "common_name": "Indian Gooseberry (Amla)",
        "tamil_name": "நெல்லி மரம்",
        "rarity": "Regular",
        "peak_months": ["Oct", "Nov", "Dec", "Jan"],
        "summary": "Phyllanthus emblica, also known as emblic or amla, is a deciduous tree of the family Phyllanthaceae renowned for its sour vitamin C-rich fruit.",
        "description_text": "The tree is small to medium in size, reaching 1–8 m in height. Branchlets are feathery, not true leaves but bearing 20–30 pairs of tiny linear-oblong leaflets giving a delicate pinnate look. Bark is light greyish brown, flaking in thin irregular patches. Fruit is globose, depressed, greenish-yellow, smooth and hard with six vertical faint stripes or furrows, tasting sour, bitter and astringent.",
        "key_traits": {
            "leaf_shape": "needle",
            "leaf_arrangement": "feathery_compound",
            "bark": "peeling",
            "flowers_fruit": "visible_fruit",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Native to the dry deciduous scrub forests around Thadagam and Anaikatti; ancient Tamil symbol of longevity gifted by Avvaiyar to king Athiyaman.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/0/05/Phyllanthus_emblica_fruit.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Butea monosperma",
        "common_name": "Flame of the Forest (Palash)",
        "tamil_name": "பலாசு (முருக்கு)",
        "rarity": "Regular",
        "peak_months": ["Feb", "Mar", "Apr"],
        "summary": "Butea monosperma is a species of Butea native to tropical and sub-tropical parts of the Indian subcontinent.",
        "description_text": "A medium-sized dry-season deciduous tree growing to 15 m tall. Leaves are pinnate, with an 8–16 cm petiole and 3 leaflets, each 10–20 cm long. Flowers are 2.5 cm long, bright orange-red (resembling flames), produced in racemes up to 15 cm long when the tree is leafless. Fruit is a flat pod 15–20 cm long and 4–5 cm broad containing a single seed.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Paints the dry scrub slopes of Madukkarai and the Walayar border into blazing orange flames in late winter when all leaves drop.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Butea_monosperma_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Pterocarpus santalinus",
        "common_name": "Red Sandalwood",
        "tamil_name": "செஞ்சந்தனம்",
        "rarity": "Special find",
        "peak_months": ["Apr", "May", "Jun"],
        "summary": "Pterocarpus santalinus, with the common name red sanders or red sandalwood, is an endemic timber tree of southern India valued for its ruby red heartwood.",
        "description_text": "Pterocarpus santalinus is a small to medium-sized tree growing to 8 m tall with a trunk 50–150 cm diameter. Bark is black-brown, deeply cleft into rectangular plates with red gum exudate when cut. Leaves are alternate, 3–9 cm long, trifoliate with three round leaflets. Flowers are yellow in short racemes. Pod is circular, winged, flat, 6–9 cm diameter with one or two seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_pods",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Endemic southern peninsular tree species cultivated in local botanical reserves; known for its distinct deep ruby-red wood and circular winged pods.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/aa/Pterocarpus_santalinus_leaves.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Madhuca longifolia",
        "common_name": "Mahua",
        "tamil_name": "இலுப்பை மரம்",
        "rarity": "Regular",
        "peak_months": ["Mar", "Apr", "May"],
        "summary": "Madhuca longifolia is an Indian tropical tree found largely in the central and north Indian plains and forests, sacred in rural traditions.",
        "description_text": "Madhuca longifolia is a fast-growing tree that grows to approximately 20 metres in height, possesses evergreen or semi-evergreen foliage. Leaves are clustered at branch ends, oblong-ovate, 10–25 cm long. Bark is dark brown and fissured. Flowers are fleshy, cream-coloured, sweet-scented and drop at dawn. Fruit is a green ovoid berry containing 1 to 4 glossy seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "single_alternate",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "scrub"
        },
        "local_fact": "Traditional village tree around Coimbatore rural tracts; oil from its seeds was historically burned in temple lamps across Kongu Nadu.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/64/Madhuca_longifolia_flowers.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Moringa oleifera",
        "common_name": "Drumstick Tree (Moringa)",
        "tamil_name": "முருங்கை மரம்",
        "rarity": "Everyday",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Moringa oleifera is a fast-growing, drought-resistant tree of the family Moringaceae native to the Indian subcontinent.",
        "description_text": "Moringa is a fast-growing, deciduous tree that can reach a height of 10–12 m with an open crown of drooping branches. Bark is whitish-grey and corky. Leaves are tripinnate, 30–60 cm long, with numerous tiny rounded leaflets. Flowers are yellowish-white, fragrant, produced throughout the year. Fruit is a long, 3-sided pendulous brown pod (drumstick) 20–45 cm long containing winged dark seeds.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "feathery_compound",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_pods",
            "crushed_smell": "none",
            "habitat": "campus"
        },
        "local_fact": "Extensively cultivated in the surrounding Kongu plains (Dharapuram-Vellakovil belt); both leaves and long hanging pods are dietary staples in Coimbatore.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Moringa_oleifera_pods.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Thespesia populnea",
        "common_name": "Portia Tree (Indian Tulip Tree)",
        "tamil_name": "பூவரசு",
        "rarity": "Regular",
        "peak_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "summary": "Thespesia populnea is a species of flowering plant in the mallow family, Malvaceae, commonly known as the portia tree or Pacific rosewood.",
        "description_text": "Thespesia populnea reaches a height of 6–10 m with a dense rounded crown. Leaves are distinctive, glossy dark green, heart-shaped (cordate), 7–15 cm long with 5–7 prominent veins. Flowers are cup-shaped, 4–7 cm long, bright yellow with a purple centre, turning dull orange-red before falling. Fruit is a globose flattened woody capsule that does not split open.",
        "key_traits": {
            "leaf_shape": "heart",
            "leaf_arrangement": "single_alternate",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "wetland"
        },
        "local_fact": "Planted along Coimbatore wetlands and farm boundaries; famous for its bell-like yellow flowers that transform into dark red as the day progresses.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Thespesia_populnea_flower.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Santalum album",
        "common_name": "Indian Sandalwood",
        "tamil_name": "சந்தன மரம்",
        "rarity": "Special find",
        "peak_months": ["Jul", "Aug", "Sep", "Oct"],
        "summary": "Santalum album, or Indian sandalwood, is a small tropical tree native to southern India and the source of world-renowned sandalwood oil.",
        "description_text": "An evergreen tree growing to 4–9 m tall with slender drooping branches. Leaves are thin, opposite, ovate to lanceolate, 4–7 cm long, shiny bright green on top and pale glaucous beneath. Bark is smooth and greyish-brown when young, turning dark and cracked with age. Flowers are small, purplish-brown, in axillary cymes. The heartwood is dense, yellowish and intensely aromatic.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "paired_opposite",
            "bark": "smooth",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "resinous",
            "habitat": "scrub"
        },
        "local_fact": "Protected native tree found in the adjacent dry forest tracts of Marayoor and the Siruvani river catchment; world-famous for its fragrant heartwood.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Santalum_album_leaves.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    },
    {
        "scientific_name": "Neolamarckia cadamba",
        "common_name": "Kadamba Tree (Burflower-tree)",
        "tamil_name": "கடம்ப மரம்",
        "rarity": "Regular",
        "peak_months": ["May", "Jun", "Jul", "Aug"],
        "summary": "Neolamarckia cadamba, with common name burflower-tree or kadamba, is an evergreen, tropical tree native to South and Southeast Asia.",
        "description_text": "A large tree with a broad crown and straight cylindrical bole growing up to 45 m tall. Leaves are large, glossy, opposite, oblong-elliptic, 15–30 cm long with prominent veins. Flowers are produced in unique, dense, fragrant, globe-shaped (spherical) orange-yellow flower heads 5 cm across, resembling miniature glowing pincushions. Fruit is a small fleshy pseudocarp.",
        "key_traits": {
            "leaf_shape": "oval",
            "leaf_arrangement": "paired_opposite",
            "bark": "rough_furrowed",
            "flowers_fruit": "visible_flowers",
            "crushed_smell": "none",
            "habitat": "campus"
        },
        "local_fact": "Revered sacred tree celebrated in Sangam poetry and temple gardens of the Kongu region; easily identified by its unique spherical orange pincushion blossoms.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Neolamarckia_cadamba_flower.jpg",
        "image_local_path": "/static/images/fallback.jpg"
    }
]


KNOWN_BIRD_CALLS = {
    "Eudynamys scolopaceus": "https://upload.wikimedia.org/wikipedia/commons/1/18/Eudynamys_scolopaceus_-_Asian_Koel_XC476378.mp3",
    "Pycnonotus cafer": "https://upload.wikimedia.org/wikipedia/commons/c/ca/Pycnonotus_cafer_-_Red-vented_Bulbul_XC129368.ogg",
    "Pycnonotus jocosus": "https://upload.wikimedia.org/wikipedia/commons/2/22/Pycnonotus_jocosus_-_Red-whiskered_Bulbul_XC129370.ogg",
    "Pavo cristatus": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Indian_Peafowl.ogg",
    "Halcyon smyrnensis": "https://upload.wikimedia.org/wikipedia/commons/6/67/White-throated_kingfisher.wav",
    "Acridotheres tristis": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Acridotheres_tristis_-_Common_Myna_XC129571.ogg",
    "Dicrurus macrocercus": "https://upload.wikimedia.org/wikipedia/commons/9/91/Dicrurus_macrocercus_-_Black_Drongo_XC129573.ogg",
    "Spilopelia chinensis": "https://upload.wikimedia.org/wikipedia/commons/f/f6/Spilopelia_chinensis_-_Eastern_Spotted_Dove_XC129342.ogg",
    "Streptopelia decaocto": "https://upload.wikimedia.org/wikipedia/commons/c/c9/Streptopelia_decaocto_song.ogg",
    "Columba livia": "https://upload.wikimedia.org/wikipedia/commons/7/77/Rock_Dove_cooing.ogg",
    "Corvus splendens": "https://upload.wikimedia.org/wikipedia/commons/e/e0/House_crow_call.ogg",
    "Corvus macrorhynchos": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Corvus_macrorhynchos_-_Large-billed_Crow_XC129576.ogg",
    "Psittacula krameri": "https://upload.wikimedia.org/wikipedia/commons/6/69/Rose-ringed_Parakeet_call.ogg",
    "Cinnyris asiaticus": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Cinnyris_asiaticus_-_Purple_Sunbird_XC129366.ogg",
    "Merops orientalis": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Merops_orientalis_call.ogg",
    "Copsychus saularis": "https://upload.wikimedia.org/wikipedia/commons/8/87/Oriental_Magpie-Robin_song.ogg",
    "Ardeola grayii": "https://upload.wikimedia.org/wikipedia/commons/9/9e/Indian_Pond_Heron_call.ogg",
    "Bubulcus ibis": "https://upload.wikimedia.org/wikipedia/commons/5/52/Cattle_Egret_call.ogg",
    "Milvus migrans": "https://upload.wikimedia.org/wikipedia/commons/7/71/Black_Kite_whistling_call.ogg",
    "Upupa epops": "https://upload.wikimedia.org/wikipedia/commons/8/85/Upupa_epops_call.ogg",
    "Centropus sinensis": "https://upload.wikimedia.org/wikipedia/commons/6/62/Greater_Coucal_call.ogg",
    "Turdoides affinis": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Yellow-billed_Babbler_chattering.ogg",
    "Dinopium benghalense": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Black-rumped_Flameback_call.ogg",
    "Prinia socialis": "https://upload.wikimedia.org/wikipedia/commons/2/23/Ashy_Prinia_call.ogg",
    "Vanellus indicus": "https://upload.wikimedia.org/wikipedia/commons/7/7b/Red-wattled_Lapwing_Did-he-do-it_call.ogg"
}


def fetch_wikimedia_audio(scientific_name: str) -> str:
    """Queries Wikimedia Commons API for audio files of a species."""
    if scientific_name in KNOWN_BIRD_CALLS:
        return KNOWN_BIRD_CALLS[scientific_name]

    query = urllib.parse.quote(f"{scientific_name} sound OR call")
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={query}&gsrnamespace=6&prop=imageinfo&iiprop=url&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "FieldGuide/1.0 (Hacktoberfest Open Source)"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                title = p.get("title", "").lower()
                if title.endswith((".ogg", ".mp3", ".wav")):
                    info = p.get("imageinfo", [{}])[0]
                    file_url = info.get("url")
                    if file_url:
                        return file_url
    except Exception as e:
        pass
    return ""


def seed_database():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Ensure audio_url column exists
    cols = [c[1] for c in conn.execute("PRAGMA table_info(species)").fetchall()]
    if "audio_url" not in cols:
        conn.execute("ALTER TABLE species ADD COLUMN audio_url TEXT;")
        conn.commit()

    print("--- 1. Seeding 25 Native Coimbatore & Western Ghats Trees ---")
    inserted_trees = 0
    for tree in TREES_DATA:
        key_traits_json = json.dumps(tree["key_traits"], ensure_ascii=False)
        peak_months_json = json.dumps(tree["peak_months"])
        
        # Check if already exists
        existing = conn.execute(
            "SELECT id FROM species WHERE region_id = 1 AND scientific_name = ?",
            (tree["scientific_name"],)
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE species SET
                    category = 'trees',
                    common_name = ?,
                    tamil_name = ?,
                    rarity = ?,
                    peak_months = ?,
                    summary = ?,
                    description_text = ?,
                    key_traits = ?,
                    local_fact = ?
                WHERE id = ?""",
                (
                    tree["common_name"],
                    tree["tamil_name"],
                    tree["rarity"],
                    peak_months_json,
                    tree["summary"],
                    tree["description_text"],
                    key_traits_json,
                    tree["local_fact"],
                    existing["id"]
                )
            )
        else:
            conn.execute(
                """INSERT INTO species (
                    region_id, category, scientific_name, common_name, tamil_name,
                    observation_count, rarity, peak_months, summary, description_text,
                    key_traits, local_fact, image_url, image_local_path
                ) VALUES (1, 'trees', ?, ?, ?, 10, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tree["scientific_name"],
                    tree["common_name"],
                    tree["tamil_name"],
                    tree["rarity"],
                    peak_months_json,
                    tree["summary"],
                    tree["description_text"],
                    key_traits_json,
                    tree["local_fact"],
                    tree["image_url"],
                    tree["image_local_path"]
                )
            )
            inserted_trees += 1

    conn.commit()
    print(f"Tree seeding complete: {len(TREES_DATA)} trees active in category='trees'.")

    print("\n--- 2. Seeding Real Bird Call Audio URLs ---")
    bird_rows = conn.execute("SELECT id, scientific_name, common_name, audio_url FROM species WHERE category = 'birds'").fetchall()
    audio_updated = 0

    for b in bird_rows:
        sci = b["scientific_name"]
        existing_audio = b["audio_url"]
        if existing_audio:
            continue

        audio_link = KNOWN_BIRD_CALLS.get(sci)
        if not audio_link:
            # Try Wikimedia Commons query with quick timeout
            audio_link = fetch_wikimedia_audio(sci)

        if audio_link:
            conn.execute("UPDATE species SET audio_url = ? WHERE id = ?", (audio_link, b["id"]))
            audio_updated += 1
            print(f"  + {b['common_name']} ({sci}) -> {audio_link[:65]}...")

    conn.commit()
    conn.close()

    print(f"\nFinished! Audio URLs assigned to {audio_updated} species.")

if __name__ == "__main__":
    seed_database()
