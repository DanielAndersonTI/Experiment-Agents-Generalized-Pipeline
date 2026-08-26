"use strict";

document.addEventListener("DOMContentLoaded", () => {
	const template = document.querySelector("#system-block-template");
	const systemsContainer = document.querySelector("#systems-container");
	const addButton = document.querySelector("#add-system-button");
	const countLabel = document.querySelector("#system-count");
	const runButton = document.querySelector("#run-button");
	const globalAlert = document.querySelector("#global-alert");
	const loadingAlert = document.querySelector("#pipeline-loading");
	const progressBar = document.querySelector("#pipeline-progress-bar");
	const progressPercent = document.querySelector("#pipeline-percent");
	const progressStatus = document.querySelector("#pipeline-status");
	const inputView = document.querySelector("#input-view");
	const resultsView = document.querySelector("#results-view");
	const newDecompositionButton = document.querySelector("#new-decomposition-button");
	const downloadReportButton = document.querySelector("#download-report-button");
	if (!template || !systemsContainer) return;

	const showAlert = (message, type = "danger") => {
		globalAlert.className = `alert alert-${type}`;
		globalAlert.textContent = message;
		globalAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
	};

	const clearAlert = () => {
		globalAlert.className = "alert d-none";
		globalAlert.textContent = "";
	};

	const updateBlocks = () => {
		const blocks = [...systemsContainer.querySelectorAll("[data-system-block]")];
		blocks.forEach((block, index) => {
			const number = index + 1;
			block.querySelector("[data-system-number]").textContent = number;
			block.querySelectorAll("[data-field]").forEach((field) => {
				const fieldName = field.dataset.field;
				field.id = `${fieldName.replaceAll("_", "-")}-${number}`;
				const label = block.querySelector(`label[for^="${fieldName.replaceAll("_", "-")}-"]`);
				if (label) label.htmlFor = field.id;
			});
			block.querySelector("[data-remove-system]").disabled = blocks.length === 1;
		});
		countLabel.textContent = blocks.length;
		addButton.disabled = blocks.length >= 10;
	};

	const appendBlock = () => {
		systemsContainer.appendChild(template.content.cloneNode(true));
		updateBlocks();
	};

	const validateSystems = () => {
		let isValid = true;
		const blocks = [...systemsContainer.querySelectorAll("[data-system-block]")];
		blocks.forEach((block) => {
			block.querySelectorAll("[data-field]").forEach((field) => {
				const valid = field.value.trim().length > 0;
				field.classList.toggle("is-invalid", !valid);
				if (!valid) isValid = false;
			});
		});
		if (!isValid) showAlert("Complete all required fields before running the pipeline.");
		else clearAlert();
		return isValid;
	};

	const formatMetric = (value) => typeof value === "number" ? value.toFixed(4) : "-";
	const renderRows = (items, target, columns) => {
		target.innerHTML = "";
		if (!items || items.length === 0) {
			target.innerHTML = `<tr><td colspan="${columns}" class="empty-state">No results available.</td></tr>`;
			return;
		}
		items.forEach((item) => {
			const row = document.createElement("tr");
			row.innerHTML = `<td>${item.system || "-"}</td><td>${item.proposal || "-"}</td><td>${formatMetric(item.precision)}</td><td>${formatMetric(item.recall)}</td><td>${formatMetric(item.f1_score)}</td>`;
			target.appendChild(row);
		});
	};

	const renderResults = (payload) => {
		const resultsAlert = document.querySelector("#results-alert");
		const messages = [...(payload.errors || []), ...(payload.warnings || [])].map((item) => `${item.system}: ${item.message}`);
		resultsAlert.className = messages.length ? "alert alert-warning" : "alert d-none";
		resultsAlert.textContent = messages.join(" ");
		renderRows(payload.service_metrics, document.querySelector("#services-table-body"), 5);
		renderRows(payload.interaction_metrics, document.querySelector("#interactions-table-body"), 5);
		const bestBody = document.querySelector("#best-results-table-body");
		bestBody.innerHTML = "";
		if (!payload.best_results || payload.best_results.length === 0) {
			bestBody.innerHTML = '<tr><td colspan="3" class="empty-state">No best results available.</td></tr>';
		} else {
			payload.best_results.forEach((item) => {
				const row = document.createElement("tr");
				row.innerHTML = `<td>${item.system || "-"}</td><td>${item.best_services || "-"}</td><td>${item.best_interactions || "-"}</td>`;
				bestBody.appendChild(row);
			});
		}
		inputView.classList.add("d-none");
		resultsView.classList.remove("d-none");
		window.scrollTo({ top: 0, behavior: "smooth" });
	};

	const collectSystems = () => [...systemsContainer.querySelectorAll("[data-system-block]")].map((block) => {
		const system = {};
		block.querySelectorAll("[data-field]").forEach((field) => { system[field.dataset.field] = field.value; });
		return system;
	});

	const updateProgress = (progress) => {
		const percent = Math.max(0, Math.min(100, Number(progress.percent) || 0));
		progressBar.style.width = `${percent}%`;
		progressPercent.textContent = `${percent}%`;
		progressBar.parentElement.setAttribute("aria-valuenow", String(percent));
		progressStatus.textContent = progress.completed < progress.total
			? `Completed ${progress.completed} of ${progress.total} systems${progress.current_system ? ` | Running: ${progress.current_system}` : ""}`
			: "All systems processed. Preparing results...";
	};

	const watchProgress = () => {
		updateProgress({ percent: 0, completed: 0, total: systemsContainer.querySelectorAll("[data-system-block]").length });
		return setInterval(async () => {
			try {
				const response = await fetch("/api/pipeline/progress", { cache: "no-store" });
				if (response.ok) updateProgress(await response.json());
			} catch (error) {
				// The run request remains the source of truth if a progress poll fails.
			}
		}, 500);
	};

	addButton.addEventListener("click", async () => {
		const currentCount = systemsContainer.querySelectorAll("[data-system-block]").length;
		if (currentCount >= 10) return;
		const response = await fetch("/api/systems", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ current_count: currentCount }),
		});
		if (!response.ok) return;
		appendBlock();
	});

	systemsContainer.addEventListener("click", async (event) => {
		const removeButton = event.target.closest("[data-remove-system]");
		if (!removeButton) return;
		const blocks = [...systemsContainer.querySelectorAll("[data-system-block]")];
		if (blocks.length === 1) return;
		const block = removeButton.closest("[data-system-block]");
		const index = blocks.indexOf(block);
		const response = await fetch(`/api/systems/${index}`, {
			method: "DELETE",
			headers: { "X-System-Count": String(blocks.length) },
		});
		if (!response.ok) return;
		block.remove();
		updateBlocks();
	});

	systemsContainer.addEventListener("input", (event) => {
		const field = event.target.closest("[data-field]");
		if (!field || field.value.trim().length === 0) return;
		field.classList.remove("is-invalid");
	});

	runButton.addEventListener("click", async () => {
		if (!validateSystems()) return;
		runButton.disabled = true;
		runButton.textContent = "RUNNING PIPELINE...";
		loadingAlert.classList.remove("d-none");
		const progressWatcher = watchProgress();
		showAlert("The pipeline is running. This may take a few minutes. Please wait...", "info");
		try {
			const response = await fetch("/api/pipeline/run", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ systems: collectSystems() }),
			});
			const payload = await response.json();
			if (!response.ok || !payload.ok) throw new Error(payload.message || "The pipeline run failed.");
			renderResults(payload);
		} catch (error) {
			showAlert(error.message || "The pipeline run could not be completed.");
		} finally {
			clearInterval(progressWatcher);
			updateProgress({ percent: 100, completed: systemsContainer.querySelectorAll("[data-system-block]").length, total: systemsContainer.querySelectorAll("[data-system-block]").length });
			loadingAlert.classList.add("d-none");
			runButton.disabled = false;
			runButton.textContent = "RUN PIPELINE";
		}
	});

	newDecompositionButton.addEventListener("click", () => {
		document.querySelector("#decomposition-form").reset();
		systemsContainer.innerHTML = "";
		appendBlock();
		resultsView.classList.add("d-none");
		inputView.classList.remove("d-none");
		clearAlert();
		window.scrollTo({ top: 0, behavior: "smooth" });
	});

	downloadReportButton.addEventListener("click", () => {
		window.location.href = "/api/report/pdf";
	});

	appendBlock();
});
