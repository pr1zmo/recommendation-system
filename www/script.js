function createElement(tagName, className, textContent) {
	const element = document.createElement(tagName);

	if (className) {
		element.className = className;
	}

	if (textContent) {
		element.textContent = textContent;
	}

	return element;
}

const API = {
	bootstrap: "/api/bootstrap",
	login: "/api/login",
	logout: "/api/logout",
	preferences: "/api/user/preferences",
	recommendations: "/api/recommendations",
	eventAction(eventId) {
		return `/api/events/${encodeURIComponent(eventId)}/action`;
	}
};

const EVENT_CATEGORIES = [
	"Pop", "Rock & Roll", "Hip-Hop", "Jazz", "Blues", "Classical", "Electronic", "Indie", "Metal", "R&B", "Reggae", "Country",
	"Startup Pitch", "Leadership", "Sales", "Marketing", "Entrepreneurship", "Project Management", "Networking", "Career Development", "Finance", "Real Estate",
	"Wine Tasting", "Craft Beer", "Coffee Culture", "Street Food", "Fine Dining", "Cooking Class", "Baking", "Vegan Cuisine", "BBQ", "World Cuisine",
	"Local Heritage", "Cultural Exchange", "Volunteer Meetup", "Language Exchange", "Neighborhood Gathering", "Public Forum", "Community Art", "Social Impact",
	"Theater", "Dance", "Opera", "Stand-up Comedy", "Photography", "Painting", "Sculpture", "Digital Art", "Street Art",
	"Independent Film", "Documentary", "Short Films", "Animation", "Podcast Live", "Creator Meetup", "Content Production", "Fan Convention",
	"Football", "Basketball", "Running", "Cycling", "Yoga", "CrossFit", "Martial Arts", "Swimming", "Tennis", "Esports Fitness",
	"Mental Health", "Meditation", "Breathwork", "Nutrition", "Holistic Healing", "Sleep Optimization", "Stress Management", "Self-care", "Mindfulness",
	"AI & Machine Learning", "Web Development", "Cybersecurity", "Data Science", "Robotics", "Cloud Computing", "Open Source", "Blockchain", "Biotech", "Space Tech",
	"Hiking", "Backpacking", "Camping", "Road Trips", "Adventure Travel", "Wildlife Tours", "Nature Photography", "Urban Exploration",
	"Fundraiser", "Environmental Action", "Animal Welfare", "Education Access", "Health Campaign", "Human Rights", "Disaster Relief", "Community Service",
	"Interfaith Dialogue", "Prayer Gathering", "Scripture Study", "Spiritual Retreat", "Gospel Night", "Meditative Worship", "Faith & Society",
	"Parenting", "Early Learning", "STEM for Kids", "Teen Development", "Homeschooling", "College Prep", "Scholarship Workshops", "Lifelong Learning",
	"Christmas", "New Year", "Halloween", "Easter", "Valentine's Day", "Summer Festival", "Winter Market", "Spring Fair",
	"Town Hall", "Policy Discussion", "Election Debate", "Civic Education", "Public Administration", "Advocacy", "Constitutional Rights",
	"Streetwear", "Haute Couture", "Makeup Artistry", "Skincare", "Hair Styling", "Sustainable Fashion", "Personal Styling", "Fragrance",
	"Interior Design", "Minimalism", "DIY Decor", "Smart Home", "Gardening", "Home Organization", "Pet-friendly Living", "Wellness at Home",
	"Car Meet", "Motorcycles", "Classic Cars", "Boat Show", "Sailing", "Aviation Expo", "Drone Showcase", "EV Technology",
	"Board Games", "Tabletop RPG", "Collectibles", "Comics", "Photography Club", "Model Building", "DIY Electronics", "Writing Circle",
	"Miscellaneous Meetup", "General Interest", "Pop-up Experience", "Experimental Format",
	"Debate Club", "Science Fair", "Art Showcase", "Sports Day", "Music Recital", "Coding Club", "Student Council", "Academic Competition"
];

const placeholderEvent = Object.freeze({
	id: "placeholder",
	title: "Loading event",
	description: "Preparing your event feed.",
	imageUrl: null,
	tags: ["#loading"],
	url: null
});

const appState = {
	events: [],
	user: null,
	activeView: "all"
};

let views = {
	all: {
		tabId: "tab-all",
		label: "All available events",
		caption: "Loading events...",
		items: Array.from({ length: 6 }, () => placeholderEvent)
	},
	forYou: {
		tabId: "tab-for-you",
		label: "Recommended for you",
		caption: "Loading recommendations...",
		items: Array.from({ length: 4 }, () => placeholderEvent)
	}
};

const panel = document.querySelector("#event-panel");
const panelLabel = document.querySelector("#panel-label");
const panelCaption = document.querySelector("#panel-caption");
const tabSwitcher = document.querySelector(".tab-switcher");
const tabButtons = Array.from(document.querySelectorAll(".tab-button"));
const pageShell = document.querySelector(".page-shell");
const navUserButton = document.querySelector("#nav-user-button");

// Modals
const loginModal = document.querySelector("#login-modal");
const profileModal = document.querySelector("#profile-modal");
const preferencesModal = document.querySelector("#preferences-modal");
const modalOverlays = [loginModal, profileModal, preferencesModal];
const dialogCloses = document.querySelectorAll(".dialog-close");

// Logins & auth
const loginForm = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username-input");
const passwordInput = document.querySelector("#password-input");
const userSummaryName = document.querySelector("#user-summary-name");
const userSummaryMeta = document.querySelector("#user-summary-meta");
const userNextRecommendation = document.querySelector("#user-next-recommendation");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");

// Preferences
const preferencesForm = document.querySelector("#preferences-form");
const preferencesList = document.querySelector("#preferences-list");
const skipPreferencesBtn = document.querySelector("#skip-preferences");

let panelAnimation;
let activeReadMoreButton = null;
let currentEventViewDuration = {
	eventId: null,
	openTime: null
};

const detailOverlay = createElement("div", "event-overlay");
detailOverlay.setAttribute("hidden", "");
detailOverlay.setAttribute("aria-hidden", "true");

const detailDialog = createElement("section", "event-dialog");
detailDialog.setAttribute("role", "dialog");
detailDialog.setAttribute("aria-modal", "true");
detailDialog.setAttribute("aria-labelledby", "event-dialog-title");

const detailClose = createElement("button", "dialog-close", "Close");
detailClose.type = "button";

const detailHero = createElement("div", "dialog-hero");
const detailBody = createElement("div", "dialog-body");
const detailTitle = createElement("h3", "dialog-title");
detailTitle.id = "event-dialog-title";
const detailDescription = createElement("p", "dialog-description");
const detailTags = createElement("div", "dialog-tags");
const detailActions = createElement("div", "dialog-actions");

detailBody.append(detailTitle, detailDescription, detailTags, detailActions);
detailDialog.append(detailClose, detailHero, detailBody);
detailOverlay.append(detailDialog);
pageShell.append(detailOverlay);

function getCsrfToken() {
	const cookie = document.cookie
		.split(";")
		.map((value) => value.trim())
		.find((value) => value.startsWith("csrftoken="));

	return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

async function requestJson(url, options = {}) {
	const response = await fetch(url, {
		headers: {
			"Content-Type": "application/json",
			"X-CSRFToken": getCsrfToken(),
			...(options.headers || {})
		},
		credentials: "same-origin",
		...options
	});

	const isJson = response.headers.get("content-type")?.includes("application/json");
	const payload = isJson ? await response.json() : null;

	if (!response.ok) {
		throw new Error(payload?.error || `Request failed with status ${response.status}`);
	}

	return payload;
}

function normalizeEvent(rawEvent) {
	const images = Array.isArray(rawEvent.images) ? rawEvent.images : [];
	const heroImage = images.find((image) => image.ratio === "16_9") || images[0];
	const classifications = Array.isArray(rawEvent.classifications) ? rawEvent.classifications : [];
	const primaryClassification = classifications[0] || {};
	const segment = rawEvent.segment || primaryClassification.segment?.name || null;
	const genre = rawEvent.genre || primaryClassification.genre?.name || null;
	const status = rawEvent.status || rawEvent.dates?.status?.code || null;
	const localDate = rawEvent.localDate || rawEvent.dates?.start?.localDate || null;
	const description = rawEvent.description || rawEvent.info || rawEvent.pleaseNote || "No description available.";
	const imageUrl = rawEvent.imageUrl || heroImage?.url || null;

	const tags = [segment, genre, status, localDate]
		.filter(Boolean)
		.slice(0, 4)
		.map((value) => `#${String(value).replace(/\s+/g, "-").toLowerCase()}`);

	return {
		id: String(rawEvent.id || rawEvent.url || rawEvent.name),
		title: rawEvent.name || rawEvent.title || "Untitled event",
		description,
		imageUrl,
		tags: tags.length > 0 ? tags : ["#event"],
		url: rawEvent.url || null,
		segment,
		genre,
		status,
		localDate
	};
}

function shuffleArray(items) {
	const arr = [...items];
	for (let i = arr.length - 1; i > 0; i -= 1) {
		const j = Math.floor(Math.random() * (i + 1));
		[arr[i], arr[j]] = [arr[j], arr[i]];
	}
	return arr;
}

function eventMap() {
	return new Map(appState.events.map((eventData) => [eventData.id, eventData]));
}

function buildViews() {
	const randomized = shuffleArray(appState.events);
	const allItems = randomized.slice(0, Math.min(24, randomized.length));

	return {
		all: {
			tabId: "tab-all",
			label: "All available events",
			caption: `${allItems.length} events ready to browse.`,
			items: allItems
		},
		forYou: {
			tabId: "tab-for-you",
			label: "Recommended for you",
			caption: "Loading recommendations...",
			items: Array.from({ length: 4 }, () => placeholderEvent)
		}
	};
}

function userHistorySet(key) {
	const historyItem = appState.user?.history?.[key];
	if (!historyItem) return new Set();

	if (Array.isArray(historyItem)) {
		return new Set(historyItem);
	}
	// For viewedEventIds which is now a dictionary
	if (typeof historyItem === 'object') {
		return new Set(Object.keys(historyItem));
	}
	return new Set();
}

function isActionActive(eventId, key) {
	return userHistorySet(key).has(eventId);
}

function createMediaNode(eventData, imageClass) {
	let media;
	if (eventData.imageUrl) {
		media = createElement("img", imageClass);
		media.src = eventData.imageUrl;
		media.alt = eventData.title;
		media.loading = "lazy";
		media.decoding = "async";
		media.referrerPolicy = "no-referrer";
		media.addEventListener("error", () => {
			const fallback = createElement("div", "image-placeholder", "No image");
			media.replaceWith(fallback);
		});
	} else {
		media = createElement("div", "image-placeholder", "No image");
	}
	return media;
}

function setActiveTab(viewKey) {
	tabButtons.forEach((button) => {
		const isActive = button.dataset.view === viewKey;
		button.classList.toggle("is-active", isActive);
		button.setAttribute("aria-selected", String(isActive));
		button.tabIndex = isActive ? 0 : -1;
	});
}

function animatePanel() {
	if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
		return;
	}

	if (panelAnimation) {
		panelAnimation.cancel();
	}

	panelAnimation = panel.animate(
		[
			{ opacity: 0, transform: "translateY(16px)" },
			{ opacity: 1, transform: "translateY(0)" }
		],
		{
			duration: 220,
			easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
			fill: "both"
		}
	);
}

function openModal(modalEl) {
	modalOverlays.forEach((m) => {
		m.setAttribute("hidden", "");
		m.setAttribute("aria-hidden", "true");
	});
	if (modalEl) {
		modalEl.removeAttribute("hidden");
		modalEl.setAttribute("aria-hidden", "false");
		document.body.classList.add("dialog-open");
	}
}

function closeAllModals() {
	modalOverlays.forEach((m) => {
		m.setAttribute("hidden", "");
		m.setAttribute("aria-hidden", "true");
	});
	document.body.classList.remove("dialog-open");
}

function renderPreferencesModal() {
	const allPreferences = [...EVENT_CATEGORIES];

	const fragment = document.createDocumentFragment();

	allPreferences.forEach((pref) => {
		const label = createElement("label");
		const checkbox = createElement("input");
		checkbox.type = "checkbox";
		checkbox.name = "segment";
		checkbox.value = pref;

		const span = createElement("span", "", pref);
		label.append(checkbox, span);
		fragment.append(label);
	});

	preferencesList.replaceChildren(fragment);
}

function checkPreferencesFlow() {
	const user = appState.user;
	if (user && (!user.preferences || !user.preferences.segments || user.preferences.segments.length === 0)) {
		renderPreferencesModal();
		openModal(preferencesModal);
	}
}

function updateAuthUI() {
	const user = appState.user;
	if (!user) {
		loginForm.hidden = false;
		authMessage.textContent = "Log in to like, dislike, mark events attended, and track user-specific recommendations.";
		navUserButton.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
		return;
	}

	loginForm.hidden = true;
	userSummaryName.textContent = `${user.name} (@${user.username})`;
	userSummaryMeta.textContent = `${user.city || "Unknown city"}, ${user.countryCode || "Unknown country"} · ${user.history.likedEventIds.length} liked · ${user.history.attendedEventIds.length} attended`;

	const nextEvent = eventMap().get(String(user.nextRecommendation));
	userNextRecommendation.textContent = nextEvent
		? `Next recommendation: ${nextEvent.title}`
		: "Next recommendation: not set yet";
	authMessage.textContent = "You are signed in. Event actions now save directly to users.json.";

	// Switch to a filled profile icon or active state when logged in
	navUserButton.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
}

function createSkeletonCard() {
	const card = createElement("article", "skeleton-card");
	const img = createElement("div", "skeleton-shimmer skeleton-image");
	const body = createElement("div", "skeleton-body");
	body.append(
		createElement("div", "skeleton-shimmer skeleton-title"),
		createElement("div", "skeleton-shimmer skeleton-text"),
		createElement("div", "skeleton-shimmer skeleton-text-short")
	);
	const tags = createElement("div", "skeleton-tags");
	tags.append(
		createElement("div", "skeleton-shimmer skeleton-tag"),
		createElement("div", "skeleton-shimmer skeleton-tag")
	);
	card.append(img, body, tags);
	return card;
}

function renderSkeletons(count = 6) {
	const fragment = document.createDocumentFragment();
	for (let i = 0; i < count; i++) {
		fragment.append(createSkeletonCard());
	}
	panel.replaceChildren(fragment);
}

function renderLoginNudge() {
	const nudge = createElement("div", "login-nudge");
	nudge.append(
		createElement("p", "", "Log in to see personalized recommendations."),
		(() => {
			const btn = createElement("button", "primary-button", "Log In");
			btn.type = "button";
			btn.addEventListener("click", () => openModal(loginModal));
			return btn;
		})()
	);
	panel.replaceChildren(nudge);
}

async function loadRecommendations() {
	panelLabel.textContent = "Recommended for you";
	panelCaption.textContent = "Finding events you'll love...";
	setActiveTab("forYou");
	panel.setAttribute("aria-labelledby", "tab-for-you");
	appState.activeView = "forYou";

	if (!appState.user) {
		renderLoginNudge();
		panelCaption.textContent = "Sign in for personalized picks.";
		animatePanel();
		return;
	}

	renderSkeletons(6);
	animatePanel();

	try {
		// Show skeletons for at least 800ms so the shimmer effect is visible
		const [payload] = await Promise.all([
			requestJson(API.recommendations, { method: "GET", headers: {} }),
			new Promise((r) => setTimeout(r, 800))
		]);
		appState.user = payload.user;

		const events = (payload.events || []).map(normalizeEvent);
		const fragment = document.createDocumentFragment();
		events.forEach((eventData) => fragment.append(createCard(eventData)));

		panelCaption.textContent = `${events.length} events recommended for you.`;
		panel.replaceChildren(fragment);
		animatePanel();
		updateAuthUI();
	} catch (error) {
		console.error(error);
		panelCaption.textContent = "Could not load recommendations.";
		panel.replaceChildren(createElement("p", "auth-message", error.message));
	}
}

function renderView(viewKey) {
	if (viewKey === "forYou") {
		loadRecommendations();
		return;
	}

	views = buildViews();
	const view = views[viewKey];
	const fragment = document.createDocumentFragment();

	view.items.forEach((eventData) => {
		fragment.append(createCard(eventData));
	});

	panelLabel.textContent = view.label;
	panelCaption.textContent = view.caption;
	panel.setAttribute("aria-labelledby", view.tabId);
	panel.replaceChildren(fragment);
	setActiveTab(viewKey);
	animatePanel();
	appState.activeView = viewKey;
	updateAuthUI();
}

function closeEventDialog() {
	if (detailOverlay.hasAttribute("hidden")) {
		return;
	}

	if (appState.user && currentEventViewDuration.eventId && currentEventViewDuration.openTime) {
		const duration = Date.now() - currentEventViewDuration.openTime;
		sendEventAction(currentEventViewDuration.eventId, "view", duration).catch((error) => {
			console.error(error);
		});
	}

	currentEventViewDuration.eventId = null;
	currentEventViewDuration.openTime = null;

	detailOverlay.setAttribute("hidden", "");
	detailOverlay.setAttribute("aria-hidden", "true");
	document.body.classList.remove("dialog-open");

	if (activeReadMoreButton) {
		activeReadMoreButton.focus();
	}
}

async function sendEventAction(eventId, action, duration = 0) {
	const payload = await requestJson(API.eventAction(eventId), {
		method: "POST",
		body: JSON.stringify({ action, duration })
	});
	appState.user = payload.user;
	updateAuthUI();
	updateActionButtonStates();
	return payload.user;
}

function getActionPresentation(eventId, action) {
	if (action === "like") {
		const active = isActionActive(eventId, "likedEventIds");
		return {
			label: active ? "Liked" : "Like",
			active,
			disabled: !appState.user,
			extraClass: "is-like"
		};
	}

	if (action === "dislike") {
		const active = isActionActive(eventId, "dislikedEventIds");
		return {
			label: active ? "Disliked" : "Dislike",
			active,
			disabled: !appState.user,
			extraClass: "is-dislike"
		};
	}

	const active = isActionActive(eventId, "attendedEventIds");
	return {
		label: active ? "Attended" : "Attend",
		active,
		disabled: !appState.user || active,
		extraClass: "is-attend"
	};
}

function updateActionButtonStates() {
	document.querySelectorAll(".action-button[data-event-id][data-action]").forEach((button) => {
		const eventId = button.dataset.eventId;
		const action = button.dataset.action;
		const presentation = getActionPresentation(eventId, action);

		button.textContent = presentation.label;
		button.disabled = presentation.disabled;
		button.classList.toggle("is-active", presentation.active);
	});
}

function buildActionButtons(eventData) {
	const actions = createElement("div", "card-actions");
	const actionConfigs = ["like", "dislike", "attend"].map((action) => ({
		action,
		...getActionPresentation(eventData.id, action)
	}));

	actionConfigs.forEach((config) => {
		const button = createElement("button", `action-button ${config.extraClass}`, config.label);
		button.type = "button";
		button.dataset.eventId = eventData.id;
		button.dataset.action = config.action;
		button.disabled = config.disabled;
		button.classList.toggle("is-active", config.active);
		button.addEventListener("click", async () => {
			try {
				await sendEventAction(eventData.id, config.action);
			} catch (error) {
				authMessage.textContent = error.message;
			}
		});
		actions.append(button);
	});

	return actions;
}

function openEventDialog(eventData, triggerButton) {
	activeReadMoreButton = triggerButton;
	detailHero.replaceChildren(createMediaNode(eventData, "dialog-image"));
	detailTitle.textContent = eventData.title;
	detailDescription.textContent = eventData.description;
	detailTags.replaceChildren();
	detailActions.replaceChildren(buildActionButtons(eventData));

	eventData.tags.forEach((tagText) => {
		detailTags.append(createElement("span", "tag", tagText));
	});

	detailOverlay.removeAttribute("hidden");
	detailOverlay.setAttribute("aria-hidden", "false");
	document.body.classList.add("dialog-open");
	detailClose.focus();

	if (appState.user) {
		currentEventViewDuration.eventId = eventData.id;
		currentEventViewDuration.openTime = Date.now();
	}
}

function createCard(eventData) {
	const card = createElement("article", "event-card");
	const media = createMediaNode(eventData, "event-image");
	const body = createElement("div", "card-body");
	const title = createElement("h3", "card-title", eventData.title);
	const description = createElement("p", "card-description", eventData.description);
	const meta = createElement("p", "card-meta", [eventData.localDate, eventData.segment].filter(Boolean).join(" · "));
	const readMore = createElement("button", "read-more", "Read more...");
	readMore.type = "button";
	readMore.addEventListener("click", () => openEventDialog(eventData, readMore));
	const tags = createElement("div", "tags");

	eventData.tags.forEach((tagText) => {
		tags.append(createElement("span", "tag", tagText));
	});

	body.append(title, description, meta, readMore, buildActionButtons(eventData));
	card.append(media, body, tags);
	return card;
}

async function loadBootstrap() {
	try {
		const payload = await requestJson(API.bootstrap, { method: "GET", headers: {} });
		appState.user = payload.user;
		appState.events = (payload.events || []).map(normalizeEvent);
		views = buildViews();
		renderView(appState.activeView);
	} catch (error) {
		console.error(error);
		authMessage.textContent = error.message;
	}
}

function moveFocus(currentIndex, nextIndex) {
	if (nextIndex < 0 || nextIndex >= tabButtons.length) {
		return;
	}
	tabButtons[nextIndex].focus();
	renderView(tabButtons[nextIndex].dataset.view);
}

loginForm.addEventListener("submit", async (event) => {
	event.preventDefault();
	try {
		const payload = await requestJson(API.login, {
			method: "POST",
			body: JSON.stringify({
				username: usernameInput.value,
				password: passwordInput.value
			})
		});
		appState.user = payload.user;
		passwordInput.value = "";
		authMessage.textContent = `Logged in as ${payload.user.username}.`;

		closeAllModals();
		renderView(appState.activeView);
		checkPreferencesFlow();
	} catch (error) {
		authMessage.textContent = error.message;
	}
});

logoutButton.addEventListener("click", async () => {
	try {
		await requestJson(API.logout, { method: "POST", body: JSON.stringify({}) });
		appState.user = null;
		usernameInput.value = "";
		passwordInput.value = "";
		authMessage.textContent = "You have been logged out.";
		closeAllModals();
		renderView(appState.activeView);
	} catch (error) {
		authMessage.textContent = error.message;
	}
});

preferencesForm.addEventListener("submit", async (event) => {
	event.preventDefault();
	const checked = Array.from(preferencesForm.querySelectorAll('input[name="segment"]:checked')).map((el) => el.value);

	try {
		const payload = await requestJson(API.preferences, {
			method: "POST",
			body: JSON.stringify({ segments: checked })
		});
		appState.user = payload.user;
		updateAuthUI();
		closeAllModals();
		renderView(appState.activeView);
	} catch (error) {
		console.error("Failed to save preferences:", error);
	}
});

skipPreferencesBtn.addEventListener("click", () => {
	closeAllModals();
});

navUserButton.addEventListener("click", () => {
	if (appState.user) {
		openModal(profileModal);
	} else {
		openModal(loginModal);
	}
});

dialogCloses.forEach((btn) => {
	btn.addEventListener("click", () => {
		// Event dialog vs app modal closes
		if (btn.closest(".modal-overlay")) {
			closeAllModals();
		} else {
			closeEventDialog();
		}
	});
});

modalOverlays.forEach((overlay) => {
	overlay.addEventListener("click", (event) => {
		if (event.target === overlay) {
			closeAllModals();
		}
	});
});

const themeToggleBtn = document.querySelector("#theme-toggle");
if (themeToggleBtn) {
	// Initialize theme from storage
	const savedTheme = localStorage.getItem("app-theme") || "light";
	document.documentElement.setAttribute("data-theme", savedTheme);

	const moonSvg = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="moon-icon"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
	const sunSvg = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="sun-icon"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;

	if (savedTheme === "dark") {
		themeToggleBtn.innerHTML = sunSvg;
	} else {
		themeToggleBtn.innerHTML = moonSvg;
	}

	themeToggleBtn.addEventListener("click", () => {
		const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
		const newTheme = currentTheme === "dark" ? "light" : "dark";
		document.documentElement.setAttribute("data-theme", newTheme);
		localStorage.setItem("app-theme", newTheme);
		themeToggleBtn.innerHTML = newTheme === "dark" ? sunSvg : moonSvg;
	});
}

tabSwitcher.addEventListener("click", (event) => {
	const button = event.target.closest(".tab-button");
	if (!button) {
		return;
	}
	const nextView = button.dataset.view;
	if (nextView !== appState.activeView) {
		renderView(nextView);
	}
});

tabSwitcher.addEventListener("keydown", (event) => {
	const currentIndex = tabButtons.findIndex((button) => button.dataset.view === appState.activeView);
	if (event.key === "ArrowRight") {
		event.preventDefault();
		moveFocus(currentIndex, currentIndex + 1);
	}
	if (event.key === "ArrowLeft") {
		event.preventDefault();
		moveFocus(currentIndex, currentIndex - 1);
	}
});

detailClose.addEventListener("click", closeEventDialog);

detailOverlay.addEventListener("click", (event) => {
	if (event.target === detailOverlay) {
		closeEventDialog();
	}
});

document.addEventListener("keydown", (event) => {
	if (event.key === "Escape") {
		closeEventDialog();
	}
});

renderView(appState.activeView);
loadBootstrap();
