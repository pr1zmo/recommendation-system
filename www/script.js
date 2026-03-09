const placeholderEvent = Object.freeze({
	title: "test",
	description: "test",
	imageUrl: null,
	tags: ["#test1", "#test2", "#test3"]
});

const JSON_FILE = "/static/data_copy.json";

async function readJson(filePath) {
	try{
		const response = await fetch(filePath);

		if (!response.ok){
			throw new Error(`Failed to load file: ${filePath}`);
		}
		const jsonData = await response.json();
		return jsonData;
	} catch(error) {
		console.error('Error reading JSON file:', error)
		throw error;
	}
}

function normalizeEvent(rawEvent) {
	if (rawEvent.name && "imageUrl" in rawEvent && "description" in rawEvent) {
		const compactTags = [rawEvent.segment, rawEvent.genre, rawEvent.status, rawEvent.localDate]
			.filter(Boolean)
			.slice(0, 3)
			.map((value) => `#${String(value).replace(/\s+/g, "-").toLowerCase()}`);

		return {
			title: rawEvent.name,
			description: rawEvent.description || "No description available.",
			imageUrl: rawEvent.imageUrl || null,
			tags: compactTags.length > 0 ? compactTags : ["#event"]
		};
	}

	const images = Array.isArray(rawEvent.images) ? rawEvent.images : [];
	const heroImage = images.find((image) => image.ratio === "16_9") || images[0];
	const classifications = Array.isArray(rawEvent.classifications)
		? rawEvent.classifications
		: [];
	const primaryClassification = classifications[0] || {};
	const segment = primaryClassification.segment?.name;
	const genre = primaryClassification.genre?.name;
	const status = rawEvent.dates?.status?.code;
	const localDate = rawEvent.dates?.start?.localDate;

	const tags = [segment, genre, status, localDate]
		.filter(Boolean)
		.slice(0, 3)
		.map((value) => `#${String(value).replace(/\s+/g, "-").toLowerCase()}`);

	return {
		title: rawEvent.name || "Untitled event",
		description: rawEvent.info || rawEvent.pleaseNote || "No description available.",
		imageUrl: heroImage?.url || null,
		tags: tags.length > 0 ? tags : ["#event"]
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

function pickForYou(events) {
	return shuffleArray(events).slice(0, Math.min(6, events.length));
}

function buildViews(events) {
	const randomized = shuffleArray(events);
	const allItems = randomized.slice(0, Math.min(24, randomized.length));
	const forYouItems = pickForYou(randomized);

	return {
		all: {
			tabId: "tab-all",
			label: "All available events",
			caption: `${allItems.length} random events loaded.`,
			items: allItems
		},
		forYou: {
			tabId: "tab-for-you",
			label: "Recommended for you",
			caption: "Sample picks from the loaded event feed.",
			items: forYouItems
		}
	};
}

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

let activeView = "all";
let panelAnimation;
let activeDialogEvent = null;
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

detailBody.append(detailTitle, detailDescription, detailTags);
detailDialog.append(detailClose, detailHero, detailBody);
detailOverlay.append(detailDialog);
pageShell.append(detailOverlay);

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

function openEventDialog(eventData, triggerButton) {
	activeDialogEvent = eventData;
	activeReadMoreButton = triggerButton;

	detailHero.replaceChildren(createMediaNode(eventData, "dialog-image"));
	detailTitle.textContent = eventData.title;
	detailDescription.textContent = eventData.description;
	detailTags.replaceChildren();

	eventData.tags.forEach((tagText) => {
		detailTags.append(createElement("span", "tag", tagText));
	});

	detailOverlay.removeAttribute("hidden");
	detailOverlay.setAttribute("aria-hidden", "false");
	document.body.classList.add("dialog-open");
	detailClose.focus();
}

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

function createCard(eventData) {
	const card = createElement("article", "event-card");
	const media = createMediaNode(eventData, "event-image");
	const body = createElement("div", "card-body");
	const title = createElement("h3", "card-title", eventData.title);
	const description = createElement("p", "card-description", eventData.description);
	const readMore = createElement("button", "read-more", "Read more...");
	readMore.type = "button";
	readMore.addEventListener("click", () => {
		openEventDialog(eventData, readMore);
	});
	const tags = createElement("div", "tags");

	eventData.tags.forEach((tagText) => {
		tags.append(createElement("span", "tag", tagText));
	});

	body.append(title, description, readMore);
	card.append(media, body, tags);

	return card;
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

function renderView(viewKey) {
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

	activeView = viewKey;
}

async function loadAndRenderEvents() {
	try {
		const payload = await readJson(JSON_FILE);
		const rawEvents = Array.isArray(payload?.events)
			? payload.events
			: payload?._embedded?.events;

		if (!Array.isArray(rawEvents) || rawEvents.length === 0) {
			throw new Error("No events found in data.json");
		}

		const mappedEvents = rawEvents.map(normalizeEvent);
		views = buildViews(mappedEvents);
	} catch (error) {
		console.error("Falling back to placeholder events:", error);
		views = {
			all: {
				tabId: "tab-all",
				label: "All available events",
				caption: "Could not load data.json. Showing placeholders.",
				items: Array.from({ length: 6 }, () => placeholderEvent)
			},
			forYou: {
				tabId: "tab-for-you",
				label: "Recommended for you",
				caption: "Could not load recommendations. Showing placeholders.",
				items: Array.from({ length: 4 }, () => placeholderEvent)
			}
		};
	}

	renderView(activeView);
}

function moveFocus(currentIndex, nextIndex) {
	if (nextIndex < 0 || nextIndex >= tabButtons.length) {
		return;
	}

	tabButtons[nextIndex].focus();
	renderView(tabButtons[nextIndex].dataset.view);
}

tabSwitcher.addEventListener("click", (event) => {
	const button = event.target.closest(".tab-button");

	if (!button) {
		return;
	}

	const nextView = button.dataset.view;

	if (nextView === activeView) {
		return;
	}

	renderView(nextView);
});

tabSwitcher.addEventListener("keydown", (event) => {
	const currentIndex = tabButtons.findIndex((button) => button.dataset.view === activeView);

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

loadAndRenderEvents();
