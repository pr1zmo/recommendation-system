I’m pulling the actual Ticketmaster event API docs alongside your current script so the explanation stays specific to what this code does and doesn’t invent unsupported event calls.

Fetched 7 resources

I have the official endpoint and parameter surface now. Next I’m organizing it into the actual event workflow: what your script calls, which other event-adjacent endpoints matter, how classification and genre discovery works, and where the hard limits are.I’m sampling the live API once to verify the payload shape and classification hierarchy your code actually receives, so the explanation can connect the docs to real event JSON.

Ran terminal command:  curl -s "https://app.ticketmaster.com/discovery/v2/events.json?apikey=$TICKETMASTER_KEY&size=1&segmentId=KZFzniwnSyZfZ7v7nJ" | head -c 6000

Ran terminal command:  curl -s "https://app.ticketmaster.com/discovery/v2/classifications.json?apikey=$TICKETMASTER_KEY&size=5" | head -c 6000

**What Your Script Is Using**

Your file api-get.py is using the Ticketmaster Discovery API, specifically the event search endpoint.

The exact endpoint in your code is:

https://app.ticketmaster.com/discovery/v2/events.json

That is defined in api-get.py.

Your script is doing this flow:

[Your script] → picks a random segment from api-get.py → calls Event Search with apikey + segmentId + size + sort → gets a page of event results → reduces each event to a smaller object in api-get.py → writes the final dataset to data.json

There is one important detail in your current script:

api-get.py creates a random country, but api-get.py has countryCode commented out, so the API call is not actually country-filtered right now.

Also, your fallback logic in api-get.py removes segmentId if too few events are returned, which broadens the search.

**High-Level Mental Model**

Think of the Discovery API as a read-only event catalog.

It works like this:

Authentication → Search catalog → Get event ids → Expand details → Optionally expand venues, attractions, images, and classifications

ASCII view:

API Key
  ↓
GET /events.json
  ↓
List of events
  ↓
Each event has:
  → event id
  → classifications
  → venue ids
  → attraction ids
  → dates
  → sales info
  → images
  ↓
Use ids to drill deeper:
  → GET /events/{id}.json
  → GET /events/{id}/images.json
  → GET /venues/{id}.json
  → GET /attractions/{id}.json
  → GET /classifications/{id}
  → GET /classifications/genres/{id}
  → GET /classifications/segments/{id}
  → GET /classifications/subgenres/{id}

That is the core event ecosystem for this API.

**The Important Rule About “All Possible Calls”**

For the public Discovery API event surface, these are read-only GET calls. You are not creating, updating, or deleting events. There is no public event POST, PUT, PATCH, or DELETE flow here.

So when you say all possible calls concerning events, that effectively means:

GET /discovery/v2/events
GET /discovery/v2/events/{id}
GET /discovery/v2/events/{id}/images
GET /discovery/v2/classifications
GET /discovery/v2/classifications/{id}
GET /discovery/v2/classifications/segments/{id}
GET /discovery/v2/classifications/genres/{id}
GET /discovery/v2/classifications/subgenres/{id}
GET /discovery/v2/attractions
GET /discovery/v2/attractions/{id}
GET /discovery/v2/venues
GET /discovery/v2/venues/{id}
GET /discovery/v2/suggest

The first three are direct event endpoints.
The rest are event-supporting endpoints you use to understand, filter, enrich, and normalize events.

**Authentication**

Every request needs an API key passed as the apikey query parameter.

Pattern:

https://app.ticketmaster.com/discovery/v2/events.json?apikey=YOUR_KEY

If the key is invalid, the API returns 401 with an Invalid ApiKey fault.

I tried verifying live payloads from your environment, but the current key in this workspace returned Invalid ApiKey, so I could not live-enumerate your account’s current classification catalog. The explanation below is based on the official API docs and your current code.

**Root URL**

Base root:

https://app.ticketmaster.com/discovery/v2/

You append resource paths like:

events.json
events/{id}.json
classifications.json
venues.json
attractions.json
suggest

**What “Event” Means in This API**

An event is the public listing that users can buy or view on Ticketmaster-style systems.

A typical event record can include:

id
name
url
dates
sales windows
images
classifications
venue data
attractions
price ranges
promoter info
notes and descriptions
seatmap and related links in some cases

Your code only keeps a small subset in api-get.py, specifically:

id
name
url
description
localDate
countryCode
segment
genre
status
imageUrl

So your script is consuming only a thin slice of what the full event object can provide.

**The Classification Hierarchy**

This is the most important concept if you want better data generation.

Ticketmaster classifies events using a hierarchy like this:

Segment → Genre → SubGenre → Type → SubType

Example structure:

Music
  → Rock
    → Alternative Rock
  → Jazz
    → Smooth Jazz

Sports
  → Basketball
    → NBA

Arts & Theatre
  → Theatre
    → Musical

Film
  → Film
    → Documentary

Miscellaneous
  → Fairs & Festivals
    → County Fair

In your script, you only read:

segment.name
genre.name

from api-get.py and api-get.py

That means you are currently ignoring:

subGenre
type
subType
family flag
primary classification markers

If you want richer recommendation or dataset quality, those extra classification fields matter a lot.

**What Genres It Sends**

The API does not really send one small fixed genre list. It sends classification objects attached to events, and the available genres depend on:

country
market
source
segment
venue inventory
partner availability
locale

So the correct way to think about “genres it sends” is:

The API sends whatever genre taxonomy is associated with the matched events, not a single universal hardcoded list embedded in your script.

Your current script hardcodes only five segment ids in api-get.py:

music
sports
arts-theatre
film
misc

Those are segment filters, not the full genre universe.

To discover actual genre values, the right workflow is:

GET /classifications.json
  ↓
read segment, genre, subgenre ids and names
  ↓
use genreId, subGenreId, segmentId, classificationName, or classificationId in event search
  ↓
inspect event classifications returned on actual events

ASCII view:

GET /classifications.json
  ↓
Segments and genres catalog
  ↓
Choose:
  → segmentId
  → genreId
  → subGenreId
  → classificationId
  ↓
GET /events.json with those filters
  ↓
Event results with matching classifications

So if your goal is better data, your first step is not random event pulls. Your first step is taxonomy discovery.

**Direct Event Endpoint 1: Search Events**

Endpoint:

GET /discovery/v2/events.json

Purpose:

Search for events and filter by location, time, classification, source, and sales-related criteria.

This is the endpoint your script uses in api-get.py.

**What Search Events Returns**

Top-level response usually contains:

_links
_embedded.events
page

If there are no matches, you may get no _embedded.events. Your helper in api-get.py safely falls back to an empty list.

**Main Query Parameters for Event Search**

These are the event-search parameters that matter most.

Identity and lookup:
id
keyword
attractionId
venueId
promoterId
collectionId

Location filters:
postalCode
city
stateCode
countryCode
marketId
dmaId
geoPoint
latlong, but deprecated
radius
unit

Time filters:
startDateTime
endDateTime
localStartDateTime
localStartEndDateTime
startEndDateTime
onsaleStartDateTime
onsaleEndDateTime
onsaleOnStartDate
onsaleOnAfterStartDate
publicVisibilityStartDateTime
preSaleDateTime

Classification filters:
classificationName
classificationId
segmentId
segmentName
genreId
subGenreId
typeId
subTypeId
includeFamily

Source and visibility filters:
source
includeTBA
includeTBD
includeTest
domain
locale
preferredCountry
includeSpellcheck

Pagination and sorting:
size
page
sort

**How to Think About Those Parameters**

The best way is by intent:

Location intent:
I want events near somewhere.
Use countryCode, city, stateCode, postalCode, geoPoint, radius, dmaId, or marketId.

Time intent:
I want events in a date range.
Use startDateTime and endDateTime, or localStartDateTime/localStartEndDateTime if you care about local time.

Taxonomy intent:
I want only certain categories.
Use segmentId, genreId, subGenreId, typeId, or classificationName/classificationId.

Source intent:
I only want Ticketmaster or Universe or Frontgate or Resale.
Use source.

Data quality intent:
I want family-friendly only, no test data, maybe include TBA/TBD.
Use includeFamily, includeTest, includeTBA, includeTBD.

Retrieval intent:
I want stable pagination or randomized discovery.
Use size, page, and sort.

**Event Search Parameter Notes That Matter in Practice**

classificationName and classificationId support negative filtering
You can exclude values by prefixing with a minus sign, but the docs warn performance may degrade.

geoPoint is preferred over latlong
latlong is deprecated.

size default is 20
Your script overrides this to 80 in api-get.py.

page starts at 0

sort supports:
name,asc
name,desc
date,asc
date,desc
relevance,asc
relevance,desc
distance,asc
name,date,asc
name,date,desc
date,name,asc
date,name,desc
distance,date,asc
onSaleStartDate,asc
id,asc
venueName,asc
venueName,desc
random

Your script uses random in api-get.py. That is good for variety, bad for reproducibility.

Deep paging is limited
The docs only support roughly the first 1000 results, expressed as size × page < 1000.

**Concrete Event Search Recipes**

All US events:
https://app.ticketmaster.com/discovery/v2/events.json?countryCode=US&apikey=YOUR_KEY

Music events in Los Angeles DMA:
https://app.ticketmaster.com/discovery/v2/events.json?classificationName=music&dmaId=324&apikey=YOUR_KEY

Events for a specific attraction in Canada:
https://app.ticketmaster.com/discovery/v2/events.json?attractionId=SOME_ATTRACTION_ID&countryCode=CA&apikey=YOUR_KEY

Events near a postal code:
https://app.ticketmaster.com/discovery/v2/events.json?postalCode=10001&radius=25&unit=miles&apikey=YOUR_KEY

Events in a date window:
https://app.ticketmaster.com/discovery/v2/events.json?startDateTime=2026-04-01T00:00:00Z&endDateTime=2026-04-30T23:59:59Z&apikey=YOUR_KEY

Sports events from Ticketmaster only:
https://app.ticketmaster.com/discovery/v2/events.json?segmentId=KZFzniwnSyZfZ7v7nE&source=ticketmaster&apikey=YOUR_KEY

**Direct Event Endpoint 2: Get Event Details**

Endpoint:

GET /discovery/v2/events/{id}.json

Purpose:

Get the full details for one event.

This is what you call when search results are not enough and you want a single full canonical object.

Use this when you need:

full venue embedding
full attractions embedding
sales windows
price ranges
detailed notes
richer images
possibly seatmap/external links and related metadata if present

Required path input:
event id

Optional query inputs:
locale
domain

**When To Use Event Details Instead of Search**

Use Event Search to find candidates.
Use Event Details to enrich a chosen event.

ASCII flow:

GET /events.json?filters...
  ↓
Find event ids
  ↓
Choose interesting ids
  ↓
GET /events/{id}.json
  ↓
Store richer event records

This is especially useful if your data pipeline wants summary records first, then enrichment later.

**Direct Event Endpoint 3: Get Event Images**

Endpoint:

GET /discovery/v2/events/{id}/images.json

Purpose:

Fetch only the event image set.

This matters when you want:

a dedicated image refresh job
image ranking or resizing logic
lighter calls than full detail payloads
asset harvesting after event selection

Your helper api-get.py currently chooses the largest 16:9 image from what is already present in the event payload. That is fine for many use cases, but if search responses do not include the image variety you want, this endpoint is the targeted follow-up.

**Supporting Endpoint: Classifications Search**

Endpoint:

GET /discovery/v2/classifications.json

Purpose:

This is the taxonomy catalog. It tells you what segments, genres, and subgenres exist.

If your goal is better generated data, this endpoint is foundational.

Use it to answer:
Which segments exist?
Which genres exist under each segment?
Which subgenres exist under each genre?
Which type and subtype labels are available?
Which classifications are family-friendly?

Important query inputs:
id
keyword
source
locale
includeTest
size
page
sort
preferredCountry
includeSpellcheck
domain

This endpoint is not about event instances. It is about event vocabulary.

**Supporting Endpoint: Get Classification Details**

Endpoint:

GET /discovery/v2/classifications/{id}

Purpose:

Given a classification id, get its structure.

This is useful when an event gives you classification ids and you want to resolve them or inspect family/type metadata.

The docs describe this detail response as including things like:
segment
type
subType
family
primary

**Supporting Endpoint: Get Segment Details**

Endpoint:

GET /discovery/v2/classifications/segments/{id}

Purpose:

Resolve a segment and its linked genre container.

Example use:
You know the segment id for Music and want the genres under Music.

This is how you move from broad category to filterable secondary taxonomy.

**Supporting Endpoint: Get Genre Details**

Endpoint:

GET /discovery/v2/classifications/genres/{id}

Purpose:

Resolve one genre and inspect its linked subgenres.

This is how you get from something like Rock to more granular values underneath it.

This is one of the most useful endpoints if you want a controlled dataset generation strategy rather than random pull-and-hope.

**Supporting Endpoint: Get SubGenre Details**

Endpoint:

GET /discovery/v2/classifications/subgenres/{id}

Purpose:

Resolve one subgenre by id.

Use this when you need the precise lowest-level classification name, usually for normalization or analytics.

**Supporting Endpoint: Attractions Search**

Endpoint:

GET /discovery/v2/attractions.json

Purpose:

Search artists, teams, performers, packages, and similar entities linked to events.

Why this matters for events:
An event often points to one or more attractions.
If you want event generation around known artists, teams, or brands, you first find attractions, then filter events by attractionId.

Useful pattern:

GET /attractions.json?keyword=Adele
  ↓
find attraction id
  ↓
GET /events.json?attractionId=THAT_ID

Useful query inputs:
id
keyword
source
locale
includeTest
size
page
sort
classificationName
classificationId
segmentId
genreId
subGenreId
typeId
subTypeId
includeFamily
preferredCountry
includeSpellcheck
domain

**Supporting Endpoint: Get Attraction Details**

Endpoint:

GET /discovery/v2/attractions/{id}.json

Purpose:

Fetch full details for one attraction.

Why it matters:
Attraction objects often give better artist/team-level metadata than event search alone. If you want a recommendation system that knows the performer identity, attraction enrichment helps.

**Supporting Endpoint: Venue Search**

Endpoint:

GET /discovery/v2/venues.json

Purpose:

Search venues and then use venueId to constrain event search.

Useful flow:

GET /venues.json?keyword=Madison Square Garden
  ↓
find venue id
  ↓
GET /events.json?venueId=THAT_ID

Useful query inputs:
id
keyword
countryCode
stateCode
geoPoint
radius
unit
locale
includeTest
size
page
sort
source
preferredCountry
includeSpellcheck
domain

**Supporting Endpoint: Get Venue Details**

Endpoint:

GET /discovery/v2/venues/{id}.json

Purpose:

Fetch full venue information.

Why it matters:
Venue metadata can help you derive:
city normalization
timezone normalization
country/state consistency
market grouping
ADA flags
upcoming event counts
venue-based recommendation features

**Supporting Endpoint: Suggest**

Endpoint:

GET /discovery/v2/suggest

Purpose:

Typeahead-style suggestions across resources.

This is not a full search endpoint. It is for partial keyword discovery and pre-search assistance.

Why it matters for events:
You can use it to build a search UI or to discover likely attractions, venues, or events from partial user text.

Useful inputs:
keyword
location filters
segmentId
resource
countryCode
includeTBA
includeTBD
includeSpellcheck
source
domain
preferredCountry

Important note:
resource can include attractions, events, venues, products.

So Suggest is useful for discovery, but not the right backbone for dataset generation.

**The Sources Ticketmaster Can Return**

The docs list these supported sources:

ticketmaster
tmr, Ticketmaster resale
universe
frontgate

This matters because your event data can differ significantly by source. If you want a cleaner or more consistent dataset, source filtering is a major lever.

Example:

ticketmaster tends to be the obvious baseline
tmr may include resale inventory behavior
universe and frontgate can change the content mix

**The Countries, Markets, and DMA Layers**

Ticketmaster supports event filtering at multiple geographic levels.

countryCode
ISO alpha-2 country filter, like US, CA, GB, FR

marketId
bigger regional market groupings

dmaId
Designated Market Area, mostly useful in US and some regional modeling contexts

geoPoint plus radius
best when you want actual proximity search

postalCode
good for user-centered local queries

city and stateCode
simple text-based regional filters

Think of them like this:

countryCode → broad national scope
marketId → larger commercial region
dmaId → audience/media region
geoPoint/postalCode → user proximity
venueId → exact venue scope

ASCII decision tree:

Need broad coverage?
  → use countryCode

Need stable regional partitions?
  → use marketId or dmaId

Need nearest events to a user?
  → use geoPoint + radius

Need only one venue?
  → use venueId

**How Your Current Script Works Internally**

In api-get.py, your script builds params with:

apikey
segmentId
size
sort

Then api-get.py calls search.

If there are too few events, api-get.py removes the segment filter and retries.

Then api-get.py reduces events to compact objects.

Then api-get.py shuffles them again.

Then it writes output to data.json.

So the script is currently doing:

broad event search
minimal taxonomy use
minimal geographic precision
minimal temporal precision
minimal enrichment

That is fine for getting any data quickly, but not ideal for producing high-quality recommendation data.

**What You Are Missing If You Want Better Data**

Your current approach leaves value on the table in five areas.

Classification depth:
You only keep segment and genre, not subGenre, type, subType, family, or primary markers.

Temporal control:
You are not partitioning by date windows, so data freshness and seasonality are uncontrolled.

Geographic control:
countryCode is currently commented out, so the geographic distribution is effectively broad and inconsistent.

Source control:
You are not filtering by source, so you may mix different provider ecosystems.

Enrichment:
You are not following up with event detail, venue detail, or attraction detail calls.

**Best-Practice Event Data Pipeline**

If the goal is recommendation quality rather than just random records, the better pipeline is:

Step 1 → pull classifications
Step 2 → choose target segments, genres, and subgenres intentionally
Step 3 → search events in controlled country and date windows
Step 4 → paginate deterministically
Step 5 → enrich chosen events with event details
Step 6 → enrich venue and attraction records
Step 7 → normalize and deduplicate by event id

ASCII pipeline:

GET /classifications.json
  ↓
Build taxonomy map
  ↓
For each country
  ↓
For each segment or genre
  ↓
For each date window
  ↓
GET /events.json?page=0..N
  ↓
Deduplicate by event id
  ↓
GET /events/{id}.json for high-value records
  ↓
GET /venues/{id}.json and /attractions/{id}.json
  ↓
Store normalized dataset

That is how you generate much better data.

**Recommended Query Strategies**

If you want diverse data:
Use countryCode + segmentId + date window + page traversal

If you want focused music data:
Use genreId or subGenreId, not just segmentId

If you want nearby events for users:
Use geoPoint + radius instead of country-level pulls

If you want stable training data:
Avoid sort=random and use date,asc or relevance,desc

If you want better event labels:
Enrich with attraction and venue detail endpoints

If you want taxonomy completeness:
Start with classifications, not events

**The Important Event Search Recipes You’ll Actually Use**

Catalog sweep by segment:
GET /events.json?countryCode=US&segmentId=SOME_SEGMENT_ID&size=200&page=0&sort=date,asc

Genre-focused harvest:
GET /events.json?countryCode=US&genreId=SOME_GENRE_ID&startDateTime=...&endDateTime=...

Venue-specific harvest:
GET /events.json?venueId=SOME_VENUE_ID&apikey=...

Artist/team-specific harvest:
GET /events.json?attractionId=SOME_ATTRACTION_ID&apikey=...

Family-only harvest:
GET /events.json?includeFamily=only&countryCode=US&apikey=...

Source-specific harvest:
GET /events.json?source=ticketmaster&countryCode=GB&apikey=...

Nearby user search:
GET /events.json?geoPoint=SOME_GEOHASH&radius=25&unit=miles&apikey=...

Debug taxonomy by text:
GET /events.json?classificationName=music&apikey=...

**What The Response Usually Looks Like**

At search level:

_links
_embedded.events
page

At event level, common useful fields are:

id
name
type
url
locale
images
dates
sales
classifications
info
pleaseNote
priceRanges
promoter or promoters
_embedded.venues
_embedded.attractions
externalLinks
test

Your compact mapper in api-get.py extracts only a subset of that.

**Errors and Limits You Need To Respect**

Authentication errors:
Invalid key returns 401

Rate limit:
Docs say default quota is around 5000 calls per day and 5 requests per second

Deep paging:
You cannot reliably go arbitrarily deep; the docs cap deep paging around the first 1000 items

Empty matches:
You may get no _embedded.events, which should be treated as an empty result set

Deprecated location mode:
latlong exists but geoPoint is preferred

**A Useful Diagram of the Whole Event Surface**

Event taxonomy side:

Classifications
  ↓
Segment
  ↓
Genre
  ↓
SubGenre
  ↓
Type
  ↓
SubType
  ↓
Used as filters in Event Search

Entity enrichment side:

Event Search
  ↓
Event ids
  ↓
Event Details
  ↙           ↓           ↘
Venue ids   Images       Attraction ids
  ↓                         ↓
Venue Detail             Attraction Detail

Search-assist side:

User types query
  ↓
Suggest
  ↓
Possible event, venue, or attraction choices
  ↓
Use chosen id in Event Search or Detail call

**If You Want To Understand The Script Against The API**

Here is the exact mapping from your file to API behavior:

api-get.py sets the event search endpoint only.
api-get.py hardcodes only five segment ids.
api-get.py picks one best image from the event payload.
api-get.py maps only a limited set of event fields.
api-get.py performs a basic GET with params.
api-get.py builds a broad random query.
api-get.py does not currently use countryCode.
api-get.py falls back to all segments if the chosen one is sparse.
api-get.py writes the compact payload to data.json.

So today, your code is using only one slice of the API: broad search events.

**What I Would Tell You To Use For Better Data**

If your real goal is recommendation quality, use this order of operations:

1. Pull the classification catalog first and persist it.
2. Build a taxonomy map of segment → genre → subgenre.
3. Search events by country plus date windows plus genre ids.
4. Stop using pure random as the primary retrieval strategy.
5. Enrich selected events with details, venues, and attractions.
6. Keep more fields than your current compact mapper stores.

**Bottom Line**

The Ticketmaster Discovery API event surface is a read-only search-and-enrichment API.

The direct event calls are:
GET /events
GET /events/{id}
GET /events/{id}/images

The supporting calls you need for serious event data work are:
GET /classifications
GET /classifications/{id}
GET /classifications/segments/{id}
GET /classifications/genres/{id}
GET /classifications/subgenres/{id}
GET /attractions
GET /attractions/{id}
GET /venues
GET /venues/{id}
GET /suggest

Your current script uses only Event Search, and even there it uses a very small subset of the available filtering and classification power. The biggest improvement opportunity is to move from random segment pulls to classification-driven, date-windowed, location-controlled harvesting.

If you want, I can do one of these next:

1. Add a new script that dumps the full Ticketmaster classification tree into JSON for you.
2. Rewrite api-get.py into a better event harvester with country, date, genre, pagination, and enrichment support.
3. Design a dataset schema for recommendations so you know exactly which event, venue, attraction, and classification fields to keep.