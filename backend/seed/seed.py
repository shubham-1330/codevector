"""
Seed script – inserts realistic products per category.

Usage:
    cd backend
    python -m seed.seed

Environment:
    DATABASE_URL  (from .env or shell)
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.models.product import Product  # noqa: F401

setup_logging()
logger = logging.getLogger("codevector.seed")

_TWO_YEARS_SECONDS = 2 * 365 * 24 * 3600
_NOW = datetime.now(timezone.utc)

PRODUCTS_BY_CATEGORY: dict[str, list[tuple[str, float, float]]] = {
    "Electronics": [
        ("Apple iPhone 15 Pro 256GB", 999.99, 1199.99),
        ("Samsung Galaxy S24 Ultra", 1199.99, 1399.99),
        ("Sony WH-1000XM5 Headphones", 299.99, 399.99),
        ("Apple MacBook Air M3 13\"", 1099.99, 1299.99),
        ("Dell XPS 15 Laptop", 1499.99, 1899.99),
        ("LG 55\" OLED 4K Smart TV", 1299.99, 1799.99),
        ("Apple iPad Pro 12.9\"", 1099.99, 1299.99),
        ("Samsung 65\" QLED 4K TV", 999.99, 1499.99),
        ("Sony PlayStation 5", 499.99, 549.99),
        ("Microsoft Xbox Series X", 499.99, 549.99),
        ("Nintendo Switch OLED", 349.99, 379.99),
        ("Apple Watch Series 9 45mm", 399.99, 499.99),
        ("GoPro HERO12 Black Camera", 349.99, 399.99),
        ("Canon EOS R50 Mirrorless Camera", 679.99, 799.99),
        ("Bose SoundLink Flex Speaker", 149.99, 179.99),
        ("Amazon Echo Dot 5th Gen", 49.99, 59.99),
        ("Google Nest Hub Max", 199.99, 229.99),
        ("Anker 65W USB-C Charger", 35.99, 45.99),
        ("Samsung 1TB SSD T7 Shield", 89.99, 119.99),
        ("Logitech MX Master 3S Mouse", 99.99, 109.99),
        ("Razer DeathAdder V3 Gaming Mouse", 69.99, 89.99),
        ("Mechanical Keyboard Keychron K8", 89.99, 109.99),
        ("DJI Mini 4 Pro Drone", 759.99, 959.99),
        ("Apple AirPods Pro 2nd Gen", 199.99, 249.99),
        ("Samsung Galaxy Watch 6", 269.99, 299.99),
    ],
    "Books": [
        ("Atomic Habits by James Clear", 14.99, 18.99),
        ("The Psychology of Money", 13.99, 17.99),
        ("Rich Dad Poor Dad", 10.99, 14.99),
        ("Zero to One by Peter Thiel", 15.99, 19.99),
        ("Deep Work by Cal Newport", 14.99, 17.99),
        ("The Lean Startup by Eric Ries", 15.99, 19.99),
        ("Thinking Fast and Slow", 14.99, 18.99),
        ("The 4-Hour Work Week", 13.99, 17.99),
        ("Sapiens by Yuval Noah Harari", 15.99, 19.99),
        ("The Alchemist by Paulo Coelho", 12.99, 15.99),
        ("Clean Code by Robert Martin", 34.99, 44.99),
        ("The Pragmatic Programmer", 39.99, 49.99),
        ("Design Patterns: GoF", 44.99, 54.99),
        ("Introduction to Algorithms", 79.99, 99.99),
        ("Python Crash Course 3rd Ed.", 29.99, 39.99),
        ("JavaScript: The Good Parts", 24.99, 34.99),
        ("Harry Potter Complete Box Set", 79.99, 99.99),
        ("The Great Gatsby", 9.99, 13.99),
        ("To Kill a Mockingbird", 10.99, 14.99),
        ("1984 by George Orwell", 9.99, 12.99),
        ("The Midnight Library", 13.99, 17.99),
        ("It Ends with Us", 12.99, 16.99),
        ("Fourth Wing", 14.99, 18.99),
        ("The Body Keeps the Score", 16.99, 20.99),
        ("Ikigai: The Japanese Secret", 11.99, 15.99),
    ],
    "Clothing": [
        ("Levi's 501 Original Jeans", 59.99, 79.99),
        ("Nike Air Max 270 Sneakers", 129.99, 159.99),
        ("Adidas Ultraboost 23 Running Shoes", 149.99, 189.99),
        ("The North Face Puffer Jacket", 199.99, 279.99),
        ("Ralph Lauren Polo Shirt", 79.99, 99.99),
        ("Zara Slim Fit Chinos", 49.99, 69.99),
        ("H&M Basic Cotton T-Shirt Pack", 24.99, 34.99),
        ("Calvin Klein Underwear 3-Pack", 34.99, 44.99),
        ("Tommy Hilfiger Oxford Shirt", 69.99, 89.99),
        ("Uniqlo Ultra Light Down Jacket", 89.99, 119.99),
        ("Converse Chuck Taylor All Star", 59.99, 74.99),
        ("Vans Old Skool Sneakers", 64.99, 74.99),
        ("Lululemon Align Leggings", 98.00, 118.00),
        ("Under Armour HeatGear T-Shirt", 29.99, 39.99),
        ("Columbia Fleece Pullover", 69.99, 89.99),
        ("Patagonia Better Sweater Fleece", 139.00, 159.00),
        ("Ray-Ban Aviator Sunglasses", 154.00, 194.00),
        ("Timberland 6-Inch Premium Boot", 189.99, 219.99),
        ("Dr. Martens 1460 Pascal Boots", 159.99, 189.99),
        ("Champion Reverse Weave Hoodie", 59.99, 74.99),
        ("Carhartt WIP Canvas Pants", 79.99, 99.99),
        ("New Balance 574 Sneakers", 84.99, 99.99),
        ("Brooks Ghost 15 Running Shoes", 129.99, 149.99),
        ("Fossil Leather Belt", 39.99, 54.99),
        ("Hanes Crew Neck Sweatshirt", 29.99, 39.99),
    ],
    "Home & Garden": [
        ("Dyson V15 Detect Vacuum", 699.99, 799.99),
        ("Instant Pot Duo 7-in-1 6Qt", 89.99, 119.99),
        ("Ninja Air Fryer Max XL 5.5Qt", 119.99, 149.99),
        ("KitchenAid Stand Mixer 5Qt", 399.99, 499.99),
        ("Nespresso Vertuo Next Coffee", 159.99, 199.99),
        ("Keurig K-Elite Coffee Maker", 149.99, 189.99),
        ("iRobot Roomba j7+ Robot Vacuum", 599.99, 799.99),
        ("Philips Hue Starter Kit 4-Bulbs", 199.99, 249.99),
        ("IKEA KALLAX Shelf Unit 4x4", 179.99, 199.99),
        ("Casper Original Foam Pillow", 79.99, 99.99),
        ("Egyptian Cotton Sheet Set Queen", 59.99, 89.99),
        ("Le Creuset Dutch Oven 5.5Qt", 379.99, 419.99),
        ("All-Clad Stainless 10-Piece Set", 699.99, 799.99),
        ("Vitamix 5200 Blender", 449.99, 549.99),
        ("Weber Spirit II Gas Grill", 499.99, 599.99),
        ("DeWalt 20V Drill Combo Kit", 249.99, 299.99),
        ("Black+Decker 20V Leaf Blower", 79.99, 99.99),
        ("Fiskars 46\" Steel D-handle Spade", 34.99, 44.99),
        ("Miracle-Gro Potting Mix 16Qt", 14.99, 19.99),
        ("Ring Video Doorbell 4", 199.99, 249.99),
        ("Nest Learning Thermostat 3rd Gen", 249.99, 279.99),
        ("Brita Large 10-Cup Water Filter", 34.99, 44.99),
        ("OXO Good Grips 15-Piece Set", 79.99, 99.99),
        ("Rubbermaid Brilliance 22-Piece", 49.99, 64.99),
        ("Clorox Disinfecting Wipes 5-Pack", 19.99, 24.99),
    ],
    "Sports & Outdoors": [
        ("Peloton Bike+ Indoor Cycle", 2495.00, 2995.00),
        ("NordicTrack T Series Treadmill", 799.99, 999.99),
        ("Bowflex SelectTech 552 Dumbbells", 429.99, 549.99),
        ("TRX All-in-One Suspension Trainer", 149.99, 199.99),
        ("Manduka PRO Yoga Mat 6mm", 119.99, 139.99),
        ("Hydro Flask 32oz Water Bottle", 44.95, 54.95),
        ("Coleman 6-Person Camping Tent", 129.99, 169.99),
        ("REI Co-op Sleeping Bag 30°", 149.99, 199.99),
        ("Black Diamond Trekking Poles", 99.99, 139.99),
        ("Garmin Forerunner 255 GPS Watch", 349.99, 399.99),
        ("Fitbit Charge 6 Fitness Tracker", 159.99, 179.99),
        ("Wilson Pro Staff Tennis Racket", 189.99, 219.99),
        ("Spalding NBA Official Basketball", 149.99, 169.99),
        ("Callaway Strata Golf Club Set", 299.99, 399.99),
        ("Yeti Tundra 45 Cooler", 349.99, 399.99),
        ("Osprey Atmos AG 65 Backpack", 299.99, 349.99),
        ("Merrell Moab 3 Hiking Boots", 109.99, 134.99),
        ("Columbia Men's PFG Shorts", 39.99, 54.99),
        ("Yakima FullBack 2-Bike Hitch Rack", 229.99, 279.99),
        ("Trek FX 3 Disc Hybrid Bike", 899.99, 999.99),
        ("Schwinn Cruiser Bike 26\"", 329.99, 399.99),
        ("Speedo Vanquisher 2.0 Goggles", 19.99, 24.99),
        ("Decathlon 10L Running Vest", 44.99, 59.99),
        ("Theragun Elite Massage Gun", 299.99, 399.99),
        ("Jump Rope Speed Cable Steel", 29.99, 39.99),
    ],
    "Toys & Games": [
        ("LEGO Star Wars Millennium Falcon", 849.99, 999.99),
        ("LEGO Technic Bugatti Chiron", 449.99, 549.99),
        ("Monopoly Classic Board Game", 19.99, 29.99),
        ("Scrabble Classic Board Game", 19.99, 24.99),
        ("Jenga Classic Game", 14.99, 19.99),
        ("Uno Card Game", 9.99, 14.99),
        ("Exploding Kittens Card Game", 19.99, 24.99),
        ("Catan Board Game", 44.99, 54.99),
        ("Ticket to Ride Board Game", 44.99, 54.99),
        ("Barbie Dreamhouse 2023", 199.99, 259.99),
        ("Hot Wheels Ultimate Garage", 99.99, 129.99),
        ("Nerf Elite 2.0 Blaster", 29.99, 39.99),
        ("Funko Pop! Marvel Spider-Man", 11.99, 15.99),
        ("Play-Doh 36-Can Mega Set", 34.99, 44.99),
        ("Melissa & Doug Wooden Puzzle Set", 29.99, 39.99),
        ("Osmo Genius Starter Kit iPad", 69.99, 89.99),
        ("Kinetic Sand 11lbs Bundle", 49.99, 64.99),
        ("Roblox Gift Card $50", 50.00, 50.00),
        ("Magic: The Gathering Starter Kit", 14.99, 19.99),
        ("Pokémon Scarlet & Violet Booster", 14.99, 19.99),
        ("Remote Control Car Off-Road 4WD", 49.99, 69.99),
        ("Drone for Kids with Camera", 49.99, 69.99),
        ("Rubik's Cube 3x3 Original", 9.99, 12.99),
        ("K'NEX 521-Piece Building Set", 39.99, 49.99),
        ("Ravensburger 1000-Piece Puzzle", 19.99, 29.99),
    ],
    "Food & Grocery": [
        ("Quaker Old Fashioned Oats 10lb", 12.99, 16.99),
        ("Optimum Nutrition Gold Standard Whey 5lb", 54.99, 69.99),
        ("KIND Dark Chocolate Bars 12-Pack", 19.99, 24.99),
        ("Clif Bar Variety Pack 16-Count", 22.99, 27.99),
        ("Starbucks Pike Place Ground Coffee 2lb", 22.99, 27.99),
        ("Lavazza Super Crema Espresso 2.2lb", 24.99, 29.99),
        ("Ghirardelli Premium Hot Cocoa Mix", 12.99, 16.99),
        ("Manuka Honey MGO 400+ 8.8oz", 34.99, 44.99),
        ("Justin's Almond Butter Squeeze Packs 10ct", 14.99, 18.99),
        ("RXBar Protein Bar 12-Pack", 22.99, 27.99),
        ("Himalayan Pink Salt Fine 5lb", 14.99, 18.99),
        ("California Almonds Raw Unsalted 3lb", 24.99, 32.99),
        ("Mixed Nuts Deluxe 40oz Canister", 19.99, 24.99),
        ("Organic Coconut Oil Extra Virgin 54oz", 22.99, 28.99),
        ("Annie's Mac & Cheese 12-Pack", 14.99, 18.99),
        ("Kettle Brand Chips Variety 20-Pack", 19.99, 24.99),
        ("LaCroix Sparkling Water 24-Pack", 17.99, 22.99),
        ("Liquid I.V. Hydration Multiplier 30ct", 24.99, 31.99),
        ("Emergen-C Vitamin C 1000mg 60ct", 17.99, 22.99),
        ("Kirkland Signature Olive Oil 2L", 19.99, 24.99),
        ("Green Tea Bags Celestial 100ct", 12.99, 16.99),
        ("Organic Brown Rice 25lb", 29.99, 39.99),
        ("Ancient Grains Granola 28oz", 12.99, 16.99),
        ("Bai Antioxidant Infused Water 36-Pack", 29.99, 37.99),
        ("Bob's Red Mill Almond Flour 3lb", 16.99, 21.99),
    ],
    "Beauty & Personal Care": [
        ("CeraVe Moisturizing Cream 19oz", 18.99, 24.99),
        ("La Roche-Posay SPF 60 Sunscreen", 22.99, 29.99),
        ("Neutrogena Hydro Boost Serum", 24.99, 32.99),
        ("The Ordinary Niacinamide 10% Serum", 9.99, 13.99),
        ("Olaplex No.3 Hair Perfector", 29.99, 36.99),
        ("Pantene Shampoo & Conditioner Set", 14.99, 19.99),
        ("Dove Body Wash Deep Moisture 3-Pack", 16.99, 21.99),
        ("ELF Halo Glow Liquid Filter", 14.00, 18.00),
        ("Maybelline Sky High Mascara", 10.99, 13.99),
        ("Charlotte Tilbury Pillow Talk Lipstick", 35.00, 39.00),
        ("MAC Ruby Woo Lipstick", 22.00, 26.00),
        ("NARS Sheer Glow Foundation", 49.00, 54.00),
        ("Urban Decay Naked Eyeshadow Palette", 54.00, 64.00),
        ("Dyson Supersonic Hair Dryer", 429.99, 479.99),
        ("BaBylissPRO Titanium Flat Iron", 119.99, 149.99),
        ("Philips Norelco OneBlade Face", 34.99, 44.99),
        ("Gillette Fusion5 Razor + 12 Blades", 34.99, 44.99),
        ("Colgate Optic White Toothpaste 3-Pack", 14.99, 19.99),
        ("Listerine Cool Mint Mouthwash 2L", 11.99, 15.99),
        ("Dr. Bronner's Peppermint Castile Soap", 17.99, 22.99),
        ("Tree Hut Shea Sugar Scrub 18oz", 10.99, 13.99),
        ("Aveeno Daily Moisturizing Lotion 18oz", 12.99, 16.99),
        ("Biotin 10000mcg Hair Growth 120ct", 16.99, 22.99),
        ("Revlon One-Step Hair Dryer Brush", 39.99, 54.99),
        ("Cetaphil Gentle Skin Cleanser 16oz", 14.99, 18.99),
    ],
    "Automotive": [
        ("Michelin Defender T+H 225/65R17 Tire", 149.99, 189.99),
        ("Bosch ICON Wiper Blades 26\" Pair", 34.99, 44.99),
        ("Armor All Car Cleaning Kit 15-Piece", 29.99, 39.99),
        ("Chemical Guys Complete Car Care Kit", 69.99, 89.99),
        ("Meguiar's Ultimate Liquid Wax 16oz", 22.99, 29.99),
        ("OBD2 Scanner Bluetooth CarScan Pro", 39.99, 59.99),
        ("Garmin DriveSmart 76 GPS Navigator", 199.99, 249.99),
        ("Vantrue N4 Dash Cam Front/Rear", 199.99, 249.99),
        ("NOCO Boost Plus GB40 Jump Starter", 99.99, 129.99),
        ("Black+Decker 20V Inflator Pump", 44.99, 59.99),
        ("Turtle Wax ICE Seal N Shine 14oz", 17.99, 22.99),
        ("WeatherTech FloorLiners Front+Rear", 149.99, 189.99),
        ("Covercraft Weathershield HP Car Cover", 179.99, 229.99),
        ("Optima Batteries RedTop Starting", 199.99, 239.99),
        ("Castrol EDGE 5W-30 5Qt Motor Oil", 29.99, 39.99),
        ("K&N Engine Air Filter HP-1007", 44.99, 59.99),
        ("Rain-X Water Repellent Glass Treatment", 12.99, 16.99),
        ("Auto-Vox Solar Wireless Backup Camera", 79.99, 109.99),
        ("Steering Wheel Lock Anti-Theft Club", 34.99, 44.99),
        ("BDK MT-671-RD Car Floor Mat 4-Piece", 24.99, 34.99),
        ("Carlinkit 4.0 Wireless CarPlay Adapter", 79.99, 99.99),
        ("Thule Crossroads Roof Rack Fit Kit", 129.99, 159.99),
        ("Hella 550 Series Driving Lamp Kit", 79.99, 99.99),
        ("Rhino USA Tow Strap Recovery Kit", 39.99, 54.99),
        ("Energizer 800A Jump Starter Pack", 69.99, 89.99),
    ],
    "Health & Wellness": [
        ("Garden of Life Multivitamin for Men", 29.99, 39.99),
        ("Nature Made Vitamin D3 5000 IU 360ct", 19.99, 24.99),
        ("Omega-3 Fish Oil 2400mg 120 Softgels", 24.99, 32.99),
        ("Magnesium Glycinate 400mg 180ct", 19.99, 26.99),
        ("Ashwagandha 600mg 90 Capsules", 19.99, 27.99),
        ("Probiotics 100 Billion CFU 30ct", 29.99, 39.99),
        ("Collagen Peptides Powder Unflavored 1lb", 34.99, 44.99),
        ("Garden of Life Raw Protein 20 Servings", 29.99, 39.99),
        ("Melatonin 10mg 365ct Sleep Aid", 16.99, 22.99),
        ("Zinc 50mg Immune Support 200ct", 11.99, 15.99),
        ("Turmeric Curcumin 1500mg 180ct", 24.99, 32.99),
        ("Apple Cider Vinegar Gummies 60ct", 19.99, 26.99),
        ("Hair Skin Nails Vitamins 180ct", 24.99, 32.99),
        ("Fiber One Psyllium Husk Powder 15oz", 14.99, 19.99),
        ("Theraworx Muscle Cramp Relief 7.1oz", 19.99, 26.99),
        ("Bragg Organic Apple Cider Vinegar 32oz", 11.99, 15.99),
        ("Himalaya Ashwagandha 60 Caplets", 14.99, 19.99),
        ("NOW Supplements Vitamin C-1000 250ct", 19.99, 26.99),
        ("Pure Encapsulations B-Complex 60ct", 34.99, 44.99),
        ("Thorne Basic Nutrients 2/Day 60ct", 39.99, 49.99),
        ("Blood Pressure Monitor Omron Platinum", 79.99, 99.99),
        ("Oximeter Fingertip Pulse Zacurate", 19.99, 26.99),
        ("Digital Thermometer iHealth No-Touch", 29.99, 39.99),
        ("Heating Pad King Size with Auto Shutoff", 34.99, 44.99),
        ("Compression Socks 6-Pair for Women", 24.99, 32.99),
    ],
}

BATCH_SIZE = 500


def _random_timestamp() -> datetime:
    offset = timedelta(seconds=random.randint(0, _TWO_YEARS_SECONDS))
    return _NOW - offset


def _build_rows(total: int) -> list[dict]:
    rows = []
    categories = list(PRODUCTS_BY_CATEGORY.keys())
    for _ in range(total):
        category = random.choice(categories)
        name, price_min, price_max = random.choice(PRODUCTS_BY_CATEGORY[category])
        price = round(random.uniform(price_min, price_max), 2)
        ts = _random_timestamp()
        rows.append({
            "name": name,
            "category": category,
            "price": price,
            "created_at": ts,
            "updated_at": ts,
        })
    return rows


async def run_seed(total: int = 500) -> None:
    logger.info("Connecting to %s", settings.DATABASE_URL.split("@")[-1])
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Clearing existing products…")
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE products RESTART IDENTITY"))

    rows = _build_rows(total)
    t0 = time.perf_counter()
    logger.info("Seeding %d realistic products…", total)

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i: i + BATCH_SIZE]
        async with engine.begin() as conn:
            await conn.execute(insert(Product), batch)
        logger.info("Inserted %d / %d", min(i + BATCH_SIZE, total), total)

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar_one()

    await engine.dispose()
    logger.info("Done. %d products in DB (%.1fs)", count, time.perf_counter() - t0)


if __name__ == "__main__":
    asyncio.run(run_seed())
