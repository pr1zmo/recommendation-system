import json
import random
import os
from datetime import date, timedelta

types = {
	"1": "Conference",
	"2": "Seminar or Talk",
	"3": "Tradeshow, Consumer Show, or Expo",
	"4": "Convention",
	"5": "Festival or Fair",
	"6": "Concert or Performance",
	"7": "Screening",
	"8": "Dinner or Gala",
	"9": "Class, Training, or Workshop",
	"10": "Meeting or Networking Event",
	"11": "Party or Social Gathering",
	"12": "Rally",
	"13": "Tournament",
	"14": "Game or Competition",
	"15": "Race or Endurance Event",
	"16": "Tour",
	"17": "Attraction",
	"18": "Camp, Trip, or Retreat",
	"19": "Appearance or Signing",
	"100": "Other",
}

category = {
	"103": "Music",
	"101": "Business & Professional",
	"110": "Food & Drink",
	"113": "Community & Culture",
	"105": "Performing & Visual Arts",
	"104": "Film, Media & Entertainment",
	"108": "Sports & Fitness",
	"107": "Health & Wellness",
	"102": "Science & Technology",
	"109": "Travel & Outdoor",
	"111": "Charity & Causes",
	"114": "Religion & Spirituality",
	"115": "Family & Education",
	"116": "Seasonal & Holiday",
	"112": "Government & Politics",
	"106": "Fashion & Beauty",
	"117": "Home & Lifestyle",
	"118": "Auto, Boat & Air",
	"119": "Hobbies & Special Interest",
	"199": "Other",
	"120": "School Activities",
}

sub_category = {
	"Music": [
		"Pop",
		"Rock & Roll",
		"Hip-Hop",
		"Jazz",
		"Blues",
		"Classical",
		"Electronic",
		"Indie",
		"Metal",
		"R&B",
		"Reggae",
		"Country",
	],
	"Business & Professional": [
		"Startup Pitch",
		"Leadership",
		"Sales",
		"Marketing",
		"Entrepreneurship",
		"Project Management",
		"Networking",
		"Career Development",
		"Finance",
		"Real Estate",
	],
	"Food & Drink": [
		"Wine Tasting",
		"Craft Beer",
		"Coffee Culture",
		"Street Food",
		"Fine Dining",
		"Cooking Class",
		"Baking",
		"Vegan Cuisine",
		"BBQ",
		"World Cuisine",
	],
	"Community & Culture": [
		"Local Heritage",
		"Cultural Exchange",
		"Volunteer Meetup",
		"Language Exchange",
		"Neighborhood Gathering",
		"Public Forum",
		"Community Art",
		"Social Impact",
	],
	"Performing & Visual Arts": [
		"Theater",
		"Dance",
		"Opera",
		"Stand-up Comedy",
		"Photography",
		"Painting",
		"Sculpture",
		"Digital Art",
		"Street Art",
	],
	"Film, Media & Entertainment": [
		"Independent Film",
		"Documentary",
		"Short Films",
		"Animation",
		"Podcast Live",
		"Creator Meetup",
		"Content Production",
		"Fan Convention",
	],
	"Sports & Fitness": [
		"Football",
		"Basketball",
		"Running",
		"Cycling",
		"Yoga",
		"CrossFit",
		"Martial Arts",
		"Swimming",
		"Tennis",
		"Esports Fitness",
	],
	"Health & Wellness": [
		"Mental Health",
		"Meditation",
		"Breathwork",
		"Nutrition",
		"Holistic Healing",
		"Sleep Optimization",
		"Stress Management",
		"Self-care",
		"Mindfulness",
	],
	"Science & Technology": [
		"AI & Machine Learning",
		"Web Development",
		"Cybersecurity",
		"Data Science",
		"Robotics",
		"Cloud Computing",
		"Open Source",
		"Blockchain",
		"Biotech",
		"Space Tech",
	],
	"Travel & Outdoor": [
		"Hiking",
		"Backpacking",
		"Camping",
		"Road Trips",
		"Adventure Travel",
		"Wildlife Tours",
		"Nature Photography",
		"Urban Exploration",
	],
	"Charity & Causes": [
		"Fundraiser",
		"Environmental Action",
		"Animal Welfare",
		"Education Access",
		"Health Campaign",
		"Human Rights",
		"Disaster Relief",
		"Community Service",
	],
	"Religion & Spirituality": [
		"Interfaith Dialogue",
		"Prayer Gathering",
		"Scripture Study",
		"Spiritual Retreat",
		"Gospel Night",
		"Meditative Worship",
		"Faith & Society",
	],
	"Family & Education": [
		"Parenting",
		"Early Learning",
		"STEM for Kids",
		"Teen Development",
		"Homeschooling",
		"College Prep",
		"Scholarship Workshops",
		"Lifelong Learning",
	],
	"Seasonal & Holiday": [
		"Christmas",
		"New Year",
		"Halloween",
		"Easter",
		"Valentine's Day",
		"Summer Festival",
		"Winter Market",
		"Spring Fair",
	],
	"Government & Politics": [
		"Town Hall",
		"Policy Discussion",
		"Election Debate",
		"Civic Education",
		"Public Administration",
		"Advocacy",
		"Constitutional Rights",
	],
	"Fashion & Beauty": [
		"Streetwear",
		"Haute Couture",
		"Makeup Artistry",
		"Skincare",
		"Hair Styling",
		"Sustainable Fashion",
		"Personal Styling",
		"Fragrance",
	],
	"Home & Lifestyle": [
		"Interior Design",
		"Minimalism",
		"DIY Decor",
		"Smart Home",
		"Gardening",
		"Home Organization",
		"Pet-friendly Living",
		"Wellness at Home",
	],
	"Auto, Boat & Air": [
		"Car Meet",
		"Motorcycles",
		"Classic Cars",
		"Boat Show",
		"Sailing",
		"Aviation Expo",
		"Drone Showcase",
		"EV Technology",
	],
	"Hobbies & Special Interest": [
		"Board Games",
		"Tabletop RPG",
		"Collectibles",
		"Comics",
		"Photography Club",
		"Model Building",
		"DIY Electronics",
		"Writing Circle",
	],
	"Other": [
		"Miscellaneous Meetup",
		"General Interest",
		"Pop-up Experience",
		"Experimental Format",
	],
	"School Activities": [
		"Debate Club",
		"Science Fair",
		"Art Showcase",
		"Sports Day",
		"Music Recital",
		"Coding Club",
		"Student Council",
		"Academic Competition",
	],
}


string = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789----____"
cc = [
	"US", "AD", "AI", "AR", "AU", "AT", "AZ", "BS", "BH", "BB", "BE", "BM",
	"BR", "BG", "CA", "CL", "CN", "CO", "CR", "HR", "CY", "CZ", "DK", "DO",
	"EC", "EE", "FO", "FI", "FR", "GE", "DE", "GH", "GI", "GB", "GR", "HK",
	"HU", "IS", "IN", "IE", "IL", "IT", "JM", "JP", "KR", "LV", "LB", "LT",
	"LU", "MA", "MY", "MT", "MX", "MC", "ME", "MA", "NL", "AN", "NZ", "ND",
	"NO", "PE", "PL", "PT", "RO", "RU", "LC", "SA", "RS", "SG", "SK", "SI",
	"ZA", "ES", "SE", "CH", "TW", "TH", "TT", "TR", "UA", "AE", "UY", "VE",
]

placeholder_images = [
	"https://picsum.photos/seed/event-1/1200/675",
	"https://picsum.photos/seed/event-2/1200/675",
	"https://picsum.photos/seed/event-3/1200/675",
	"https://picsum.photos/seed/event-4/1200/675",
	"https://picsum.photos/seed/event-5/1200/675",
	"https://picsum.photos/seed/event-6/1200/675",
	"https://picsum.photos/seed/event-7/1200/675",
	"https://picsum.photos/seed/event-8/1200/675",
]


def random_local_date(start_year=2026, end_year=2028):
	start_date = date(start_year, 1, 1)
	end_date = date(end_year, 12, 31)
	day_offset = random.randint(0, (end_date - start_date).days)
	return (start_date + timedelta(days=day_offset)).isoformat()
'''
{
	"id": "11uYvxxZjUudvu",
	"name": "Bluey's Big Play",
	"url": "https://www.ticketmaster.co.uk/blueys-big-play-liverpool-04-07-2026/event/370062880736343C",
	"description": "All ages welcome. Under 16s to be accompanied by an adult 18+. Free for 18 months and under. A max of 9 tickets per person and per household applies. Tickets in excess of 9 will be cancelled.",
	"localDate": "2026-07-04",
	"countryCode": "GB",
	"segment": "Arts & Theatre",
	"genre": "Children's Theatre",
	"status": "onsale",
	"imageUrl": "https://s1.ticketm.net/dam/a/6e0/1b4c5954-6cfb-4e4a-bc0f-09abea7296e0_SOURCE"
}
'''
def generate_events() -> list:
	r = random.sample(string, 14)
	_id = "".join(r)
	name = "placeholder event"
	url = "https://www.broken.com"
	description = "placeholder description"
	localdate = random_local_date()
	country_code = random.choice(cc)
	segment = random.choice(list(category.values()))
	genre = random.choice(sub_category[segment])
	status = random.choice(list(types.values()))
	image_url = random.choice(placeholder_images)
	payload = {
		"id": _id,
		"name": name,
		"url": url,
		"description": description,
		"localDate": localdate,
		"countryCode": country_code,
		"segment": segment,
		"genre": genre,
		"status": status,
		"imageUrl": image_url,
	}
	with open("generator/data.json", "a+") as f:
		json.dump(payload, f, indent=2)
		f.write(",\n")
	event = []

	return event

for _ in range(100):
	generate_events()