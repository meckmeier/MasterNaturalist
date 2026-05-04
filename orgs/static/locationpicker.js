function getCSRFToken() {
    const tokenField = document.querySelector("[name=csrfmiddlewaretoken]");
    return tokenField ? tokenField.value : "";
}
function getCSRFTokenFromForm(form) {
    const tokenField = form.querySelector("[name=csrfmiddlewaretoken]");
    return tokenField ? tokenField.value : "";
}
function syncLocationDisplay(row) {
    let locationField = null;
    let display = null;

    if (row) {
        locationField =
            row.querySelector("select[name$='-location']") ||
            row.querySelector("select[name='default_location']");

        display = row.querySelector(".selected-location-display");
    } else {
        locationField = document.querySelector("select[name='default_location']");

        const wrapper = locationField
            ? locationField.closest(".form-field")
            : null;

        display = wrapper
            ? wrapper.querySelector(".selected-location-display")
            : document.querySelector(".selected-location-display");
    }

    if (!locationField || !display) return;

    const selectedOption = locationField.options[locationField.selectedIndex];

    if (locationField.value && selectedOption) {
        display.textContent = selectedOption.textContent;
    } else {
        display.innerHTML = '<span class="text-muted">No location selected</span>';
    }
}
function syncAllLocationDisplays() {
    document.querySelectorAll(".formset-row").forEach(function (row) {
        if (!row.classList.contains("form-template")) {
            syncLocationDisplay(row);
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("location picker loaded");

    let activeRow = null;
    const formEl =
    document.getElementById("activity-form") ||
    document.getElementById("org-form");

    const currentOrgId = formEl ? formEl.dataset.orgId : "";
    console.log ("currentOrgId", currentOrgId);

    const searchInput = document.getElementById("location-search-input");
    const orgResults = document.getElementById("org-location-results");
    const otherResults = document.getElementById("other-location-results");
    const modalEl = document.getElementById("locationSearchModal");

    if (!modalEl) return;

    syncAllLocationDisplays();

    document.addEventListener("click", handleDocumentClick);
    document.addEventListener("submit", handleDocumentSubmit);

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            renderLocationResults(searchInput.value.trim());
        });
    }

    modalEl.addEventListener("shown.bs.modal", function () {
        if (!searchInput) return;

        searchInput.value = "";
        renderLocationResults("");
        searchInput.focus();
    });

    modalEl.addEventListener("show.bs.modal", function (e) {
        const openBtn = e.relatedTarget;

        if (openBtn && openBtn.classList.contains("open-location-search")) {
            activeRow = openBtn.closest("tr")||
            openBtn.closest(".location-picker-row") ||
            openBtn.closest("form");

            console.log("location picker activeRow", activeRow);
            syncLocationDisplay(activeRow);
        }
    });
    const quickAddBtn = document.getElementById("open-quick-add-location");

    if (quickAddBtn) {
        quickAddBtn.addEventListener("click", function () {
            const searchValue = searchInput ? searchInput.value.trim() : "";
            const quickNameInput = document.querySelector("#quick-location-form input[name='loc_name']");

            console.log("copying search to add form", searchValue, quickNameInput);

            if (quickNameInput) {
                quickNameInput.value = searchValue;
            }
        });
    }

 function handleDocumentClick(e) {
    console.log("document click target:", e.target);

    const resultBtn = e.target.closest(".location-result");
    console.log("resultBtn:", resultBtn);

    if (!resultBtn) return;

    console.log("location result clicked", {
        id: resultBtn.dataset.id,
        label: resultBtn.dataset.label
    });

    chooseLocation({
        id: resultBtn.dataset.id,
        label: resultBtn.dataset.label
    });
}

    function handleDocumentSubmit(e) {
        if (e.target.id !== "quick-location-form") return;

        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const quickLocationForm = document.getElementById("quick-location-form");
        const csrfToken = getCSRFTokenFromForm(quickLocationForm);

        fetch("/locations/loc_modal/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    chooseLocation({
                        id: data.id,
                        label: data.label
                    });

                    const quickAddModalEl = document.getElementById("quickAddLocationModal");
                    const quickAddModal = bootstrap.Modal.getInstance(quickAddModalEl);
                    if (quickAddModal) {
                        quickAddModal.hide();
                    }
                } else {
                    console.log("quick location errors", data.errors);
                }
            })
            .catch(err => {
                console.error("Quick create failed:", err);
            });
    }

    function renderLocationResults(query) {
        fetch(`/locations/search/?q=${encodeURIComponent(query)}&org_id=${currentOrgId}`)
            .then(res => res.json())
            .then(data => {
                renderGroup(orgResults, data.org_locations || []);
                renderGroup(otherResults, data.other_locations || []);
            })
            .catch(err => {
                console.error("Search failed:", err);
            });
    }

    function renderGroup(container, locations) {
        if (!container) return;

        container.innerHTML = "";

        if (!locations.length) {
            container.innerHTML = '<div class="text-muted small">No matches</div>';
            return;
        }

        locations.forEach(function (loc) {
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

    function chooseLocation(loc) {

        let locationField =null;
        console.log("selects inside activeRow:", activeRow ? activeRow.querySelectorAll("select") : "no activeRow");
        if (activeRow) {
            locationField =
                activeRow.querySelector("select[name$='-location']") ||
                activeRow.querySelector("select[name='default_location']");
        } else {
            locationField = document.querySelector("select[name='default_location']");
        }

        let option = locationField.querySelector(`option[value="${loc.id}"]`);

        if (!option) {
            option = document.createElement("option");
            option.value = String(loc.id);
            option.textContent = loc.label;
            locationField.appendChild(option);
        }

        locationField.value = String(loc.id);
        locationField.dispatchEvent(new Event("change", { bubbles: true }));

        syncLocationDisplay(activeRow);
        
        const orgDisplay = document.getElementById("selected-default-location");
        if (!activeRow && orgDisplay) {
            orgDisplay.textContent = loc.label;
        }

        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
            modal.hide();
        }
    }
    window.chooseLocation = chooseLocation;
});