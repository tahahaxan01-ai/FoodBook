/**
 * FoodBook Frontend Configuration & Media Asset Registry
 */
export const CONFIG = {
    APP_NAME: "FoodBook",
    API_BASE_URL: window.location.origin.includes(":8000") 
        ? `${window.location.origin}/api` 
        : "http://localhost:8000/api",
    SUPABASE_URL: "https://ahvzudsccvofskmeagkl.supabase.co",
    SUPABASE_ANON_KEY: "sb_publishable_5iOWGEDdltPGox_ZccQpMQ_CvKiumjh",
    ML_SERVICE_URL: "http://localhost:8001",
    DEFAULT_LOCATION: {
        name: "Gulberg, Lahore",
        latitude: 31.5126,
        longitude: 74.3436
    },
    LAHORE_AREAS: [
        { name: "Gulberg, Lahore", latitude: 31.5126, longitude: 74.3436, icon: "🏙️" },
        { name: "DHA (Defence), Lahore", latitude: 31.4707, longitude: 74.4098, icon: "🌳" },
        { name: "Johar Town, Lahore", latitude: 31.4697, longitude: 74.2728, icon: "🛍️" },
        { name: "Model Town, Lahore", latitude: 31.4883, longitude: 74.3214, icon: "🏡" },
        { name: "Mall Road / Old City", latitude: 31.5657, longitude: 74.3142, icon: "🏛️" },
        { name: "Bahria Town, Lahore", latitude: 31.3685, longitude: 74.1809, icon: "🏰" },
        { name: "Faisal Town, Lahore", latitude: 31.4984, longitude: 74.3092, icon: "🎓" },
        { name: "Shadman, Lahore", latitude: 31.5369, longitude: 74.3292, icon: "📍" }
    ],
    TASTE_DIMENSIONS: [
        { id: "spicy", name: "Spicy", emoji: "🌶️", color: "#EF4444", desc: "Heat and chili intensity" },
        { id: "sweet", name: "Sweet", emoji: "🍯", color: "#F59E0B", desc: "Sugar, honey, sweetness" },
        { id: "salty", name: "Salty", emoji: "🧂", color: "#3B82F6", desc: "Savory seasoning & salt" },
        { id: "sour", name: "Sour", emoji: "🍋", color: "#84CC16", desc: "Citrus, tangy notes" },
        { id: "umami", name: "Umami", emoji: "🍄", color: "#8B5CF6", desc: "Deep savory broth & meatiness" },
        { id: "smoky", name: "Smoky", emoji: "🔥", color: "#F97316", desc: "Charcoal, BBQ aroma" },
        { id: "creamy", name: "Creamy", emoji: "🧀", color: "#EC4899", desc: "Dairy, cheese, richness" },
        { id: "crispy", name: "Crispy", emoji: "🍟", color: "#EAB308", desc: "Crunch, fried texture" },
        { id: "rich", name: "Rich", emoji: "🍛", color: "#D97706", desc: "Heavy spices & deep gravy" }
    ],
    CUISINES: [
        { name: "Fast Food", icon: "🍔" },
        { name: "Pakistani", icon: "🍛" },
        { name: "Desi", icon: "🥘" },
        { name: "BBQ", icon: "🍢" },
        { name: "Chinese", icon: "🥡" },
        { name: "Italian", icon: "🍝" },
        { name: "Turkish", icon: "🥙" },
        { name: "Cafe", icon: "☕" },
        { name: "Desserts", icon: "🍰" },
        { name: "Seafood", icon: "🦐" },
        { name: "Continental", icon: "🥩" }
    ],
    
    // Curated high-resolution original restaurant photography & descriptions
    RESTAURANT_MEDIA: {
        "haveli-restaurant": {
            image: "https://images.unsplash.com/photo-1544025162-d76694265947?w=1200&auto=format&fit=crop&q=80",
            desc: "Iconic rooftop dining overlooking the illuminated Badshahi Mosque in the Walled City, serving authentic Pakistani BBQ, handi & mutton chops."
        },
        "bundu-khan-restaurant": {
            image: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1200&auto=format&fit=crop&q=80",
            desc: "Pakistan's legendary BBQ masters since 1948, celebrated for their signature Seekh Kababs, crispy Puri Parathas and White Karahi."
        },
        "cheezious": {
            image: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200&auto=format&fit=crop&q=80",
            desc: "Viral fast-food sensation famous for the Crown Crust Pizza, Beholder Zinger Burger, and oozing cheesy baked sticks."
        },
        "monal-lahore": {
            image: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&auto=format&fit=crop&q=80",
            desc: "Luxury rooftop restaurant above Liberty Roundabout in Gulberg with royal BBQ platters, tarragon steaks, and panoramic views."
        },
        "howdy": {
            image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1200&auto=format&fit=crop&q=80",
            desc: "Western-cowboy themed flame-grilled charcoal burgers, Son of a Bun double beef patties, and loaded wild fries."
        },
        "johnny-and-jugnu": {
            image: "https://images.unsplash.com/photo-1550547660-d9450f859349?w=1200&auto=format&fit=crop&q=80",
            desc: "Lahore's premier cult-favorite burger joint, famed for the Wephfil Greek burger, Firebird atomic burger, and signature wraps."
        },
        "cafe-aylanto": {
            image: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200&auto=format&fit=crop&q=80",
            desc: "Fine European dining on MM Alam Road featuring handmade smoked salmon truffle pastas, brick-oven pizzas, and prime tenderloin steaks."
        },
        "warid-butt-karahi": {
            image: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=1200&auto=format&fit=crop&q=80",
            desc: "The authentic street-food legend of Lakshmi Chowk, cooking world-famous desi makhan mutton and organic chicken karahi."
        },
        "saltn-pepper-village": {
            image: "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=1200&auto=format&fit=crop&q=80",
            desc: "Traditional village-themed live cooking experience with an expansive Pakistani buffet, fresh tandoor, and authentic regional delicacies."
        },
        "gloria-jeans-coffees-dha": {
            image: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80",
            desc: "Popular specialty coffee house in DHA serving handcrafted espresso, gourmet cheesecakes, and cozy brunch platters."
        },
        "broadway-pizza-dha": {
            image: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=1200&auto=format&fit=crop&q=80",
            desc: "Gigantic 21-inch slices, loaded peri-peri chicken toppings, and stuffed garlic crust pizzas."
        },
        "mandarin-kitchen": {
            image: "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=1200&auto=format&fit=crop&q=80",
            desc: "Contemporary Pan-Asian bistro on MM Alam Road serving spicy Szechuan beef, crispy prawn tempura, and aromatic Pad Thai."
        },
        "baituti-lebanese-restaurant": {
            image: "https://images.unsplash.com/photo-1541518763669-27fef04b14ea?w=1200&auto=format&fit=crop&q=80",
            desc: "Authentic Mediterranean & Lebanese eatery in Model Town serving smooth hummus tahini, shish tawook skewers, and fresh pita."
        }
    },

    getRestaurantImage(restaurant) {
        if (!restaurant) return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&auto=format&fit=crop&q=80";
        if (restaurant.cover_image_url) return restaurant.cover_image_url;
        
        const slug = (restaurant.slug || "").toLowerCase();
        if (CONFIG.RESTAURANT_MEDIA[slug]) {
            return CONFIG.RESTAURANT_MEDIA[slug].image;
        }

        const name = (restaurant.name || "").toLowerCase();
        for (const [key, val] of Object.entries(CONFIG.RESTAURANT_MEDIA)) {
            if (name.includes(key.replace(/-/g, ' ')) || key.includes(name.replace(/\s+/g, '-'))) {
                return val.image;
            }
        }

        // Cuisine-based fallbacks
        const cuisines = restaurant.cuisines || [];
        const cuisinesStr = cuisines.join(' ').toLowerCase();
        if (cuisinesStr.includes('pizza')) return "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&auto=format&fit=crop&q=80";
        if (cuisinesStr.includes('burger')) return "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&auto=format&fit=crop&q=80";
        if (cuisinesStr.includes('bbq')) return "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&auto=format&fit=crop&q=80";
        if (cuisinesStr.includes('italian')) return "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop&q=80";
        if (cuisinesStr.includes('chinese')) return "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=800&auto=format&fit=crop&q=80";
        if (cuisinesStr.includes('cafe')) return "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&auto=format&fit=crop&q=80";

        return "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&auto=format&fit=crop&q=80";
    },

    getRestaurantDescription(restaurant) {
        if (restaurant?.description && restaurant.description.length > 15) return restaurant.description;
        const slug = (restaurant?.slug || "").toLowerCase();
        if (CONFIG.RESTAURANT_MEDIA[slug]) {
            return CONFIG.RESTAURANT_MEDIA[slug].desc;
        }
        return "Authentic dining spot in Lahore with signature taste flavors, fresh ingredients and rich culinary traditions.";
    }
};
