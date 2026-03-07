const placeholderEvent = Object.freeze({
	title: "test",
	description: "test",
	tags: ["#test1", "#test2", "#test3"]
});

Events = {
	//
}

const views = {
	all: {
		tabId: "tab-all",
		label: "All available events",
		caption: "A simple card grid ready for your future catalog.",
		items: Array.from({ length: 6 }, () => placeholderEvent)
	},
	forYou: {
		tabId: "tab-for-you",
		label: "Recommended for you",
		caption: "A recommendation-focused lane for future personalized ranking.",
		items: Array.from({ length: 4 }, () => placeholderEvent)
	}
};

const panel = document.querySelector("#event-panel");
const panelLabel = document.querySelector("#panel-label");
const panelCaption = document.querySelector("#panel-caption");
const tabSwitcher = document.querySelector(".tab-switcher");
const tabButtons = Array.from(document.querySelectorAll(".tab-button"));

let activeView = "all";
let panelAnimation;

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
	const media = createElement("div", "image-placeholder", "No image");
	const body = createElement("div", "card-body");
	const title = createElement("h3", "card-title", eventData.title);
	const description = createElement("p", "card-description", eventData.description);
	const tags = createElement("div", "tags");

	eventData.tags.forEach((tagText) => {
		tags.append(createElement("span", "tag", tagText));
	});

	body.append(title, description);
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

renderView(activeView);
