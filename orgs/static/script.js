// --- global URL for AJAX ---
// --this form contains page UI, activity form/formset and zip lookup for location.
console.log("FORMSET SCRIPT LOADED");

// --- run after DOM is ready ---
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");
  
    const tabButtons = document.querySelectorAll('#eventTabs button[data-bs-toggle="tab"]');

    tabButtons.forEach(btn => {
        btn.addEventListener('shown.bs.tab', function (event) {
        // event.target = newly activated tab button
        const targetId = event.target.getAttribute('data-bs-target'); // e.g. "#online"
        history.replaceState(null, '', targetId); // updates URL hash without reloading
        });
    });


    // Check if the URL has a hash like #activity-123
    const hash = window.location.hash;

    if (hash) {
        const targetEl = document.querySelector(hash);
            if (targetEl) {

                targetEl.scrollIntoView({ behavior: "smooth", block: "start" });

                const tabPane =targetEl.classList.contains("tab-pane")
                        ? targetEl
                        : targetEl.closest(".tab-pane");
                if (tabPane && !tabPane.classList.contains("show", "active")) {
                    const tabId = tabPane.id;
                    const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
                    if (tabButton) {
                        const tab = new bootstrap.Tab(tabButton);
                        tab.show();
                    }
                }

            }
            console.log("finished with hash code")
        }
    
    // description block expand/collapse

    const descriptionBlocks = document.querySelectorAll('.me-description-block');

    descriptionBlocks.forEach(block => {
    block.addEventListener('click', () => {
        block.classList.toggle('expanded');
        });
    });
    function updateSessionRowVisibility(row) {
    const formatField = row.querySelector("select[name$='-session_format']");
    const locationField = row.querySelector("select[name$='-location']");
    const urlGroup = row.querySelector(".url-group");
    const locationGroup = row.querySelector(".loc-group");

    if (!formatField) return;

    const format = formatField.value;
    console.log("visibility", { format, urlGroup, locationGroup, locationField });

    const showUrl = (format === "o" || format === "b");
    const showLocation = (format === "i" || format === "b");

    if (urlGroup) {
        urlGroup.style.display = showUrl ? "block" : "none";
    }

    if (locationGroup) {
        locationGroup.style.display = showLocation ? "block" : "none";
    }

    // Clear location whenever this format should not keep a location
    if (locationField && (format === "o" || format === "s")) {
        locationField.value = "";
    }

    syncLocationDisplay(row);
    }
    const activityForm = document.getElementById("activity-form");
 
    function syncLocationDisplay(row) {
    if (!row) return;

    const locationField = row.querySelector("select[name$='-location']");
    const display = row.querySelector(".selected-location-display");

    if (!locationField || !display) return;

    const selectedOption = locationField.options[locationField.selectedIndex];

    if (locationField.value && selectedOption) {
        display.textContent = selectedOption.textContent;
    } else {
        display.innerHTML = '<span class="text-muted">No location selected</span>';
    }
}

function wireSessionRow(row) {
    const formatField = row.querySelector("select[name$='session_format']");
    const locationField = row.querySelector("select[name$='-location']");
    const startField = row.querySelector("input[name$='start']");
    const endField = row.querySelector("input[name$='end']");

    if (!formatField) return;

    const format = formatField.value;

    

    syncLocationDisplay(row);

    formatField.addEventListener("change", function () {
        const format = formatField.value;
        const currentLocation = locationField ? locationField.value : "";

        updateSessionRowVisibility(row);

       

        syncLocationDisplay(row);
    });

    if (startField && endField) {
        startField.addEventListener("change", function () {
            if (!endField.value) {
                endField.value = startField.value;
            }
        });
    }

    updateSessionRowVisibility(row);
    }
    document.querySelectorAll(".formset-row").forEach(row => {
        if (!row.classList.contains("form-template")){
            wireSessionRow(row);
        }
    });
    document.addEventListener("click", function(e) {
    if (e.target && e.target.id === "add-btn") {
        const container = document.querySelector(".formset");
        const totalForms = document.querySelector("[id$='-TOTAL_FORMS']");
        const template = document.querySelector(".form-template");
        const tbody = document.querySelector(".formset-table tbody");
        console.log("Add button clicked", { container, totalForms, template, tbody });

        if (!container || !totalForms || !template || !tbody) return;

        const emptyHint = document.querySelector(".empty-hint");
        if (emptyHint) emptyHint.remove();

        const formIndex = parseInt(totalForms.value);
        const newRow = template.cloneNode(true);
        newRow.style.display = "table-row";
        newRow.classList.remove("form-template");
        newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formIndex);

        tbody.appendChild(newRow);
        totalForms.value = formIndex + 1;
        const newFormatField = newRow.querySelector("select[name$='session_format']");
        if (newFormatField && !newFormatField.value) {
            newFormatField.value = "i";
        }

        wireSessionRow(newRow);

    }
    });

    console.log("finished with current code")

    const zipField = document.getElementById("id_zip_code");
    const countyField = document.getElementById("id_county_id");
    const regionField = document.getElementById("id_region_name");
    console.log("starting zip code lookup wiring", { zipField, countyField, regionField });
    if (zipField && countyField && regionField) {

        zipField.addEventListener("change", function () {
           
            const zip = zipField.value.trim().substring(0, 5);          
            console.log("looking up zip code", zip);
            
            fetch(`/lookup-zip/?zip_code=${zip}`)
                .then(response => response.json())
                .then(data => {
                    console.log("zip lookup response", data);
                    if (data.county_id) {
                        countyField.value = data.county_id;
                    }
                    if (data.region) {
                        regionField.value = data.region;
                    }
                })
                .catch(error => console.error("Zip lookup failed:", error));
        });
    }
    
});