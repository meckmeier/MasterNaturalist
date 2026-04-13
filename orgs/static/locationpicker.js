function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

document.addEventListener("DOMContentLoaded", function () {
    let activeRow = null;

    const formEl = document.getElementById("activity-form");
    const currentOrgId = formEl ? formEl.dataset.orgId : null;
    const searchInput = document.getElementById("location-search-input");
    const orgResults = document.getElementById("org-location-results");
    const otherResults = document.getElementById("other-location-results");
    const modalEl = document.getElementById("locationSearchModal");

    if (!modalEl) return;

    document.addEventListener("click", function (e) {
        const openBtn = e.target.closest(".open-location-search");
        if (openBtn) {
            activeRow = openBtn.closest(".formset-row");
            renderLocationResults("");
            return;
        }

        const resultBtn = e.target.closest(".location-result");
        if (resultBtn) {
            chooseLocation({
                id: resultBtn.dataset.id,
                label: resultBtn.dataset.label
            });
        }
    });

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            renderLocationResults(searchInput.value);
        });
    }

    modalEl.addEventListener("shown.bs.modal", function () {
        if (searchInput) {
            searchInput.value = "";
            renderLocationResults("");
            searchInput.focus();
        }
    });

    function renderLocationResults(query) {
        fetch(`/locations/search/?q=${encodeURIComponent(query)}&org_id=${currentOrgId}`)
            .then(res => res.json())
            .then(data => {
                renderGroup(orgResults, data.org_locations);
                renderGroup(otherResults, data.other_locations);
            })
            .catch(err => {
                console.error("Search failed:", err);
            });
    }

    function renderGroup(container, locations) {
        if (!container) return;
        container.innerHTML = "";

        if (!locations.length) {
            container.innerHTML = `<div class="text-muted small">No matches</div>`;
            return;
        }

        locations.forEach(loc => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "list-group-item list-group-item-action location-result";
            button.dataset.id = loc.id;
            button.dataset.label = `${loc.label} - ${loc.city}`;
            button.innerHTML = `
                <div><strong>${loc.label}</strong></div>
                <div class="small text-muted">${loc.city} | ${loc.org_name || ""}</div>
            `;
            container.appendChild(button);
        });
    }

    window.chooseLocation = function (loc) {
        if (!activeRow) return;

        const locationField = activeRow.querySelector("select[name$='location']");
        if (!locationField) return;

        let existingOption = Array.from(locationField.options).find(
            option => option.value === String(loc.id)
        );

        if (!existingOption) {
            existingOption = document.createElement("option");
            existingOption.value = loc.id;
            existingOption.text = loc.label;
            locationField.appendChild(existingOption);
        }

        locationField.value = String(loc.id);

        const display = activeRow.querySelector(".selected-location-display");
        if (display) {
            display.textContent = `Selected: ${loc.label}`;
        }

        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
            modal.hide();
        }
    };
    document.addEventListener("submit", function (e) {
    if (e.target.id === "quick-location-form") {
        console.log("quick submit fired")
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);

        fetch("/locations/loc_modal/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCSRFToken()
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                chooseLocation({
                    id: data.id,
                    label: data.label
                });

                // close modal
                const modalEl = document.getElementById("quickAddLocationModal");
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            } else {
                console.log("errors", data.errors);
            }
        })
        .catch(err => console.error("Quick create failed:", err));
    }
});
});