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
	eventAction(eventId) {
		return `/api/events/${encodeURIComponent(eventId)}/action`;
	}
};

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
const loginForm = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username-input");
const passwordInput = document.querySelector("#password-input");
const userSummary = document.querySelector("#user-summary");
const userSummaryName = document.querySelector("#user-summary-name");
const userSummaryMeta = document.querySelector("#user-summary-meta");
const userNextRecommendation = document.querySelector("#user-next-recommendation");
const logoutButton = document.querySelector("#logout-button");
const authMessage = document.querySelector("#auth-message");

let panelAnimation;
let activeReadMoreButton = null;

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

function resolveRecommendedEvents() {
	if (!appState.user) {
		return [];
	}

	const byId = eventMap();
	const recommended = (appState.user.recommendedEventIds || [])
		.map((eventId) => byId.get(String(eventId)))
		.filter(Boolean);

	if (recommended.length > 0) {
		return recommended;
	}

	const preferredSegments = new Set(appState.user.preferences?.segments || []);
	return shuffleArray(appState.events)
		.filter((eventData) => preferredSegments.has(eventData.segment))
		.slice(0, 6);
}

function buildViews() {
	const randomized = shuffleArray(appState.events);
	const allItems = randomized.slice(0, Math.min(24, randomized.length));
	const forYouItems = appState.user ? resolveRecommendedEvents() : [];

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
			caption: appState.user
				? `${forYouItems.length} user-linked recommendations loaded.`
				: "Log in to see your user-specific recommendations.",
			items: appState.user ? forYouItems : Array.from({ length: 4 }, () => placeholderEvent)
		}
	};
}

function userHistorySet(key) {
	return new Set(appState.user?.history?.[key] || []);
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

function updateAuthUI() {
	const user = appState.user;
	if (!user) {
		loginForm.hidden = false;
		userSummary.hidden = true;
		authMessage.textContent = "Log in to like, dislike, mark events attended, and track user-specific recommendations.";
		return;
	}

	loginForm.hidden = true;
	userSummary.hidden = false;
	userSummaryName.textContent = `${user.name} (@${user.username})`;
	userSummaryMeta.textContent = `${user.city || "Unknown city"}, ${user.countryCode || "Unknown country"} · ${user.history.likedEventIds.length} liked · ${user.history.attendedEventIds.length} attended`;

	const nextEvent = eventMap().get(String(user.nextRecommendation));
	userNextRecommendation.textContent = nextEvent
		? `Next recommendation: ${nextEvent.title}`
		: "Next recommendation: not set yet";
		authMessage.textContent = "You are signed in. Event actions now save directly to users.json.";
}

function renderView(viewKey) {
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

	detailOverlay.setAttribute("hidden", "");
	detailOverlay.setAttribute("aria-hidden", "true");
	document.body.classList.remove("dialog-open");

	if (activeReadMoreButton) {
		activeReadMoreButton.focus();
	}
}

async function sendEventAction(eventId, action) {
	const payload = await requestJson(API.eventAction(eventId), {
		method: "POST",
		body: JSON.stringify({ action })
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
		sendEventAction(eventData.id, "view").catch((error) => {
			console.error(error);
		});
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
		renderView(appState.activeView);
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
		renderView(appState.activeView);
	} catch (error) {
		authMessage.textContent = error.message;
	}
});

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
